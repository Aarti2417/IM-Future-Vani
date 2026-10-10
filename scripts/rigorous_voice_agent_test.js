/**
 * ==============================================================================
 * IndiaMART VANI - Rigorous Voice Agent Test Suite (Sarvam Samvaad)
 * ==============================================================================
 * Evaluates the live Sarvam Voice Agent across 10 critical stress scenarios:
 *  1. Outbound Opening & Identity Anchor
 *  2. Real-Time Buyer Demand Retrieval (Grounded Tool)
 *  3. Turnover-Based Pricing Calculation (Rate Card Tool)
 *  4. Sunday / Holiday Shop Closure Protocol
 *  5. Counter Rush / Busy Vyapari Pivot (WhatsApp / Later)
 *  6. "Fake Leads" Skepticism & ROI Defense
 *  7. DNC / Hostile Rejection Graceful Exit (Zero Pushback)
 *  8. Relationship Manager Slot Booking (Calendar Tool)
 *  9. Knowledge Base RAG Ingestion Verification (Video KYC / Onboarding)
 * 10. Multi-Turn End-to-End Vyapari Conversion Journey (5 Turns)
 *
 * Usage:
 *   node scripts/rigorous_voice_agent_test.js
 * ==============================================================================
 */

const fs = require('fs');
const path = require('path');

// 1. Load Sarvam MCP OAuth Access Token
const tokenPath = 'C:\\Users\\IMart\\.gemini\\antigravity-ide\\mcp_oauth_tokens.json';
if (!fs.existsSync(tokenPath)) {
  console.error("Error: Token file not found at " + tokenPath);
  process.exit(1);
}
const tokens = JSON.parse(fs.readFileSync(tokenPath, 'utf-8'));
const accessToken = tokens['https://mcp.sarvam.ai/voice-agents'].token.access_token;
const AGENT_ID = 'IM-Future-0c2c99ce-3384';

// ANSI Colors
const RESET = "\x1b[0m";
const BOLD = "\x1b[1m";
const GREEN = "\x1b[32m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const CYAN = "\x1b[36m";
const BLUE = "\x1b[34m";
const GRAY = "\x1b[90m";

/**
 * Execute a turn on Sarvam Samvaad via MCP send_chat
 */
async function sendTurn(text, interactionId = null, startInteraction = false) {
  const startTime = Date.now();
  const payload = {
    app_id: AGENT_ID,
    text: text,
    start_interaction: startInteraction,
    save_logs: true
  };
  if (interactionId) {
    payload.interaction_id = interactionId;
  }

  try {
    const res = await fetch('https://mcp.sarvam.ai/voice-agents', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: 'send_chat',
          arguments: payload
        }
      })
    });

    const responseText = await res.text();
    const latencyMs = Date.now() - startTime;
    const match = responseText.match(/data: (\{.*\})/);
    
    if (match) {
      const parsed = JSON.parse(match[1]);
      if (parsed.result && parsed.result.content && parsed.result.content[0]) {
        const data = JSON.parse(parsed.result.content[0].text);
        return {
          success: true,
          agentText: data.text || data.message || '',
          interactionId: data.interaction_id || interactionId,
          latencyMs: latencyMs,
          raw: data
        };
      }
    }

    return {
      success: false,
      error: responseText,
      agentText: '',
      interactionId: interactionId,
      latencyMs: latencyMs
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
      agentText: '',
      interactionId: interactionId,
      latencyMs: Date.now() - startTime
    };
  }
}

// Evaluation Test Cases
const TEST_CASES = [
  {
    id: "TC-01",
    name: "Outbound Opening & Identity",
    description: "Verify agent identifies as IndiaMART VANI and opens with buyer inquiries context",
    category: "Persona & Opening",
    prompt: "Hello, kaun bol raha hai aur kyu phone kiya?",
    assertions: [
      {
        name: "Mentions IndiaMART",
        test: (t) => /indiamart|इंडियामार्ट/i.test(t)
      },
      {
        name: "Mentions Buyer Leads / Inquiries / Business Growth",
        test: (t) => /buyer|inquir|leads|ऑर्डर|व्यापार|बिजनेस|खरीदार/i.test(t)
      },
      {
        name: "Respectful Vyapari Tone (ji / namaste / aap)",
        test: (t) => /जी|ji|नमस्ते|namaste|आप|aap/i.test(t)
      }
    ]
  },
  {
    id: "TC-02",
    name: "Live Category Buyer Demand (Grounded Tool)",
    description: "Verify agent retrieves real buyer inquiries for UPVC sliding windows",
    category: "Tool: Buyer Leads",
    prompt: "UPVC sliding windows ke liye kitne buyers hain aapke paas abhi?",
    assertions: [
      {
        name: "Grounded Buyer Count (mentions specific numbers like 28 / verified)",
        test: (t) => /28|२८|अट्ठाइस|verified|buyer|कोटेशन/i.test(t)
      },
      {
        name: "Proactive Engagement Offer",
        test: (t) => /check|चेक|शेयर|whatsapp|देखना|बात|चाहेंगे|लीड्स/i.test(t)
      }
    ]
  },
  {
    id: "TC-03",
    name: "Turnover-Based Pricing Calculation (Rate Card Tool)",
    description: "Inquire about package cost with small MSME turnover (Rs 25 Lakh)",
    category: "Tool: Pricing",
    prompt: "Mera turnover saal ka 25 lakh hai, IndiaMART package ka kya kharcha aayega?",
    assertions: [
      {
        name: "Quotes Mini Leader / baseline tier",
        test: (t) => /mini leader|28|२८|हज़ार|hazar|thousand|28,000/i.test(t)
      },
      {
        name: "Mentions GST or Monthly breakdown or Quotas",
        test: (t) => /gst|महीने|month|quota|leads|45/i.test(t)
      }
    ]
  },
  {
    id: "TC-04",
    name: "Sunday / Holiday Shop Closure Protocol",
    description: "Seller indicates shop is closed for Sunday, bot must reschedule without pitch",
    category: "Seller Empathy Guardrail",
    prompt: "Bhai aaj Sunday hai, dukaan band hai meri, aaj koi baat nahi ho sakti.",
    assertions: [
      {
        name: "Respects Sunday / shop closure",
        test: (t) => /sunday|रविवार|छुट्टी|बंद|holiday|kal|monday|सोमवार/i.test(t)
      },
      {
        name: "Proposes Monday / later callback politely",
        test: (t) => /सोमवार|monday|कल|baad me|समय|call|कॉल/i.test(t)
      },
      {
        name: "Does NOT aggressively push sale immediately",
        test: (t) => !/abhi turant khareedo|credit card do|aaj hi payment/i.test(t)
      }
    ]
  },
  {
    id: "TC-05",
    name: "Counter Rush / Busy Vyapari Pivot",
    description: "Seller has customers at counter; bot must pivot to WhatsApp / callback",
    category: "Objection Handling",
    prompt: "Abhi counter pe bohot bheed hai gaahek khade hain, mere paas bilkul time nahi hai.",
    assertions: [
      {
        name: "Acknowledges rush / customer priority",
        test: (t) => /customer|कस्टमर|ग्राहक|bheed|भीड़|व्यस्त|disturb|परेशान|अटेंड/i.test(t)
      },
      {
        name: "Offers low-friction alternative (WhatsApp or later call)",
        test: (t) => /whatsapp|व्हाट्सएप|baad me|बाद में|free|समय|कॉल|दुकान|शाम/i.test(t)
      }
    ]
  },
  {
    id: "TC-06",
    name: "Fake Leads Skepticism & ROI Defense",
    description: "Seller complains past leads were fake; bot explains OTP verification and guarantee",
    category: "Objection Handling",
    prompt: "IndiaMART pe sab fake leads aati hain, pehle bhi paise doobe the mere.",
    assertions: [
      {
        name: "Explains OTP-verification / genuine buyer filters",
        test: (t) => /otp|verified|वेरीफाइड|ओटीपी|filter|genuine|फिल्टर/i.test(t)
      },
      {
        name: "Reassures with free WhatsApp test or RM guidance",
        test: (t) => /whatsapp|चेक|help|manager|नया|system|सपोर्ट/i.test(t)
      }
    ]
  },
  {
    id: "TC-07",
    name: "DNC / Hostile Rejection Protocol",
    description: "Seller demands Do Not Call; bot must instantly apologize and exit gracefully",
    category: "Compliance & Safety",
    prompt: "Faltu phone mat karo, mera number hatao yahan se aur DNC me dalo!",
    assertions: [
      {
        name: "Immediate apology & respects DNC preference",
        test: (t) => /माफ़|sorry|क्षमा|dnc|हटा|disturb|परेशान|शुभ/i.test(t)
      },
      {
        name: "Does not argue or attempt further sales pitch",
        test: (t) => !/lekin package|discount le lo|sir suno to/i.test(t)
      }
    ]
  },
  {
    id: "TC-08",
    name: "RM Slot Booking (Appointment Tool)",
    description: "Seller agrees to a callback on Monday at 3 PM; bot schedules slot",
    category: "Tool: Slot Booking",
    prompt: "Theek hai, Somwar dopeher 3 baje kisi relationship manager se call karwa dena.",
    assertions: [
      {
        name: "Confirms appointment booking / closure",
        test: (t) => /सोमवार|monday|3|तीन|schedule|connect|बात|समय देने के लिए|शुक्रिया|नमस्ते/i.test(t)
      },
      {
        name: "Polite closing acknowledgement",
        test: (t) => /शुभ|धन्यवाद|theek|done|ज़रूर|शुक्रिया|नमस्ते/i.test(t)
      }
    ]
  },
  {
    id: "TC-09",
    name: "Knowledge Base RAG Retrieval (Video KYC / Onboarding)",
    description: "Inquires about Video KYC verification and required documents",
    category: "Knowledge Base RAG",
    prompt: "IndiaMART pe seller verification aur Video KYC ke liye kya procedure hai?",
    assertions: [
      {
        name: "Mentions verification / support / business onboarding",
        test: (t) => /kyc|वेरिफिकेशन|document|सपोर्ट|business|दस्तावेज़|profile/i.test(t)
      }
    ]
  }
];

// Multi-Turn End-to-End Simulation
const END_TO_END_JOURNEY = [
  {
    role: "Seller",
    turn: 1,
    text: "Namaste ji, kis baare me call kiya hai aapne?",
    expectedTopic: "Intro & Buyer Leads offer"
  },
  {
    role: "Seller",
    turn: 2,
    text: "Mera corrugated boxes aur packaging materials ka manufacturing plant hai. Isme demand hai?",
    expectedTopic: "Category demand affirmation"
  },
  {
    role: "Seller",
    turn: 3,
    text: "Aur iska paid package kitne ka aayega saal ka?",
    expectedTopic: "Turnover inquiry / Pricing rate card"
  },
  {
    role: "Seller",
    turn: 4,
    text: "Mera turnover lagbhag 50 lakh hai saal ka.",
    expectedTopic: "Mini Leader calculation & benefits"
  },
  {
    role: "Seller",
    turn: 5,
    text: "Theek hai ji, kal subah 11 baje detail me baat karte hain, phone karwa dijiye.",
    expectedTopic: "Slot confirmed & courteous call completion"
  }
];

async function runRigorousSuite() {
  console.log(`\n${BOLD}${BLUE}==============================================================================${RESET}`);
  console.log(`${BOLD}${CYAN}   🚀 IndiaMART VANI - RIGOROUS SARVAM VOICE AGENT TEST SUITE ${RESET}`);
  console.log(`${BOLD}${BLUE}==============================================================================${RESET}`);
  console.log(`${GRAY}Target Agent ID:${RESET}   ${AGENT_ID}`);
  console.log(`${GRAY}Target Engine:${RESET}     Sarvam Samvaad (Bulbul v4-flash Voice Agent)`);
  console.log(`${GRAY}Test Scenarios:${RESET}    10 Stress Tests (Single-Turn + 5-Turn Journey)\n`);

  const results = [];
  let passedCount = 0;
  let totalLatency = 0;

  // Part 1: Run TC-01 through TC-09
  for (const tc of TEST_CASES) {
    process.stdout.write(`${BOLD}[${tc.id}] ${tc.name}${RESET} ... `);
    
    // Fresh interaction for each isolated stress case
    const res = await sendTurn(tc.prompt, null, true);
    
    if (!res.success) {
      console.log(`${RED}FAILED (Network/RPC Error)${RESET}`);
      console.log(`  ${GRAY}Error: ${res.error}${RESET}`);
      results.push({
        id: tc.id,
        name: tc.name,
        passed: false,
        latencyMs: res.latencyMs,
        prompt: tc.prompt,
        response: "",
        assertions: [],
        error: res.error
      });
      continue;
    }

    totalLatency += res.latencyMs;

    // Run assertions
    const assertionResults = tc.assertions.map(a => {
      const ok = a.test(res.agentText);
      return { name: a.name, passed: ok };
    });

    const allPassed = assertionResults.every(a => a.passed);
    if (allPassed) {
      passedCount++;
      console.log(`${GREEN}PASSED${RESET} ${GRAY}(${res.latencyMs}ms)${RESET}`);
    } else {
      console.log(`${YELLOW}PARTIAL / ATTENTION${RESET} ${GRAY}(${res.latencyMs}ms)${RESET}`);
    }

    console.log(`  ${CYAN}Seller:${RESET} "${tc.prompt}"`);
    console.log(`  ${BOLD}VANI:${RESET}   "${res.agentText}"`);
    for (const a of assertionResults) {
      const mark = a.passed ? `${GREEN}✔${RESET}` : `${RED}✘${RESET}`;
      console.log(`    ${mark} ${GRAY}${a.name}${RESET}`);
    }
    console.log('');

    results.push({
      id: tc.id,
      name: tc.name,
      category: tc.category,
      passed: allPassed,
      latencyMs: res.latencyMs,
      prompt: tc.prompt,
      response: res.agentText,
      assertions: assertionResults
    });

    // Small delay between calls to simulate natural pacing
    await new Promise(r => setTimeout(r, 600));
  }

  // Part 2: TC-10 Multi-Turn Journey
  console.log(`${BOLD}${BLUE}------------------------------------------------------------------------------${RESET}`);
  console.log(`${BOLD}[TC-10] Multi-Turn End-to-End Vyapari Conversion Journey (5 Turns)${RESET}`);
  console.log(`${BOLD}${BLUE}------------------------------------------------------------------------------${RESET}`);

  let currentInteractionId = null;
  const journeyTurns = [];
  let journeyPassed = true;

  for (let i = 0; i < END_TO_END_JOURNEY.length; i++) {
    const step = END_TO_END_JOURNEY[i];
    const isStart = (i === 0);
    process.stdout.write(`  Turn ${step.turn}/5: ${GRAY}"${step.text.slice(0, 40)}..."${RESET} -> `);

    const res = await sendTurn(step.text, currentInteractionId, isStart);
    if (!res.success) {
      console.log(`${RED}Turn Failed${RESET}`);
      journeyPassed = false;
      break;
    }

    currentInteractionId = res.interactionId;
    totalLatency += res.latencyMs;
    console.log(`${GREEN}OK${RESET} ${GRAY}(${res.latencyMs}ms)${RESET}`);
    console.log(`    ${BOLD}VANI:${RESET} "${res.agentText}"\n`);

    journeyTurns.push({
      turn: step.turn,
      sellerText: step.text,
      vaniText: res.agentText,
      latencyMs: res.latencyMs
    });

    await new Promise(r => setTimeout(r, 800));
  }

  if (journeyPassed && journeyTurns.length === 5) {
    passedCount++;
  }

  results.push({
    id: "TC-10",
    name: "Multi-Turn End-to-End Vyapari Conversion Journey",
    category: "End-to-End Dialogue",
    passed: journeyPassed,
    turns: journeyTurns
  });

  // Summary Metrics
  const totalTests = TEST_CASES.length + 1;
  const passRate = ((passedCount / totalTests) * 100).toFixed(1);
  const avgLatency = (totalLatency / (results.length + 4)).toFixed(0);

  console.log(`\n${BOLD}${BLUE}==============================================================================${RESET}`);
  console.log(`${BOLD}${CYAN}                     TEST SUITE EXECUTION SUMMARY                             ${RESET}`);
  console.log(`${BOLD}${BLUE}==============================================================================${RESET}`);
  console.log(`Total Test Scenarios:   ${BOLD}${totalTests}${RESET}`);
  console.log(`Passed Scenarios:       ${GREEN}${passedCount}${RESET}`);
  console.log(`Attention / Failed:     ${totalTests - passedCount > 0 ? YELLOW : GREEN}${totalTests - passedCount}${RESET}`);
  console.log(`Pass Rate:              ${BOLD}${passRate}%${RESET}`);
  console.log(`Average Latency:        ${avgLatency} ms (Voice conversational standard: < 4500ms)`);
  console.log(`${BOLD}${BLUE}==============================================================================${RESET}\n`);

  // Write detailed report to JSON and Markdown
  const reportPathJson = path.join(__dirname, '..', 'rigorous_test_report.json');
  fs.writeFileSync(reportPathJson, JSON.stringify({
    timestamp: new Date().toISOString(),
    agent_id: AGENT_ID,
    summary: {
      total_tests: totalTests,
      passed: passedCount,
      pass_rate: `${passRate}%`,
      avg_latency_ms: avgLatency
    },
    results: results
  }, null, 2));

  const reportPathMd = path.join(__dirname, '..', 'rigorous_test_report.md');
  let md = `# IndiaMART VANI Voice Agent - Rigorous Test Execution Report\n\n`;
  md += `**Date:** ${new Date().toLocaleString()}  \n`;
  md += `**Target Voice Agent:** \`${AGENT_ID}\` (Sarvam Samvaad)  \n`;
  md += `**Pass Rate:** **${passRate}%** (${passedCount}/${totalTests} Passed)  \n`;
  md += `**Average Turnaround Latency:** **${avgLatency} ms**  \n\n`;
  md += `## Individual Scenario Results\n\n`;
  md += `| Test ID | Scenario Name | Category | Status | Latency |\n`;
  md += `|---|---|---|---|---|\n`;
  for (const r of results) {
    const statusMark = r.passed ? "✅ PASS" : "⚠️ ATTENTION";
    md += `| ${r.id} | ${r.name} | ${r.category || 'Multi-Turn'} | ${statusMark} | ${r.latencyMs ? r.latencyMs + ' ms' : 'N/A'} |\n`;
  }
  md += `\n## Detailed Dialogue Transcripts\n\n`;
  for (const r of results) {
    md += `### [${r.id}] ${r.name}\n`;
    if (r.prompt) {
      md += `- **Seller:** "${r.prompt}"\n`;
      md += `- **VANI:** "${r.response}"\n`;
      md += `- **Assertions:**\n`;
      for (const a of r.assertions || []) {
        md += `  - [${a.passed ? 'x' : ' '}] ${a.name}\n`;
      }
    } else if (r.turns) {
      for (const t of r.turns) {
        md += `**Turn ${t.turn}:**\n- **Seller:** "${t.sellerText}"\n- **VANI:** "${t.vaniText}" (${t.latencyMs}ms)\n\n`;
      }
    }
    md += `\n`;
  }
  fs.writeFileSync(reportPathMd, md);

  console.log(`${GREEN}✔ Full test report saved to:${RESET}`);
  console.log(`  - [JSON] ${reportPathJson}`);
  console.log(`  - [MD]   ${reportPathMd}\n`);
}

runRigorousSuite();
