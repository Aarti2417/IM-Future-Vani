# Call Quality Matrix Definitions (from VANI image)

| Parameter | Definition | Fatal | Non Fatal |
|---|---|---|---|
| **Outcome Accuracy** | Buyer intent is buying or not | Always Fatal | NA |
| **Quantity Accuracy (Numeric)** | Qty Value is correctly captured or not | Subject to the Category Fatal if value effect | Minor difference which can be overlook (Difference is of 10-20) |
| **Quantity Unit Accuracy** | Qty Unit shared by buyer is correctly captured or not | Subject to the Category - fatal if impacting the BL | Similar value units |
| **Quantity Probing Error** | Qty probed when not defined - error / Qty not probed when defined / Nudge is not proper | Fatal if defined and not asked | Non fatal if not defined and asked |
| **Qty Missed Opportunity** | Qty Shared but missed to capture | Fatal | If Voice not clear then Non Fatal |
| **Spec1 Accuracy** | if X input captured as Y and have impact on Buy lead | Subject to the Category | Minor difference which can be overlook |
| **Spec2 Accuracy** | if X input captured as Y and have impact on Buy lead | Subject to the Category | Minor difference which can be overlook |
| **Spec Missed Opportunity** | Spec 1 or 2 shared by buyer is not captured / Not even added in BFD | Spec 1 or 2 shared by buyer is not captured / Not even added in BFD | If spec 3 is missed to captured not even in BFD |
| **Looping Behavior** | Probing more then 1+ 2 times for any Parameter like qty spec | If Buyer gets irritated - Leading to call disconnection or opportunity miss for Qty/Spec | No Impact on the call |
| **WER** | Words getting wrongly captured | Fatal - Impact on BL - Lead where word capture otherwise | Non-Fatal - word is wrongly captured but no major impact on BL |
| **Additional_details** | Buyer filled details captured | Fatal - Grossly wrong/irrelevant - BL impacting BFD is captured | Non-Fatal - Duplicate BFD captured / Very generic non impacting BFD captured - Pass - if generic BFD is there |
| **OnCall AstBuy Error** | IF seller present but not pitched | Fatal / Non-fatal - if not pitched but disposition wrongly shared | IF seller present but not pitched - Fatal | Non-fatal - if not pitched but disposition wrongly shared |
| **Product Change / No Product Accuracy** | product wrongly captured | Fatal if wrong product approved | |
| **Category ISQ's Error** | Contradicting or confusing ISQ | if ISQs are not contradicting | |
| **MCAT / Search errors** | Wrong MCAT selected | | |
| **Dead air** | Dead air more then 5 seconds for normal case / for Noise absorption consider 8 seconds | | |
| **Overall Call** | Pass or Fatal or non fatal basis above parameters | | |
| **Additional Observation** | Any other observation apart from above parameters like pronunciation | | |

## Key Takeaways for Persona Design
1. **Looping/Repetition** → if buyer/seller gets irritated, it's fatal. Our persona should detect looping early and adapt.
2. **Dead air** → 5+ seconds is flagged. Our persona should fill gaps proactively.
3. **WER (Word Error Rate)** → Wrong word capture. Our persona must speak clearly at appropriate pace.
4. **Outcome Accuracy** is always the most critical metric — getting the intent right.
5. **Probing** should be done correctly — not too much (looping) and not too little (missed opportunity).
