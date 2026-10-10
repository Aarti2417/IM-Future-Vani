const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;

const KB_ID = '01a1261e-69f1-7daa-aa1d-710cc98fc453';
const DOCS_DIR = path.join(__dirname, '..', 'knowledge_base_docs');

async function callMcp(toolName, args) {
  const res = await fetch('https://mcp.sarvam.ai/voice-agents', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args
      }
    })
  });
  const t = await res.text();
  const match = t.match(/data: (\{.*\})/);
  if (match) {
    const d = JSON.parse(match[1]);
    if (d.result && d.result.content && d.result.content[0]) {
      return JSON.parse(d.result.content[0].text);
    }
  }
  return { raw: t };
}

async function uploadFile(fileName) {
  const filePath = path.join(DOCS_DIR, fileName);
  const buffer = fs.readFileSync(filePath);
  const hash = crypto.createHash('sha256').update(buffer).digest('hex');
  const size = buffer.length;

  console.log(`\n--- Uploading ${fileName} (Size: ${size} bytes, SHA256: ${hash.slice(0, 10)}...) ---`);
  
  // Step 1: kb_file_upload_begin
  const beginRes = await callMcp('kb_file_upload_begin', {
    kb_id: KB_ID,
    file_name: fileName,
    mime_type: 'text/markdown',
    size_bytes: size,
    sha256: hash
  });

  console.log("Begin result:", beginRes);

  if (beginRes.duplicate) {
    console.log(`File ${fileName} is already in KB.`);
    return;
  }

  const uploadUrl = beginRes.url || beginRes.upload_url;
  const fileId = beginRes.file_id || beginRes.id;
  const uploadToken = beginRes.upload_token || beginRes.token;

  if (uploadUrl) {
    console.log(`PUTing bytes to uploadUrl...`);
    const putHeaders = beginRes.headers || { 'Content-Type': 'text/markdown' };
    const putRes = await fetch(uploadUrl, {
      method: 'PUT',
      headers: putHeaders,
      body: buffer
    });
    console.log(`PUT status: ${putRes.status}`);
  }

  // Step 2: kb_file_upload_commit
  console.log(`Committing file ${fileId}...`);
  const commitRes = await callMcp('kb_file_upload_commit', {
    kb_id: KB_ID,
    file_id: fileId,
    upload_token: uploadToken,
    wait_seconds: 30
  });

  console.log("Commit result:", commitRes);
}

async function run() {
  const files = fs.readdirSync(DOCS_DIR).filter(f => f.endsWith('.md'));
  for (const f of files) {
    await uploadFile(f);
  }
  console.log("\nAll files uploaded to Sarvam Knowledge Base!");
}

run();
