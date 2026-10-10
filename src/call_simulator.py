"""
Call Simulator & Voice Loop for IndiaMART Voice Bot (VANI)
Executes end-to-end simulated calls showcasing persona generation,
real-time signal detection, dynamic mid-call adaptation, TTS audio synthesis,
and persona memory evolution.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import os
import json
import logging
import time

from src.persona_generator import PersonaGenerator, Persona
from src.signal_detector import SignalDetector, DetectedSignal
from src.persona_manager import PersonaManager, AdaptationEvent
from src.persona_memory import PersonaMemoryStore
from src.sarvam_client import get_sarvam_client, MockSarvamClient, SarvamClient

logger = logging.getLogger(__name__)


@dataclass
class TurnRecord:
    turn_index: int
    speaker: str               # 'bot' or 'seller'
    text: str
    signal: Optional[Dict[str, Any]] = None
    adaptation: Optional[Dict[str, Any]] = None
    active_persona: Optional[Dict[str, Any]] = None
    audio_base64: Optional[str] = None
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "speaker": self.speaker,
            "text": self.text,
            "signal": self.signal,
            "adaptation": self.adaptation,
            "active_persona": self.active_persona,
            "audio_base64": self.audio_base64,
            "latency_ms": round(self.latency_ms, 1)
        }


@dataclass
class CallSimulationResult:
    call_id: str
    seller_id: str
    seller_profile: Dict[str, Any]
    initial_persona: Dict[str, Any]
    final_persona: Dict[str, Any]
    disposition: str
    total_turns: int
    adaptations_count: int
    signals_detected: List[str]
    trajectory: List[Dict[str, Any]]
    turns: List[TurnRecord]
    memory_evolution_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "seller_id": self.seller_id,
            "seller_profile": self.seller_profile,
            "initial_persona": self.initial_persona,
            "final_persona": self.final_persona,
            "disposition": self.disposition,
            "total_turns": self.total_turns,
            "adaptations_count": self.adaptations_count,
            "signals_detected": self.signals_detected,
            "trajectory": self.trajectory,
            "turns": [t.to_dict() for t in self.turns],
            "memory_evolution_notes": self.memory_evolution_notes
        }


class CallSimulator:
    """Simulates realistic voice interactions with dynamic mid-call adaptation."""

    def __init__(self, sarvam_client=None, memory_store=None):
        self.sarvam = sarvam_client or get_sarvam_client()
        self.memory_store = memory_store or PersonaMemoryStore()
        self.generator = PersonaGenerator()
        self.detector = SignalDetector()

    def run_simulation(self, seller_data: Dict[str, Any],
                       scripted_turns: Optional[List[Dict[str, Any]]] = None,
                       generate_audio: bool = True) -> CallSimulationResult:
        """
        Runs a complete simulated call with the seller.
        If scripted_turns is provided, walks through the seller responses.
        Otherwise, uses a default dialogue based on the seller's profile.
        """
        seller_id = str(seller_data.get("fk_glusr_usr_id", "UNKNOWN"))
        call_id = f"sim_{seller_id}_{int(time.time())}"

        # 1. Generate Pre-Call Persona
        initial_persona = self.generator.generate_persona(seller_data)

        # 2. Enrich with Persona Memory if available
        initial_persona = self.memory_store.apply_memory_to_persona(initial_persona)

        # 3. Initialize Persona Manager for live tracking
        manager = PersonaManager(initial_persona)

        turns_log: List[TurnRecord] = []
        signals_logged: List[str] = []

        # If no script provided, select default script for this seller archetype
        script = scripted_turns or self._get_default_script(seller_data)

        # Opening bot turn
        opening_text = initial_persona.opening_line
        audio_b64 = None
        t0 = time.time()
        if generate_audio:
            try:
                lang_code = "hi-IN" if initial_persona.language_mix != "indian_english" else "en-IN"
                tts_res = self.sarvam.text_to_speech(
                    text=opening_text,
                    language_code=lang_code,
                    speaker=initial_persona.voice_id,
                    pace=initial_persona.pace
                )
                audio_b64 = tts_res.get("audios", [""])[0] if tts_res.get("audios") else None
            except Exception as e:
                logger.error(f"TTS generation error on opening turn: {e}")

        bot_open_turn = TurnRecord(
            turn_index=1,
            speaker="bot",
            text=opening_text,
            active_persona=manager.active_persona.to_dict(),
            audio_base64=audio_b64,
            latency_ms=(time.time() - t0) * 1000
        )
        turns_log.append(bot_open_turn)

        turn_idx = 2
        final_disposition = "meeting_fixed"

        # Walk through conversational exchange
        for step in script:
            seller_utterance = step.get("seller_text", "")
            acoustic_feats = step.get("acoustic_features", {})

            # A. Signal Detection on Seller Utterance
            signal = self.detector.detect(seller_utterance, acoustic_feats)
            if signal.signal != "neutral":
                signals_logged.append(signal.signal)

            # B. Live Mid-Call Adaptation
            adapt_event = manager.adapt(signal, turn_number=turn_idx)

            seller_turn_rec = TurnRecord(
                turn_index=turn_idx,
                speaker="seller",
                text=seller_utterance,
                signal=signal.to_dict(),
                adaptation=adapt_event.to_dict() if adapt_event else None,
                active_persona=manager.active_persona.to_dict()
            )
            turns_log.append(seller_turn_rec)
            turn_idx += 1

            # C. Generate Bot Response
            # Determine bot's response using either scripted dialogue or contextual template
            bot_reply_text = step.get("bot_reply")
            if not bot_reply_text:
                bot_reply_text = self._synthesize_bot_response(
                    seller_text=seller_utterance,
                    signal=signal,
                    active_persona=manager.active_persona,
                    seller_data=seller_data
                )

            # D. Synthesize Audio for Bot Response with newly adapted persona parameters!
            bot_audio_b64 = None
            t_tts = time.time()
            if generate_audio:
                try:
                    lang_code = "hi-IN" if manager.active_persona.language_mix != "indian_english" else "en-IN"
                    tts_res = self.sarvam.text_to_speech(
                        text=bot_reply_text,
                        language_code=lang_code,
                        speaker=manager.active_persona.voice_id,
                        pace=manager.active_persona.pace
                    )
                    bot_audio_b64 = tts_res.get("audios", [""])[0] if tts_res.get("audios") else None
                except Exception as e:
                    logger.error(f"TTS error on turn {turn_idx}: {e}")

            bot_turn_rec = TurnRecord(
                turn_index=turn_idx,
                speaker="bot",
                text=bot_reply_text,
                active_persona=manager.active_persona.to_dict(),
                audio_base64=bot_audio_b64,
                latency_ms=(time.time() - t_tts) * 1000
            )
            turns_log.append(bot_turn_rec)
            turn_idx += 1

            if step.get("disposition"):
                final_disposition = step["disposition"]

        # 4. Record Call Outcome to Persona Memory
        notes = f"Completed call with {len(manager.trajectory)} persona adaptations."
        mem_record = self.memory_store.record_call(
            seller_id=seller_id,
            disposition=final_disposition,
            initial_persona=initial_persona,
            final_persona=manager.active_persona,
            signals_encountered=signals_logged,
            notes=notes
        )

        memory_notes = (
            f"Seller total calls: {mem_record.total_calls}, Successful: {mem_record.successful_calls}. "
            f"Learned preferred pace: {mem_record.preferred_pace}x, tone: {mem_record.preferred_tone}."
        )

        return CallSimulationResult(
            call_id=call_id,
            seller_id=seller_id,
            seller_profile=seller_data,
            initial_persona=initial_persona.to_dict(),
            final_persona=manager.active_persona.to_dict(),
            disposition=final_disposition,
            total_turns=len(turns_log),
            adaptations_count=len(manager.trajectory),
            signals_detected=list(set(signals_logged)),
            trajectory=[e.to_dict() for e in manager.trajectory],
            turns=turns_log,
            memory_evolution_notes=memory_notes
        )

    def _synthesize_bot_response(self, seller_text: str, signal: DetectedSignal,
                                 active_persona: Persona, seller_data: Dict[str, Any]) -> str:
        """Rule-based contextual bot dialogue generation aligned with active persona."""
        category = seller_data.get("top_category_1", "products")
        state = seller_data.get("seller_state", "aapke area")

        if signal.signal == "rushed":
            return f"Samajh gaya sir. Sirf 1 baat: {category} ke 12 verified buyers is hafte {state} mein order lena chahte hain. Kya main WhatsApp pe catalog bhej du?"

        elif signal.signal == "confused":
            return f"Ji koi baat nahi sir. Jaise mandi mein grahak aate hain, waise hi IndiaMART par buyers direct aapko phone karke {category} ka bulk rate puchte hain."

        elif signal.signal == "frustrated":
            return f"Sir, bilkul sahi keh rahe hain aap, pareshan karne ke liye maafi chahta hu. Main abhi aapka number update kar deta hu taaki bematlab call na aaye. Kya kal 4 baje baat ho sakti hai?"

        elif signal.signal == "hesitant":
            return f"Aapka kehna bilkul sahi hai sir. Lekin pichle mahine aapke jaise 15 suppliers ne yahan se regular orders uthaye hain. Aap bina kisi risk ke ek bar verified leads check kar sakte hain."

        elif signal.signal == "engaged":
            return f"Ji bilkul! Isme aapko daily verified SMS leads milti hain aur buyer direct aapke phone pe call karega. Kya kal subah 11 baje ek 5 minute ka online demo schedule karein?"

        else:
            return f"Ji sir, {category} ke regarding humare paas genuine buy requirements hain. Kya aap bulk orders supply karte hain?"

    def _get_default_script(self, seller_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Returns realistic dialogue steps tailored to seller archetype."""
        showed_frustration = int(seller_data.get("showed_frustration", 0) or 0)
        past_objections = str(seller_data.get("past_objections", "")).lower()

        if showed_frustration == 1:
            return [
                {
                    "seller_text": "Bar bar kyu phone karte ho bhai? Bola na nahi chahiye! Disturb mat karo!",
                    "disposition": "callback_requested"
                },
                {
                    "seller_text": "Acha theek hai, kal 3 baje call karna, abhi main customer ke saath hu.",
                    "disposition": "callback_requested"
                }
            ]
        elif "pricing" in past_objections or "costly" in past_objections:
            return [
                {
                    "seller_text": "IndiaMART bohot costly hai, pehle bhi paise dale the koi fayda nahi hua.",
                    "disposition": "meeting_fixed"
                },
                {
                    "seller_text": "Achha, to leads direct mere phone par aayengi? Kitna kharcha padega?",
                    "disposition": "meeting_fixed"
                },
                {
                    "seller_text": "Theek hai, kal 12 baje demo dikha do.",
                    "disposition": "meeting_fixed"
                }
            ]
        else:
            # Default busy to engaged
            return [
                {
                    "seller_text": "Bolo jaldi, main thoda busy hu, time nahi hai abhi.",
                    "disposition": "meeting_fixed"
                },
                {
                    "seller_text": "Achha, UPVC windows ke kitne buyers hain aapke paas?",
                    "disposition": "meeting_fixed"
                },
                {
                    "seller_text": "Haan WhatsApp pe bhej do aur kal subah call kar lena.",
                    "disposition": "meeting_fixed"
                }
            ]
