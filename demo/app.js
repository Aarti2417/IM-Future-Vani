/**
 * IndiaMART VANI Voice Persona Engine — Frontend Application
 * Handles simulation orchestration, mid-call signal adaptation,
 * audio playback, persona studio, and telemetry.
 */

// ── Fallback Pre-Packaged Data (ensures UI works even without server) ──
const FALLBACK_SCENARIOS = [
  {
    scenario_id: "scenario_1",
    title: "Busy Factory Owner",
    subtitle: "Color Coating Services (40L - 1.5Cr) • Tests pace acceleration",
    seller: {
      fk_glusr_usr_id: 192119502,
      seller_state: "Uttar Pradesh",
      business_type: "Proprietorship",
      annual_turnover: "40 L - 1.5 Cr",
      nature_of_business: "Manufacturer",
      top_category_1: "Color Coating Services",
      bot_answered: 10,
      showed_frustration: 0,
      past_objections: "Seller Unavailability & Scheduling Constraints (1)",
      past_dispositions_detailed: "not_interested (2); call_dropped (1)",
      avg_answered_call_sec: 56.0,
      turn_count: 42
    },
    dialogue_script: [
      {
        seller_text: "Bolo jaldi, main factory floor pe hu, bilkul time nahi hai.",
        expected_signal: "rushed"
      },
      {
        seller_text: "Achha, industrial color coating ke kitne bulk buyers hain Kanpur aur Lucknow se?",
        expected_signal: "engaged"
      },
      {
        seller_text: "Theek hai, mujhe WhatsApp pe details bhej do aur kal 11 baje connect karo.",
        expected_signal: "engaged",
        disposition: "meeting_fixed"
      }
    ]
  },
  {
    scenario_id: "scenario_2",
    title: "Skeptical Artisan",
    subtitle: "Brass Statues (0 - 40L) • Tests slow Hindi pace & social proof",
    seller: {
      fk_glusr_usr_id: 245762792,
      seller_state: "Rajasthan",
      business_type: "Proprietorship",
      annual_turnover: "0 - 40 L",
      nature_of_business: "Trader - Wholesaler/Distributor",
      top_category_1: "Brass God Statues",
      bot_answered: 3,
      showed_frustration: 0,
      past_objections: "Pricing / Affordability; Past Bad Experience",
      past_dispositions_detailed: "meeting_fixed (2); not_interested (1)",
      avg_answered_call_sec: 435.3,
      turn_count: 169
    },
    dialogue_script: [
      {
        seller_text: "Pehle bhi account banaya tha, koi faayda nahi hua, paise waste hote hain.",
        expected_signal: "hesitant"
      },
      {
        seller_text: "Kya matlab? Dusre brass karigaron ko sach me orders mil rahe hain kya?",
        expected_signal: "confused"
      },
      {
        seller_text: "Achha samajh gaya. Iska kitna kharcha padega agar hum demo dekhein?",
        expected_signal: "engaged",
        disposition: "meeting_fixed"
      }
    ]
  },
  {
    scenario_id: "scenario_3",
    title: "Frustrated Churn Risk",
    subtitle: "UPVC Windows (0 - 40L) • Tests emergency de-escalation",
    seller: {
      fk_glusr_usr_id: 241241351,
      seller_state: "Bihar",
      business_type: "Proprietorship",
      annual_turnover: "0 - 40 L",
      nature_of_business: "Service Provider and Others",
      top_category_1: "UPVC Sliding Windows",
      bot_answered: 3,
      showed_frustration: 1,
      past_objections: "Explicit Disinterest / Refusal (1)",
      past_dispositions_detailed: "do_not_call (1); call_dropped (1)",
      avg_answered_call_sec: 192.0,
      turn_count: 32
    },
    dialogue_script: [
      {
        seller_text: "Bar bar kyu call karte ho bhai? Bola na nahi chahiye! Disturb mat karo!",
        expected_signal: "frustrated"
      },
      {
        seller_text: "Acha theek hai, abhi main customer ke site pe hu. Kal 3 baje call karna.",
        expected_signal: "engaged",
        disposition: "callback_requested"
      }
    ]
  },
  {
    scenario_id: "scenario_4",
    title: "Enterprise Distributor",
    subtitle: "Ambuja Cement (5 - 25 Cr) • Tests formal executive tone & ROI",
    seller: {
      fk_glusr_usr_id: 29416327,
      seller_state: "Gujarat",
      business_type: "Proprietorship",
      annual_turnover: "5 - 25 Cr",
      nature_of_business: "Service Provider and Others",
      top_category_1: "Ambuja Cement",
      bot_answered: 3,
      showed_frustration: 0,
      past_objections: "nan",
      past_dispositions_detailed: "callback_requested (1); meeting_fixed (1)",
      avg_answered_call_sec: 162.3,
      turn_count: 49
    },
    dialogue_script: [
      {
        seller_text: "Good afternoon. Please make it quick, what are the bulk procurement quantities on your platform?",
        expected_signal: "engaged"
      },
      {
        seller_text: "We handle 200+ metric ton orders across West India. Can you filter GST-verified construction firms?",
        expected_signal: "engaged"
      },
      {
        seller_text: "Sounds productive. Send the calendar invite for tomorrow 3 PM.",
        expected_signal: "engaged",
        disposition: "meeting_fixed"
      }
    ]
  }
];

// State
let currentScenarios = FALLBACK_SCENARIOS;
let activeScenario = FALLBACK_SCENARIOS[0];
let activePersona = null;
let initialPersona = null;
let currentTurnIndex = 0;
let callDurationSec = 0;
let callTimerInterval = null;
let isCallActive = false;
let autoPlayInterval = null;
let currentTrajectory = [];

// ── DOM Initialization ─────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initScenarios();
  initCallControls();
  initRoleplaySimulator();
  initPersonaStudio();
  initSignalLab();
  initMemoryTab();
  initSarvamTab();
  checkBackendStatus();
});

// ── Navigation Tabs ────────────────────────────────────────
function switchTab(tabId) {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");
  tabButtons.forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
  });
  tabPanes.forEach(p => {
    p.classList.toggle("active", p.id === tabId);
  });
  if (tabId === "tab-memory") {
    loadMemoryCards();
  }
}

function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      switchTab(btn.getAttribute("data-tab"));
    });
  });

  const btnGotoStudio = document.getElementById("btn-goto-persona-builder");
  if (btnGotoStudio) {
    btnGotoStudio.addEventListener("click", () => {
      switchTab("tab-generator");
    });
  }
}

// ── Backend Connectivity Check ─────────────────────────────
async function checkBackendStatus() {
  try {
    const res = await fetch("/api/status");
    if (res.ok) {
      const data = await res.json();
      const sarvamText = document.getElementById("status-sarvam-text");
      if (sarvamText) {
        sarvamText.textContent = data.sarvam_mode === "live" ? "Sarvam AI (Live)" : "Sarvam AI (Resilient Mock)";
      }
    }
    const mcpRes = await fetch("/api/mcp/status");
    if (mcpRes.ok) {
      const mcpData = await mcpRes.json();
      const mcpPill = document.getElementById("status-mcp-pill");
      if (mcpPill && mcpData.active_tools) {
        mcpPill.querySelector("span:last-child").textContent = `MCP: ${mcpData.active_tools.length} Tools Active`;
      }
    }
  } catch (e) {
    console.log("Running in client mode with mock fallbacks.");
  }
}

// ── Scenarios Initialization ───────────────────────────────
async function initScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    if (res.ok) {
      const data = await res.json();
      if (data.scenarios && data.scenarios.length > 0) {
        currentScenarios = data.scenarios;
      }
    }
  } catch (e) {
    console.log("Using embedded scenario templates.");
  }

  const container = document.getElementById("scenario-selector-container");
  if (!container) return;
  container.innerHTML = "";

  currentScenarios.forEach((sc, idx) => {
    const btn = document.createElement("button");
    btn.className = `scenario-card-btn ${idx === 0 ? "active" : ""}`;
    btn.id = `btn-scenario-${sc.scenario_id}`;
    btn.innerHTML = `
      <span class="scenario-card-title">${getCategoryIcon(sc.seller.top_category_1)} ${sc.title}</span>
      <span class="scenario-card-sub">${sc.subtitle || sc.seller.seller_state}</span>
    `;
    btn.addEventListener("click", () => selectScenario(sc, btn));
    container.appendChild(btn);
  });

  // Load first scenario
  selectScenario(currentScenarios[0]);
}

function getCategoryIcon(cat) {
  const c = (cat || "").toLowerCase();
  if (c.includes("brass") || c.includes("statue")) return "🎨";
  if (c.includes("coating") || c.includes("color")) return "🏭";
  if (c.includes("cement") || c.includes("building")) return "🏢";
  if (c.includes("window") || c.includes("sliding")) return "🪟";
  return "📦";
}

// ── Select Scenario & Generate Persona ─────────────────────
async function selectScenario(scenario, btnElement) {
  activeScenario = scenario;
  if (btnElement) {
    document.querySelectorAll(".scenario-card-btn").forEach(b => b.classList.remove("active"));
    btnElement.classList.add("active");
  }

  // Update Call Topbar
  const seller = scenario.seller;
  document.getElementById("call-seller-name").textContent = `${seller.top_category_1} (${seller.nature_of_business || "MSME"})`;
  document.getElementById("call-seller-loc").textContent = `${seller.seller_state} • ${seller.annual_turnover} Turnover`;

  // Reset Call
  resetCallSimulation();

  // Generate Persona via API (or local generator fallback)
  try {
    const res = await fetch("/api/generate_persona", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seller })
    });
    if (res.ok) {
      const data = await res.json();
      initialPersona = data.persona;
      activePersona = JSON.parse(JSON.stringify(data.persona));
      renderPersonaCard(activePersona);
      startCallSimulation();
      return;
    }
  } catch (e) {
    console.log("Falling back to client-side persona generator.");
  }

  // Fallback client-side generator
  initialPersona = buildClientPersona(seller);
  activePersona = JSON.parse(JSON.stringify(initialPersona));
  renderPersonaCard(activePersona);
  startCallSimulation();
}

function buildClientPersona(seller) {
  const showedFrust = seller.showed_frustration === 1;
  const isLarge = (seller.annual_turnover || "").includes("Cr");
  const gender = isLarge ? "male" : (showedFrust ? "female" : "male");
  const voiceId = isLarge ? "sunny_enhi_customer" : (showedFrust ? "ishita_enhi_customer" : "shubh_enhi_ads");
  const voiceName = isLarge ? "Sunny / Vikram (Executive Register)" : (showedFrust ? "Ishita (Empathetic Register)" : "Shubh (Friendly Register)");
  const repName = isLarge ? "Vikram" : (showedFrust ? "Ishita" : "Shubh");
  const verbSelf = gender === "female" ? "bol rahi hu" : "bol raha hu";

  return {
    seller_id: String(seller.fk_glusr_usr_id),
    voice_id: voiceId,
    voice_name: voiceName,
    gender: gender,
    pitch_register: isLarge ? "bright_crisp" : (showedFrust ? "warm" : "medium_resonant"),
    pace: isLarge ? 1.05 : (showedFrust ? 0.90 : 0.98),
    formality: isLarge ? "formal_corporate" : "respectful_warm",
    tone: showedFrust ? "empathetic_problem_solver" : (isLarge ? "direct_closing" : "consultative"),
    language_mix: isLarge ? "indian_english" : (seller.seller_state === "Rajasthan" ? "pure_hindi" : "hinglish"),
    script_strategy: isLarge ? "roi_numbers" : (showedFrust ? "problem_solving" : "social_proof"),
    opening_line: `Namaste ji! Main IndiaMART se ${repName} ${verbSelf}. Aapke ${seller.top_category_1 || "business"} ke liye verified buyer leads aaye hain.`,
    rationale: {
      turnover: `Turnover ${seller.annual_turnover} aligned with ${isLarge ? 'executive direct closing' : 'consultative MSME approach'}.`,
      state: `Region ${seller.seller_state} matched to optimal linguistic cadence.`,
      frustration: showedFrust ? 'Prior frustration detected: Activated empathy and de-escalation guardrails.' : 'Normal baseline.'
    }
  };
}

// ── Render Persona Details Card ────────────────────────────
function renderPersonaCard(persona) {
  document.getElementById("persona-seller-title").textContent = `Seller ID: ${persona.seller_id}`;
  document.getElementById("persona-voice-name").textContent = persona.voice_name || persona.voice_id;
  document.getElementById("persona-voice-id").textContent = `Voice ID: ${persona.voice_id}`;
  document.getElementById("persona-gender-chip").textContent = `Gender: ${persona.gender || "neutral"}`;
  document.getElementById("persona-pitch-chip").textContent = `Pitch: ${persona.pitch_register || "medium"}`;

  // Pace Gauge
  const paceVal = persona.pace || 1.0;
  document.getElementById("gauge-pace-val").textContent = `${paceVal.toFixed(2)}x`;
  const pct = Math.max(5, Math.min(100, ((paceVal - 0.85) / (1.18 - 0.85)) * 100));
  document.getElementById("meter-pace-fill").style.width = `${pct}%`;

  // Formality, Tone, Lang, Strategy
  document.getElementById("prop-formality").textContent = formatKey(persona.formality);
  document.getElementById("prop-tone").textContent = formatKey(persona.tone);
  document.getElementById("prop-lang").textContent = formatKey(persona.language_mix);
  document.getElementById("prop-strategy").textContent = formatKey(persona.script_strategy);

  // Rationale list
  const list = document.getElementById("persona-rationale-list");
  list.innerHTML = "";
  if (persona.rationale) {
    Object.entries(persona.rationale).forEach(([k, v]) => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${formatKey(k)}:</strong> ${v}`;
      list.appendChild(li);
    });
  }
}

function formatKey(str) {
  if (!str) return "—";
  return str.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

// ── Call Simulation Lifecycle ──────────────────────────────
function startCallSimulation() {
  isCallActive = true;
  currentTurnIndex = 0;
  currentTrajectory = [];
  callDurationSec = 0;

  clearInterval(callTimerInterval);
  callTimerInterval = setInterval(() => {
    callDurationSec++;
    const mins = String(Math.floor(callDurationSec / 60)).padStart(2, "0");
    const secs = String(callDurationSec % 60).padStart(2, "0");
    const timerElem = document.getElementById("call-timer-display");
    if (timerElem) timerElem.textContent = `${mins}:${secs}`;
  }, 1000);

  // Stream container clear
  const stream = document.getElementById("conversation-stream-container");
  stream.innerHTML = "";

  // Telemetry clear
  document.getElementById("adaptation-count-badge").textContent = "0 Shifts";
  document.getElementById("telemetry-trajectory-list").innerHTML = '<div class="empty-timeline">No adaptations yet. Click a quick reaction button to trigger mid-call adaptation!</div>';
  updateTelemetrySignal("neutral", 1.0, "Bot maintaining baseline conversational rhythm.");

  // Inject Bot Opening Line
  injectBotTurn(activePersona.opening_line || "Namaste ji, main IndiaMART se Vani bol rahi hu.");
}

function resetCallSimulation() {
  clearInterval(callTimerInterval);
  clearInterval(autoPlayInterval);
  isCallActive = false;
  currentTurnIndex = 0;
  document.getElementById("call-timer-display").textContent = "00:00";
  document.getElementById("btn-autoplay-simulation").textContent = "⏩ Auto-Play Scenario";
  const stream = document.getElementById("conversation-stream-container");
  if (stream) stream.innerHTML = "";
}

// ── Turn Injection Helpers ─────────────────────────────────
function injectBotTurn(text, audioB64) {
  const stream = document.getElementById("conversation-stream-container");
  const bubble = document.createElement("div");
  bubble.className = "turn-bubble turn-bot";
  
  const turnNum = stream.children.length + 1;
  bubble.innerHTML = `
    <div class="turn-header">
      <strong>🤖 VANI (Bot)</strong>
      <span>Turn #${turnNum} • Pace: ${activePersona ? activePersona.pace.toFixed(2) : '1.0'}x</span>
    </div>
    <div class="turn-text">${escapeHtml(text)}</div>
    <button class="turn-audio-btn" data-text="${escapeHtml(text)}">
      🔊 Listen Audio
    </button>
  `;

  const btn = bubble.querySelector(".turn-audio-btn");
  btn.addEventListener("click", () => playBotAudio(text, audioB64));

  stream.appendChild(bubble);
  stream.scrollTop = stream.scrollHeight;
}

function injectSellerTurn(text, signalType, conf) {
  const stream = document.getElementById("conversation-stream-container");
  const bubble = document.createElement("div");
  bubble.className = "turn-bubble turn-seller";
  
  const turnNum = stream.children.length + 1;
  const sigBadge = signalType && signalType !== "neutral" 
    ? `<span class="sig-pill sig-${signalType}">${signalType.toUpperCase()} (${(conf || 0.85).toFixed(2)})</span>` 
    : "";

  bubble.innerHTML = `
    <div class="turn-header">
      <strong>👤 Seller</strong>
      <div>${sigBadge} <span>Turn #${turnNum}</span></div>
    </div>
    <div class="turn-text">${escapeHtml(text)}</div>
  `;

  stream.appendChild(bubble);
  stream.scrollTop = stream.scrollHeight;
}

function injectAdaptationBanner(event) {
  const stream = document.getElementById("conversation-stream-container");
  const banner = document.createElement("div");
  banner.className = "adaptation-banner";

  const changesStr = Object.entries(event.changes_made || {})
    .filter(([k]) => k !== "instruction")
    .map(([k, v]) => `${k.toUpperCase()}: ${v.from} ➔ ${v.to}`)
    .join(" • ");

  banner.innerHTML = `
    <span class="adapt-icon">⚡</span>
    <div>
      <strong>MID-CALL PERSONA ADAPTED (${event.signal_detected.toUpperCase()})</strong><br>
      <span>${changesStr || 'Cadence Adjusted'} — <em>${event.adaptation_rationale || ''}</em></span>
    </div>
  `;

  stream.appendChild(banner);
  stream.scrollTop = stream.scrollHeight;
}

// ── Interactive Controls ───────────────────────────────────
function initCallControls() {
  // Step Next Turn
  document.getElementById("btn-step-simulation").addEventListener("click", stepNextScriptTurn);

  // Auto-Play
  document.getElementById("btn-autoplay-simulation").addEventListener("click", toggleAutoPlay);

  // Reset
  document.getElementById("btn-reset-simulation").addEventListener("click", () => {
    selectScenario(activeScenario);
  });

  // Quick Signal Injections
  document.querySelectorAll(".inject-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const type = btn.getAttribute("data-type");
      const sampleTexts = {
        rushed: "Bolo jaldi, main gaadi chala raha hu, bilkul time nahi hai abhi!",
        confused: "Kya matlab? Kaun bol raha hai aur kiska call hai?",
        frustrated: "Bar bar call karke pareshan mat karo! Band karo phone!",
        hesitant: "Pehle bhi liya tha, koi fayda nahi hua, bohot costly hai.",
        engaged: "Achha bataiye, leads kaise aati hain aur charges kya hain?"
      };
      processSellerUtterance(sampleTexts[type] || "Theek hai bataiye.");
    });
  });

  // Custom Utterance Form
  document.getElementById("custom-utterance-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("input-custom-utterance");
    const val = input.value.trim();
    if (val) {
      processSellerUtterance(val);
      input.value = "";
    }
  });

  // Microphone Voice Input
  initVoiceInput();
}

let isRecordingVoice = false;
let speechRecognizer = null;
let mediaRecorder = null;
let audioChunks = [];

function initVoiceInput() {
  const micBtn = document.getElementById("btn-mic-record");
  const micStatus = document.getElementById("mic-status-text");
  const inputElem = document.getElementById("input-custom-utterance");
  if (!micBtn) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    speechRecognizer = new SpeechRecognition();
    speechRecognizer.continuous = false;
    speechRecognizer.interimResults = true;

    speechRecognizer.onstart = () => {
      isRecordingVoice = true;
      micBtn.classList.add("recording");
      if (micStatus) micStatus.textContent = "Listening...";
      inputElem.placeholder = "Listening to your voice... speak now in Hindi, Hinglish or English";
    };

    speechRecognizer.onresult = (event) => {
      let interim = "";
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      inputElem.value = finalTranscript || interim;
    };

    speechRecognizer.onerror = (event) => {
      console.log("Speech recognition error:", event.error);
      stopVoiceInput();
    };

    speechRecognizer.onend = () => {
      stopVoiceInput();
      const text = inputElem.value.trim();
      if (text) {
        processSellerUtterance(text);
        inputElem.value = "";
      }
    };

    micBtn.addEventListener("click", () => {
      if (isRecordingVoice) {
        speechRecognizer.stop();
      } else {
        speechRecognizer.lang = (activePersona && activePersona.language_mix === "indian_english") ? "en-IN" : "hi-IN";
        try {
          speechRecognizer.start();
        } catch (e) {
          console.log("Recognition start error:", e);
        }
      }
    });

  } else if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    micBtn.addEventListener("click", async () => {
      if (isRecordingVoice) {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
        }
      } else {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunks.push(e.data);
          };

          mediaRecorder.onstart = () => {
            isRecordingVoice = true;
            micBtn.classList.add("recording");
            if (micStatus) micStatus.textContent = "Listening...";
            inputElem.placeholder = "Recording audio... click Speak again when done";
          };

          mediaRecorder.onstop = async () => {
            stopVoiceInput();
            stream.getTracks().forEach(t => t.stop());
            const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
            const reader = new FileReader();
            reader.onloadend = async () => {
              const b64 = reader.result.split(",")[1];
              try {
                const res = await fetch("/api/stt", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    audio_base64: b64,
                    language_code: (activePersona && activePersona.language_mix === "indian_english") ? "en-IN" : "hi-IN"
                  })
                });
                if (res.ok) {
                  const data = await res.json();
                  if (data.text) {
                    processSellerUtterance(data.text);
                  }
                }
              } catch (err) {
                console.log("STT fetch error:", err);
              }
            };
            reader.readAsDataURL(audioBlob);
          };

          mediaRecorder.start();
        } catch (err) {
          alert("Microphone permission denied or not supported in this browser.");
          stopVoiceInput();
        }
      }
    });
  } else {
    micBtn.addEventListener("click", () => {
      alert("Microphone speech input is not supported in this browser. Please type your message.");
    });
  }
}

function stopVoiceInput() {
  isRecordingVoice = false;
  const micBtn = document.getElementById("btn-mic-record");
  const micStatus = document.getElementById("mic-status-text");
  const inputElem = document.getElementById("input-custom-utterance");
  if (micBtn) micBtn.classList.remove("recording");
  if (micStatus) micStatus.textContent = "Speak";
  if (inputElem) inputElem.placeholder = "Type or click '🎙️ Speak' to talk directly...";
}

function stepNextScriptTurn() {
  if (!activeScenario || !activeScenario.dialogue_script) return;
  if (currentTurnIndex >= activeScenario.dialogue_script.length) {
    showCallEndedBanner();
    return;
  }

  const step = activeScenario.dialogue_script[currentTurnIndex];
  currentTurnIndex++;
  processSellerUtterance(step.seller_text);
}

function toggleAutoPlay() {
  const btn = document.getElementById("btn-autoplay-simulation");
  if (autoPlayInterval) {
    clearInterval(autoPlayInterval);
    autoPlayInterval = null;
    btn.textContent = "⏩ Auto-Play Scenario";
  } else {
    btn.textContent = "⏸ Pause Auto-Play";
    stepNextScriptTurn();
    autoPlayInterval = setInterval(() => {
      if (currentTurnIndex >= activeScenario.dialogue_script.length) {
        clearInterval(autoPlayInterval);
        autoPlayInterval = null;
        btn.textContent = "⏩ Auto-Play Scenario";
        showCallEndedBanner();
      } else {
        stepNextScriptTurn();
      }
    }, 3800);
  }
}

function showCallEndedBanner() {
  const stream = document.getElementById("conversation-stream-container");
  const banner = document.createElement("div");
  banner.className = "adaptation-banner";
  banner.style.background = "rgba(16, 185, 129, 0.2)";
  banner.style.borderColor = "rgba(16, 185, 129, 0.4)";
  banner.style.color = "#34d399";
  banner.innerHTML = `
    <span class="adapt-icon">✅</span>
    <div>
      <strong>CALL COMPLETED • OUTCOME: MEETING SCHEDULED</strong><br>
      <span>Winning persona configuration persisted to Persona Memory for future calls.</span>
    </div>
  `;
  stream.appendChild(banner);
  stream.scrollTop = stream.scrollHeight;
}

// ── Utterance Processing Pipeline ──────────────────────────
async function processSellerUtterance(text) {
  // 1. Detect Signal via API or client fallback
  let sig = null;
  try {
    const res = await fetch("/api/detect_signal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (res.ok) {
      const data = await res.json();
      sig = data.signal;
    }
  } catch (e) {
    console.log("Client fallback signal detection.");
  }

  if (!sig) {
    sig = clientDetectSignal(text);
  }

  // 2. Inject Seller speech bubble
  injectSellerTurn(text, sig.signal, sig.confidence);

  // 3. Update Telemetry
  updateTelemetrySignal(sig.signal, sig.confidence, sig.recommended_action);

  // 4. Adapt Active Persona via API or client state machine
  let adaptEvent = null;
  const turnNum = document.getElementById("conversation-stream-container").children.length;
  try {
    const res = await fetch("/api/adapt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        active_persona: activePersona,
        signal: sig,
        turn_number: turnNum
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.adapted) {
        adaptEvent = data.event;
        activePersona = data.new_persona;
      }
    }
  } catch (e) {
    console.log("Client fallback adaptation.");
  }

  if (!adaptEvent && sig.signal !== "neutral") {
    adaptEvent = clientAdaptPersona(sig, turnNum);
  }

  // If adapted, render update
  if (adaptEvent) {
    currentTrajectory.push(adaptEvent);
    renderPersonaCard(activePersona);
    injectAdaptationBanner(adaptEvent);
    showAdaptationAlert(adaptEvent);
    appendTelemetryTrajectory(adaptEvent);
    document.getElementById("adaptation-count-badge").textContent = `${currentTrajectory.length} Shifts`;
  }

  // 5. Generate Dynamic Bot Response (via /api/generate_reply or intelligent fallback)
  injectThinkingIndicator();

  const history = [];
  document.querySelectorAll(".turn-bubble").forEach(b => {
    const isBot = b.classList.contains("turn-bot");
    const t = b.querySelector(".turn-text")?.textContent || "";
    if (t && !b.classList.contains("thinking-bubble")) {
      history.push({ speaker: isBot ? "bot" : "seller", text: t });
    }
  });

  let botReply = null;
  let botAudioB64 = null;

  try {
    const res = await fetch("/api/generate_reply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        seller_text: text,
        seller: activeScenario ? activeScenario.seller : {},
        active_persona: activePersona,
        signal: sig,
        history: history,
        generate_audio: true
      })
    });
    if (res.ok) {
      const data = await res.json();
      botReply = data.reply_text;
      botAudioB64 = data.audio_base64;
    }
  } catch (err) {
    console.log("Error from /api/generate_reply, using fallback:", err);
  }

  if (!botReply || botReply.trim().length === 0) {
    botReply = generateBotReply(text, sig, activePersona);
  }

  const currentBotGender = (activePersona && activePersona.gender) ? activePersona.gender : "male";
  botReply = enforceSpeakerGender(botReply, currentBotGender);

  removeThinkingIndicator();

  injectBotTurn(botReply, botAudioB64);
  playBotAudio(botReply, botAudioB64);
}

function injectThinkingIndicator() {
  const stream = document.getElementById("conversation-stream-container");
  const bubble = document.createElement("div");
  bubble.id = "turn-thinking-indicator";
  bubble.className = "turn-bubble turn-bot thinking-bubble";
  bubble.innerHTML = `
    <div class="turn-header"><strong>🤖 VANI (Bot)</strong> <span>Synthesizing...</span></div>
    <div class="turn-text" style="color: var(--accent-cyan); font-style: italic;">Processing response & neural voice...</div>
  `;
  stream.appendChild(bubble);
  stream.scrollTop = stream.scrollHeight;
}

function removeThinkingIndicator() {
  const elem = document.getElementById("turn-thinking-indicator");
  if (elem) elem.remove();
}

// ── Client Fallback Signal Detection ───────────────────────
function isDevanagari(text) {
  return /[\u0900-\u097F]/.test(text || "");
}

function clientDetectSignal(text) {
  const t = (text || "").toLowerCase();
  const raw = text || "";

  // Frustrated (Priority 1)
  if (t.includes("bar bar") || t.includes("disturb") || t.includes("pareshan") || t.includes("band karo") || t.includes("nahi chahiye") || t.includes("faltu") ||
      raw.includes("बार बार") || raw.includes("परेशान") || raw.includes("बकवास") || raw.includes("नहीं चाहिए") || raw.includes("काट दो") || raw.includes("बंद करो") || raw.includes("फालतू")) {
    return {
      signal: "frustrated",
      confidence: 0.94,
      recommended_action: "De-escalate immediately: apologize sincerely, yield conversational control, ask to reschedule.",
      cues_matched: ["nahi chahiye / pareshan"]
    };
  }

  // Rushed (Priority 2)
  if (t.includes("jaldi") || t.includes("time nahi") || t.includes("busy") || t.includes("driving") || t.includes("bheed") || t.includes("grahak") ||
      raw.includes("जल्दी") || raw.includes("टाइम नहीं") || raw.includes("समय नहीं") || raw.includes("भीड़") || raw.includes("ग्राहक खड़ा") || raw.includes("व्यस्त") || raw.includes("गाड़ी चला")) {
    return {
      signal: "rushed",
      confidence: 0.88,
      recommended_action: "Accelerate pace (+0.12x), remove fluff, give 1 concise bullet point.",
      cues_matched: ["jaldi / time nahi / bheed"]
    };
  }

  // Confused
  if (t.includes("kya matlab") || t.includes("samajh nahi") || t.includes("kaun bol") || t.includes("kiska call") ||
      raw.includes("क्या मतलब") || raw.includes("समझ नहीं") || raw.includes("कौन बोल") || raw.includes("किसका फोन") || raw.includes("क्या चीज")) {
    return {
      signal: "confused",
      confidence: 0.85,
      recommended_action: "Decelerate pace (-0.12x), simplify words, use physical mandi/shop analogy.",
      cues_matched: ["kya matlab / samajh nahi"]
    };
  }

  // Hesitant
  if (t.includes("fayda nahi") || t.includes("costly") || t.includes("paise waste") || t.includes("sochna") || t.includes("paise doob") ||
      raw.includes("फायदा नहीं") || raw.includes("पैसे डूब") || raw.includes("सोचना पड़ेगा") || raw.includes("महंगा") || raw.includes("भरोसा नहीं") || raw.includes("नुकसान")) {
    return {
      signal: "hesitant",
      confidence: 0.80,
      recommended_action: "Pivot to Social Proof & verified peer metrics; reduce perceived risk.",
      cues_matched: ["paise doob / fayda nahi"]
    };
  }

  // Engaged
  if (t.includes("bataiye") || t.includes("kitna kharcha") || t.includes("leads") || t.includes("interested") || t.includes("theek hai") || t.includes("rate") ||
      raw.includes("बताइए") || raw.includes("बताओ") || raw.includes("कितना खर्चा") || raw.includes("कितना पैसा") || raw.includes("रेट क्या") || raw.includes("अच्छा") || raw.includes("ठीक है")) {
    return {
      signal: "engaged",
      confidence: 0.82,
      recommended_action: "Maintain consultative flow, provide crisp answers, drive toward demo booking.",
      cues_matched: ["bataiye / kitna kharcha"]
    };
  }

  return {
    signal: "neutral",
    confidence: 0.70,
    recommended_action: "Bot maintaining baseline conversational rhythm.",
    cues_matched: []
  };
}

function clientAdaptPersona(sig, turnNum) {
  const prevPace = activePersona.pace;
  const changes = {};

  if (sig.signal === "rushed") {
    const newPace = Math.min(1.18, +(prevPace + 0.12).toFixed(2));
    changes.pace = { from: prevPace, to: newPace };
    activePersona.pace = newPace;
    activePersona.tone = "direct_closing";
  } else if (sig.signal === "confused") {
    const newPace = Math.max(0.86, +(prevPace - 0.12).toFixed(2));
    changes.pace = { from: prevPace, to: newPace };
    activePersona.pace = newPace;
    activePersona.tone = "reassuring_patient";
  } else if (sig.signal === "frustrated") {
    activePersona.pace = 0.90;
    activePersona.tone = "empathetic_problem_solver";
    activePersona.script_strategy = "problem_solving";
    changes.tone = { from: "consultative", to: "empathetic_problem_solver" };
  } else if (sig.signal === "hesitant") {
    activePersona.script_strategy = "social_proof";
    changes.script_strategy = { from: "product_features", to: "social_proof" };
  } else if (sig.signal === "engaged") {
    activePersona.tone = "consultative";
  }

  return {
    turn_number: turnNum,
    signal_detected: sig.signal,
    signal_confidence: sig.confidence,
    cues: sig.cues_matched,
    changes_made: changes,
    adaptation_rationale: sig.recommended_action
  };
}

function enforceSpeakerGender(text, gender) {
  if (!text) return "";
  let t = text;
  const g = (gender || "male").toLowerCase();

  if (g === "male") {
    const devRules = [
      [/बोल रही हूँ/g, 'बोल रहा हूँ'], [/बोल रही हु/g, 'बोल रहा हूँ'],
      [/बात कर रही हूँ/g, 'बात कर रहा हूँ'], [/कर रही हूँ/g, 'कर रहा हूँ'],
      [/कर रही हु/g, 'कर रहा हूँ'], [/कर रही थी/g, 'कर रहा था'],
      [/माफी चाहती हूँ/g, 'माफी चाहता हूँ'], [/माफ़ी चाहती हूँ/g, 'माफ़ी चाहता हूँ'],
      [/माफी माँगती हूँ/g, 'माफी माँगता हूँ'], [/माफ़ी माँगती हूँ/g, 'माफ़ी माँगता हूँ'],
      [/माफी मांगती हूँ/g, 'माफी मांगता हूँ'], [/माफ़ी मांगती हूँ/g, 'माफ़ी मांगता हूँ'],
      [/माफी चाहती/g, 'माफी चाहता'], [/माफ़ी चाहती/g, 'माफ़ी चाहता'],
      [/माफी माँगती/g, 'माफी माँगता'], [/माफ़ी माँगती/g, 'माफ़ी माँगता'],
      [/माफी मांगती/g, 'माफी मांगता'], [/माफ़ी मांगती/g, 'माफ़ी मांगता'],
      [/चाहती हूँ/g, 'चाहता हूँ'], [/चाहती हु/g, 'चाहता हूँ'],
      [/चाहूँगी/g, 'चाहूँगा'], [/चाहूंगी/g, 'चाहूंगा'],
      [/कर दूँगी/g, 'कर दूँगा'], [/कर दूंगी/g, 'कर दूंगा'],
      [/कर लूँगी/g, 'कर लूँगा'], [/कर लूंगी/g, 'कर लूंगा'],
      [/देती हूँ/g, 'देता हूँ'], [/लेती हूँ/g, 'लेता हूँ'],
      [/समझती हूँ/g, 'समझता हूँ'], [/समझ गई/g, 'समझ गया'],
      [/करूँगी/g, 'करूँगा'], [/करूंगी/g, 'करूंगा'],
      [/बताती हूँ/g, 'बताता हूँ'], [/सुनाती हूँ/g, 'सुनाता हूँ'],
      [/आई हूँ/g, 'आया हूँ'], [/गई हूँ/g, 'गया हूँ']
    ];
    devRules.forEach(([pat, repl]) => { t = t.replace(pat, repl); });

    const hingRules = [
      [/\bbol rahi hu\b/gi, 'bol raha hu'], [/\bbol rahi hoon\b/gi, 'bol raha hoon'],
      [/\bbaat kar rahi hu\b/gi, 'baat kar raha hu'], [/\bbaat kar rahi hoon\b/gi, 'baat kar raha hoon'],
      [/\bkar rahi hu\b/gi, 'kar raha hu'], [/\bkar rahi hoon\b/gi, 'kar raha hoon'],
      [/\bkr rahi hu\b/gi, 'kar raha hu'], [/\bkar rahi thi\b/gi, 'kar raha tha'],
      [/\bmaafi chahti hu\b/gi, 'maafi chahta hu'], [/\bmaafi chahti hoon\b/gi, 'maafi chahta hoon'],
      [/\bmafi chahti hu\b/gi, 'maafi chahta hu'],
      [/\bmaafi mangti hu\b/gi, 'maafi mangta hu'], [/\bmaafi mangti hoon\b/gi, 'maafi mangta hoon'],
      [/\bmafi mangti hu\b/gi, 'maafi mangta hu'],
      [/\bmaafi chahti\b/gi, 'maafi chahta'], [/\bmafi chahti\b/gi, 'maafi chahta'],
      [/\bmaafi mangti\b/gi, 'maafi mangta'], [/\bmafi mangti\b/gi, 'maafi mangta'],
      [/\bchahti hu\b/gi, 'chahta hu'], [/\bchahti hoon\b/gi, 'chahta hoon'],
      [/\bchati hu\b/gi, 'chahta hu'], [/\bchati hoon\b/gi, 'chahta hoon'],
      [/\bchahungi\b/gi, 'chahunga'],
      [/\bkar dungi\b/gi, 'kar dunga'], [/\bkr dungi\b/gi, 'kar dunga'],
      [/\bkar lungi\b/gi, 'kar lunga'], [/\bkr lungi\b/gi, 'kar lunga'],
      [/\bde deti hu\b/gi, 'de deta hu'], [/\bdeti hu\b/gi, 'deta hu'],
      [/\bleti hu\b/gi, 'leta hu'],
      [/\bsamajhti hu\b/gi, 'samajhta hu'], [/\bsamajhti hoon\b/gi, 'samajhta hoon'],
      [/\bsamajh gayi\b/gi, 'samajh gaya'],
      [/\bkarungi\b/gi, 'karunga'], [/\bkrungi\b/gi, 'karunga'],
      [/\baayi hu\b/gi, 'aaya hu'], [/\baayi hoon\b/gi, 'aaya hoon']
    ];
    hingRules.forEach(([pat, repl]) => { t = t.replace(pat, repl); });

  } else if (g === "female") {
    const devRules = [
      [/बोल रहा हूँ/g, 'बोल रही हूँ'], [/बोल रहा हु/g, 'बोल रही हूँ'],
      [/बात कर रहा हूँ/g, 'बात कर रही हूँ'], [/कर रहा हूँ/g, 'कर रही हूँ'],
      [/कर रहा था/g, 'कर रही थी'],
      [/माफी चाहता हूँ/g, 'माफी चाहती हूँ'], [/माफ़ी चाहता हूँ/g, 'माफ़ी चाहती हूँ'],
      [/माफी माँगता हूँ/g, 'माफी माँगती हूँ'], [/माफ़ी माँगता हूँ/g, 'माफ़ी माँगती हूँ'],
      [/माफी मांगता हूँ/g, 'माफी मांगती हूँ'], [/माफ़ी मांगता हूँ/g, 'माफ़ी मांगती हूँ'],
      [/माफी चाहता/g, 'माफी चाहती'], [/माफ़ी चाहता/g, 'माफ़ी चाहती'],
      [/माफी माँगता/g, 'माफी माँगती'], [/माफ़ी माँगता/g, 'माफ़ी माँगती'],
      [/माफी मांगता/g, 'माफी मांगती'], [/माफ़ी मांगता/g, 'माफ़ी मांगती'],
      [/चाहता हूँ/g, 'चाहती हूँ'], [/चाहता हु/g, 'चाहती हूँ'],
      [/चाहूँगा/g, 'चाहूँगी'], [/चाहूंगा/g, 'चाहूंगी'],
      [/कर दूँगा/g, 'कर दूँगी'], [/कर दूंगा/g, 'कर दूंगी'],
      [/कर लूँगा/g, 'कर लूँगी'], [/कर लूंगा/g, 'कर लूंगी'],
      [/देता हूँ/g, 'देती हूँ'], [/लेता हूँ/g, 'लेती हूँ'],
      [/समझता हूँ/g, 'समझती हूँ'], [/समझ गया/g, 'समझ गई'],
      [/करूँगा/g, 'करूँगी'], [/करूंगा/g, 'करूंगी'],
      [/बताता हूँ/g, 'बताती हूँ'], [/सुनाता हूँ/g, 'सुनाती हूँ'],
      [/आया हूँ/g, 'आई हूँ'], [/गया हूँ/g, 'गई हूँ']
    ];
    devRules.forEach(([pat, repl]) => { t = t.replace(pat, repl); });

    const hingRules = [
      [/\bbol raha hu\b/gi, 'bol rahi hu'], [/\bbol raha hoon\b/gi, 'bol rahi hoon'],
      [/\bbaat kar raha hu\b/gi, 'baat kar rahi hu'], [/\bbaat kar raha hoon\b/gi, 'baat kar rahi hoon'],
      [/\bkar raha hu\b/gi, 'kar rahi hu'], [/\bkar raha hoon\b/gi, 'kar rahi hoon'],
      [/\bkr raha hu\b/gi, 'kar rahi hu'], [/\bkar raha tha\b/gi, 'kar rahi thi'],
      [/\bmaafi chahta hu\b/gi, 'maafi chahti hu'], [/\bmaafi chahta hoon\b/gi, 'maafi chahti hoon'],
      [/\bmafi chahta hu\b/gi, 'maafi chahti hu'],
      [/\bmaafi mangta hu\b/gi, 'maafi mangti hu'], [/\bmaafi mangta hoon\b/gi, 'maafi mangti hoon'],
      [/\bmafi mangta hu\b/gi, 'maafi mangti hu'],
      [/\bmaafi chahta\b/gi, 'maafi chahti'], [/\bmafi chahta\b/gi, 'maafi chahti'],
      [/\bmaafi mangta\b/gi, 'maafi mangti'], [/\bmafi mangta\b/gi, 'maafi mangti'],
      [/\bchahta hu\b/gi, 'chahti hu'], [/\bchahta hoon\b/gi, 'chahti hoon'],
      [/\bchati hu\b/gi, 'chahti hu'], [/\bchahunga\b/gi, 'chahungi'],
      [/\bkar dunga\b/gi, 'kar dungi'], [/\bkr dunga\b/gi, 'kar dungi'],
      [/\bkar lunga\b/gi, 'kar lungi'], [/\bkr lunga\b/gi, 'kar lungi'],
      [/\bde deta hu\b/gi, 'de deti hu'], [/\bdeti hu\b/gi, 'deti hu'],
      [/\bleta hu\b/gi, 'leti hu'],
      [/\bsamajhta hu\b/gi, 'samajhti hu'], [/\bsamajhta hoon\b/gi, 'samajhti hoon'],
      [/\bsamajh gaya\b/gi, 'samajh gayi'],
      [/\bkarunga\b/gi, 'karungi'], [/\baaya hu\b/gi, 'aayi hu'], [/\baaya hoon\b/gi, 'aayi hoon']
    ];
    hingRules.forEach(([pat, repl]) => { t = t.replace(pat, repl); });
  }

  return t;
}

function generateBotReply(sellerText, sig, persona) {
  const raw = sellerText || "";
  const t = raw.toLowerCase().trim();
  const isHindi = isDevanagari(raw);
  const cat = (activeScenario && activeScenario.seller) ? (activeScenario.seller.top_category_1 || "products") : "products";
  const state = (activeScenario && activeScenario.seller) ? (activeScenario.seller.seller_state || "aapke area") : "aapke area";

  const p = persona || activePersona;
  const botGender = (p && p.gender) ? p.gender.toLowerCase() : "male";
  const isMale = botGender === "male";
  const botName = (p && p.voice_name) ? p.voice_name.split("(")[0].trim() : (isMale ? "Shubh" : "Vani");

  const sellerGenderHint = (activeScenario && activeScenario.seller && (activeScenario.seller.caller_gender || activeScenario.seller.gender || activeScenario.seller.seller_gender)) ? String(activeScenario.seller.caller_gender || activeScenario.seller.gender || activeScenario.seller.seller_gender).toLowerCase() : "";
  const isCallerFemale = sellerGenderHint === "female" ||
                         t.includes("bol rahi") || t.includes("kar rahi") || t.includes("keh rahi") || t.includes("rahi hu") ||
                         t.includes("chahti") || t.includes("karti") || t.includes("bolti") || t.includes("karungi") ||
                         t.includes("gayi hu") || t.includes("gayi hoon") || t.includes("ho gayi") || t.includes("aa gayi") ||
                         t.includes("madam") || t.includes("ma'am") || t.includes("mam") || t.includes("mahila") || t.includes("didi") ||
                         raw.includes("बोल रही") || raw.includes("कर रही") || raw.includes("रही हूँ") || raw.includes("रही हु") ||
                         raw.includes("करती") || raw.includes("बोलती") || raw.includes("चाहती") || raw.includes("करूँगी") ||
                         raw.includes("गई हूँ") || raw.includes("गई हु") || raw.includes("हो गई") || raw.includes("मैडम") || raw.includes("महिला");
  const honorificHi = isCallerFemale ? "मैडम" : "सर";
  const honorificEn = isCallerFemale ? "Ma'am" : "sir";

  const bolRahaHi = isMale ? "बोल रहा हूँ" : "बोल रही हूँ";
  const bolRahaEn = isMale ? "bol raha hu" : "bol rahi hu";
  const karLungaHi = isMale ? "कर लूँगा" : "कर लूँगी";
  const karLungaEn = isMale ? "kar lunga" : "kar lungi";
  const maafiHi = isMale ? "माफी चाहता हूँ" : "माफी चाहती हूँ";
  const maafiEn = isMale ? "maafi chahta hu" : "maafi chahti hu";
  const samajhGayaHi = isMale ? "समझ गया" : "समझ गई";
  const samajhGayaEn = isMale ? "samajh gaya" : "samajh gayi";
  const karRahaHi = isMale ? "कर रहा हूँ" : "कर रही हूँ";
  const karRahaEn = isMale ? "kar raha hu" : "kar rahi hu";

  let out = "";

  // 0. Emergency De-escalation: Frustration / Anger / Do Not Call
  const sigType = (sig && sig.signal) ? sig.signal : "";
  if (sigType === "frustrated" || t.includes("bar bar") || t.includes("baar baar") || t.includes("disturb") || t.includes("band karo") || t.includes("phone kaat") || t.includes("pareshan") || t.includes("faltu call") || t.includes("dimag kharab") ||
      raw.includes("बार बार") || raw.includes("बार-बार") || raw.includes("परेशान मत करो") || raw.includes("दिमाग खराब") || raw.includes("फोन काटो") || raw.includes("काट दो") || raw.includes("बंद करो") || raw.includes("फालतू")) {
    out = isHindi
      ? `${honorificHi}, परेशान करने के लिए मैं दिल से ${maafiHi}। मैं सिस्टम में तुरंत अपडेट ${karRahaHi} ताकि आपको दोबारा बेवजह कॉल न आए। नमस्कार ${honorificHi}।`
      : `${honorificEn.charAt(0).toUpperCase() + honorificEn.slice(1)}, bilkul ${maafiEn} pareshan karne ke liye. Main abhi aapka status update ${karRahaEn} taaki bematlab call na aaye. Namaskar ${honorificEn}.`;
  }

  // 1. Constraint: Sunday / Holiday / Shop Closed
  else if (t.includes("sunday") || t.includes("itwar") || t.includes("ravivar") || t.includes("dukan band") || t.includes("chhutti") || t.includes("closed") ||
      raw.includes("रविवार") || raw.includes("संडे") || raw.includes("इतवार") || raw.includes("दुकान बंद") || raw.includes("छुट्टी")) {
    out = isHindi
      ? `अरे बिल्कुल ${honorificHi}! संडे को तो दुकान बंद रहती है, आप आराम कीजिए। सोमवार सुबह 11 बजे फर्स्ट क्लास रहेगा या दोपहर 2 बजे?`
      : `Arey bilkul ${honorificEn}, Sunday ko toh dukan band rehti hai. Somwar subah 11 baje first class rahega ya dopahar me 2 baje?`;
  }

  // 2. Constraint: Shop Crowd / Customer present / Factory floor
  else if (t.includes("bheed") || t.includes("grahak") || t.includes("customer") || t.includes("counter") || t.includes("dukaan pe hu") || t.includes("machine") ||
      raw.includes("भीड़") || raw.includes("ग्राहक खड़ा") || raw.includes("कस्टमर खड़ा") || raw.includes("काउंटर पे") || raw.includes("दुकान पे हूँ") || raw.includes("फुर्सत नहीं")) {
    out = isHindi
      ? `${samajhGayaHi} ${honorificHi}, ग्राहक को पहले अटेंड कीजिए—धंधा पहले है! मैं शाम को 7 बजे दुकान बढ़ाने के बाद कॉल करूँ?`
      : `${samajhGayaEn.charAt(0).toUpperCase() + samajhGayaEn.slice(1)} ${honorificEn}, grahak ko pehle attend kijiye—vyapar pehle hai! Main shaam ko 7 baje dukan badhane ke baad call karu?`;
  }

  // 3. Constraint: Phone / WhatsApp instead of physical visit
  else if (t.includes("phone pe") || t.includes("online hi") || t.includes("aane ki") || t.includes("milne ki") || t.includes("whatsapp pe") || t.includes("visit nahi") ||
      raw.includes("फोन पर बताओ") || raw.includes("फोन पे बताओ") || raw.includes("आने की जरूरत नहीं") || raw.includes("व्हाट्सएप पर भेजो") || raw.includes("ऑनलाइन बताओ") || raw.includes("विजिट नहीं")) {
    out = isHindi
      ? `बिल्कुल ${honorificHi}! किसी को दुकान पर आने की कोई जरूरत नहीं है। हम सीधे आपके व्हाट्सएप पर लाइव वेरिफाइड बायर्स की इंक्वायरी भेज देते हैं। क्या इसी नंबर पर व्हाट्सएप चालू है?`
      : `Bilkul ${honorificEn}! Hum aapke WhatsApp par live verified buyers ke orders bhej dete hain, kisi ko aane ki zaroorat nahi hai. Kya is number par WhatsApp chalu hai?`;
  }

  // 4. Identity / Who are you / Bot check
  else if (t.includes("kaun bol") || t.includes("kon bol") || t.includes("kiska call") || t.includes("who are you") || t.includes("bot") || t.includes("robot") || t.includes("insaan") || t.includes("kaha se") ||
      raw.includes("कौन बोल") || raw.includes("किसका फोन") || raw.includes("बॉट हो") || raw.includes("रोबोट") || raw.includes("इंसान")) {
    const isBotQ = t.includes("bot") || t.includes("robot") || t.includes("insaan") || raw.includes("बॉट") || raw.includes("रोबोट") || raw.includes("इंसान");
    if (isBotQ) {
      out = isHindi
        ? `${honorificHi}, मैं इंडियामार्ट से ${botName} ${bolRahaHi}, एक डिजिटल वॉइस असिस्टेंट। आपके ${cat} के काम के लिए नए वेरिफाइड बायर्स की डिमांड आई है, इसलिए सीधे आपको इन्फॉर्म किया।`
        : `Main IndiaMART se ${botName} ${bolRahaEn} ${honorificEn}, ek digital voice assistant. Humare paas aapke ${cat} ke business ke liye verified buyer leads aayi hain.`;
    } else {
      out = isHindi
        ? `${honorificHi}, मैं इंडियामार्ट के सेलर सपोर्ट से ${botName} ${bolRahaHi}। हम बिना काम के फोन नहीं करते—आपके एरिया में ${cat} के वेरिफाइड बायर्स के नए ऑर्डर्स पेंडिंग थे, इसलिए सीधे आपको कॉल किया।`
        : `${honorificEn.charAt(0).toUpperCase() + honorificEn.slice(1)}, main IndiaMART ke seller team se ${botName} ${bolRahaEn}. Aapke area mein ${cat} ke verified buyers ke orders aaye the, isliye direct aapko phone kiya hai.`;
    }
  }

  // 5. Purpose: Kyu milna hai / Kya fayda hoga
  else if (t.includes("kyu milna") || t.includes("kis regarding") || t.includes("kya fayda") || t.includes("kya bataoge") || t.includes("purpose") || t.includes("kis baare me") ||
      raw.includes("क्यों फोन किया") || raw.includes("क्या काम है") || raw.includes("किसलिए") || raw.includes("क्या फायदा")) {
    out = isHindi
      ? `${honorificHi}, पिछले हफ्ते आपके शहर में ${cat} के 25 से ज्यादा वेरिफाइड बल्क ऑर्डर्स आए हैं। हम बस आपको व्हाट्सएप पर दिखाना चाहते हैं कि बिना किसी रिस्क के बायर्स से सीधे कैसे जुड़ना है।`
      : `${honorificEn.charAt(0).toUpperCase() + honorificEn.slice(1)}, pichle hafte aapke sheher mein ${cat} ke 25 se zyada verified bulk orders pending the. Hum bas aapko mobile par dikhana chahte hain ki buyers se direct kaise judna hai bina kisi advance kharche ke.`;
  }

  // 6. Pricing / Charges / Cost
  else if (t.includes("kitna kharcha") || t.includes("kitne paise") || t.includes("price") || t.includes("pricing") || t.includes("cost") || t.includes("package") || t.includes("rate") ||
      raw.includes("कितना खर्चा") || raw.includes("कितना पैसा") || raw.includes("रेट क्या") || raw.includes("भाव क्या") || raw.includes("पैकेज") || raw.includes("सीधे-सीधे बताओ")) {
    out = isHindi
      ? `${honorificHi}, इंडियामार्ट पर महीने का लगभग 2,000 से 2,500 रुपये से प्लान शुरू होते हैं, जिसमें बायर्स सीधे आपके फोन पर कॉल करते हैं। पहले आप बिना कोई पैसा दिए फ्री में डिमांड देख लीजिए।`
      : `${honorificEn.charAt(0).toUpperCase() + honorificEn.slice(1)}, IndiaMART par packages lagbhag 2,000 se 2,500 rupaye mahine se shuru hote hain. Isme verified buyers direct aapke phone par call karte hain. Pehle aap bina kisi paise ke demand dekh lijiye.`;
  }

  // 7. Skepticism & Past Experience: Fake leads / Paise waste
  else if (t.includes("fayda nahi") || t.includes("pehle bhi") || t.includes("fake lead") || t.includes("bekar lead") || t.includes("paise waste") || t.includes("paise doob") ||
      raw.includes("पैसे डूब गए") || raw.includes("फेक लीड") || raw.includes("बेकार लीड") || raw.includes("नुकसान हुआ") || raw.includes("धोखा")) {
    out = isHindi
      ? `आपका गुस्सा बिल्कुल सही है ${honorificHi}, पहले बिना ओटीपी वाली पुरानी लीड्स आ जाती थीं। पर अब इंडियामार्ट ने जीएसटी और मोबाइल ओटीपी वेरिफाइड फिल्टर अनिवार्य कर दिया है। आप एक बार बिना किसी पेमेंट के खुद डिमांड देख लीजिए।`
      : `Aapka gussa bilkul sahi hai ${honorificEn}, pehle unverified enquiries aati thi. Par ab humne mobile OTP aur GST filter mandatory kar diya hai. Jaise aapke sheher ke 15 suppliers regular orders nikaal rahe hain, aap ek bar bina risk ke review karke dekhein.`;
  }

  // 8. Free User / Not interested in paid
  else if (t.includes("free wala") || t.includes("paid nahi") || t.includes("nahi chahiye") ||
      raw.includes("फ्री वाला") || raw.includes("पेड नहीं") || raw.includes("नहीं चाहिए")) {
    out = isHindi
      ? `बिल्कुल सही ${honorificHi}, आप फ्री वाला ही इस्तेमाल करते रहिए! बस अपने प्रोफाइल में 2-3 नए प्रोडक्ट्स की फोटो व्हाट्सएप से अपडेट करवा लीजिए, ताकि जो फ्री इंक्वायरी आती हैं उनकी क्वालिटी और बढ़ जाए।`
      : `Bilkul sahi ${honorificEn}, aap free wala hi use karte rahiye! Bas apne profile par 2-3 naye products ki photo WhatsApp se update karwa lijiye, taaki free enquiries ki quality aur behtar ho jaye.`;
  }

  // 9. Payment security / Fraud / Advance
  else if (t.includes("payment") || t.includes("paise fas") || t.includes("fraud") || t.includes("safe") ||
      raw.includes("पेमेंट") || raw.includes("पैसे फंस") || raw.includes("गारंटी") || raw.includes("फ्रॉड")) {
    out = isHindi
      ? `इंडियामार्ट पर 'Pay with IndiaMART' एस्क्रो सुरक्षा है ${honorificHi}—जब तक बायर को सामान नहीं मिलता और आप कन्फर्म नहीं करते, पेमेंट 100% बैंक में सुरक्षित रहती है।`
      : `IndiaMART par 'Pay with IndiaMART' escrow protection hai ${honorificEn}—jab tak aapka delivery confirmation nahi hota, payment 100% bank-guaranteed secure rehti hai.`;
  }

  // 10A. Driving / In transit (Safety First)
  else if (t.includes("driving") || t.includes("gaadi chala") || t.includes("bike pe") || t.includes("traffic") ||
      raw.includes("ड्राइविंग") || raw.includes("गाड़ी चला") || raw.includes("बाइक पर") || raw.includes("ट्रैफिक में")) {
    out = isHindi
      ? `अरे ${honorificHi}, आप सुरक्षित ड्राइव कीजिए! मैं 2 घंटे बाद या शाम को कॉल ${karLungaHi}। ध्यान से चलिएगा ${honorificHi}!`
      : `Arey ${honorificEn}, aap bilkul safe drive kijiye! Main 2 ghante baad ya shaam ko call ${karLungaEn}. Dhyan se chaliyega ${honorificEn}!`;
  }

  // 10B. Busy / Occupied / Meeting (Respect Time)
  else if (t.includes("busy") || t.includes("vyast") || t.includes("time nahi") || t.includes("fursat nahi") || t.includes("meeting") ||
      raw.includes("व्यस्त") || raw.includes("मीटिंग") || raw.includes("समय नहीं") || raw.includes("टाइम नहीं")) {
    out = isHindi
      ? `${samajhGayaHi} ${honorificHi}, आपका समय बहुत कीमती है। क्या मैं आज शाम को 7 बजे या कल सुबह 11 बजे कॉल ${karLungaHi}?`
      : `${samajhGayaEn.charAt(0).toUpperCase() + samajhGayaEn.slice(1)} ${honorificEn}, bilkul samajh sakta hu aap busy hain. Main shaam ko 7 baje ya kal subah 11 baje call ${karLungaEn}?`;
  }

  // 10C. Scheduling: Specific Day/Time vs General Postponement
  else if (t.includes("kal") || t.includes("somwar") || t.includes("mangalwar") || t.includes("baje") || t.includes("dopahar") || t.includes("shaam") ||
      raw.includes("सोमवार") || raw.includes("मंगलवार") || raw.includes("कल") || raw.includes("बजे") || raw.includes("शाम को")) {
    out = isHindi
      ? `बहुत बढ़िया ${honorificHi}! मैंने समय नोट कर लिया है। उसी समय इंडियामार्ट से हमारा कॉल आएगा। धन्यवाद, आपका दिन शुभ हो!`
      : `Theek hai ${honorificEn}! Maine samay note kar liya hai, hum usi time connect karenge. Bahut-bahut shukriya, shubh din!`;
  }

  else if (t.includes("baad me") || t.includes("abhi nahi") || t.includes("later") || raw.includes("बाद में") || raw.includes("अभी नहीं")) {
    out = isHindi
      ? `${samajhGayaHi} ${honorificHi}, क्या आज शाम को 7 बजे या कल दोपहर में 2 बजे कॉल ${karLungaHi}?`
      : `${samajhGayaEn.charAt(0).toUpperCase() + samajhGayaEn.slice(1)} ${honorificEn}, kya aaj shaam ko 7 baje ya kal dopahar 2 baje call ${karLungaEn}?`;
  }

  // Default contextual fallback matching script
  else if (isHindi) {
    if (sig && sig.signal === "engaged") {
      out = `जी बिल्कुल ${honorificHi}! हम सीधे आपके व्हाट्सएप पर वेरिफाइड खरीदारों के बल्क ऑर्डर्स शेयर कर देते हैं। क्या इसी नंबर पर व्हाट्सएप चालू है?`;
    } else {
      out = `जी ${honorificHi}, ${cat} के नए वेरिफाइड बायर्स ऑर्डर्स लेना चाहते हैं। क्या मैं व्हाट्सएप पर डिटेल शेयर कर दूँ?`;
    }
  } else {
    if (sig && sig.signal === "engaged") {
      out = `Ji bilkul ${honorificEn}! Hum aapke WhatsApp par verified bulk inquiries share kar dete hain. Kya is number par WhatsApp chalu hai?`;
    } else {
      out = `Ji ${honorificEn}, ${cat} ke regarding naye verified buyers orders dena chahte hain. Kya main WhatsApp par details share kar du?`;
    }
  }

  return enforceSpeakerGender(out, botGender);
}

// ── Audio Playback ─────────────────────────────────────────
async function playBotAudio(text, existingB64, overrideSpeaker, overridePace, overrideLang) {
  const audioElem = document.getElementById("global-audio-player");
  
  if (existingB64 && existingB64.length > 100) {
    audioElem.src = `data:audio/wav;base64,${existingB64}`;
    audioElem.play().catch(e => console.log("Audio play prevented:", e));
    return;
  }

  const speaker = overrideSpeaker || (activePersona ? activePersona.voice_id : "shubh_enhi_ads");
  const pace = overridePace !== undefined ? overridePace : (activePersona ? activePersona.pace : 1.0);
  const lang = overrideLang || ((activePersona && activePersona.language_mix === "indian_english") ? "en-IN" : "hi-IN");

  // Request TTS from server
  try {
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        speaker,
        pace,
        language_code: lang
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.audio_base64 && data.audio_base64.length > 100) {
        audioElem.src = `data:audio/wav;base64,${data.audio_base64}`;
        audioElem.play().catch(e => console.log("Audio play error:", e));
        return;
      }
    }
  } catch (e) {
    console.log("TTS fetch failed, falling back to Web Speech API.");
  }

  // Browser speech synthesis fallback so the user can hear the voice
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = activePersona ? activePersona.pace : 1.0;
    utter.lang = (activePersona && activePersona.language_mix === "indian_english") ? "en-IN" : "hi-IN";
    window.speechSynthesis.speak(utter);
  }
}

// ── Telemetry View Updates ─────────────────────────────────
function updateTelemetrySignal(signal, conf, action) {
  const pill = document.getElementById("telemetry-signal-pill");
  pill.className = `sig-pill sig-${signal}`;
  pill.textContent = signal.toUpperCase();
  document.getElementById("telemetry-signal-conf").textContent = `Conf: ${(conf || 0.8).toFixed(2)}`;
  document.getElementById("telemetry-signal-action").textContent = action;
}

function appendTelemetryTrajectory(event) {
  const list = document.getElementById("telemetry-trajectory-list");
  const empty = list.querySelector(".empty-timeline");
  if (empty) empty.remove();

  const item = document.createElement("div");
  item.className = `trajectory-item traj-${event.signal_detected}`;

  const changesStr = Object.entries(event.changes_made || {})
    .filter(([k]) => k !== "instruction")
    .map(([k, v]) => `${k}: ${v.from} ➔ ${v.to}`)
    .join(", ");

  item.innerHTML = `
    <div class="traj-turn">Turn #${event.turn_number} • ${event.signal_detected.toUpperCase()}</div>
    <div class="traj-changes">${changesStr || 'Adapted Style'}</div>
    <div class="traj-rationale">${event.adaptation_rationale || ''}</div>
  `;

  list.insertBefore(item, list.firstChild);
}

// ── Archetype Presets Catalog ──────────────────────────────
const ARCHETYPE_PRESETS = {
  mandi_vyapari: {
    voice_id: "shubh_enhi_ads",
    voice_name: "Chandan Bhaiya (Wholesale Specialist)",
    gender: "male",
    pitch_register: "medium_resonant",
    pace: 0.95,
    tone: "consultative",
    language: "hindi",
    strategy: "social_proof",
    formality: "respectful_warm",
    opening_line: "Namaskar sir! Main IndiaMART se bol raha hoon, aapke wholesale business ke liye verified buyers ke bulk inquiries check kar rahe the.",
    seller_state: "Uttar Pradesh",
    category: "Industrial Valves & Fittings",
    turnover: "40 L - 1.5 Cr",
    business_type: "Proprietorship",
    nature: "Manufacturer"
  },
  empathetic_resolver: {
    voice_id: "ishita_enhi_customer",
    voice_name: "Priya Sharma (Empathetic Problem Solver)",
    gender: "female",
    pitch_register: "warm",
    pace: 0.90,
    tone: "empathetic_problem_solver",
    language: "hinglish",
    strategy: "problem_solving",
    formality: "respectful_warm",
    opening_line: "Namaste sir, main IndiaMART se Priya baat kar rahi hu. Hum samajhte hain aapka samay kimti hai, kya 2 minute verified leads ke bare me baat ho sakti hai?",
    seller_state: "Rajasthan",
    category: "Brass God Statues",
    turnover: "0 - 40 L",
    business_type: "Proprietorship",
    nature: "Trader - Wholesaler/Distributor"
  },
  fast_closer: {
    voice_id: "sunny_enhi_customer",
    voice_name: "Vikram Malhotra (Metro Closer)",
    gender: "male",
    pitch_register: "bright_crisp",
    pace: 1.10,
    tone: "direct_closing",
    language: "hinglish",
    strategy: "product_features",
    formality: "formal_corporate",
    opening_line: "Hello sir, Vikram here from IndiaMART! We have 14 direct bulk enquiries for your category in NCR. Can I share the summary on WhatsApp right now?",
    seller_state: "Delhi",
    category: "Color Coating Services",
    turnover: "1.5 - 5 Cr",
    business_type: "Private Limited",
    nature: "Manufacturer"
  },
  traditional_guide: {
    voice_id: "ritu_hi_customer",
    voice_name: "Sunita Patel (Trade Consultant)",
    gender: "female",
    pitch_register: "reassuring",
    pace: 0.92,
    tone: "reassuring_patient",
    language: "hindi",
    strategy: "social_proof",
    formality: "respectful_warm",
    opening_line: "Ram Ram ji! Main IndiaMART se Sunita baat kar rahi hu. Jaise aapki mandi me dukan hoti hai, waise hi digital dukan ke vishay me charcha karni thi.",
    seller_state: "Gujarat",
    category: "Ceramic Floor Tiles",
    turnover: "40 L - 1.5 Cr",
    business_type: "Partnership",
    nature: "Manufacturer"
  }
};

// ── Tab 2: Persona Studio ──────────────────────────────────
function initPersonaStudio() {
  const form = document.getElementById("form-persona-studio");
  if (!form) return;

  // 1-Click Preset Card click handlers
  const presetCards = document.querySelectorAll(".archetype-preset-card");
  presetCards.forEach(card => {
    card.addEventListener("click", () => {
      presetCards.forEach(c => c.classList.remove("active-preset"));
      card.classList.add("active-preset");
      const key = card.getAttribute("data-preset");
      const data = ARCHETYPE_PRESETS[key];
      if (!data) return;

      if (document.getElementById("studio-voice-id")) document.getElementById("studio-voice-id").value = data.voice_id;
      if (document.getElementById("studio-pace")) document.getElementById("studio-pace").value = String(data.pace);
      if (document.getElementById("studio-tone")) document.getElementById("studio-tone").value = data.tone;
      if (document.getElementById("studio-language")) document.getElementById("studio-language").value = data.language;
      if (document.getElementById("studio-strategy")) document.getElementById("studio-strategy").value = data.strategy;
      if (document.getElementById("studio-formality")) document.getElementById("studio-formality").value = data.formality;
      if (document.getElementById("studio-opening-line")) document.getElementById("studio-opening-line").value = data.opening_line;
      if (document.getElementById("studio-seller-state")) document.getElementById("studio-seller-state").value = data.seller_state;
      if (document.getElementById("studio-category")) document.getElementById("studio-category").value = data.category;
      if (document.getElementById("studio-turnover")) document.getElementById("studio-turnover").value = data.turnover;
      if (document.getElementById("studio-business-type")) document.getElementById("studio-business-type").value = data.business_type;
      if (document.getElementById("studio-nature")) document.getElementById("studio-nature").value = data.nature;

      // Automatically build preview blueprint
      buildAndRenderCustomPersona();
    });
  });

  // Form Submission
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    buildAndRenderCustomPersona();
  });

  // Initial render of default preset blueprint
  setTimeout(() => {
    buildAndRenderCustomPersona();
  }, 200);
}

function buildAndRenderCustomPersona() {
  const voiceId = document.getElementById("studio-voice-id") ? document.getElementById("studio-voice-id").value : "shubh_enhi_ads";
  const paceVal = parseFloat(document.getElementById("studio-pace") ? document.getElementById("studio-pace").value : "0.95") || 0.95;
  const toneVal = document.getElementById("studio-tone") ? document.getElementById("studio-tone").value : "consultative";
  const langVal = document.getElementById("studio-language") ? document.getElementById("studio-language").value : "hindi";
  const stratVal = document.getElementById("studio-strategy") ? document.getElementById("studio-strategy").value : "social_proof";
  const formalityVal = document.getElementById("studio-formality") ? document.getElementById("studio-formality").value : "respectful_warm";
  const openingLine = document.getElementById("studio-opening-line") ? document.getElementById("studio-opening-line").value : "Namaskar sir! Main IndiaMART se bol raha hoon.";

  const sellerId = (document.getElementById("studio-seller-id") && document.getElementById("studio-seller-id").value) || "987654321";
  const sellerState = (document.getElementById("studio-seller-state") && document.getElementById("studio-seller-state").value) || "Uttar Pradesh";
  const category = (document.getElementById("studio-category") && document.getElementById("studio-category").value) || "Industrial Valves & Fittings";
  const turnover = (document.getElementById("studio-turnover") && document.getElementById("studio-turnover").value) || "40 L - 1.5 Cr";
  const businessType = (document.getElementById("studio-business-type") && document.getElementById("studio-business-type").value) || "Proprietorship";
  const nature = (document.getElementById("studio-nature") && document.getElementById("studio-nature").value) || "Manufacturer";

  const VOICE_METAS = {
    shubh_enhi_ads: { name: "Shubh (Resonant Commercial Male)", gender: "male", pitch: "medium_resonant" },
    ishita_enhi_customer: { name: "Ishita / Priya (Warm Empathetic Female)", gender: "female", pitch: "warm" },
    sunny_enhi_customer: { name: "Sunny / Vikram (Crisp High-Velocity Male)", gender: "male", pitch: "bright_crisp" },
    ritu_hi_customer: { name: "Ritu / Sunita (Traditional Regional Female)", gender: "female", pitch: "reassuring" }
  };
  const meta = VOICE_METAS[voiceId] || { name: voiceId, gender: "neutral", pitch: "medium" };

  const customPersona = {
    seller_id: String(sellerId),
    voice_id: voiceId,
    voice_name: meta.name,
    gender: meta.gender,
    pitch_register: meta.pitch,
    pace: paceVal,
    formality: formalityVal,
    tone: toneVal,
    language_mix: langVal,
    script_strategy: stratVal,
    opening_line: openingLine,
    system_prompt: `You are IndiaMART voice executive representing ${meta.name} with ${toneVal} tone and ${paceVal}x pace.`,
    rationale: {
      voice_delivery: `${meta.name} calibrated at ${paceVal.toFixed(2)}x tempo for high comprehension.`,
      conversational_tone: `${formatKey(toneVal)} style aligned with ${formatKey(langVal)} linguistic cadence.`,
      seller_market: `${category} in ${sellerState} (${turnover} turnover).`,
      persuasion_strategy: `${formatKey(stratVal)} with ${formatKey(formalityVal)} protocol.`
    },
    metadata: { is_custom: true, created_at: new Date().toISOString() }
  };

  const customSeller = {
    fk_glusr_usr_id: sellerId,
    seller_state: sellerState,
    top_category_1: category,
    annual_turnover: turnover,
    business_type: businessType,
    nature_of_business: nature,
    bot_answered: 1,
    showed_frustration: 0,
    past_objections: "",
    past_dispositions_detailed: "custom_configured_seller"
  };

  renderStudioBlueprint(customPersona, customSeller);
}

function renderStudioBlueprint(p, seller) {
  const card = document.getElementById("studio-result-content");
  if (!card) return;

  const badgeElem = document.getElementById("studio-persona-badge");
  if (badgeElem) badgeElem.textContent = "Custom Configured";

  card.innerHTML = `
    <div class="voice-hero-card">
      <div class="speaker-avatar">${p.gender === "female" ? "👩" : "👨"}</div>
      <div class="speaker-meta">
        <h4>${p.voice_name || p.voice_id}</h4>
        <span class="speaker-id">Voice ID: ${p.voice_id}</span>
        <div class="tag-row">
          <span class="chip chip-sm">Gender: ${p.gender}</span>
          <span class="chip chip-sm">Pitch: ${p.pitch_register}</span>
          <span class="chip chip-sm">Pace: ${p.pace.toFixed(2)}x</span>
        </div>
      </div>
    </div>

    <div class="gauges-grid" style="margin-top: 14px;">
      <div class="prop-row"><span class="prop-name">Formality:</span><span class="chip chip-highlight">${formatKey(p.formality)}</span></div>
      <div class="prop-row"><span class="prop-name">Tone:</span><span class="chip chip-primary">${formatKey(p.tone)}</span></div>
      <div class="prop-row"><span class="prop-name">Language Mix:</span><span class="chip chip-accent">${formatKey(p.language_mix)}</span></div>
      <div class="prop-row"><span class="prop-name">Script Strategy:</span><span class="chip chip-warning">${formatKey(p.script_strategy)}</span></div>
    </div>

    <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: var(--radius-sm); margin: 14px 0; border: 1px solid var(--border-subtle);">
      <h5 style="color: var(--accent-cyan); font-size: 0.8rem; margin-bottom: 4px;">Tailored Opening Greeting (Audio Ready):</h5>
      <p style="font-size: 0.85rem; color: #fff; line-height: 1.5;">"${escapeHtml(p.opening_line)}"</p>
      <button type="button" class="turn-audio-btn" id="btn-studio-play-audio" style="margin-top: 10px;">
        🔊 Preview Opening Voice (${p.voice_id} • ${p.pace.toFixed(2)}x)
      </button>
    </div>

    <div class="rationale-box">
      <h4>💡 Evidence Rationale:</h4>
      <ul class="rationale-bullets">
        ${Object.entries(p.rationale || {}).map(([k, v]) => `<li><strong>${formatKey(k)}:</strong> ${v}</li>`).join("")}
      </ul>
    </div>

    <!-- Glowing Launch CTA -->
    <button type="button" class="btn btn-launch-talk" id="btn-studio-launch-call">
      🚀 Launch Live Call & Talk to My Persona
    </button>
  `;

  // Attach Audio Preview
  const btnAudio = document.getElementById("btn-studio-play-audio");
  if (btnAudio) {
    btnAudio.addEventListener("click", () => {
      playBotAudio(p.opening_line, null, p.voice_id, p.pace, p.language_mix === "indian_english" ? "en-IN" : "hi-IN");
    });
  }

  // Attach Launch Live Call Handler
  const btnLaunch = document.getElementById("btn-studio-launch-call");
  if (btnLaunch) {
    btnLaunch.addEventListener("click", () => {
      launchCustomPersonaCall(p, seller);
    });
  }
}

function launchCustomPersonaCall(persona, seller) {
  activePersona = JSON.parse(JSON.stringify(persona));
  initialPersona = JSON.parse(JSON.stringify(persona));

  const shortName = persona.voice_name.split("(")[0].trim();
  activeScenario = {
    scenario_id: "custom_" + Date.now(),
    title: shortName,
    subtitle: `${seller.top_category_1} (${seller.annual_turnover}) • Custom Persona`,
    seller: seller,
    dialogue_script: []
  };

  // 1. Switch smoothly to Live Call tab
  switchTab("tab-sim");

  // 2. Update Call Topbar
  const sellerTitle = document.getElementById("call-seller-name");
  const sellerLoc = document.getElementById("call-seller-loc");
  if (sellerTitle) sellerTitle.textContent = `${seller.top_category_1} (${seller.nature_of_business || "MSME"})`;
  if (sellerLoc) sellerLoc.textContent = `${seller.seller_state} • ${seller.annual_turnover} Turnover`;

  // 3. Render Left panel Persona Card with custom attributes
  renderPersonaCard(activePersona);

  // 4. Reset & start the call simulation with custom opening line
  resetCallSimulation();
  startCallSimulation();

  // 5. Immediately speak the opening line using custom voice & pace!
  playBotAudio(activePersona.opening_line);

  // 6. Highlight & focus the input for immediate testing
  setTimeout(() => {
    const inputElem = document.getElementById("input-custom-utterance");
    if (inputElem) {
      inputElem.focus();
      inputElem.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, 400);
}

// ── Tab 3: Signal Lab ──────────────────────────────────────
function initSignalLab() {
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById("lab-input-text").value = btn.getAttribute("data-sample");
    });
  });

  document.getElementById("btn-run-signal-test").addEventListener("click", async () => {
    const text = document.getElementById("lab-input-text").value.trim();
    if (!text) return;

    const interrupted = document.getElementById("lab-toggle-interruption").checked;
    const noise = document.getElementById("lab-toggle-noise").checked;

    let sig = null;
    try {
      const res = await fetch("/api/detect_signal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          acoustic_features: {
            interrupted,
            background_noise_level: noise ? "high" : "low",
            snr_db: noise ? 8 : 28
          }
        })
      });
      if (res.ok) {
        const data = await res.json();
        sig = data.signal;
      }
    } catch (e) {}

    if (!sig) {
      sig = clientDetectSignal(text);
      if (interrupted) sig.signal = "interrupted";
      if (noise) sig.signal = "noise";
    }

    renderLabResult(sig, text);
  });
}

function renderLabResult(sig, text) {
  const container = document.getElementById("lab-result-content");
  document.getElementById("lab-badge-output").textContent = sig.signal.toUpperCase();

  container.innerHTML = `
    <div style="background: rgba(0,0,0,0.25); padding: 14px; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); margin-bottom: 14px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span class="sig-pill sig-${sig.signal}" style="font-size: 0.85rem; padding: 4px 12px;">
          ${sig.signal.toUpperCase()}
        </span>
        <strong style="color: var(--accent-cyan);">Confidence: ${(sig.confidence || 0.85).toFixed(2)}</strong>
      </div>
      <p style="font-size: 0.85rem; color: #fff; margin-bottom: 8px;">"${escapeHtml(text)}"</p>
      <div style="font-size: 0.78rem; color: var(--text-secondary);">
        <strong>Cues Matched:</strong> ${sig.cues_matched && sig.cues_matched.length ? sig.cues_matched.join(", ") : "Acoustic / Pattern Rules"}
      </div>
    </div>

    <div class="danger-box" style="background: rgba(6, 182, 212, 0.1); border-color: rgba(6, 182, 212, 0.3);">
      <h4 style="color: var(--accent-cyan);">⚡ Recommended Dynamic Persona Adaptation:</h4>
      <p style="color: #fff; font-size: 0.85rem;">${sig.recommended_action}</p>
    </div>
  `;
}

// ── Tab 4: Memory Tab ──────────────────────────────────────
async function initMemoryTab() {
  document.getElementById("btn-reset-memory-store").addEventListener("click", async () => {
    try {
      await fetch("/api/memory/reset", { method: "POST" });
    } catch (e) {}
    loadMemoryCards();
  });
}

async function loadMemoryCards() {
  const container = document.getElementById("memory-cards-container");
  container.innerHTML = "<p class='placeholder-text'>Loading seller memory profiles...</p>";

  let memories = {};
  try {
    const res = await fetch("/api/memory");
    if (res.ok) {
      const data = await res.json();
      memories = data.memories || {};
    }
  } catch (e) {}

  container.innerHTML = "";
  const sids = Object.keys(memories);

  if (sids.length === 0) {
    container.innerHTML = `
      <div class="glass-card" style="grid-column: 1 / -1; text-align: center; padding: 40px;">
        <h3>No Memory Records Yet</h3>
        <p style="color: var(--text-secondary); margin-top: 8px;">Run calls in the Live Simulation tab to generate persistent learned profiles for IndiaMART sellers.</p>
      </div>
    `;
    return;
  }

  sids.forEach(sid => {
    const m = memories[sid];
    const card = document.createElement("div");
    card.className = "seller-memory-card";
    card.innerHTML = `
      <div class="memory-header">
        <h4>Seller ID: ${sid}</h4>
        <span class="chip chip-highlight">${m.successful_calls}/${m.total_calls} Meetings</span>
      </div>
      <div style="font-size: 0.8rem; display: flex; flex-direction: column; gap: 4px;">
        <div><strong>Learned Preferred Pace:</strong> <span style="color: var(--accent-cyan);">${m.preferred_pace ? m.preferred_pace.toFixed(2) + 'x' : 'Baseline'}</span></div>
        <div><strong>Preferred Tone:</strong> ${formatKey(m.preferred_tone)}</div>
        <div><strong>Preferred Language:</strong> ${formatKey(m.preferred_language)}</div>
        <div><strong>Logged Objections:</strong> ${m.past_objections_logged && m.past_objections_logged.length ? m.past_objections_logged.join(", ") : "None"}</div>
        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">Last Updated: ${m.last_updated}</div>
      </div>
    `;
    container.appendChild(card);
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ── Mid-Call Adaptation Visual Alert ──────────────────────
let adaptationAlertTimeout = null;
function showAdaptationAlert(event) {
  const banner = document.getElementById("adaptation-alert-banner");
  const title = document.getElementById("alert-title");
  const desc = document.getElementById("alert-desc");
  if (!banner || !event) return;

  const sig = (event.signal_detected || "SHIFT").toUpperCase();
  const conf = Math.round(((event.confidence || 0.90) * 100));
  const tone = formatKey(event.new_persona ? event.new_persona.tone : "");
  const pace = event.new_persona ? event.new_persona.pace.toFixed(2) : "1.00";
  
  if (title) {
    title.textContent = `⚡ MID-CALL ADAPTATION: ${sig} DETECTED (${conf}% CONFIDENCE)`;
  }
  if (desc) {
    const changesStr = Object.entries(event.changes_made || {})
      .filter(([k]) => k !== "instruction")
      .map(([k, v]) => `${k.toUpperCase()}: ${v.from} ➔ ${v.to}`)
      .join(" • ");
    desc.textContent = `${changesStr || 'Cadence adjusted'} • Tone: "${tone}" • Pace: ${pace}x. ${event.adaptation_rationale || ''}`;
  }

  banner.style.display = "flex";
  banner.classList.remove("fade-out");
  banner.classList.add("pulse-glow");

  if (adaptationAlertTimeout) clearTimeout(adaptationAlertTimeout);
  adaptationAlertTimeout = setTimeout(() => {
    banner.classList.remove("pulse-glow");
    banner.classList.add("fade-out");
    setTimeout(() => {
      if (banner.classList.contains("fade-out")) {
        banner.style.display = "none";
      }
    }, 600);
  }, 7000);
}

// ── Mid-Call Mood Shift Toolbar ────────────────────────────
function initMoodShiftToolbar() {
  const angryBtn = document.getElementById("btn-mood-angry");
  const rushedBtn = document.getElementById("btn-mood-rushed");
  const skepticalBtn = document.getElementById("btn-mood-skeptical");
  const curiousBtn = document.getElementById("btn-mood-curious");

  const triggers = [
    {
      btn: angryBtn,
      text: "Baar baar kyu phone karte ho, band karo ye phone! Hume koi package nahi chahiye, disturb mat karo!"
    },
    {
      btn: rushedBtn,
      text: "Abhi counter pe grahakon ki bheed hai, bilkul time nahi hai baat karne ka!"
    },
    {
      btn: skepticalBtn,
      text: "Pehle bhi 25 hazaar diye the, koi genuine buyer nahi aaya, sab paise waste gaye the!"
    },
    {
      btn: curiousBtn,
      text: "Achha samajh gaya, par ye batao ki hamare area me marble ke kitne bulk buyers hain?"
    }
  ];

  triggers.forEach(({ btn, text }) => {
    if (btn) {
      btn.addEventListener("click", () => {
        const inputElem = document.getElementById("input-custom-utterance");
        if (inputElem) {
          inputElem.value = text;
        }
        processSellerUtterance(text);
      });
    }
  });
}

// ── Prompt-to-Seller Roleplay Simulator ─────────────────────
function initRoleplaySimulator() {
  const inputPrompt = document.getElementById("input-roleplay-prompt");
  const btnLaunch = document.getElementById("btn-launch-prompt-seller");
  const exitBtn = document.getElementById("btn-exit-roleplay");
  const banner = document.getElementById("roleplay-active-banner");

  if (!btnLaunch || !inputPrompt) return;

  // Inspiration Chips Click Handlers
  document.querySelectorAll(".inspiration-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const promptText = chip.getAttribute("data-prompt");
      if (promptText) {
        inputPrompt.value = promptText;
        inputPrompt.focus();
        inputPrompt.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  });

  // Launch Live Call from Prompt
  btnLaunch.addEventListener("click", async () => {
    let promptVal = inputPrompt.value.trim();
    if (!promptVal) {
      promptVal = "I am a 48-year-old brass handicrafts manufacturer in Moradabad, turnover 80 Lakhs, speaking polite Hindi. I will start calm, but if you pitch paid plans I will get angry because I lost money before.";
      inputPrompt.value = promptVal;
    }

    const origBtnText = btnLaunch.innerHTML;
    btnLaunch.disabled = true;
    btnLaunch.innerHTML = "⏳ Generating Live Seller & Persona...";

    try {
      const res = await fetch("/api/create_custom_seller", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: promptVal })
      });

      if (!res.ok) {
        throw new Error(`Server responded with HTTP ${res.status}`);
      }

      const data = await res.json();
      const seller = data.seller;
      const persona = data.persona;

      activePersona = JSON.parse(JSON.stringify(persona));
      initialPersona = JSON.parse(JSON.stringify(persona));

      const sellerTitle = `${seller.top_category_1 || "MSME Business"} Seller`;
      const sellerSub = `${seller.seller_state || "India"} • ${seller.annual_turnover || "Turnover Unspecified"}`;

      activeScenario = {
        scenario_id: "roleplay_" + Date.now(),
        title: sellerTitle,
        subtitle: `${sellerSub} • Roleplay Mode`,
        seller: seller,
        dialogue_script: []
      };

      // 1. Show active roleplay banner
      if (banner) {
        banner.style.display = "flex";
        const heading = document.getElementById("roleplay-character-heading");
        const sub = document.getElementById("roleplay-character-sub");
        if (heading) {
          heading.textContent = `Roleplaying as: ${sellerTitle} (${seller.seller_state || "MSME"})`;
        }
        if (sub) {
          sub.textContent = `Turnover: ${seller.annual_turnover} | Mood: ${seller.initial_mood || "Calm"} ➔ Test getting angry or rushed with the toolbar below!`;
        }
      }

      // 2. Switch tab to Live Simulation
      switchTab("tab-sim");

      // 3. Update Call Topbar
      const nameElem = document.getElementById("call-seller-name");
      const locElem = document.getElementById("call-seller-loc");
      if (nameElem) nameElem.textContent = `${seller.top_category_1} (${seller.nature_of_business || seller.business_type || "MSME"})`;
      if (locElem) locElem.textContent = `${seller.seller_state} • ${seller.annual_turnover} Turnover`;

      // 4. Update left Persona Card
      renderPersonaCard(activePersona);

      // 5. Reset & start call simulation
      resetCallSimulation();
      startCallSimulation();

      // 6. Speak opening line with audio
      playBotAudio(activePersona.opening_line, data.opening_audio_base64);

      // 7. Scroll smoothly to call area & focus utterance input
      setTimeout(() => {
        const streamContainer = document.getElementById("conversation-stream-container");
        if (streamContainer) {
          streamContainer.scrollIntoView({ behavior: "smooth", block: "center" });
        }
        const inputElem = document.getElementById("input-custom-utterance");
        if (inputElem) {
          inputElem.focus();
        }
      }, 500);

    } catch (err) {
      console.error("Roleplay generation error:", err);
      alert("Failed to build custom seller: " + err.message);
    } finally {
      btnLaunch.disabled = false;
      btnLaunch.innerHTML = origBtnText;
    }
  });

  // Exit roleplay button
  if (exitBtn) {
    exitBtn.addEventListener("click", () => {
      if (banner) banner.style.display = "none";
      if (currentScenarios && currentScenarios.length > 0) {
        selectScenario(currentScenarios[0]);
      }
    });
  }
}

// ── Sarvam Voice Agents (Samvaad) Playground ───────────────
function initSarvamTab() {
  const btnSpec = document.getElementById("btn-load-spec");
  const specViewer = document.getElementById("sarvam-spec-viewer");
  const outputElem = document.getElementById("sarvam-test-output");
  const statusElem = document.getElementById("sarvam-test-status");
  const labelElem = document.getElementById("sarvam-test-label");

  async function loadSpec() {
    try {
      const res = await fetch("/api/sarvam/agent-spec");
      if (res.ok) {
        const spec = await res.json();
        if (specViewer) specViewer.textContent = JSON.stringify(spec, null, 2);
      } else {
        if (specViewer) specViewer.textContent = "Agent spec not found on server.";
      }
    } catch (e) {
      if (specViewer) specViewer.textContent = "Error loading spec: " + e.message;
    }
  }

  if (btnSpec) btnSpec.addEventListener("click", loadSpec);

  // Hook test buttons
  const btnOnStart = document.getElementById("btn-test-onstart");
  if (btnOnStart) {
    btnOnStart.addEventListener("click", async () => {
      if (labelElem) labelElem.textContent = "Testing On-Start Hook (POST /webhook/on-start)...";
      if (statusElem) {
        statusElem.textContent = "Executing...";
        statusElem.className = "chip chip-sm";
      }
      try {
        const res = await fetch("/webhook/on-start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seller_id: "241241351", phone_number: "+919876543210" })
        });
        const data = await res.json();
        if (outputElem) outputElem.textContent = JSON.stringify(data, null, 2);
        if (statusElem) {
          statusElem.textContent = "200 OK";
          statusElem.className = "chip chip-sm chip-highlight";
        }
      } catch (err) {
        if (outputElem) outputElem.textContent = JSON.stringify({ error: err.message }, null, 2);
        if (statusElem) statusElem.textContent = "Error";
      }
    });
  }

  const btnLeads = document.getElementById("btn-test-leads");
  if (btnLeads) {
    btnLeads.addEventListener("click", async () => {
      if (labelElem) labelElem.textContent = "Testing Tool: Verified Buyer Leads (POST /api/tools/buyer_leads)...";
      if (statusElem) statusElem.textContent = "Executing...";
      try {
        const res = await fetch("/api/tools/buyer_leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ category: "Cotton Yarn", state_or_city: "Surat" })
        });
        const data = await res.json();
        if (outputElem) outputElem.textContent = JSON.stringify(data, null, 2);
        if (statusElem) {
          statusElem.textContent = "200 OK";
          statusElem.className = "chip chip-sm chip-highlight";
        }
      } catch (err) {
        if (outputElem) outputElem.textContent = JSON.stringify({ error: err.message }, null, 2);
      }
    });
  }

  const btnPricing = document.getElementById("btn-test-pricing");
  if (btnPricing) {
    btnPricing.addEventListener("click", async () => {
      if (labelElem) labelElem.textContent = "Testing Tool: Official Pricing (POST /api/tools/pricing)...";
      if (statusElem) statusElem.textContent = "Executing...";
      try {
        const res = await fetch("/api/tools/pricing", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ turnover: "0 - 40 L" })
        });
        const data = await res.json();
        if (outputElem) outputElem.textContent = JSON.stringify(data, null, 2);
        if (statusElem) {
          statusElem.textContent = "200 OK";
          statusElem.className = "chip chip-sm chip-highlight";
        }
      } catch (err) {
        if (outputElem) outputElem.textContent = JSON.stringify({ error: err.message }, null, 2);
      }
    });
  }

  const btnBooking = document.getElementById("btn-test-booking");
  if (btnBooking) {
    btnBooking.addEventListener("click", async () => {
      if (labelElem) labelElem.textContent = "Testing Tool: Book RM Slot (POST /api/tools/book_slot)...";
      if (statusElem) statusElem.textContent = "Executing...";
      try {
        const res = await fetch("/api/tools/book_slot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seller_id: "241241351", date: "Monday", time_slot: "11:00 AM", channel: "phone" })
        });
        const data = await res.json();
        if (outputElem) outputElem.textContent = JSON.stringify(data, null, 2);
        if (statusElem) {
          statusElem.textContent = "200 OK";
          statusElem.className = "chip chip-sm chip-highlight";
        }
      } catch (err) {
        if (outputElem) outputElem.textContent = JSON.stringify({ error: err.message }, null, 2);
      }
    });
  }

  const btnOnEnd = document.getElementById("btn-test-onend");
  if (btnOnEnd) {
    btnOnEnd.addEventListener("click", async () => {
      if (labelElem) labelElem.textContent = "Testing On-End Hook (POST /webhook/on-end)...";
      if (statusElem) statusElem.textContent = "Executing...";
      try {
        const res = await fetch("/webhook/on-end", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            seller_id: "241241351",
            call_disposition: "meeting_fixed",
            primary_objection: "none",
            duration_sec: 145.0,
            baseline_pace: 0.92,
            final_pace: 0.95
          })
        });
        const data = await res.json();
        if (outputElem) outputElem.textContent = JSON.stringify(data, null, 2);
        if (statusElem) {
          statusElem.textContent = "Memory Evolved!";
          statusElem.className = "chip chip-sm chip-highlight";
        }
      } catch (err) {
        if (outputElem) outputElem.textContent = JSON.stringify({ error: err.message }, null, 2);
      }
    });
  }

  // Auto-load spec on start
  loadSpec();
}


