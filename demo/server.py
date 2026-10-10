"""
Interactive Web Demo Server for IndiaMART VANI Persona Engine
Provides REST API endpoints and serves the modern frontend application.
Uses standard Python http.server for zero external server dependencies.
"""
import os
import sys
import json
import logging
import base64
import time
import re
from typing import Dict, Any, List, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.persona_generator import PersonaGenerator
from src.signal_detector import SignalDetector
from src.persona_manager import PersonaManager
from src.persona_memory import PersonaMemoryStore
from src.call_simulator import CallSimulator
from src.dialogue_engine import DialogueEngine
from src.sarvam_client import get_sarvam_client, MockSarvamClient, VOICE_CATALOG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PORT = 8000
DEMO_DIR = os.path.join(BASE_DIR, "demo")
DATA_DIR = os.path.join(BASE_DIR, "data_sample")
SCENARIOS_DIR = os.path.join(DEMO_DIR, "scenarios")

# Global instances
generator = PersonaGenerator()
detector = SignalDetector()
memory_store = PersonaMemoryStore()
sarvam_client = get_sarvam_client()
simulator = CallSimulator(sarvam_client=sarvam_client, memory_store=memory_store)
dialogue_engine = DialogueEngine(sarvam_client=sarvam_client)


def _build_persona_safely(p_dict, fallback_seller=None):
    if not p_dict or not isinstance(p_dict, dict):
        return generator.generate_persona(fallback_seller or {}) if fallback_seller else None
    from src.persona_generator import Persona
    from dataclasses import fields
    valid_p_fields = {f.name for f in fields(Persona)}
    p_filtered = {k: v for k, v in p_dict.items() if k in valid_p_fields}
    p_filtered.setdefault("seller_id", "UNKNOWN")
    p_filtered.setdefault("voice_id", "shubh_enhi_ads")
    p_filtered.setdefault("voice_name", "Shubh (Friendly)")
    p_filtered.setdefault("gender", "male")
    p_filtered.setdefault("pitch_register", "medium_resonant")
    p_filtered.setdefault("pace", 1.0)
    p_filtered.setdefault("formality", "respectful_warm")
    p_filtered.setdefault("tone", "consultative")
    p_filtered.setdefault("language_mix", "hinglish")
    p_filtered.setdefault("script_strategy", "social_proof")
    p_filtered.setdefault("opening_line", "Namaste ji, main IndiaMART se bol raha hoon.")
    p_filtered.setdefault("system_prompt", "")
    p_filtered.setdefault("rationale", {})
    p_filtered.setdefault("metadata", {})
    try:
        return Persona(**p_filtered)
    except Exception:
        return generator.generate_persona(fallback_seller or {}) if fallback_seller else None


def _build_signal_safely(s_dict, fallback_text=""):
    from src.signal_detector import DetectedSignal
    from dataclasses import fields
    if s_dict and isinstance(s_dict, dict):
        valid_s_fields = {f.name for f in fields(DetectedSignal)}
        s_filtered = {k: v for k, v in s_dict.items() if k in valid_s_fields}
        s_filtered.setdefault("signal", s_dict.get("primary_signal") or s_dict.get("signal") or "neutral")
        s_filtered.setdefault("confidence", float(s_dict.get("confidence", 0.7)))
        s_filtered.setdefault("cues_matched", s_dict.get("evidence") or s_dict.get("cues_matched") or [])
        s_filtered.setdefault("seller_text", fallback_text or s_dict.get("seller_text", ""))
        s_filtered.setdefault("recommended_action", s_dict.get("recommended_action", "maintain_consultative_flow"))
        s_filtered.setdefault("acoustic_context", s_dict.get("acoustic_context", {}))
        try:
            return DetectedSignal(**s_filtered)
        except Exception:
            pass
    return detector.detect(fallback_text or "")


class VaniDemoHandler(SimpleHTTPRequestHandler):
    """Handles static files and API requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DEMO_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/sellers":
            self._send_json(self._get_sellers())
        elif path == "/api/scenarios":
            self._send_json(self._get_scenarios())
        elif path == "/api/memory":
            memories = {sid: m.to_dict() for sid, m in memory_store._memories.items()}
            self._send_json({"status": "ok", "memories": memories})
        elif path == "/api/voices":
            self._send_json({"status": "ok", "catalog": VOICE_CATALOG})
        elif path == "/api/status":
            is_mock = isinstance(sarvam_client, MockSarvamClient)
            self._send_json({
                "status": "ok",
                "sarvam_mode": "mock" if is_mock else "live",
                "evidence_rows": 12788,
                "port": PORT
            })
        elif path == "/api/mcp/status":
            self._send_json({
                "status": "connected",
                "server_name": "indiamart-voice-engine",
                "mcp_version": "2.3.0",
                "protocol": "Model Context Protocol (JSON-RPC 2.0)",
                "active_tools": [
                    "get_seller_profile",
                    "get_verified_buyer_leads",
                    "get_official_pricing",
                    "check_dnd_and_compliance",
                    "book_relationship_manager_slot",
                    "synthesize_speech",
                    "enforce_gender_guardrail"
                ],
                "active_resources": [
                    "indiamart://knowledge/b2b-objection-playbook",
                    "indiamart://pricing/rate-card"
                ]
            })
        else:
            # Fall back to serving static files from DEMO_DIR
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self._send_error(400, f"Invalid JSON payload: {e}")
            return

        try:
            if path == "/api/generate_persona":
                seller = data.get("seller", {})
                persona = generator.generate_persona(seller)
                persona = memory_store.apply_memory_to_persona(persona)
                self._send_json({"status": "ok", "persona": persona.to_dict()})

            elif path == "/api/create_custom_seller":
                prompt_text = data.get("prompt", "").strip()
                if not prompt_text:
                    self._send_error(400, "Missing prompt string")
                    return

                seller = None
                # 1. Try parsing with Sarvam LLM
                try:
                    system_prompt = (
                        "You are an expert IndiaMART CRM profiling assistant. "
                        "Given a user's description of a seller they want to roleplay, extract a structured JSON profile with exactly these keys:\n"
                        "- seller_name (string, e.g. 'Rajesh Kumar')\n"
                        "- top_category_1 (string, main product category, e.g. 'Brass Handicrafts')\n"
                        "- seller_state (string, Indian state, e.g. 'Uttar Pradesh')\n"
                        "- annual_turnover (string: '0 - 40 L', '40 L - 1.5 Cr', '1.5 - 5 Cr', '5 - 25 Cr')\n"
                        "- business_type (string: 'Proprietorship', 'Partnership', or 'Private Limited')\n"
                        "- nature_of_business (string: 'Manufacturer', 'Wholesaler', or 'Trader')\n"
                        "- caller_gender (string: 'male' or 'female')\n"
                        "- initial_mood (string: 'calm', 'curious', 'skeptical', 'rushed', or 'angry')\n"
                        "- personality_summary (string, 1 short sentence summarizing personality and secret trigger)\n"
                        "- past_objections (string, e.g. 'loss_in_past', 'price_concern', 'none')\n"
                        "- showed_frustration (int, 0 or 1)\n\n"
                        "Return ONLY valid JSON. No markdown fences."
                    )
                    resp = sarvam_client._request("POST", "/v1/chat/completions", {
                        "model": "sarvam-105b-conversations",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt_text}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 300
                    })
                    raw_json = resp["choices"][0]["message"].get("content", "").strip()
                    if raw_json.startswith("```"):
                        raw_json = re.sub(r"^```(?:json)?\n?", "", raw_json)
                        raw_json = re.sub(r"\n?```$", "", raw_json)
                    seller = json.loads(raw_json)
                except Exception as e:
                    logger.warning(f"Sarvam prompt extraction fallback used: {e}")

                # 2. Resilient Heuristic Fallback
                if not seller or not isinstance(seller, dict):
                    low = prompt_text.lower()
                    is_female = any(w in low for w in ["female", "woman", "girl", "lady", "mahila", "ananya", "priya", "pooja", "sunita"])
                    state = "Gujarat" if ("surat" in low or "gujarat" in low) else ("Rajasthan" if ("jaipur" in low or "rajasthan" in low) else ("Maharashtra" if ("mumbai" in low or "pune" in low) else ("Delhi" if "delhi" in low else "Uttar Pradesh")))
                    cat = "Textiles & Cotton" if any(w in low for w in ["textile", "saree", "fabric", "cotton", "cloth", "garment"]) else ("Brass Handicrafts" if ("brass" in low or "handicraft" in low) else ("Industrial Goods" if ("industry" in low or "machine" in low) else "General Goods"))
                    turnover = "5 - 25 Cr" if ("cr" in low and any(d in low for d in ["5", "10", "15", "20"])) else ("1.5 - 5 Cr" if "cr" in low else ("40 L - 1.5 Cr" if any(w in low for w in ["lakh", "l"]) else "40 L - 1.5 Cr"))
                    seller = {
                        "seller_name": "Sonia Sharma" if is_female else "Rajesh Patel",
                        "top_category_1": cat,
                        "seller_state": state,
                        "annual_turnover": turnover,
                        "business_type": "Partnership" if "partnership" in low else "Proprietorship",
                        "nature_of_business": "Manufacturer" if "manufactur" in low else "Trader",
                        "caller_gender": "female" if is_female else "male",
                        "initial_mood": "calm",
                        "personality_summary": prompt_text[:120],
                        "past_objections": "loss_in_past" if ("cheated" in low or "loss" in low or "paisa" in low) else "none",
                        "showed_frustration": 1 if ("angry" in low or "gussa" in low or "irritat" in low) else 0
                    }

                seller["fk_glusr_usr_id"] = f"ROLEPLAY_{int(time.time())}"
                seller.setdefault("bot_answered", 1)
                seller.setdefault("avg_answered_call_sec", 65.0)
                seller.setdefault("turn_count", 3)

                # Generate tailored persona for this seller
                persona = generator.generate_persona(seller)
                persona = memory_store.apply_memory_to_persona(persona)

                self._send_json({
                    "status": "ok",
                    "seller": seller,
                    "persona": persona.to_dict(),
                    "roleplay_brief": {
                        "name": seller.get("seller_name", "Seller"),
                        "category": seller.get("top_category_1", "General Goods"),
                        "location": seller.get("seller_state", "India"),
                        "turnover": seller.get("annual_turnover", "40 L - 1.5 Cr"),
                        "nature": seller.get("nature_of_business", "Manufacturer"),
                        "gender": seller.get("caller_gender", "male"),
                        "personality_summary": seller.get("personality_summary", ""),
                        "opening_line": persona.opening_line
                    }
                })

            elif path == "/api/detect_signal":
                text = data.get("text", "")
                acoustic = data.get("acoustic_features", {})
                sig = detector.detect(text, acoustic)
                self._send_json({"status": "ok", "signal": sig.to_dict()})

            elif path == "/api/adapt":
                active_persona_data = data.get("active_persona", {})
                signal_data = data.get("signal", {})
                turn_number = int(data.get("turn_number", 1))

                from src.persona_generator import Persona
                from src.signal_detector import DetectedSignal
                from dataclasses import fields

                persona_obj = _build_persona_safely(active_persona_data, data.get("seller", {}))
                sig_obj = _build_signal_safely(signal_data, data.get("seller_text", ""))

                mgr = PersonaManager(persona_obj)
                event = mgr.adapt(sig_obj, turn_number)

                self._send_json({
                    "status": "ok",
                    "adapted": event is not None,
                    "event": event.to_dict() if event else None,
                    "new_persona": mgr.active_persona.to_dict()
                })

            elif path == "/api/simulate":
                seller = data.get("seller", {})
                script = data.get("script", None)
                gen_audio = data.get("generate_audio", True)
                result = simulator.run_simulation(seller, scripted_turns=script, generate_audio=gen_audio)
                self._send_json({"status": "ok", "simulation": result.to_dict()})

            elif path == "/api/tts":
                text = data.get("text", "")
                speaker = data.get("speaker", "shubh_enhi_ads")
                pace = float(data.get("pace", 1.0))
                lang = data.get("language_code", "hi-IN")
                res = sarvam_client.text_to_speech(
                    text=text,
                    language_code=lang,
                    speaker=speaker,
                    pace=pace
                )
                b64 = res.get("audios", [""])[0] if res.get("audios") else res.get("audio", "")
                self._send_json({"status": "ok", "audio_base64": b64, "speaker": speaker, "pace": pace})

            elif path == "/api/stt":
                audio_b64 = data.get("audio_base64", "")
                lang_code = data.get("language_code", "hi-IN")
                transcript = ""
                if audio_b64:
                    try:
                        audio_bytes = base64.b64decode(audio_b64)
                        stt_res = sarvam_client.speech_to_text(audio_data=audio_bytes, language_code=lang_code)
                        transcript = stt_res.get("text", "")
                    except Exception as err:
                        logger.warning(f"STT failed: {err}")
                self._send_json({"status": "ok", "text": transcript})

            elif path == "/api/generate_reply":
                seller_text = data.get("seller_text", "")
                seller = data.get("seller", {})
                active_persona_data = data.get("active_persona", {})
                signal_data = data.get("signal", {})
                history = data.get("history", [])
                gen_audio = data.get("generate_audio", True)

                persona_obj = _build_persona_safely(active_persona_data, seller)
                sig_obj = _build_signal_safely(signal_data, seller_text)

                reply_text = dialogue_engine.generate_reply(
                    seller_text=seller_text,
                    history=history,
                    seller_profile=seller,
                    active_persona=persona_obj,
                    signal=sig_obj
                )

                audio_b64 = None
                if gen_audio and reply_text:
                    try:
                        spk = persona_obj.voice_id if persona_obj else "shubh_enhi_ads"
                        pce = persona_obj.pace if persona_obj else 1.0
                        lng = "en-IN" if (persona_obj and persona_obj.language_mix == "indian_english") else "hi-IN"
                        tts_res = sarvam_client.text_to_speech(
                            text=reply_text,
                            language_code=lng,
                            speaker=spk,
                            pace=pce
                        )
                        audio_b64 = tts_res.get("audios", [""])[0] if tts_res.get("audios") else tts_res.get("audio", "")
                    except Exception as err:
                        logger.warning(f"TTS failed for reply: {err}")

                self._send_json({
                    "status": "ok",
                    "reply_text": reply_text,
                    "audio_base64": audio_b64,
                    "signal": sig_obj.to_dict() if sig_obj else None,
                    "speaker": persona_obj.voice_id if persona_obj else "shubh_enhi_ads",
                    "pace": persona_obj.pace if persona_obj else 1.0
                })

            elif path == "/api/memory/reset":
                memory_store._memories = {}
                memory_store._save()
                self._send_json({"status": "ok", "message": "Memory reset successfully"})

            else:
                self._send_error(404, f"Endpoint {path} not found")

        except Exception as e:
            logger.error(f"Error handling POST {path}: {e}", exc_info=True)
            self._send_error(500, str(e))

    def _get_sellers(self) -> Dict[str, Any]:
        path = os.path.join(DATA_DIR, "sellers.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return {"status": "ok", "sellers": json.load(f)}
        return {"status": "ok", "sellers": []}

    def _get_scenarios(self) -> Dict[str, Any]:
        scenarios = []
        if os.path.exists(SCENARIOS_DIR):
            for fname in sorted(os.listdir(SCENARIOS_DIR)):
                if fname.endswith(".json"):
                    with open(os.path.join(SCENARIOS_DIR, fname), "r", encoding="utf-8") as f:
                        scenarios.append(json.load(f))
        return {"status": "ok", "scenarios": scenarios}

    def _send_json(self, data: Dict[str, Any]):
        out = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(out)

    def _send_error(self, code: int, message: str):
        out = json.dumps({"status": "error", "message": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(out)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Quiet standard HTTP access logging to prevent noisy terminal
        pass


def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, VaniDemoHandler)
    print(f"============================================================")
    print(f"  IndiaMART VANI Voice Persona Demo Server Started!")
    print(f"  URL: http://localhost:{PORT}")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
