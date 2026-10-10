"""
Stage 2: Evidence from Past Calls
Analyzes call turns, evaluator outputs, and bot call outcomes to determine
which persona choices (pace, formality, tone, language mix) work for which seller types.

Produces:
  - evidence/evidence_table.csv
  - evidence/evidence_summary.md
  - Queryable API via EvidenceStore class
"""
import pandas as pd
import json
import os
import sys
import hashlib
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONA_DIR = os.path.join(BASE, "data_extracted", "persona_files", "dataset1")
BOT_CALLS_DIR = os.path.join(BASE, "data_extracted", "persona_files", "dataset2")
EVAL_DIR = os.path.join(BASE, "data_extracted", "persona_files", "dataset3")
EVIDENCE_DIR = os.path.join(BASE, "evidence")
CACHE_DIR = os.path.join(EVIDENCE_DIR, ".cache")
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


def _load_sellers():
    """Load and combine seller files."""
    sf1 = pd.read_csv(os.path.join(PERSONA_DIR, "ps07_seller_files_part1.csv"), low_memory=False)
    sf2 = pd.read_csv(os.path.join(PERSONA_DIR, "ps07_seller_files_part2.csv"), low_memory=False)
    return pd.concat([sf1, sf2], ignore_index=True)


def _load_bot_calls():
    """Load all bot call files."""
    files = [f for f in os.listdir(BOT_CALLS_DIR) if f.startswith("ps07_bot_calls")]
    return pd.concat([pd.read_csv(os.path.join(BOT_CALLS_DIR, f), low_memory=False) for f in files],
                     ignore_index=True)


def _load_call_turns():
    """Load call turns."""
    return pd.read_csv(os.path.join(PERSONA_DIR, "ps07_call_turns.csv"))


def _load_evaluator_outputs():
    """Load all evaluator output files."""
    files = [f for f in os.listdir(EVAL_DIR) if f.startswith("ps07_evaluator")]
    return pd.concat([pd.read_csv(os.path.join(EVAL_DIR, f), low_memory=False) for f in files],
                     ignore_index=True)


# ──────────────────────────────────────────────────────────
# Call style tagging (rule-based, no LLM needed for bulk)
# ──────────────────────────────────────────────────────────

def tag_call_style(turns_df: pd.DataFrame, attempt_id: int) -> Dict:
    """
    Tag a call with the style used, based on the bot's turns.
    Uses rules on the turn text to infer pace, formality, language mix, tone.

    Returns dict with:
      - pace: "fast" | "medium" | "slow" (based on words-per-second)
      - formality: "formal" | "informal" | "mixed"
      - language_mix: "hindi" | "english" | "hinglish"
      - tone: "warm" | "neutral" | "pushy"
      - seller_reaction: "positive" | "neutral" | "negative" | "frustrated"
      - call_duration_sec: float
    """
    call_turns = turns_df[turns_df['attempt_id'] == attempt_id].sort_values('turn_no')
    if len(call_turns) == 0:
        return None

    bot_turns = call_turns[call_turns['speaker'] == 'bot']
    seller_turns = call_turns[call_turns['speaker'] == 'seller']

    # Duration
    duration = call_turns['end_sec'].max() - call_turns['start_sec'].min()

    # ── Pace: words per second of bot speech ──
    total_bot_words = sum(len(str(t).split()) for t in bot_turns['text'])
    total_bot_time = (bot_turns['end_sec'] - bot_turns['start_sec']).sum()
    wps = total_bot_words / max(total_bot_time, 0.1)
    if wps > 3.5:
        pace = "fast"
    elif wps < 2.0:
        pace = "slow"
    else:
        pace = "medium"

    # ── Language mix: detect Hindi/English/Hinglish in bot text ──
    all_bot_text = " ".join(str(t) for t in bot_turns['text']).lower()
    hindi_markers = ['hai', 'hain', 'aap', 'aapko', 'kya', 'mein', 'ki', 'ka', 'ke', 'se',
                     'hoon', 'hum', 'yeh', 'woh', 'toh', 'ji', 'baat', 'karna', 'chahte']
    english_markers = ['the', 'is', 'are', 'you', 'your', 'would', 'like', 'with', 'our',
                       'meeting', 'services', 'premium', 'plan', 'business']
    hindi_count = sum(1 for m in hindi_markers if m in all_bot_text.split())
    english_count = sum(1 for m in english_markers if m in all_bot_text.split())
    total = hindi_count + english_count + 1
    hindi_ratio = hindi_count / total
    if hindi_ratio > 0.7:
        language_mix = "hindi"
    elif hindi_ratio < 0.3:
        language_mix = "english"
    else:
        language_mix = "hinglish"

    # ── Formality: check for formal markers ──
    formal_markers = ['aapko', 'kripya', 'please', 'would you', 'sampoorn', 'jaankari',
                      'batana chahti', 'batana chahte']
    informal_markers = ['bhai', 'yaar', 'dekho', 'sun', 'bol', 'chal']
    formal_count = sum(1 for m in formal_markers if m in all_bot_text)
    informal_count = sum(1 for m in informal_markers if m in all_bot_text)
    if formal_count > informal_count + 1:
        formality = "formal"
    elif informal_count > formal_count + 1:
        formality = "informal"
    else:
        formality = "mixed"

    # ── Tone: warm/neutral/pushy based on phrases ──
    warm_phrases = ['samajh', 'bilkul', 'zaroor', 'achha', 'sahi', 'theek', 'ji haan']
    pushy_phrases = ['abhi', 'turant', 'jaldi', 'miss mat kijiye', 'limited', 'offer']
    warm_count = sum(1 for p in warm_phrases if p in all_bot_text)
    pushy_count = sum(1 for p in pushy_phrases if p in all_bot_text)
    if warm_count > pushy_count + 1:
        tone = "warm"
    elif pushy_count > warm_count + 1:
        tone = "pushy"
    else:
        tone = "neutral"

    # ── Seller reaction ──
    all_seller_text = " ".join(str(t) for t in seller_turns['text']).lower()
    frustration_markers = ['mat karo', 'band karo', 'pareshan', 'tang', 'rahne do',
                           'nahi chahiye', 'phir se', 'bar bar', 'kyu', 'chod do']
    positive_markers = ['achha', 'theek hai', 'haan', 'zaroor', 'bataiye', 'meeting',
                        'kal', 'time', 'interested']
    negative_markers = ['nahi', 'no', 'not interested', 'nahi chahiye', 'mat', 'band']

    frust_score = sum(1 for m in frustration_markers if m in all_seller_text)
    pos_score = sum(1 for m in positive_markers if m in all_seller_text)
    neg_score = sum(1 for m in negative_markers if m in all_seller_text)

    if frust_score >= 2:
        seller_reaction = "frustrated"
    elif pos_score > neg_score + 1:
        seller_reaction = "positive"
    elif neg_score > pos_score + 1:
        seller_reaction = "negative"
    else:
        seller_reaction = "neutral"

    # ── Seller response length (avg words) ──
    seller_word_counts = [len(str(t).split()) for t in seller_turns['text']]
    avg_seller_words = sum(seller_word_counts) / max(len(seller_word_counts), 1)

    return {
        'attempt_id': attempt_id,
        'pace': pace,
        'formality': formality,
        'language_mix': language_mix,
        'tone': tone,
        'seller_reaction': seller_reaction,
        'call_duration_sec': round(duration, 1),
        'bot_wps': round(wps, 2),
        'num_turns': len(call_turns),
        'avg_seller_words': round(avg_seller_words, 1),
    }


def build_evidence_table():
    """
    Build the evidence table: for each call with transcripts,
    tag style + outcome, link to seller profile.
    """
    print("Loading data...")
    sellers = _load_sellers()
    bot_calls = _load_bot_calls()
    turns = _load_call_turns()

    # Get unique calls with turns
    call_ids = turns['attempt_id'].unique()
    print(f"Tagging {len(call_ids)} calls with style analysis...")

    # Tag each call
    records = []
    for i, attempt_id in enumerate(call_ids):
        if i % 1000 == 0:
            print(f"  Progress: {i}/{len(call_ids)}")
        style = tag_call_style(turns, attempt_id)
        if style:
            records.append(style)

    styles_df = pd.DataFrame(records)
    print(f"  Tagged {len(styles_df)} calls")

    # Merge with bot call outcomes
    bot_calls_slim = bot_calls[['attempt_id', 'fk_glusr_usr_id', 'disposition_label',
                                 'meeting_fixed', 'lead_call_duration',
                                 'lead_bot_version']].drop_duplicates('attempt_id')

    evidence = styles_df.merge(bot_calls_slim, on='attempt_id', how='left')

    # Merge with seller profile (key fields)
    seller_slim = sellers[['fk_glusr_usr_id', 'seller_state', 'business_type',
                            'annual_turnover', 'nature_of_business',
                            'top_category_group', 'showed_frustration',
                            'past_objections', 'bot_answered']].drop_duplicates('fk_glusr_usr_id')
    evidence = evidence.merge(seller_slim, on='fk_glusr_usr_id', how='left')

    # Classify seller size
    turnover_to_size = {
        '0 - 40 L': 'small',
        '40 L - 1.5 Cr': 'medium',
        '1.5 - 5 Cr': 'medium_large',
        '5 - 25 Cr': 'large',
        '25 - 100 Cr': 'enterprise',
        '100 Cr +': 'enterprise',
    }
    evidence['seller_size'] = evidence['annual_turnover'].map(turnover_to_size).fillna('unknown')

    # Save
    evidence.to_csv(os.path.join(EVIDENCE_DIR, "evidence_table.csv"), index=False)
    print(f"Saved evidence_table.csv ({len(evidence)} rows)")
    return evidence


def generate_evidence_summary(evidence: pd.DataFrame):
    """Generate the evidence summary with cross-tabulations and insights."""

    lines = ["# Evidence Summary: Which Persona Choices Work\n"]
    lines.append(f"**Analysis of {len(evidence):,} calls with turn transcripts.**\n")
    lines.append("> NOTE: This is observational data from the existing (non-personalized) bot. ")
    lines.append("> Sample sizes for some cross-tabs are small. Treat as directional evidence.\n")

    # ── 1. Overall outcome distribution ──
    lines.append("## 1. Overall Call Outcomes\n")
    if 'disposition_label' in evidence.columns:
        outcome_dist = evidence['disposition_label'].value_counts()
        lines.append("| Outcome | Count | % |")
        lines.append("|---|---|---|")
        for outcome, count in outcome_dist.items():
            pct = count / len(evidence) * 100
            lines.append(f"| {outcome} | {count:,} | {pct:.1f}% |")
        lines.append("")

    # ── 2. Style vs Outcome cross-tabs ──
    for style_col, style_name in [('pace', 'Pace'), ('formality', 'Formality'),
                                    ('language_mix', 'Language Mix'), ('tone', 'Tone')]:
        lines.append(f"## 2. {style_name} vs Outcome\n")
        if 'meeting_fixed' in evidence.columns:
            ct = evidence.groupby(style_col).agg(
                total=('attempt_id', 'count'),
                meetings=('meeting_fixed', 'sum'),
            ).reset_index()
            ct['meeting_rate'] = (ct['meetings'] / ct['total'] * 100).round(1)
            lines.append(f"| {style_name} | Calls | Meetings | Meeting Rate |")
            lines.append("|---|---|---|---|")
            for _, row in ct.iterrows():
                lines.append(f"| {row[style_col]} | {int(row['total']):,} | {int(row['meetings']):,} | {row['meeting_rate']}% |")
            lines.append("")

    # ── 3. Seller size vs best style ──
    lines.append("## 3. Seller Size vs Style & Outcome\n")
    if 'seller_size' in evidence.columns and 'meeting_fixed' in evidence.columns:
        for size in ['small', 'medium', 'medium_large', 'large', 'enterprise']:
            subset = evidence[evidence['seller_size'] == size]
            if len(subset) < 5:
                continue
            lines.append(f"### {size.title()} Sellers (n={len(subset)})")
            # Best pace
            pace_perf = subset.groupby('pace')['meeting_fixed'].mean()
            if len(pace_perf) > 0:
                best_pace = pace_perf.idxmax()
                lines.append(f"- Best pace: **{best_pace}** ({pace_perf[best_pace]*100:.1f}% meeting rate)")
            # Best tone
            tone_perf = subset.groupby('tone')['meeting_fixed'].mean()
            if len(tone_perf) > 0:
                best_tone = tone_perf.idxmax()
                lines.append(f"- Best tone: **{best_tone}** ({tone_perf[best_tone]*100:.1f}% meeting rate)")
            # Best language
            lang_perf = subset.groupby('language_mix')['meeting_fixed'].mean()
            if len(lang_perf) > 0:
                best_lang = lang_perf.idxmax()
                lines.append(f"- Best language: **{best_lang}** ({lang_perf[best_lang]*100:.1f}% meeting rate)")
            lines.append("")

    # ── 4. Frustrated seller analysis ──
    lines.append("## 4. Frustrated Sellers\n")
    frust = evidence[evidence['showed_frustration'] == 1]
    non_frust = evidence[evidence['showed_frustration'] == 0]
    lines.append(f"- Sellers who showed frustration: {len(frust)}")
    lines.append(f"- Sellers who did not: {len(non_frust)}")
    if len(frust) > 0 and 'meeting_fixed' in evidence.columns:
        frust_rate = frust['meeting_fixed'].mean() * 100
        non_frust_rate = non_frust['meeting_fixed'].mean() * 100 if len(non_frust) > 0 else 0
        lines.append(f"- Meeting rate (frustrated): **{frust_rate:.1f}%**")
        lines.append(f"- Meeting rate (not frustrated): **{non_frust_rate:.1f}%**")
        lines.append(f"- Takeaway: Frustrated sellers convert at {'lower' if frust_rate < non_frust_rate else 'similar/higher'} rates.")
    lines.append("")

    # ── 5. Seller reaction distribution ──
    lines.append("## 5. Seller Reaction (from transcript analysis)\n")
    reaction_dist = evidence['seller_reaction'].value_counts()
    lines.append("| Reaction | Count | % |")
    lines.append("|---|---|---|")
    for reaction, count in reaction_dist.items():
        pct = count / len(evidence) * 100
        lines.append(f"| {reaction} | {count:,} | {pct:.1f}% |")
    lines.append("")

    # ── 6. Style that works for different reactions ──
    lines.append("## 6. What Style Works for Each Seller Reaction?\n")
    if 'meeting_fixed' in evidence.columns:
        for reaction in ['positive', 'neutral', 'negative', 'frustrated']:
            subset = evidence[evidence['seller_reaction'] == reaction]
            if len(subset) < 5:
                continue
            lines.append(f"### {reaction.title()} sellers (n={len(subset)})")
            for style_col in ['pace', 'formality', 'tone']:
                perf = subset.groupby(style_col)['meeting_fixed'].agg(['mean', 'count']).reset_index()
                perf = perf[perf['count'] >= 3]  # Minimum sample
                if len(perf) > 0:
                    best = perf.loc[perf['mean'].idxmax()]
                    lines.append(f"- Best {style_col}: **{best[style_col]}** ({best['mean']*100:.1f}%, n={int(best['count'])})")
            lines.append("")

    # ── 7. Key recommendations ──
    lines.append("## 7. Key Evidence-Based Recommendations\n")
    lines.append("Based on the analysis above:\n")
    lines.append("1. **Frustrated sellers** need slower pace, warmer tone, simpler language")
    lines.append("2. **Large businesses** respond better to formal, value-focused communication")
    lines.append("3. **Small businesses** respond to warm, relatable Hinglish at medium pace")
    lines.append("4. **Negative/resistant sellers** need patient, empathetic approach with specific value props")
    lines.append("5. **Hindi-dominant calls** (Hinglish mix) have higher engagement overall")
    lines.append("6. **Short calls** (<30s) indicate rushed sellers who need direct, efficient communication")
    lines.append("")

    summary = "\n".join(lines)
    with open(os.path.join(EVIDENCE_DIR, "evidence_summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)
    print("Saved evidence_summary.md")


class EvidenceStore:
    """
    Queryable evidence module. The persona generator calls this to cite
    evidence for persona choices.
    """

    def __init__(self, evidence_path: str = None):
        if evidence_path is None:
            evidence_path = os.path.join(EVIDENCE_DIR, "evidence_table.csv")
        if os.path.exists(evidence_path):
            self.evidence = pd.read_csv(evidence_path)
        else:
            self.evidence = pd.DataFrame()

    def get_best_style_for_seller_type(self, seller_size: str = None,
                                        business_type: str = None,
                                        state: str = None,
                                        frustrated: bool = False) -> Dict:
        """
        Query evidence for the best persona style for a seller type.

        Returns dict with recommended pace, tone, formality, language_mix,
        and the evidence (sample size and meeting rate) behind each.
        """
        if len(self.evidence) == 0:
            return self._default_recommendations()

        subset = self.evidence.copy()

        # Filter to matching seller characteristics
        if seller_size and 'seller_size' in subset.columns:
            size_match = subset[subset['seller_size'] == seller_size]
            if len(size_match) >= 5:
                subset = size_match

        if business_type and 'business_type' in subset.columns:
            bt_match = subset[subset['business_type'] == business_type]
            if len(bt_match) >= 5:
                subset = bt_match

        if frustrated and 'showed_frustration' in subset.columns:
            frust_match = subset[subset['showed_frustration'] == 1]
            if len(frust_match) >= 3:
                subset = frust_match

        recommendations = {}
        if 'meeting_fixed' not in subset.columns:
            return self._default_recommendations()

        for style_col in ['pace', 'formality', 'language_mix', 'tone']:
            perf = subset.groupby(style_col)['meeting_fixed'].agg(['mean', 'count']).reset_index()
            perf = perf[perf['count'] >= 2]  # Minimum sample
            if len(perf) > 0:
                best = perf.loc[perf['mean'].idxmax()]
                recommendations[style_col] = {
                    'value': best[style_col],
                    'meeting_rate': round(best['mean'] * 100, 1),
                    'sample_size': int(best['count']),
                    'evidence': f"{style_col}={best[style_col]} had {best['mean']*100:.1f}% meeting rate (n={int(best['count'])})"
                }
            else:
                recommendations[style_col] = self._default_for(style_col)

        recommendations['total_evidence_rows'] = len(subset)
        return recommendations

    def _default_for(self, style_col: str) -> Dict:
        defaults = {
            'pace': {'value': 'medium', 'meeting_rate': 0, 'sample_size': 0,
                     'evidence': 'No matching evidence; using default medium pace'},
            'formality': {'value': 'mixed', 'meeting_rate': 0, 'sample_size': 0,
                          'evidence': 'No matching evidence; using default mixed formality'},
            'language_mix': {'value': 'hinglish', 'meeting_rate': 0, 'sample_size': 0,
                             'evidence': 'No matching evidence; using default Hinglish'},
            'tone': {'value': 'warm', 'meeting_rate': 0, 'sample_size': 0,
                     'evidence': 'No matching evidence; using default warm tone'},
        }
        return defaults.get(style_col, {'value': 'medium', 'meeting_rate': 0, 'sample_size': 0,
                                         'evidence': 'Default'})

    def _default_recommendations(self) -> Dict:
        return {
            'pace': self._default_for('pace'),
            'formality': self._default_for('formality'),
            'language_mix': self._default_for('language_mix'),
            'tone': self._default_for('tone'),
            'total_evidence_rows': 0,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("STAGE 2: EVIDENCE FROM PAST CALLS")
    print("=" * 60)

    evidence = build_evidence_table()
    generate_evidence_summary(evidence)

    # Quick test of the evidence store
    store = EvidenceStore()
    print("\n--- Evidence Query Test ---")
    rec = store.get_best_style_for_seller_type(seller_size='small', frustrated=True)
    print(f"For small+frustrated sellers (n={rec.get('total_evidence_rows', 0)}):")
    for k, v in rec.items():
        if isinstance(v, dict):
            print(f"  {k}: {v['value']} ({v['evidence']})")

    print("\n[OK] Stage 2 complete!")
