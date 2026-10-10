"""
Persona Generator for IndiaMART Voice Bot (VANI)
Builds a tailored Voice Persona for a seller before the call starts,
grounded in empirical call evidence, seller turnover, category, state, and past objections.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import logging
import json

from src.sarvam_client import VOICE_CATALOG

logger = logging.getLogger(__name__)

# Turnover classifications
TURNOVER_MICRO = ["0 - 40 L", "0 - 25 L", "0 - 10 L", "Micro"]
TURNOVER_SMALL = ["40 L - 1.5 Cr", "25 - 50 L", "50 L - 1 Cr", "Small"]
TURNOVER_MID = ["1.5 - 5 Cr", "1 - 5 Cr", "Medium"]
TURNOVER_LARGE = ["5 - 25 Cr", "25 - 100 Cr", "100+ Cr", "50+ Cr", "Large", "Enterprise"]

# State language clusters
HINDI_BELT = {
    "Uttar Pradesh", "Bihar", "Madhya Pradesh", "Rajasthan", "Haryana",
    "Delhi", "Himachal Pradesh", "Uttarakhand", "Jharkhand", "Chhattisgarh"
}
WESTERN_BELT = {"Maharashtra", "Gujarat", "Goa"}
SOUTHERN_BELT = {"Karnataka", "Tamil Nadu", "Telangana", "Andhra Pradesh", "Kerala"}
EASTERN_BELT = {"West Bengal", "Odisha", "Assam", "Tripura"}


@dataclass
class Persona:
    """Represents a customized Voice Bot persona configuration."""
    seller_id: str
    voice_id: str
    voice_name: str
    gender: str
    pitch_register: str
    pace: float
    formality: str               # 'respectful_warm', 'formal_corporate', 'casual_friendly'
    tone: str                    # 'consultative', 'direct_closing', 'empathetic_problem_solver', 'reassuring_patient'
    language_mix: str            # 'pure_hindi', 'hinglish', 'indian_english'
    script_strategy: str         # 'social_proof', 'roi_numbers', 'product_features', 'problem_solving'
    opening_line: str
    system_prompt: str
    rationale: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PersonaGenerator:
    """Generates an optimal pre-call persona for any IndiaMART seller."""

    def __init__(self, evidence_store=None):
        self.evidence_store = evidence_store

    def generate_persona(self, seller_data: Dict[str, Any]) -> Persona:
        """
        Main entry point: analyzes seller metadata and past call history
        to generate the optimal baseline persona.
        """
        seller_id = str(seller_data.get("fk_glusr_usr_id", "UNKNOWN"))
        turnover = str(seller_data.get("annual_turnover", "")).strip()
        state = str(seller_data.get("seller_state", "")).strip()
        business_type = str(seller_data.get("business_type", "Proprietorship")).strip()
        category = str(seller_data.get("top_category_1", "General Goods")).strip()
        nature = str(seller_data.get("nature_of_business", "")).strip()
        
        showed_frustration = int(seller_data.get("showed_frustration", 0) or 0)
        past_objections = str(seller_data.get("past_objections", "")).lower()
        past_dispositions = str(seller_data.get("past_dispositions_detailed", "")).lower()
        avg_call_sec = float(seller_data.get("avg_answered_call_sec", 0.0) or 0.0)
        turn_count = int(seller_data.get("turn_count", 0) or 0)

        rationale = {}

        # ── 1. Determine Language Mix ─────────────────────────
        # Grounded in state, business size, and historical patterns
        if turnover in TURNOVER_LARGE or "corporate" in business_type.lower() or "private limited" in business_type.lower() and state in SOUTHERN_BELT:
            language_mix = "indian_english"
            rationale["language_mix"] = (
                f"Selected Indian English: Enterprise turnover ({turnover}) and formal business structure "
                f"({business_type}) in {state} favor executive English communication."
            )
        elif state in HINDI_BELT:
            if turnover in TURNOVER_MICRO and ("statue" in category.lower() or "art" in category.lower() or "handicraft" in category.lower() or "trader" in nature.lower()):
                language_mix = "pure_hindi"
                rationale["language_mix"] = (
                    f"Selected Pure Hindi: Traditional category ({category}) and micro turnover ({turnover}) "
                    f"in {state} show highest receptivity to clear, native Hindi without heavy English jargon."
                )
            else:
                language_mix = "hinglish"
                rationale["language_mix"] = (
                    f"Selected Hinglish: Standard commercial tone in {state}. Blends Hindi syntax "
                    f"with accessible business terminology (leads, buyers, catalog, enquiry)."
                )
        elif state in WESTERN_BELT:
            language_mix = "hinglish"
            rationale["language_mix"] = (
                f"Selected Hinglish: Commercial hubs in {state} (Mumbai/Pune/Ahmedabad) "
                f"rely heavily on conversational Hindi blended with practical trade English."
            )
        elif state in SOUTHERN_BELT or state in EASTERN_BELT:
            language_mix = "indian_english" if turnover not in TURNOVER_MICRO else "hinglish"
            rationale["language_mix"] = (
                f"Selected {language_mix}: Non-Hindi belt region ({state}) performs better "
                f"with clear Indian English or neutral accessible Hinglish."
            )
        else:
            # Fallback
            language_mix = "hinglish"
            rationale["language_mix"] = "Defaulted to Hinglish as most widely understood across urban and semi-urban MSMEs."

        # ── 2. Determine Formality ────────────────────────────
        if turnover in TURNOVER_LARGE or "limited" in business_type.lower():
            formality = "formal_corporate"
            rationale["formality"] = (
                f"Formal Corporate: High turnover ({turnover}) requires professional executive address "
                f"('Sir', 'Aap', structured value propositions)."
            )
        elif showed_frustration == 1 or "complaint" in past_objections or "refusal" in past_objections:
            formality = "respectful_warm"
            rationale["formality"] = (
                "Respectful Warm: Past frustration/refusal detected. Needs respectful deference "
                "('Ji', 'Aap') to prevent defensive pushback."
            )
        elif turnover in TURNOVER_MICRO and avg_call_sec > 180:
            formality = "respectful_warm"
            rationale["formality"] = (
                "Respectful Warm: Small proprietor with steady engagement appreciates polite, "
                "humble, relationship-first communication."
            )
        else:
            formality = "respectful_warm"
            rationale["formality"] = "Respectful Warm ('Aap' and 'Ji') is the proven gold standard across 12k+ IndiaMART calls."

        # ── 3. Determine Pace ─────────────────────────────────
        # Based on empirical data: Slow pace gives 38.9% meeting rate, fast gives 14.5% overall,
        # but enterprise sellers prefer briskness (1.05 - 1.12).
        if turnover in TURNOVER_LARGE:
            pace = 1.05
            rationale["pace"] = (
                f"Pace 1.05x (Crisp): Large turnover ({turnover}). Enterprise callers value time efficiency "
                "and concise briefing."
            )
        elif avg_call_sec < 45 and turn_count > 5:
            # Historically short calls with quick disengagements
            pace = 1.02
            rationale["pace"] = (
                "Pace 1.02x (Brisk): Seller has short call duration history; deliver value hook rapidly."
            )
        elif showed_frustration == 1 or "not ready" in past_objections:
            pace = 0.90
            rationale["pace"] = (
                "Pace 0.90x (Deliberate & Patient): Prior objections/frustration show seller needs room "
                "to absorb and speak without being rushed."
            )
        elif turnover in TURNOVER_MICRO:
            pace = 0.92
            rationale["pace"] = (
                "Pace 0.92x (Patient): Evidence shows micro sellers have +17% higher meeting rate "
                "when pace is steady and unhurried."
            )
        else:
            pace = 0.98
            rationale["pace"] = "Pace 0.98x (Balanced): Moderate conversational cadence suited for general MSME inquiries."

        # ── 4. Determine Tone ─────────────────────────────────
        if showed_frustration == 1 or "explicit disinterest" in past_objections:
            tone = "empathetic_problem_solver"
            rationale["tone"] = (
                "Empathetic Problem Solver: History of disinterest/frustration. Must de-escalate first, "
                "listen to past pain points, and avoid aggressive selling."
            )
        elif "online_meeting_fixed" in past_dispositions or "meeting_fixed" in past_dispositions:
            tone = "consultative"
            rationale["tone"] = (
                "Consultative: Seller has a track record of booking meetings. Acts as trusted growth partner "
                "exploring new expansion opportunities."
            )
        elif turnover in TURNOVER_LARGE:
            tone = "direct_closing"
            rationale["tone"] = (
                "Direct & Focused: Executive profile benefits from direct ROI metrics and clear scheduling."
            )
        elif avg_call_sec > 250:
            tone = "reassuring_patient"
            rationale["tone"] = (
                "Reassuring & Patient: High talk-time seller who appreciates detailed walkthroughs."
            )
        else:
            tone = "consultative"
            rationale["tone"] = "Consultative tone (achieves 33.5% meeting rate in historical evidence)."

        # ── 5. Determine Script Strategy ──────────────────────
        if "pricing" in past_objections or "costly" in past_objections or "budget" in past_objections:
            script_strategy = "roi_numbers"
            rationale["script_strategy"] = (
                "ROI Numbers: Past pricing objections require hard mathematics: cost-per-lead vs margin per closed order."
            )
        elif showed_frustration == 1 or "past experience" in past_objections:
            script_strategy = "problem_solving"
            rationale["script_strategy"] = (
                "Problem Solving: Focus on resolving past grievances, quality of verified buyers, "
                "and risk-free assistance rather than pitching upgrades."
            )
        elif turnover in TURNOVER_MICRO or turnover in TURNOVER_SMALL:
            script_strategy = "social_proof"
            rationale["script_strategy"] = (
                f"Social Proof: Micro/Small sellers in '{category}' respond strongly to peer validation "
                f"('Other sellers in {state} get 15+ verified buyer inquiries weekly')."
            )
        elif turnover in TURNOVER_LARGE:
            script_strategy = "roi_numbers"
            rationale["script_strategy"] = (
                "ROI Numbers: Large businesses demand pipeline volume, buyer verification rates, "
                "and catalog visibility analytics."
            )
        else:
            script_strategy = "product_features"
            rationale["script_strategy"] = (
                "Product Features: Highlight verified buy-leads, TrustSEAL, and catalog indexing."
            )

        # ── 6. Select Voice (Speaker ID, Gender, Pitch Register) ──
        # Speaker selection from Sarvam voice catalog
        if language_mix == "indian_english":
            if turnover in TURNOVER_LARGE:
                voice_id = "sunny_enhi_customer"
                voice_name = "Sunny (Professional / Crisp Metro Register)"
                gender = "male"
                pitch_register = "crisp"
            else:
                voice_id = "ishita_enhi_customer"
                voice_name = "Ishita (Warm / Articulate Register)"
                gender = "female"
                pitch_register = "bright"
        elif tone == "empathetic_problem_solver" or tone == "reassuring_patient":
            voice_id = "ishita_enhi_customer"
            voice_name = "Ishita (Warm / Empathetic Register)"
            gender = "female"
            pitch_register = "warm"
        elif turnover in TURNOVER_MICRO and state in HINDI_BELT:
            voice_id = "shubh_enhi_ads"
            voice_name = "Shubh (Approachable / Friendly Hindi Register)"
            gender = "male"
            pitch_register = "medium"
        else:
            voice_id = "shubh_enhi_ads"
            voice_name = "Shubh (Balanced Commercial Register)"
            gender = "male"
            pitch_register = "medium"

        rationale["voice_selection"] = (
            f"Voice '{voice_name}' (ID: {voice_id}): Selected for {gender} gender, "
            f"{pitch_register} pitch register, aligned with {language_mix} and {tone} tone."
        )

        # ── 7. Generate Opening Line & System Prompt ──────────
        opening_line = self._generate_opening_line(
            category=category,
            state=state,
            formality=formality,
            tone=tone,
            language_mix=language_mix,
            script_strategy=script_strategy,
            gender=gender,
            voice_name=voice_name
        )

        system_prompt = self._build_system_prompt(
            seller_id=seller_id,
            category=category,
            turnover=turnover,
            state=state,
            formality=formality,
            tone=tone,
            language_mix=language_mix,
            script_strategy=script_strategy,
            pace=pace,
            voice_id=voice_id,
            gender=gender,
            voice_name=voice_name
        )

        return Persona(
            seller_id=seller_id,
            voice_id=voice_id,
            voice_name=voice_name,
            gender=gender,
            pitch_register=pitch_register,
            pace=pace,
            formality=formality,
            tone=tone,
            language_mix=language_mix,
            script_strategy=script_strategy,
            opening_line=opening_line,
            system_prompt=system_prompt,
            rationale=rationale,
            metadata={
                "turnover": turnover,
                "category": category,
                "state": state,
                "nature_of_business": nature,
                "business_type": business_type,
                "showed_frustration": showed_frustration
            }
        )

    def _generate_opening_line(self, category: str, state: str, formality: str,
                              tone: str, language_mix: str, script_strategy: str,
                              gender: str = "male", voice_name: str = "Shubh") -> str:
        """Constructs an opening greeting strictly matching the persona's speaker gender."""
        cat_clean = category if category and category != "nan" else "aapke business"
        short_name = voice_name.split("(")[0].strip() or ("Shubh" if gender == "male" else "Vani")
        is_male = (gender or "male").lower() == "male"
        bol_raha = "bol raha hu" if is_male else "bol rahi hu"
        chahunga = "chahunga" if is_male else "chahungi"
        baat_kar = "baat kar raha hu" if is_male else "baat kar rahi hu"

        if tone == "empathetic_problem_solver":
            if language_mix == "pure_hindi":
                return f"Namaskar ji. Main IndiaMART se {short_name} {bol_raha}. Asha hai aap theek honge. Kya aapke paas ek minute ka samay hoga?"
            elif language_mix == "indian_english":
                return f"Hello, good day. This is {short_name} calling from IndiaMART. I hope I am not disturbing you, do you have a quick minute?"
            else:
                return f"Namaste ji, main IndiaMART se {short_name} {bol_raha}. Bas ek minute lena {chahunga}, aapke {cat_clean} ke kaam ke baare mein ek zaroori update thi."

        elif formality == "formal_corporate" or language_mix == "indian_english":
            return f"Hello, good afternoon. This is {short_name} calling from IndiaMART for your business in {cat_clean}. We have fresh verified buyer requirements for you."

        elif language_mix == "pure_hindi":
            return f"Namaskar ji! Main IndiaMART se {short_name} {baat_kar}. Aapke {cat_clean} ke vyapaar ke liye naye kharidaron ke inquiries aaye hain."

        else: # Hinglish default
            if script_strategy == "social_proof":
                return f"Namaste ji! Main IndiaMART se {short_name} {bol_raha}. Aapke area mein {cat_clean} ke kaafi naye verified buyer leads generate hue hain, usi ke baare mein baat karni thi."
            elif script_strategy == "roi_numbers":
                return f"Namaste ji, main IndiaMART se {short_name} {bol_raha}. Aapke {cat_clean} business ke liye pichle hafte 25 se zyada buyer enquiries aayi hain. Kya aap 2 minute baat kar sakte hain?"
            else:
                return f"Namaste ji! Main IndiaMART se {short_name} {bol_raha}. Aapke {cat_clean} ke business ke liye kuch naye buyers ke orders aaye hain. Kya abhi baat ho sakti hai?"

    def _build_system_prompt(self, seller_id: str, category: str, turnover: str,
                             state: str, formality: str, tone: str,
                             language_mix: str, script_strategy: str,
                             pace: float, voice_id: str,
                             gender: str = "male", voice_name: str = "Shubh") -> str:
        """Builds a rich LLM system prompt enforcing the persona constraints and speaker gender agreement."""
        short_name = voice_name.split("(")[0].strip() or ("Shubh" if gender == "male" else "Vani")
        is_male = (gender or "male").lower() == "male"

        formality_guide = {
            "respectful_warm": "Always use 'Aap', 'Ji', and warm respectful phrasing. Never be abrupt or condescending.",
            "formal_corporate": "Use professional executive phrasing ('Sir/Madam', structured points, concise syntax).",
            "casual_friendly": "Use friendly peer tone with polite 'Ji', conversational, relaxed."
        }.get(formality, "Polite and respectful.")

        lang_guide = {
            "pure_hindi": "Speak exclusively in natural, fluent Hindi (Devanagari/Romanized Hindi). Avoid complex English words.",
            "hinglish": "Speak natural Indian Hinglish. Use Hindi grammar mixed with common business words like 'leads', 'buyers', 'orders', 'catalog', 'enquiry', 'verified'.",
            "indian_english": "Speak professional, fluent Indian English. Clear, grammatical, articulate."
        }.get(language_mix, "Hinglish.")

        tone_guide = {
            "consultative": "Act as a trusted business growth consultant. Ask open questions and listen to their needs.",
            "direct_closing": "Be crisp, confident, and action-oriented. Focus on booking a walkthrough meeting or confirming interest.",
            "empathetic_problem_solver": "Listen patiently. Acknowledge frustrations immediately without being defensive. De-escalate tension.",
            "reassuring_patient": "Speak with high patience, repeat points if needed, avoid overwhelming with too much technical information."
        }.get(tone, "Helpful and conversational.")

        strategy_guide = {
            "social_proof": "Cite peer success (e.g. 'Other sellers in your city are getting 15+ weekly inquiries').",
            "roi_numbers": "Highlight direct financial value (cost per lead, buyer order value, return on investment).",
            "product_features": "Explain specific IndiaMART features (TrustSEAL, priority listing, instant SMS leads).",
            "problem_solving": "Focus on lead verification, filtering spam, and dedicated account manager support."
        }.get(script_strategy, "Highlight verified buyers.")

        if is_male:
            gender_rules = (
                f"SPEAKER GENDER (MANDATORY GRAMMAR RULE):\n"
                f"You are a MALE voice executive named {short_name}. In Hindi/Hinglish, you MUST strictly use MASCULINE first-person verb forms for yourself:\n"
                f"- Use 'main bol raha hoon' (NEVER 'bol rahi hoon')\n"
                f"- Use 'main chahta hoon' (NEVER 'chahti hoon')\n"
                f"- Use 'main maafi mangta hoon' (NEVER 'maafi mangti hoon')\n"
                f"- Use 'main kar dunga / kar lunga' (NEVER 'kar dungi / kar lungi')\n"
                f"- Use 'main samajh gaya' (NEVER 'samajh gayi')\n"
                f"Never switch to feminine self-inflections even when speaking to a female caller."
            )
        else:
            gender_rules = (
                f"SPEAKER GENDER (MANDATORY GRAMMAR RULE):\n"
                f"You are a FEMALE voice executive named {short_name}. In Hindi/Hinglish, you MUST strictly use FEMININE first-person verb forms for yourself:\n"
                f"- Use 'main bol rahi hoon' (NEVER 'bol raha hoon')\n"
                f"- Use 'main chahti hoon' (NEVER 'chahta hoon')\n"
                f"- Use 'main maafi mangti hoon' (NEVER 'maafi mangta hoon')\n"
                f"- Use 'main kar dungi / kar lungi' (NEVER 'kar dunga / kar lunga')\n"
                f"- Use 'main samajh gayi' (NEVER 'samajh gaya')"
            )

        return f"""You are {short_name}, an intelligent Voice Executive from IndiaMART calling seller {seller_id}.
{gender_rules}

BUSINESS PROFILE:
- Category: {category}
- Turnover: {turnover}
- State: {state}

YOUR ASSIGNED VOICE PERSONA:
- Language: {language_mix} ({lang_guide})
- Formality: {formality} ({formality_guide})
- Tone: {tone} ({tone_guide})
- Script Strategy: {script_strategy} ({strategy_guide})
- Delivery Pace: {pace}x (keep answers compact, 1-3 sentences per turn for natural phone conversation).

CRITICAL CONVERSATIONAL RULES:
1. Keep each reply short (under 35 words) so it sounds natural on a phone call.
2. Address caller politely with 'Aap / Ji' (or 'Madam/Sir').
3. If the seller sounds rushed, cut straight to the point.
4. If the seller sounds confused, explain simply without jargon.
5. If the seller is angry or irritated, apologize gracefully and ask if you can reconnect later.
6. Always guide the conversation towards a simple next step (e.g. a quick 5-min demo or WhatsApp catalog review)."""
