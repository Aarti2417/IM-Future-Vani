# Architecture & Assumptions Document
## IndiaMART VANI Voice Bot: Persona Design & Dynamic Mid-Call Adaptation

### 1. Executive Summary & Problem Context
Today, the IndiaMART Voice Bot (VANI) interacts with diverse sellers across India using a single static voice and style throughout an entire call. 
Indian MSME and enterprise sellers vary drastically across:
- **Pace and Patience**: A busy factory owner in Moradabad wants 30-second bullet points, while a brass artisan in Jaipur appreciates a patient, warm walkthrough.
- **Language & Cultural Mix**: From Shuddh Hindi in UP/Bihar, to Hindi-English (Hinglish) in Delhi/Mumbai, to Indian English for enterprise corporations in Bangalore/Gurgaon.
- **Formality**: Using "Aap", "Ji", "Sir", or friendly collegial phrasing.
- **Objection Profiles**: Pricing doubts, past bad experience with irrelevant leads, skepticism about online B2B, or simple lack of time.
- **Live Emotional Trajectory**: A seller who becomes rushed ("jaldi bolo"), confused ("kya matlab?"), or irritated ("disturb mat karo") will immediately hang up if the bot maintains a monotone sales pitch.

This solution provides an end-to-end autonomous Voice Persona Engine:
1. **Pre-Call Persona Generation**: Constructs a hyper-targeted voice persona grounded in historical empirical evidence (12,788 analyzed calls).
2. **Live Signal Detection**: Monitors seller utterances for 7 key behavioral signals with low latency.
3. **Dynamic Mid-Call Adaptation**: Adjusts voice delivery, pace, formality, tone, and script strategy in real time.
4. **Persistent Persona Memory**: Retains winning persona configurations per seller and evolves baseline configurations across calls.
5. **Sarvam AI Integration**: Full integration with Bulbul TTS, Saaras STT, and LLM chat completions with a resilient fallback mock layer.

---

### 2. Sarvam AI API Integration & Parameter Mappings

#### 2.1 Voice Parameter Realities & Mappings
According to Sarvam AI official documentation:
- **TTS Model**: `bulbul:v4-flash` is Sarvam's recommended low-latency voice model.
- **Pace**: Directly supported via the `pace` parameter (supported range 0.5 to 2.0). 
  - We constrain operational conversational pace between **0.85** (patient/slow for confused/older sellers) to **1.18** (crisp/rushed for busy executives), centered at **1.0**.
- **Pitch**: In Sarvam v3 and v4-flash, pitch is *not* an independent scalar parameter (it was only in older experimental v2).
  - *Engineering Assumption*: We map pitch registers via **speaker selection** from the Sarvam voice catalog. Deeper resonance is mapped to speakers like `shubh_enhi_ads`, `amartya_enhi_ads`, or `aravind_enhi_ads`; higher pitch / melodic resonance is mapped to `aditi_enhi_ads` or `priya_enhi_ads`.
- **Accent**: Accent is *not* a discrete parameter; instead, Sarvam provides region-tuned voices (e.g., Hindi native, Indian English native). 
  - *Engineering Assumption*: Regional accents are assigned via speaker selection mapped against seller state and language preference:
    - Hindi Heartland (UP, Bihar, MP, Rajasthan, Delhi): `shubh_enhi_ads`, `aditi_enhi_ads`
    - Western/Business (Maharashtra, Gujarat): `amartya_enhi_ads`, `priya_enhi_ads`
    - Southern/Pan-India English: `aravind_enhi_ads`, `aditi_enhi_ads`

#### 2.2 Offline / Resilient Mock Mode
To guarantee deterministic execution, unit testing without network dependency, and demo availability regardless of API quotas or temporary network drops:
- `MockSarvamClient` implements the identical interface as `SarvamClient`.
- Returns valid PCM/WAV headers and synthetic transcriptions.
- If `SARVAM_API_KEY` is present in the environment or `.env`, the system automatically leverages the live Sarvam API endpoints.

---

### 3. Empirical Grounding: Insights from 12,788 Calls

Based on Stage 2 analysis (`evidence/evidence_summary.md`):
1. **Pace Impact**:
   - Slow pace (0.85–0.92) achieved a **38.9% meeting rate**, compared to **14.5%** for fast pace overall.
   - For Small Sellers (0 - 40 Lakhs turnover), slow/patient pace won with **38.8%** conversion.
   - However, for Enterprise sellers (> 5 Crore turnover), fast pace yielded **24.0%** conversion (busy executives value conciseness).
2. **Tone Impact**:
   - Warm/Consultative tone converted at **33.5%**, compared to neutral (16.8%) and pushy/hard-sell (9.1%).
3. **Frustration Impact**:
   - Under the legacy static bot, sellers exhibiting frustration had a **0.0% conversion rate**. 
   - This proves that without dynamic mid-call de-escalation, irritated calls are guaranteed lost revenue.

---

### 4. Persona Dimensions & Taxonomy

Each persona is structured along 5 explicit dimensions:

| Dimension | Permitted Values | Business Purpose |
|---|---|---|
| **Voice** | `speaker` (Sarvam ID), `gender` (M/F), `pace` (0.85 - 1.18), `pitch_register` (deep/medium/bright) | Acoustic affinity and intelligibility |
| **Formality** | `respectful_warm` (Aap + Ji), `formal_corporate` (Aap + Sir), `casual_friendly` (Colloquial Ji) | Cultural alignment with MSME vs Enterprise hierarchy |
| **Tone** | `consultative`, `direct_closing`, `empathetic_problem_solver`, `reassuring_patient` | Emotional matching |
| **Language Mix** | `pure_hindi`, `hinglish`, `indian_english` | Natural linguistic comfort |
| **Script Strategy**| `social_proof`, `roi_numbers`, `product_features`, `problem_solving` | Persuasion framework suited to seller maturity |

---

### 5. Signal Detection & Adaptation Rules

The `SignalDetector` scans both acoustic attributes and utterance semantics:

1. **Rushed (`rushed`)**:
   - *Triggers*: Keywords like *"jaldi bolo"*, *"time nahi hai"*, *"busy hu"*, *"gaadi chala raha hu"*, or clipped responses (< 3 words).
   - *Adaptation*: Increase pace (+0.10 to +0.15), strip introductory pleasantries, compress value proposition to 1 key metric, offer 30-second summary or schedule immediate callback.
2. **Confused (`confused`)**:
   - *Triggers*: Keywords like *"kya matlab"*, *"samajh nahi aaya"*, *"kiska call hai"*, *"kaun bol raha hai"*, long hesitations.
   - *Adaptation*: Reduce pace (-0.12), switch to `reassuring_patient` tone, simplify terminology, introduce an intuitive physical market analogy (*"Jaise aapki mandi me dukaan hai..."*).
3. **Irritated / Frustrated (`frustrated`)**:
   - *Triggers*: Keywords like *"bar bar call mat karo"*, *"disturb mat karo"*, *"bakwas"*, *"complaint"* or negative sentiment.
   - *Adaptation*: Immediately drop sales agenda, switch to `empathetic_problem_solver`, offer concise apology, yield conversational control back to seller (*"Bilkul sir, pareshan karne ke liye maafi chahta hu. Main aapko disturb nahi karunga, bas..."*).
4. **Hesitant / Skeptical (`hesitant`)**:
   - *Triggers*: *"pehle bhi liya tha fayda nahi hua"*, *"pata nahi"*, *"costly hai"*, *"sochna padega"*.
   - *Adaptation*: Shift strategy to `social_proof` or `problem_solving` with low-risk assurances.
5. **Engaged / Interested (`engaged`)**:
   - *Triggers*: *"bataiye"*, *"kitna kharcha hoga"*, *"leads kaise aati hai"*, *"theek hai"*.
   - *Adaptation*: Maintain pace, switch to `direct_closing` / consultative demo booking.

#### 5.1 Stability Guardrails (Hysteresis & Anti-Oscillation)
- **Minimum Turns Between Persona Shift**: A persona property cannot shift twice within 2 consecutive turns to avoid jarring acoustic artifacts.
- **Maximum Pace Step**: Step-size limited to $\Delta \le \pm 0.15$ per turn.
- **De-escalation Precedence**: Safety/frustration signals override all commercial strategies.

---

### 6. Cold-Start / Sparse Data Policy
When a seller has minimal or missing data:
- **Default Profile**: `respectful_warm` formality, `hinglish` language mix, `consultative` tone, `social_proof` script strategy, pace `0.98`.
- Inferred from category and state location if available (e.g. Northern agricultural/artisan -> pure Hindi, Western manufacturing -> Hinglish).
- The system rapidly converges to the optimal persona based on the first 2 caller turns.
