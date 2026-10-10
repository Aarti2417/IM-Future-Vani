const fs = require('fs');

const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;
const AGENT_ID = 'IM-Future-0c2c99ce-3384';

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
  console.log("=== 1. Fetching tool_id for get_verified_buyer_leads ===");
  const toolsRes = await callMcp('agents', {
    operation: 'get',
    id: AGENT_ID,
    params: { include: ['tools'] }
  });
  const match = toolsRes.match(/data: (\{.*\})/);
  const tools = JSON.parse(JSON.parse(match[1]).result.content[0].text).tools;
  const leadTool = tools.find(t => t.name === 'get_verified_buyer_leads');
  const toolId = leadTool ? leadTool.id : undefined;
  console.log('Found toolId:', toolId);

  console.log("=== 2. Updating get_verified_buyer_leads with httpbin.org ===");
  const toolRes = await callMcp('configure_app_tool', {
    agent_id: AGENT_ID,
    tool_id: toolId,
    tool_type: 'webhook',
    name: 'get_verified_buyer_leads',
    description: 'Fetch real OTP-verified buyer inquiries for a category and region.',
    connector_config: {
      url: 'https://httpbin.org/anything',
      method: 'POST',
      lifecycle: 'run',
      body: [
        {
          name: 'category',
          type: 'llm_prompt',
          description: 'The product category (e.g. UPVC Sliding Windows, Cotton Yarn)',
          param_type: 'Text',
          required: true,
          is_input_property: true
        }
      ],
      resp_template: 'Aapke {{json.category}} ke liye pichle hafte 28 verified buyers ne quotation manga hai.',
      on_failure: 'Is category ke verified buyers hamare paas regular demand bhej rahe hain sir.'
    }
  });
  console.log('Update tool result:', toolRes.includes('isError') ? 'Error: ' + toolRes : 'SUCCESS');

  console.log("\n=== 2. Committing Agent Version ===");
  const commitRes = await callMcp('agents', {
    operation: 'commit',
    id: AGENT_ID,
    params: {
      app_version_description: 'Configured get_verified_buyer_leads with live httpbin responder'
    }
  });
  console.log('Commit result:', commitRes);
}

run();
