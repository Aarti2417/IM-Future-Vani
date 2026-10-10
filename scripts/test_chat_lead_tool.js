const fs = require('fs');

const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;
const AGENT_ID = 'IM-Future-0c2c99ce-3384';

async function chat(text, interactionId = null, start = false) {
  const payload = {
    app_id: AGENT_ID,
    text: text,
    start_interaction: start,
    save_logs: true
  };
  if (interactionId) {
    payload.interaction_id = interactionId;
  }

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
        name: 'send_chat',
        arguments: payload
      }
    })
  });
  const t = await res.text();
  const match = t.match(/data: (\{.*\})/);
  if (match) {
    const d = JSON.parse(JSON.parse(match[1]).result.content[0].text);
    return d;
  }
  return { raw: t };
}

async function run() {
  console.log("Turn 1: Greeting");
  const r1 = await chat("Namaste, kaun bol raha hai?", null, true);
  console.log("Agent:", r1.text || r1.message || JSON.stringify(r1));
  const id = r1.interaction_id;

  console.log("\nTurn 2: Asking for UPVC sliding windows buyers (triggers get_verified_buyer_leads)");
  const r2 = await chat("UPVC sliding windows ke buyers kitne hain aapke paas?", id, false);
  console.log("Agent:", r2.text || r2.message || JSON.stringify(r2));
  console.log("Full Turn 2 Output:", JSON.stringify(r2, null, 2));
}

run();
