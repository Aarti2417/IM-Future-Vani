# IndiaMART VANI: Dynamic Voice Bot Persona Engine
### Problem 4 of 6: Persona Design | Voice AI Hackathon

> **Transforming IndiaMART's Voice Bot (VANI) from a one-size-fits-all voice into an adaptive, hyper-personalized conversational intelligence.**
> Grounded in empirical analysis of **12,788 IndiaMART calls**, powered by **Sarvam AI (Bulbul v4-flash)**, and equipped with **real-time mid-call behavioral adaptation**.

---

## 🏆 Key Features

1. **Pre-Call Persona Generation (`src/persona_generator.py`)**:
   - Analyzes seller turnover, business type, state, product category, engagement duration, and past objections.
   - Tailors 5 persona dimensions:
     - **Voice**: Speaker ID (`shubh_enhi_ads`, `aditi_enhi_ads`, `amartya_enhi_ads`), Gender, Pitch Register, Conversational Pace (0.85x – 1.18x).
     - **Formality**: `respectful_warm` ("Aap" / "Ji"), `formal_corporate` ("Sir" / executive), `casual_friendly`.
     - **Tone**: `consultative`, `direct_closing`, `empathetic_problem_solver`, `reassuring_patient`.
     - **Language Mix**: Pure Hindi, Hinglish, Indian English.
     - **Script Strategy**: Social Proof (local cluster validation), ROI Numbers (quantified pipeline), Product Features (TrustSEAL), Problem Solving (addressing churn/past issues).
   - Generates tailored opening greetings and detailed evidence-backed rationales.

2. **Ultra-Low-Latency Signal Detection (`src/signal_detector.py`)**:
   - Classifies 7 critical behavioral signals in `< 10ms`:
     - 🏃 `rushed`: Time-constrained, driving, factory floor.
     - ❓ `confused`: Bewildered, unclear about intent.
     - 🛑 `frustrated`: Hostile, irritated, do-not-call risk.
     - 💰 `hesitant`: Skeptical, past bad experience, price-sensitive.
     - ✨ `engaged`: Inquisitive, asking about pricing and leads.
     - ⚡ `interrupted`: Barge-in detection.
     - 🔊 `noise`: High factory/traffic interference.

3. **Dynamic Mid-Call Adaptation State Machine (`src/persona_manager.py`)**:
   - Transitions delivery pace, tone, language mix, and strategy on the fly.
   - **Anti-Oscillation Guardrails & Hysteresis**: Prevents unnatural flip-flopping; clamps pace steps to $\Delta \le \pm 0.15$.
   - **De-escalation Priority**: Frustration immediately halts commercial pitching and shifts to sincere apology and rescheduling.
   - Logs full adaptation trajectory for call auditing.

4. **Persistent Persona Memory & Evolution (`src/persona_memory.py`)**:
   - Stores winning persona configurations in `personas/seller_memory.json`.
   - Adapts baseline starting pace and tone for a seller's future calls based on past successful meetings.

5. **Sarvam AI Integration & Offline Resilience (`src/sarvam_client.py`)**:
   - Seamless integration with Sarvam Bulbul TTS (`bulbul:v4-flash`), Saaras STT (`saaras:v3`), and LLM completions.
   - Built-in `MockSarvamClient` for 100% offline development, testing, and deterministic evaluation.
   - Full parameter documentation in [`docs/assumptions.md`](file:///c:/Users/Imart/Desktop/IM%20Future/docs/assumptions.md).

6. **Rich Interactive Web Dashboard (`demo/`)**:
   - Modern dark-theme UI with glassmorphism and IndiaMART styling.
   - 4 realistic seller archetypes ready for 1-click simulation.
   - Live phone simulator with animated waveform, audio playback, and quick-signal injection buttons.
   - Persona Studio, Signal Lab, Memory Explorer, and 12.8k Call Evidence charts.

---

## 📊 Empirical Grounding (12,788 Analyzed Calls)

| Parameter | Best Performing | Conversion Rate | Legacy Bot Baseline | Key Insight |
|---|---|---|---|---|
| **Pace** | **Slow (0.88x - 0.92x)** | **38.9%** | 14.5% (Fast) | Patient delivery drives +168% higher meeting rate for MSMEs |
| **Tone** | **Warm / Consultative** | **33.5%** | 9.1% (Pushy) | Hard-sell leads to rapid hang-ups; consultative listening wins |
| **Frustrated Sellers** | **Empathetic De-escalation** | **Avoids Churn** | **0.0%** (Static Bot) | Static bot failed 100% of irritated calls; VANI secures callbacks |
| **Enterprise (>5Cr)** | **Crisp Pace (1.05x)** | **33.3%** | 21.8% | High-turnover executives demand concise ROI over long pleasantries |

---

## 🚀 Quickstart & Demo

### 1. Launch the Interactive Web Demo
```bash
python demo/server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

### 2. Run the Unit & Integration Test Suite
```bash
python -m tests.run_tests -v
```
All 13 test cases pass with zero external dependencies.

### 3. Run Command-Line Simulation
```bash
python -c "from src.call_simulator import CallSimulator; import json; s=json.load(open('data_sample/sellers.json'))[0]; sim=CallSimulator(); res=sim.run_simulation(s); print('Result:', res.disposition, 'Adaptations:', res.adaptations_count)"
```

### 4. Optional: Configure Live Sarvam AI API Key
Create a `.env` file in the project root:
```env
SARVAM_API_KEY=your_actual_sarvam_api_key_here
```
If omitted, VANI automatically runs in resilient mock mode with realistic responses.

---

## 📁 Repository Structure

```
IM Future/
├── demo/                          # Interactive Web Application
│   ├── index.html                 # Semantic HTML5 dashboard
│   ├── styles.css                 # Dark-mode glassmorphism CSS
│   ├── app.js                     # Simulation & audio logic
│   ├── server.py                  # Standard Python HTTP & REST API server
│   └── scenarios/                 # Curated realistic seller archetypes
├── src/                           # Core Engine Modules
│   ├── persona_generator.py       # Pre-call multi-dimensional persona builder
│   ├── signal_detector.py         # Real-time behavioral signal classifier
│   ├── persona_manager.py         # Mid-call adaptation state machine & hysteresis
│   ├── persona_memory.py          # Cross-call persistent memory & evolution
│   ├── call_simulator.py          # End-to-end voice loop simulator
│   ├── sarvam_client.py           # Sarvam AI TTS/STT client + Mock fallback
│   └── evidence.py                # 12,788 call analyzer & style tagging
├── docs/                          # Architectural Documentation
│   ├── assumptions.md             # Engineering choices & Sarvam parameter mapping
│   ├── call_quality.md            # Evaluator dataset summary
│   └── data_summary.md            # Stage 1 data distribution report
├── evidence/                      # Empirical Outputs
│   ├── evidence_summary.md        # Cross-tabulation conversion insights
│   └── evidence_table.csv         # 12,788 tagged call style records
├── personas/                      # Memory Storage
│   └── seller_memory.json         # Learned per-seller profiles & trajectories
├── data_sample/                   # Sample Datasets
│   └── sellers.json               # Representative MSME & Enterprise profiles
└── tests/                         # Test Suites
    ├── run_tests.py               # Standard library unittest suite (13 passing tests)
    └── test_persona_engine.py     # Pytest test suite
```
