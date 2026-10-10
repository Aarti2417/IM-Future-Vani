"""
Sarvam Voice Agent Webhook & Tool Bridge Server
================================================
Provides the HTTP bridge connecting Sarvam's hosted Voice Agent platform
(https://indus.sarvam.ai/samvaad) to IndiaMART VANI's local grounded tools and persona memory.

Endpoints:
- POST /webhook/on-start          -> Pre-call persona calibration & opening line injection
- POST /webhook/on-end            -> Post-call disposition logging & memory evolution
- POST /api/tools/seller_profile  -> CRM seller profile lookup
- POST /api/tools/buyer_leads     -> Live verified OTP buyer inquiries
- POST /api/tools/pricing         -> Official IndiaMART package rate card
- POST /api/tools/book_slot       -> Relationship Manager callback booking
- POST /api/tools/compliance      -> DND & TRAI compliance verification
- GET  /agent-spec                -> Serves the complete Sarvam agent specification JSON
- GET  /health                    -> Healthcheck endpoint
"""
import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.persona_generator import PersonaGenerator
from src.persona_memory import PersonaMemoryStore
from src.sarvam_tools import (
    get_seller_profile,
    get_verified_buyer_leads,
    get_official_pricing,
    book_relationship_manager_slot,
    check_dnd_compliance
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sarvam_webhook_server")

PORT = 8080
generator = PersonaGenerator()
memory_store = PersonaMemoryStore()


class SarvamBridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for Sarvam Voice Agent webhooks and tool calls."""

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._send_json({"status": "healthy", "service": "sarvam-vani-bridge", "port": PORT})
        elif path == "/agent-spec":
            spec_path = os.path.join(PROJECT_ROOT, "sarvam_agent_spec.json")
            if os.path.exists(spec_path):
                with open(spec_path, "r", encoding="utf-8") as f:
                    self._send_json(json.load(f))
            else:
                self._send_json({"error": "sarvam_agent_spec.json not found"}, 404)
        elif path == "/memory":
            memories = {sid: m.to_dict() for sid, m in memory_store._memories.items()}
            self._send_json({"status": "ok", "memories": memories})
        else:
            self._send_json({"error": f"Unknown endpoint: {path}"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self._send_json({"error": f"Malformed JSON: {e}"}, 400)
            return

        # ── 1. ON-START HOOK ────────────────────────────────────
        if path == "/webhook/on-start":
            """
            Fired by Sarvam before the call connects.
            Enriches the call with grounded persona calibration and memory.
            """
            seller_id = str(payload.get("seller_id") or payload.get("phone_number") or "241241351")
            profile = get_seller_profile(seller_id)

            # Generate tailored baseline persona
            persona = generator.generate_persona({
                "fk_glusr_usr_id": seller_id,
                "annual_turnover": profile.get("annual_turnover"),
                "seller_state": profile.get("seller_state"),
                "business_type": profile.get("business_type"),
                "top_category_1": profile.get("top_category"),
                "past_objections": profile.get("past_objections"),
                "showed_frustration": 1 if profile.get("showed_frustration") else 0
            })

            # Apply past cross-call memory if available
            persona = memory_store.apply_memory_to_persona(persona)

            # Return variables to Sarvam to populate agent context
            variables_out = {
                "seller_id": seller_id,
                "seller_name": profile.get("seller_name", "Vyapari Ji"),
                "turnover": profile.get("annual_turnover", "0 - 40 L"),
                "seller_state": profile.get("seller_state", "Uttar Pradesh"),
                "top_category_1": profile.get("top_category", "General Goods"),
                "opening_line": persona.opening_line,
                "strategy": persona.script_strategy,
                "baseline_pace": persona.pace
            }
            logger.info(f"[ON-START] Injected persona for seller {seller_id} -> pace={persona.pace}, strategy={persona.script_strategy}")
            self._send_json({
                "status": "success",
                "variables": variables_out,
                "persona_rationale": persona.rationale
            })

        # ── 2. ON-END HOOK ──────────────────────────────────────
        elif path == "/webhook/on-end":
            """
            Fired by Sarvam after the call ends.
            Persists disposition & outcome into seller memory for continuous evolution.
            """
            seller_id = str(payload.get("seller_id") or "UNKNOWN")
            disposition = str(payload.get("call_disposition") or payload.get("disposition") or "general")
            objection = str(payload.get("primary_objection") or payload.get("objection") or "")
            duration = float(payload.get("duration_sec") or 0.0)

            is_success = disposition in ["meeting_fixed", "callback_requested", "agreed_to_resume"]

            memory_store.record_call_outcome(
                seller_id=seller_id,
                disposition=disposition,
                success=is_success,
                initial_persona={"pace": payload.get("baseline_pace", 0.92)},
                final_persona={"pace": payload.get("final_pace", 0.92)},
                signals=[payload.get("signal", "neutral")],
                notes=f"Primary objection: {objection}. Call duration: {duration}s"
            )

            logger.info(f"[ON-END] Recorded outcome for seller {seller_id} -> disposition={disposition}, success={is_success}")
            self._send_json({
                "status": "recorded",
                "seller_id": seller_id,
                "disposition": disposition,
                "success": is_success
            })

        # ── 3. TOOL ENDPOINTS (Called by Sarvam Agentic Loop) ───
        elif path == "/api/tools/seller_profile":
            seller_id = payload.get("seller_id") or payload.get("phone") or ""
            res = get_seller_profile(seller_id)
            self._send_json(res)

        elif path == "/api/tools/buyer_leads":
            cat = payload.get("category", "General Goods")
            loc = payload.get("state_or_city", "")
            res = get_verified_buyer_leads(cat, loc)
            self._send_json(res)

        elif path == "/api/tools/pricing":
            turnover = payload.get("turnover", "")
            res = get_official_pricing(turnover)
            self._send_json(res)

        elif path == "/api/tools/book_slot":
            sid = payload.get("seller_id", "UNKNOWN")
            date = payload.get("date", "Tomorrow")
            time_slot = payload.get("time_slot", "11:00 AM")
            channel = payload.get("channel", "phone")
            res = book_relationship_manager_slot(sid, date, time_slot, channel)
            self._send_json(res)

        elif path == "/api/tools/compliance":
            sid = payload.get("seller_id", "UNKNOWN")
            res = check_dnd_compliance(sid)
            self._send_json(res)

        else:
            self._send_json({"error": f"Unknown POST endpoint: {path}"}, 404)


def run_server(port: int = PORT):
    server = HTTPServer(("0.0.0.0", port), SarvamBridgeHandler)
    logger.info(f"==================================================")
    logger.info(f"Sarvam Voice Agent Webhook Server running on port {port}")
    logger.info(f"• On-Start Hook:  http://localhost:{port}/webhook/on-start")
    logger.info(f"• On-End Hook:    http://localhost:{port}/webhook/on-end")
    logger.info(f"• Tool APIs:      http://localhost:{port}/api/tools/*")
    logger.info(f"• Agent Spec:     http://localhost:{port}/agent-spec")
    logger.info(f"==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.server_close()


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)
