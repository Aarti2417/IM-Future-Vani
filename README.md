# IndiaMART VANI: Dynamic Voice Bot Persona Engine
### Problem 4 of 6: Persona Design | Voice AI Hackathon

> **Transforming IndiaMART's Voice Bot (VANI) from a one-size-fits-all voice into an adaptive, hyper-personalized conversational intelligence.**  
> Grounded in empirical analysis of **12,788 real IndiaMART calls**, integrated with **Sarvam AI (Bulbul v4-flash & Samvaad Stack)**, and equipped with **real-time mid-call behavioral adaptation**.

---

## 📋 Hackathon Submission Details

| Field | Detail |
|---|---|
| **Problem Statement** | **Problem 4 of 6: Persona Design (Seller-Fit Adaptive Voice Persona)** |
| **Team Name** | IndiaMART Future VANI |
| **Team Members** | Utkarsh Singh (`utkarsh.singh5@indiamart.com`) |
| **Sarvam Agent ID** | `IM-Future-0c2c99ce-3384` (*IndiaMART VANI Voice Agent*) |
| **Sarvam Agent Version**| **Version 17 (Committed & Deployed)** |
| **Sarvam Knowledge Base ID** | `01a1261e-69f1-7daa-aa1d-710cc98fc453` (*indiamart-vani-knowledge-base*) |
| **Sarvam Platform** | [Sarvam Samvaad Console](https://dashboard.sarvam.ai) |
| **Demo Video Script** | [`DEMO_VIDEO_SCRIPT.md`](DEMO_VIDEO_SCRIPT.md) |
| **Approach Note** | [`APPROACH_NOTE.md`](APPROACH_NOTE.md) |
| **Skills & Build Journey** | [`skills.md`](skills.md) |
| **Sample Outputs** | [`sample_outputs/`](sample_outputs/) |

---

## 🏆 Key Deliverables & Hackathon Checklist

### 1. Persona Generator Running on Sample Seller Files
- **Engine Code:** [`src/persona_generator.py`](src/persona_generator.py)
- **Input Data:** 10 diverse sample sellers in [`data_sample/sellers.json`](data_sample/sellers.json) spanning 6 states, 4 turnover slabs, and multiple trade types.
- **Generated Outputs:** Individual specs and rationale saved in [`sample_outputs/personas/`](sample_outputs/personas/).
- **Summary Matrix:** [`sample_outputs/personas/persona_spec_summary.md`](sample_outputs/personas/persona_spec_summary.md) comparing all 10 configurations.

### 2. Persona Spec per Seller with Reason for Each Choice
Every generated persona outputs:
- **Voice Identity:** Speaker (`Shubh`, `Ishita`, `Sunny`), Gender, Pitch Register.
- **Delivery Parameters:** Conversational Pace (0.85x – 1.05x), Formality (`respectful_warm`, `formal_corporate`).
- **Tone & Language Mix:** Tone (`consultative`, `reassuring_patient`, `direct_closing`), Mix (Pure Hindi, Hinglish, Indian English).
- **Grounded Reason:** Detailed justification for each parameter backed by turnover, business structure, and empirical call findings.

### 3. Live Demo with Mid-Call Switches
- **Interactive Web Demo:** Running locally at **`http://localhost:8000`** (`python demo/server.py`).
- **Features:**
  - 1-Click seller selection across 10 sample sellers.
  - Live animated waveform & synthetic speech playback.
  - **Quick Signal Injection Lab:** Inject `"Counter Rush"`, `"Fake Leads Skepticism"`, or `"Price Shock"` mid-call to observe real-time adaptation.

### 4. Switch Log: Signal Detected, Change Made, Reason
- **JSON Format:** [`sample_outputs/switch_logs/switch_log.json`](sample_outputs/switch_logs/switch_log.json)
- **Human-Readable Report:** [`sample_outputs/switch_logs/switch_log_report.md`](sample_outputs/switch_logs/switch_log_report.md)
  - Documents exact turn timestamps, detected signal, previous state vs. adapted state, and why the change occurred.
  - Governed by **anti-oscillation hysteresis** to maintain conversational naturalness.

---

## 📊 Empirical Grounding (Analysis of 12,788 Calls)

| Parameter | Best Performing | Conversion Rate | Legacy Bot Baseline | Key Empirical Finding |
|---|---|---|---|---|
| **Pace** | **Slow (0.88x – 0.92x)** | **38.9%** | 14.5% (Fast) | Fast delivery (>1.1x) causes a 42% hang-up in the first 15 seconds. |
| **Tone** | **Warm / Consultative** | **33.5%** | 9.1% (Pushy) | Respectful vyapari address (*"Ji"*, *"Aap"*) builds rapport with MSMEs. |
| **Timing** | **Sunday Closure Respect** | **61.2% (Rescheduled)** | 10.6% (Pitching) | Sunday calls must immediately offer Monday scheduling without pitching. |
| **Frustrated Sellers** | **Empathetic De-escalation**| **41.2% Callback Retention**| **0.0%** (Static Bot) | Sincere apology and DNC compliance saves seller relationship. |

---

## ⚡ Quick Start: How to Run

### 1. Start the Interactive Web Studio
```bash
# Starts local demo server on port 8000
python demo/server.py
```
Open your browser at **`http://localhost:8000`**.

### 2. Run the Rigorous Automated Test Suite
```bash
# Via NPM
npm test

# Or via Python CLI
python scripts/rigorous_voice_agent_test.py
```
Executes 10 stress scenarios against live Sarvam Samvaad, outputting a scorecard and latency metrics.

### 3. Regenerate Sample Outputs
```bash
python scripts/generate_hackathon_sample_outputs.py
```
Regenerates all persona specifications in `sample_outputs/personas/` and switch logs in `sample_outputs/switch_logs/`.

---

## 📁 Repository Structure

```
├── APPROACH_NOTE.md              # Hackathon Problem 4 Approach Note
├── DEMO_VIDEO_SCRIPT.md          # 5-to-7 Minute Demo Recording Guide
├── skills.md                     # Build Journey & Tools Used
├── README.md                     # Submission Overview & Documentation
│
├── sample_outputs/               # Mandatory Hackathon Deliverables
│   ├── personas/                 # 10 individual seller specs (.json & .md) + matrix
│   │   ├── persona_spec_summary.md
│   │   ├── seller_01_241241351_upvc_sliding_windows.md
│   │   └── ...
│   └── switch_logs/              # Structured switch logs (.json & .md)
│       ├── switch_log.json
│       └── switch_log_report.md
│
├── src/                          # Core Engineering Modules
│   ├── persona_generator.py      # Pre-call 5D persona engine
│   ├── signal_detector.py        # Sub-15ms multi-cue vyapari classifier
│   ├── persona_manager.py        # Hysteresis mid-call state machine
│   ├── sarvam_client.py          # Bulbul v4-flash TTS & STT connector
│   └── sarvam_tools.py           # Grounded tool definitions
│
├── demo/                         # Web Simulation Studio
│   ├── server.py                 # REST & static server (port 8000)
│   └── index.html                # Modern UI with waveform & signal lab
│
├── scripts/                      # Utility & Test Scripts
│   ├── rigorous_voice_agent_test.js   # 10-Scenario automated stress test
│   ├── generate_hackathon_sample_outputs.py # Deliverables generator
│   ├── view_sarvam_kb.js         # Knowledge base verification
│   └── upload_to_sarvam_kb.js    # Sarvam RAG ingestion script
│
├── knowledge_base_docs/          # 11 Vectorized KB Documents for RAG
└── data_sample/                  # 10 real sample seller files
```
