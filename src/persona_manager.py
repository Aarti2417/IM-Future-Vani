"""
Persona Manager for IndiaMART Voice Bot (VANI)
Orchestrates dynamic mid-call adaptation of the Voice Bot persona.
Applies behavioral transition rules, hysteresis, guardrails, and audit logging.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import copy
import logging

from src.persona_generator import Persona
from src.signal_detector import DetectedSignal

logger = logging.getLogger(__name__)


@dataclass
class AdaptationEvent:
    turn_number: int
    signal_detected: str
    signal_confidence: float
    cues: List[str]
    changes_made: Dict[str, Any]
    adaptation_rationale: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_number": self.turn_number,
            "signal_detected": self.signal_detected,
            "signal_confidence": round(self.signal_confidence, 2),
            "cues": self.cues,
            "changes_made": self.changes_made,
            "adaptation_rationale": self.adaptation_rationale,
            "previous_state": self.previous_state,
            "new_state": self.new_state
        }


class PersonaManager:
    """Manages active persona state and mid-call adaptations with stability guardrails."""

    def __init__(self, initial_persona: Persona):
        self.initial_persona = copy.deepcopy(initial_persona)
        self.active_persona = copy.deepcopy(initial_persona)
        self.trajectory: List[AdaptationEvent] = []
        self.last_adapted_turn: int = -999  # Turn when last non-neutral change occurred
        self.min_turns_between_shifts: int = 1  # Anti-oscillation guardrail

    def adapt(self, signal: DetectedSignal, turn_number: int) -> Optional[AdaptationEvent]:
        """
        Evaluates detected seller signal and transitions persona parameters.
        Returns AdaptationEvent if a change occurred, or None if kept steady.
        """
        # If None, neutral or very low confidence, keep current persona
        if not signal or signal.signal == "neutral" or signal.confidence < 0.60:
            return None

        # Guardrail: Check hysteresis (except for critical frustration de-escalation)
        if signal.signal != "frustrated" and (turn_number - self.last_adapted_turn < self.min_turns_between_shifts):
            logger.info(f"Skipping shift on turn {turn_number} due to hysteresis stability dampening.")
            return None

        prev_state = {
            "pace": self.active_persona.pace,
            "formality": self.active_persona.formality,
            "tone": self.active_persona.tone,
            "script_strategy": self.active_persona.script_strategy,
            "language_mix": self.active_persona.language_mix
        }
        changes = {}
        rationale_parts = []

        # ── Adaptation Rule 1: RUSHED ─────────────────────────
        if signal.signal == "rushed":
            # Speed up pace (clamped to max 1.18)
            new_pace = min(1.18, round(self.active_persona.pace + 0.12, 2))
            if new_pace != self.active_persona.pace:
                changes["pace"] = {"from": self.active_persona.pace, "to": new_pace}
                self.active_persona.pace = new_pace
            
            # Switch to direct closing or punchy ROI numbers
            if self.active_persona.tone != "direct_closing":
                changes["tone"] = {"from": self.active_persona.tone, "to": "direct_closing"}
                self.active_persona.tone = "direct_closing"
            
            changes["instruction"] = "Strip polite fillers. Deliver 1 key value stat in <= 15 words or offer immediate callback."
            rationale_parts.append("Seller indicated rush/scarcity of time. Accelerated delivery pace and condensed to direct value summary.")

        # ── Adaptation Rule 2: CONFUSED ───────────────────────
        elif signal.signal == "confused":
            # Slow down pace (clamped to min 0.86)
            new_pace = max(0.86, round(self.active_persona.pace - 0.12, 2))
            if new_pace != self.active_persona.pace:
                changes["pace"] = {"from": self.active_persona.pace, "to": new_pace}
                self.active_persona.pace = new_pace
            
            if self.active_persona.tone != "reassuring_patient":
                changes["tone"] = {"from": self.active_persona.tone, "to": "reassuring_patient"}
                self.active_persona.tone = "reassuring_patient"

            # Avoid English jargon if confused
            if self.active_persona.language_mix == "indian_english":
                changes["language_mix"] = {"from": "indian_english", "to": "hinglish"}
                self.active_persona.language_mix = "hinglish"

            changes["instruction"] = "Slow down cadence. Use simple physical market analogy (e.g. 'Jaise aapki dukan pe naye grahak aate hain...')."
            rationale_parts.append("Confusion detected. Decelerated pace, removed technical jargon, and pivoted to patient explanatory tone.")

        # ── Adaptation Rule 3: FRUSTRATED / IRRITATED ──────────
        elif signal.signal == "frustrated":
            # De-escalation takes top priority
            if self.active_persona.tone != "empathetic_problem_solver":
                changes["tone"] = {"from": self.active_persona.tone, "to": "empathetic_problem_solver"}
                self.active_persona.tone = "empathetic_problem_solver"

            if self.active_persona.script_strategy != "problem_solving":
                changes["script_strategy"] = {"from": self.active_persona.script_strategy, "to": "problem_solving"}
                self.active_persona.script_strategy = "problem_solving"

            # Moderate pace so bot sounds respectful and unhurried
            if self.active_persona.pace > 0.92:
                changes["pace"] = {"from": self.active_persona.pace, "to": 0.90}
                self.active_persona.pace = 0.90

            changes["instruction"] = "Cease sales push. Acknowledge frustration sincerely: 'Maaf kijiye sir, pareshan nahi karna chahta tha. Main abhi call disconnect karta hu, kab baat kar sakte hain?'"
            rationale_parts.append("CRITICAL: Frustration detected. Halted commercial pitch; initiated empathetic de-escalation protocol.")

        # ── Adaptation Rule 4: HESITANT / SKEPTICAL ───────────
        elif signal.signal == "hesitant":
            if self.active_persona.script_strategy != "social_proof":
                changes["script_strategy"] = {"from": self.active_persona.script_strategy, "to": "social_proof"}
                self.active_persona.script_strategy = "social_proof"

            if self.active_persona.tone not in ["consultative", "reassuring_patient"]:
                changes["tone"] = {"from": self.active_persona.tone, "to": "consultative"}
                self.active_persona.tone = "consultative"

            changes["instruction"] = "Provide risk-free peer evidence: Share how nearby verified sellers in their category are receiving buyer requirements."
            rationale_parts.append("Hesitation detected. Switched to localized social proof to build confidence without pressure.")

        # ── Adaptation Rule 5: ENGAGED / INTERESTED ───────────
        elif signal.signal == "engaged":
            if self.active_persona.tone != "consultative":
                changes["tone"] = {"from": self.active_persona.tone, "to": "consultative"}
                self.active_persona.tone = "consultative"

            # Maintain natural rhythm, guide to concrete booking
            changes["instruction"] = "Seller is receptive. Answer their exact question crisply, then suggest a 5-minute online walkthrough."
            rationale_parts.append("Seller showed active interest. Reinforced consultative partnership and framed clear next step.")

        # ── Adaptation Rule 6: INTERRUPTED (Barge-in) ─────────
        elif signal.signal == "interrupted":
            changes["instruction"] = "Immediately pause. Acknowledge their point: 'Ji boliye sir, main sun raha hu.'"
            rationale_parts.append("Seller interrupted previous bot speech. Yielded floor immediately.")

        # ── Adaptation Rule 7: NOISE ──────────────────────────
        elif signal.signal == "noise":
            changes["instruction"] = "Verify audibility clearly: 'Sir peeche se shor aa raha hai, kya meri aawaz aap tak aa rahi hai?'"
            rationale_parts.append("High background audio interference detected.")

        if not changes:
            return None

        self.last_adapted_turn = turn_number
        new_state = {
            "pace": self.active_persona.pace,
            "formality": self.active_persona.formality,
            "tone": self.active_persona.tone,
            "script_strategy": self.active_persona.script_strategy,
            "language_mix": self.active_persona.language_mix
        }

        event = AdaptationEvent(
            turn_number=turn_number,
            signal_detected=signal.signal,
            signal_confidence=signal.confidence,
            cues=signal.cues_matched,
            changes_made=changes,
            adaptation_rationale=" ".join(rationale_parts),
            previous_state=prev_state,
            new_state=new_state
        )
        self.trajectory.append(event)
        return event

    def get_turn_directive(self, signal: DetectedSignal) -> str:
        """Generates dynamic prompt instructions to steer the bot's immediate next utterance."""
        return (
            f"\n[LIVE PERSONA ADAPTATION DIRECTIVE]\n"
            f"- Detected seller signal: {signal.signal.upper()} (confidence: {signal.confidence:.2f})\n"
            f"- Current Active Pace: {self.active_persona.pace}x\n"
            f"- Current Tone: {self.active_persona.tone}\n"
            f"- Current Formality: {self.active_persona.formality}\n"
            f"- Strategy: {self.active_persona.script_strategy}\n"
            f"- Recommended action: {signal.recommended_action}\n"
            f"Adhere strictly to this delivery style for your next answer.\n"
        )
