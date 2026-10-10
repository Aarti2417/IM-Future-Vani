"""
Stage 1: Data Understanding & Sample Selection
Reads all persona files, builds data summary, and selects 8-10 diverse sample sellers.
"""
import pandas as pd
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PERSONA_DIR = os.path.join(BASE, "data_extracted", "persona_files", "dataset1")
BOT_CALLS_DIR = os.path.join(BASE, "data_extracted", "persona_files", "dataset2")
EVAL_DIR = os.path.join(BASE, "data_extracted", "persona_files", "dataset3")
CALL_TURNS_FILE = os.path.join(PERSONA_DIR, "ps07_call_turns.csv")
DOCS_DIR = os.path.join(BASE, "docs")
SAMPLE_DIR = os.path.join(BASE, "data_sample")
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

print("=" * 60)
print("STAGE 1: DATA UNDERSTANDING")
print("=" * 60)

# ── 1. Load seller files ──
print("\n[1/6] Loading seller files...")
sf1 = pd.read_csv(os.path.join(PERSONA_DIR, "ps07_seller_files_part1.csv"))
sf2 = pd.read_csv(os.path.join(PERSONA_DIR, "ps07_seller_files_part2.csv"))
sellers = pd.concat([sf1, sf2], ignore_index=True)
print(f"  Total sellers: {len(sellers):,}")

# ── 2. Load bot calls ──
print("\n[2/6] Loading bot calls...")
bot_files = [f for f in os.listdir(BOT_CALLS_DIR) if f.startswith("ps07_bot_calls")]
bot_calls = pd.concat([pd.read_csv(os.path.join(BOT_CALLS_DIR, f)) for f in bot_files], ignore_index=True)
print(f"  Total bot calls: {len(bot_calls):,}")

# ── 3. Load call turns ──
print("\n[3/6] Loading call turns...")
turns = pd.read_csv(CALL_TURNS_FILE)
print(f"  Total turns: {len(turns):,}")
print(f"  Unique calls with turns: {turns['attempt_id'].nunique():,}")

# ── 4. Load evaluator outputs (just counts) ──
print("\n[4/6] Loading evaluator outputs...")
eval_files = [f for f in os.listdir(EVAL_DIR) if f.startswith("ps07_evaluator")]
eval_counts = {}
total_evals = 0
for f in eval_files:
    df = pd.read_csv(os.path.join(EVAL_DIR, f))
    total_evals += len(df)
    for agent, count in df['eval_agent'].value_counts().items():
        eval_counts[agent] = eval_counts.get(agent, 0) + count
print(f"  Total evaluator rows: {total_evals:,}")
print(f"  Evaluator types: {json.dumps(eval_counts, indent=2)}")

# ── 5. Generate distribution stats ──
print("\n[5/6] Computing distributions...")

stats = {}
# Business type
stats['business_type'] = sellers['business_type'].value_counts().to_dict()
# Annual turnover
stats['annual_turnover'] = sellers['annual_turnover'].value_counts().to_dict()
# State (top 15)
stats['seller_state_top15'] = sellers['seller_state'].value_counts().head(15).to_dict()
# Nature of business
stats['nature_of_business'] = sellers['nature_of_business'].value_counts().to_dict()
# Top category group
stats['top_category_group_top10'] = sellers['top_category_group'].value_counts().head(10).to_dict()
# Bot call stats
stats['bot_attempts_stats'] = sellers['bot_attempts'].describe().to_dict()
stats['bot_answered_stats'] = sellers['bot_answered'].describe().to_dict()
# Frustration and engagement
stats['showed_frustration'] = sellers['showed_frustration'].value_counts(dropna=False).to_dict()
stats['asked_if_talking_to_bot'] = sellers['asked_if_talking_to_bot'].value_counts(dropna=False).to_dict()
stats['do_not_call_requested'] = sellers['do_not_call_requested'].value_counts(dropna=False).to_dict()
# Objection types
obj_counts = {}
for objs in sellers['past_objections'].dropna():
    for part in str(objs).split(', '):
        # Extract category name (remove count in parens)
        cat = part.rsplit(' (', 1)[0].strip()
        if cat:
            obj_counts[cat] = obj_counts.get(cat, 0) + 1
stats['objection_types'] = dict(sorted(obj_counts.items(), key=lambda x: -x[1])[:10])
# Disposition types
disp_counts = {}
for disps in sellers['past_dispositions_detailed'].dropna():
    for part in str(disps).split(', '):
        cat = part.rsplit(' (', 1)[0].strip()
        if cat:
            disp_counts[cat] = disp_counts.get(cat, 0) + 1
stats['disposition_types'] = dict(sorted(disp_counts.items(), key=lambda x: -x[1])[:10])
# Engagement stats
stats['eng_activity_30d'] = sellers['eng_activity_30d'].describe().to_dict()
stats['avg_answered_call_sec'] = sellers['avg_answered_call_sec'].describe().to_dict()
# Missing data
missing = {}
for col in sellers.columns:
    pct = sellers[col].isna().mean() * 100
    if pct > 0:
        missing[col] = round(pct, 1)
stats['missing_data_pct'] = missing

# Bot call disposition breakdown
stats['call_disposition_totals'] = {
    'meeting_fixed': int(sellers['calls_meeting_fixed'].sum()),
    'not_interested': int(sellers['calls_not_interested'].sum()),
    'general': int(sellers['calls_general'].sum()),
    'call_later': int(sellers['calls_call_later'].sum()),
}

# ── 6. Select 8-10 diverse sample sellers ──
print("\n[6/6] Selecting diverse sample sellers...")

# We need sellers with:
# - Turn transcripts (for evidence analysis)
# - Variety in: state/language, business_type, turnover, frustration, objections, engagement
turn_seller_ids = set(turns['fk_glusr_usr_id'].unique())
sellers_with_turns = sellers[sellers['fk_glusr_usr_id'].isin(turn_seller_ids)].copy()
print(f"  Sellers with turn transcripts: {len(sellers_with_turns)}")

# Enrich with turn count
turn_counts = turns.groupby('fk_glusr_usr_id').size().reset_index(name='turn_count')
sellers_with_turns = sellers_with_turns.merge(turn_counts, on='fk_glusr_usr_id', how='left')

# Also get call count from bot_calls
call_counts = bot_calls.groupby('fk_glusr_usr_id').size().reset_index(name='total_calls')
sellers_with_turns = sellers_with_turns.merge(call_counts, on='fk_glusr_usr_id', how='left')

# Strategy: pick sellers that are clearly distinct
samples = []

def add_sample(mask, reason, n=1):
    candidates = sellers_with_turns[mask]
    already = set(s['fk_glusr_usr_id'] for s in samples)
    candidates = candidates[~candidates['fk_glusr_usr_id'].isin(already)]
    if len(candidates) == 0:
        return
    # Pick the one with most turns for better evidence
    picked = candidates.nlargest(n, 'turn_count')
    for _, row in picked.iterrows():
        samples.append({
            'fk_glusr_usr_id': int(row['fk_glusr_usr_id']),
            'seller_state': row.get('seller_state', ''),
            'business_type': row.get('business_type', ''),
            'annual_turnover': row.get('annual_turnover', ''),
            'nature_of_business': row.get('nature_of_business', ''),
            'top_category_1': row.get('top_category_1', ''),
            'bot_answered': int(row.get('bot_answered', 0)),
            'showed_frustration': int(row.get('showed_frustration', 0)) if pd.notna(row.get('showed_frustration')) else 0,
            'past_objections': str(row.get('past_objections', '')),
            'past_dispositions_detailed': str(row.get('past_dispositions_detailed', '')),
            'avg_answered_call_sec': round(row.get('avg_answered_call_sec', 0), 1) if pd.notna(row.get('avg_answered_call_sec')) else 0,
            'turn_count': int(row.get('turn_count', 0)),
            'reason': reason
        })

# 1. Frustrated seller - showed frustration
add_sample(
    sellers_with_turns['showed_frustration'] == 1,
    "Showed frustration on past calls - tests empathy/de-escalation persona"
)

# 2. High-engagement, meeting-fixer
add_sample(
    (sellers_with_turns['calls_meeting_fixed'] >= 2) & (sellers_with_turns['bot_answered'] >= 3),
    "High engagement, multiple meetings fixed - tests warm/efficient persona"
)

# 3. Not interested, multiple objections
add_sample(
    (sellers_with_turns['calls_not_interested'] >= 2) & (sellers_with_turns['past_objections'].notna()),
    "Repeatedly not interested with objections - tests persuasive/patient persona"
)

# 4. Small business, low turnover
add_sample(
    (sellers_with_turns['annual_turnover'] == '0 - 40 L') & (sellers_with_turns['business_type'] == 'Proprietorship'),
    "Small proprietorship (0-40L) - tests budget-sensitive, simple language persona"
)

# 5. Large business, high turnover
add_sample(
    (sellers_with_turns['annual_turnover'].isin(['5 - 25 Cr', '25 - 100 Cr', '100 Cr +'])),
    "Large business (5Cr+) - tests formal, value-focused, executive persona"
)

# 6. Asked if talking to bot
add_sample(
    sellers_with_turns['asked_if_talking_to_bot'] == 1,
    "Asked if talking to bot - tests natural/human-like persona handling"
)

# 7. Short call duration (rushed seller)
short_mask = (sellers_with_turns['avg_answered_call_sec'] < 30) & (sellers_with_turns['avg_answered_call_sec'] > 0)
add_sample(short_mask, "Very short calls (<30s avg) - tests concise/direct persona for rushed sellers")

# 8. Long calls, engaged but undecided
long_mask = (sellers_with_turns['avg_answered_call_sec'] > 120) & (sellers_with_turns['calls_meeting_fixed'] == 0)
add_sample(long_mask, "Long calls but no meeting - tests patient/consultative persona")

# 9. Different region/state for language diversity - Tamil Nadu or South
south_mask = sellers_with_turns['seller_state'].isin(['Tamil Nadu', 'Karnataka', 'Kerala', 'Andhra Pradesh', 'Telangana'])
add_sample(south_mask, "South Indian seller - tests regional sensitivity and language adaptation")

# 10. Already in touch with executive
exec_mask = sellers_with_turns['already_in_touch_with_executive'] == 1
add_sample(exec_mask, "Already in touch with IM executive - tests coordination/referral persona")

print(f"  Selected {len(samples)} diverse sellers")
for s in samples:
    print(f"    {s['fk_glusr_usr_id']}: {s['reason'][:70]}...")

# Save samples
with open(os.path.join(SAMPLE_DIR, "sellers.json"), "w", encoding="utf-8") as f:
    json.dump(samples, f, indent=2, ensure_ascii=False)
print(f"\n  Saved to data_sample/sellers.json")

# ── Write data_summary.md ──
print("\nWriting docs/data_summary.md ...")

def fmt_dict(d, max_items=15):
    lines = []
    for i, (k, v) in enumerate(d.items()):
        if i >= max_items:
            lines.append(f"  ... and {len(d)-max_items} more")
            break
        lines.append(f"  - {k}: {v}")
    return "\n".join(lines)

summary = f"""# Data Summary

## Files Overview

### Persona Files (primary dataset for this problem)

| File | Description | Rows |
|---|---|---|
| `ps07_seller_files.csv` (2 parts) | Seller profiles with engagement & bot history | {len(sellers):,} |
| `ps07_bot_calls_YYYY-MM.csv` (4 files) | Answered bot calls with summaries & recordings | {len(bot_calls):,} |
| `ps07_evaluator_outputs_YYYY-MM.csv` (7 files) | LLM evaluator results per call | {total_evals:,} |
| `ps07_call_turns.csv` | Turn-by-turn transcripts | {len(turns):,} ({turns['attempt_id'].nunique():,} calls) |
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
{fmt_dict(stats['business_type'])}

### Annual Turnover
{fmt_dict(stats['annual_turnover'])}

### Top States
{fmt_dict(stats['seller_state_top15'])}

### Nature of Business
{fmt_dict(stats['nature_of_business'])}

### Top Category Groups
{fmt_dict(stats['top_category_group_top10'])}

### Call Dispositions (totals across all sellers)
{fmt_dict(stats['call_disposition_totals'])}

### Objection Types (from past_objections field)
{fmt_dict(stats['objection_types'])}

### Disposition Types (from past_dispositions_detailed)
{fmt_dict(stats['disposition_types'])}

### Bot Call Statistics
- Mean attempts per seller: {stats['bot_attempts_stats']['mean']:.1f}
- Mean answered per seller: {stats['bot_answered_stats']['mean']:.1f}
- Mean call duration: {stats['avg_answered_call_sec']['mean']:.1f}s

### Engagement Flags
- Showed frustration: {stats['showed_frustration']}
- Asked if talking to bot: {stats['asked_if_talking_to_bot']}
- Do not call requested: {stats['do_not_call_requested']}

### Missing Data (% null)
{fmt_dict(stats['missing_data_pct'])}

## Sample Sellers Selected
{len(samples)} sellers chosen for diversity. See `data_sample/sellers.json`.
"""

with open(os.path.join(DOCS_DIR, "data_summary.md"), "w", encoding="utf-8") as f:
    f.write(summary)

print("\n[OK] Stage 1 complete!")
print(f"  - docs/data_summary.md written")
print(f"  - data_sample/sellers.json: {len(samples)} sellers")
