"""
==============================================================================
Hackathon Sample Output Generator - Problem 4: Persona Design
==============================================================================
Generates all mandatory deliverables:
  1. Persona generator running on all 10 sample seller files
  2. Persona spec per seller with detailed reasoning for each choice
  3. Live demo mid-call switch simulation
  4. Structured Switch Log (signal detected, change made, reason)
  5. Summary markdown matrices and transcripts
==============================================================================
"""

import os
import sys
import json
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from src.persona_generator import PersonaGenerator
from src.signal_detector import SignalDetector
from src.persona_manager import PersonaManager
from src.call_simulator import CallSimulator

DATA_SAMPLE_PATH = os.path.join(BASE_DIR, "data_sample", "sellers.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "sample_outputs")
PERSONAS_DIR = os.path.join(OUTPUT_DIR, "personas")
SWITCH_LOGS_DIR = os.path.join(OUTPUT_DIR, "switch_logs")
TRANSCRIPTS_DIR = os.path.join(OUTPUT_DIR, "call_transcripts")

os.makedirs(PERSONAS_DIR, exist_ok=True)
os.makedirs(SWITCH_LOGS_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)


def generate_seller_personas():
    print("=== 1. Generating Persona Specs for Sample Sellers ===")
    with open(DATA_SAMPLE_PATH, "r", encoding="utf-8") as f:
        sellers = json.load(f)

    generator = PersonaGenerator()
    summary_rows = []

    for idx, s in enumerate(sellers, 1):
        seller_id = str(s.get("fk_glusr_usr_id"))
        category = s.get("top_category_1", "General")
        state = s.get("seller_state", "Unknown")
        turnover = str(s.get("annual_turnover", "Not Specified"))
        business_type = s.get("business_type", "Proprietorship")
        
        persona = generator.generate_persona(s)
        p_dict = persona.to_dict()

        # Save individual JSON
        file_slug = f"seller_{idx:02d}_{seller_id}_{category.lower().replace(' ', '_').replace('/', '_')}"
        json_path = os.path.join(PERSONAS_DIR, f"{file_slug}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "seller_metadata": s,
                "persona_spec": p_dict
            }, f, indent=2, ensure_ascii=False)

        # Save individual Markdown with detailed reasoning
        md_path = os.path.join(PERSONAS_DIR, f"{file_slug}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# Persona Specification: Seller {seller_id}\n\n")
            f.write(f"**Category:** {category} | **State:** {state} | **Turnover:** {turnover} | **Structure:** {business_type}\n\n")
            f.write(f"**Target Rationale:** {s.get('reason', 'N/A')}\n\n")
            f.write("## 1. Selected Voice Persona Configuration\n\n")
            f.write(f"| Parameter | Value |\n|---|---|\n")
            f.write(f"| **Voice ID** | `{persona.voice_id}` ({persona.voice_name}) |\n")
            f.write(f"| **Gender** | `{persona.gender}` |\n")
            f.write(f"| **Pace** | `{persona.pace}x` |\n")
            f.write(f"| **Pitch Register** | `{persona.pitch_register}` |\n")
            f.write(f"| **Formality** | `{persona.formality}` |\n")
            f.write(f"| **Tone** | `{persona.tone}` |\n")
            f.write(f"| **Language Mix** | `{persona.language_mix}` |\n")
            f.write(f"| **Script Strategy** | `{persona.script_strategy}` |\n")
            f.write(f"| **Opening Line** | *\"{persona.opening_line}\"* |\n\n")

            f.write("## 2. Reasons for Each Choice (Grounded Rationale)\n\n")
            for param, explanation in persona.rationale.items():
                f.write(f"### • Choice: `{param.replace('_', ' ').title()}`\n")
                f.write(f"{explanation}\n\n")

            f.write("## 3. Past Call Evidence & Behavior Grounding\n\n")
            f.write(f"- **Avg Answered Duration:** {s.get('avg_answered_call_sec', 0)} seconds\n")
            f.write(f"- **Past Objections Observed:** `{s.get('past_objections', 'None')}`\n")
            f.write(f"- **Historical Outcomes:** `{s.get('past_dispositions_detailed', 'None')}`\n")
            f.write(f"- **Frustration Flag:** `{s.get('showed_frustration', 0)}` (1=High, 0=None)\n")

        summary_rows.append({
            "id": seller_id,
            "category": category,
            "state": state,
            "turnover": turnover,
            "voice": persona.voice_name,
            "language": persona.language_mix,
            "tone": persona.tone,
            "strategy": persona.script_strategy,
            "pace": f"{persona.pace}x"
        })
        print(f"  [OK] Generated {file_slug} ({persona.voice_name}, {persona.language_mix})")

    # Save Persona Spec Summary Matrix
    summary_md_path = os.path.join(PERSONAS_DIR, "persona_spec_summary.md")
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write("# IndiaMART VANI - Persona Specification Summary Matrix\n\n")
        f.write("Comparative matrix of all 10 sample sellers showing distinct persona fit and tuning across dimensions:\n\n")
        f.write("| Seller ID | Category | State | Turnover | Selected Voice | Language Mix | Tone | Strategy | Pace |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for r in summary_rows:
            f.write(f"| `{r['id']}` | {r['category']} | {r['state']} | {r['turnover']} | **{r['voice']}** | `{r['language']}` | `{r['tone']}` | `{r['strategy']}` | {r['pace']} |\n")
        f.write("\n## Key Design Principles Demonstrated\n")
        f.write("1. **Geographic Distinctness:** Southern sellers receive Indian English / neutral diction; traditional Hindi-belt traders receive pure Hindi / localized Hinglish.\n")
        f.write("2. **Turnover-Tiered Formality:** Large turnover (5-25 Cr) receives formal corporate framing (`formal_corporate`); small proprietors receive respectful peer warmth (`respectful_warm`).\n")
        f.write("3. **Behavioral De-escalation:** Sellers with past frustration receive slower, empathetic calming registers rather than aggressive sales pitches.\n")

    print(f"[OK] Wrote Summary Matrix to {summary_md_path}")


def generate_mid_call_switch_demo():
    print("\n=== 2. Simulating Live Demo with Mid-Call Switches ===")
    detector = SignalDetector()

    # Load Seller 1 (UPVC Sliding Windows from Bihar)
    with open(DATA_SAMPLE_PATH, "r", encoding="utf-8") as f:
        seller_data = json.load(f)[0]

    initial_persona = PersonaGenerator().generate_persona(seller_data)
    manager = PersonaManager(initial_persona)

    # Scenario: 5-turn call with 2 distinct mid-call switches:
    # Turn 1: Normal greeting
    # Turn 2: Seller exhibits "Counter Rush / Busy" -> Switch 1
    # Turn 3: Seller exhibits "Fake Leads Skepticism / Frustration" -> Switch 2
    # Turn 4: Seller asks for pricing
    # Turn 5: Seller agrees to Monday appointment

    dialogue_script = [
        {
            "turn": 1,
            "seller_speech": "Haanji kaun bol raha hai?",
            "context": "Call connected, seller answers"
        },
        {
            "turn": 2,
            "seller_speech": "Bhai abhi counter pe bohot bheed hai gaahek khade hain, mere paas time nahi hai jaldi bolo.",
            "context": "Seller interrupted by retail customer rush"
        },
        {
            "turn": 3,
            "seller_speech": "Dekho pehle bhi IndiaMART se phone aaya tha, sab fake leads aati hain bekaar me time kharab mat karo.",
            "context": "Seller voices deep distrust / past frustration"
        },
        {
            "turn": 4,
            "seller_speech": "Accha WhatsApp pe dekhunga. Vaise iska saal ka kharcha kitna hota hai?",
            "context": "Seller inquires on cost structure"
        },
        {
            "turn": 5,
            "seller_speech": "Theek hai, Somwar subah 11 baje detail me call karwa do relationship manager se.",
            "context": "Seller commits to appointment"
        }
    ]

    switch_logs = []
    full_transcript = []

    print(f"Initial Persona: Voice={manager.active_persona.voice_name}, Tone={manager.active_persona.tone}, Pace={manager.active_persona.pace}x, Strategy={manager.active_persona.script_strategy}\n")

    for step in dialogue_script:
        t_num = step["turn"]
        speech = step["seller_speech"]
        
        # 1. Detect Signal
        signal = detector.detect(speech)

        # 2. Check for mid-call adaptation
        event = manager.adapt(signal, t_num)

        if event:
            switch_entry = {
                "turn": t_num,
                "timestamp_offset_sec": (t_num - 1) * 24 + 12,
                "seller_utterance": speech,
                "signal_detected": {
                    "primary_signal": event.signal_detected,
                    "confidence": event.signal_confidence,
                    "cues_matched": event.cues
                },
                "changes_made": event.changes_made,
                "reason": event.adaptation_rationale,
                "previous_state": event.previous_state,
                "new_state": event.new_state
            }
            switch_logs.append(switch_entry)
            print(f"  [ADAPTATION] MID-CALL SWITCH DETECTED at Turn {t_num}!")
            print(f"     Signal: {event.signal_detected} (Conf: {event.signal_confidence})")
            print(f"     Changes: {event.changes_made}")
            print(f"     Reason: {event.adaptation_rationale}\n")

        # Mock Bot Response matching adapted persona
        if t_num == 1:
            bot_reply = "नमस्ते जी, मैं इंडियामार्ट से बोल रहा हूँ। आपके UPVC sliding windows के लिए कुछ verified bulk buyers की inquiries आई हैं, क्या दो मिनट बात हो सकती है?"
        elif t_num == 2:
            bot_reply = "अरे बिल्कुल सर, मैं समझ गया, पहले आप ग्राहक अटेंड कर लीजिए। मैं कोई डिस्टर्ब नहीं करूँगा, बस WhatsApp पर 2 verified buyers की डिटेल्स भेज दूँ?"
        elif t_num == 3:
            bot_reply = "सर आपकी नाराज़गी बिल्कुल जायज़ है। पर अब हमारा नया सिस्टम 90-second OTP verification के बाद ही बायर कनेक्ट करता है। आप खुद WhatsApp पे चेक कर लीजिए, कोई पैसा नहीं लग रहा।"
        elif t_num == 4:
            bot_reply = "आपके टर्नओवर के हिसाब से Mini Leader प्लान बेस्ट है—साल का ₹28,000 + GST, यानी सिर्फ ₹77 प्रतिदिन। 1 भी बल्क आर्डर से पूरा खर्चा निकल जाता है।"
        elif t_num == 5:
            bot_reply = "बहुत बढ़िया जी, सोमवार सुबह 11 बजे का स्लॉट पक्का कर दिया है। आपका दिन शुभ हो!"

        full_transcript.append({
            "turn": t_num,
            "speaker": "Seller",
            "text": speech
        })
        full_transcript.append({
            "turn": t_num,
            "speaker": "VANI Voice Bot",
            "text": bot_reply,
            "active_persona": {
                "tone": manager.active_persona.tone,
                "pace": manager.active_persona.pace,
                "strategy": manager.active_persona.script_strategy
            }
        })

    # Save Switch Log JSON
    switch_log_json_path = os.path.join(SWITCH_LOGS_DIR, "switch_log.json")
    with open(switch_log_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": "call_demo_live_switch_01",
            "seller_id": str(seller_data.get("fk_glusr_usr_id")),
            "initial_persona": initial_persona.to_dict(),
            "total_switches": len(switch_logs),
            "switch_events": switch_logs
        }, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved structured Switch Log JSON to {switch_log_json_path}")

    # Save Switch Log Markdown Report
    switch_log_md_path = os.path.join(SWITCH_LOGS_DIR, "switch_log_report.md")
    with open(switch_log_md_path, "w", encoding="utf-8") as f:
        f.write("# IndiaMART VANI - Mid-Call Persona Switch Log Report\n\n")
        f.write("## Overview\n")
        f.write("During live interaction, human vyaparis exhibit sudden situational shifts (counter rushes, skepticism, price hesitation). ")
        f.write("VANI continuously analyzes seller speech and acoustic cues to dynamically pivot persona parameters without dropping call rapport.\n\n")
        f.write(f"**Total Mid-Call Switches in Demo:** {len(switch_logs)}\n\n")

        for idx, sw in enumerate(switch_logs, 1):
            f.write(f"### Switch #{idx}: Turn {sw['turn']} (at ~{sw['timestamp_offset_sec']}s)\n\n")
            f.write(f"- **Seller Spoke:** *\"{sw['seller_utterance']}\"*\n")
            f.write(f"- **Signal Detected:** `{sw['signal_detected']['primary_signal']}` (Confidence: `{sw['signal_detected']['confidence']}`)\n")
            f.write(f"- **Cues Matched:** `{', '.join(sw['signal_detected']['cues_matched'])}`\n")
            f.write(f"- **Changes Made to Persona:**\n")
            f.write(f"  - **Tone:** `{sw['previous_state']['tone']}` -> **`{sw['new_state']['tone']}`**\n")
            f.write(f"  - **Pace:** `{sw['previous_state']['pace']}x` -> **`{sw['new_state']['pace']}x`**\n")
            f.write(f"  - **Script Strategy:** `{sw['previous_state']['script_strategy']}` -> **`{sw['new_state']['script_strategy']}`**\n")
            f.write(f"- **Why This Change Was Made:**\n")
            f.write(f"  > *\"{sw['reason']}\"*\n\n")
            f.write("---\n\n")

        f.write("## Full Annotated Dialogue Transcript\n\n")
        for item in full_transcript:
            role = item["speaker"]
            if role == "Seller":
                f.write(f"**Turn {item['turn']} [Seller]:** \"{item['text']}\"\n\n")
            else:
                p = item["active_persona"]
                f.write(f"**Turn {item['turn']} [VANI Bot]** *(Tone: `{p['tone']}`, Pace: `{p['pace']}x`, Strategy: `{p['strategy']}`)*:\n")
                f.write(f"> \"{item['text']}\"\n\n")

    print(f"[OK] Saved Switch Log Markdown to {switch_log_md_path}")


if __name__ == "__main__":
    generate_seller_personas()
    generate_mid_call_switch_demo()
    print("\nAll sample outputs successfully generated in 'sample_outputs/'!")
