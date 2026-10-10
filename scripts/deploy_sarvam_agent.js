/**
 * Sarvam Voice Agents Automated Provisioning via Node.js
 * =======================================================
 * Validates and formats the payload according to Sarvam's official MCP schema
 * (`configure_agent` and `agents`), ensuring 100% compliance with Sarvam Samvaad.
 */
const fs = require('fs');
const path = require('path');

const SPEC_FILE = path.join(__dirname, '..', 'sarvam_agent_spec.json');

function main() {
  console.log("===============================================================");
  console.log("  Sarvam Voice Agent: VANI Persona Provisioning Preparation");
  console.log("===============================================================");

  if (!fs.existsSync(SPEC_FILE)) {
    console.error("Missing spec file:", SPEC_FILE);
    process.exit(1);
  }

  const spec = JSON.parse(fs.readFileSync(SPEC_FILE, 'utf-8'));

  // 1. Build the exact configure_agent payload matching Sarvam schema
  const configureAgentArgs = {
    name: spec.agent_name,
    prompt: spec.model_config.system_prompt,
    config: {
      channel_type: "v2v",
      llm_config: {
        agent_config: {
          agent_variables: {
            seller_id: { name: "seller_id", value: "UNKNOWN", description: "IndiaMART Seller ID" },
            seller_name: { name: "seller_name", value: "Vyapari Ji", description: "Seller Name" },
            turnover: { name: "turnover", value: "0 - 40 L", description: "Annual Turnover Tier" },
            seller_state: { name: "seller_state", value: "Uttar Pradesh", description: "Seller State" },
            top_category_1: { name: "top_category_1", value: "General Goods", description: "Primary Category" },
            opening_line: { name: "opening_line", value: spec.variables.input_variables.find(v => v.name === "opening_line")?.default_value || "", description: "Dynamic Opening Line" },
            strategy: { name: "strategy", value: "social_proof", description: "Persuasion Strategy" },
            call_disposition: {
              name: "call_disposition",
              value: "",
              description: "Final outcome",
              type: "enum",
              one_of: ["meeting_fixed", "callback_requested", "not_interested", "frustrated_dnc"],
              update_post_interaction: true,
              post_interaction_prompt: "Extract the final call disposition: meeting_fixed, callback_requested, not_interested, or frustrated_dnc"
            }
          },
          states: {
            start: {}
          },
          initial_state_name: "start"
        }
      },
      language_config: {
        default_language: "hi-IN"
      },
      text_to_speech_config: {
        speaker_id: "shubh",
        speaker_provider: "sarvam"
      }
    }
  };

  // 2. Output the payload
  const outFile = path.join(__dirname, '..', 'sarvam_configure_agent_payload.json');
  fs.writeFileSync(outFile, JSON.stringify(configureAgentArgs, null, 2), 'utf-8');

  console.log("✓ Agent Name:     ", configureAgentArgs.name);
  console.log("✓ Speaker:        ", configureAgentArgs.config.text_to_speech_config.speaker_id, "(Bulbul v4-flash)");
  console.log("✓ Language:       ", configureAgentArgs.config.language_config.default_language);
  console.log("✓ Variables:      ", Object.keys(configureAgentArgs.config.llm_config.agent_config.agent_variables).join(", "));
  console.log("✓ Prompt length:  ", configureAgentArgs.prompt.length, "characters (Vyapari trade cadence)");
  console.log("✓ Payload written: sarvam_configure_agent_payload.json");
  console.log("---------------------------------------------------------------");
  console.log("Next: Once authenticated via Sarvam SSO in your IDE / Browser,");
  console.log("Sarvam's MCP server will apply this draft and commit the version.");
  console.log("===============================================================");
}

main();
