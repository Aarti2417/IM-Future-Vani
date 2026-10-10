const fs = require('fs');
const schema = JSON.parse(fs.readFileSync('agent_config_schema.json', 'utf-8'));
const defs = schema['$defs'];
const v2v = defs['V2VApp'];
const llmConfig = defs[v2v.properties.llm_config['$ref'].split('/').pop()];
const agentConfig = defs[llmConfig.properties.agent_config['$ref'].split('/').pop()];

console.log('KnowledgeBaseConfig:', JSON.stringify(defs['KnowledgeBaseConfig'], null, 2));
console.log('AppKnowledgeBaseConfig:', JSON.stringify(defs['AppKnowledgeBaseConfig'], null, 2));
