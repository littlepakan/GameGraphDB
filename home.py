"""หน้าแรก: เลือกผลงานที่ส่งอาจารย์ (5 ชิ้น) — GameGraph คือชิ้นสุดท้ายที่กดเข้าไปใช้งานระบบจริง

การ์ดเรียงเป็นแถวลงไป (รูปปกซ้าย / รายละเอียดขวา)
รูปปก: ถ้าอยากใช้รูปของตัวเอง ให้วางไฟล์ไว้ที่  assets/covers/card_1.png … card_5.png
(รองรับ .png .jpg .jpeg .webp) ถ้าไม่มีไฟล์ ระบบจะวาดรูปปกให้อัตโนมัติ
"""
from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path

import streamlit as st

# ════════════════════════════════════════════════════════════════
#  ✏️  แก้ลิงก์ตรงนี้ที่เดียว (เว้นว่าง "" = ปุ่มจะถูกปิดไว้จนกว่าจะใส่ลิงก์)
# ════════════════════════════════════════════════════════════════
LINKS = {
    "intro_colab": "https://colab.research.google.com/drive/1HSW_zcuTOrRy9oSEF6OeOm5aZk8iRzrp?usp=sharing",
    "intro_github": "https://github.com/mediuni/GameGraphDB/blob/main/Week2_664245056.ipynb",
    "neo4j_github": "https://github.com/mediuni/GameGraphDB/blob/main/664245056_Neo4jGraphDB.pdf",
    "recsys_colab": "https://colab.research.google.com/drive/1F6NlHCEr3OjVgNXJqCD3HBblgVGT4I-l?usp=sharing",
    "recsys_github": "https://github.com/mediuni/GameGraphDB/blob/main/GameGenresRecommenderSystem.ipynb",
    "recsys_neo4j_colab": "https://colab.research.google.com/drive/1Lqlh90eylLxEPic16uhgXmAVaxnvyq6O?usp=sharing",
    "recsys_neo4j_github": "https://github.com/mediuni/GameGraphDB/blob/main/664245056_GameGenresRecommenderWithNeo4j.ipynb",
    "gamegraph_github": "https://github.com/mediuni/GameGraphDB",
}
HERE = Path(__file__).parent
PDF_FILE = HERE / "664245056_Neo4jGraphDB.pdf"
COVER_DIR = HERE / "assets" / "covers"

OWNER = "นายปกานต์ วงษ์ท่าเรือ"
STUDENT_ID = "664245056"
SECTION = "66/44"

AMBER, TEAL, ROSE, VIOLET = "#ffb347", "#37d5c8", "#ff6b8b", "#9b95ff"
ACCENTS = {1: AMBER, 2: TEAL, 3: ROSE, 4: VIOLET, 5: AMBER}

esc = html.escape


@st.cache_data(show_spinner=False)
def _pdf_bytes() -> bytes | None:
    return PDF_FILE.read_bytes() if PDF_FILE.exists() else None


# ════════════════════════════════════════════════════════════════
#  รูปปก
# ════════════════════════════════════════════════════════════════
_GRAPH_NODES = [(120, 90), (250, 55), (380, 110), (520, 70), (170, 235), (320, 250), (470, 215), (560, 290)]
_GRAPH_EDGES = [(0, 1), (1, 2), (2, 3), (0, 4), (1, 5), (2, 5), (2, 6), (3, 6), (4, 5), (5, 6), (6, 7)]


def _graph(c: str, hub: int | None = None, op: float = 1.0) -> str:
    lines = "".join(
        f'<line x1="{_GRAPH_NODES[a][0]}" y1="{_GRAPH_NODES[a][1]}" '
        f'x2="{_GRAPH_NODES[b][0]}" y2="{_GRAPH_NODES[b][1]}"/>'
        for a, b in _GRAPH_EDGES
    )
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="{17 if i == hub else 10}" '
        f'fill="{c if i == hub else "#161a36"}"/>'
        for i, (x, y) in enumerate(_GRAPH_NODES)
    )
    return (
        f'<g opacity="{op}" stroke="{c}" stroke-width="3" stroke-linecap="round">{lines}'
        f'<g stroke-width="3.5">{dots}</g></g>'
    )


def _motif(n: int, c: str) -> str:
    if n == 1:  # ฐานข้อมูล (ทรงกระบอก 3 ชั้น)
        disks = ""
        for y in (110, 170, 230):
            disks += (
                f'<path d="M230 {y} v60 a90 26 0 0 0 180 0 v-60" fill="{c}" fill-opacity=".10"/>'
            )
        return (
            f'<g stroke="{c}" stroke-width="4" fill="none" stroke-linejoin="round">{disks}'
            f'<ellipse cx="320" cy="110" rx="90" ry="26" fill="{c}" fill-opacity=".25"/></g>'
        )
    if n == 2:  # กราฟ Neo4j
        return _graph(c)
    if n == 3:  # กราฟแท่ง (แนวเกมแบบดั้งเดิม)
        heights = [90, 150, 120, 200, 140, 175]
        bars = "".join(
            f'<rect x="{150 + i * 62}" y="{290 - h}" width="40" height="{h}" rx="8" '
            f'fill="{c}" fill-opacity="{0.35 + 0.1 * (i % 3)}"/>'
            for i, h in enumerate(heights)
        )
        pts = " ".join(f"{170 + i * 62},{270 - h}" for i, h in enumerate(heights))
        return (
            f'{bars}<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="4" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<line x1="130" y1="292" x2="520" y2="292" stroke="{c}" stroke-width="3"/>'
        )
    if n == 4:  # กราฟ + ผู้ใช้ตรงกลางที่ได้รับคำแนะนำ
        return _graph(c, hub=5)
    # n == 5 : จอยเกม + กราฟจาง ๆ ด้านหลัง
    pad = (
        f'<g stroke="{c}" stroke-width="4" fill="#161a36">'
        f'<rect x="190" y="140" width="260" height="120" rx="60"/></g>'
        f'<g fill="{c}"><rect x="238" y="188" width="46" height="12" rx="4"/>'
        f'<rect x="255" y="171" width="12" height="46" rx="4"/>'
        f'<circle cx="385" cy="170" r="9"/><circle cx="385" cy="214" r="9"/>'
        f'<circle cx="363" cy="192" r="9"/><circle cx="407" cy="192" r="9"/></g>'
    )
    return _graph(c, op=0.28) + pad


def _cover_svg(n: int) -> str:
    c = ACCENTS[n]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#161a36"/><stop offset="1" stop-color="#2c3070"/></linearGradient>'
        f'<radialGradient id="r" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{c}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient></defs>'
        '<rect width="640" height="360" fill="url(#g)"/>'
        '<circle cx="320" cy="180" r="230" fill="url(#r)"/>'
        f"{_motif(n, c)}</svg>"
    )


@st.cache_data(show_spinner=False)
def _cover_src(n: int) -> str:
    """คืน data-URI ของรูปปก: ใช้ไฟล์ใน assets/covers ก่อน ถ้าไม่มีใช้ SVG ที่วาดให้"""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = COVER_DIR / f"card_{n}.{ext}"
        if p.exists():
            mime = mimetypes.guess_type(p.name)[0] or "image/png"
            return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"
    return "data:image/svg+xml;base64," + base64.b64encode(_cover_svg(n).encode()).decode()


# ════════════════════════════════════════════════════════════════
#  สไตล์
# ════════════════════════════════════════════════════════════════
def _css() -> None:
    per_card = "\n".join(
        f".st-key-card_{i} {{--accent:{c};}}" for i, c in ACCENTS.items()
    )
    st.markdown(
        f"""
        <style>
          [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{display:none !important;}}
          {per_card}
          [class*="st-key-card_"] {{
            background: var(--panel); border:1px solid var(--line); border-radius:16px;
            padding:1rem 1.2rem 1rem 1rem; position:relative; overflow:hidden; transition: border-color .2s;
          }}
          [class*="st-key-card_"]::before {{
            content:""; position:absolute; inset:0 auto 0 0; width:4px; background:var(--accent); z-index:1;
          }}
          [class*="st-key-card_"]:hover {{border-color:var(--accent);}}
          .st-key-card_5 {{
            background: linear-gradient(135deg, rgba(22,26,54,.98), rgba(44,48,112,.98));
            border-color: rgba(255,179,71,.45);
            padding:1.2rem 1.5rem 1.2rem 1.2rem;
          }}

          .hero {{padding:.4rem 0 1.4rem;}}
          .hero .eyebrow {{display:inline-block; font-size:.78rem; color:var(--amber); border:1px solid rgba(255,179,71,.4);
                          background:rgba(255,179,71,.1); padding:.2rem .7rem; border-radius:999px; margin-bottom:.8rem;}}
          .hero h1 {{font-size:2.8rem; margin:0; line-height:1.1;}}
          .hero h1 b {{color:var(--amber);}}
          .hero p {{color:var(--muted); margin:.6rem 0 0; max-width:62ch;}}

          .cover {{border-radius:12px; overflow:hidden; border:1px solid var(--line); line-height:0;}}
          .cover img {{width:100%; aspect-ratio:16/9; object-fit:cover; display:block;}}
          .st-key-card_5 .cover {{border-color: rgba(255,179,71,.35);}}

          .pnum {{font-family:'Kanit',sans-serif; font-size:.9rem; font-weight:600; color:var(--accent); letter-spacing:.06em;}}
          .ptitle {{font-family:'Kanit',sans-serif; font-size:1.4rem; font-weight:600; margin:.15rem 0 .45rem; line-height:1.25;}}
          .pdesc {{color:var(--muted); font-size:.95rem; margin-bottom:.6rem; max-width:62ch;}}
          .ptags {{margin-bottom:.9rem;}}
          .st-key-card_5 .ptitle {{font-size:1.9rem;}}
          .st-key-card_5 .pdesc {{font-size:1rem; color:#c5c9ec;}}

          [class*="st-key-card_"] a[data-testid="stBaseLinkButton-secondary"],
          [class*="st-key-card_"] button[data-testid="stBaseButton-secondary"],
          [class*="st-key-card_"] [data-testid="stDownloadButton"] button {{
            border-color: var(--line); background: rgba(255,255,255,.03); width:100%;
          }}
          [class*="st-key-card_"] a[data-testid="stBaseLinkButton-secondary"]:hover,
          [class*="st-key-card_"] [data-testid="stDownloadButton"] button:hover {{
            border-color: var(--accent); color: var(--accent);
          }}
          .foot {{color:var(--muted); font-size:.82rem; text-align:center; margin-top:2rem;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
#  ส่วนประกอบการ์ด
# ════════════════════════════════════════════════════════════════
def _cover(n: int, alt: str) -> None:
    st.markdown(
        f'<div class="cover"><img src="{_cover_src(n)}" alt="{esc(alt)}"></div>',
        unsafe_allow_html=True,
    )


def _head(num: str, title: str, desc: str, tags: list[str]) -> None:
    chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in tags)
    st.markdown(
        f'<div class="pnum">ผลงานชิ้นที่ {num}</div><div class="ptitle">{esc(title)}</div>'
        f'<div class="pdesc">{esc(desc)}</div><div class="ptags">{chips}</div>',
        unsafe_allow_html=True,
    )


def _link(label: str, key: str, icon: str) -> None:
    url = LINKS.get(key, "")
    st.link_button(f"{icon}  {label}", url or "https://github.com", disabled=not url, width="stretch")


def _enter_app() -> None:
    st.session_state["view"] = "app"


def _colab_github(colab_key: str, github_key: str) -> None:
    a, b, _ = st.columns([1, 1, 1])
    with a:
        _link("Colab", colab_key, "📓")
    with b:
        _link("GitHub", github_key, "🐙")


def _card(n: int, title: str, desc: str, tags: list[str], actions) -> None:
    with st.container(key=f"card_{n}"):
        left, right = st.columns([2, 3], gap="large", vertical_alignment="center")
        with left:
            _cover(n, title)
        with right:
            _head(str(n), title, desc, tags)
            actions()


# ════════════════════════════════════════════════════════════════
#  หน้าหลัก
# ════════════════════════════════════════════════════════════════
def render() -> None:
    _css()

    st.markdown(
        """
        <div class="hero">
          <span class="eyebrow">ผลงานรายวิชา Advanced Database</span>
          <h1>Portfolio <b>Graph</b> &amp; Recommender</h1>
          <p>รวมผลงาน 5 ชิ้น ตั้งแต่พื้นฐานฐานข้อมูลขั้นสูง Neo4j ไปจนถึงระบบแนะนำเกมที่ใช้งานได้จริง
          เลือกผลงานที่ต้องการดูได้จากการ์ดด้านล่าง</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── ผลงาน 1 ──
    _card(
        1, "Intro of Advanced Database",
        "ปูพื้นฐานฐานข้อมูลขั้นสูง แนวคิดที่ใช้ต่อยอดในผลงานชิ้นถัดไป",
        ["Colab", "Database"],
        lambda: _colab_github("intro_colab", "intro_github"),
    )
    st.write("")

    # ── ผลงาน 2 ──
    def _neo4j_actions() -> None:
        a, b, _ = st.columns([1, 1, 1])
        with a:
            data = _pdf_bytes()
            st.download_button(
                "📄  ดาวน์โหลด", data or b"", file_name=PDF_FILE.name, mime="application/pdf",
                disabled=data is None, key="dl_neo4j_pdf", width="stretch",
            )
        with b:
            _link("GitHub", "neo4j_github", "🐙")

    _card(
        2, "Neo4jGraphDB",
        "บันทึกการทดลอง Neo4j: constraint, ข้อมูลตัวอย่าง, query 1–2 hop และระบบแนะนำชมรม",
        ["Neo4j", "Cypher", "PDF"],
        _neo4j_actions,
    )
    st.write("")

    # ── ผลงาน 3 ──
    _card(
        3, "GameGenresRecommenderSystem",
        "ระบบแนะนำแนวเกมแบบดั้งเดิม วิเคราะห์ข้อมูลและให้คำแนะนำ ก่อนต่อยอดไปสู่ระบบแนะนำเกมด้วยกราฟ Neo4j",
        ["Colab", "Recommender"],
        lambda: _colab_github("recsys_colab", "recsys_github"),
    )
    st.write("")

    # ── ผลงาน 4 ──
    _card(
        4, "GameGenresRecommenderWithNeo4j",
        "ต่อยอดระบบแนะนำแนวเกมให้ดึงความสัมพันธ์จากกราฟ Neo4j",
        ["Colab", "Neo4j", "Recommender"],
        lambda: _colab_github("recsys_neo4j_colab", "recsys_neo4j_github"),
    )
    st.write("")

    # ── ผลงาน 5 : GameGraph (ชิ้นหลัก) ──
    def _gamegraph_actions() -> None:
        a, b = st.columns([2, 1])
        with a:
            st.button("🚀  เข้าสู่ระบบ GameGraph", type="primary", width="stretch",
                      on_click=_enter_app, key="enter_gamegraph")
        with b:
            _link("GitHub", "gamegraph_github", "🐙")

    _card(
        5, "🎮 GameGraph",
        "เว็บระบบแนะนำเกมด้วย Neo4j จัดอันดับจากเพื่อนที่เล่น แนวเกมที่ตรงกัน ความนิยม "
        "และคะแนนรีวิว พร้อมจัดการผู้เล่น เกม และกราฟความสัมพันธ์ครบในที่เดียว",
        ["Streamlit", "Neo4j Aura", "ระบบหลัก"],
        _gamegraph_actions,
    )

    st.markdown(
        f'<div class="foot">{esc(OWNER)} · {esc(STUDENT_ID)} · {esc(SECTION)}</div>',
        unsafe_allow_html=True,
    )
