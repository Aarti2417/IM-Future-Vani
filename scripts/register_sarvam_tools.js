const fs = require('fs');
const path = require('path');

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
  console.log("=== 1. Registering get_official_pricing ===");
  const pricingRes = await callMcp('configure_app_tool', {
    agent_id: AGENT_ID,
    tool_type: 'webhook',
    name: 'get_official_pricing',
    description: 'Fetch verified IndiaMART membership package pricing and monthly breakdown.',
    connector_config: {
      url: 'https://api.indiamart.mock/pricing',
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
      resp_template: 'Mini Leader plan lagbhag ₹2,000 se ₹2,500 mahina shuru hota hai sir, jisme monthly verified direct buy leads milti hain.',
      on_failure: 'Mini Leader plan lagbhag ₹2,000 se ₹2,500 mahina shuru hota hai sir.',
      mock: [
        {
          body: JSON.stringify({
            package: 'Mini Leader',
            monthly_cost: '₹2,333/month',
            annual_cost: '₹28,000 + GST',
            verified_leads: 45
          })
        }
      ]
    }
  });
  console.log('Pricing result:', pricingRes.includes('isError') ? 'Error: ' + pricingRes : 'SUCCESS');

  console.log("\n=== 2. Registering book_relationship_manager_slot ===");
  const bookingRes = await callMcp('configure_app_tool', {
    agent_id: AGENT_ID,
    tool_type: 'webhook',
    name: 'book_relationship_manager_slot',
    description: 'Book a confirmed callback or appointment with an IndiaMART Relationship Manager.',
    connector_config: {
      url: 'https://api.indiamart.mock/book-slot',
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
      resp_template: 'Aapka slot {{date}} ko {{time_slot}} baje confirm ho gaya hai sir.',
      on_failure: 'Main slot note kar leta hoon sir, team aapse connect kar legi.',
      mock: [
        {
          body: JSON.stringify({
            status: 'confirmed',
            booking_id: 'IM-RM-102938'
          })
        }
      ]
    }
  });
  console.log('Booking result:', bookingRes.includes('isError') ? 'Error: ' + bookingRes : 'SUCCESS');

  console.log("\n=== 3. Committing Agent Version ===");
  const commitRes = await callMcp('agents', {
    operation: 'commit',
    id: AGENT_ID,
    params: {
      app_version_description: 'Registered get_verified_buyer_leads, get_official_pricing, and book_relationship_manager_slot'
    }
  });
  console.log('Commit result:', commitRes);
}

run();
