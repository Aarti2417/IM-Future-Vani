const fs = require('fs');
const schema = JSON.parse(fs.readFileSync('agent_config_schema.json', 'utf-8'));
const defs = schema['$defs'];
const v2v = defs['V2VApp'];
const intro = defs[v2v.properties.intro_message_config['$ref'].split('/').pop()];
console.log('IntroMessageConfig properties:', Object.keys(intro.properties || {}));
console.log('IntroMessageConfig schema:', JSON.stringify(intro, null, 2));
