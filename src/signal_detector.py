"""
Signal Detector for IndiaMART Voice Bot (VANI)
Analyzes seller utterances in real-time to detect behavioral signals:
- rushed (time-pressed / busy)
- confused (unclear / bewildered)
- frustrated (irritated / hostile)
- hesitant (skeptical / doubtful)
- engaged (interested / inquisitive)
- interrupted (barge-in / cut-off)
- background_noise (high environmental disturbance)

Designed for ultra-low latency (<10ms) per conversational turn.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class DetectedSignal:
    signal: str                 # 'rushed', 'confused', 'frustrated', 'hesitant', 'engaged', 'interrupted', 'noise', 'neutral'
    confidence: float           # 0.0 to 1.0
    cues_matched: List[str]     # Specific words/patterns that triggered detection
    seller_text: str            # Raw utterance
    recommended_action: str     # What adaptation is suggested
    acoustic_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal": self.signal,
            "confidence": round(self.confidence, 2),
            "cues_matched": self.cues_matched,
            "seller_text": self.seller_text,
            "recommended_action": self.recommended_action,
            "acoustic_context": self.acoustic_context
        }


class SignalDetector:
    """Real-time utterance behavioral signal classifier."""

    # Curated regex patterns for Indian B2B seller conversations (Hindi, Hinglish, English)
    PATTERNS = {
        "rushed": [
            r"\b(jaldi|jaldi bolo|quick|quickly|time nahi|samay nahi|busy|driving|gaadi chala|meeting|later|baad me|phir karo|call later|ab nahi|fursat nahi)\b",
            r"\b(ek minute|2 minute|short me bolo|batao jaldi|ruk nahi sakta|bheed|grahak khada|customer khada)\b"
        ],
        "confused": [
            r"\b(kya matlab|samajh nahi|kaun bol raha|kiska call|kya bola|kya hai ye|samajh nahi aaya|samajh nahi aya|kon ho|kaha se|kis company|kya chiz|hein\?|hain\?|repeat karo)\b",
            r"\b(who is this|what do you mean|dont understand|didnt get you|which company)\b"
        ],
        "frustrated": [
            r"\b(bar bar|baar baar|disturb mat|pareshan|bakwas|time pass|bekar|fraud|complaint|nahi chahiye bola na|nahi chahiye|kitni baar bologe|phone rakho|kat do|gussa|chup|band karo|faltu)\b",
            r"\b(stop calling|dont call|harassment|annoying|useless|rubbish|hang up)\b"
        ],
        "hesitant": [
            r"\b(sochna padega|baad me dekhenge|pata nahi|costly|mehnga|zyada paise|bharosa nahi|faayda nahi hua|fayda nahi|pehle bhi liya tha|doubt|dekhte hai|zarurat nahi lagti|paise doob|nuksan|free wala)\b",
            r"\b(not sure|maybe later|too expensive|wasted money|did not work)\b"
        ],
        "engaged": [
            r"\b(bataiye|batao|kitna kharcha|kitne paise|kaise kaam karta|leads kaise|buyers kaun|achha|theek hai|suniye|process kya hai|interested|bhejiye|whatsapp pe bhejo|demo do)\b",
            r"\b(tell me more|how much does it cost|send details|share quotation|sounds good|yes explain)\b"
        ]
    }

    # Devanagari Hindi cues for authentic Indian MSME trade interactions
    DEVANAGARI_CUES = {
        "frustrated": [
            "बार बार", "परेशान", "बकवास", "टाइम पास", "बेकार", "फ्रॉड", "नहीं चाहिए बोला ना", "नहीं चाहिए",
            "फोन रखो", "काट दो", "काटो", "बंद करो", "फालतू", "दिमाग खराब", "गुस्सा", "कॉल मत करो", "फोन मत करो"
        ],
        "rushed": [
            "जल्दी", "टाइम नहीं", "समय नहीं", "फुर्सत नहीं", "व्यस्त", "बिजी", "ड्राइविंग", "गाड़ी चला",
            "बाद में", "एक मिनट", "दो मिनट", "भीड़", "ग्राहक खड़ा", "कस्टमर खड़ा", "काउंटर पे", "दुकान पे हूँ", "दुकान पर हूँ"
        ],
        "confused": [
            "क्या मतलब", "समझ नहीं", "कौन बोल रहा", "किसका फोन", "किसका कॉल", "क्या बोला", "कहाँ से",
            "क्या चीज", "क्या चीज़", "हैं?", "रिपीट करो", "किस कंपनी", "कौन हो"
        ],
        "hesitant": [
            "सोचना पड़ेगा", "बाद में देखेंगे", "पता नहीं", "महंगा", "ज्यादा पैसे", "भरोसा नहीं", "फायदा नहीं",
            "पहले भी लिया", "पैसे डूब", "नुकसान", "शक", "जरूरत नहीं", "फ्री वाला"
        ],
        "engaged": [
            "बताइए", "बताओ", "कितना खर्चा", "कितना पैसा", "रेट क्या", "भाव क्या", "कैसे काम", "अच्छा",
            "ठीक है", "व्हाट्सएप पर", "डिटेल भेजो", "भेज दीजिए", "सुनिए", "इंटरेस्टेड"
        ]
    }

    ACTION_MAP = {
        "rushed": "Increase pace (+0.12x), remove filler/polite preambles, offer 30-sec pitch or immediate callback.",
        "confused": "Decrease pace (-0.12x), simplify words, use everyday physical market analogy (mandi/dukaan).",
        "frustrated": "De-escalate immediately: apologize sincerely, yield conversational control, ask permission to reschedule.",
        "hesitant": "Pivot to Social Proof & verified metrics; address risk without being pushy.",
        "engaged": "Maintain consultative flow, provide crisp answers, drive toward demo/catalog walkthrough.",
        "interrupted": "Yield floor immediately, listen without speaking over the seller.",
        "noise": "Increase clarity and volume, check audibility ('Kya meri aawaz saaf aa rahi hai?').",
        "neutral": "Continue current conversational persona baseline."
    }

    def detect(self, text: str, acoustic_features: Optional[Dict[str, Any]] = None) -> DetectedSignal:
        """
        Classifies the seller utterance and returns DetectedSignal.
        Supports both text transcripts and audio features (e.g. interruption flag, SNR).
        """
        if not text and not acoustic_features:
            return DetectedSignal(
                signal="neutral",
                confidence=0.5,
                cues_matched=[],
                seller_text="",
                recommended_action=self.ACTION_MAP["neutral"]
            )

        text_clean = text.lower().strip() if text else ""
        raw_text = text.strip() if text else ""
        acoustic = acoustic_features or {}

        # 1. Check for physical barge-in / interruption
        if acoustic.get("interrupted", False):
            return DetectedSignal(
                signal="interrupted",
                confidence=0.95,
                cues_matched=["interruption_event"],
                seller_text=text,
                recommended_action=self.ACTION_MAP["interrupted"],
                acoustic_context=acoustic
            )

        # 2. Check for heavy background noise
        if acoustic.get("snr_db", 30) < 10 or acoustic.get("background_noise_level", "low") == "high":
            return DetectedSignal(
                signal="noise",
                confidence=0.85,
                cues_matched=["low_snr_or_market_noise"],
                seller_text=text,
                recommended_action=self.ACTION_MAP["noise"],
                acoustic_context=acoustic
            )

        # 3. Match linguistic patterns (Priority order: Frustrated > Rushed > Confused > Hesitant > Engaged)
        for signal_name in ["frustrated", "rushed", "confused", "hesitant", "engaged"]:
            matched_cues = []

            # 3a. Latin / Hinglish regex matching
            for pat in self.PATTERNS.get(signal_name, []):
                matches = re.findall(pat, text_clean)
                if matches:
                    matched_cues.extend(matches)

            # 3b. Devanagari Hindi cues matching
            for dev_cue in self.DEVANAGARI_CUES.get(signal_name, []):
                if dev_cue in raw_text:
                    matched_cues.append(dev_cue)

            if matched_cues:
                confidence = min(0.95, 0.70 + 0.12 * len(matched_cues))
                return DetectedSignal(
                    signal=signal_name,
                    confidence=confidence,
                    cues_matched=list(set(matched_cues)),
                    seller_text=text,
                    recommended_action=self.ACTION_MAP[signal_name],
                    acoustic_context=acoustic
                )

        # 4. Short clipped utterances heuristic
        word_count = len(text_clean.split())
        if 0 < word_count <= 3 and any(w in text_clean or w in raw_text for w in ["haan", "bolo", "hmmm", "accha", "ji", "हाँ", "हां", "बोलो", "अच्छा", "जी"]):
            return DetectedSignal(
                signal="engaged",
                confidence=0.65,
                cues_matched=["short_affirmative"],
                seller_text=text,
                recommended_action=self.ACTION_MAP["engaged"],
                acoustic_context=acoustic
            )

        # 5. Fallback neutral
        return DetectedSignal(
            signal="neutral",
            confidence=0.70,
            cues_matched=[],
            seller_text=text,
            recommended_action=self.ACTION_MAP["neutral"],
            acoustic_context=acoustic
        )
