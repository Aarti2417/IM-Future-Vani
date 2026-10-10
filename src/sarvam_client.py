"""
Sarvam AI Client Module
Wraps all Sarvam API calls (STT, TTS, Chat) with retries, timeouts, and a text-only mock mode.

API Reference (from docs.sarvam.ai):
- TTS: POST /text-to-speech with model=bulbul:v4-flash, speaker=<voice_id>, pace=0.5-2.0
  - Pitch is NOT available on v3/v4-flash (only v2). We map pitch to voice selection instead.
  - Accent is NOT a parameter; mapped to voice selection (regional voices).
- STT: POST /speech-to-text with model=saaras:v3
- Chat: POST /v1/chat/completions with model=sarvam-105b (OpenAI-compatible)

Streaming STT is available via WebSocket but we use per-turn transcription for simplicity.
"""
import os
import json
import time
import base64
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────
SARVAM_BASE_URL = "https://api.sarvam.ai"
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds, doubles each retry
TIMEOUT = 30  # seconds

def _get_api_key() -> str:
    """Load API key from environment. Never hardcode."""
    key = os.environ.get("SARVAM_API_KEY", "")
    if not key:
        # Try loading from .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SARVAM_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return key


class MockSarvamClient:
    """
    Text-only mock mode for testing without audio or network.
    Returns plausible dummy responses for all API methods.
    """

    def text_to_speech(self, text: str, language_code: str = "hi-IN",
                       speaker: str = "shubh_enhi_ads", pace: float = 1.0,
                       model: str = "bulbul:v4-flash") -> Dict[str, Any]:
        """Mock TTS: returns a tiny silent WAV as base64."""
        logger.info(f"[MOCK TTS] speaker={speaker}, pace={pace}, lang={language_code}, text={text[:80]}...")
        # Minimal WAV header (44 bytes of silence)
        import struct
        sample_rate = 22050
        num_samples = int(sample_rate * 0.1)  # 100ms of silence
        data_size = num_samples * 2
        wav = bytearray()
        wav.extend(b'RIFF')
        wav.extend(struct.pack('<I', 36 + data_size))
        wav.extend(b'WAVEfmt ')
        wav.extend(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
        wav.extend(b'data')
        wav.extend(struct.pack('<I', data_size))
        wav.extend(b'\x00' * data_size)
        b64_str = base64.b64encode(bytes(wav)).decode()
        return {
            "audio": b64_str,
            "audios": [b64_str],
            "text": text,
            "speaker": speaker,
            "mock": True
        }

    def speech_to_text(self, audio_data: bytes, language_code: str = "hi-IN",
                       model: str = "saaras:v3") -> Dict[str, Any]:
        """Mock STT: returns a placeholder transcript."""
        logger.info(f"[MOCK STT] lang={language_code}, audio_size={len(audio_data)} bytes")
        return {
            "text": "Haan ji, main sun raha hoon. Kya baat hai?",
            "language": language_code,
            "mock": True
        }

    def chat_completion(self, messages: List[Dict[str, str]],
                        model: str = "sarvam-105b",
                        temperature: float = 0.7,
                        max_tokens: int = 512) -> str:
        """Mock chat: returns a placeholder response."""
        last_msg = messages[-1]["content"] if messages else ""
        logger.info(f"[MOCK CHAT] model={model}, messages={len(messages)}, last={last_msg[:80]}...")
        return "[Mock LLM response] Based on the seller's profile, I would recommend a warm, empathetic approach with medium pace."


class SarvamClient:
    """
    Production Sarvam AI client with retries and timeouts.
    Uses the REST API directly (no SDK dependency).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _get_api_key()
        if not self.api_key:
            raise ValueError(
                "SARVAM_API_KEY not found. Set it in .env or environment variables."
            )
        self._headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, path: str, payload: Dict = None,
                 files: Dict = None) -> Dict:
        """Make an HTTP request with retries and exponential backoff."""
        import requests
        url = f"{SARVAM_BASE_URL}{path}"

        for attempt in range(MAX_RETRIES):
            try:
                if files:
                    # Multipart form data (for STT)
                    headers = {"api-subscription-key": self.api_key}
                    resp = requests.post(url, headers=headers, files=files,
                                        data=payload or {}, timeout=TIMEOUT)
                else:
                    resp = requests.request(method, url, headers=self._headers,
                                            json=payload, timeout=TIMEOUT)

                if resp.status_code == 429:
                    # Rate limited - wait and retry
                    wait = RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"Sarvam API error after {MAX_RETRIES} retries: {e}")
                    raise
                wait = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)

    def text_to_speech(self, text: str, language_code: str = "hi-IN",
                       speaker: str = "shubh_enhi_ads", pace: float = 1.0,
                       model: str = "bulbul:v4-flash") -> Dict[str, Any]:
        """
        Convert text to speech using Bulbul.

        Args:
            text: Text to synthesize (max 2500 chars). Use native script for Indic.
            language_code: BCP-47 code (hi-IN, en-IN, etc.)
            speaker: Voice ID from Bulbul catalog
            pace: Speech speed 0.5-2.0 (default 1.0)
            model: bulbul:v4-flash (recommended) or bulbul:v3

        Returns:
            Dict with 'audio' (base64 encoded WAV) and metadata
        """
        # Clamp pace to valid range
        pace = max(0.5, min(2.0, pace))

        payload = {
            "text": text[:2500],  # API limit
            "language_code": language_code,
            "model": model,
            "speaker": speaker,
            "pace": pace,
        }
        logger.info(f"[TTS] speaker={speaker}, pace={pace}, lang={language_code}")
        return self._request("POST", "/text-to-speech", payload)

    def speech_to_text(self, audio_data: bytes, language_code: str = "hi-IN",
                       model: str = "saaras:v3") -> Dict[str, Any]:
        """
        Transcribe audio using Saaras v3.

        Args:
            audio_data: Raw audio bytes (WAV/MP3)
            language_code: BCP-47 code
            model: saaras:v3

        Returns:
            Dict with 'text' (transcript) and metadata
        """
        files = {
            "file": ("audio.wav", audio_data, "audio/wav")
        }
        data = {
            "language_code": language_code,
            "model": model,
        }
        logger.info(f"[STT] lang={language_code}, audio_size={len(audio_data)}")
        return self._request("POST", "/speech-to-text", files=files, payload=data)

    def chat_completion(self, messages: List[Dict[str, str]],
                        model: str = "sarvam-105b",
                        temperature: float = 0.7,
                        max_tokens: int = 512) -> str:
        """
        Chat completion using Sarvam-105B (OpenAI-compatible).

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            model: sarvam-105b or sarvam-105b-conversations
            temperature: 0.0-2.0
            max_tokens: Max response tokens

        Returns:
            Generated text string
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        logger.info(f"[CHAT] model={model}, msgs={len(messages)}")
        resp = self._request("POST", "/v1/chat/completions", payload)
        # OpenAI-compatible response format
        return resp["choices"][0]["message"]["content"]


def get_client(mock: bool = False) -> "SarvamClient | MockSarvamClient":
    """
    Factory: returns a mock client for testing or a real client for production.
    Auto-detects: if no API key is available, falls back to mock with a warning.
    """
    if mock:
        logger.info("Using mock Sarvam client (text-only mode)")
        return MockSarvamClient()

    try:
        return SarvamClient()
    except ValueError:
        logger.warning("No SARVAM_API_KEY found. Falling back to mock mode.")
        return MockSarvamClient()


# ──────────────────────────────────────────────────────────
# Voice mapping utilities
# ──────────────────────────────────────────────────────────

# Since Bulbul v4-flash does NOT support pitch or accent as parameters,
# we map persona attributes to different voice IDs.

VOICE_CATALOG = {
    # ── Hindi voices by style ──
    "hi_customer_warm_female": "ritu_hi_customer_warm",
    "hi_customer_female": "ritu_hi_customer",
    "hi_sales_female": "ritu_hi_sales",
    "hi_sales_male": "tarun_hi_sales",
    "hi_conversational_male": "aditya_hi_conversational",
    "hi_conversational_female": "shreya_hi_conversational",
    "hi_recovery_female": "priya_hi_recovery",
    "hi_recovery_male": "shubh_hi_recovery",
    "hi_companion_female": "roopa_hi_companion",
    "hi_banking_female": "sanchita_hi_banking",
    "hi_ads_male": "shubh_hi_ads",
    # ── English voices by style ──
    "en_customer_female": "simran_en_customer",
    "en_sales_female": "simran_en_sales",
    "en_conversational_male": "dev_en_conversational",
    "en_conversational_female": "roopa_en_conversational",
    "en_recovery_male": "shubh_en_recovery",
    # ── Hinglish (code-mixed) voices ──
    "enhi_customer_female": "ishita_enhi_customer",
    "enhi_customer_expressive_female": "ishita_enhi_customer_expressive",
    "enhi_companion_female": "sanchita_enhi_companion",
    "enhi_banking_male": "shubh_enhi_banking",
    "enhi_ads_male": "shubh_enhi_ads",
    "enhi_customer_male": "sunny_enhi_customer",
    # ── Regional voices ──
    "ta_narration_male": "gokul_ta_narration",
    "te_conversation_female": "kavitha_te_conversation",
    "mr_conversational_female": "ishita_mr_conversational",
    "bn_conversation_male": "bappa_bn_conversation",
    "gu_conversational_female": "pooja_gu_conversational",
    "pa_customer_male": "anand_pa_customer",
    "kn_conversation_female": "chaitra_kn_conversation",
}

# Maps language preference to BCP-47 code
LANGUAGE_CODES = {
    "hindi": "hi-IN",
    "english": "en-IN",
    "hinglish": "hi-IN",  # Use Hindi code for mixed
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "marathi": "mr-IN",
    "bengali": "bn-IN",
    "gujarati": "gu-IN",
    "punjabi": "pa-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "odia": "od-IN",
}


def select_voice(gender: str, language: str, style: str) -> str:
    """
    Select the best Bulbul v4-flash voice ID based on persona attributes.

    Since pitch and accent are not API parameters on v4-flash,
    we encode persona characteristics (warmth, formality, energy)
    into voice style selection.

    Args:
        gender: "male" or "female"
        language: "hindi", "english", "hinglish", "tamil", etc.
        style: "customer", "sales", "conversational", "recovery", "companion", "banking"

    Returns:
        Bulbul v4-flash voice ID string
    """
    # Build lookup key
    lang_prefix = {
        "hindi": "hi", "english": "en", "hinglish": "enhi",
        "tamil": "ta", "telugu": "te", "marathi": "mr",
        "bengali": "bn", "gujarati": "gu", "punjabi": "pa",
        "kannada": "kn",
    }.get(language, "hi")

    key = f"{lang_prefix}_{style}_{gender}"
    voice = VOICE_CATALOG.get(key)

    if voice:
        return voice

    # Fallback: try without style, then default
    for fallback_style in ["conversational", "customer", "narration"]:
        fallback_key = f"{lang_prefix}_{fallback_style}_{gender}"
        if fallback_key in VOICE_CATALOG:
            return VOICE_CATALOG[fallback_key]

    # Ultimate fallback
    if gender == "female":
        return "ritu_hi_customer" if lang_prefix == "hi" else "simran_en_customer"
    else:
        return "shubh_enhi_ads"


def save_audio(response: Dict, filepath: str):
    """Save TTS response audio to a WAV file."""
    if "audio" in response:
        audio_bytes = base64.b64decode(response["audio"])
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        logger.info(f"Audio saved to {filepath}")
    elif "audios" in response and response["audios"]:
        # Some responses use 'audios' array
        audio_bytes = base64.b64decode(response["audios"][0])
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        logger.info(f"Audio saved to {filepath}")


def get_sarvam_client():
    """Returns a live SarvamClient if API key is configured, else MockSarvamClient."""
    api_key = _get_api_key()
    if api_key:
        try:
            return SarvamClient(api_key=api_key)
        except Exception as e:
            logger.warning(f"Could not initialize live SarvamClient: {e}. Falling back to mock.")
            return MockSarvamClient()
    return MockSarvamClient()

