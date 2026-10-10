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
  console.log("==================================================");
  console.log("  Testing IndiaMART VANI on Sarvam Samvaad Live");
  console.log("==================================================");

  // Scenario: Pricing test
  const r1 = await chat("Namaste, IndiaMART ka charges kitna padega?", null, true);
  console.log("Caller: Namaste, IndiaMART ka charges kitna padega?");
  console.log("Agent:", r1.text || r1.message);

  console.log("\n--------------------------------------------------");
  // Scenario: Buyer Leads test
  const r2 = await chat("UPVC windows me kitne buyers hain?", r1.interaction_id, false);
  console.log("Caller: UPVC windows me kitne buyers hain?");
  console.log("Agent:", r2.text || r2.message);

  console.log("\n--------------------------------------------------");
  // Scenario: Booking slot
  const r3 = await chat("Theek hai, Somwar subah 11 baje phone pe baat karwa dijiye.", r1.interaction_id, false);
  console.log("Caller: Theek hai, Somwar subah 11 baje phone pe baat karwa dijiye.");
  console.log("Agent:", r3.text || r3.message);
  console.log("==================================================");
}

run();
