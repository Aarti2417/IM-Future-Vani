# Data Summary

## Files Overview

### Persona Files (primary dataset for this problem)

| File | Description | Rows |
|---|---|---|
| `ps07_seller_files.csv` (2 parts) | Seller profiles with engagement & bot history | 149,363 |
| `ps07_bot_calls_YYYY-MM.csv` (4 files) | Answered bot calls with summaries & recordings | 269,455 |
| `ps07_evaluator_outputs_YYYY-MM.csv` (7 files) | LLM evaluator results per call | 278,332 |
| `ps07_call_turns.csv` | Turn-by-turn transcripts | 139,555 (12,788 calls) |
| `ps07_recording_sample_5000.csv` | Balanced audio sample | 5,000 |
| `ps07_executive_calls.csv` | Executive calls to sellers | 67,151 |

### Global Context (supplementary)
| File | Description | Rows |
|---|---|---|
| `gc_seller_profile.csv` | 5K seller profiles with engagement | 5,000 |
| `gc_bot_calls.csv` / `gc_bot_call_turns.csv` | Bot calls & turns | 9,657 / 4,920 |
| `gc_enquiries_received.csv` | Buyer enquiries | 33,006 |
| `gc_whatsapp_chatbot_conversations.csv` | WhatsApp bot chats | 83,280 |

### Other files
| File | Description | Use |
|---|---|---|
| `Call_Logs_Hackathon.csv` | External call logs | 1,000 rows, limited relevance |
| `call_recordings.zip` | Audio files | For Sarvam STT testing |
| Buyer-side files | Problem statement & prompt | Reference for prompt style |
| Seller Enrichment | KYC, products, categories | Enrichment if needed |

## Join Keys
- **`fk_glusr_usr_id`** (seller GLID): links across all files
- **`attempt_id`**: links a bot call across bot_calls, evaluator_outputs, and call_turns

## Value Distributions

### Business Type
  - Proprietorship: 120502
  - Partnership: 15470
  - Limited Company: 10896
  - Others: 87

### Annual Turnover
  - 0 - 40 L: 86874
  - 40 L - 1.5 Cr: 23382
  - 1.5 - 5 Cr: 13660
  - 5 - 25 Cr: 6845
  - 25 - 100 Cr: 1900
  - 100 - 500 Cr: 536
  - > 500 Cr: 161

### Top States
  - Gujarat: 27536
  - Uttar Pradesh: 24762
  - Maharashtra: 23737
  - Delhi: 22096
  - Rajasthan: 10499
  - Haryana: 9498
  - West Bengal: 6232
  - Punjab: 5284
  - Madhya Pradesh: 5242
  - Telangana: 3184
  - Tamil Nadu: 3079
  - Bihar: 1621
  - Odisha: 1565
  - Uttarakhand: 1037
  - Chhattisgarh: 998

### Nature of Business
  - Manufacturer: 33938
  - Trader - Retailer: 29251
  - Trader - Wholesaler/Distributor: 25283
  - Service Provider and Others: 25270
  - Retailer: 11972
  - Wholesaler/Distributor: 7788
  - Unknown: 102

### Top Category Groups
  - Building Construction Material, Equipment, Civil Engineering and Real Estate: 16481
  - Apparel, Clothing & Garments: 11507
  - Vegetables, Fruits, Grains, Dairy Products & Other FMCG and Grocery Items: 9048
  - Consumer Electronics &  Household Appliances: 7860
  - Electrical Equipment and Supplies: 5768
  - Packaging Material, Supplies & Machines: 5565
  - Housewares, Home Appliances, Household Decorations & Consumables: 5386
  - Cosmetics, Toiletries & Personal Care Products: 5163
  - Industrial & Engineering Products, Spares and Supplies: 4776
  - Industrial Plants, Machinery & Equipment: 4555

### Call Dispositions (totals across all sellers)
  - meeting_fixed: 31054
  - not_interested: 116364
  - general: 78365
  - call_later: 43672

### Objection Types (from past_objections field)
  - Call Quality / Technical Failures: 621
  - Seller Unavailability & Scheduling Constraints (1); Callback / Deferred Engagement (Neutral): 538
  - No Seller Response / Engagement Drop: 501
  - Explicit Disinterest / Refusal: 222
  - Call Handling / Executive Gaps (1); Call Quality / Technical Failures: 204
  - Seller Unavailability & Scheduling Constraints: 182
  - Callback / Deferred Engagement (Neutral): 144
  - Wrong Contact / Business Not Applicable: 99
  - Call Handling / Executive Gaps (1); No Seller Response / Engagement Drop: 64
  - Call Handling / Executive Gaps: 63

### Disposition Types (from past_dispositions_detailed)
  - call_dropped: 29337
  - meeting_fixed: 9609
  - not_interested: 6114
  - callback_requested: 4846
  - online_meeting_fixed: 1812
  - callback_requested (1); call_dropped: 1699
  - already_in_touch_with_im: 1398
  - wrong_number: 1199
  - call_dropped (2); callback_requested: 686
  - not_interested (1); call_dropped: 671

### Bot Call Statistics
- Mean attempts per seller: 3.6
- Mean answered per seller: 1.8
- Mean call duration: 40.6s

### Engagement Flags
- Showed frustration: {0.0: 79823, nan: 69401, 1.0: 139}
- Asked if talking to bot: {0.0: 79837, nan: 69401, 1.0: 125}
- Do not call requested: {0.0: 78784, nan: 69401, 1.0: 1178}

### Missing Data (% null)
  - seller_city: 0.0
  - seller_district: 0.1
  - seller_state: 0.0
  - seller_pincode: 0.0
  - seller_locality: 63.0
  - business_type: 1.6
  - annual_turnover: 10.7
  - nature_of_business: 10.6
  - nature_of_business_secondary: 1.7
  - gst_registration_year: 1.6
  - top_category_1: 3.1
  - top_category_2: 5.8
  - top_category_3: 11.6
  - top_parent_category: 20.7
  - top_category_group: 3.3
  ... and 35 more

## Sample Sellers Selected
10 sellers chosen for diversity. See `data_sample/sellers.json`.
