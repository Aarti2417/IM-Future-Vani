const fs = require('fs');
const schema = JSON.parse(fs.readFileSync('agent_config_schema.json', 'utf-8'));
const defs = schema['$defs'];
console.log('KBFullName:', JSON.stringify(defs['KBFullName'], null, 2));
