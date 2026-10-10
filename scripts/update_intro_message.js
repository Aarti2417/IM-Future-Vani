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
  console.log("=== 1. Fetching Agent Current Config ===");
  const getRes = await callMcp('agents', {
    operation: 'get',
    id: AGENT_ID,
    params: { include: ['config'] }
  });
  const match = getRes.match(/data: (\{.*\})/);
  const data = JSON.parse(JSON.parse(match[1]).result.content[0].text);
  const config = data.config;

  console.log("=== 2. Updating intro_message_config to Outbound IndiaMART Seller Growth ===");
  const hindiIntro = "नमस्ते जी, मैं इंडियामार्ट से बोल रहा हूँ। आपके व्यापार के लिए कुछ verified bulk buyers की inquiries आई हैं, क्या अभी आपसे दो मिनट बात हो सकती है?";
  const englishIntro = "Namaste ji, I am calling from IndiaMART. We have verified bulk buyer inquiries for your business, is this a good time to speak for two minutes?";

  config.intro_message_config = {
    config_version: "1.0",
    audio: englishIntro,
    multilingual_audio: {
      default_language: "Hindi",
      language_text_mapping: {
        Hindi: hindiIntro,
        English: englishIntro
      }
    },
    multilingual_audio_male: {
      default_language: "Hindi",
      language_text_mapping: {
        Hindi: hindiIntro,
        English: englishIntro
      }
    },
    multilingual_audio_female: {
      default_language: "Hindi",
      language_text_mapping: {
        Hindi: "नमस्ते जी, मैं इंडियामार्ट से बोल रही हूँ। आपके व्यापार के लिए कुछ verified bulk buyers की inquiries आई हैं, क्या अभी आपसे दो मिनट बात हो सकती है?",
        English: englishIntro
      }
    },
    pre_recorded_audio_message: null
  };

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
      app_version_description: 'Updated intro_message to outbound IndiaMART Vyapari seller greeting'
    }
  });
  console.log("Commit result:", commitRes);
}

run();
