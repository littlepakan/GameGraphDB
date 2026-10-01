from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from neo4j_service import (
    get_dashboard_metrics,
    get_profile,
    get_users,
    graph_neighborhood,
    list_genres,
    ping,
    recommend_games,
    record_play,
    search_games,
    seed_demo_data,
)

st.set_page_config(
    page_title="GameGraph Recommender",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #1e1b4b 0%, #312e81 55%, #4c1d95 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .game-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px; margin-bottom: .75rem;
      }
      .score-pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        background:#6d28d9; color:white; font-size:.8rem; font-weight:700;
      }
      .muted {opacity:.72; font-size:.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ให้นำค่าด้านบนไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def user_selector(key: str = "user") -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีข้อมูลผู้ใช้ กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง")
        st.stop()
    labels = {f"{x['user_id']} — {x['name']} ({x['platform']})": x["user_id"] for x in users}
    chosen = st.selectbox("เลือกผู้ใช้", list(labels), key=key)
    return labels[chosen]


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count", 0):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนเคยเล่น" + (f" ({friends})" if friends else ""))
    if row.get("genre_matches", 0):
        genres = ", ".join(row.get("matched_genres") or [])
        parts.append(f"ตรงกับแนวเกมที่ชอบ {row['genre_matches']} แนว" + (f" ({genres})" if genres else ""))
    if row.get("popularity", 0):
        parts.append(f"มีผู้เล่นแล้ว {row['popularity']} คน")
    if row.get("avg_rating", 0):
        parts.append(f"คะแนนรีวิวเฉลี่ย {row['avg_rating']:.2f}/5")
    return " • ".join(parts) or "แนะนำจากข้อมูลความนิยมโดยรวม"


require_connection()

with st.sidebar:
    st.image("kairung99.jpg", width=100)       
    st.markdown("## 🎮 GameGraph")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Game Search", "Play / Rate Game", "Graph Explorer", "Admin / Setup"],
    )
    st.divider()
    st.caption("Graph Database Project — Game Recommendation System")


st.markdown(
    """
    <div class="hero">
      <h1>🎮 GameGraph Recommendation System</h1>
      <p>ระบบแนะนำแนวเกมพร้อมชื่อเกมสมมติด้วย Graph Database พร้อมระบบอธิบายเหตุผลของคำแนะนำ</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m.get("users", 0))
    c2.metric("Games", m.get("games", 0))
    c3.metric("Played relationships", m.get("plays", 0))
    c4.metric("Friend relationships", m.get("friendships", 0))

    st.divider()
    user_id = user_selector("dash_user")
    profile = get_profile(user_id)
    
    if profile:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f"### {profile['name']}")
            st.write(f"**รหัส:** {profile['user_id']}")
            st.write(f"**แพลตฟอร์มหลัก:** {profile['platform']}")
            st.write(f"**เลเวล:** {profile['level']}")
            st.write("**แนวเกมที่สนใจ:** " + (", ".join(profile["interests"]) or "ยังไม่ได้ระบุ"))
        with right:
            st.markdown("### ประวัติการเล่นเกม")
            if profile["played"]:
                st.dataframe(pd.DataFrame(profile["played"]), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติการเล่นเกม")

elif page == "Recommendations":
    st.subheader("✨ เกมที่แนะนำสำหรับคุณ")
    user_id = user_selector("rec_user")
    top_n = st.slider("จำนวนคำแนะนำ", 3, 12, 6)
    rows = recommend_games(user_id, top_n)

    st.caption("สูตรคำนวณคะแนน = เพื่อนเล่น × 3 + แนวเกมตรงกัน × 2 + จำนวนผู้เล่น × 0.20 + คะแนนเฉลี่ย × 0.50")
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    for i, row in enumerate(rows, start=1):
        developers = ", ".join(row.get("developers") or []) or "ไม่ระบุผู้พัฒนา"
        genres = ", ".join(row.get("genres") or []) or "ไม่ระบุแนวเกม"
        st.markdown(
            f"""
            <div class="game-card">
              <span class="score-pill">#{i} · score {row['score']:.2f}</span>
              <h3 style="margin:.55rem 0 .2rem 0">{row['title']}</h3>
              <div class="muted">{row['game_id']} · ค่าย: {developers} · แนว: {genres}</div>
              <p><b>เหตุผล:</b> {explain_reason(row)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif page == "Game Search":
    st.subheader("🔎 ค้นหาเกม")
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("ชื่อเกมหรือค่ายผู้พัฒนา", placeholder="เช่น CyberPulse, Aether, PixelCraft")
    genres = [""] + list_genres()
    genre = c2.selectbox("แนวเกม", genres, format_func=lambda x: "ทุกแนวเกม" if x == "" else x)
    rows = search_games(keyword, genre)
    st.write(f"พบ {len(rows)} รายการ")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Play / Rate Game":
    st.subheader("📝 บันทึกการเล่นเกมและให้คะแนน")
    user_id = user_selector("play_user")
    games = search_games()
    if not games:
        st.info("ยังไม่มีข้อมูลเกมในระบบ")
        st.stop()
    game_labels = {f"{g['game_id']} — {g['title']}": g["game_id"] for g in games}
    selected = st.selectbox("เลือกเกม", list(game_labels))
    play_date = st.date_input("วันที่เล่น", value=date.today())
    use_rating = st.checkbox("ให้คะแนนรีวิวด้วย")
    rating = st.slider("คะแนนรีวิว", 1.0, 5.0, 4.0, 0.5, disabled=not use_rating)
    if st.button("บันทึกข้อมูล", type="primary", use_container_width=True):
        record_play(user_id, game_labels[selected], play_date.isoformat(), rating if use_rating else None)
        st.success("บันทึกความสัมพันธ์ PLAYED เรียบร้อยแล้ว")

elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    user_id = user_selector("graph_user")
    rows = graph_neighborhood(user_id)
    if not rows:
        st.info("ยังไม่มี neighborhood graph")
    else:
        dot = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded,filled", fillcolor="#f8fafc"];']
        seen_nodes = set()
        for r in rows:
            for nid, label, name in [
                (r["source_id"], r["source_label"], r["source_name"]),
                (r["target_id"], r["target_label"], r["target_name"]),
            ]:
                if nid not in seen_nodes:
                    safe_name = str(name).replace('"', "'")
                    dot.append(f'"{nid}" [label="{safe_name}\\n:{label}"];')
                    seen_nodes.add(nid)
            dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}"];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)
        with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Admin / Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.warning("ปุ่มนี้ไม่ลบข้อมูลเดิม และใช้ MERGE จึงสามารถกดซ้ำได้ปลอดภัย")
    st.markdown(
        """
        **Graph Schema (ระบบแนะนำเกม):**
        - `(:User)-[:FRIEND_OF]-(:User)`
        - `(:User)-[:PLAYED {play_date, rating}]->(:Game)`
        - `(:User)-[:LIKES_GENRE]->(:Genre)`
        - `(:Game)-[:IN_GENRE]->(:Genre)`
        - `(:Developer)-[:DEVELOPED]->(:Game)`
        """
    )
    if st.button("สร้าง Constraint + Demo Data", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างข้อมูลเกมและผู้ใช้..."):
            seed_demo_data()
        st.success("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")
        st.rerun()  