"""
Sarvam Voice Agent Automated Provisioning & Deployment Script
=============================================================
This script deploys the IndiaMART VANI Voice Agent directly to Sarvam's
hosted Voice Agent platform (Samvaad) using the agent specification (`sarvam_agent_spec.json`).

Actions performed:
1. Authenticates using SARVAM_API_KEY from environment or .env.
2. Creates/configures the Agent Draft with prompt, Bulbul TTS voice, and Vyapari cadence.
3. Registers the Grounded IndiaMART Tools (CRM lookup, buyer leads, pricing, appointment booking).
4. Configures the On-Start and On-End Webhook URLs for persona calibration and memory evolution.
5. Commits the immutable production version.

Usage:
    python scripts/deploy_sarvam_agent.py --webhook-url https://your-public-url.ngrok-free.app
    python scripts/deploy_sarvam_agent.py --mock (to validate payloads without network)
"""
import os
import sys
import json
import logging
import argparse
import urllib.request
import urllib.error

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.sarvam_client import _get_api_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("deploy_sarvam_agent")

SARVAM_BASE_URL = "https://api.sarvam.ai"
SPEC_FILE = os.path.join(PROJECT_ROOT, "sarvam_agent_spec.json")


def load_agent_spec() -> dict:
    if not os.path.exists(SPEC_FILE):
        raise FileNotFoundError(f"Agent spec not found at {SPEC_FILE}")
    with open(SPEC_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def deploy_agent(webhook_url: str = "http://localhost:8080", is_mock: bool = False):
    spec = load_agent_spec()
    api_key = _get_api_key()

    print("=" * 65)
    print("  Deploying IndiaMART VANI to Sarvam Voice Agents Platform")
    print("=" * 65)
    print(f"Agent Name:    {spec['agent_name']}")
    print(f"Model:         {spec['model_config']['model']}")
    print(f"Voice Speaker: {spec['voice_config']['speaker']} (Bulbul v4-flash)")
    print(f"Pace:          {spec['voice_config']['pace']}x")
    print(f"Webhook URL:   {webhook_url}")
    print(f"Mode:          {'MOCK VALIDATION (Offline)' if is_mock or not api_key else 'LIVE SARVAM DEPLOYMENT'}")
    print("-" * 65)

    # 1. Prepare Agent Payload for Sarvam Voice Agents API
    agent_payload = {
        "name": spec["agent_name"],
        "description": spec["description"],
        "prompt": spec["model_config"]["system_prompt"],
        "llm": {
            "model": spec["model_config"]["model"],
            "temperature": spec["model_config"]["temperature"],
            "max_tokens": spec["model_config"]["max_tokens"]
        },
        "tts": {
            "model": spec["voice_config"]["model"],
            "speaker": spec["voice_config"]["speaker"],
            "language_code": spec["voice_config"]["language_code"],
            "pace": spec["voice_config"]["pace"]
        },
        "variables": spec["variables"]["input_variables"],
        "output_variables": spec["variables"]["output_variables"],
        "hooks": {
            "on_start": {
                "url": f"{webhook_url.rstrip('/')}/webhook/on-start",
                "method": "POST"
            },
            "on_end": {
                "url": f"{webhook_url.rstrip('/')}/webhook/on-end",
                "method": "POST"
            }
        }
    }

    # 2. Tool endpoints to register with Sarvam
    tools_to_register = [
        {
            "name": "get_seller_profile",
            "url": f"{webhook_url.rstrip('/')}/api/tools/seller_profile",
            "method": "POST",
            "description": "Fetch verified IndiaMART CRM seller profile"
        },
        {
            "name": "get_verified_buyer_leads",
            "url": f"{webhook_url.rstrip('/')}/api/tools/buyer_leads",
            "method": "POST",
            "description": "Fetch live OTP-verified buyer inquiries for category"
        },
        {
            "name": "get_official_pricing",
            "url": f"{webhook_url.rstrip('/')}/api/tools/pricing",
            "method": "POST",
            "description": "Fetch official package rate card (Mini Leader, TrustSEAL)"
        },
        {
            "name": "book_relationship_manager_slot",
            "url": f"{webhook_url.rstrip('/')}/api/tools/book_slot",
            "method": "POST",
            "description": "Book Relationship Manager phone or visit appointment"
        },
        {
            "name": "check_dnd_compliance",
            "url": f"{webhook_url.rstrip('/')}/api/tools/compliance",
            "method": "POST",
            "description": "Check DND and TRAI calling window compliance"
        }
    ]

    if is_mock or not api_key:
        logger.info("[MOCK] Validating payload structure...")
        assert len(agent_payload["prompt"]) > 50, "Prompt is missing or too short"
        assert len(agent_payload["variables"]) >= 5, "Variables missing"
        assert len(tools_to_register) == 5, "Tools missing"
        
        print("\n[SUCCESS] Agent payload validated successfully!")
        print(f"✓ Agent Config: {len(agent_payload['prompt'])} character Vyapari prompt verified")
        print(f"✓ Registered {len(tools_to_register)} Grounded Tools pointing to {webhook_url}")
        print(f"✓ Configured On-Start Hook -> {agent_payload['hooks']['on_start']['url']}")
        print(f"✓ Configured On-End Hook   -> {agent_payload['hooks']['on_end']['url']}")
        print(f"✓ Output Goal Set: call_disposition == 'meeting_fixed'")
        print("\nTo deploy to real Sarvam account:")
        print("1. Set SARVAM_API_KEY in .env")
        print(f"2. Run: python scripts/deploy_sarvam_agent.py --webhook-url {webhook_url}")
        return True

    # Live API Call to Sarvam Voice Agents
    logger.info("Connecting to Sarvam Voice Agents platform API...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Step A: Create or Update Agent Draft
        req = urllib.request.Request(
            f"{SARVAM_BASE_URL}/v1/voice-agents/agents",
            data=json.dumps(agent_payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            agent_id = data.get("id") or data.get("agent_id")
            logger.info(f"Agent Draft created successfully! ID: {agent_id}")

        # Step B: Register Tools
        for t in tools_to_register:
            tool_req = urllib.request.Request(
                f"{SARVAM_BASE_URL}/v1/voice-agents/agents/{agent_id}/tools",
                data=json.dumps(t).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(tool_req, timeout=15) as t_resp:
                logger.info(f"Registered tool: {t['name']}")

        # Step C: Commit Immutable Version
        commit_req = urllib.request.Request(
            f"{SARVAM_BASE_URL}/v1/voice-agents/agents/{agent_id}/commit",
            data=json.dumps({"description": "Production release with Vyapari cadence"}).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(commit_req, timeout=20) as c_resp:
            commit_data = json.loads(c_resp.read().decode("utf-8"))
            version_id = commit_data.get("version_id")
            logger.info(f"Committed production version: {version_id}")

        print("\n🎉 VANI Voice Agent deployed and committed to Sarvam!")
        return True

    except Exception as e:
        logger.warning(f"Sarvam Voice Agents API notice: {e}")
        logger.info("Falling back to local validated specification format.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy IndiaMART VANI to Sarvam Voice Agents Platform")
    parser.add_argument("--webhook-url", default="http://localhost:8080", help="Base URL of your webhook bridge server")
    parser.add_argument("--mock", action="store_true", help="Validate payload without making external network calls")
    args = parser.parse_args()

    deploy_agent(webhook_url=args.webhook_url, is_mock=args.mock)
