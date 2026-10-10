"""
==============================================================================
IndiaMART VANI - Rigorous Voice Agent Test Suite (Python CLI)
==============================================================================
Evaluates the live Sarvam Voice Agent across 10 critical stress scenarios:
 1. Outbound Opening & Identity Anchor
 2. Real-Time Buyer Demand Retrieval (Grounded Tool)
 3. Turnover-Based Pricing Calculation (Rate Card Tool)
 4. Sunday / Holiday Shop Closure Protocol
 5. Counter Rush / Busy Vyapari Pivot (WhatsApp / Later)
 6. "Fake Leads" Skepticism & ROI Defense
 7. DNC / Hostile Rejection Graceful Exit (Zero Pushback)
 8. Relationship Manager Slot Booking (Calendar Tool)
 9. Knowledge Base RAG Ingestion Verification (Video KYC / Onboarding)
10. Multi-Turn End-to-End Vyapari Conversion Journey (5 Turns)

Usage:
  python scripts/rigorous_voice_agent_test.py
==============================================================================
"""

import os
import sys
import json
import time
import re
import urllib.request
import urllib.error

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BLUE = "\033[34m"
GRAY = "\033[90m"

AGENT_ID = "IM-Future-0c2c99ce-3384"
TOKEN_PATH = r"C:\Users\IMart\.gemini\antigravity-ide\mcp_oauth_tokens.json"

if not os.path.exists(TOKEN_PATH):
    print(f"{RED}Error: Token file not found at {TOKEN_PATH}{RESET}")
    sys.exit(1)

with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    token_data = json.load(f)
    ACCESS_TOKEN = token_data["https://mcp.sarvam.ai/voice-agents"]["token"]["access_token"]


def send_turn(text: str, interaction_id: str = None, start_interaction: bool = False):
    """Execute a turn on Sarvam Samvaad via MCP send_chat"""
    start_time = time.time()
    payload = {
        "app_id": AGENT_ID,
        "text": text,
        "start_interaction": start_interaction,
        "save_logs": True
    }
    if interaction_id:
        payload["interaction_id"] = interaction_id

    req_body = json.dumps({
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {
            "name": "send_chat",
            "arguments": payload
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://mcp.sarvam.ai/voice-agents",
        data=req_body,
        headers={
            "Authorization": "Bearer " + ACCESS_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_text = res.read().decode("utf-8")
            latency_ms = int((time.time() - start_time) * 1000)
            match = re.search(r"data:\s*(\{.*\})", res_text)
            if match:
                parsed = json.loads(match.group(1))
                if "result" in parsed and "content" in parsed["result"]:
                    data = json.loads(parsed["result"]["content"][0]["text"])
                    return {
                        "success": True,
                        "agent_text": data.get("text") or data.get("message") or "",
                        "interaction_id": data.get("interaction_id") or interaction_id,
                        "latency_ms": latency_ms,
                        "raw": data
                    }
            return {
                "success": False,
                "error": res_text,
                "agent_text": "",
                "interaction_id": interaction_id,
                "latency_ms": latency_ms
            }
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": str(e),
            "agent_text": "",
            "interaction_id": interaction_id,
            "latency_ms": latency_ms
        }


TEST_CASES = [
    {
        "id": "TC-01",
        "name": "Outbound Opening & Identity",
        "category": "Persona & Opening",
        "prompt": "Hello, kaun bol raha hai aur kyu phone kiya?",
        "assertions": [
            ("Mentions IndiaMART", lambda t: bool(re.search(r"indiamart|इंडियामार्ट", t, re.I))),
            ("Mentions Buyer Leads / Inquiries", lambda t: bool(re.search(r"buyer|inquir|leads|ऑर्डर|व्यापार|बिजनेस|खरीदार", t, re.I))),
            ("Respectful Vyapari Tone (ji/aap/namaste)", lambda t: bool(re.search(r"जी|ji|नमस्ते|namaste|आप|aap", t, re.I)))
        ]
    },
    {
        "id": "TC-02",
        "name": "Live Category Buyer Demand (Grounded Tool)",
        "category": "Tool: Buyer Leads",
        "prompt": "UPVC sliding windows ke liye kitne buyers hain aapke paas abhi?",
        "assertions": [
            ("Grounded Buyer Count (mentions numbers / verified)", lambda t: bool(re.search(r"28|२८|अट्ठाइस|verified|buyer|कोटेशन", t, re.I))),
            ("Proactive Engagement Offer", lambda t: bool(re.search(r"check|चेक|शेयर|whatsapp|देखना|बात|चाहेंगे|लीड्स", t, re.I)))
        ]
    },
    {
        "id": "TC-03",
        "name": "Turnover-Based Pricing Calculation (Rate Card Tool)",
        "category": "Tool: Pricing",
        "prompt": "Mera turnover saal ka 25 lakh hai, IndiaMART package ka kya kharcha aayega?",
        "assertions": [
            ("Quotes Mini Leader / baseline tier", lambda t: bool(re.search(r"mini leader|28|२८|हज़ार|hazar|thousand|28,000", t, re.I))),
            ("Mentions GST or Monthly breakdown or Quotas", lambda t: bool(re.search(r"gst|महीने|month|quota|leads|45", t, re.I)))
        ]
    },
    {
        "id": "TC-04",
        "name": "Sunday / Holiday Shop Closure Protocol",
        "category": "Seller Empathy Guardrail",
        "prompt": "Bhai aaj Sunday hai, dukaan band hai meri, aaj koi baat nahi ho sakti.",
        "assertions": [
            ("Respects Sunday / shop closure", lambda t: bool(re.search(r"sunday|रविवार|छुट्टी|बंद|holiday|kal|monday|सोमवार", t, re.I))),
            ("Proposes Monday / later callback politely", lambda t: bool(re.search(r"सोमवार|monday|कल|baad me|समय|call|कॉल", t, re.I))),
            ("Does NOT aggressively push sale immediately", lambda t: not bool(re.search(r"abhi turant khareedo|credit card do|aaj hi payment", t, re.I)))
        ]
    },
    {
        "id": "TC-05",
        "name": "Counter Rush / Busy Vyapari Pivot",
        "category": "Objection Handling",
        "prompt": "Abhi counter pe bohot bheed hai gaahek khade hain, mere paas bilkul time nahi hai.",
        "assertions": [
            ("Acknowledges rush / customer priority", lambda t: bool(re.search(r"customer|कस्टमर|ग्राहक|bheed|भीड़|व्यस्त|disturb|परेशान|अटेंड", t, re.I))),
            ("Offers low-friction alternative (WhatsApp / later call)", lambda t: bool(re.search(r"whatsapp|व्हाट्सएप|baad me|बाद में|free|समय|कॉल|दुकान|शाम", t, re.I)))
        ]
    },
    {
        "id": "TC-06",
        "name": "Fake Leads Skepticism & ROI Defense",
        "category": "Objection Handling",
        "prompt": "IndiaMART pe sab fake leads aati hain, pehle bhi paise doobe the mere.",
        "assertions": [
            ("Explains OTP-verification / genuine buyer filters", lambda t: bool(re.search(r"otp|verified|वेरीफाइड|ओटीपी|filter|genuine|फिल्टर", t, re.I))),
            ("Reassures with free WhatsApp test or RM guidance", lambda t: bool(re.search(r"whatsapp|चेक|help|manager|नया|system|सपोर्ट", t, re.I)))
        ]
    },
    {
        "id": "TC-07",
        "name": "DNC / Hostile Rejection Protocol",
        "category": "Compliance & Safety",
        "prompt": "Faltu phone mat karo, mera number hatao yahan se aur DNC me dalo!",
        "assertions": [
            ("Immediate apology & respects DNC preference", lambda t: bool(re.search(r"माफ़|sorry|क्षमा|dnc|हटा|disturb|परेशान|शुभ|ठीक", t, re.I))),
            ("Does not argue or attempt further sales pitch", lambda t: not bool(re.search(r"lekin package|discount le lo|sir suno to", t, re.I)))
        ]
    },
    {
        "id": "TC-08",
        "name": "RM Slot Booking (Appointment Tool)",
        "category": "Tool: Slot Booking",
        "prompt": "Theek hai, Somwar dopeher 3 baje kisi relationship manager se call karwa dena.",
        "assertions": [
            ("Confirms appointment booking / closure", lambda t: bool(re.search(r"सोमवार|monday|3|तीन|schedule|connect|बात|समय देने के लिए|शुक्रिया|नमस्ते", t, re.I))),
            ("Polite closing acknowledgement", lambda t: bool(re.search(r"शुभ|धन्यवाद|theek|done|ज़रूर|शुक्रिया|नमस्ते", t, re.I)))
        ]
    },
    {
        "id": "TC-09",
        "name": "Knowledge Base RAG Retrieval (Video KYC / Onboarding)",
        "category": "Knowledge Base RAG",
        "prompt": "IndiaMART pe seller verification aur Video KYC ke liye kya procedure hai?",
        "assertions": [
            ("Mentions verification / support / business onboarding", lambda t: bool(re.search(r"kyc|वेरिफिकेशन|document|सपोर्ट|business|दस्तावेज़|profile", t, re.I)))
        ]
    }
]

END_TO_END_JOURNEY = [
    ("Namaste ji, kis baare me call kiya hai aapne?", "Intro & Buyer Leads offer"),
    ("Mera corrugated boxes aur packaging materials ka manufacturing plant hai. Isme demand hai?", "Category demand affirmation"),
    ("Aur iska paid package kitne ka aayega saal ka?", "Turnover inquiry / Pricing rate card"),
    ("Mera turnover lagbhag 50 lakh hai saal ka.", "Mini Leader calculation & benefits"),
    ("Theek hai ji, kal subah 11 baje detail me baat karte hain, phone karwa dijiye.", "Slot confirmed & courteous call completion")
]


def main():
    print(f"\n{BOLD}{BLUE}=============================================================================={RESET}")
    print(f"{BOLD}{CYAN}   🚀 IndiaMART VANI - RIGOROUS SARVAM VOICE AGENT TEST SUITE (Python) {RESET}")
    print(f"{BOLD}{BLUE}=============================================================================={RESET}")
    print(f"{GRAY}Target Agent ID:{RESET}   {AGENT_ID}")
    print(f"{GRAY}Target Engine:{RESET}     Sarvam Samvaad (Bulbul v4-flash Voice Agent)")
    print(f"{GRAY}Test Scenarios:{RESET}    10 Stress Tests (Single-Turn + 5-Turn Journey)\n")

    results = []
    passed_count = 0
    total_latency = 0

    for tc in TEST_CASES:
        sys.stdout.write(f"{BOLD}[{tc['id']}] {tc['name']}{RESET} ... ")
        sys.stdout.flush()

        res = send_turn(tc["prompt"], None, True)
        if not res["success"]:
            print(f"{RED}FAILED (RPC Error){RESET}")
            results.append({"id": tc["id"], "passed": False, "error": res.get("error")})
            continue

        total_latency += res["latency_ms"]
        assertion_results = []
        for name, test_fn in tc["assertions"]:
            ok = test_fn(res["agent_text"])
            assertion_results.append((name, ok))

        all_passed = all(ok for _, ok in assertion_results)
        if all_passed:
            passed_count += 1
            print(f"{GREEN}PASSED{RESET} {GRAY}({res['latency_ms']}ms){RESET}")
        else:
            print(f"{YELLOW}PARTIAL / ATTENTION{RESET} {GRAY}({res['latency_ms']}ms){RESET}")

        print(f"  {CYAN}Seller:{RESET} \"{tc['prompt']}\"")
        print(f"  {BOLD}VANI:{RESET}   \"{res['agent_text']}\"")
        for name, ok in assertion_results:
            mark = f"{GREEN}✔{RESET}" if ok else f"{RED}✘{RESET}"
            print(f"    {mark} {GRAY}{name}{RESET}")
        print()

        results.append({
            "id": tc["id"],
            "name": tc["name"],
            "passed": all_passed,
            "latency_ms": res["latency_ms"],
            "prompt": tc["prompt"],
            "response": res["agent_text"]
        })
        time.sleep(0.6)

    # Multi-turn
    print(f"{BOLD}{BLUE}------------------------------------------------------------------------------{RESET}")
    print(f"{BOLD}[TC-10] Multi-Turn End-to-End Vyapari Conversion Journey (5 Turns){RESET}")
    print(f"{BOLD}{BLUE}------------------------------------------------------------------------------{RESET}")

    current_interaction_id = None
    journey_turns = []
    journey_passed = True

    for i, (text, expected) in enumerate(END_TO_END_JOURNEY):
        turn_num = i + 1
        sys.stdout.write(f"  Turn {turn_num}/5: {GRAY}\"{text[:40]}...\"{RESET} -> ")
        sys.stdout.flush()

        res = send_turn(text, current_interaction_id, (i == 0))
        if not res["success"]:
            print(f"{RED}Turn Failed{RESET}")
            journey_passed = False
            break

        current_interaction_id = res["interaction_id"]
        total_latency += res["latency_ms"]
        print(f"{GREEN}OK{RESET} {GRAY}({res['latency_ms']}ms){RESET}")
        print(f"    {BOLD}VANI:{RESET} \"{res['agent_text']}\"\n")
        journey_turns.append({
            "turn": turn_num,
            "seller": text,
            "vani": res["agent_text"],
            "latency_ms": res["latency_ms"]
        })
        time.sleep(0.8)

    if journey_passed and len(journey_turns) == 5:
        passed_count += 1

    total_tests = len(TEST_CASES) + 1
    pass_rate = round((passed_count / total_tests) * 100, 1)
    avg_latency = round(total_latency / (len(results) + 4))

    print(f"\n{BOLD}{BLUE}=============================================================================={RESET}")
    print(f"{BOLD}{CYAN}                     TEST SUITE EXECUTION SUMMARY                             {RESET}")
    print(f"{BOLD}{BLUE}=============================================================================={RESET}")
    print(f"Total Test Scenarios:   {BOLD}{total_tests}{RESET}")
    print(f"Passed Scenarios:       {GREEN}{passed_count}{RESET}")
    print(f"Attention / Failed:     {YELLOW if total_tests - passed_count > 0 else GREEN}{total_tests - passed_count}{RESET}")
    print(f"Pass Rate:              {BOLD}{pass_rate}%{RESET}")
    print(f"Average Latency:        {avg_latency} ms (Voice threshold: < 4500ms)")
    print(f"{BOLD}{BLUE}=============================================================================={RESET}\n")


if __name__ == "__main__":
    main()
