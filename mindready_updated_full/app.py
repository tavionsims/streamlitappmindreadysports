import re
import base64
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_NAME = "MindReady Sports"

# -----------------------------
# Paths / storage
# -----------------------------
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RESPONSES_CSV = DATA_DIR / "responses.csv"

SOCIAL_POSTS_CSV = DATA_DIR / "social_posts.csv"
SOCIAL_COMMENTS_CSV = DATA_DIR / "social_comments.csv"
SOCIAL_LIKES_CSV = DATA_DIR / "social_likes.csv"
SOCIAL_DMS_CSV = DATA_DIR / "social_dms.csv"
SOCIAL_PROFILES_CSV = DATA_DIR / "social_profiles.csv"
SOCIAL_MEMBERSHIPS_CSV = DATA_DIR / "social_memberships.csv"

UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

AVATARS_DIR = DATA_DIR / "avatars"
AVATARS_DIR.mkdir(exist_ok=True)

# -----------------------------
# Athlete check-in settings
# -----------------------------
LIKERT_LABELS = [
    "None of the time",
    "A little of the time",
    "Some of the time",
    "Most of the time",
    "All of the time",
]

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

# -----------------------------
# Community (social) settings
# -----------------------------
GROUPS_META = [
    {
        "name": "NBA Players",
        "private": True,
        "desc": "Private group concept for NBA-level players to share rehab updates with peers.",
    },
    {
        "name": "College Athletes",
        "private": False,
        "desc": "Support group for student-athletes balancing rehab, school, and pressure.",
    },
    {
        "name": "Rehab Crew",
        "private": False,
        "desc": "Mixed group focused on accountability, routines, and mental reset strategies.",
    },
    {
        "name": "Public (All Athletes)",
        "private": False,
        "desc": "Public forum for any athlete to share motivation and progress.",
    },
]
SOCIAL_GROUPS = [g["name"] for g in GROUPS_META]

DEMO_USERS = ["Tavion", "Justin", "Ava", "Chris", "Maya", "Jordan", "Sam", "Riley"]

# -----------------------------
# Shared UI helpers
# -----------------------------
def pill(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div style="padding: 12px 14px; border-radius: 14px; background: rgba(255,255,255,0.06);
                    border: 1px solid rgba(255,255,255,0.12); margin: 10px 0;">
          <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">{title}</div>
          <div style="opacity: 0.9; line-height: 1.35; white-space: pre-line;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_header(text: str) -> None:
    st.markdown(f"### {text}")

# -----------------------------
# Check-in storage
# -----------------------------
def init_checkin_storage() -> None:
    if not RESPONSES_CSV.exists():
        cols = ["timestamp", "athlete_id", "role"] + [f"q{i}" for i in range(1, 11)]
        pd.DataFrame(columns=cols).to_csv(RESPONSES_CSV, index=False)

def load_responses() -> pd.DataFrame:
    init_checkin_storage()
    try:
        return pd.read_csv(RESPONSES_CSV)
    except Exception:
        cols = ["timestamp", "athlete_id", "role"] + [f"q{i}" for i in range(1, 11)]
        return pd.DataFrame(columns=cols)

def append_response(athlete_id: str, role: str, answers: dict) -> None:
    init_checkin_storage()
    row = {"timestamp": datetime.now().isoformat(timespec="seconds"), "athlete_id": athlete_id.strip(), "role": role}
    for i in range(1, 11):
        row[f"q{i}"] = answers.get(f"q{i}")
    df = load_responses()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(RESPONSES_CSV, index=False)

def _extract_num(athlete_id: str) -> int:
    if not isinstance(athlete_id, str):
        return 0
    m = re.search(r"ATHLETE_(\d+)$", athlete_id.strip().upper())
    return int(m.group(1)) if m else 0

def get_next_athlete_id(existing_df: pd.DataFrame) -> str:
    if existing_df is None or existing_df.empty or "athlete_id" not in existing_df.columns:
        return "ATHLETE_001"
    nums = existing_df["athlete_id"].apply(_extract_num)
    max_num = int(nums.max()) if len(nums) else 0
    return f"ATHLETE_{max_num + 1:03d}"

def question_label(i: int) -> str:
    return f"{i}. {ATHLETE_QUESTIONS[i-1]}"

# -----------------------------
# Social storage helpers
# -----------------------------
def init_social_storage() -> None:
    if not SOCIAL_POSTS_CSV.exists():
        pd.DataFrame(columns=["post_id", "timestamp", "group", "author", "content", "media_type", "media_ref"]).to_csv(
            SOCIAL_POSTS_CSV, index=False
        )
    if not SOCIAL_COMMENTS_CSV.exists():
        pd.DataFrame(columns=["comment_id", "post_id", "timestamp", "author", "comment"]).to_csv(
            SOCIAL_COMMENTS_CSV, index=False
        )
    if not SOCIAL_LIKES_CSV.exists():
        pd.DataFrame(columns=["post_id", "user"]).to_csv(SOCIAL_LIKES_CSV, index=False)
    if not SOCIAL_DMS_CSV.exists():
        pd.DataFrame(columns=["dm_id", "timestamp", "from_user", "to_user", "message"]).to_csv(
            SOCIAL_DMS_CSV, index=False
        )
    if not SOCIAL_PROFILES_CSV.exists():
        pd.DataFrame(columns=["user", "injury_type", "rehab_week", "team", "avatar_ref"]).to_csv(
            SOCIAL_PROFILES_CSV, index=False
        )
    if not SOCIAL_MEMBERSHIPS_CSV.exists():
        pd.DataFrame(columns=["user", "group", "status"]).to_csv(SOCIAL_MEMBERSHIPS_CSV, index=False)

def load_csv(path: Path) -> pd.DataFrame:
    init_social_storage()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)

def _next_id(df: pd.DataFrame, col: str, prefix: str) -> str:
    if df is None or df.empty or col not in df.columns:
        return f"{prefix}_001"
    nums = []
    for v in df[col].astype(str).tolist():
        m = re.search(rf"{prefix}_(\d+)$", v)
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) + 1) if nums else 1
    return f"{prefix}_{n:03d}"

def is_group_private(group_name: str) -> bool:
    for g in GROUPS_META:
        if g["name"] == group_name:
            return bool(g["private"])
    return False

def group_label(group_name: str) -> str:
    return ("🔒 " if is_group_private(group_name) else "🌍 ") + group_name

def ensure_demo_profiles_and_memberships() -> None:
    profiles = load_csv(SOCIAL_PROFILES_CSV)
    memberships = load_csv(SOCIAL_MEMBERSHIPS_CSV)

    if profiles.empty:
        demo = [
            {"user": "Tavion", "injury_type": "ACL", "rehab_week": 8, "team": "MindReady Demo", "avatar_ref": ""},
            {"user": "Justin", "injury_type": "Hamstring", "rehab_week": 3, "team": "OSU Club", "avatar_ref": ""},
            {"user": "Jordan", "injury_type": "Ankle", "rehab_week": 5, "team": "NBA Team", "avatar_ref": ""},
            {"user": "Chris", "injury_type": "Shoulder", "rehab_week": 4, "team": "NBA Team", "avatar_ref": ""},
            {"user": "Maya", "injury_type": "Knee", "rehab_week": 6, "team": "College Program", "avatar_ref": ""},
            {"user": "Ava", "injury_type": "Back", "rehab_week": 2, "team": "Public", "avatar_ref": ""},
            {"user": "Sam", "injury_type": "Wrist", "rehab_week": 7, "team": "Rehab Crew", "avatar_ref": ""},
            {"user": "Riley", "injury_type": "Concussion", "rehab_week": 1, "team": "Public", "avatar_ref": ""},
        ]
        save_csv(pd.DataFrame(demo), SOCIAL_PROFILES_CSV)

    if memberships.empty:
        demo_members = [
            {"user": "Jordan", "group": "NBA Players", "status": "approved"},
            {"user": "Chris", "group": "NBA Players", "status": "approved"},
            {"user": "Tavion", "group": "NBA Players", "status": "approved"},
        ]
        save_csv(pd.DataFrame(demo_members), SOCIAL_MEMBERSHIPS_CSV)

def can_user_view_group(user: str, group: str) -> bool:
    if not is_group_private(group):
        return True
    memberships = load_csv(SOCIAL_MEMBERSHIPS_CSV)
    if memberships.empty:
        return False
    m = memberships[
        (memberships["user"] == user) & (memberships["group"] == group) & (memberships["status"] == "approved")
    ]
    return not m.empty

def request_or_join_group(user: str, group: str) -> None:
    memberships = load_csv(SOCIAL_MEMBERSHIPS_CSV)
    if memberships.empty:
        memberships = pd.DataFrame(columns=["user", "group", "status"])
    existing = memberships[(memberships["user"] == user) & (memberships["group"] == group)]
    if not existing.empty:
        return
    status = "approved" if not is_group_private(group) else "requested"
    memberships = pd.concat(
        [memberships, pd.DataFrame([{"user": user, "group": group, "status": status}])],
        ignore_index=True,
    )
    save_csv(memberships, SOCIAL_MEMBERSHIPS_CSV)

def approve_request(user: str, group: str) -> None:
    memberships = load_csv(SOCIAL_MEMBERSHIPS_CSV)
    if memberships.empty:
        return
    mask = (memberships["user"] == user) & (memberships["group"] == group) & (memberships["status"] == "requested")
    memberships.loc[mask, "status"] = "approved"
    save_csv(memberships, SOCIAL_MEMBERSHIPS_CSV)

def seed_social_demo_data_if_empty() -> None:
    posts = load_csv(SOCIAL_POSTS_CSV)
    if not posts.empty:
        return

    now = datetime.now().replace(microsecond=0)

    # 10 posts total, ONLY 3 with media (2 photos + 1 video)
    demo_posts = [
        # media posts (3 total)
        ("NBA Players", "Jordan", "Day 12 post-op. Finally walked without crutches today. Small win.", "photo", "photo_1"),
        ("College Athletes", "Maya", "Rehab felt heavy today, but I still showed up. Proud of that.", "photo", "photo_2"),
        ("Rehab Crew", "Sam", "Quick progress clip today. Not perfect, but better than last week.", "video", "video_placeholder"),

        # text-only posts (7 total)
        ("Public (All Athletes)", "Ava", "Progress isn’t linear. Keep going even when it’s quiet.", "none", ""),
        ("NBA Players", "Chris", "Confidence is coming back. I’m trusting my body again.", "none", ""),
        ("College Athletes", "Justin", "Reminder: showing up counts even when the session feels rough.", "none", ""),
        ("Rehab Crew", "Riley", "Today I focused on breathing before rehab. It helped more than I expected.", "none", ""),
        ("Public (All Athletes)", "Tavion", "Small wins add up. Stack the days and protect your mindset.", "none", ""),
        ("College Athletes", "Maya", "Told myself: I don’t need to be perfect, I just need to be consistent.", "none", ""),
        ("Rehab Crew", "Sam", "One thing that helped today: I stopped comparing my timeline to anyone else.", "none", ""),
    ]

    rows = []
    for i, (g, a, c, mt, mr) in enumerate(demo_posts, start=1):
        rows.append(
            {
                "post_id": f"POST_{i:03d}",
                "timestamp": now.isoformat(),
                "group": g,
                "author": a,
                "content": c,
                "media_type": mt,
                "media_ref": mr,
            }
        )

    save_csv(pd.DataFrame(rows), SOCIAL_POSTS_CSV)

    # Light comments (optional but nice)
    demo_comments = [
        ("POST_001", "Tavion", "Love this. Keep stacking days."),
        ("POST_002", "Justin", "Showing up is the win."),
        ("POST_004", "Riley", "Needed this today."),
        ("POST_008", "Ava", "Facts."),
    ]
    c_rows = []
    for i, (pid, author, comment) in enumerate(demo_comments, start=1):
        c_rows.append(
            {
                "comment_id": f"CMT_{i:03d}",
                "post_id": pid,
                "timestamp": datetime.now().replace(microsecond=0).isoformat(),
                "author": author,
                "comment": comment,
            }
        )
    save_csv(pd.DataFrame(c_rows), SOCIAL_COMMENTS_CSV)

    # Likes (optional)
    demo_likes = [
        ("POST_001", "Tavion"),
        ("POST_001", "Justin"),
        ("POST_002", "Ava"),
        ("POST_003", "Jordan"),
        ("POST_004", "Chris"),
    ]
    save_csv(pd.DataFrame(demo_likes, columns=["post_id", "user"]), SOCIAL_LIKES_CSV)

    # DMs (optional)
    demo_dms = [
        ("Tavion", "Justin", "Community feed is looking clean now."),
        ("Maya", "Ava", "Your post helped me today. Thank you."),
    ]
    d_rows = []
    for i, (f, t, msg) in enumerate(demo_dms, start=1):
        d_rows.append(
            {
                "dm_id": f"DM_{i:03d}",
                "timestamp": datetime.now().replace(microsecond=0).isoformat(),
                "from_user": f,
                "to_user": t,
                "message": msg,
            }
        )
    save_csv(pd.DataFrame(d_rows), SOCIAL_DMS_CSV)
    
    demo_likes = [
        ("POST_001", "Tavion"),
        ("POST_001", "Justin"),
        ("POST_001", "Maya"),
        ("POST_002", "Ava"),
        ("POST_003", "Jordan"),
        ("POST_003", "Tavion"),
        ("POST_004", "Chris"),
        ("POST_004", "Riley"),
    ]
    save_csv(pd.DataFrame(demo_likes, columns=["post_id", "user"]), SOCIAL_LIKES_CSV)

    demo_dms = [
        ("Tavion", "Justin", "This community feature is gonna be fire for the demo."),
        ("Maya", "Ava", "Your post helped me today. Thank you."),
        ("Jordan", "Sam", "What’s your rehab routine look like lately?"),
    ]
    d_rows = []
    for i, (f, t, msg) in enumerate(demo_dms, start=1):
        d_rows.append({"dm_id": f"DM_{i:03d}", "timestamp": datetime.now().replace(microsecond=0).isoformat(), "from_user": f, "to_user": t, "message": msg})
    save_csv(pd.DataFrame(d_rows), SOCIAL_DMS_CSV)

def add_post(group: str, author: str, content: str, media_type: str, media_ref: str) -> None:
    posts = load_csv(SOCIAL_POSTS_CSV)
    post_id = _next_id(posts, "post_id", "POST")
    new_row = {"post_id": post_id, "timestamp": datetime.now().replace(microsecond=0).isoformat(), "group": group, "author": author, "content": content.strip(), "media_type": media_type, "media_ref": media_ref}
    posts = pd.concat([posts, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(posts, SOCIAL_POSTS_CSV)

def add_comment(post_id: str, author: str, comment: str) -> None:
    comments = load_csv(SOCIAL_COMMENTS_CSV)
    comment_id = _next_id(comments, "comment_id", "CMT")
    new_row = {"comment_id": comment_id, "post_id": post_id, "timestamp": datetime.now().replace(microsecond=0).isoformat(), "author": author, "comment": comment.strip()}
    comments = pd.concat([comments, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(comments, SOCIAL_COMMENTS_CSV)

def toggle_like(post_id: str, user: str) -> None:
    likes = load_csv(SOCIAL_LIKES_CSV)
    if likes.empty:
        likes = pd.DataFrame(columns=["post_id", "user"])
    mask = (likes["post_id"] == post_id) & (likes["user"] == user)
    if mask.any():
        likes = likes.loc[~mask].copy()
    else:
        likes = pd.concat([likes, pd.DataFrame([{"post_id": post_id, "user": user}])], ignore_index=True)
    save_csv(likes, SOCIAL_LIKES_CSV)

def send_dm(from_user: str, to_user: str, message: str) -> None:
    dms = load_csv(SOCIAL_DMS_CSV)
    dm_id = _next_id(dms, "dm_id", "DM")
    new_row = {"dm_id": dm_id, "timestamp": datetime.now().replace(microsecond=0).isoformat(), "from_user": from_user, "to_user": to_user, "message": message.strip()}
    dms = pd.concat([dms, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(dms, SOCIAL_DMS_CSV)

# -----------------------------
# Profiles + Avatars
# -----------------------------
def get_profile(user: str) -> dict:
    profiles = load_csv(SOCIAL_PROFILES_CSV)
    if profiles.empty:
        return {"user": user, "injury_type": "", "rehab_week": 1, "team": "", "avatar_ref": ""}
    row = profiles[profiles["user"] == user]
    if row.empty:
        return {"user": user, "injury_type": "", "rehab_week": 1, "team": "", "avatar_ref": ""}
    r = row.iloc[0].to_dict()
    try:
        r["rehab_week"] = int(r.get("rehab_week", 1))
    except Exception:
        r["rehab_week"] = 1
    r["avatar_ref"] = str(r.get("avatar_ref", "")).strip()
    return r

def upsert_profile(user: str, injury_type: str, rehab_week: int, team: str, avatar_ref: str) -> None:
    profiles = load_csv(SOCIAL_PROFILES_CSV)
    if profiles.empty:
        profiles = pd.DataFrame(columns=["user", "injury_type", "rehab_week", "team", "avatar_ref"])
    if (profiles["user"] == user).any():
        profiles.loc[profiles["user"] == user, "injury_type"] = injury_type
        profiles.loc[profiles["user"] == user, "rehab_week"] = rehab_week
        profiles.loc[profiles["user"] == user, "team"] = team
        profiles.loc[profiles["user"] == user, "avatar_ref"] = avatar_ref
    else:
        profiles = pd.concat([profiles, pd.DataFrame([{"user": user, "injury_type": injury_type, "rehab_week": rehab_week, "team": team, "avatar_ref": avatar_ref}])], ignore_index=True)
    save_csv(profiles, SOCIAL_PROFILES_CSV)

def initials(name: str) -> str:
    parts = [p for p in str(name).strip().split() if p]
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def avatar_placeholder_svg(name: str) -> str:
    h = hashlib.md5(str(name).encode("utf-8")).hexdigest()
    c1 = f"#{h[:6]}"
    c2 = f"#{h[6:12]}"
    ini = initials(name)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="{c1}" />
          <stop offset="100%" stop-color="{c2}" />
        </linearGradient>
      </defs>
      <circle cx="110" cy="110" r="108" fill="url(#g)"/>
      <circle cx="110" cy="95" r="38" fill="rgba(255,255,255,0.18)"/>
      <path d="M45 190c14-42 116-42 130 0" fill="rgba(255,255,255,0.18)"/>
      <text x="110" y="126" fill="white" font-family="Arial" font-size="54"
            text-anchor="middle" font-weight="800" opacity="0.9">{ini}</text>
    </svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

def get_avatar_path(user: str) -> str | None:
    prof = get_profile(user)
    ref = str(prof.get("avatar_ref", "")).strip()
    if ref.startswith("file:"):
        path = Path(ref.replace("file:", ""))
        if path.exists():
            return str(path)
    return None

# -----------------------------
# Fake post media
# -----------------------------
def svg_media_placeholder(kind: str, label: str) -> str:
    if kind == "photo":
        bg1, bg2, badge = "#1f2a44", "#2d1f44", "PHOTO"
    else:
        bg1, bg2, badge = "#223a2a", "#1f2a44", "VIDEO"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="{bg1}" />
          <stop offset="100%" stop-color="{bg2}" />
        </linearGradient>
      </defs>
      <rect width="900" height="360" rx="28" fill="url(#g)"/>
      <rect x="28" y="28" width="140" height="44" rx="18" fill="rgba(255,255,255,0.10)" stroke="rgba(255,255,255,0.16)"/>
      <text x="98" y="58" fill="white" font-family="Arial" font-size="16" text-anchor="middle" opacity="0.9">{badge}</text>
      <text x="450" y="280" fill="white" font-family="Arial" font-size="44" text-anchor="middle" font-weight="700" opacity="0.92">{label}</text>
      <text x="450" y="330" fill="white" font-family="Arial" font-size="20" text-anchor="middle" opacity="0.75">MindReady Sports demo</text>
      {"<circle cx='450' cy='260' r='62' fill='rgba(255,255,255,0.10)'/><polygon points='438,232 438,288 492,260' fill='rgba(255,255,255,0.75)'/>" if kind == "video" else ""}
    </svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

def render_post_media(media_type: str, media_ref: str, author: str) -> None:
    media_type = str(media_type or "none")
    media_ref = str(media_ref or "")
    if media_type == "photo":
        uri = svg_media_placeholder("photo", f"{author} • Progress")
        st.markdown(f"<img src='{uri}' style='width:100%; border-radius:16px; margin-top:10px;'/>", unsafe_allow_html=True)
    elif media_type == "video":
        if media_ref.startswith("file:"):
            path = Path(media_ref.replace("file:", ""))
            if path.exists():
                st.video(str(path))
                return
        uri = svg_media_placeholder("video", f"{author} • Rehab Clip")
        st.markdown(f"<img src='{uri}' style='width:100%; border-radius:16px; margin-top:10px;'/>", unsafe_allow_html=True)

# -----------------------------
# Page setup + styling
# -----------------------------
st.set_page_config(page_title=APP_NAME, page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.1rem; }
      div[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,0.08); }
      .small-muted { opacity: 0.75; font-size: 0.92rem; }
      .kpi { font-size: 1.4rem; font-weight: 800; }
      .post-card {
        padding: 12px 14px;
        border-radius: 16px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        margin: 6px 0;
      }
      .post-meta { opacity: 0.82; font-size: 0.9rem; margin-bottom: 6px; }
      .post-author { font-weight: 800; }
      .tag {
        display:inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.16);
        background: rgba(255,255,255,0.06);
        font-size: 0.82rem;
        margin-right: 6px;
        opacity: 0.92;
      }
      .feed-wrap { max-width: 780px; margin: 0 auto; }
      .mini { opacity:0.75; font-size:0.88rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Seed social data
init_social_storage()
ensure_demo_profiles_and_memberships()
seed_social_demo_data_if_empty()

df = load_responses()

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown(f"## 🧠 {APP_NAME}")
    st.markdown('<div class="small-muted">Beta demo: role-based views + community</div>', unsafe_allow_html=True)
    st.divider()

    view = st.radio("Select view", ["Athlete", "Coach", "Clinician", "Community"], index=0)

    if view == "Community":
        st.markdown("**Demo login**")
        demo_user = st.selectbox("Username", options=DEMO_USERS, index=0)
        st.session_state["demo_user"] = demo_user

    st.divider()
    st.markdown("**Demo controls**")
    if st.button("Reset check-in data (clears responses)", type="secondary"):
        if RESPONSES_CSV.exists():
            RESPONSES_CSV.unlink()
        st.session_state.pop("athlete_id", None)
        st.success("Cleared. Refresh or switch views.")
        st.stop()

    if st.button("Reset community demo (clears social posts)", type="secondary"):
        for f in [SOCIAL_POSTS_CSV, SOCIAL_COMMENTS_CSV, SOCIAL_LIKES_CSV, SOCIAL_DMS_CSV, SOCIAL_PROFILES_CSV, SOCIAL_MEMBERSHIPS_CSV]:
            if f.exists():
                f.unlink()
        init_social_storage()
        ensure_demo_profiles_and_memberships()
        seed_social_demo_data_if_empty()
        st.success("Community demo reset.")
        st.stop()

# -----------------------------
# Header
# -----------------------------
st.title(f"{APP_NAME} — {view} View")
st.caption("Class beta demo. Not diagnosis. Privacy-first design. Community section is a demo concept.")

# -----------------------------
# Athlete view
# -----------------------------
if view == "Athlete":
    col1, col2 = st.columns([1.25, 1])

    with col1:
        pill("Quick mental check-in (beta)", "Answer the questions below. This helps normalize mental readiness as part of training and recovery.")

        if "athlete_id" not in st.session_state:
            st.session_state["athlete_id"] = get_next_athlete_id(df)

        athlete_id = st.session_state["athlete_id"]
        st.text_input("Athlete ID (auto-generated)", value=athlete_id, disabled=True)

        section_header("Today’s check-in")
        st.write("Scale: None of the time (1) → All of the time (5)")

        answers = {}
        for i in range(1, 11):
            answers[f"q{i}"] = st.radio(question_label(i), LIKERT_LABELS, horizontal=True, key=f"ath_q{i}")

        if st.button("Submit check-in", type="primary"):
            append_response(athlete_id=athlete_id, role="Athlete", answers=answers)
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
        df2 = load_responses()
        if df2.empty:
            st.info("Submit a check-in to see it here.")
        else:
            recent = df2[df2["role"] == "Athlete"].sort_values("timestamp", ascending=False).head(10)
            st.dataframe(recent, use_container_width=True, hide_index=True)

# -----------------------------
# Coach view
# -----------------------------
elif view == "Coach":
    pill("Team-level insights (anonymized)", "Coaches see aggregated patterns only. This supports prevention and culture—not surveillance.")
    df2 = load_responses()
    if df2.empty:
        st.info("No data yet. Go to Athlete view and submit a few check-ins.")
    else:
        athletes = df2[df2["role"] == "Athlete"].copy()
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
            q_pick = st.selectbox("Choose a question to view team trend", options=[f"Q{i}: {ATHLETE_QUESTIONS[i-1]}" for i in range(1, 11)], index=0)
            q_num = int(q_pick.split(":")[0].replace("Q", "").strip())
            col_name = f"q{q_num}"

            counts = athletes[col_name].value_counts(dropna=False).reindex(LIKERT_LABELS, fill_value=0).reset_index()
            counts.columns = ["Response", "Count"]
            st.dataframe(counts, use_container_width=True, hide_index=True)

# -----------------------------
# Clinician view
# -----------------------------
elif view == "Clinician":
    pill("Clinician insights (individual, early flags)", "Clinicians can review individual check-ins to support earlier, more informed conversations. This is not diagnosis.")
    df2 = load_responses()
    if df2.empty:
        st.info("No data yet. Go to Athlete view and submit a few check-ins.")
    else:
        athletes = df2[df2["role"] == "Athlete"].copy()
        if athletes.empty:
            st.info("No Athlete submissions yet.")
        else:
            athlete_ids = sorted(athletes["athlete_id"].dropna().unique().tolist())
            selected = st.selectbox("Select an Athlete (demo)", athlete_ids, index=0)
            person = athletes[athletes["athlete_id"] == selected].sort_values("timestamp", ascending=False)
            st.dataframe(person.head(15), use_container_width=True, hide_index=True)

            st.markdown("---")
            section_header("Early flags (simple beta rules)")
            if not person.empty:
                latest = person.iloc[0].to_dict()
                high = {"Most of the time", "All of the time"}
                flags = []
                if latest.get("q5") in high:
                    flags.append("High worry about injury/performance.")
                if latest.get("q9") in high:
                    flags.append("Reports needing alcohol/substances to relax.")
                if latest.get("q10") in high:
                    flags.append("Reports unusual risks off-field.")
                if latest.get("q4") in high:
                    flags.append("High irritability/anger/aggression.")
                if flags:
                    st.warning("Flags detected:")
                    for f in flags:
                        st.write(f"• {f}")
                else:
                    st.success("No high-risk flags on the latest check-in (demo rules).")

            st.markdown("---")
            section_header("Clinician check-in (beta)")
            c_q1 = st.radio("1) Athlete engagement today", ["Engaged", "Neutral", "Withdrawn"], horizontal=True, key="clin_q1")
            c_q2 = st.radio("2) Readiness for progression", ["Ready", "Maybe", "Not ready"], horizontal=True, key="clin_q2")
            c_q3 = st.radio("3) Follow-up needed", ["No", "Yes - short", "Yes - urgent"], horizontal=True, key="clin_q3")
            if st.button("Save clinician entry", type="primary"):
                append_response(athlete_id=selected, role="Clinician", answers={"q1": c_q1, "q2": c_q2, "q3": c_q3})
                st.success("Saved clinician entry (local CSV).")

# -----------------------------
# Community view
# -----------------------------
elif view == "Community":
    user = st.session_state.get("demo_user", DEMO_USERS[0])
    prof = get_profile(user)

    pill("Community (demo)", "A social space for athletes to share rehab journeys, support each other, and build accountability. Private groups are locked unless approved.")
    posts = load_csv(SOCIAL_POSTS_CSV)
    comments = load_csv(SOCIAL_COMMENTS_CSV)
    likes = load_csv(SOCIAL_LIKES_CSV)
    dms = load_csv(SOCIAL_DMS_CSV)
    memberships = load_csv(SOCIAL_MEMBERSHIPS_CSV)

    tab_feed, tab_post, tab_groups, tab_profile, tab_dm = st.tabs(["Feed", "Create Post", "Groups", "Profile", "DMs"])

    with tab_feed:
        st.markdown("<div class='feed-wrap'>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns([1.7, 1, 1])
        with f1:
            group_filter = st.selectbox("Filter by group", ["All"] + [group_label(g) for g in SOCIAL_GROUPS], index=0)
        with f2:
            only_mine = st.checkbox("Only my posts", value=False)
        with f3:
            show_private = st.checkbox("Show private groups", value=True)

        group_filter_raw = "All" if group_filter == "All" else group_filter.replace("🔒 ", "").replace("🌍 ", "")

        view_df = posts.copy()
        if not show_private:
            view_df = view_df[~view_df["group"].apply(is_group_private)]
        else:
            allowed_mask = view_df["group"].apply(lambda g: (not is_group_private(g)) or can_user_view_group(user, g))
            view_df = view_df[allowed_mask]

        if group_filter_raw != "All":
            view_df = view_df[view_df["group"] == group_filter_raw]
        if only_mine:
            view_df = view_df[view_df["author"] == user]

        if view_df.empty:
            st.info("No posts to show yet. Create one in Create Post.")
        else:
            view_df = view_df.sort_values("timestamp", ascending=False)
            for _, row in view_df.iterrows():
                post_id = row["post_id"]
                post_likes = likes[likes["post_id"] == post_id] if not likes.empty else pd.DataFrame(columns=["post_id", "user"])
                like_count = len(post_likes)
                user_liked = ((post_likes["user"] == user).any()) if like_count else False

                author = str(row["author"])
                author_profile = get_profile(author)
                avatar_path = get_avatar_path(author)

                left, right = st.columns([0.10, 0.90], vertical_alignment="top")
                with left:
                    if avatar_path:
                        st.image(avatar_path, width=56)
                    else:
                        st.markdown(f"<img src='{avatar_placeholder_svg(author)}' style='width:56px; height:56px; border-radius:50%;'/>", unsafe_allow_html=True)

                with right:
                    st.markdown(
                        f"""<div class="post-card">
                          <div class="post-meta">
                            <span class="tag">{group_label(row["group"])}</span>
                            <span class="post-author">{author}</span>
                            <span class="mini"> • {author_profile.get("team","")} • Week {author_profile.get("rehab_week", 1)}</span>
                            <span class="mini"> • {row["timestamp"]}</span>
                          </div>
                          <div style="font-size: 1.04rem; line-height: 1.4;">{row["content"]}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    render_post_media(row.get("media_type", "none"), row.get("media_ref", ""), author)

                    a1, a2, a3 = st.columns([1, 1, 2.2])
                    with a1:
                        if st.button(("❤️ Liked" if user_liked else "🤍 Like") + f" ({like_count})", key=f"like_{post_id}"):
                            toggle_like(post_id, user)
                            st.rerun()
                    with a2:
                        if st.button("✉️ DM author", key=f"dm_author_{post_id}"):
                            st.session_state["dm_to_prefill"] = author
                            st.session_state["dm_msg_prefill"] = f"Hey {author}, your post helped me today."
                            st.toast("Go to DMs tab to send it.")
                    with a3:
                        with st.expander("Comments"):
                            post_comments = comments[comments["post_id"] == post_id].sort_values("timestamp") if not comments.empty else pd.DataFrame()
                            if post_comments.empty:
                                st.write("No comments yet.")
                            else:
                                for _, cr in post_comments.iterrows():
                                    st.write(f"**{cr['author']}**: {cr['comment']}")
                            new_comment = st.text_input("Add a comment", key=f"cmt_input_{post_id}")
                            if st.button("Post comment", key=f"cmt_btn_{post_id}"):
                                if new_comment.strip():
                                    add_comment(post_id, user, new_comment)
                                    st.rerun()
                                else:
                                    st.warning("Type a comment first.")

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_post:
        st.markdown("<div class='feed-wrap'>", unsafe_allow_html=True)
        section_header("Create a post")

        group_choice = st.selectbox("Post to group", [group_label(g) for g in SOCIAL_GROUPS], index=0)
        group = group_choice.replace("🔒 ", "").replace("🌍 ", "")

        if is_group_private(group) and not can_user_view_group(user, group):
            st.warning("This is a private group. Request access in the Groups tab before posting here.")
        else:
            media_type = st.selectbox("Attach media (demo)", ["none", "photo", "video"], index=1)
            media_ref = ""
            if media_type == "photo":
                st.info("Demo uses a fake photo placeholder (no upload needed).")
                media_ref = "photo_generated"
            if media_type == "video":
                vid = st.file_uploader("Upload a progress clip", type=["mp4", "mov", "m4v"])
                if vid is not None:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", vid.name)
                    out = UPLOADS_DIR / f"{user}_{ts}_{safe}"
                    out.write_bytes(vid.read())
                    media_ref = f"file:{str(out)}"
                    st.success("Video uploaded for demo.")
            content = st.text_area("What do you want to share?", placeholder="Rehab update, motivation, progress clip, mindset win…")
            if st.button("Publish", type="primary"):
                if not content.strip():
                    st.error("Please write something before publishing.")
                else:
                    if media_type == "none":
                        media_ref = ""
                    add_post(group, user, content, media_type, media_ref)
                    st.success("Posted! Check the Feed tab.")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_groups:
        st.markdown("<div class='feed-wrap'>", unsafe_allow_html=True)
        section_header("Groups")
        st.write("Public groups are open. Private groups require approval (demo: request + approve).")

        for g in GROUPS_META:
            gname = g["name"]
            private = g["private"]
            status = "Open"
            if private:
                mem = memberships[(memberships["user"] == user) & (memberships["group"] == gname)] if not memberships.empty else pd.DataFrame()
                status = "Not a member" if mem.empty else str(mem.iloc[0]["status"]).capitalize()

            pill(group_label(gname), f"{g['desc']}\nStatus: {status}")

            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                if not private:
                    if st.button(f"Join {gname}", key=f"join_{gname}"):
                        request_or_join_group(user, gname)
                        st.success("Joined.")
                        st.rerun()
                else:
                    if st.button("Request access", key=f"req_{gname}"):
                        request_or_join_group(user, gname)
                        st.success("Request submitted (demo).")
                        st.rerun()
            with c2:
                if private and user == "Tavion":
                    memberships = load_csv(SOCIAL_MEMBERSHIPS_CSV)
                    requested = memberships[(memberships["group"] == gname) & (memberships["status"] == "requested")] if not memberships.empty else pd.DataFrame()
                    if not requested.empty:
                        who = st.selectbox(f"Approve request for {gname}", requested["user"].tolist(), key=f"approve_pick_{gname}")
                        if st.button("Approve", key=f"approve_btn_{gname}"):
                            approve_request(who, gname)
                            st.success(f"Approved {who}.")
                            st.rerun()
            with c3:
                st.write("")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_profile:
        st.markdown("<div class='feed-wrap'>", unsafe_allow_html=True)
        section_header("My Profile (demo)")
        injury = st.text_input("Injury type", value=str(prof.get("injury_type", "")))
        week = st.slider("Week of rehab", 1, 52, int(prof.get("rehab_week", 1)))
        team = st.text_input("Team / Program", value=str(prof.get("team", "")))

        st.write("Profile photo (demo)")
        avatar_ref = str(prof.get("avatar_ref", "")).strip()
        current_avatar = get_avatar_path(user)
        if current_avatar:
            st.image(current_avatar, width=80)
        else:
            st.markdown(f"<img src='{avatar_placeholder_svg(user)}' style='width:80px; height:80px; border-radius:50%;'/>", unsafe_allow_html=True)

        photo = st.file_uploader("Upload a headshot", type=["png", "jpg", "jpeg"])
        if photo is not None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", photo.name)
            out = AVATARS_DIR / f"{user}_{ts}_{safe}"
            out.write_bytes(photo.read())
            avatar_ref = f"file:{str(out)}"
            st.success("Photo saved for demo.")

        if st.button("Save profile", type="primary"):
            upsert_profile(user, injury, week, team, avatar_ref)
            st.success("Saved.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_dm:
        st.markdown("<div class='feed-wrap'>", unsafe_allow_html=True)
        section_header("Direct messages (demo)")
        to_prefill = st.session_state.get("dm_to_prefill", "Justin")
        msg_prefill = st.session_state.get("dm_msg_prefill", "")

        recipients = [u for u in DEMO_USERS if u != user]
        default_idx = recipients.index(to_prefill) if to_prefill in recipients else 0

        to_user = st.selectbox("Send to", recipients, index=default_idx, key="dm_to")
        message = st.text_input("Message", value=msg_prefill, placeholder="Type a quick message...")

        if st.button("Send DM", type="primary"):
            if not message.strip():
                st.warning("Type a message first.")
            else:
                send_dm(user, to_user, message)
                st.success("Sent!")
                st.session_state["dm_msg_prefill"] = ""
                st.rerun()

        st.markdown("---")
        section_header("Inbox (demo)")
        dms = load_csv(SOCIAL_DMS_CSV)
        inbox = dms[(dms["to_user"] == user) | (dms["from_user"] == user)].sort_values("timestamp", ascending=False) if not dms.empty else pd.DataFrame()
        if inbox.empty:
            st.info("No messages yet.")
        else:
            for _, r in inbox.head(25).iterrows():
                direction = "➡️" if r["from_user"] == user else "⬅️"
                st.write(f"{direction} **{r['from_user']}** → **{r['to_user']}**: {r['message']}  \n_{r['timestamp']}_")

        st.markdown("</div>", unsafe_allow_html=True)
