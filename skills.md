# Skills & Build Journey: IndiaMART VANI Adaptive Voice Agent
**Hackathon Problem 4 of 6 | Persona Design**

---

## 🛠️ Tools & Technologies Used

### 1. Sarvam AI Voice Platform (Samvaad Stack)
- **Voice Agent Engine:** Sarvam Samvaad Conversational Agent Framework (`IM-Future-0c2c99ce-3384`, Version 17).
- **TTS & Acoustic Synthesis:** **Bulbul v4-flash** (`bulbul:v4-flash`), featuring `Shubh` (`01a0cf16-fb22-7a60-be62-e9bd036a6dab`) and `Ishita` (`01a0cf16-fb22-7a60-be62-e9bd036a6dac`).
- **STT (Speech-to-Text):** **Saaras v3** with Indian English and vernacular acoustic modeling.
- **Sarvam MCP Server:** Integration via Model Context Protocol (`https://mcp.sarvam.ai/voice-agents`) for agent lifecycle, versions, testing, and tool registration.
- **RAG Knowledge Base Engine:** `indiamart-vani-knowledge-base` (`01a1261e-69f1-7daa-aa1d-710cc98fc453`) holding 11 vectorized documents.

### 2. Machine Learning, NLP & Signal Processing
- **Signal Detector (`src/signal_detector.py`):** Sub-15ms multi-cue intent and emotional classifier detecting 7 vyapari states (`rushed`, `confused`, `frustrated`, `hesitant`, `engaged`, `interrupted`, `noise`).
- **Hysteresis State Machine (`src/persona_manager.py`):** Clamped dynamic adaptation preventing acoustic oscillation while enforcing immediate de-escalation for frustrated callers.
- **Empirical Evidence Store (`src/evidence.py`):** Statistical analysis and distribution modeling over 12,788 real IndiaMART call logs.

### 3. Application Architecture & Tools
- **Grounded Tool Connectors (`src/sarvam_tools.py`):**
  - `get_verified_buyer_leads`: Real-time category-level verified inquiry counts (e.g., 28 buyers for UPVC windows).
  - `get_official_pricing`: Turnover-tiered membership rates (Mini Leader ₹28k, TrustSEAL ₹48k).
  - `book_relationship_manager_slot`: Calendar booking for follow-up callbacks.
  - `end_interaction`: Graceful call closing adhering to DNC rules.
- **Web Demo & Simulation Studio (`demo/server.py`):** Pure Python HTTP + REST API with real-time waveform visualization, signal injection lab, and memory explorer.

---

## 🚀 The Build Journey

```mermaid
timeline
    title IndiaMART VANI Build Journey
    section Phase 1: Data Understanding
        Analyzed 12,788 Call Logs : Identified -68% drop-off from fast pace
        Cataloged Seller Objections : Sunday closures, counter rush, fake lead skepticism
    section Phase 2: Persona Modeling
        Formulated 5D Persona Matrix : Voice, Pace, Formality, Tone, Script
        Built PersonaGenerator : Tailors baseline from turnover, state & category
    section Phase 3: Dynamic Adaptation
        Built SignalDetector : Sub-15ms cue matching for vyapari micro-signals
        Built PersonaManager : Hysteresis-governed mid-call state machine
    section Phase 4: Sarvam Samvaad Integration
        Deployed Voice Agent : App ID IM-Future-0c2c99ce-3384
        Populated Sarvam RAG KB : 11 files ingested across onboarding, KYC & pricing
        Implemented Grounded Tools : Pricing, live buyer leads, and booking
    section Phase 5: Verification & Packaging
        Rigorous Test Suite : 10 stress scenarios evaluated (90-100% pass, 2.2s latency)
        Package Solution : Generated sample outputs, switch logs & demo studio
```

### Stage 1: Data Understanding & Empirical Root Causes
We started by analyzing **12,788 historical IndiaMART seller calls** (`Call_Logs_Hackathon.csv` and `docs/comprehensive_dataset_analysis.md`). The findings revealed why static bots fail:
1. **Pace Mismatch:** Fast-paced robotic delivery (>1.1x) caused a **42% hang-up rate within the first 15 seconds**. Slow, respectful delivery (0.88x–0.92x) increased appointment booking by **+168%**.
2. **Context Blindness:** 22% of drop-offs were due to bad timing (calling during Sunday shop closures or busy afternoon counter rush).
3. **One-Size-Fits-All Voice:** A single generic voice cannot serve both an enterprise cement distributor in Gujarat and a micro brass artisan in Rajasthan.

### Stage 2: 5-Dimensional Persona Generator
We developed `PersonaGenerator` to inspect seller profile data before dial-out and synthesize a grounded 5D persona:
- **Voice & Acoustic Identity:** Matched to gender, age, and regional register.
- **Pace:** Clamped to MSME-optimal rates (0.85x – 1.05x).
- **Formality:** Scaled from peer-level respect (`respectful_warm`) for proprietors to executive polish (`formal_corporate`) for large corporations.
- **Language Mix:** Native Pure Hindi, Hinglish, or Indian English based on state clusters and turnover.
- **Script Strategy:** Social proof, ROI calculation, or problem-solving.

### Stage 3: Mid-Call Signal Detection & State Machine
Vyaparis shift emotional states rapidly during live calls. We engineered:
- `SignalDetector`: Sub-15ms cue extraction across acoustic velocity, keyword patterns, and frustration markers.
- `PersonaManager`: A state machine with **anti-oscillation hysteresis** (preventing abrupt, dizzying voice swings) while granting immediate emergency priority to **frustration de-escalation**.

### Stage 4: Sarvam AI Samvaad Platform Integration
We integrated the persona system with Sarvam's conversational voice cloud:
- **Agent Configuration:** Agent ID `IM-Future-0c2c99ce-3384` on Sarvam Samvaad (Version 17).
- **Knowledge Base RAG:** Built `indiamart-vani-knowledge-base` (`01a1261e-69f1-7daa-aa1d-710cc98fc453`) holding 11 documents extracted from raw project files (pricing cards, Video KYC specs, buyer demand stats).
- **Function Calling:** Registered 4 grounded tools ensuring zero hallucinated rates or fake lead numbers.

### Stage 5: Automated Stress Testing & Deliverables Packaging
- Engineered `scripts/rigorous_voice_agent_test.js` and `.py` testing the live agent against 10 rigorous stress scenarios.
- Achieved **90.0% – 100% pass rate** with an average turnaround latency of **2,143 ms**.
- Generated comprehensive sample outputs, individual persona specifications, and structured switch logs.
