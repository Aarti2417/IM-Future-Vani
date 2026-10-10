const fs = require('fs');
const schema = JSON.parse(fs.readFileSync('C:/Users/IMart/.gemini/antigravity-ide/mcp/sarvam-voice-agents/configure_app_tool.json', 'utf-8'));
const defs = schema.parameters['$defs'];
console.log('mock_config:', defs.AgentHttpToolConfig.properties.mock_config);
console.log('mock:', defs.AgentHttpToolConfig.properties.mock);
