const fs = require('fs');

const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;
const AGENT_ID = 'IM-Future-0c2c99ce-3384';
const KB_NAME = 'indiamart-vani-knowledge-base';

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
  return t;
}

async function run() {
  console.log("=== 1. Fetching Agent Current Config ===");
  const getRes = await callMcp('agents', {
    operation: 'get',
    id: AGENT_ID,
    params: { include: ['config', 'tools'] }
  });
  const match = getRes.match(/data: (\{.*\})/);
  const data = JSON.parse(JSON.parse(match[1]).result.content[0].text);
  const config = data.config;

  console.log("=== 2. Configuring kb_config and tool_names ===");
  config.llm_config.agent_config.kb_config = {
    [KB_NAME]: {
      kb_full_name: {
        org: "01a1112c-bff9-7099-98ef-6c8f07b46b81",
        workspace: "01a1112c-bffd-7e07-9097-09e6f78f8a3c",
        kb: "01a1261e-69f1-7daa-aa1d-710cc98fc453"
      },
      description: "Official IndiaMART seller datasets, package pricing cards, buyer inquiry demand stats, and trade objection protocols.",
      version: "latest"
    }
  };

  const startTools = new Set(config.llm_config.agent_config.states.start.tool_names || []);
  startTools.add('query_knowledge_base');
  config.llm_config.agent_config.states.start.tool_names = Array.from(startTools);

  console.log("Updated start tool_names:", config.llm_config.agent_config.states.start.tool_names);

  console.log("=== 3. Writing config update to Sarvam ===");
  const updateRes = await callMcp('configure_agent', {
    agent_id: AGENT_ID,
    config: config
  });
  console.log("Config update result:", updateRes);

  console.log("=== 4. Committing Agent Version ===");
  const commitRes = await callMcp('agents', {
    operation: 'commit',
    id: AGENT_ID,
    params: {
      app_version_description: 'Bound indiamart-vani-knowledge-base with 3 ingested docs and enabled query_knowledge_base'
    }
  });
  console.log("Commit result:", commitRes);
}

run();
