const fs = require('fs');

const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;
const AGENT_ID = 'IM-Future-0c2c99ce-3384';

async function run() {
  console.log("=== 1. Fetching current config ===");
  const getRes = await fetch('https://mcp.sarvam.ai/voice-agents', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: 'agents',
        arguments: {
          operation: 'get',
          id: AGENT_ID,
          params: { include: ['config'] }
        }
      }
    })
  });
  const t = await getRes.text();
  const match = t.match(/data: (\{.*\})/);
  const data = JSON.parse(JSON.parse(match[1]).result.content[0].text);
  const config = data.config;

  console.log("=== 2. Updating states.start.tool_names ===");
  config.llm_config.agent_config.states.start.tool_names = [
    'get_verified_buyer_leads',
    'get_official_pricing',
    'book_relationship_manager_slot',
    'end_interaction'
  ];

  const updateRes = await fetch('https://mcp.sarvam.ai/voice-agents', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: 'configure_agent',
        arguments: {
          agent_id: AGENT_ID,
          config: config
        }
      }
    })
  });
  console.log('Update config result:', await updateRes.text());

  console.log("\n=== 3. Committing Version ===");
  const commitRes = await fetch('https://mcp.sarvam.ai/voice-agents', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + accessToken,
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: {
        name: 'agents',
        arguments: {
          operation: 'commit',
          id: AGENT_ID,
          params: {
            app_version_description: 'Added tools to start state tool_names'
          }
        }
      }
    })
  });
  console.log('Commit result:', await commitRes.text());
}

run();
