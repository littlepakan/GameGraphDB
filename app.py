from __future__ import annotations

import base64
import html
import io
import os
from datetime import date

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

import neo4j_service as db

st.set_page_config(
    page_title="GameGraph",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PLATFORMS = ["PC / Steam", "PC / Epic", "PlayStation 5", "Xbox Series X", "Nintendo Switch", "Mobile"]
C_FRIEND, C_GENRE, C_POP, C_RATE = "#ff6b8b", "#37d5c8", "#9b95ff", "#ffb347"

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@500;600;700&family=IBM+Plex+Sans+Thai:wght@400;500;600&display=swap');
      :root {
        --bg:#0e1124; --panel:#161a36; --line:#2a3066; --text:#eceefb; --muted:#9aa0c8;
        --amber:#ffb347; --teal:#37d5c8; --rose:#ff6b8b; --violet:#6c63ff;
      }
      .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1240px;}
      h1, h2, h3, .display {font-family: 'Kanit', sans-serif !important; letter-spacing: 0;}
      [data-testid="stMarkdownContainer"] p, label, .stTextInput input, .stSelectbox, .stTabs button {
        font-family: 'IBM Plex Sans Thai', sans-serif;
      }
      [data-testid="stSidebar"] {border-right: 1px solid var(--line);}
      .brand {font-family:'Kanit',sans-serif; font-size:1.7rem; font-weight:700; line-height:1.1;}
      .brand b {color: var(--amber); font-weight:700;}
      .brand-sub {color: var(--muted); font-size:.85rem; margin-top:.2rem;}

      .pagehead {border-bottom:1px solid var(--line); padding-bottom:.9rem; margin-bottom:1.3rem;}
      .pagehead h1 {font-size:2.1rem; margin:0; padding:0; line-height:1.15;}
      .pagehead p {color: var(--muted); margin:.3rem 0 0 0;}

      .tile {background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:1rem 1.2rem;}
      .tile .n {font-family:'Kanit',sans-serif; font-size:2.6rem; font-weight:700; line-height:1;}
      .tile .l {color:var(--muted); font-size:.9rem; margin-top:.35rem;}

      .rec {display:grid; grid-template-columns:56px 1fr; gap:1rem; background:var(--panel);
            border:1px solid var(--line); border-radius:14px; padding:1.1rem 1.3rem; margin-bottom:.9rem;}
      .rank {font-family:'Kanit',sans-serif; font-size:2.8rem; font-weight:700; color:var(--amber); line-height:1;}
      .rec-top {display:flex; justify-content:space-between; align-items:baseline; gap:1rem;}
      .rec h3 {margin:0; font-size:1.35rem;}
      .score {font-family:'Kanit',sans-serif; font-size:1.5rem; font-weight:600; white-space:nowrap;}
      .score small {color:var(--muted); font-weight:400; font-size:.8rem; margin-left:.25rem;}
      .meta {color:var(--muted); font-size:.88rem; margin:.15rem 0 .5rem 0;}
      .chip {display:inline-block; padding:.1rem .6rem; border-radius:6px; border:1px solid var(--line);
             font-size:.8rem; margin:.15rem .3rem .15rem 0; color:var(--muted);}
      .chip.hit {background:rgba(55,213,200,.14); border-color:var(--teal); color:var(--teal);}
      .bar {display:flex; height:10px; border-radius:5px; overflow:hidden; background:var(--line); margin:.75rem 0 .45rem;}
      .bar span {display:block; height:100%;}
      .legend {display:flex; flex-wrap:wrap; gap:.4rem 1.1rem; font-size:.8rem; color:var(--muted);}
      .legend i {display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:.35rem;}
      .why {margin:.65rem 0 0 0; font-size:.92rem;}

      .profile {background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:1.2rem 1.3rem;}
      .profile h3 {margin:0 0 .6rem 0; font-size:1.6rem;}
      .lvl {height:8px; border-radius:4px; background:var(--line); overflow:hidden; margin:.3rem 0 .9rem;}
      .lvl span {display:block; height:100%; background:var(--amber);}
      .kv {color:var(--muted); font-size:.85rem; margin-top:.5rem;}
      @media (max-width: 640px) {.rec {grid-template-columns:1fr;} .rec-top {flex-direction:column;}}
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
      [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {display:none !important;}
      [data-testid="stHeader"] {background: transparent;}
      .stApp {background:
        radial-gradient(900px 420px at 88% -90px, rgba(108,99,255,.30), transparent 70%),
        radial-gradient(700px 380px at 0% -70px, rgba(255,179,71,.15), transparent 70%), var(--bg);
        color: var(--text);}
      .block-container {padding-top: .9rem;}

      .topbar {display:flex; align-items:center; gap:.9rem; padding:.7rem 1.1rem; border:1px solid var(--line);
               border-radius:16px; background:linear-gradient(135deg, rgba(22,26,54,.95), rgba(34,38,88,.95));}
      .logo {width:46px; height:46px; border-radius:12px; object-fit:cover; display:grid; place-items:center;
             font-size:1.5rem; background:linear-gradient(135deg, var(--amber), var(--rose)); flex:none;}
      .status {margin-left:auto; font-size:.8rem; color:var(--teal); border:1px solid rgba(55,213,200,.4);
               background:rgba(55,213,200,.1); padding:.2rem .7rem; border-radius:999px; white-space:nowrap;}

      [data-testid="stRadio"] [role="radiogroup"] {gap:.3rem; flex-wrap:wrap; background:var(--panel);
               border:1px solid var(--line); border-radius:14px; padding:.35rem; margin:.7rem 0 1.4rem;}
      [data-testid="stRadio"] label {padding:.4rem .9rem; border-radius:10px; cursor:pointer; margin:0;}
      [data-testid="stRadio"] label > div:first-child {display:none;}
      [data-testid="stRadio"] label:hover {background:rgba(255,255,255,.06);}
      [data-testid="stRadio"] label:has(input:checked) {background:linear-gradient(135deg, var(--violet), #8a7bff);
               box-shadow:0 4px 14px rgba(108,99,255,.45);}
      [data-testid="stRadio"] label:has(input:checked) p {color:#fff; font-weight:600;}

      .pagehead {border-bottom:none; border-left:4px solid var(--amber); padding:.1rem 0 .1rem 1rem;}
      .tile {position:relative; overflow:hidden;}
      .tile::before {content:""; position:absolute; inset:0 0 auto 0; height:3px; background:var(--accent, var(--amber));}

      .gcard {background:var(--panel); border:1px solid var(--line); border-radius:16px; overflow:hidden; margin-bottom:1rem;}
      .gcard:hover {border-color:var(--violet);}
      .gbody {padding:.8rem 1rem 1rem;}
      .gbody h4 {margin:0; font-family:'Kanit',sans-serif; font-size:1.05rem;}
      .pcard {text-align:center; padding:1.2rem 1rem;}
      .pcard .avatar {margin:0 auto .6rem;}
      .cover {width:100%; aspect-ratio:16/9; object-fit:cover; display:block;}
      .cover.ph {display:grid; place-items:center; font-size:2.4rem;}
      .avatar {border-radius:50%; object-fit:cover; display:grid; place-items:center; color:#fff;
               font-family:'Kanit',sans-serif; font-weight:600; flex:none;}
      .rowuser {display:flex; align-items:center; gap:.7rem;}

      .rec {grid-template-columns:48px 168px 1fr;}
      .rec .cover {border-radius:10px;}
      @media (max-width: 760px) {.rec {grid-template-columns:1fr;} .status {display:none;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# ───────────────────────── helpers ─────────────────────────
esc = html.escape
AVATAR_SIZE, COVER_SIZE = (360, 360), (640, 360)
IMG_TYPES = ["png", "jpg", "jpeg", "webp"]


@st.cache_data(ttl=600, show_spinner=False)
def images(label: str) -> dict[str, str]:
    return db.get_images(label)


def process_image(file, size: tuple[int, int]) -> str:
    """Crop to the target ratio, shrink, and return a compact JPEG data-URI (~30-80 KB)."""
    img = ImageOps.exif_transpose(Image.open(file)).convert("RGB")
    img = ImageOps.fit(img, size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _grad(seed: str) -> str:
    h = sum(ord(c) for c in seed) * 37 % 360
    return f"linear-gradient(135deg,hsl({h} 65% 52%),hsl({(h + 55) % 360} 65% 38%))"


def avatar(name: str, img: str | None = None, size: int = 64) -> str:
    if img:
        return f'<img class="avatar" src="{img}" style="width:{size}px;height:{size}px">'
    ini = esc((name or "?").strip()[:1].upper())
    return (f'<div class="avatar" style="width:{size}px;height:{size}px;font-size:{size * .42:.0f}px;'
            f'background:{_grad(name or "?")}">{ini}</div>')


def cover(title: str, img: str | None = None) -> str:
    if img:
        return f'<img class="cover" src="{img}">'
    return f'<div class="cover ph" style="background:{_grad(title or "?")}">🎮</div>'


def photo_key(form_key: str) -> str:
    return f"{form_key}_img_{st.session_state.get('_imgver', 0)}"


def _bump_img() -> None:
    st.session_state["_imgver"] = st.session_state.get("_imgver", 0) + 1


def save_with_image(saver, label: str, item_id: str, photo, *args) -> None:
    saver(*args)
    if photo is not None:
        db.set_image(label, item_id, process_image(photo, AVATAR_SIZE if label == "User" else COVER_SIZE))
    _bump_img()


def _save_image(label: str, item_id: str, file) -> None:
    db.set_image(label, item_id, process_image(file, AVATAR_SIZE if label == "User" else COVER_SIZE))
    _bump_img()


def _remove_image(label: str, item_id: str) -> None:
    db.remove_image(label, item_id)
    _bump_img()


def image_panel(label: str, item_id: str, name: str) -> None:
    """Preview of the current image + upload / replace / delete controls."""
    cur = images(label).get(item_id)
    if label == "User":
        st.markdown(f'<div style="display:grid;place-items:center;margin-bottom:.5rem">{avatar(name, cur, 150)}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="gcard">{cover(name, cur)}</div>', unsafe_allow_html=True)
    up = st.file_uploader("เลือกรูปใหม่ (PNG / JPG / WEBP)", type=IMG_TYPES,
                          key=f"img_{label}_{item_id}_{st.session_state.get('_imgver', 0)}")
    if up is not None:
        st.image(up, caption="ตัวอย่างรูปที่เลือก (ระบบจะครอปกึ่งกลางให้อัตโนมัติ)")
    c1, c2 = st.columns(2)
    if c1.button("เปลี่ยนรูป" if cur else "บันทึกรูป", type="primary", disabled=up is None, key=f"imgsave_{label}_{item_id}"):
        do(_save_image, "บันทึกรูปแล้ว", label, item_id, up)
    if c2.button("🗑️ ลบรูป", disabled=not cur, key=f"imgdel_{label}_{item_id}"):
        do(_remove_image, "ลบรูปแล้ว", label, item_id)


def page_header(title: str, sub: str) -> None:
    st.markdown(
        f'<div class="pagehead"><h1>{esc(title)}</h1><p>{esc(sub)}</p></div>',
        unsafe_allow_html=True,
    )


def tile(col, number, label: str, color: str) -> None:
    col.markdown(
        f'<div class="tile" style="--accent:{color}"><div class="n" style="color:{color}">{number}</div>'
        f'<div class="l">{esc(label)}</div></div>',
        unsafe_allow_html=True,
    )


def chip(text: str, hit: bool = False) -> str:
    return f'<span class="chip{" hit" if hit else ""}">{esc(str(text))}</span>'


def do(fn, ok: str, *args, **kwargs) -> None:
    """Run a write action, show errors inline, and refresh the page on success."""
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        st.error(f"ดำเนินการไม่สำเร็จ: {exc}")
        return
    st.cache_data.clear()
    st.session_state["_flash"] = ok
    st.rerun()


def danger_zone(label: str, key: str, fn, *args, ok: str, warning: str) -> None:
    with st.expander(f"🗑️ ลบ{label}"):
        st.warning(warning)
        sure = st.checkbox("ฉันยืนยันว่าต้องการลบ", key=f"{key}_confirm")
        if st.button(f"ลบ{label}", key=f"{key}_btn", disabled=not sure):
            do(fn, ok, *args)


def require_connection() -> None:
    try:
        if not db.ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:  # noqa: BLE001
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("นำค่าด้านบนไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def pick_user(key: str, label: str = "เลือกผู้เล่น") -> str | None:
    users = db.get_users()
    if not users:
        st.info("ยังไม่มีผู้เล่น — ไปที่เมนู “ผู้เล่น” เพื่อเพิ่มผู้เล่นคนแรก หรือสร้างข้อมูลตัวอย่างที่เมนู “ตั้งค่าระบบ”")
        return None
    labels = {f"{u['user_id']} — {u['name']} ({u['platform']})": u["user_id"] for u in users}
    return labels[st.selectbox(label, list(labels), key=key)]


def pick_game(key: str, label: str = "เลือกเกม") -> str | None:
    games = db.search_games()
    if not games:
        st.info("ยังไม่มีเกมในระบบ — ไปที่เมนู “เกม” เพื่อเพิ่มเกม")
        return None
    labels = {f"{g['game_id']} — {g['title']}": g["game_id"] for g in games}
    return labels[st.selectbox(label, list(labels), key=key)]


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count"):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนเคยเล่น" + (f" ({friends})" if friends else ""))
    if row.get("genre_matches"):
        parts.append(f"ตรงกับแนวที่ชอบ {row['genre_matches']} แนว")
    if row.get("popularity"):
        parts.append(f"มีผู้เล่นแล้ว {row['popularity']} คน")
    if row.get("avg_rating"):
        parts.append(f"รีวิวเฉลี่ย {row['avg_rating']:.2f}/5")
    return " • ".join(parts) or "แนะนำจากความนิยมโดยรวม"


def breakdown(row: dict) -> tuple[str, str]:
    parts = [
        ("เพื่อนเล่น", (row.get("friend_count") or 0) * 3.0, C_FRIEND),
        ("แนวเกมตรงกัน", (row.get("genre_matches") or 0) * 2.0, C_GENRE),
        ("ความนิยม", (row.get("popularity") or 0) * 0.20, C_POP),
        ("คะแนนรีวิว", (row.get("avg_rating") or 0) * 0.50, C_RATE),
    ]
    total = sum(v for _, v, _ in parts) or 1
    bar = "".join(
        f'<span style="width:{v / total * 100:.1f}%;background:{c}" title="{n} +{v:.2f}"></span>'
        for n, v, c in parts if v > 0
    )
    legend = "".join(
        f'<span><i style="background:{c}"></i>{n} +{v:.2f}</span>' for n, v, c in parts if v > 0
    )
    return bar, legend


def to_date(value) -> date:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return date.today()


# ───────────────────────── reusable forms ─────────────────────────
def user_form(key: str, d: dict, submit_label: str, with_photo: bool = False):
    genres = db.list_genres()
    plats = PLATFORMS if (not d["platform"] or d["platform"] in PLATFORMS) else [d["platform"]] + PLATFORMS
    with st.form(key):
        name = st.text_input("ชื่อผู้เล่น", d["name"], key=f"{key}_name")
        c1, c2 = st.columns(2)
        platform = c1.selectbox(
            "แพลตฟอร์มหลัก", plats,
            index=plats.index(d["platform"]) if d["platform"] in plats else 0, key=f"{key}_plat",
        )
        level = c2.number_input("เลเวล", 1, 999, int(d["level"] or 1), key=f"{key}_lvl")
        interests = st.multiselect(
            "แนวเกมที่ชอบ", genres, default=[x for x in d["interests"] if x in genres], key=f"{key}_int"
        )
        if with_photo:
            st.file_uploader("รูปผู้เล่น (ไม่บังคับ)", type=IMG_TYPES, key=photo_key(key))
        submit = st.form_submit_button(submit_label, type="primary")
    return submit, name.strip(), platform, int(level), interests


def game_form(key: str, d: dict, submit_label: str, with_photo: bool = False):
    devs = {x["developer_id"]: x["name"] for x in db.list_developers()}
    genres = db.list_genres()
    with st.form(key):
        title = st.text_input("ชื่อเกม", d["title"], key=f"{key}_title")
        year = st.number_input("ปีที่วางจำหน่าย", 1980, 2100, int(d["year"] or date.today().year), key=f"{key}_year")
        dev_ids = st.multiselect(
            "ผู้พัฒนา", list(devs), default=[x for x in d["developer_ids"] if x in devs],
            format_func=lambda x: devs[x], key=f"{key}_dev",
        )
        gs = st.multiselect("แนวเกม", genres, default=[x for x in d["genres"] if x in genres], key=f"{key}_gen")
        if with_photo:
            st.file_uploader("รูปปกเกม (ไม่บังคับ)", type=IMG_TYPES, key=photo_key(key))
        submit = st.form_submit_button(submit_label, type="primary")
    return submit, title.strip(), int(year), dev_ids, gs


# ───────────────────────── boot ─────────────────────────
require_connection()
if "_flash" in st.session_state:
    st.toast(st.session_state.pop("_flash"), icon="✅")

MENU = {
    "📊  ภาพรวม": "dashboard",
    "✨  เกมแนะนำ": "recommend",
    "🎮  เกม": "games",
    "🧑‍🤝‍🧑  ผู้เล่น": "players",
    "📝  บันทึกการเล่น": "plays",
    "🏷️  ค่ายและแนวเกม": "catalog",
    "🕸️  กราฟความสัมพันธ์": "graph",
    "⚙️  ตั้งค่าระบบ": "setup",
}

logo = '<div class="logo">🎮</div>'
if os.path.exists("kairung99.jpg"):
    with open("kairung99.jpg", "rb") as fh:
        logo = f'<img class="logo" src="data:image/jpeg;base64,{base64.b64encode(fh.read()).decode()}">'
st.markdown(
    f'<div class="topbar">{logo}<div><div class="brand">Game<b>Graph</b></div>'
    '<div class="brand-sub">ระบบแนะนำเกมด้วย Neo4j</div></div>'
    '<span class="status">● เชื่อมต่อ Neo4j แล้ว</span></div>',
    unsafe_allow_html=True,
)
page = MENU[
    st.segmented_control(
        "เมนู", list(MENU), default=list(MENU)[0], label_visibility="collapsed"
    )
]


# ───────────────────────── Dashboard ─────────────────────────
if page == "dashboard":
    page_header("ภาพรวมระบบ", "สถิติของผู้เล่น เกม และความสัมพันธ์ทั้งหมดในกราฟ")
    m = db.get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    tile(c1, m.get("users", 0), "ผู้เล่น", C_RATE)
    tile(c2, m.get("games", 0), "เกม", C_GENRE)
    tile(c3, m.get("plays", 0), "ประวัติการเล่น", C_POP)
    tile(c4, m.get("friendships", 0), "ความเป็นเพื่อน", C_FRIEND)
    st.write("")

    left, right = st.columns(2)
    with left:
        st.markdown("### เกมที่มีผู้เล่นมากที่สุด")
        tg = db.top_games(8)
        if tg:
            st.bar_chart(pd.DataFrame(tg).set_index("title")["players"], color=C_GENRE)
        else:
            st.info("ยังไม่มีข้อมูลเกม")
    with right:
        st.markdown("### แนวเกมที่ผู้เล่นชอบ")
        gs = db.genre_stats()
        if gs:
            st.bar_chart(pd.DataFrame(gs).set_index("name")["fans"], color=C_RATE)
        else:
            st.info("ยังไม่มีแนวเกม")

    st.markdown("### โปรไฟล์ผู้เล่น")
    user_id = pick_user("dash_user")
    profile = db.get_profile(user_id) if user_id else None
    if profile:
        a, b = st.columns([1, 2])
        with a:
            lvl = min(100, int(profile["level"] or 0))
            st.markdown(
                f"""<div class="profile">
                <div class="rowuser" style="margin-bottom:.7rem">{avatar(profile['name'], images("User").get(profile['user_id']), 72)}
                <div><h3 style="margin:0">{esc(profile['name'] or '')}</h3>
                <div class="meta" style="margin:0">{esc(profile['user_id'])} · {esc(profile['platform'] or '-')}</div></div></div>
                <div class="kv">เลเวล {profile['level']}</div>
                <div class="lvl"><span style="width:{lvl}%"></span></div>
                <div class="kv">แนวเกมที่ชอบ</div>
                {''.join(chip(g) for g in profile['interests']) or '<span class="meta">ยังไม่ได้ระบุ</span>'}
                </div>""",
                unsafe_allow_html=True,
            )
        with b:
            if profile["played"]:
                df = pd.DataFrame(profile["played"]).rename(
                    columns={"game_id": "รหัส", "title": "เกม", "rating": "คะแนน", "play_date": "วันที่เล่น"}
                )
                st.dataframe(df, hide_index=True)
            else:
                st.info("ผู้เล่นคนนี้ยังไม่มีประวัติการเล่น — เพิ่มได้ที่เมนู “บันทึกการเล่น”")


# ───────────────────────── Recommendations ─────────────────────────
elif page == "recommend":
    page_header("เกมแนะนำ", "จัดอันดับเกมที่ผู้เล่นยังไม่เคยเล่น พร้อมแสดงที่มาของคะแนนทุกส่วน")
    c1, c2 = st.columns([2, 1])
    with c1:
        user_id = pick_user("rec_user")
    with c2:
        top_n = st.slider("จำนวนคำแนะนำ", 3, 12, 6)
    if user_id:
        rows = db.recommend_games(user_id, top_n)
        st.caption("คะแนน = เพื่อนเล่น × 3 + แนวเกมตรงกัน × 2 + จำนวนผู้เล่น × 0.20 + คะแนนรีวิวเฉลี่ย × 0.50")
        if not rows:
            st.info("ยังไม่มีคำแนะนำ — ลองเพิ่มเพื่อน แนวเกมที่ชอบ หรือประวัติการเล่นให้ผู้เล่นคนนี้")
        gimgs = images("Game")
        for i, row in enumerate(rows, start=1):
            matched = set(row.get("matched_genres") or [])
            chips = "".join(chip(g, g in matched) for g in (row.get("genres") or []))
            devs = esc(", ".join(row.get("developers") or []) or "ไม่ระบุผู้พัฒนา")
            bar, legend = breakdown(row)
            year = f" · {row['year']}" if row.get("year") else ""
            st.markdown(
                f"""<div class="rec">
                  <div class="rank">{i}</div>
                  <div>{cover(row['title'], gimgs.get(row['game_id']))}</div>
                  <div>
                    <div class="rec-top"><h3>{esc(row['title'] or '')}</h3>
                      <div class="score">{row['score']:.2f}<small>คะแนน</small></div></div>
                    <div class="meta">{esc(row['game_id'])}{year} · {devs}</div>
                    <div>{chips}</div>
                    <div class="bar">{bar}</div>
                    <div class="legend">{legend}</div>
                    <p class="why"><b>เหตุผล:</b> {esc(explain_reason(row))}</p>
                  </div></div>""",
                unsafe_allow_html=True,
            )


# ───────────────────────── Games ─────────────────────────
elif page == "games":
    page_header("เกม", "ค้นหา เพิ่ม แก้ไข และลบเกมในระบบ")
    t1, t2, t3 = st.tabs(["คลังเกม", "เพิ่มเกม", "แก้ไข / ลบเกม"])

    with t1:
        c1, c2 = st.columns([2, 1])
        keyword = c1.text_input("ค้นหาชื่อเกมหรือค่ายผู้พัฒนา", placeholder="เช่น CyberPulse, Aether, PixelCraft")
        genre = c2.selectbox("แนวเกม", [""] + db.list_genres(), format_func=lambda x: "ทุกแนวเกม" if x == "" else x)
        rows = db.search_games(keyword, genre)
        st.caption(f"พบ {len(rows)} เกม")
        gimgs = images("Game")
        cols = st.columns(4)
        for n, r in enumerate(rows):
            with cols[n % 4]:
                chips = "".join(chip(x) for x in r["genres"])
                st.markdown(
                    f'<div class="gcard">{cover(r["title"], gimgs.get(r["game_id"]))}<div class="gbody">'
                    f'<h4>{esc(r["title"])}</h4><div class="meta">{r["year"] or "-"} · '
                    f'{esc(", ".join(r["developers"]) or "ไม่ระบุผู้พัฒนา")}</div>{chips}'
                    f'<div class="meta" style="margin:.4rem 0 0">👥 {r["players"]} ผู้เล่น</div></div></div>',
                    unsafe_allow_html=True,
                )
        if rows:
            df = pd.DataFrame(rows)
            df["developers"] = df["developers"].map(", ".join)
            df["genres"] = df["genres"].map(", ".join)
            df = df.rename(columns={"game_id": "รหัส", "title": "ชื่อเกม", "year": "ปี",
                                    "developers": "ผู้พัฒนา", "genres": "แนวเกม", "players": "ผู้เล่น"})
            with st.expander("ดูแบบตาราง"):
                st.dataframe(df, hide_index=True)
        else:
            st.info("ไม่พบเกมที่ตรงกับเงื่อนไข ลองล้างช่องค้นหาหรือเพิ่มเกมใหม่ที่แท็บ “เพิ่มเกม”")

    with t2:
        with st.container(border=True):
            ok, title, year, dev_ids, gs = game_form(
                "g_add", {"title": "", "year": date.today().year, "developer_ids": [], "genres": []}, "เพิ่มเกม",
                with_photo=True,
            )
        if ok:
            if not title:
                st.error("กรุณากรอกชื่อเกม")
            else:
                gid = db.next_id("Game", "game_id", "G")
                do(save_with_image, f"เพิ่มเกม {title} ({gid}) แล้ว", db.save_game, "Game", gid,
                   st.session_state.get(photo_key("g_add")), gid, title, year, dev_ids, gs)

    with t3:
        gid = pick_game("g_edit_sel", "เลือกเกมที่ต้องการแก้ไข")
        d = db.get_game_detail(gid) if gid else None
        if d:
            left, right = st.columns([1, 2])
            with left:
                st.markdown("##### รูปปกเกม")
                image_panel("Game", gid, d["title"])
            with right:
                with st.container(border=True):
                    ok, title, year, dev_ids, gs = game_form(f"g_edit_{gid}", d, "บันทึกการแก้ไข")
                if ok:
                    if not title:
                        st.error("กรุณากรอกชื่อเกม")
                    else:
                        do(db.save_game, f"บันทึกเกม {title} แล้ว", gid, title, year, dev_ids, gs)
                danger_zone(
                    "เกม", f"g_del_{gid}", db.delete_game, gid,
                    ok=f"ลบเกม {d['title']} แล้ว",
                    warning="การลบจะลบประวัติการเล่น ความสัมพันธ์ และรูปปกของเกมนี้ และย้อนกลับไม่ได้",
                )


# ───────────────────────── Players ─────────────────────────
elif page == "players":
    page_header("ผู้เล่น", "จัดการข้อมูลผู้เล่น แนวเกมที่ชอบ และเพื่อน")
    t1, t2, t3, t4 = st.tabs(["ผู้เล่นทั้งหมด", "เพิ่มผู้เล่น", "แก้ไข / ลบผู้เล่น", "เพื่อน"])

    with t1:
        users = db.get_users()
        uimgs = images("User")
        cols = st.columns(4)
        for n, u in enumerate(users):
            with cols[n % 4]:
                lvl = min(100, int(u["level"] or 0))
                st.markdown(
                    f'<div class="gcard pcard">{avatar(u["name"], uimgs.get(u["user_id"]), 92)}'
                    f'<h4 style="margin:0;font-family:Kanit,sans-serif">{esc(u["name"] or "")}</h4>'
                    f'<div class="meta" style="margin:.1rem 0 .5rem">{esc(u["user_id"])} · {esc(u["platform"] or "-")}</div>'
                    f'<div class="lvl"><span style="width:{lvl}%"></span></div>'
                    f'<div class="meta" style="margin:0">เลเวล {u["level"]} · เล่น {u["games"]} เกม · เพื่อน {u["friends"]}</div></div>',
                    unsafe_allow_html=True,
                )
        if users:
            df = pd.DataFrame(users).rename(columns={
                "user_id": "รหัส", "name": "ชื่อ", "platform": "แพลตฟอร์ม",
                "level": "เลเวล", "games": "เกมที่เล่น", "friends": "เพื่อน"})
            with st.expander("ดูแบบตาราง"):
                st.dataframe(df, hide_index=True)
        else:
            st.info("ยังไม่มีผู้เล่น เริ่มต้นที่แท็บ “เพิ่มผู้เล่น”")

    with t2:
        with st.container(border=True):
            ok, name, platform, level, interests = user_form(
                "u_add", {"name": "", "platform": "", "level": 1, "interests": []}, "เพิ่มผู้เล่น",
                with_photo=True,
            )
        if ok:
            if not name:
                st.error("กรุณากรอกชื่อผู้เล่น")
            else:
                uid = db.next_id("User", "user_id", "U")
                do(save_with_image, f"เพิ่มผู้เล่น {name} ({uid}) แล้ว", db.save_user, "User", uid,
                   st.session_state.get(photo_key("u_add")), uid, name, platform, level, interests)

    with t3:
        uid = pick_user("u_edit_sel", "เลือกผู้เล่นที่ต้องการแก้ไข")
        d = db.get_profile(uid) if uid else None
        if d:
            left, right = st.columns([1, 2])
            with left:
                st.markdown("##### รูปผู้เล่น")
                image_panel("User", uid, d["name"])
            with right:
                with st.container(border=True):
                    ok, name, platform, level, interests = user_form(f"u_edit_{uid}", d, "บันทึกการแก้ไข")
                if ok:
                    if not name:
                        st.error("กรุณากรอกชื่อผู้เล่น")
                    else:
                        do(db.save_user, f"บันทึกข้อมูล {name} แล้ว", uid, name, platform, level, interests)
                danger_zone(
                    "ผู้เล่น", f"u_del_{uid}", db.delete_user, uid,
                    ok=f"ลบผู้เล่น {d['name']} แล้ว",
                    warning="การลบจะลบเพื่อน ประวัติการเล่น แนวเกมที่ชอบ และรูปของผู้เล่นคนนี้ และย้อนกลับไม่ได้",
                )

    with t4:
        uid = pick_user("u_friend_sel", "เลือกผู้เล่น")
        if uid:
            friends = db.list_friends(uid)
            st.markdown(f"**เพื่อนปัจจุบัน ({len(friends)})**")
            if not friends:
                st.caption("ยังไม่มีเพื่อน เพิ่มได้ด้านล่าง")
            uimgs = images("User")
            for f in friends:
                c1, c2 = st.columns([4, 1], vertical_alignment="center")
                c1.markdown(
                    f'<div class="rowuser">{avatar(f["name"], uimgs.get(f["user_id"]), 38)}'
                    f'<span>{esc(f["name"])} · {esc(f["user_id"])} · {esc(f["platform"] or "-")}</span></div>',
                    unsafe_allow_html=True,
                )
                if c2.button("ลบเพื่อน", key=f"rmf_{uid}_{f['user_id']}"):
                    do(db.remove_friend, f"ลบ {f['name']} ออกจากเพื่อนแล้ว", uid, f["user_id"])
            st.divider()
            taken = {f["user_id"] for f in friends} | {uid}
            others = {f"{u['user_id']} — {u['name']}": u["user_id"] for u in db.get_users() if u["user_id"] not in taken}
            if others:
                c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
                chosen = c1.selectbox("เพิ่มเพื่อน", list(others), key=f"addf_{uid}")
                if c2.button("เพิ่มเพื่อน", type="primary", key=f"addf_btn_{uid}"):
                    do(db.add_friend, "เพิ่มเพื่อนแล้ว", uid, others[chosen])
            else:
                st.caption("ไม่มีผู้เล่นอื่นให้เพิ่มเป็นเพื่อนแล้ว")


# ───────────────────────── Plays ─────────────────────────
elif page == "plays":
    page_header("บันทึกการเล่น", "เพิ่ม แก้ไขวันที่และคะแนน หรือลบประวัติการเล่นเกม")
    t1, t2 = st.tabs(["บันทึกการเล่นใหม่", "จัดการประวัติ"])

    with t1:
        with st.container(border=True):
            uid = pick_user("play_user")
            gid = pick_game("play_game")
            c1, c2 = st.columns(2)
            pdate = c1.date_input("วันที่เล่น", value=date.today(), key="play_date")
            use_rating = c2.checkbox("ให้คะแนนรีวิว", key="play_use_rating")
            rating = c2.slider("คะแนน", 1.0, 5.0, 4.0, 0.5, disabled=not use_rating, key="play_rating")
            if st.button("บันทึกการเล่น", type="primary", disabled=not (uid and gid)):
                do(db.record_play, "บันทึกการเล่นแล้ว", uid, gid, pdate.isoformat(), rating if use_rating else None)
        st.caption("ถ้าผู้เล่นเคยเล่นเกมนี้แล้ว ระบบจะอัปเดตวันที่และคะแนนของรายการเดิม")

    with t2:
        users = db.get_users()
        opts = {"ทุกคน": ""} | {f"{u['user_id']} — {u['name']}": u["user_id"] for u in users}
        who = opts[st.selectbox("กรองตามผู้เล่น", list(opts), key="plays_filter")]
        plays = db.list_plays(who)
        if not plays:
            st.info("ยังไม่มีประวัติการเล่น เพิ่มได้ที่แท็บ “บันทึกการเล่นใหม่”")
        else:
            df = pd.DataFrame(plays).rename(columns={
                "user_id": "รหัสผู้เล่น", "user_name": "ผู้เล่น", "game_id": "รหัสเกม",
                "title": "เกม", "play_date": "วันที่เล่น", "rating": "คะแนน"})
            st.dataframe(df, hide_index=True)

            st.markdown("##### แก้ไขหรือลบรายการ")
            labels = {f"{p['user_name']} → {p['title']} ({p['play_date']})": p for p in plays}
            p = labels[st.selectbox("เลือกรายการ", list(labels), key="plays_sel")]
            k = f"{p['user_id']}_{p['game_id']}"
            with st.container(border=True):
                with st.form(f"play_edit_{k}"):
                    c1, c2 = st.columns(2)
                    nd = c1.date_input("วันที่เล่น", to_date(p["play_date"]), key=f"pe_d_{k}")
                    has = c2.checkbox("มีคะแนนรีวิว", value=p["rating"] is not None, key=f"pe_h_{k}")
                    nr = c2.slider("คะแนน", 1.0, 5.0, float(p["rating"] or 4.0), 0.5, key=f"pe_r_{k}")
                    save = st.form_submit_button("บันทึกการแก้ไข", type="primary")
            if save:
                do(db.record_play, "แก้ไขประวัติการเล่นแล้ว", p["user_id"], p["game_id"], nd.isoformat(), nr if has else None)
            danger_zone(
                "ประวัติการเล่น", f"pl_del_{k}", db.delete_play, p["user_id"], p["game_id"],
                ok="ลบประวัติการเล่นแล้ว", warning="รายการนี้จะถูกลบออกจากประวัติของผู้เล่น",
            )


# ───────────────────────── Developers & Genres ─────────────────────────
elif page == "catalog":
    page_header("ค่ายและแนวเกม", "จัดการค่ายผู้พัฒนาและแนวเกมที่ใช้จัดหมวดหมู่เกม")
    t1, t2 = st.tabs(["ค่ายผู้พัฒนา", "แนวเกม"])

    with t1:
        devs = db.list_developers()
        if devs:
            st.dataframe(
                pd.DataFrame(devs).rename(columns={"developer_id": "รหัส", "name": "ชื่อค่าย", "games": "จำนวนเกม"}),
                hide_index=True,
            )
        else:
            st.info("ยังไม่มีค่ายผู้พัฒนา เพิ่มได้ด้านล่าง")
        a, b = st.columns(2)
        with a:
            st.markdown("##### เพิ่มค่ายใหม่")
            with st.container(border=True), st.form("d_add", clear_on_submit=True):
                n = st.text_input("ชื่อค่าย", key="d_add_name")
                go = st.form_submit_button("เพิ่มค่าย", type="primary")
            if go:
                if not n.strip():
                    st.error("กรุณากรอกชื่อค่าย")
                else:
                    did = db.next_id("Developer", "developer_id", "D", 2)
                    do(db.save_developer, f"เพิ่มค่าย {n.strip()} ({did}) แล้ว", did, n.strip())
        with b:
            st.markdown("##### แก้ไข / ลบค่าย")
            if devs:
                labels = {f"{x['developer_id']} — {x['name']}": x for x in devs}
                x = labels[st.selectbox("เลือกค่าย", list(labels), key="d_edit_sel")]
                with st.container(border=True), st.form(f"d_edit_{x['developer_id']}"):
                    n = st.text_input("ชื่อค่าย", x["name"], key=f"d_edit_name_{x['developer_id']}")
                    go = st.form_submit_button("บันทึกการแก้ไข", type="primary")
                if go:
                    if not n.strip():
                        st.error("กรุณากรอกชื่อค่าย")
                    else:
                        do(db.save_developer, "บันทึกชื่อค่ายแล้ว", x["developer_id"], n.strip())
                danger_zone(
                    "ค่าย", f"d_del_{x['developer_id']}", db.delete_developer, x["developer_id"],
                    ok=f"ลบค่าย {x['name']} แล้ว",
                    warning="เกมของค่ายนี้จะยังอยู่ แต่จะไม่มีผู้พัฒนาระบุ",
                )

    with t2:
        gs = db.genre_stats()
        if gs:
            st.dataframe(
                pd.DataFrame(gs).rename(columns={"name": "แนวเกม", "games": "จำนวนเกม", "fans": "ผู้เล่นที่ชอบ"}),
                hide_index=True,
            )
        else:
            st.info("ยังไม่มีแนวเกม เพิ่มได้ด้านล่าง")
        a, b = st.columns(2)
        with a:
            st.markdown("##### เพิ่มแนวเกมใหม่")
            with st.container(border=True), st.form("gn_add", clear_on_submit=True):
                n = st.text_input("ชื่อแนวเกม", key="gn_add_name")
                go = st.form_submit_button("เพิ่มแนวเกม", type="primary")
            if go:
                if not n.strip():
                    st.error("กรุณากรอกชื่อแนวเกม")
                else:
                    do(db.add_genre, f"เพิ่มแนวเกม {n.strip()} แล้ว", n.strip())
        with b:
            st.markdown("##### เปลี่ยนชื่อ / ลบแนวเกม")
            if gs:
                name = st.selectbox("เลือกแนวเกม", [g["name"] for g in gs], key="gn_edit_sel")
                with st.container(border=True), st.form(f"gn_edit_{name}"):
                    n = st.text_input("ชื่อใหม่", name, key=f"gn_edit_name_{name}")
                    go = st.form_submit_button("บันทึกชื่อใหม่", type="primary")
                if go:
                    if not n.strip():
                        st.error("กรุณากรอกชื่อแนวเกม")
                    else:
                        do(db.rename_genre, f"เปลี่ยนชื่อเป็น {n.strip()} แล้ว", name, n.strip())
                danger_zone(
                    "แนวเกม", f"gn_del_{name}", db.delete_genre, name,
                    ok=f"ลบแนวเกม {name} แล้ว",
                    warning="เกมและผู้เล่นที่ผูกกับแนวนี้จะถูกตัดความสัมพันธ์ออก",
                )


# ───────────────────────── Graph Explorer ─────────────────────────
elif page == "graph":
    page_header("กราฟความสัมพันธ์", "ดูเครือข่ายรอบตัวผู้เล่น: เพื่อน เกมที่เล่น แนวเกม และค่ายผู้พัฒนา")
    c1, c2 = st.columns([2, 1])
    with c1:
        user_id = pick_user("graph_user")
    with c2:
        limit = st.slider("จำนวน edge สูงสุด", 10, 120, 60, 10)
    if user_id:
        rows = db.graph_neighborhood(user_id, limit)
        if not rows:
            st.info("ผู้เล่นคนนี้ยังไม่มีความสัมพันธ์ในกราฟ")
        else:
            fill = {"User": "#ffb347", "Game": "#37d5c8", "Genre": "#9b95ff", "Developer": "#ff6b8b"}
            dot = [
                "digraph G {", 'rankdir="LR"; bgcolor="transparent";',
                'node [shape=box, style="rounded,filled", fontname="Helvetica", fontcolor="#0e1124", color="transparent"];',
                'edge [color="#6b72a8", fontcolor="#9aa0c8", fontsize=10, fontname="Helvetica"];',
            ]
            seen = set()
            for r in rows:
                for nid, label, name in [
                    (r["source_id"], r["source_label"], r["source_name"]),
                    (r["target_id"], r["target_label"], r["target_name"]),
                ]:
                    if nid not in seen:
                        safe = str(name).replace('"', "'")
                        dot.append(f'"{nid}" [label="{safe}", fillcolor="{fill.get(label, "#cccccc")}"];')
                        seen.add(nid)
                dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}"];')
            dot.append("}")
            st.markdown(
                " ".join(f'<span class="chip" style="border-color:{c};color:{c}">{k}</span>' for k, c in fill.items()),
                unsafe_allow_html=True,
            )
            st.graphviz_chart("\n".join(dot))
            with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
                st.dataframe(pd.DataFrame(rows), hide_index=True)


# ───────────────────────── Setup ─────────────────────────
elif page == "setup":
    page_header("ตั้งค่าระบบ", "สร้างข้อมูลตัวอย่าง หรือเริ่มต้นใหม่ด้วยฐานข้อมูลว่าง")
    st.markdown(
        """
        **โครงสร้างกราฟ**
        - `(:User)-[:FRIEND_OF]-(:User)`
        - `(:User)-[:PLAYED {play_date, rating}]->(:Game)`
        - `(:User)-[:LIKES_GENRE]->(:Genre)`
        - `(:Game)-[:IN_GENRE]->(:Genre)`
        - `(:Developer)-[:DEVELOPED]->(:Game)`
        """
    )
    with st.container(border=True):
        st.markdown("##### สร้าง constraint และข้อมูลตัวอย่าง")
        st.caption("ใช้ MERGE จึงไม่ลบข้อมูลเดิม และกดซ้ำได้อย่างปลอดภัย")
        if st.button("สร้าง Constraint + Demo Data", type="primary"):
            with st.spinner("กำลังสร้างข้อมูลเกมและผู้ใช้..."):
                do(db.seed_demo_data, "สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")
    danger_zone(
        "ข้อมูลทั้งหมด", "wipe", db.clear_all_data,
        ok="ล้างข้อมูลทั้งหมดแล้ว",
        warning="ข้อมูลทุก node และ relationship ในฐานข้อมูลนี้จะถูกลบ และย้อนกลับไม่ได้",
    )
