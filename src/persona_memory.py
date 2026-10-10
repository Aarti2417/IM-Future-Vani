"""
Persona Memory System for IndiaMART Voice Bot (VANI)
Stores successful personas per seller, tracks call outcomes, and evolves
the baseline persona for subsequent calls over time.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import os
import json
import logging
from datetime import datetime

from src.persona_generator import Persona

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(BASE_DIR, "personas", "seller_memory.json")
os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)


@dataclass
class CallRecord:
    call_id: str
    timestamp: str
    disposition: str          # e.g., 'meeting_fixed', 'not_interested', 'callback_requested'
    success: bool             # True if meeting fixed or callback agreed
    initial_persona_state: Dict[str, Any]
    final_persona_state: Dict[str, Any]
    signals_encountered: List[str]
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SellerMemory:
    seller_id: str
    total_calls: int = 0
    successful_calls: int = 0
    preferred_language: Optional[str] = None
    preferred_pace: Optional[float] = None
    preferred_tone: Optional[str] = None
    preferred_strategy: Optional[str] = None
    past_objections_logged: List[str] = field(default_factory=list)
    call_history: List[CallRecord] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["call_history"] = [c.to_dict() if isinstance(c, CallRecord) else c for c in self.call_history]
        return d


class PersonaMemoryStore:
    """Persistent storage and evolution engine for seller personas."""

    def __init__(self, storage_path: str = MEMORY_FILE):
        self.storage_path = storage_path
        self._memories: Dict[str, SellerMemory] = {}
        self._load()

    def _load(self):
        """Loads memory state from JSON storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sid, record in data.items():
                        history = [
                            CallRecord(**h) if isinstance(h, dict) else h
                            for h in record.get("call_history", [])
                        ]
                        self._memories[sid] = SellerMemory(
                            seller_id=record["seller_id"],
                            total_calls=record.get("total_calls", 0),
                            successful_calls=record.get("successful_calls", 0),
                            preferred_language=record.get("preferred_language"),
                            preferred_pace=record.get("preferred_pace"),
                            preferred_tone=record.get("preferred_tone"),
                            preferred_strategy=record.get("preferred_strategy"),
                            past_objections_logged=record.get("past_objections_logged", []),
                            call_history=history,
                            last_updated=record.get("last_updated", "")
                        )
            except Exception as e:
                logger.error(f"Failed to load seller memory from {self.storage_path}: {e}")
                self._memories = {}

    def _save(self):
        """Persists memory state to JSON storage."""
        try:
            out = {sid: mem.to_dict() for sid, mem in self._memories.items()}
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save seller memory: {e}")

    def get_seller_memory(self, seller_id: str) -> Optional[SellerMemory]:
        """Retrieves history for a given seller."""
        return self._memories.get(str(seller_id))

    def record_call(self, seller_id: str, disposition: str,
                    initial_persona: Persona, final_persona: Persona,
                    signals_encountered: List[str], notes: str = "") -> SellerMemory:
        """
        Records a completed call and evolves the seller's learned persona baseline.
        Positive dispositions: 'meeting_fixed', 'online_meeting_fixed', 'callback_requested'.
        """
        sid = str(seller_id)
        if sid not in self._memories:
            self._memories[sid] = SellerMemory(seller_id=sid)

        mem = self._memories[sid]
        mem.total_calls += 1

        is_success = disposition.lower() in [
            "meeting_fixed", "online_meeting_fixed", "callback_requested", "interested"
        ]
        if is_success:
            mem.successful_calls += 1

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        call_rec = CallRecord(
            call_id=f"call_{sid}_{mem.total_calls}_{int(datetime.now().timestamp())}",
            timestamp=now,
            disposition=disposition,
            success=is_success,
            initial_persona_state={
                "pace": initial_persona.pace,
                "tone": initial_persona.tone,
                "formality": initial_persona.formality,
                "language_mix": initial_persona.language_mix,
                "script_strategy": initial_persona.script_strategy
            },
            final_persona_state={
                "pace": final_persona.pace,
                "tone": final_persona.tone,
                "formality": final_persona.formality,
                "language_mix": final_persona.language_mix,
                "script_strategy": final_persona.script_strategy
            },
            signals_encountered=signals_encountered,
            notes=notes
        )
        mem.call_history.append(call_rec)
        mem.last_updated = now

        # Update logged signals
        for sig in signals_encountered:
            if sig not in ["neutral", "noise", "interrupted"] and sig not in mem.past_objections_logged:
                mem.past_objections_logged.append(sig)

        # ── Persona Evolution Logic ───────────────────────────
        # If call was successful, adopt the final adapted persona as learned preferences!
        if is_success:
            # Running average for pace
            if mem.preferred_pace is None:
                mem.preferred_pace = final_persona.pace
            else:
                mem.preferred_pace = round(0.6 * final_persona.pace + 0.4 * mem.preferred_pace, 2)
            
            mem.preferred_language = final_persona.language_mix
            mem.preferred_tone = final_persona.tone
            mem.preferred_strategy = final_persona.script_strategy
        else:
            # If call was unsuccessful and seller was rushed/frustrated, log that for future avoidance
            if "rushed" in signals_encountered and (mem.preferred_pace is None or mem.preferred_pace < 1.05):
                mem.preferred_pace = 1.08
            if "frustrated" in signals_encountered:
                mem.preferred_tone = "empathetic_problem_solver"

        self._save()
        return mem

    def apply_memory_to_persona(self, persona: Persona) -> Persona:
        """
        Enhances a newly generated persona with learned historical memory for this seller.
        """
        mem = self.get_seller_memory(persona.seller_id)
        if not mem or mem.total_calls == 0:
            return persona

        applied_changes = []

        if mem.preferred_pace is not None and abs(persona.pace - mem.preferred_pace) > 0.04:
            old_pace = persona.pace
            persona.pace = mem.preferred_pace
            applied_changes.append(f"Pace updated from {old_pace}x to learned preference {persona.pace}x")

        if mem.preferred_language and mem.preferred_language != persona.language_mix:
            old_lang = persona.language_mix
            persona.language_mix = mem.preferred_language
            applied_changes.append(f"Language mix evolved from {old_lang} to {persona.language_mix}")

        if mem.preferred_tone and mem.successful_calls > 0:
            old_tone = persona.tone
            persona.tone = mem.preferred_tone
            applied_changes.append(f"Tone updated from {old_tone} to proven winning tone '{persona.tone}'")

        if mem.preferred_strategy and mem.successful_calls > 0:
            old_strat = persona.script_strategy
            persona.script_strategy = mem.preferred_strategy
            applied_changes.append(f"Strategy evolved from {old_strat} to proven strategy '{persona.script_strategy}'")

        if applied_changes:
            persona.rationale["memory_evolution"] = (
                f"Memory Evolution (Seller has {mem.total_calls} prior calls, {mem.successful_calls} successful): "
                + "; ".join(applied_changes)
            )

        return persona
