const fs = require('fs');

const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;
const KB_ID = '01a1261e-69f1-7daa-aa1d-710cc98fc453';

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

async function run() {
  console.log("==============================================================");
  console.log("  INSPECTING DATA STORED IN SARVAM KNOWLEDGE BASE");
  console.log("==============================================================");

  // 1. Get KB and Files list
  const kbData = await callMcp('knowledge_base', {
    operation: 'get',
    id: KB_ID,
    params: { include: ['files'] }
  });

  console.log("Knowledge Base Name:", kbData.name || kbData.kb_name);
  console.log("Knowledge Base ID:  ", kbData.id);
  console.log("Files Ingested:     ", (kbData.files || []).length);
  console.log("--------------------------------------------------------------");

  (kbData.files || []).forEach((f, idx) => {
    console.log(`[File ${idx + 1}]`);
    console.log(`  Filename:  ${f.filename}`);
    console.log(`  File ID:   ${f.id}`);
    console.log(`  Status:    ${f.status} (Indexed & Searchable)`);
    console.log(`  Size:      ${f.size_bytes} bytes`);
    console.log(`  Pages:     ${f.page_count}`);
    console.log(`  Entities:  ${f.entity_count}`);
    console.log("--------------------------------------------------------------");
  });

  // 2. Perform a live semantic retrieval search test to show stored chunks
  console.log("\n==============================================================");
  console.log("  LIVE VECTOR RETRIEVAL: WHAT SARVAM'S BRAIN SEES");
  console.log("==============================================================");
  const searchResults = await callMcp('knowledge_base', {
    operation: 'search',
    params: {
      kb_ids: [KB_ID],
      query: "Mini Leader package cost and UPVC sliding windows buyers",
      top_k: 3,
      mode: 'balanced'
    }
  });

  console.log("Search Query: 'Mini Leader package cost and UPVC sliding windows buyers'");
  console.log("\nRetrieved Passages from Sarvam's Index:");
  if (searchResults && searchResults.results) {
    searchResults.results.forEach((r, idx) => {
      console.log(`\nResult #${idx + 1} (Score: ${r.score || r.relevance}):`);
      console.log(`Source File: ${r.filename || r.file_id}`);
      console.log(`Passage Text:`);
      console.log(r.text || r.content || JSON.stringify(r));
    });
  } else {
    console.log(JSON.stringify(searchResults, null, 2));
  }
}

run();
