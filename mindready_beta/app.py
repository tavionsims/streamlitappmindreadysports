import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_NAME = "MindReady Sports"
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
RESPONSES_CSV = DATA_DIR / "responses.csv"

# Likert scale options (matching screenshot style)
LIKERT_LABELS = [
    "None of the time",
    "A little of the time",
    "Some of the time",
    "Most of the time",
    "All of the time",
]

# Screenshot questions
ATHLETE_QUESTIONS = [
    "It was difficult to be around teammates",
    "I found it difficult to do what I needed to do",
    "I was less motivated",
    "I was irritable, angry or aggressive",
    "I could not stop worrying about injury or my performance",
    "I found training more stressful",
    "I found it hard to cope with selection pressures",
    "I worried about life after sport",
    "I needed alcohol or other substances to relax",
    "I took unusual risks off-field",
]

# ---------- Utilities ----------
def init_storage() -> None:
    """Create CSV if it doesn't exist, with updated columns for 10 athlete questions."""
    if not RESPONSES_CSV.exists():
        cols = ["timestamp", "athlete_id", "role"] + [f"q{i}" for i in range(1, 11)]
        df = pd.DataFrame(columns=cols)
        df.to_csv(RESPONSES_CSV, index=False)

def load_responses() -> pd.DataFrame:
    init_storage()
    try:
        return pd.read_csv(RESPONSES_CSV)
    except Exception:
        cols = ["timestamp", "athlete_id", "role"] + [f"q{i}" for i in range(1, 11)]
        return pd.DataFrame(columns=cols)

def append_response(athlete_id: str, role: str, answers: dict) -> None:
    init_storage()
    row = {"timestamp": datetime.now().isoformat(timespec="seconds"), "athlete_id": athlete_id.strip(), "role": role}

    # Ensure q1..q10 exist
    for i in range(1, 11):
        row[f"q{i}"] = answers.get(f"q{i}")

    df = load_responses()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESPONSES_CSV, index=False)

def pill(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div style="padding: 12px 14px; border-radius: 14px; background: rgba(255,255,255,0.06);
                    border: 1px solid rgba(255,255,255,0.12); margin: 10px 0;">
          <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">{title}</div>
          <div style="opacity: 0.9; line-height: 1.35;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_header(text: str) -> None:
    st.markdown(f"### {text}")

def _extract_num(athlete_id: str) -> int:
    """
    Extract numeric suffix from ATHLETE_###.
    Returns 0 if not found.
    """
    if not isinstance(athlete_id, str):
        return 0
    m = re.search(r"ATHLETE_(\d+)$", athlete_id.strip().upper())
    return int(m.group(1)) if m else 0

def get_next_athlete_id(existing_df: pd.DataFrame) -> str:
    """
    Compute next ATHLETE_### based on max in existing CSV.
    """
    if existing_df is None or existing_df.empty or "athlete_id" not in existing_df.columns:
        return "ATHLETE_001"

    nums = existing_df["athlete_id"].apply(_extract_num)
    max_num = int(nums.max()) if len(nums) else 0
    next_num = max_num + 1
    return f"ATHLETE_{next_num:03d}"

def question_label(i: int) -> str:
    return f"{i}. {ATHLETE_QUESTIONS[i-1]}"

# ---------- Page setup ----------
st.set_page_config(page_title=APP_NAME, page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.4rem; }
      div[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.08); }
      .small-muted { opacity: 0.75; font-size: 0.92rem; }
      .kpi { font-size: 1.4rem; font-weight: 800; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load data once
df = load_responses()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(f"## 🧠 {APP_NAME}")
    st.markdown('<div class="small-muted">Beta demo: 3 role-based views</div>', unsafe_allow_html=True)
    st.divider()

    role = st.radio("Select view", ["Athlete", "Coach", "Clinician"], index=0)

    st.divider()
    st.markdown("**Demo controls**")
    if st.button("Reset demo data (clears responses)", type="secondary"):
        if RESPONSES_CSV.exists():
            RESPONSES_CSV.unlink()
        # Reset session athlete id so it starts fresh
        st.session_state.pop("athlete_id", None)
        st.success("Cleared. Refresh or switch views.")
        st.stop()

# ---------- Header ----------
st.title(f"{APP_NAME} — {role} View")
st.caption("Class beta demo: quick role-based check-ins + simple insights. No diagnosis. Privacy-first by design.")

# ---------- Views ----------
if role == "Athlete":
    col1, col2 = st.columns([1.25, 1])

    with col1:
        pill(
            "Quick mental check-in (beta)",
            "Answer the questions below. This helps normalize mental readiness as part of training and recovery.",
        )

        # Auto-increment athlete id
        if "athlete_id" not in st.session_state:
            st.session_state["athlete_id"] = get_next_athlete_id(df)

        athlete_id = st.session_state["athlete_id"]
        st.text_input("Athlete ID (auto-generated)", value=athlete_id, disabled=True)

        section_header("Today’s check-in")
        st.write("Scale: None of the time (1) → All of the time (5)")

        answers = {}
        # 10 questions, each multiple choice (Likert)
        for i in range(1, 11):
            answers[f"q{i}"] = st.radio(
                question_label(i),
                LIKERT_LABELS,
                horizontal=True,
                key=f"ath_q{i}",
            )

        if st.button("Submit check-in", type="primary"):
            append_response(
                athlete_id=athlete_id,
                role="Athlete",
                answers=answers,
            )
            # Reload df and increment athlete id for the next submission
            df = load_responses()
            st.session_state["athlete_id"] = get_next_athlete_id(df)
            st.success(f"Submitted! Next Athlete ID ready: {st.session_state['athlete_id']}")

        st.markdown("---")
        section_header("Wellness tools (beta placeholders)")
        st.write("• 60-second breathing prompt")
        st.write("• Short reflection: “What’s one controllable thing I can do today?”")
        st.write("• Quick reset routine: hydrate, stretch, 3 deep breaths")

    with col2:
        pill("Recent submissions (demo)", "This is local demo history saved in data/responses.csv.")
        df = load_responses()
        if not df.empty:
            recent = df[df["role"] == "Athlete"].sort_values("timestamp", ascending=False).head(10)
            if recent.empty:
                st.info("No athlete submissions yet.")
            else:
                st.dataframe(recent, use_container_width=True, hide_index=True)
        else:
            st.info("Submit a check-in to see it here.")

elif role == "Coach":
    pill(
        "Team-level insights (anonymized)",
        "Coaches see aggregated patterns only. This supports prevention and culture—not surveillance.",
    )

    df = load_responses()
    if df.empty:
        st.info("No data yet. Go to Athlete view and submit a few check-ins.")
    else:
        athletes = df[df["role"] == "Athlete"].copy()
        if athletes.empty:
            st.info("No Athlete submissions yet.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown('<div class="small-muted">Total check-ins</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi">{len(athletes):,}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="small-muted">Unique athletes</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi">{athletes["athlete_id"].nunique():,}</div>', unsafe_allow_html=True)
            with c3:
                st.markdown('<div class="small-muted">Most recent check-in</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="kpi">{athletes["timestamp"].max()}</div>', unsafe_allow_html=True)

            st.markdown("---")
            section_header("Aggregated trends (counts)")

            q_pick = st.selectbox(
                "Choose a question to view team trend",
                options=[f"Q{i}: {ATHLETE_QUESTIONS[i-1]}" for i in range(1, 11)],
                index=0,
            )
            q_num = int(q_pick.split(":")[0].replace("Q", "").strip())
            col_name = f"q{q_num}"

            counts = athletes[col_name].value_counts(dropna=False).reindex(LIKERT_LABELS, fill_value=0).reset_index()
            counts.columns = ["Response", "Count"]
            st.dataframe(counts, use_container_width=True, hide_index=True)

            st.markdown("---")
            section_header("Coach action prompts (beta)")
            st.write("• If stress-related responses are trending high: add a short team reset routine post-practice.")
            st.write("• If motivation and coping responses drop: communicate expectations clearly and check workload.")
            st.write("• If worry and pressure responses rise: coordinate with clinicians on support resources.")

elif role == "Clinician":
    pill(
        "Clinician insights (individual, early flags)",
        "Clinicians can review individual check-ins to support earlier, more informed conversations. This is not diagnosis.",
    )

    df = load_responses()
    if df.empty:
        st.info("No data yet. Go to Athlete view and submit a few check-ins.")
    else:
        athletes = df[df["role"] == "Athlete"].copy()
        if athletes.empty:
            st.info("No Athlete submissions yet.")
        else:
            athlete_ids = sorted(athletes["athlete_id"].dropna().unique().tolist())
            selected = st.selectbox("Select an Athlete (demo)", athlete_ids, index=0)

            person = athletes[athletes["athlete_id"] == selected].sort_values("timestamp", ascending=False)
            st.dataframe(person.head(15), use_container_width=True, hide_index=True)

            st.markdown("---")
            section_header("Early flags (simple beta rules)")

            if person.empty:
                st.info("No entries for this athlete.")
            else:
                latest = person.iloc[0].to_dict()

                # Demo flags: "Most of the time" or "All of the time" on certain risk items
                high = {"Most of the time", "All of the time"}
                flags = []

                # Map a few key questions to flags (demo)
                # 5 worry about injury/performance
                if latest.get("q5") in high:
                    flags.append("High worry about injury/performance.")
                # 9 alcohol/substances to relax
                if latest.get("q9") in high:
                    flags.append("Reports needing alcohol/substances to relax.")
                # 10 unusual risks off-field
                if latest.get("q10") in high:
                    flags.append("Reports unusual risks off-field.")
                # 4 irritable/angry/aggressive
                if latest.get("q4") in high:
                    flags.append("High irritability/anger/aggression.")

                if flags:
                    st.warning("Flags detected:")
                    for f in flags:
                        st.write(f"• {f}")
                    st.write("")
                    st.write(
                        "Suggested next step (demo): during rehab, ask a quick open question like "
                        "“What’s feeling hardest right now, mentally or emotionally?”"
                    )
                else:
                    st.success("No high-risk flags on the latest check-in (demo rules).")

            st.markdown("---")
            section_header("Clinician check-in (beta)")
            st.write("For the demo, clinicians can record a quick note using 3 multiple-choice fields.")
            c_q1 = st.radio("1) Athlete engagement today", ["Engaged", "Neutral", "Withdrawn"], horizontal=True, key="clin_q1")
            c_q2 = st.radio("2) Readiness for progression", ["Ready", "Maybe", "Not ready"], horizontal=True, key="clin_q2")
            c_q3 = st.radio("3) Follow-up needed", ["No", "Yes - short", "Yes - urgent"], horizontal=True, key="clin_q3")

            if st.button("Save clinician entry", type="primary"):
                append_response(
                    athlete_id=selected,
                    role="Clinician",
                    answers={"q1": c_q1, "q2": c_q2, "q3": c_q3},
                )
                st.success("Saved clinician entry (local CSV).")