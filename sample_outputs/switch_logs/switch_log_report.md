# IndiaMART VANI - Mid-Call Persona Switch Log Report

## Overview
During live interaction, human vyaparis exhibit sudden situational shifts (counter rushes, skepticism, price hesitation). VANI continuously analyzes seller speech and acoustic cues to dynamically pivot persona parameters without dropping call rapport.

**Total Mid-Call Switches in Demo:** 3

### Switch #1: Turn 1 (at ~12s)

- **Seller Spoke:** *"Haanji kaun bol raha hai?"*
- **Signal Detected:** `confused` (Confidence: `0.82`)
- **Cues Matched:** `kaun bol raha`
- **Changes Made to Persona:**
  - **Tone:** `empathetic_problem_solver` -> **`reassuring_patient`**
  - **Pace:** `0.9x` -> **`0.86x`**
  - **Script Strategy:** `problem_solving` -> **`problem_solving`**
- **Why This Change Was Made:**
  > *"Confusion detected. Decelerated pace, removed technical jargon, and pivoted to patient explanatory tone."*

---

### Switch #2: Turn 2 (at ~36s)

- **Seller Spoke:** *"Bhai abhi counter pe bohot bheed hai gaahek khade hain, mere paas time nahi hai jaldi bolo."*
- **Signal Detected:** `rushed` (Confidence: `0.95`)
- **Cues Matched:** `time nahi, bheed, jaldi`
- **Changes Made to Persona:**
  - **Tone:** `reassuring_patient` -> **`direct_closing`**
  - **Pace:** `0.86x` -> **`0.98x`**
  - **Script Strategy:** `problem_solving` -> **`problem_solving`**
- **Why This Change Was Made:**
  > *"Seller indicated rush/scarcity of time. Accelerated delivery pace and condensed to direct value summary."*

---

### Switch #3: Turn 5 (at ~108s)

- **Seller Spoke:** *"Theek hai, Somwar subah 11 baje detail me call karwa do relationship manager se."*
- **Signal Detected:** `engaged` (Confidence: `0.82`)
- **Cues Matched:** `theek hai`
- **Changes Made to Persona:**
  - **Tone:** `direct_closing` -> **`consultative`**
  - **Pace:** `0.98x` -> **`0.98x`**
  - **Script Strategy:** `problem_solving` -> **`problem_solving`**
- **Why This Change Was Made:**
  > *"Seller showed active interest. Reinforced consultative partnership and framed clear next step."*

---

## Full Annotated Dialogue Transcript

**Turn 1 [Seller]:** "Haanji kaun bol raha hai?"

**Turn 1 [VANI Bot]** *(Tone: `reassuring_patient`, Pace: `0.86x`, Strategy: `problem_solving`)*:
> "नमस्ते जी, मैं इंडियामार्ट से बोल रहा हूँ। आपके UPVC sliding windows के लिए कुछ verified bulk buyers की inquiries आई हैं, क्या दो मिनट बात हो सकती है?"

**Turn 2 [Seller]:** "Bhai abhi counter pe bohot bheed hai gaahek khade hain, mere paas time nahi hai jaldi bolo."

**Turn 2 [VANI Bot]** *(Tone: `direct_closing`, Pace: `0.98x`, Strategy: `problem_solving`)*:
> "अरे बिल्कुल सर, मैं समझ गया, पहले आप ग्राहक अटेंड कर लीजिए। मैं कोई डिस्टर्ब नहीं करूँगा, बस WhatsApp पर 2 verified buyers की डिटेल्स भेज दूँ?"

**Turn 3 [Seller]:** "Dekho pehle bhi IndiaMART se phone aaya tha, sab fake leads aati hain bekaar me time kharab mat karo."

**Turn 3 [VANI Bot]** *(Tone: `direct_closing`, Pace: `0.98x`, Strategy: `problem_solving`)*:
> "सर आपकी नाराज़गी बिल्कुल जायज़ है। पर अब हमारा नया सिस्टम 90-second OTP verification के बाद ही बायर कनेक्ट करता है। आप खुद WhatsApp पे चेक कर लीजिए, कोई पैसा नहीं लग रहा।"

**Turn 4 [Seller]:** "Accha WhatsApp pe dekhunga. Vaise iska saal ka kharcha kitna hota hai?"

**Turn 4 [VANI Bot]** *(Tone: `direct_closing`, Pace: `0.98x`, Strategy: `problem_solving`)*:
> "आपके टर्नओवर के हिसाब से Mini Leader प्लान बेस्ट है—साल का ₹28,000 + GST, यानी सिर्फ ₹77 प्रतिदिन। 1 भी बल्क आर्डर से पूरा खर्चा निकल जाता है।"

**Turn 5 [Seller]:** "Theek hai, Somwar subah 11 baje detail me call karwa do relationship manager se."

**Turn 5 [VANI Bot]** *(Tone: `consultative`, Pace: `0.98x`, Strategy: `problem_solving`)*:
> "बहुत बढ़िया जी, सोमवार सुबह 11 बजे का स्लॉट पक्का कर दिया है। आपका दिन शुभ हो!"

