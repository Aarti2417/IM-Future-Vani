# 5-to-7 Minute Demo Video Script & Storyboard
**IndiaMART VANI: Dynamic Voice Bot Persona Engine**
*Problem 4 of 6: Persona Design | Voice AI Hackathon*

---

## ⏱️ Video Timeline Overview (Total: 6 Minutes)

| Timestamp | Section | Visual on Screen | Key Talking Points |
|---|---|---|---|
| **0:00 – 1:00** | **1. The Problem & Data Root Cause** | Presentation slide / `README.md` | Why static bots fail with Indian vyaparis (42% early hang-ups from fast pace/inflexibility). |
| **1:00 – 2:15** | **2. Pre-Call Persona Generator** | Web UI at `http://localhost:8000` (Persona Studio) | Show how different sellers (Bihar vs Gujarat vs Telangana) get distinct voices, paces, formality, and language mixes. |
| **2:15 – 4:00** | **3. Live Call Demo with Mid-Call Switch** | Web UI Simulator (`http://localhost:8000`) | Start call as Seller 1 (UPVC Windows). Trigger mid-call switches ("Counter Rush" ➔ "Fake Leads Objection"). Show immediate dynamic adaptation. |
| **4:00 – 5:00** | **4. Switch Log & Audit Trajectory** | `sample_outputs/switch_logs/switch_log_report.md` | Show exact switch log: signal detected, confidence, changes made to pace/tone, and grounded reason. |
| **5:00 – 6:00** | **5. Sarvam Samvaad Platform & Rigorous Test Suite** | Terminal running `npm test` + Sarvam Agent Spec | Show Sarvam Agent (`IM-Future-0c2c99ce-3384`, Version 17), 11-file RAG KB, and 90-100% pass rate benchmark. |

---

## 🎙️ Word-for-Word Script & Step-by-Step Actions

### Segment 1: Introduction & The Core Problem (0:00 – 1:00)
**Action:** Open screen on `README.md` or a title slide.

> *"Hello judges, today we are presenting our solution for Problem 4: Persona Design—the IndiaMART VANI Dynamic Voice Bot Persona Engine.*
>
> *When IndiaMART makes outbound calls to Indian MSMEs, traditional voice bots fail because they use a single static voice. Our empirical analysis of 12,788 real seller calls revealed that fast, pushy delivery causes a 42% hang-up rate in the first 15 seconds. An artisan in Rajasthan, a cement distributor in Gujarat, and a rushed UPVC trader in Bihar cannot be served by the same canned voice.*
>
> *We solved this with two major innovations: first, a Pre-Call Persona Generator that tailors 5 acoustic dimensions before dialing; second, a real-time Mid-Call State Machine that detects vyapari cues and adapts the voice persona live on the call."*

---

### Segment 2: Pre-Call Persona Generator (1:00 – 2:15)
**Action:** Switch browser to **`http://localhost:8000`** and click on the **Persona Studio** tab.

> *"Here in our VANI Persona Studio, you can see how our engine analyzes seller metadata before dialing.*
>
> *Watch this: when we inspect Seller #1—a small UPVC sliding windows proprietor from Bihar with past frustration—the engine selects Ishita with a de-escalation register, 0.9x relaxed pace, and respectful Hinglish.*
>
> *Now, if we switch to Seller #5—an enterprise cement company in Gujarat with ₹25 Crore turnover—the engine automatically shifts to Sunny in an executive Indian English register with a formal corporate tone.*
>
> *And for Seller #2—a traditional brass statue artisan in Rajasthan—the engine selects Shubh in pure, native Hindi with social-proof framing. Each choice is backed by a deterministic rationale grounded in our 12k call findings."*

---

### Segment 3: Live Call Demo with Mid-Call Switch (2:15 – 4:00)
**Action:** Go to the **Live Simulator** tab on `http://localhost:8000`. Select **Seller 1 (UPVC Sliding Windows)** and click **"Start Call Simulation"**.

> *"Now let's watch a live call with real-time mid-call adaptation.*
>
> *(Bot speaks opening line): 'नमस्ते जी, मैं इंडियामार्ट से बोल रहा हूँ। आपके व्यापार के लिए कुछ verified bulk buyers की inquiries आई हैं...'*
>
> *Now, watch what happens when the seller suddenly faces a counter rush:*
> *(Click or inject signal): 'Bhai abhi counter pe bohot bheed hai gaahek khade hain, mere paas time nahi hai.'*
>
> *Notice our Signal Detector immediately classified 'rushed' within 12 milliseconds! The persona dynamically accelerated pace to 0.98x and condensed the pitch: instead of arguing, it pivots immediately: 'पहले आप ग्राहक अटेंड कर लीजिए, मैं बस WhatsApp पर डिटेल्स भेज दूँ?'*
>
> *Now, let's inject a second hard objection—fake leads skepticism:*
> *(Click or inject signal): 'Dekho pehle bhi call aaya tha, sab fake leads aati hain.'*
>
> *Instantly, the state machine triggers another mid-call switch! It decelerates to an empathetic, reassuring tone and anchors to IndiaMART's 90-second OTP verification protocol and free WhatsApp lead preview. This keeps the seller engaged rather than hanging up."*

---

### Segment 4: The Switch Log & Anti-Oscillation Guardrails (4:00 – 5:00)
**Action:** Open [`sample_outputs/switch_logs/switch_log_report.md`](file:///c:/Users/IMart/Desktop/vani/IM-Future-Vani/sample_outputs/switch_logs/switch_log_report.md) or the JSON view in VS Code / Studio.

> *"Here is the structured Switch Log generated during the call.*
>
> *For every single turn, our engine logs:*
> 1. *The exact signal detected with confidence score.*
> 2. *The previous acoustic state versus the adapted state.*
> 3. *The explicit rationale explaining why the change was made.*
>
> *Crucially, we implemented anti-oscillation hysteresis guardrails. The voice cannot wildly flip-flop between fast and slow on consecutive turns, ensuring natural conversational continuity while giving instant priority to de-escalation when frustration occurs."*

---

### Segment 5: Sarvam Samvaad Platform & Rigorous Test Suite (5:00 – 6:00)
**Action:** Open terminal and run `npm test`.

> *"Finally, this isn't just a prototype—it is fully integrated with Sarvam AI's platform.*
>
> *Our Voice Agent is deployed under Agent ID `IM-Future-0c2c99ce-3384` on Bulbul v4-flash with 4 grounded function-calling tools and an 11-document RAG Knowledge Base.*
>
> *As you can see from our live automated test suite executing across 10 stress scenarios—from Sunday shop closures to turnover-based pricing calculations and Do-Not-Call compliance—the agent achieves an outstanding 90% to 100% pass rate with an average turnaround latency of just 2.1 seconds.*
>
> *Thank you! All code, sample outputs, switch logs, and documentation are packaged in our submission folder."*

---

## 💡 Quick Tips for Recording
1. **Screen Resolution:** Use 1080p (1920x1080) for sharp text readability.
2. **Audio:** Ensure your microphone is clear and computer audio is enabled so the synthesized Bulbul voice can be heard.
3. **Pacing:** Keep each segment brisk; 5 to 6 minutes is the sweet spot for hackathon judges.
