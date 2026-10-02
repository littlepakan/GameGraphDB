"""หน้าแรก: เลือกผลงานที่ส่งอาจารย์ (5 ชิ้น) — GameGraph คือชิ้นสุดท้ายที่กดเข้าไปใช้งานระบบจริง"""
from __future__ import annotations

import base64
import html
import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

# ════════════════════════════════════════════════════════════════
#  ✏️  แก้ลิงก์ตรงนี้ที่เดียว (เว้นว่าง "" = ปุ่มจะถูกปิดไว้จนกว่าจะใส่ลิงก์)
# ════════════════════════════════════════════════════════════════
LINKS = {
    "intro_colab": "",
    "intro_github": "",
    "neo4j_github": "",
    "recsys_colab": "",
    "recsys_github": "",
    "recsys_neo4j_colab": "",
    "recsys_neo4j_github": "",
    "gamegraph_github": "",
}
BASE_DIR = Path(__file__).parent
PDF_FILE = BASE_DIR / "664245056_Neo4jGraphDB.pdf"

# ชื่อไฟล์รูปปก (ไม่ต้องใส่นามสกุล รองรับ .png .jpg .jpeg .webp) วางไว้โฟลเดอร์เดียวกับ app.py
# ถ้าไม่พบรูป จะแสดงพื้นหลังไล่สีแทนโดยอัตโนมัติ
COVERS = {
    "intro": "cover_intro",
    "neo4j": "cover_neo4j",
    "recsys": "cover_recsys",
    "recsys_neo4j": "cover_recsys_neo4j",
    "gamegraph": "cover_gamegraph",
}
EXTS = (".png", ".jpg", ".jpeg", ".webp")

OWNER = "นายปกานต์ วงษ์ท่าเรือ"
STUDENT_ID = "664245056"
SECTION = "66/44"

AMBER, TEAL, ROSE, VIOLET = "#ffb347", "#37d5c8", "#ff6b8b", "#9b95ff"

esc = html.escape


@st.cache_data(show_spinner=False)
def _pdf_bytes() -> bytes | None:
    return PDF_FILE.read_bytes() if PDF_FILE.exists() else None


@st.cache_data(show_spinner=False)
def _cover_uri(stem: str) -> str | None:
    """หาไฟล์รูปตามชื่อ ย่อขนาดและบีบอัดเป็น JPEG data-URI (หน้าเว็บโหลดเร็ว ไม่ต้องพึ่งไฟล์ static)"""
    for ext in EXTS:
        path = BASE_DIR / f"{stem}{ext}"
        if path.exists():
            img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
            img.thumbnail((1200, 1200), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=85, optimize=True)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return None


def _grad(seed: str) -> str:
    h = sum(ord(c) for c in seed) * 37 % 360
    return f"linear-gradient(135deg,hsl({h} 65% 52%),hsl({(h + 55) % 360} 65% 38%))"


def _css() -> None:
    accents = {1: AMBER, 2: TEAL, 3: ROSE, 4: VIOLET, 5: AMBER}
    per_card = "\n".join(
        f".st-key-card_{i} {{--accent:{c};}}" for i, c in accents.items()
    )
    st.markdown(
        f"""
        <style>
          [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{display:none !important;}}
          {per_card}
          [class*="st-key-card_"] {{
            background: var(--panel); border:1px solid var(--line); border-radius:16px;
            padding:1.2rem 1.3rem 1.1rem; position:relative; overflow:hidden; transition: border-color .2s, transform .2s;
          }}
          [class*="st-key-card_"]::before {{
            content:""; position:absolute; inset:0 0 auto 0; height:3px; background:var(--accent); z-index:2;
          }}
          .pcover {{display:block; width:calc(100% + 2.6rem); margin:-1.2rem -1.3rem .95rem; aspect-ratio:16/9;
                   object-fit:cover; background-size:cover;}}
          .pcover.ph {{display:grid; place-items:center; font-size:2.6rem;}}
          .st-key-card_5 .pcover {{aspect-ratio:21/9;}}
          [class*="st-key-card_"]:hover {{border-color:var(--accent); transform: translateY(-2px);}}
          .st-key-card_5 {{
            background: linear-gradient(135deg, rgba(22,26,54,.98), rgba(44,48,112,.98));
            border-color: rgba(255,179,71,.45);
          }}

          .hero {{padding:.4rem 0 1.4rem;}}
          .hero .eyebrow {{display:inline-block; font-size:.78rem; color:var(--amber); border:1px solid rgba(255,179,71,.4);
                          background:rgba(255,179,71,.1); padding:.2rem .7rem; border-radius:999px; margin-bottom:.8rem;}}
          .hero h1 {{font-size:2.8rem; margin:0; line-height:1.1;}}
          .hero h1 b {{color:var(--amber);}}
          .hero p {{color:var(--muted); margin:.6rem 0 0; max-width:62ch;}}
          .hero .who {{display:flex; flex-wrap:wrap; gap:.4rem .6rem; margin-top:1rem;}}

          .pnum {{font-family:'Kanit',sans-serif; font-size:.9rem; font-weight:600; color:var(--accent); letter-spacing:.06em;}}
          .ptitle {{font-family:'Kanit',sans-serif; font-size:1.3rem; font-weight:600; margin:.15rem 0 .45rem; line-height:1.25;}}
          .pdesc {{color:var(--muted); font-size:.92rem; min-height:4.2em; margin-bottom:.6rem;}}
          .ptags {{margin-bottom:.9rem;}}
          .st-key-card_5 .ptitle {{font-size:1.8rem;}}
          .st-key-card_5 .pdesc {{min-height:0; font-size:1rem; color:#c5c9ec;}}

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


def _head(num: str, title: str, desc: str, tags: list[str], cover: str) -> None:
    chips = "".join(f'<span class="chip">{esc(t)}</span>' for t in tags)
    uri = _cover_uri(COVERS[cover])
    if uri:
        pic = f'<img class="pcover" src="{uri}" alt="{esc(title)}">'
    else:
        pic = f'<div class="pcover ph" style="background:{_grad(title)}">🎮</div>'
    st.markdown(
        f'{pic}<div class="pnum">ผลงานชิ้นที่ {num}</div><div class="ptitle">{esc(title)}</div>'
        f'<div class="pdesc">{esc(desc)}</div><div class="ptags">{chips}</div>',
        unsafe_allow_html=True,
    )


def _link(label: str, key: str, icon: str) -> None:
    url = LINKS.get(key, "")
    st.link_button(f"{icon}  {label}", url or "https://github.com", disabled=not url, width="stretch")


def _enter_app() -> None:
    st.session_state["view"] = "app"


def render() -> None:
    _css()

    st.markdown(
        f"""
        <div class="hero">
          <span class="eyebrow">ผลงานรายวิชา Advanced Database</span>
          <h1>Portfolio <b>Graph</b> &amp; Recommender</h1>
          <p>รวมผลงาน 5 ชิ้น ตั้งแต่พื้นฐานฐานข้อมูลขั้นสูง Neo4j ไปจนถึงระบบแนะนำเกมที่ใช้งานได้จริง
          เลือกผลงานที่ต้องการดูได้จากการ์ดด้านล่าง</p>
          <div class="who"><span class="chip">{esc(OWNER)}</span>
          <span class="chip">รหัส {esc(STUDENT_ID)}</span><span class="chip">{esc(SECTION)}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── แถว 1: ผลงาน 1–3 ──
    c1, c2, c3 = st.columns(3)

    with c1, st.container(key="card_1"):
        _head("1", "Intro of Advanced Database",
              "ปูพื้นฐานฐานข้อมูลขั้นสูง แนวคิดที่ใช้ต่อยอดในผลงานชิ้นถัดไป",
              ["Colab", "Database"], "intro")
        a, b = st.columns(2)
        with a:
            _link("Colab", "intro_colab", "📓")
        with b:
            _link("GitHub", "intro_github", "🐙")

    with c2, st.container(key="card_2"):
        _head("2", "Neo4jGraphDB",
              "บันทึกการทดลอง Neo4j: constraint, ข้อมูลตัวอย่าง, query 1–2 hop และระบบแนะนำชมรม",
              ["Neo4j", "Cypher", "PDF"], "neo4j")
        a, b = st.columns(2)
        with a:
            data = _pdf_bytes()
            st.download_button(
                "📄  ดาวน์โหลด", data or b"", file_name=PDF_FILE.name, mime="application/pdf",
                disabled=data is None, key="dl_neo4j_pdf", width="stretch",
            )
        with b:
            _link("GitHub", "neo4j_github", "🐙")

    with c3, st.container(key="card_3"):
        _head("3", "GameGenresRecommenderSystem",
              "ระบบแนะนำแนวเกมแบบดั้งเดิม วิเคราะห์ข้อมูลและให้คำแนะนำโดยไม่ใช้กราฟ",
              ["Colab", "Recommender"], "recsys")
        a, b = st.columns(2)
        with a:
            _link("Colab", "recsys_colab", "📓")
        with b:
            _link("GitHub", "recsys_github", "🐙")

    st.write("")

    # ── แถว 2: ผลงาน 4 และ GameGraph ──
    c4, c5 = st.columns([1, 2])

    with c4, st.container(key="card_4"):
        _head("4", "GameGenresRecommenderWithNeo4j",
              "ต่อยอดระบบแนะนำแนวเกมให้ดึงความสัมพันธ์จากกราฟ Neo4j",
              ["Colab", "Neo4j", "Recommender"], "recsys_neo4j")
        a, b = st.columns(2)
        with a:
            _link("Colab", "recsys_neo4j_colab", "📓")
        with b:
            _link("GitHub", "recsys_neo4j_github", "🐙")

    with c5, st.container(key="card_5"):
        _head("5", "🎮 GameGraph",
              "เว็บระบบแนะนำเกมด้วย Neo4j จัดอันดับจากเพื่อนที่เล่น แนวเกมที่ตรงกัน ความนิยม "
              "และคะแนนรีวิว พร้อมจัดการผู้เล่น เกม และกราฟความสัมพันธ์ครบในที่เดียว",
              ["Streamlit", "Neo4j Aura", "ระบบหลัก"], "gamegraph")
        a, b = st.columns([2, 1])
        with a:
            st.button("🚀  เข้าสู่ระบบ GameGraph", type="primary", width="stretch",
                      on_click=_enter_app, key="enter_gamegraph")
        with b:
            _link("GitHub", "gamegraph_github", "🐙")

    st.markdown(
        f'<div class="foot">{esc(OWNER)} · {esc(STUDENT_ID)} · {esc(SECTION)}</div>',
        unsafe_allow_html=True,
    )
