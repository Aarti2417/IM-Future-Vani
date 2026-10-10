import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

def enforce_speaker_gender(text: str, gender: str) -> str:
    """
    Enforces strict grammatical gender agreement for the AI speaker's first-person verbs.
    If speaker is male, replaces any feminine first-person inflections with masculine.
    If speaker is female, replaces any masculine first-person inflections with feminine.
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
            (r'कर रहा हूँ', 'कर रही हूँ'),
            (r'कर रहा हु', 'कर रही हूँ'),
            (r'कर रहा था', 'कर रही थी'),
            (r'माफी चाहता हूँ', 'माफी चाहती हूँ'),
            (r'माफ़ी चाहता हूँ', 'माफ़ी चाहती हूँ'),
            (r'माफी माँगता हूँ', 'माफी माँगती हूँ'),
            (r'माफ़ी माँगता हूँ', 'माफ़ी माँगती हूँ'),
            (r'माफी मांगता हूँ', 'माफी मांगती हूँ'),
            (r'माफ़ी मांगता हूँ', 'माफ़ी मांगती हूँ'),
            (r'माफी चाहता', 'माफी चाहती'),
            (r'माफ़ी चाहता', 'माफ़ी चाहती'),
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

# Run tests
test_cases_male = [
    ("Main IndiaMART se bol rahi hu madam, maafi mangti hu, main kar dungi aur chati hu aap dekhein.",
     "Main IndiaMART se bol raha hu madam, maafi mangta hu, main kar dunga aur chahta hu aap dekhein."),
    ("सर, परेशान करने के लिए मैं दिल से माफी चाहती हूँ। मैं सिस्टम में तुरंत अपडेट कर रही हूँ।",
     "सर, परेशान करने के लिए मैं दिल से माफी चाहता हूँ। मैं सिस्टम में तुरंत अपडेट कर रहा हूँ।"),
    ("मैं 2 घंटे बाद कॉल कर लूँगी।",
     "मैं 2 घंटे बाद कॉल कर लूँगा।")
]

test_cases_female = [
    ("Main IndiaMART se bol raha hu sir, maafi mangta hu, main kar dunga aur chahta hu aap dekhein.",
     "Main IndiaMART se bol rahi hu sir, maafi chahti hu, main kar dungi aur chahti hu aap dekhein."),
    ("सर, परेशान करने के लिए मैं दिल से माफी चाहता हूँ। मैं सिस्टम में तुरंत अपडेट कर रहा हूँ।",
     "सर, परेशान करने के लिए मैं दिल से माफी चाहती हूँ। मैं सिस्टम में तुरंत अपडेट कर रही हूँ।")
]

print("=== TESTING MALE BOT ENFORCEMENT ===")
for inp, exp in test_cases_male:
    out = enforce_speaker_gender(inp, "male")
    print(f"INPUT:  {inp}")
    print(f"OUTPUT: {out}")
    print(f"MATCH:  {out == exp}\n")

print("=== TESTING FEMALE BOT ENFORCEMENT ===")
for inp, exp in test_cases_female:
    out = enforce_speaker_gender(inp, "female")
    print(f"INPUT:  {inp}")
    print(f"OUTPUT: {out}")
    print(f"MATCH:  {out == exp}\n")
