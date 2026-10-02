# GameGraph — Portfolio Graph & Recommender

ผลงานรายวิชา **Advanced Database** ของ นายปกานต์ วงษ์ท่าเรือ (รหัส 664245056, กลุ่ม 66/44)

รวมผลงาน 5 ชิ้น ตั้งแต่พื้นฐานฐานข้อมูลขั้นสูง → Neo4j และ Cypher → ระบบแนะนำแบบกราฟ → เว็บแอป **GameGraph**
ระบบแนะนำเกมที่พัฒนาด้วย **Streamlit + Neo4j Aura + Cypher** และ deploy ผ่าน **GitHub → Streamlit Community Cloud**

> Repository: <https://github.com/mediuni/GameGraphDB>

---

## 1. ผลงานทั้ง 5 ชิ้น

หน้าแรกของเว็บ (`home.py`) แสดงผลงานเป็นการ์ด 5 ใบ ชิ้นสุดท้ายคือระบบ GameGraph ที่กดเข้าไปใช้งานจริง

| # | ผลงาน | ไฟล์ | เนื้อหา |
|---|-------|------|---------|
| 1 | Intro of Advanced Database | `Week2_664245056.ipynb` | MySQL ผ่าน Python บน Colab: Transaction (ACID), Lost Update vs Atomic UPDATE, Isolation Level (Dirty Read), Deadlock + Retry, Redo Log / WAL, Lab Fake News Report |
| 2 | Neo4jGraphDB | `664245056_Neo4jGraphDB.pdf` | บันทึกการทดลอง Neo4j: Constraint, ข้อมูลตัวอย่าง, query 1–2 hop, ระบบแนะนำหนังสือและชมรมจากเพื่อน |
| 3 | GameGenresRecommenderSystem | `GameGenresRecommenderSystem.ipynb` | ระบบแนะนำแนวเกมแบบกราฟด้วย Python + NetworkX (`User -[:LIKES]-> Genre`) |
| 4 | GameGenresRecommenderWithNeo4j | `664245056_GameGenresRecommenderWithNeo4j.ipynb` | ต่อยอดชิ้นที่ 3 ให้ใช้ Neo4j Aura ผ่าน Python Driver |
| 5 | **GameGraph** | `app.py`, `home.py`, `neo4j_service.py` | เว็บระบบแนะนำเกมด้วย Neo4j แบบครบวงจร (หัวข้อ 2–5) |

### รายละเอียดชิ้นที่ 1–4

**ชิ้นที่ 1 — Intro of Advanced Database** (MySQL)
ทดลองบน Google Colab โดยติดตั้ง MySQL Server และใช้ `mysql-connector-python` พิสูจน์แนวคิดสำคัญ ได้แก่
Atomicity ด้วย `rollback`, Lost Update จาก read-modify-write เทียบกับ `UPDATE ... SET x = x + 1`,
Dirty Read ระหว่าง `READ UNCOMMITTED` กับ `READ COMMITTED`, Deadlock และการ retry ทั้ง transaction พร้อม backoff,
และตรวจปริมาณ Redo Log จาก `Innodb_os_log_written`

**ชิ้นที่ 2 — Neo4jGraphDB** (Cypher)
- สร้าง Constraint ให้ `Student.student_id` และ `Book.book_id`
- สร้างกราฟ Student / Book / Category ด้วย `FRIEND_OF`, `BORROWED {borrow_date}`, `IN_CATEGORY`
- Query 1 hop (เพื่อนของ S001) และ 2 hop (เพื่อนยืมหนังสืออะไร)
- นับคะแนนด้วย `count(DISTINCT friend)` และตัดสิ่งที่ผู้ใช้เคยทำแล้วด้วย `WHERE NOT EXISTS { ... }`
- แบบฝึกหัด School Club Recommendation: `Student -[:MEMBER_OF]-> Club` พร้อมคำอธิบายว่าทำไมระบบแนะนำชมรมอันดับ 1

**ชิ้นที่ 3 — GameGenresRecommenderSystem** (NetworkX)
ผู้ใช้ 10 คน แนวเกม 10 แนว โมเดล `(User)-[:LIKES]->(Genre)`
แนวคิด: แนวเกมที่ผู้ใช้ชอบ → ผู้ใช้อื่นที่ชอบแนวเดียวกัน → แนวเกมอื่นที่คนเหล่านั้นชอบ → แนะนำกลับมา (นับด้วย `Counter`)

**ชิ้นที่ 4 — GameGenresRecommenderWithNeo4j** (Neo4j Python Driver)
ย้ายแนวคิดจากชิ้นที่ 3 ขึ้น Neo4j Aura: เชื่อมต่อด้วย `GraphDatabase.driver`, สร้าง node ด้วย `UNWIND` + `MERGE`,
สร้าง `FRIEND_OF` และ `GENRES_LIKES`, ทำ traversal หลายทอด, aggregation และห่อ query เป็นฟังก์ชัน Python เช่น `recommend_genres(student_id)`

---

## 2. GameGraph — ภาพรวมระบบ

GameGraph แนะนำ **เกม** ให้ผู้เล่น โดยจัดอันดับเกมที่ผู้เล่น *ยังไม่เคยเล่น* และแสดงที่มาของคะแนนทุกส่วน
(Explainable Recommendation) ว่าถูกแนะนำเพราะ

1. เพื่อนของผู้เล่นเคยเล่น
2. แนวเกมตรงกับแนวที่ผู้เล่นชอบ
3. เกมมีผู้เล่นมาก (ความนิยม)
4. เกมมีคะแนนรีวิวเฉลี่ยสูง

### เมนูในระบบ

| เมนู | ความสามารถ |
|------|------------|
| 📊 ภาพรวม | จำนวนผู้เล่น / เกม / ประวัติการเล่น / ความเป็นเพื่อน, กราฟเกมยอดนิยม, แนวเกมที่ผู้เล่นชอบ, โปรไฟล์ผู้เล่น |
| ✨ เกมแนะนำ | จัดอันดับเกมแนะนำ 3–12 อันดับ พร้อมแถบแยกที่มาของคะแนนและข้อความเหตุผล |
| 🎮 เกม | ค้นหา (ชื่อเกม/ค่าย/แนว), เพิ่ม, แก้ไข, ลบเกม และอัปโหลดรูปปก |
| 🧑‍🤝‍🧑 ผู้เล่น | เพิ่ม/แก้ไข/ลบผู้เล่น, แนวเกมที่ชอบ, รูปโปรไฟล์, เพิ่ม/ลบเพื่อน |
| 📝 บันทึกการเล่น | บันทึกว่าใครเล่นเกมอะไร วันที่ และคะแนนรีวิว (1–5) แก้ไข/ลบประวัติ |
| 🏷️ ค่ายและแนวเกม | จัดการ Developer และ Genre |
| 🕸️ กราฟความสัมพันธ์ | วาดเครือข่ายรอบผู้เล่น (เพื่อน, เกม, แนว, ค่าย) ด้วย Graphviz |
| ⚙️ ตั้งค่าระบบ | สร้าง Constraint + Demo Data และล้างข้อมูลทั้งหมด |

---

## 3. โมเดลกราฟ (Property Graph)

```text
(User)-[:FRIEND_OF]-(User)
(User)-[:PLAYED {play_date, rating}]->(Game)
(User)-[:LIKES_GENRE]->(Genre)
(Game)-[:IN_GENRE]->(Genre)
(Developer)-[:DEVELOPED]->(Game)
```

| Label | Key (unique) | Property อื่น |
|-------|--------------|---------------|
| `User` | `user_id` เช่น `U001` | `name`, `platform`, `level`, `image` |
| `Game` | `game_id` เช่น `G101` | `title`, `year`, `image` |
| `Developer` | `developer_id` เช่น `D01` | `name` |
| `Genre` | `name` | — |

- Constraint ทั้ง 4 ตัวถูกสร้างโดย `create_schema()` ตอนกด **สร้าง Constraint + Demo Data**
- `FRIEND_OF` เก็บเป็นเส้นทางเดียว แต่ทุก query ใช้ `-[:FRIEND_OF]-` (ไม่ระบุทิศทาง) เพื่อให้มีความหมายแบบสมมาตร
- รูปผู้เล่น/เกมถูกครอปและย่อ (อวตาร 360×360, ปกเกม 640×360) แล้วเก็บเป็น JPEG data-URI ใน property `image` ของ node

---

## 4. อัลกอริทึมแนะนำ (Hybrid Score)

ฟังก์ชัน `recommend_games()` ใน `neo4j_service.py` คำนวณคะแนนของเกมที่ผู้เล่น**ยังไม่เคยเล่น**:

```text
score = friend_count   * 3.0
      + genre_matches  * 2.0
      + popularity     * 0.20
      + avg_rating     * 0.50
```

| องค์ประกอบ | ความหมาย | เส้นทางในกราฟ |
|-----------|----------|----------------|
| `friend_count` | จำนวนเพื่อนที่เคยเล่นเกมนั้น | `(u)-[:FRIEND_OF]-(f)-[:PLAYED]->(g)` |
| `genre_matches` | จำนวนแนวที่ผู้เล่นชอบและเกมอยู่ในแนวนั้น | `(u)-[:LIKES_GENRE]->(gn)<-[:IN_GENRE]-(g)` |
| `popularity` | จำนวนผู้เล่นทั้งหมดของเกม | `(:User)-[:PLAYED]->(g)` |
| `avg_rating` | คะแนนรีวิวเฉลี่ย (ถ้าไม่มีใช้ 0) | `r.rating` ของ `PLAYED` |

เกมที่ทั้ง 3 ส่วนแรกเป็น 0 จะถูกตัดออก และเรียงตาม `score DESC, title`
สูตรนี้เป็น **heuristic เพื่อการเรียนการสอน** ไม่ใช่โมเดล ML ที่ผ่านการ optimize น้ำหนักสามารถปรับได้ใน Cypher
(ต้องแก้ใน `breakdown()` ของ `app.py` ให้ตรงกันด้วย เพื่อให้แถบแสดงที่มาของคะแนนถูกต้อง)

พัฒนาการจากแนวคิดในชิ้นที่ 2–4: จากการนับ `count(DISTINCT friend)` อย่างเดียว → รวมสัญญาณด้านเนื้อหา (แนวเกม), ความนิยม และรีวิว

---

## 5. โครงสร้างไฟล์

ไฟล์ที่มีใน repository:

```text
GameGraphDB/
├── app.py                                   # UI หลักของ Streamlit (8 เมนู)
├── home.py                                  # หน้าแรก: การ์ดผลงาน 5 ชิ้น
├── neo4j_service.py                         # Database layer: Cypher + Python Driver
├── Week2_664245056.ipynb                    # ผลงานที่ 1
├── 664245056_Neo4jGraphDB.pdf               # ผลงานที่ 2
├── GameGenresRecommenderSystem.ipynb        # ผลงานที่ 3
├── 664245056_GameGenresRecommenderWithNeo4j.ipynb  # ผลงานที่ 4
└── README.md
```

ไฟล์ที่ต้องมีเพิ่มเพื่อรัน/deploy (ยังไม่อยู่ในชุดที่อัปโหลด):

```text
├── requirements.txt          # รายการ dependency (ดูด้านล่าง)
├── .gitignore                # ต้องมี .streamlit/secrets.toml
├── .streamlit/
│   └── secrets.toml          # credential จริง — ห้าม commit
├── assets/covers/            # (ไม่บังคับ) card_1.png … card_5.png รูปปกการ์ดหน้าแรก
└── p.png                     # (ไม่บังคับ) โลโก้ใน sidebar
```

ตัวอย่าง `requirements.txt`

```text
streamlit
neo4j
pandas
Pillow
```

> โค้ดใช้ `width="stretch"` กับปุ่มของ Streamlit ซึ่งต้องใช้ Streamlit รุ่นใหม่ และ query ใช้ `COUNT { }` กับ `elementId()` ซึ่งต้องใช้ **Neo4j 5 ขึ้นไป** (AuraDB ใช้ได้)

หากไม่มีไฟล์ใน `assets/covers/` ระบบจะวาดรูปปกการ์ดเป็น SVG ให้อัตโนมัติ
และหากไม่มี `p.png` จะแสดงไอคอน 🎮 แทนโลโก้

---

## 6. สร้าง Neo4j Aura

1. สร้าง AuraDB instance
2. เก็บ Connection URI, username, password และชื่อ database
3. URI ของ Aura อยู่ในรูป `neo4j+s://xxxxxxxx.databases.neo4j.io`
4. **อย่านำ password ลงในไฟล์ที่ commit ขึ้น GitHub**

---

## 7. รันในเครื่อง

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

สร้างไฟล์ `.streamlit/secrets.toml`

```toml
[neo4j]
uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
username = "neo4j"
password = "YOUR_PASSWORD"
database = "neo4j"
```

จากนั้นรัน

```bash
streamlit run app.py
```

> **ควรระบุ `database` ใน secrets เสมอ** — ถ้าไม่ระบุ `neo4j_service.py` จะใช้ค่าเริ่มต้นเป็นชื่อ database เฉพาะของ instance เดิม (`4e237aa6`)
> ซึ่งจะเชื่อมต่อไม่ได้เมื่อใช้ instance อื่น แนะนำให้เปลี่ยนค่า default ในฟังก์ชัน `_config()` เป็น `"neo4j"`

---

## 8. การใช้งานครั้งแรก

1. เปิดเว็บ จะเห็นหน้าแรกเป็นการ์ดผลงาน 5 ชิ้น
2. กด **🚀 เข้าสู่ระบบ GameGraph** ที่การ์ดใบที่ 5 (ปุ่ม **← กลับหน้าแรก** อยู่ที่ sidebar)
3. ไปที่เมนู **⚙️ ตั้งค่าระบบ** แล้วกด **สร้าง Constraint + Demo Data**
   ระบบใช้ `MERGE` จึงกดซ้ำได้ ไม่สร้าง node ซ้ำจาก key เดิม
   (หมายเหตุ: ความเป็นเพื่อนและ relationship ที่มีอยู่แล้วจะไม่ถูกสร้างซ้ำ)
4. Demo Data ประกอบด้วย ผู้เล่น 6 คน, เกม 8 เกม, ค่ายผู้พัฒนา 5 ค่าย, แนวเกม 15 แนว พร้อมเพื่อน ประวัติการเล่น และแนวที่ชอบ
5. ทดลองเมนู ภาพรวม → เกมแนะนำ → กราฟความสัมพันธ์ แล้วลองเพิ่มเพื่อนหรือบันทึกการเล่นเพื่อดูคำแนะนำเปลี่ยน

**ข้อควรระวัง:** ปุ่มลบทุกปุ่มต้องติ๊กยืนยันก่อน และ `DETACH DELETE` ย้อนกลับไม่ได้
(ลบผู้เล่น = ลบเพื่อน ประวัติการเล่น และรูป, ลบเกม = ลบประวัติการเล่นและรูปของเกมนั้น, ลบค่าย = เกมยังอยู่แต่ไม่มีผู้พัฒนา)

---

## 9. Deploy: GitHub → Streamlit Community Cloud

1. สร้าง GitHub repository แล้ว push ไฟล์ทั้งหมด **ยกเว้น `.streamlit/secrets.toml`**
2. เข้า Streamlit Community Cloud → Create app
3. เลือก repository, branch และ entrypoint = `app.py`
4. ที่ Advanced settings → Secrets ใส่

```toml
[neo4j]
uri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
username = "neo4j"
password = "YOUR_PASSWORD"
database = "neo4j"
```

5. Deploy

ลิงก์ในหน้าแรก (Colab / GitHub ของแต่ละชิ้น) แก้ได้ที่เดียวในตัวแปร `LINKS` ของ `home.py`
หากเว้นค่าเป็น `""` ปุ่มนั้นจะถูกปิดไว้

---

## 10. ประเด็น Graph Database ที่ได้ฝึก

- Node, Label, Property และ Relationship พร้อม Direction
- Constraint และ Unique Key
- `MATCH`, `OPTIONAL MATCH`, `MERGE`, `WITH`, `UNWIND`, `WHERE NOT EXISTS { }`
- Graph traversal 1–2 hop (ผู้เล่น → เพื่อน → เกม) และ variable-length path (`*1..2`)
- Aggregation: `count(DISTINCT ...)`, `avg`, `collect`
- Recommendation จาก topology ของกราฟ + Explainable score
- Parameterized Cypher (ไม่ต่อ string จาก input)
- Python Driver, `execute_query` และ connection pooling ผ่าน `st.cache_resource`
- แยก database layer (`neo4j_service.py`) ออกจาก UI (`app.py`, `home.py`)
- Streamlit UI, cache (`st.cache_data`) และ session state
- Secrets และ cloud deployment

---

## 11. ข้อสังเกตและแนวทางต่อยอด

**ข้อสังเกต**
- Notebook ชิ้นที่ 4 มี URI และ username ของ Aura อยู่ในโค้ด (password ใช้ `getpass`) ก่อนเผยแพร่ควรย้ายไปใช้ secrets หรือ environment variable และ rotate credential หากเคยเปิดเผยแล้ว
- รูปที่เก็บเป็น data-URI ใน node ทำให้ไฟล์ใหญ่ขึ้นและเพิ่มขนาดฐานข้อมูล เหมาะกับงานเรียน หากใช้จริงควรเก็บไฟล์ภายนอกแล้วเก็บเฉพาะ URL
- `next_id()` สร้างรหัสถัดไปจากค่ามากที่สุดที่มีอยู่ หากมีหลายคนเพิ่มพร้อมกัน อาจชนกันได้ (Unique Constraint จะป้องกันข้อมูลซ้ำ)
- ระบบยังไม่มีการ Login

**แนวทางต่อยอด**
Login, Wishlist/Favorite, collaborative filtering, Graph Data Science (node similarity, PageRank, community detection),
ปรับน้ำหนักคะแนนอัตโนมัติ และประเมินผลด้วย Precision@K / Recall@K

---

**จัดทำโดย** นายปกานต์ วงษ์ท่าเรือ · 664245056 · 66/44
