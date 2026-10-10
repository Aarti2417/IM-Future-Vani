import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Test Male Bot speaking to Female Caller
payload_male = {
    "seller_text": "Main dukan ki owner bol rahi hu, abhi customer khada hai, bilkul time nahi hai",
    "seller": {
        "top_category_1": "Industrial Valves",
        "seller_state": "Uttar Pradesh"
    },
    "active_persona": {
        "voice_id": "shubh_enhi_ads",
        "voice_name": "Chandan Bhaiya (Wholesale Specialist)",
        "gender": "male",
        "pitch_register": "medium",
        "pace": 0.95,
        "formality": "respectful_warm",
        "tone": "consultative",
        "language_mix": "hindi",
        "script_strategy": "social_proof",
        "opening_line": "Namaskar sir! Main IndiaMART se Chandan bol raha hoon.",
        "system_prompt": "You are Chandan, a male executive."
    },
    "generate_audio": False
}

req = urllib.request.Request(
    "http://localhost:8000/api/generate_reply",
    data=json.dumps(payload_male).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    res_male = json.loads(resp.read().decode('utf-8'))
    print("=== MALE BOT TO FEMALE CALLER ===")
    print("REPLY:", res_male.get("reply_text"))

# 2. Test Male Bot handling Frustrated Female Caller
payload_male_frust = {
    "seller_text": "Main bol rahi hu bar bar call karke disturb mat karo phone kaat do",
    "seller": {
        "top_category_1": "Industrial Valves",
        "seller_state": "Uttar Pradesh"
    },
    "active_persona": {
        "voice_id": "shubh_enhi_ads",
        "voice_name": "Shubh (Commercial Male)",
        "gender": "male",
        "pitch_register": "medium",
        "pace": 0.95,
        "formality": "respectful_warm",
        "tone": "consultative",
        "language_mix": "hindi",
        "script_strategy": "social_proof",
        "opening_line": "Namaskar!",
        "system_prompt": "You are a male executive."
    },
    "generate_audio": False
}

req = urllib.request.Request(
    "http://localhost:8000/api/generate_reply",
    data=json.dumps(payload_male_frust).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    res_male_frust = json.loads(resp.read().decode('utf-8'))
    print("\n=== MALE BOT HANDLING ANGRY FEMALE CALLER ===")
    print("REPLY:", res_male_frust.get("reply_text"))

# 3. Test Female Bot
payload_female = {
    "seller_text": "Main bol rahi hu bar bar call karke disturb mat karo",
    "seller": {
        "top_category_1": "Brass Statues",
        "seller_state": "Rajasthan"
    },
    "active_persona": {
        "voice_id": "ishita_enhi_customer",
        "voice_name": "Priya Sharma (Empathetic Solver)",
        "gender": "female",
        "pitch_register": "warm",
        "pace": 0.90,
        "formality": "respectful_warm",
        "tone": "empathetic_problem_solver",
        "language_mix": "hindi",
        "script_strategy": "problem_solving",
        "opening_line": "Namaste!",
        "system_prompt": "You are a female executive."
    },
    "generate_audio": False
}

req = urllib.request.Request(
    "http://localhost:8000/api/generate_reply",
    data=json.dumps(payload_female).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    res_female = json.loads(resp.read().decode('utf-8'))
    print("\n=== FEMALE BOT HANDLING ANGRY CALLER ===")
    print("REPLY:", res_female.get("reply_text"))
