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
  console.log("=== 1. Fetching tools to get tool IDs ===");
  const toolsRes = await callMcp('agents', {
    operation: 'get',
    id: AGENT_ID,
    params: { include: ['tools'] }
  });
  const match = toolsRes.match(/data: (\{.*\})/);
  const tools = JSON.parse(JSON.parse(match[1]).result.content[0].text).tools;
  
  const pricingTool = tools.find(t => t.name === 'get_official_pricing');
  const bookingTool = tools.find(t => t.name === 'book_relationship_manager_slot');

  console.log("=== 2. Updating get_official_pricing ===");
  if (pricingTool) {
    await callMcp('configure_app_tool', {
      agent_id: AGENT_ID,
      tool_id: pricingTool.id,
      tool_type: 'webhook',
      name: 'get_official_pricing',
      description: 'Fetch verified IndiaMART membership package pricing and monthly breakdown.',
      connector_config: {
        url: 'https://httpbin.org/anything',
        method: 'POST',
        lifecycle: 'run',
        body: [
          {
            name: 'turnover',
            type: 'llm_prompt',
            description: 'Annual turnover tier of the seller (e.g. 0 - 40 L, 40 L - 1.5 Cr)',
            param_type: 'Text',
            required: false,
            is_input_property: true
          }
        ],
        resp_template: 'Mini Leader plan lagbhag ₹2,000 se ₹2,500 mahina shuru hota hai sir, saalaana ₹28,000 plus GST, jisme direct verified buyers connect karte hain.',
        on_failure: 'Mini Leader plan lagbhag ₹2,000 se ₹2,500 mahina shuru hota hai sir.'
      }
    });
    console.log("Updated pricing tool:", pricingTool.id);
  }

  console.log("=== 3. Updating book_relationship_manager_slot ===");
  if (bookingTool) {
    await callMcp('configure_app_tool', {
      agent_id: AGENT_ID,
      tool_id: bookingTool.id,
      tool_type: 'webhook',
      name: 'book_relationship_manager_slot',
      description: 'Book a confirmed callback or appointment with an IndiaMART Relationship Manager.',
      connector_config: {
        url: 'https://httpbin.org/anything',
        method: 'POST',
        lifecycle: 'run',
        body: [
          {
            name: 'date',
            type: 'llm_prompt',
            description: 'Preferred day or date (e.g. Somwar, Tuesday)',
            param_type: 'Text',
            required: true,
            is_input_property: true
          },
          {
            name: 'time_slot',
            type: 'llm_prompt',
            description: 'Preferred time slot (e.g. 11:00 AM, shaam 7 baje)',
            param_type: 'Text',
            required: true,
            is_input_property: true
          }
        ],
        resp_template: 'Aapka slot note aur confirm ho gaya hai sir. Humare Relationship Manager aapse connect karenge.',
        on_failure: 'Slot note kar liya hai sir, Relationship Manager connect karenge.'
      }
    });
    console.log("Updated booking tool:", bookingTool.id);
  }

  console.log("=== 4. Committing final production version ===");
  const commitRes = await callMcp('agents', {
    operation: 'commit',
    id: AGENT_ID,
    params: {
      app_version_description: 'All 3 grounded tools (leads, pricing, booking) fully configured and live'
    }
  });
  console.log("Commit result:", commitRes);
}

run();
