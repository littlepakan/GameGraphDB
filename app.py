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
LOGO_PATH = "kairung99.jpg"
GAME_IMG_SIZE = (640, 360)   # game covers are cropped to 16:9
USER_IMG_SIZE = (360, 360)   # player photos are cropped to a square
MAX_UPLOAD_MB = 8

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@500;600;700&family=IBM+Plex+Sans+Thai:wght@400;500;600&display=swap');
      :root {
        --bg:#0e1124; --panel:#161a36; --line:#2a3066; --text:#eceefb; --muted:#9aa0c8;
        --amber:#ffb347; --teal:#37d5c8; --rose:#ff6b8b; --violet:#6c63ff;
      }
      .block-container {padding-top: 3.6rem; padding-bottom: 3rem; max-width: 1240px;}
      h1, h2, h3, .display {font-family: 'Kanit', sans-serif !important; letter-spacing: 0;}
      [data-testid="stMarkdownContainer"] p, label, .stTextInput input, .stSelectbox, .stTabs button {
        font-family: 'IBM Plex Sans Thai', sans-serif;
      }
      /* top bar + top navigation */
      .topbar {display:flex; align-items:center; gap:.9rem; margin-bottom:.8rem;}
      .topbar .logo {width:52px; height:52px; border-radius:12px; object-fit:cover; border:1px solid var(--line);}
      .brand {font-family:'Kanit',sans-serif; font-size:1.7rem; font-weight:700; line-height:1.1;}
      .brand b {color: var(--amber); font-weight:700;}
      .brand-sub {color: var(--muted); font-size:.85rem; margin-top:.2rem;}
      /* the sidebar is unused: navigation lives in the top bar */
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] {display:none !important;}
      .st-key-nav {position:sticky; top:2.9rem; z-index:99; margin-bottom:1.1rem; padding:.55rem 0;
                   background:rgba(14,17,36,.94); backdrop-filter:blur(8px); border-bottom:1px solid var(--line);}
      .st-key-nav [role="radiogroup"] {gap:.45rem; flex-wrap:wrap;}
      .st-key-nav label {background:var(--panel); border:1px solid var(--line); border-radius:999px;
                         padding:.35rem 1rem; margin:0; cursor:pointer; transition:border-color .15s, background .15s;}
      .st-key-nav label:hover {border-color:var(--violet);}
      .st-key-nav label > div:first-of-type {display:none;}
      .st-key-nav label:has(input:checked) {background:var(--violet); border-color:var(--violet); font-weight:600;}
      .st-key-nav label:has(input:focus-visible) {outline:2px solid var(--amber); outline-offset:2px;}
      .st-key-pager {margin-top:2rem; padding-top:1rem; border-top:1px solid var(--line);}
      .st-key-pager button {width:100%;}
      .st-key-nav label p {margin:0; font-size:.95rem; white-space:nowrap;}

      /* images */
      .cover {position:relative; overflow:hidden; width:100%; border:1px solid var(--line);
              background:linear-gradient(135deg,#1d2250,#2b2f6e);}
      .cover img {width:100%; height:100%; object-fit:cover; display:block;}
      .cover.game {aspect-ratio:16/9; border-radius:12px;}
      .cover.user {aspect-ratio:1/1; border-radius:50%;}
      .cover.ph {display:flex; align-items:center; justify-content:center; color:var(--muted);
                 font-family:'Kanit',sans-serif; font-size:2rem;}
      .cover.user.av-sm {width:40px; min-width:40px; font-size:1rem;}
      .cover.user.av-md {width:72px; min-width:72px; font-size:1.6rem;}
      .cover.user.av-lg {width:96px; min-width:96px; font-size:2.2rem;}
      .ggrid {display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:1rem; margin-top:.5rem;}
      .pgrid {display:grid; grid-template-columns:repeat(auto-fill,minmax(270px,1fr)); gap:1rem; margin-top:.5rem;}
      .gcard, .pcard {background:var(--panel); border:1px solid var(--line); border-radius:14px; overflow:hidden;}
      .gcard .cover {border:0; border-radius:0;}
      .gcard .body {padding:.8rem 1rem 1rem;}
      .pcard {display:flex; align-items:center; gap:1rem; padding:.9rem 1rem;}
      .gtitle {font-family:'Kanit',sans-serif; font-size:1.05rem; font-weight:600; line-height:1.25;}
      .frow {display:flex; align-items:center; gap:.7rem;}
      .frow .meta, .profile-top .meta {margin:0;}
      .profile-top {display:flex; align-items:center; gap:1rem; margin-bottom:.7rem;}

      .pagehead {border-bottom:1px solid var(--line); padding-bottom:.9rem; margin-bottom:1.3rem;}
      .pagehead h1 {font-size:2.1rem; margin:0; padding:0; line-height:1.15;}
      .pagehead p {color: var(--muted); margin:.3rem 0 0 0;}

      .tile {background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:1rem 1.2rem;}
      .tile .n {font-family:'Kanit',sans-serif; font-size:2.6rem; font-weight:700; line-height:1;}
      .tile .l {color:var(--muted); font-size:.9rem; margin-top:.35rem;}

      .rec {display:grid; grid-template-columns:56px 170px 1fr; gap:1rem; background:var(--panel);
            border:1px solid var(--line); border-radius:14px; padding:1.1rem 1.3rem; margin-bottom:.9rem;}
      .rec .cover {align-self:start;}
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
      .profile h3 {margin:0; font-size:1.6rem;}
      .lvl {height:8px; border-radius:4px; background:var(--line); overflow:hidden; margin:.3rem 0 .9rem;}
      .lvl span {display:block; height:100%; background:var(--amber);}
      .kv {color:var(--muted); font-size:.85rem; margin-top:.5rem;}
      @media (max-width: 640px) {
        .rec {grid-template-columns:1fr;} .rec-top {flex-direction:column;}
        .st-key-nav [role="radiogroup"] {flex-wrap:nowrap; overflow-x:auto; padding-bottom:.3rem; scrollbar-width:thin;}
        .st-key-nav label {padding:.3rem .8rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ───────────────────────── helpers ─────────────────────────
esc = html.escape


def page_header(title: str, sub: str) -> None:
    st.markdown(
        f'<div class="pagehead"><h1>{esc(title)}</h1><p>{esc(sub)}</p></div>',
        unsafe_allow_html=True,
    )


def tile(col, number, label: str, color: str) -> None:
    col.markdown(
        f'<div class="tile"><div class="n" style="color:{color}">{number}</div>'
        f'<div class="l">{esc(label)}</div></div>',
        unsafe_allow_html=True,
    )


def chip(text: str, hit: bool = False) -> str:
    return f'<span class="chip{" hit" if hit else ""}">{esc(str(text))}</span>'


def ver() -> int:
    """Bumped after each successful write so add/edit forms (and their uploaders) start fresh."""
    return st.session_state.get("_v", 0)


@st.cache_data(show_spinner=False)
def logo_html(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    return f'<img class="logo" src="data:image/jpeg;base64,{b64}" alt="logo">'


def cover(image, title: str = "", kind: str = "game", size: str = "") -> str:
    """Image (or placeholder) as HTML. kind: 'game' (16:9) or 'user' (round avatar)."""
    cls = f"cover {kind}" + (f" {size}" if size else "")
    if image:
        return f'<div class="{cls}"><img src="{esc(image)}" alt="{esc(title)}" loading="lazy"></div>'
    ph = "🎮" if kind == "game" else ((title or "").strip()[:1].upper() or "👤")
    return f'<div class="{cls} ph"><span>{esc(ph)}</span></div>'


def to_data_uri(file, size: tuple[int, int]) -> str:
    """Crop/resize an uploaded image and return a compact JPEG data-URI to store on the node."""
    img = ImageOps.exif_transpose(Image.open(file))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (22, 26, 54))
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    else:
        img = img.convert("RGB")
    img = ImageOps.fit(img, size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def image_field(key: str, current: str | None, kind: str, title: str, size: tuple[int, int]):
    """Photo controls for use inside a form: preview, upload (add / replace) and remove.

    Returns a function that is called at submit time and yields the new data-URI,
    None (remove the image) or db.KEEP_IMAGE (leave it unchanged).
    """
    st.markdown(cover(current, title, kind, "av-lg" if kind == "user" else ""), unsafe_allow_html=True)
    st.caption("รูปปัจจุบัน" if current else "ยังไม่มีรูป")
    up = st.file_uploader(
        "เปลี่ยนรูป" if current else "อัปโหลดรูป",
        type=["png", "jpg", "jpeg", "webp"], key=f"{key}_img",
        help=f"ไฟล์ไม่เกิน {MAX_UPLOAD_MB} MB ระบบจะครอบและย่อรูปให้อัตโนมัติ",
    )
    remove = st.checkbox("ลบรูปปัจจุบัน", key=f"{key}_imgrm") if current else False

    def resolve():
        if up is not None:
            if up.size > MAX_UPLOAD_MB * 1024 * 1024:
                raise ValueError(f"ไฟล์รูปใหญ่เกิน {MAX_UPLOAD_MB} MB")
            try:
                return to_data_uri(up, size)
            except Exception as exc:  # noqa: BLE001
                raise ValueError("เปิดไฟล์รูปไม่ได้ กรุณาใช้ไฟล์ PNG / JPG / WEBP") from exc
        return None if remove else db.KEEP_IMAGE

    return resolve


def game_card(g: dict) -> str:
    devs = esc(", ".join(g.get("developers") or []) or "ไม่ระบุผู้พัฒนา")
    year = f" · {g['year']}" if g.get("year") else ""
    chips = "".join(chip(x) for x in g.get("genres") or [])
    return (
        f'<div class="gcard">{cover(g.get("image"), g["title"] or "", "game")}'
        f'<div class="body"><div class="gtitle">{esc(g["title"] or "")}</div>'
        f'<div class="meta">{esc(g["game_id"])}{year} · {devs}</div>'
        f'<div>{chips}</div><div class="kv">👥 {g.get("players", 0)} ผู้เล่น</div></div></div>'
    )


def player_card(u: dict) -> str:
    return (
        f'<div class="pcard">{cover(u.get("image"), u["name"] or "", "user", "av-md")}'
        f'<div><div class="gtitle">{esc(u["name"] or "")}</div>'
        f'<div class="meta">{esc(u["user_id"])} · {esc(u["platform"] or "-")}</div>'
        f'<div class="kv">เลเวล {u["level"]} · เล่น {u["games"]} เกม · เพื่อน {u["friends"]} คน</div></div></div>'
    )


def do(fn, ok: str, *args, **kwargs) -> None:
    """Run a write action, show errors inline, and refresh the page on success."""
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        st.error(f"ดำเนินการไม่สำเร็จ: {exc}")
        return
    st.session_state["_flash"] = ok
    st.session_state["_v"] = ver() + 1
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


def user_label(u: dict) -> str:
    return f"{u['user_id']} — {u['name']} ({u['platform']})"


def pick_user(key: str, label: str = "เลือกผู้เล่น") -> str | None:
    users = db.get_users()
    if not users:
        st.info("ยังไม่มีผู้เล่น เพิ่มผู้เล่นคนแรก หรือสร้างข้อมูลตัวอย่างได้เลย")
        a, b, _ = st.columns([1, 1, 2])
        a.button("🧑‍🤝‍🧑 เพิ่มผู้เล่น", key=f"{key}_go_players", on_click=goto, args=("players",))
        b.button("⚙️ สร้างข้อมูลตัวอย่าง", key=f"{key}_go_setup", on_click=goto, args=("setup",))
        return None
    labels = {user_label(u): u["user_id"] for u in users}
    if st.session_state.get(key) not in labels:
        st.session_state.pop(key, None)
    return labels[st.selectbox(label, list(labels), key=key)]


def pick_game(key: str, label: str = "เลือกเกม") -> str | None:
    games = db.search_games()
    if not games:
        st.info("ยังไม่มีเกมในระบบ เพิ่มเกมแรกได้เลย")
        st.button("🎮 เพิ่มเกม", key=f"{key}_go_games", on_click=goto, args=("games",))
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
def user_form(key: str, d: dict, submit_label: str):
    genres = db.list_genres()
    plats = PLATFORMS if (not d["platform"] or d["platform"] in PLATFORMS) else [d["platform"]] + PLATFORMS
    with st.form(key):
        c_img, c_main = st.columns([1, 3])
        with c_img:
            image = image_field(key, d.get("image"), "user", d["name"], USER_IMG_SIZE)
        with c_main:
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
        submit = st.form_submit_button(submit_label, type="primary")
    return submit, name.strip(), platform, int(level), interests, image


def game_form(key: str, d: dict, submit_label: str):
    devs = {x["developer_id"]: x["name"] for x in db.list_developers()}
    genres = db.list_genres()
    with st.form(key):
        c_img, c_main = st.columns([1, 2])
        with c_img:
            image = image_field(key, d.get("image"), "game", d["title"], GAME_IMG_SIZE)
        with c_main:
            title = st.text_input("ชื่อเกม", d["title"], key=f"{key}_title")
            year = st.number_input("ปีที่วางจำหน่าย", 1980, 2100, int(d["year"] or date.today().year), key=f"{key}_year")
            dev_ids = st.multiselect(
                "ผู้พัฒนา", list(devs), default=[x for x in d["developer_ids"] if x in devs],
                format_func=lambda x: devs[x], key=f"{key}_dev",
            )
            gs = st.multiselect("แนวเกม", genres, default=[x for x in d["genres"] if x in genres], key=f"{key}_gen")
        submit = st.form_submit_button(submit_label, type="primary")
    return submit, title.strip(), int(year), dev_ids, gs, image


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

st.markdown(
    f'<div class="topbar">{logo_html(LOGO_PATH)}<div><div class="brand">Game<b>Graph</b></div>'
    '<div class="brand-sub">ระบบแนะนำเกมด้วย Neo4j</div></div></div>',
    unsafe_allow_html=True,
)
PAGE_LABEL = {v: k for k, v in MENU.items()}
PAGE_KEYS = list(PAGE_LABEL)


def goto(page_key: str, **state) -> None:
    """on_click callback: switch menu page (optionally presetting widget values such as a selected player)."""
    st.session_state["nav"] = PAGE_LABEL[page_key]
    st.session_state.update(state)


# deep link: open the page named in ?page=... on first load / refresh
if "nav" not in st.session_state:
    wanted = st.query_params.get("page", "dashboard")
    st.session_state["nav"] = PAGE_LABEL.get(wanted, PAGE_LABEL["dashboard"])

st.radio("เมนู", list(MENU), horizontal=True, label_visibility="collapsed", key="nav")
page = MENU[st.session_state["nav"]]
if st.query_params.get("page") != page:
    st.query_params["page"] = page   # keeps the URL in sync so refresh / sharing lands on the same page


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
            interest_html = "".join(chip(g) for g in profile["interests"]) or '<span class="meta">ยังไม่ได้ระบุ</span>'
            st.markdown(
                f"""<div class="profile">
                <div class="profile-top">{cover(profile.get('image'), profile['name'] or '', 'user', 'av-lg')}
                <div><h3>{esc(profile['name'] or '')}</h3>
                <div class="meta">{esc(profile['user_id'])} · {esc(profile['platform'] or '-')}</div></div></div>
                <div class="kv">เลเวล {profile['level']}</div>
                <div class="lvl"><span style="width:{lvl}%"></span></div>
                <div class="kv">แนวเกมที่ชอบ</div>
                {interest_html}
                </div>""",
                unsafe_allow_html=True,
            )
        with b:
            q1, q2, q3 = st.columns(3)
            q1.button("✨ ดูเกมแนะนำ", key="dash_go_rec", use_container_width=True, on_click=goto,
                      args=("recommend",), kwargs={"rec_user": user_label(profile)})
            q2.button("🕸️ ดูกราฟเพื่อน", key="dash_go_graph", use_container_width=True, on_click=goto,
                      args=("graph",), kwargs={"graph_user": user_label(profile)})
            q3.button("📝 บันทึกการเล่น", key="dash_go_plays", use_container_width=True, on_click=goto,
                      args=("plays",), kwargs={"play_user": user_label(profile)})
            if profile["played"]:
                df = pd.DataFrame(profile["played"]).rename(
                    columns={"game_id": "รหัส", "title": "เกม", "rating": "คะแนน", "play_date": "วันที่เล่น"}
                )
                st.dataframe(df, hide_index=True)
            else:
                st.info("ผู้เล่นคนนี้ยังไม่มีประวัติการเล่น กดปุ่ม “บันทึกการเล่น” ด้านบนเพื่อเพิ่ม")


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
            a, b, _ = st.columns([1, 1, 2])
            a.button("🧑‍🤝‍🧑 จัดการผู้เล่น / เพื่อน", key="rec_go_players", on_click=goto, args=("players",))
            b.button("📝 บันทึกการเล่น", key="rec_go_plays", on_click=goto, args=("plays",))
        for i, row in enumerate(rows, start=1):
            matched = set(row.get("matched_genres") or [])
            chips = "".join(chip(g, g in matched) for g in (row.get("genres") or []))
            devs = esc(", ".join(row.get("developers") or []) or "ไม่ระบุผู้พัฒนา")
            bar, legend = breakdown(row)
            year = f" · {row['year']}" if row.get("year") else ""
            st.markdown(
                f"""<div class="rec">
                  <div class="rank">{i}</div>
                  {cover(row.get('image'), row['title'] or '', 'game')}
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
        c1, c2, c3 = st.columns([2, 1, 1])
        keyword = c1.text_input("ค้นหาชื่อเกมหรือค่ายผู้พัฒนา", placeholder="เช่น CyberPulse, Aether, PixelCraft")
        genre = c2.selectbox("แนวเกม", [""] + db.list_genres(), format_func=lambda x: "ทุกแนวเกม" if x == "" else x)
        view = c3.radio("มุมมอง", ["การ์ด", "ตาราง"], horizontal=True, key="g_view")
        rows = db.search_games(keyword, genre, with_image=True)
        st.caption(f"พบ {len(rows)} เกม")
        if not rows:
            st.info("ไม่พบเกมที่ตรงกับเงื่อนไข ลองล้างช่องค้นหาหรือเพิ่มเกมใหม่ที่แท็บ “เพิ่มเกม”")
        elif view == "การ์ด":
            st.markdown('<div class="ggrid">' + "".join(game_card(g) for g in rows) + "</div>", unsafe_allow_html=True)
        else:
            df = pd.DataFrame(rows)
            df["developers"] = df["developers"].map(", ".join)
            df["genres"] = df["genres"].map(", ".join)
            df = df[["image", "game_id", "title", "year", "developers", "genres", "players"]].rename(
                columns={"image": "รูป", "game_id": "รหัส", "title": "ชื่อเกม", "year": "ปี",
                         "developers": "ผู้พัฒนา", "genres": "แนวเกม", "players": "ผู้เล่น"})
            st.dataframe(df, hide_index=True, column_config={"รูป": st.column_config.ImageColumn("รูป", width="small")})

    with t2:
        with st.container(border=True):
            ok, title, year, dev_ids, gs, image = game_form(
                f"g_add_{ver()}",
                {"title": "", "year": date.today().year, "developer_ids": [], "genres": [], "image": None},
                "เพิ่มเกม",
            )
        if ok:
            if not title:
                st.error("กรุณากรอกชื่อเกม")
            else:
                gid = db.next_id("Game", "game_id", "G")
                do(lambda: db.save_game(gid, title, year, dev_ids, gs, image()), f"เพิ่มเกม {title} ({gid}) แล้ว")

    with t3:
        gid = pick_game("g_edit_sel", "เลือกเกมที่ต้องการแก้ไข")
        d = db.get_game_detail(gid) if gid else None
        if d:
            with st.container(border=True):
                ok, title, year, dev_ids, gs, image = game_form(f"g_edit_{gid}_{ver()}", d, "บันทึกการแก้ไข")
            if ok:
                if not title:
                    st.error("กรุณากรอกชื่อเกม")
                else:
                    do(lambda: db.save_game(gid, title, year, dev_ids, gs, image()), f"บันทึกเกม {title} แล้ว")
            danger_zone(
                "เกม", f"g_del_{gid}", db.delete_game, gid,
                ok=f"ลบเกม {d['title']} แล้ว",
                warning="การลบจะลบประวัติการเล่นและความสัมพันธ์ทั้งหมดของเกมนี้ และย้อนกลับไม่ได้",
            )


# ───────────────────────── Players ─────────────────────────
elif page == "players":
    page_header("ผู้เล่น", "จัดการข้อมูลผู้เล่น แนวเกมที่ชอบ และเพื่อน")
    t1, t2, t3, t4 = st.tabs(["ผู้เล่นทั้งหมด", "เพิ่มผู้เล่น", "แก้ไข / ลบผู้เล่น", "เพื่อน"])

    with t1:
        users = db.get_users(with_image=True)
        if users:
            view = st.radio("มุมมอง", ["การ์ด", "ตาราง"], horizontal=True, key="u_view")
            if view == "การ์ด":
                st.markdown('<div class="pgrid">' + "".join(player_card(u) for u in users) + "</div>", unsafe_allow_html=True)
            else:
                df = pd.DataFrame(users)[["image", "user_id", "name", "platform", "level", "games", "friends"]].rename(columns={
                    "image": "รูป", "user_id": "รหัส", "name": "ชื่อ", "platform": "แพลตฟอร์ม",
                    "level": "เลเวล", "games": "เกมที่เล่น", "friends": "เพื่อน"})
                st.dataframe(df, hide_index=True, column_config={"รูป": st.column_config.ImageColumn("รูป", width="small")})
        else:
            st.info("ยังไม่มีผู้เล่น เริ่มต้นที่แท็บ “เพิ่มผู้เล่น”")

    with t2:
        with st.container(border=True):
            ok, name, platform, level, interests, image = user_form(
                f"u_add_{ver()}", {"name": "", "platform": "", "level": 1, "interests": [], "image": None}, "เพิ่มผู้เล่น"
            )
        if ok:
            if not name:
                st.error("กรุณากรอกชื่อผู้เล่น")
            else:
                uid = db.next_id("User", "user_id", "U")
                do(lambda: db.save_user(uid, name, platform, level, interests, image()), f"เพิ่มผู้เล่น {name} ({uid}) แล้ว")

    with t3:
        uid = pick_user("u_edit_sel", "เลือกผู้เล่นที่ต้องการแก้ไข")
        d = db.get_profile(uid) if uid else None
        if d:
            with st.container(border=True):
                ok, name, platform, level, interests, image = user_form(f"u_edit_{uid}_{ver()}", d, "บันทึกการแก้ไข")
            if ok:
                if not name:
                    st.error("กรุณากรอกชื่อผู้เล่น")
                else:
                    do(lambda: db.save_user(uid, name, platform, level, interests, image()), f"บันทึกข้อมูล {name} แล้ว")
            danger_zone(
                "ผู้เล่น", f"u_del_{uid}", db.delete_user, uid,
                ok=f"ลบผู้เล่น {d['name']} แล้ว",
                warning="การลบจะลบเพื่อน ประวัติการเล่น และแนวเกมที่ชอบของผู้เล่นคนนี้ และย้อนกลับไม่ได้",
            )

    with t4:
        uid = pick_user("u_friend_sel", "เลือกผู้เล่น")
        if uid:
            friends = db.list_friends(uid)
            st.markdown(f"**เพื่อนปัจจุบัน ({len(friends)})**")
            if not friends:
                st.caption("ยังไม่มีเพื่อน เพิ่มได้ด้านล่าง")
            for f in friends:
                c1, c2 = st.columns([4, 1])
                c1.markdown(
                    f'<div class="frow">{cover(f.get("image"), f["name"] or "", "user", "av-sm")}'
                    f'<div><b>{esc(f["name"] or "")}</b>'
                    f'<div class="meta">{esc(f["user_id"])} · {esc(f["platform"] or "-")}</div></div></div>',
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


# ───────────────────────── Prev / Next pager ─────────────────────────
_i = PAGE_KEYS.index(page)
with st.container(key="pager"):
    _l, _m, _r = st.columns([1, 1, 1], vertical_alignment="center")
    if _i > 0:
        _l.button(f"← {PAGE_LABEL[PAGE_KEYS[_i - 1]].strip()}", key="pg_prev", on_click=goto, args=(PAGE_KEYS[_i - 1],))
    _m.markdown(
        f'<div class="meta" style="text-align:center">หน้า {_i + 1} / {len(PAGE_KEYS)}</div>', unsafe_allow_html=True
    )
    if _i < len(PAGE_KEYS) - 1:
        _r.button(f"{PAGE_LABEL[PAGE_KEYS[_i + 1]].strip()} →", key="pg_next", on_click=goto,
                  args=(PAGE_KEYS[_i + 1],), type="primary")
