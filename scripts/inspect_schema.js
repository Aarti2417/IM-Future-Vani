const fs = require('fs');
const schema = JSON.parse(fs.readFileSync('agent_config_schema.json', 'utf-8'));
const defs = schema['$defs'];
const v2v = defs['V2VApp'];
console.log('V2VApp properties:', Object.keys(v2v.properties || {}));

const llmConfig = defs[v2v.properties.llm_config['$ref'].split('/').pop()];
console.log('llmConfig properties:', Object.keys(llmConfig.properties || {}));

const agentConfig = defs[llmConfig.properties.agent_config['$ref'].split('/').pop()];
console.log('agentConfig properties:', Object.keys(agentConfig.properties || {}));

const state = defs[agentConfig.properties.states.additionalProperties['$ref'].split('/').pop()];
console.log('State properties:', Object.keys(state.properties || {}));
