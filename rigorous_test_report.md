# IndiaMART VANI Voice Agent - Rigorous Test Execution Report

**Date:** 10/10/2026, 8:09:23 pm  
**Target Voice Agent:** `IM-Future-0c2c99ce-3384` (Sarvam Samvaad)  
**Pass Rate:** **90.0%** (9/10 Passed)  
**Average Turnaround Latency:** **2258 ms**  

## Individual Scenario Results

| Test ID | Scenario Name | Category | Status | Latency |
|---|---|---|---|---|
| TC-01 | Outbound Opening & Identity | Persona & Opening | ✅ PASS | 2209 ms |
| TC-02 | Live Category Buyer Demand (Grounded Tool) | Tool: Buyer Leads | ⚠️ ATTENTION | 2421 ms |
| TC-03 | Turnover-Based Pricing Calculation (Rate Card Tool) | Tool: Pricing | ✅ PASS | 3107 ms |
| TC-04 | Sunday / Holiday Shop Closure Protocol | Seller Empathy Guardrail | ✅ PASS | 2186 ms |
| TC-05 | Counter Rush / Busy Vyapari Pivot | Objection Handling | ✅ PASS | 1225 ms |
| TC-06 | Fake Leads Skepticism & ROI Defense | Objection Handling | ✅ PASS | 1392 ms |
| TC-07 | DNC / Hostile Rejection Protocol | Compliance & Safety | ✅ PASS | 1888 ms |
| TC-08 | RM Slot Booking (Appointment Tool) | Tool: Slot Booking | ✅ PASS | 3437 ms |
| TC-09 | Knowledge Base RAG Retrieval (Video KYC / Onboarding) | Knowledge Base RAG | ✅ PASS | 2188 ms |
| TC-10 | Multi-Turn End-to-End Vyapari Conversion Journey | End-to-End Dialogue | ✅ PASS | N/A |

## Detailed Dialogue Transcripts

### [TC-01] Outbound Opening & Identity
- **Seller:** "Hello, kaun bol raha hai aur kyu phone kiya?"
- **VANI:** "नमस्ते जी, मैं इंडियामार्ट से बोल रहा हूँ। दरअसल आपके बिज़नेस को बढ़ाने और आपको नए verified bulk buyers से जोड़ने के लिए मैंने call किया था। क्या अभी आपके पास थोड़ा time है?"
- **Assertions:**
  - [x] Mentions IndiaMART
  - [x] Mentions Buyer Leads / Inquiries / Business Growth
  - [x] Respectful Vyapari Tone (ji / namaste / aap)

### [TC-02] Live Category Buyer Demand (Grounded Tool)
- **Seller:** "UPVC sliding windows ke liye kitne buyers hain aapke paas abhi?"
- **VANI:** "देखिए, आपके UPVC Sliding Windows के लिए पिछले हफ्ते ही २८ वेरिफाइड बायर्स ने कोटेशन माँगा है। काफी अच्छी डिमांड चल रही है।"
- **Assertions:**
  - [x] Grounded Buyer Count (mentions specific numbers like 28 / verified)
  - [ ] Proactive Engagement Offer

### [TC-03] Turnover-Based Pricing Calculation (Rate Card Tool)
- **Seller:** "Mera turnover saal ka 25 lakh hai, IndiaMART package ka kya kharcha aayega?"
- **VANI:** "देखिए, आपके turnover के हिसाब से Mini Leader plan सही रहेगा। इसका खर्चा लगभग दो हज़ार से ढाई हज़ार रुपये महीना आता है, यानी साल का अट्ठाईस हज़ार रुपये plus GST। इसमें आपको direct verified buyers मिलते हैं। क्या मैं इसके बारे में और details बताऊँ?"
- **Assertions:**
  - [x] Quotes Mini Leader / baseline tier
  - [x] Mentions GST or Monthly breakdown or Quotas

### [TC-04] Sunday / Holiday Shop Closure Protocol
- **Seller:** "Bhai aaj Sunday hai, dukaan band hai meri, aaj koi baat nahi ho sakti."
- **VANI:** "अरे बिल्कुल सर, मैं समझ सकता हूँ, संडे को तो दुकान बंद रहती ही है। कोई बात नहीं, तो फिर सोमवार सुबह ११ बजे का टाइम सही रहेगा या दोपहर में बात करें?"
- **Assertions:**
  - [x] Respects Sunday / shop closure
  - [x] Proposes Monday / later callback politely
  - [x] Does NOT aggressively push sale immediately

### [TC-05] Counter Rush / Busy Vyapari Pivot
- **Seller:** "Abhi counter pe bohot bheed hai gaahek khade hain, mere paas bilkul time nahi hai."
- **VANI:** "अरे, मैं समझ गया सर, पहले customer attend कीजिये। मैं आपको आज शाम ७ बजे call करूँ दुकान बढ़ाने के बाद?"
- **Assertions:**
  - [x] Acknowledges rush / customer priority
  - [x] Offers low-friction alternative (WhatsApp or later call)

### [TC-06] Fake Leads Skepticism & ROI Defense
- **Seller:** "IndiaMART pe sab fake leads aati hain, pehle bhi paise doobe the mere."
- **VANI:** "अरे, मैं समझ सकता हूँ कि आपका अनुभव खराब रहा है। पर अब हमने सिस्टम बदल दिया है और सिर्फ OTP वेरिफाइड बायर ही भेजते हैं। आप बस एक बार WhatsApp पर फ्री में लीड्स चेक कर लीजिए, फिर तय कीजिएगा। क्या मैं भेज दूँ?"
- **Assertions:**
  - [x] Explains OTP-verification / genuine buyer filters
  - [x] Reassures with free WhatsApp test or RM guidance

### [TC-07] DNC / Hostile Rejection Protocol
- **Seller:** "Faltu phone mat karo, mera number hatao yahan se aur DNC me dalo!"
- **VANI:** "माफी चाहता हूँ, आपका नंबर हटा दिया गया है। आपका दिन शुभ हो।"
- **Assertions:**
  - [x] Immediate apology & respects DNC preference
  - [x] Does not argue or attempt further sales pitch

### [TC-08] RM Slot Booking (Appointment Tool)
- **Seller:** "Theek hai, Somwar dopeher 3 baje kisi relationship manager se call karwa dena."
- **VANI:** "समय देने के लिए बहुत शुक्रिया, आपका दिन शुभ हो। नमस्ते!"
- **Assertions:**
  - [x] Confirms appointment booking / closure
  - [x] Polite closing acknowledgement

### [TC-09] Knowledge Base RAG Retrieval (Video KYC / Onboarding)
- **Seller:** "IndiaMART pe seller verification aur Video KYC ke liye kya procedure hai?"
- **VANI:** "देखिए, इसका procedure बहुत simple है। आपको बस अपने IndiaMART app पर जाना है और वहां verification section में जाकर अपने documents upload करने होंगे, उसके बाद एक छोटा सा video call होगा। क्या मैं इसके बारे में और detail में बताऊं या आप app पर check करना चाहेंगे?"
- **Assertions:**
  - [x] Mentions verification / support / business onboarding

### [TC-10] Multi-Turn End-to-End Vyapari Conversion Journey
**Turn 1:**
- **Seller:** "Namaste ji, kis baare me call kiya hai aapne?"
- **VANI:** "नमस्ते जी, दरअसल मैं आपके बिज़नेस को बढ़ाने में help करना चाहता हूँ। हमारे पास आपके product के लिए कुछ verified bulk buyers की requests आई हैं, तो बस वही discuss करने के लिए call किया था।" (1977ms)

**Turn 2:**
- **Seller:** "Mera corrugated boxes aur packaging materials ka manufacturing plant hai. Isme demand hai?"
- **VANI:** "जी सर, अभी check किया तो पिछले हफ्ते ही आपके category में अट्ठाइस verified buyers ने quotation माँगा है। काफी अच्छी demand है, क्या आप इन orders को handle कर पाएंगे?" (2623ms)

**Turn 3:**
- **Seller:** "Aur iska paid package kitne ka aayega saal ka?"
- **VANI:** "देखिए, हमारे पास अलग-अलग plans हैं जो आपके टर्नओवर के हिसाब से होते हैं। अगर आप मुझे अपना साल का टर्नओवर बता दें, तो मैं आपको एकदम सही pricing बता पाऊँगा।" (2052ms)

**Turn 4:**
- **Seller:** "Mera turnover lagbhag 50 lakh hai saal ka."
- **VANI:** "अच्छा, मतलब आपका turnover पचास लाख रुपये के आसपास है। वैसे, आप किस product में डील करते हैं? ताकि मैं आपके लिए सही buyers check कर सकूँ।" (1192ms)

**Turn 5:**
- **Seller:** "Theek hai ji, kal subah 11 baje detail me baat karte hain, phone karwa dijiye."
- **VANI:** "ठीक है जी, कल सुबह ११ बजे बात होती है। आपका दिन शुभ हो!" (3711ms)


