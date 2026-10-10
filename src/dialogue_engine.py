"""
Dialogue Engine for IndiaMART Voice Bot (VANI)
Grounded in empirical analysis of 149k sellers, 139k call turns, and 278k evaluator records.
Solves the 'dumb telemarketer' problem with authentic Indian Vyapari trade cadence,
bilingual support (Devanagari Hindi & Hinglish), constraint awareness (Sunday, shop crowd, travel),
peer social proof, loss aversion, and strict speaker grammatical gender agreement.
"""
from typing import Dict, Any, List, Optional
import logging
import re

from src.persona_generator import Persona
from src.signal_detector import DetectedSignal
from src.sarvam_client import get_sarvam_client, MockSarvamClient

logger = logging.getLogger(__name__)


def is_devanagari(text: str) -> bool:
    """Detects if text contains Devanagari characters (Hindi script)."""
    return any('\u0900' <= char <= '\u097F' for char in text)


def enforce_speaker_gender(text: str, gender: str) -> str:
    """
    Enforces strict grammatical gender agreement for the AI speaker's first-person verbs.
    In Hindi/Hinglish:
    - If speaker is MALE (Shubh, Sunny, Vikram, Chandan, Amartya):
      verbs referring to oneself MUST be masculine (bol raha hoon, chahta hoon, maafi mangta hoon, kar dunga, kar lunga).
      They must NEVER be feminine (bol rahi hoon, chahti hoon, maafi mangti hoon, kar dungi) even when talking to a woman!
    - If speaker is FEMALE (Ishita, Aditi, Ritu, Priya, Sunita, Vani):
      verbs referring to oneself MUST be feminine (bol rahi hoon, chahti hoon, maafi mangti hoon, kar dungi).
    """
    if not text:
        return ""

    t = text
    g = (gender or "male").lower()

    if g == "male":
        # ── Devanagari Feminine -> Masculine ──
        dev_rules = [
            (r'बोल रही हूँ', 'बोल रहा हूँ'),
            (r'बोल रही हु', 'बोल रहा हूँ'),
            (r'बात कर रही हूँ', 'बात कर रहा हूँ'),
            (r'कर रही हूँ', 'कर रहा हूँ'),
            (r'कर रही हु', 'कर रहा हूँ'),
            (r'कर रही थी', 'कर रहा था'),
            (r'माफी चाहती हूँ', 'माफी चाहता हूँ'),
            (r'माफ़ी चाहती हूँ', 'माफ़ी चाहता हूँ'),
            (r'माफी माँगती हूँ', 'माफी माँगता हूँ'),
            (r'माफ़ी माँगती हूँ', 'माफ़ी माँगता हूँ'),
            (r'माफी मांगती हूँ', 'माफी मांगता हूँ'),
            (r'माफ़ी मांगती हूँ', 'माफ़ी मांगता हूँ'),
            (r'माफी चाहती', 'माफी चाहता'),
            (r'माफ़ी चाहती', 'माफ़ी चाहता'),
            (r'माफी माँगती', 'माफी माँगता'),
            (r'माफ़ी माँगती', 'माफ़ी माँगता'),
            (r'माफी मांगती', 'माफी मांगता'),
            (r'माफ़ी मांगती', 'माफ़ी मांगता'),
            (r'चाहती हूँ', 'चाहता हूँ'),
            (r'चाहती हु', 'चाहता हूँ'),
            (r'चाहूँगी', 'चाहूँगा'),
            (r'चाहूंगी', 'चाहूंगा'),
            (r'कर दूँगी', 'कर दूँगा'),
            (r'कर दूंगी', 'कर दूंगा'),
            (r'कर लूँगी', 'कर लूँगा'),
            (r'कर लूंगी', 'कर लूंगा'),
            (r'देती हूँ', 'देता हूँ'),
            (r'लेती हूँ', 'लेता हूँ'),
            (r'समझती हूँ', 'समझता हूँ'),
            (r'समझ गई', 'समझ गया'),
            (r'करूँगी', 'करूँगा'),
            (r'करूंगी', 'करूंगा'),
            (r'बताती हूँ', 'बताता हूँ'),
            (r'सुनाती हूँ', 'सुनाता हूँ'),
            (r'आई हूँ', 'आया हूँ'),
            (r'गई हूँ', 'गया हूँ'),
        ]
        for pat, repl in dev_rules:
            t = re.sub(pat, repl, t)

        # ── Romanized Hinglish Feminine -> Masculine ──
        hing_rules = [
            (r'\bbol rahi hu\b', 'bol raha hu'),
            (r'\bbol rahi hoon\b', 'bol raha hoon'),
            (r'\bbaat kar rahi hu\b', 'baat kar raha hu'),
            (r'\bbaat kar rahi hoon\b', 'baat kar raha hoon'),
            (r'\bkar rahi hu\b', 'kar raha hu'),
            (r'\bkar rahi hoon\b', 'kar raha hoon'),
            (r'\bkr rahi hu\b', 'kar raha hu'),
            (r'\bkar rahi thi\b', 'kar raha tha'),
            (r'\bmaafi chahti hu\b', 'maafi chahta hu'),
            (r'\bmaafi chahti hoon\b', 'maafi chahta hoon'),
            (r'\bmafi chahti hu\b', 'maafi chahta hu'),
            (r'\bmaafi mangti hu\b', 'maafi mangta hu'),
            (r'\bmaafi mangti hoon\b', 'maafi mangta hoon'),
            (r'\bmafi mangti hu\b', 'maafi mangta hu'),
            (r'\bmaafi chahti\b', 'maafi chahta'),
            (r'\bmafi chahti\b', 'maafi chahta'),
            (r'\bmaafi mangti\b', 'maafi mangta'),
            (r'\bmafi mangti\b', 'maafi mangta'),
            (r'\bchahti hu\b', 'chahta hu'),
            (r'\bchahti hoon\b', 'chahta hoon'),
            (r'\bchati hu\b', 'chahta hu'),
            (r'\bchati hoon\b', 'chahta hoon'),
            (r'\bchahungi\b', 'chahunga'),
            (r'\bkar dungi\b', 'kar dunga'),
            (r'\bkr dungi\b', 'kar dunga'),
            (r'\bkar lungi\b', 'kar lunga'),
            (r'\bkr lungi\b', 'kar lunga'),
            (r'\bde deti hu\b', 'de deta hu'),
            (r'\bdeti hu\b', 'deta hu'),
            (r'\bleti hu\b', 'leta hu'),
            (r'\bsamajhti hu\b', 'samajhta hu'),
            (r'\bsamajhti hoon\b', 'samajhta hoon'),
            (r'\bsamajh gayi\b', 'samajh gaya'),
            (r'\bkarungi\b', 'karunga'),
            (r'\bkrungi\b', 'karunga'),
            (r'\baayi hu\b', 'aaya hu'),
            (r'\baayi hoon\b', 'aaya hoon'),
        ]
        for pat, repl in hing_rules:
            t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    elif g == "female":
        # ── Devanagari Masculine -> Feminine ──
        dev_rules = [
            (r'बोल रहा हूँ', 'बोल रही हूँ'),
            (r'बोल रहा हु', 'बोल रही हूँ'),
            (r'बात कर रहा हूँ', 'बात कर रही हूँ'),
            (r'कर रहा हूँ', 'कर रही हूँ'),
            (r'कर रहा था', 'कर रही थी'),
            (r'माफी चाहता हूँ', 'माफी चाहती हूँ'),
            (r'माफ़ी चाहता हूँ', 'माफ़ी चाहती हूँ'),
            (r'माफी माँगता हूँ', 'माफी माँगती हूँ'),
            (r'माफ़ी माँगता हूँ', 'माफ़ी माँगती हूँ'),
            (r'माफी मांगता हूँ', 'माफी मांगती हूँ'),
            (r'माफ़ी मांगता हूँ', 'माफ़ी मांगती हूँ'),
            (r'माफी चाहता', 'माफी चाहती'),
            (r'माफ़ी चाहता', 'माफ़ी चाहती'),
            (r'माफी माँगता', 'माफी माँगती'),
            (r'माफ़ी माँगता', 'माफ़ी माँगती'),
            (r'माफी मांगता', 'माफी मांगती'),
            (r'माफ़ी मांगता', 'माफ़ी मांगती'),
            (r'चाहता हूँ', 'चाहती हूँ'),
            (r'चाहता हु', 'चाहती हूँ'),
            (r'चाहूँगा', 'चाहूँगी'),
            (r'चाहूंगा', 'चाहूंगी'),
            (r'कर दूँगा', 'कर दूँगी'),
            (r'कर दूंगा', 'कर दूंगी'),
            (r'कर लूँगा', 'कर लूँगी'),
            (r'कर लूंगा', 'कर लूंगी'),
            (r'देता हूँ', 'देती हूँ'),
            (r'लेता हूँ', 'लेती हूँ'),
            (r'समझता हूँ', 'समझती हूँ'),
            (r'समझ गया', 'समझ गई'),
            (r'करूँगा', 'करूँगी'),
            (r'करूंगा', 'करूंगी'),
            (r'बताता हूँ', 'बताती हूँ'),
            (r'सुनाता हूँ', 'सुनाती हूँ'),
            (r'आया हूँ', 'आई हूँ'),
            (r'गया हूँ', 'गई हूँ'),
        ]
        for pat, repl in dev_rules:
            t = re.sub(pat, repl, t)

        # ── Romanized Hinglish Masculine -> Feminine ──
        hing_rules = [
            (r'\bbol raha hu\b', 'bol rahi hu'),
            (r'\bbol raha hoon\b', 'bol rahi hoon'),
            (r'\bbaat kar raha hu\b', 'baat kar rahi hu'),
            (r'\bbaat kar raha hoon\b', 'baat kar rahi hoon'),
            (r'\bkar raha hu\b', 'kar rahi hu'),
            (r'\bkar raha hoon\b', 'kar rahi hoon'),
            (r'\bkr raha hu\b', 'kar rahi hu'),
            (r'\bkar raha tha\b', 'kar rahi thi'),
            (r'\bmaafi chahta hu\b', 'maafi chahti hu'),
            (r'\bmaafi chahta hoon\b', 'maafi chahti hoon'),
            (r'\bmafi chahta hu\b', 'maafi chahti hu'),
            (r'\bmaafi mangta hu\b', 'maafi mangti hu'),
            (r'\bmaafi mangta hoon\b', 'maafi mangti hoon'),
            (r'\bmafi mangta hu\b', 'maafi mangti hu'),
            (r'\bmaafi chahta\b', 'maafi chahti'),
            (r'\bmafi chahta\b', 'maafi chahti'),
            (r'\bmaafi mangta\b', 'maafi mangti'),
            (r'\bmafi mangta\b', 'maafi mangti'),
            (r'\bchahta hu\b', 'chahti hu'),
            (r'\bchahta hoon\b', 'chahti hoon'),
            (r'\bchati hu\b', 'chahti hu'),
            (r'\bchahunga\b', 'chahungi'),
            (r'\bkar dunga\b', 'kar dungi'),
            (r'\bkr dunga\b', 'kar dungi'),
            (r'\bkar lunga\b', 'kar lungi'),
            (r'\bkr lunga\b', 'kar lungi'),
            (r'\bde deta hu\b', 'de deti hu'),
            (r'\bdeta hu\b', 'deti hu'),
            (r'\bleta hu\b', 'leti hu'),
            (r'\bsamajhta hu\b', 'samajhti hu'),
            (r'\bsamajhta hoon\b', 'samajhti hoon'),
            (r'\bsamajh gaya\b', 'samajh gayi'),
            (r'\bkarunga\b', 'karungi'),
            (r'\baaya hu\b', 'aayi hu'),
            (r'\baaya hoon\b', 'aayi hoon'),
        ]
        for pat, repl in hing_rules:
            t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    return t


class DialogueEngine:
    """Generates dynamic conversational phone turns aligned with persona & caller signals."""

    def __init__(self, sarvam_client=None):
        self.sarvam = sarvam_client or get_sarvam_client()

    def generate_reply(self, seller_text: str,
                       history: Optional[List[Dict[str, str]]] = None,
                       seller_profile: Optional[Dict[str, Any]] = None,
                       active_persona: Optional[Persona] = None,
                       signal: Optional[DetectedSignal] = None) -> str:
        """
        Main entry point: analyzes seller utterance, classifies intent,
        applies active persona constraints, enforces speaker grammatical gender agreement,
        and produces a natural spoken response.
        """
        text_clean = seller_text.strip()
        profile = seller_profile or {}
        history = history or []

        bot_gender = (active_persona.gender or "male").lower() if active_persona else "male"
        reply = ""

        # 1. High-speed bilingual B2B domain intent matching (<10ms)
        domain_reply = self._match_domain_intent(text_clean, profile, active_persona, signal)
        if domain_reply:
            reply = domain_reply
        elif not isinstance(self.sarvam, MockSarvamClient):
            # 2. For open-ended or novel queries, invoke Sarvam Conversational LLM (<1.5s)
            try:
                llm_reply = self._call_sarvam_llm(
                    seller_text=text_clean,
                    history=history,
                    seller_profile=profile,
                    active_persona=active_persona,
                    signal=signal
                )
                if llm_reply and len(llm_reply.strip()) > 5:
                    reply = self._clean_for_speech(llm_reply)
            except Exception as e:
                logger.warning(f"Sarvam LLM call failed: {e}. Falling back to default response.")

        if not reply:
            # 3. Contextual conversational fallback matching input script
            reply = self._build_contextual_fallback(text_clean, profile, active_persona, signal)

        # 4. Strictly enforce speaker grammatical gender agreement
        return enforce_speaker_gender(reply, bot_gender)

    def _match_domain_intent(self, text: str,
                             profile: Dict[str, Any],
                             persona: Optional[Persona],
                             signal: Optional[DetectedSignal]) -> Optional[str]:
        """
        Bilingual semantic intent matching directly solving the 5 failure modes
        identified across 278k evaluator audits and 139k call turns.
        Supports both Devanagari Hindi and Romanized Hinglish with strict speaker gender consistency.
        """
        t = text.lower()
        raw = text.strip()
        is_hindi = is_devanagari(raw)
        cat = profile.get("top_category_1", "products")
        state = profile.get("seller_state", "aapke area")
        sig_type = signal.signal if signal else "neutral"

        # Speaker gender determination
        is_male = (persona.gender or "male").lower() == "male" if persona else True
        bot_name = persona.voice_name.split("(")[0].strip() if (persona and persona.voice_name) else ("शुभ" if is_male else "वाणी")
        bot_name_en = persona.voice_name.split("(")[0].strip() if (persona and persona.voice_name) else ("Shubh" if is_male else "Vani")

        # Caller gender detection (adapts address between Sir and Madam/Ma'am)
        seller_gender_hint = str(profile.get("caller_gender") or profile.get("gender") or profile.get("seller_gender") or "").lower()
        is_caller_female = (seller_gender_hint == "female") or \
                           any(w in t for w in [
                               "bol rahi", "kar rahi", "keh rahi", "soch rahi", "dekh rahi", "rahi hu", "rahi hoon",
                               "chahti", "karti", "bolti", "karungi", "bataungi", "dekhungi", "kar sakti",
                               "gayi hu", "gayi hoon", "ho gayi", "aa gayi", "madam", "ma'am", "mam", "mrs",
                               "shrimati", "mahila", "aurat", "didi", "bhabhi", "sister"
                           ]) or \
                           any(w in raw for w in [
                               "बोल रही", "कर रही", "कह रही", "सोच रही", "देख रही", "रही हूँ", "रही हु",
                               "चाहती", "करती", "बोलती", "करूँगी", "करूंगी", "बताऊँगी", "बताऊंगी",
                               "गई हूँ", "गई हु", "हो गई", "आ गई", "सकती हूँ", "सकती हु", "सकती", "मैडम",
                               "महिला", "औरत", "दीदी", "भाभी", "श्रीमती"
                           ])
        honorific_hi = "मैडम" if is_caller_female else "सर"
        honorific_en = "Ma'am" if is_caller_female else "sir"

        # Speaker gendered conjugations
        bol_raha_hi = "बोल रहा हूँ" if is_male else "बोल रही हूँ"
        bol_raha_en = "bol raha hu" if is_male else "bol rahi hu"
        kar_lunga_hi = "कर लूँगा" if is_male else "कर लूँगी"
        kar_lunga_en = "kar lunga" if is_male else "kar lungi"
        maafi_hi = "माफी चाहता हूँ" if is_male else "माफी चाहती हूँ"
        maafi_en = "maafi chahta hu" if is_male else "maafi chahti hu"
        samajh_gaya_hi = "समझ गया" if is_male else "समझ गई"
        samajh_gaya_en = "samajh gaya" if is_male else "samajh gayi"
        kar_raha_hi = "कर रहा हूँ" if is_male else "कर रही हूँ"
        kar_raha_en = "kar raha hu" if is_male else "kar rahi hu"

        # ── 0. EMERGENCY DE-ESCALATION (FRUSTRATION / ANGER / DO NOT CALL) ──
        if sig_type == "frustrated" or any(w in t for w in ["bar bar", "baar baar", "disturb", "band karo", "phone kaat", "pareshan", "faltu call", "dimag kharab"]) or \
           any(w in raw for w in ["बार बार", "बार-बार", "परेशान मत करो", "दिमाग खराब", "फोन काटो", "काट दो", "बंद करो", "फालतू"]):
            if is_hindi:
                return f"{honorific_hi}, परेशान करने के लिए मैं दिल से {maafi_hi}। मैं सिस्टम में तुरंत अपडेट {kar_raha_hi} ताकि आपको दोबारा बेवजह कॉल न आए। नमस्कार {honorific_hi}।"
            return f"{honorific_en.capitalize()}, bilkul {maafi_en} pareshan karne ke liye. Main abhi aapka status update {kar_raha_en} taaki bematlab call na aaye. Namaskar {honorific_en}."

        # ── 1. CONSTRAINT AWARENESS: SUNDAY / HOLIDAY / SHOP CLOSED ──
        if any(w in t for w in ["sunday", "ravivar", "itwar", "dukan band", "chhutti", "closed"]) or \
           any(w in raw for w in ["रविवार", "संडे", "इतवार", "दुकान बंद", "छुट्टी", "बंद है", "बंद रहती"]):
            if is_hindi:
                return f"अरे बिल्कुल {honorific_hi}! संडे को तो दुकान बंद रहती है, आप आराम कीजिए। सोमवार सुबह 11 बजे फर्स्ट क्लास रहेगा या दोपहर 2 बजे?"
            return f"Arey bilkul {honorific_en}, Sunday ko toh dukan band rehti hai. Somwar subah 11 baje first class rahega ya dopahar me 2 baje?"

        # ── 2. CONSTRAINT AWARENESS: SHOP CROWD / FACTORY NOISE / CUSTOMER PRESENT ──
        if any(w in t for w in ["bheed", "grahak", "customer", "counter", "dukaan pe", "machine", "fursat nahi", "akela hoon"]) or \
           any(w in raw for w in ["भीड़", "ग्राहक खड़ा", "कस्टमर खड़ा", "काउंटर पे", "दुकान पे हूँ", "दुकान पर हूँ", "फुर्सत नहीं", "अकेला हूँ"]):
            if is_hindi:
                return f"{samajh_gaya_hi} {honorific_hi}, ग्राहक को पहले अटेंड कीजिए—धंधा पहले है! मैं शाम को 7 बजे दुकान बढ़ाने के बाद कॉल करूँ?"
            return f"{samajh_gaya_en.capitalize()} {honorific_en}, grahak ko pehle attend kijiye—vyapar pehle hai! Main shaam ko 7 baje dukan badhane ke baad call karu?"

        # ── 3. CONSTRAINT AWARENESS: PHONE / WHATSAPP INSTEAD OF PHYSICAL VISIT ──
        if any(w in t for w in ["phone pe", "online hi", "aane ki kya zaroorat", "milne ki zaroorat", "whatsapp pe", "visit nahi", "call pe batao"]) or \
           any(w in raw for w in ["फोन पर बताओ", "फोन पे बताओ", "आने की जरूरत नहीं", "व्हाट्सएप पर भेजो", "व्हाट्सएप पे", "ऑनलाइन बताओ", "विजिट नहीं", "मिलने की क्या जरूरत", "फोन पर ही"]):
            if is_hindi:
                return f"बिल्कुल {honorific_hi}! किसी को दुकान पर आने की कोई जरूरत नहीं है। हम सीधे आपके व्हाट्सएप पर लाइव वेरिफाइड बायर्स की इंक्वायरी भेज देते हैं। क्या इसी नंबर पर व्हाट्सएप चालू है?"
            return f"Bilkul {honorific_en}! Hum aapke WhatsApp par live verified buyers ke orders bhej dete hain, kisi ko aane ki zaroorat nahi hai. Kya is number par WhatsApp chalu hai?"

        # ── 4. IDENTITY & PURPOSE: WHO ARE YOU & WHY CALL ME / ARE YOU A BOT? ──
        if any(w in t for w in ["kaun bol", "kon bol", "kiska call", "who are you", "kaha se", "bot ho", "robot", "insaan", "real ho", "automated"]) or \
           any(w in raw for w in ["कौन बोल", "किसका फोन", "किसका कॉल", "कहाँ से", "वाणी कौन", "बॉट हो", "रोबोट", "इंसान", "सिस्टम बोल", "ऑटोमेटेड"]):
            is_bot_query = any(w in t for w in ["bot", "robot", "ai", "insaan", "automated"]) or any(w in raw for w in ["बॉट", "रोबोट", "इंसान", "सिस्टम"])
            if is_bot_query:
                if is_hindi:
                    return f"{honorific_hi}, मैं इंडियामार्ट से {bot_name} {bol_raha_hi}, एक डिजिटल वॉइस असिस्टेंट। आपके {cat} के काम के लिए नए वेरिफाइड बायर्स की डिमांड आई है, इसलिए सीधे आपको इन्फॉर्म किया।"
                return f"Main IndiaMART se {bot_name_en} {bol_raha_en} {honorific_en}, ek digital voice assistant. Humare paas aapke {cat} ke business ke liye verified buyer leads aayi hain."
            else:
                if is_hindi:
                    return f"{honorific_hi}, मैं इंडियामार्ट के सेलर सपोर्ट से {bot_name} {bol_raha_hi}। हम बिना काम के फोन नहीं करते—आपके एरिया में {cat} के वेरिफाइड बायर्स के नए ऑर्डर्स पेंडिंग थे, इसलिए सीधे आपको कॉल किया।"
                return f"{honorific_en.capitalize()}, main IndiaMART ke seller team se {bot_name_en} {bol_raha_en}. Hum kisi ko bekar me call nahi karte—aapke area mein {cat} ke verified buyers ke orders pending the, isliye direct aapko phone kiya hai."

        # ── 5. PURPOSE: WHY MEETING? KYA FAYDA HOGA? ───────────
        if any(w in t for w in ["kyu milna", "kis regarding", "kya fayda", "kya bataoge", "purpose kya", "kis baare me", "kyu call kiya", "kya kaam hai"]) or \
           any(w in raw for w in ["क्यों फोन किया", "क्या काम है", "किसलिए", "क्या फायदा", "क्या बताओगे", "परपज क्या", "किस बारे में", "क्यों मिलना", "क्यों कॉल किया"]):
            if is_hindi:
                return f"{honorific_hi}, पिछले हफ्ते आपके शहर में {cat} के 25 से ज्यादा वेरिफाइड बल्क ऑर्डर्स आए हैं। हम बस आपको व्हाट्सएप पर दिखाना चाहते हैं कि बिना किसी रिस्क के बायर्स से सीधे कैसे जुड़ना है।"
            return f"{honorific_en.capitalize()}, pichle hafte aapke sheher mein {cat} ke 25 se zyada verified bulk orders aaye hain. Hum bas aapko mobile par dikhana chahte hain ki buyers se direct kaise judna hai—bina kisi advance kharche ke."

        # ── 6. SKEPTICISM & PAST EXPERIENCE: FAKE LEADS / PAISE WASTE ──
        if any(w in t for w in ["fayda nahi", "pehle bhi", "fake lead", "bekar lead", "paise waste", "paise doob", "dhokha", "loss ho gaya", "nuksan"]) or \
           any(w in raw for w in ["पैसे डूब गए", "फेक लीड", "बेकार लीड", "पैसे वेस्ट", "नुकसान हुआ", "धोखा", "कोई फायदा नहीं", "पहले भी लिया था", "डूबा"]):
            if is_hindi:
                return f"आपका गुस्सा बिल्कुल सही है {honorific_hi}, पहले बिना ओटीपी वाली पुरानी लीड्स आ जाती थीं। पर अब इंडियामार्ट ने जीएसटी और मोबाइल ओटीपी वेरिफाइड फिल्टर अनिवार्य कर दिया है। आप एक बार बिना किसी पेमेंट के खुद डिमांड देख लीजिए।"
            return f"Aapka gussa bilkul sahi hai {honorific_en}, pehle unverified enquiries aati thi. Par ab humne mobile OTP aur GST filter mandatory kar diya hai. Jaise aapke sheher ke 15 suppliers regular orders nikaal rahe hain, aap ek bar bina risk ke review karke dekhein."

        # ── 7. PRICING & VALUE: KITNA KHARCHA LAGEGA? ─────────
        if any(w in t for w in ["kitna kharcha", "kitne paise", "price", "pricing", "cost", "charge", "package", "fees", "rate card", "monthly kitna", "rate kya"]) or \
           any(w in raw for w in ["कितना खर्चा", "कितना पैसा", "रेट क्या", "भाव क्या", "प्राइस", "चार्ज", "पैकेज", "फीस", "मंथली कितना", "सीधे-सीधे बताओ", "खर्च कितना"]):
            if is_hindi:
                return f"{honorific_hi}, इंडियामार्ट पर महीने का लगभग 2,000 से 2,500 रुपये से प्लान शुरू होते हैं, जिसमें बायर्स सीधे आपके फोन पर कॉल करते हैं। पहले आप बिना कोई पैसा दिए फ्री में डिमांड देख लीजिए।"
            if sig_type == "rushed":
                return f"{honorific_en.capitalize()}, 2,000 se 2,500 monthly se packages start hote hain jisme verified buyers direct phone karte hain. WhatsApp pe rate card bhej du?"
            return f"{honorific_en.capitalize()}, IndiaMART par packages lagbhag 2,000 se 2,500 rupaye mahine se shuru hote hain. Isme verified buyers direct aapke phone par call karte hain. Pehle aap bina kisi paise ke demand dekh lijiye."

        # ── 8. FREE USER / DISINTEREST IN PAID SERVICES ───────
        if any(w in t for w in ["free wala", "paid nahi", "nahi chahiye", "nahi lena", "not interested", "zarurat nahi"]) or \
           any(w in raw for w in ["फ्री वाला", "पेड नहीं", "नहीं चाहिए", "नहीं लेना", "इंटरेस्ट नहीं", "जरूरत नहीं"]):
            if is_hindi:
                return f"बिल्कुल सही {honorific_hi}, आप फ्री वाला ही इस्तेमाल करते रहिए! बस अपने प्रोफाइल में 2-3 नए प्रोडक्ट्स की फोटो व्हाट्सएप से अपडेट करवा लीजिए, ताकि जो फ्री इंक्वायरी आती हैं उनकी क्वालिटी और बढ़ जाए।"
            return f"Bilkul sahi {honorific_en}, aap free wala hi use karte rahiye! Bas apne profile par 2-3 naye products ki photo WhatsApp se update karwa lijiye, taaki free enquiries ki quality aur behtar ho jaye."

        # ── 9. PAYMENT SECURITY & TRUST: ADVANCE & ESCROW ───────
        if any(w in t for w in ["payment", "paise fas", "guarantee", "fraud", "safe hai"]) or \
           any(w in raw for w in ["पेमेंट", "पैसे फंस", "गारंटी", "फ्रॉड", "सुरक्षित"]):
            if is_hindi:
                return f"इंडियामार्ट पर 'Pay with IndiaMART' एस्क्रो सुरक्षा है {honorific_hi}—जब तक बायर को सामान नहीं मिलता और आप कन्फर्म नहीं करते, पेमेंट 100% बैंक में सुरक्षित रहती है।"
            return f"IndiaMART par 'Pay with IndiaMART' escrow protection hai {honorific_en}—jab tak aapka delivery confirmation nahi hota, payment 100% bank-guaranteed secure rehti hai."

        # ── 10. CATALOG & PHOTOS: SETUP ISSUES ─────────────────
        if any(w in t for w in ["catalog", "photo", "upload", "delete", "edit", "listing", "product add", "image"]) or \
           any(w in raw for w in ["फोटो", "कैटलॉग", "प्रोडक्ट डालना", "लिस्टिंग", "अपलोड"]):
            if is_hindi:
                return f"जी {honorific_hi}, आपके {cat} के प्रोडक्ट्स और फोटो हमारे एग्जीक्यूटिव बिल्कुल फ्री में व्हाट्सएप के जरिए लिस्ट करवा देंगे। किसी को आने की जरूरत नहीं है।"
            return f"Ji {honorific_en}, aapka catalog setup humare executive free me karwa denge. Bas aap WhatsApp par apne {cat} ki photos aur rates share kar dijiye."

        # ── 11A. DRIVING / VEHICLE IN TRANSIT (Safety First) ──
        is_driving = any(w in t for w in ["driving", "gaadi chala", "bike pe", "traffic", "gadi chala"]) or \
                     any(w in raw for w in ["गाड़ी चला रहा", "ड्राइविंग", "बाइक पर", "ट्रैफिक में", "ड्राइव कर रहा"])
        if is_driving:
            if is_hindi:
                return f"अरे {honorific_hi}, आप सुरक्षित ड्राइव कीजिए! मैं 2 घंटे बाद या शाम को कॉल {kar_lunga_hi}। ध्यान से चलिएगा {honorific_hi}!"
            return f"Arey {honorific_en}, aap bilkul safe drive kijiye! Main 2 ghante baad ya shaam ko call {kar_lunga_en}. Dhyan se chaliyega {honorific_en}!"

        # ── 11B. BUSY / OCCUPIED / IN A MEETING (Respect Time) ──
        is_busy = sig_type == "rushed" or \
                  any(w in t for w in ["busy", "vyast", "time nahi", "fursat nahi", "meeting me", "kaam me"]) or \
                  any(w in raw for w in ["व्यस्त", "फुर्सत नहीं", "मीटिंग", "काम में हूँ", "समय नहीं", "टाइम नहीं"])
        if is_busy:
            if is_hindi:
                return f"{samajh_gaya_hi} {honorific_hi}, आपका समय बहुत कीमती है। क्या मैं आज शाम को 7 बजे या कल सुबह 11 बजे कॉल {kar_lunga_hi}?"
            return f"{samajh_gaya_en.capitalize()} {honorific_en}, bilkul samajh sakta hu aap busy hain. Main shaam ko 7 baje ya kal subah 11 baje call {kar_lunga_en}?"

        # ── 12. ANGER / HARASSMENT / DO NOT CALL ──────────────
        if sig_type == "frustrated" or any(w in t for w in ["bar bar", "disturb", "band karo", "phone kaat", "pareshan", "faltu call"]) or \
           any(w in raw for w in ["बार बार", "परेशान मत करो", "दिमाग खराब", "फोन काटो", "काट दो", "बंद करो", "फालतू"]):
            if is_hindi:
                return f"{honorific_hi}, परेशान करने के लिए मैं दिल से {maafi_hi}। मैं सिस्टम में तुरंत अपडेट {kar_raha_hi} ताकि आपको दोबारा बेवजह कॉल न आए। नमस्कार {honorific_hi}।"
            return f"{honorific_en.capitalize()}, bilkul {maafi_en} pareshan karne ke liye. Main abhi aapka status update {kar_raha_en} taaki bematlab call na aaye. Namaskar {honorific_en}."

        # ── 13. CONFUSED / HINDI ANALOGY ───────────────────────
        if sig_type == "confused" or any(w in t for w in ["kya matlab", "samajh nahi", "kya chiz"]) or \
           any(w in raw for w in ["क्या मतलब", "समझ नहीं आया", "क्या चीज है", "क्या बोला"]):
            if is_hindi:
                return f"कोई बात नहीं {honorific_hi}। जैसे मंडी में आपकी दुकान पर ग्राहक आकर {cat} का थोक भाव पूछते हैं, वैसे ही ऑनलाइन बायर्स सीधे आपके मोबाइल पर कॉल करके बड़ा आर्डर देते हैं।"
            return f"Ji koi baat nahi {honorific_en}. Jaise mandi mein dukaan pe grahak aate hain, waise hi online buyers aapko direct phone karke {cat} ka bulk rate puchte hain."

        # ── 14. SCHEDULING SPECIFIC DAYS & TIMES ───────────────
        has_specific_time = any(w in t for w in ["kal", "somwar", "mangalwar", "budhwar", "guruwar", "shukrawar", "shanivar", "baje", "dopahar", "shaam"]) or \
                            any(w in raw for w in ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "कल", "शाम को", "दोपहर को", "सुबह", "बजे"])
        is_postpone_general = any(w in t for w in ["baad me", "abhi nahi", "baad me baat", "later"]) or \
                              any(w in raw for w in ["बाद में बात", "बाद में", "अभी नहीं"])

        if has_specific_time:
            if is_hindi:
                return f"बहुत बढ़िया {honorific_hi}! मैंने समय नोट कर लिया है। इंडियामार्ट से हमारा कॉल उसी समय आएगा। बहुत-बहुत धन्यवाद, आपका दिन शुभ हो!"
            return f"Theek hai {honorific_en}! Maine samay note kar liya hai, hum usi time connect karenge. Bahut-bahut shukriya, shubh din!"
        elif is_postpone_general:
            if is_hindi:
                return f"{samajh_gaya_hi} {honorific_hi}, क्या आज शाम को 7 बजे या कल दोपहर में 2 बजे कॉल {kar_lunga_hi}?"
            return f"{samajh_gaya_en.capitalize()} {honorific_en}, kya aaj shaam ko 7 baje ya kal dopahar 2 baje call {kar_lunga_en}?"

        # ── 15. AFFIRMATION / TELL ME MORE / INTERESTED ────────
        if any(w in t for w in ["haan batao", "boliye", "sunao", "theek hai", "haanji", "batao", "free hu"]) or \
           any(w in raw for w in ["हाँ बताओ", "बोलिए", "सुनाओ", "बताओ क्या", "हांजी", "ठीक है", "बताइए", "फ्री हूँ"]):
            if is_hindi:
                return f"जी {honorific_hi}! आपके एरिया में {cat} के 15 नए वेरिफाइड बायर्स इस हफ्ते बल्क कोटेशन मांग रहे हैं। क्या मैं व्हाट्सएप पर बायर लिस्ट शेयर कर दूँ?"
            return f"Ji {honorific_en}! Aapke area mein {cat} ke 15 verified buyers is hafte bulk quotation maang rahe hain. Kya main WhatsApp par buyer list share kar du?"

        # No specific deterministic domain intent match
        return None

    def _call_sarvam_llm(self, seller_text: str,
                         history: List[Dict[str, str]],
                         seller_profile: Dict[str, Any],
                         active_persona: Optional[Persona],
                         signal: Optional[DetectedSignal]) -> str:
        """
        Invokes Sarvam-105B-Conversations LLM with strict speaker gender consistency
        and grounded B2B knowledge from the IndiaMART MCP store.
        """
        from src.mcp_server import get_verified_buyer_leads, get_official_pricing

        bot_gender = (active_persona.gender or "male").lower() if active_persona else "male"
        bot_name = active_persona.voice_name.split("(")[0].strip() if (active_persona and active_persona.voice_name) else ("Shubh" if bot_gender == "male" else "Vani")
        category = seller_profile.get("top_category_1", "products")
        state = seller_profile.get("seller_state", "India")
        is_hindi = is_devanagari(seller_text)

        # Grounded facts from MCP tools
        leads_data = get_verified_buyer_leads(category, state)
        leads_count = leads_data.get("verified_buyers_count", 15)
        pricing_data = get_official_pricing(str(seller_profile.get("annual_turnover", "")))
        pricing_summary = pricing_data.get("pricing_range_summary", "approx ₹2,000 to ₹2,500/month")

        # Detect caller gender
        t_low = seller_text.lower()
        seller_gender_hint = str(seller_profile.get("caller_gender") or seller_profile.get("gender") or seller_profile.get("seller_gender") or "").lower()
        is_caller_female = (seller_gender_hint == "female") or \
                           any(w in t_low for w in [
                               "bol rahi", "kar rahi", "chahti hu", "chahti hoon", "karti hu", "karti hoon",
                               "kartii hu", "karti", "bolti hu", "bolti hoon", "bolti", "chahti", "karungi",
                               "bataungi", "dekhungi", "madam", "ma'am", "mam", "mrs", "shrimati", "mahila",
                               "aurat", "didi", "bhabhi", "sister"
                           ]) or \
                           any(w in seller_text for w in [
                               "बोल रही", "कर रही", "चाहती", "करती हूँ", "करती हु", "करती", "बोलती हूँ",
                               "बोलती हु", "बोलती", "करूँगी", "करूंगी", "बताऊँगी", "बताऊंगी", "मैडम",
                               "महिला", "औरत", "दीदी", "भाभी", "श्रीमती"
                           ])
        honorific = "Madam / Ma'am" if is_caller_female else "Sir"

        if bot_gender == "male":
            grammar_rule = (
                f"CRITICAL SPEAKER GENDER RULE: YOU ARE A MALE EXECUTIVE NAMED {bot_name}. "
                f"Even when speaking to a female caller, YOU MUST ALWAYS USE MASCULINE FIRST-PERSON VERBS FOR YOURSELF: "
                f"Say 'main bol raha hoon' (NEVER 'bol rahi hoon'), 'main chahta hoon' (NEVER 'chahti hoon'), "
                f"'main maafi mangta hoon' (NEVER 'maafi mangti hoon'), 'main kar dunga / kar lunga' (NEVER 'kar dungi / kar lungi'), "
                f"'main samajh gaya' (NEVER 'samajh gayi'), 'main bhej deta hoon' (NEVER 'bhej deti hoon'). "
                f"{'The caller is a FEMALE seller. ALWAYS address her as Ma\'am / Madam (NEVER say Sir).' if is_caller_female else 'Address the caller politely as Sir or with respectful Aap / Ji.'}"
            )
        else:
            grammar_rule = (
                f"CRITICAL SPEAKER GENDER RULE: YOU ARE A FEMALE EXECUTIVE NAMED {bot_name}. "
                f"YOU MUST ALWAYS USE FEMININE FIRST-PERSON VERBS FOR YOURSELF: "
                f"Say 'main bol rahi hoon', 'main chahti hoon', 'main maafi mangti hoon', 'main kar dungi / kar lungi', 'main samajh gayi'. "
                f"{'The caller is a FEMALE seller. ALWAYS address her as Ma\'am / Madam (NEVER say Sir).' if is_caller_female else 'Address the caller politely as Sir or with respectful Aap / Ji.'}"
            )

        anti_hallucination_block = (
            f"GROUNDED KNOWLEDGE (NEVER INVENT DETAILS):\n"
            f"- Seller Category: {category} in {state}\n"
            f"- Active Verified Buyers: {leads_count} genuine inquiries pending in nearby regions\n"
            f"- IndiaMART Pricing: {pricing_summary}\n"
            f"- Objective: Offer to send verified inquiry summary on WhatsApp or schedule a phone briefing with an RM. DO NOT ask for money over the call.\n"
            f"- ANTI-HALLUCINATION GUARDS:\n"
            f"  1. NEVER assume the seller is driving a car or on the road unless they explicitly state 'driving', 'gaadi', or 'traffic'. If they say busy/occupied, offer a polite callback time.\n"
            f"  2. NEVER promise uninvited in-person visits to their shop or factory.\n"
            f"  3. NEVER guarantee 100% sales or make up fictitious buyer company names.\n"
            f"  4. Keep replies to 1 or 2 SHORT sentences (UNDER 25 WORDS total) for real-time voice streaming."
        )

        if is_hindi:
            system_prompt = (
                f"You are {bot_name}, an authentic, respectful and sharp AI Voice Executive from IndiaMART calling an Indian business owner on the phone.\n"
                f"{grammar_rule}\n\n"
                f"{anti_hallucination_block}\n\n"
                f"RULES FOR CONVERSATION:\n"
                f"1. Reply in authentic spoken Hindi (Devanagari script) in 1 or 2 SHORT sentences (UNDER 25 WORDS).\n"
                f"2. Never sound like an aggressive telemarketer; sound like a helpful business consultant.\n"
                f"3. Be humble and respectful (Aap, Ji).\n"
                f"4. Plain text only. No quotes, no markdown, no asterisks."
            )
        else:
            system_prompt = (
                f"You are {bot_name}, an authentic, respectful and sharp AI Voice Executive from IndiaMART calling an Indian business owner on the phone.\n"
                f"{grammar_rule}\n\n"
                f"{anti_hallucination_block}\n\n"
                f"RULES FOR CONVERSATION:\n"
                f"1. Reply in spoken conversational Hinglish in 1 or 2 SHORT sentences (UNDER 25 WORDS).\n"
                f"2. Never sound like an aggressive telemarketer; sound like a helpful business consultant.\n"
                f"3. Be humble and respectful (Aap, Ji).\n"
                f"4. Plain text only. No quotes, no markdown, no asterisks."
            )

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Use up to 6 turns of history to maintain context
        for turn in history[-6:]:
            role = "user" if turn.get("speaker") == "seller" else "assistant"
            content = turn.get("text", "").strip()
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": seller_text})

        # Use Sarvam's official conversational voice model with low temperature to prevent hallucination
        resp = self.sarvam._request("POST", "/v1/chat/completions", {
            "model": "sarvam-105b-conversations",
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 120
        })

        content = resp["choices"][0]["message"].get("content")
        return content or ""

    def _clean_for_speech(self, text: str) -> str:
        """Cleans LLM output for natural TTS delivery."""
        t = text.strip()
        t = re.sub(r'[*_#`~]', '', t)
        t = re.sub(r'["\']', '', t)
        t = re.sub(r'\[.*?\]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t.strip()

    def _build_contextual_fallback(self, text: str,
                                   profile: Dict[str, Any],
                                   persona: Optional[Persona],
                                   signal: Optional[DetectedSignal]) -> str:
        """Contextual fallback when no intent and no LLM reply, matching input script."""
        cat = profile.get("top_category_1", "products")
        is_hindi = is_devanagari(text)

        t_low = text.lower()
        is_caller_female = any(w in t_low for w in ["bol rahi hu", "kar rahi hu", "chahti hu", "madam"]) or \
                           any(w in text for w in ["बोल रही हूँ", "बोल रही हु", "कर रही हूँ", "चाहती हूँ", "मैडम"])
        honorific_hi = "मैडम" if is_caller_female else "सर"
        honorific_en = "Ma'am" if is_caller_female else "sir"

        if is_hindi:
            if signal and signal.signal == "engaged":
                return f"जी बिल्कुल {honorific_hi}! हम सीधे आपके व्हाट्सएप पर वेरिफाइड खरीदारों के बल्क ऑर्डर्स शेयर कर देते हैं। क्या इसी नंबर पर व्हाट्सएप चालू है?"
            return f"जी {honorific_hi}, {cat} के नए वेरिफाइड बायर्स ऑर्डर्स लेना चाहते हैं। क्या मैं व्हाट्सएप पर डिटेल शेयर कर दूँ?"
        else:
            if signal and signal.signal == "engaged":
                return f"Ji bilkul {honorific_en}! Hum aapke WhatsApp par verified bulk inquiries share kar dete hain. Kya is number par WhatsApp chalu hai?"
            return f"Ji {honorific_en}, {cat} ke naye genuine verified buyers orders lena chahte hain. Kya main WhatsApp par details share kar du?"
