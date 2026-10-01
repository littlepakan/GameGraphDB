from __future__ import annotations

import re
from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


# ───────────────────────── Connection ─────────────────────────
def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "4e237aa6"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    """Create one thread-safe Neo4j Driver for the Streamlit process."""
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    """Execute parameterized Cypher and return rows as dictionaries."""
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def next_id(label: str, prop: str, prefix: str, width: int = 3) -> str:
    """Generate the next free id, e.g. U007, G109, D05."""
    rows = query(f"MATCH (n:{label}) RETURN n.{prop} AS id")
    nums = [int(re.sub(r"\D", "", r["id"]) or 0) for r in rows if r["id"]]
    return f"{prefix}{(max(nums) if nums else 0) + 1:0{width}d}"


# ───────────────────────── Schema & demo data ─────────────────────────
def create_schema() -> None:
    statements = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT game_id_unique IF NOT EXISTS FOR (g:Game) REQUIRE g.game_id IS UNIQUE",
        "CREATE CONSTRAINT developer_id_unique IF NOT EXISTS FOR (d:Developer) REQUIRE d.developer_id IS UNIQUE",
        "CREATE CONSTRAINT genre_name_unique IF NOT EXISTS FOR (gn:Genre) REQUIRE gn.name IS UNIQUE",
    ]
    for stmt in statements:
        query(stmt, write=True)


def clear_all_data() -> None:
    query("MATCH (n) DETACH DELETE n", write=True)


def seed_demo_data() -> None:
    """Idempotent sample dataset: safe to run more than once."""
    create_schema()

    users = [
        {"user_id": "U001", "name": "Anan", "platform": "PC / Steam", "level": 42},
        {"user_id": "U002", "name": "Mali", "platform": "PlayStation 5", "level": 28},
        {"user_id": "U003", "name": "Krit", "platform": "PC / Epic", "level": 55},
        {"user_id": "U004", "name": "Nida", "platform": "Nintendo Switch", "level": 19},
        {"user_id": "U005", "name": "Ploy", "platform": "PC / Steam", "level": 34},
        {"user_id": "U006", "name": "Ton", "platform": "Xbox Series X", "level": 12},
    ]
    games = [
        {"game_id": "G101", "title": "Chronicles of Aetheria", "year": 2025},
        {"game_id": "G102", "title": "CyberPulse 2099", "year": 2026},
        {"game_id": "G103", "title": "Starlight Tactics", "year": 2025},
        {"game_id": "G104", "title": "Realm of Eldoria", "year": 2024},
        {"game_id": "G105", "title": "Neon Shadow: Outlaws", "year": 2026},
        {"game_id": "G106", "title": "Pixel Survival Frontier", "year": 2025},
        {"game_id": "G107", "title": "Vortex Horizon: Apex", "year": 2024},
        {"game_id": "G108", "title": "Mythic Legends: Awakening", "year": 2023},
    ]
    developers = [
        {"developer_id": "D01", "name": "PixelCraft Studios"},
        {"developer_id": "D02", "name": "Aether Interactive"},
        {"developer_id": "D03", "name": "CyberNet Games"},
        {"developer_id": "D04", "name": "MythicForge Entertainment"},
        {"developer_id": "D05", "name": "Other Dev House"},
    ]
    genres = ["Action RPG", "Cyberpunk", "Turn-Based Strategy", "Survival", "Sci-Fi", "Open World", "FPS", "Adventure", "Puzzle", "Simulation", "Bullet Hell", "Platformer", "Horror", "Stealth", "Sandbox"]

    query(
        """
        UNWIND $rows AS row
        MERGE (u:User {user_id: row.user_id})
        SET u.name = row.name, u.platform = row.platform, u.level = row.level
        """,
        {"rows": users}, write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (g:Game {game_id: row.game_id})
        SET g.title = row.title, g.year = row.year
        """,
        {"rows": games}, write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (d:Developer {developer_id: row.developer_id})
        SET d.name = row.name
        """,
        {"rows": developers}, write=True,
    )
    query("UNWIND $rows AS name MERGE (:Genre {name:name})", {"rows": genres}, write=True)

    friendships = [
        ["U001", "U002"], ["U001", "U003"], ["U001", "U004"],
        ["U002", "U005"], ["U003", "U004"], ["U004", "U006"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (a:User {user_id: row[0]}), (b:User {user_id: row[1]})
        WHERE NOT (a)-[:FRIEND_OF]-(b)
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": friendships}, write=True,
    )

    played = [
        {"u": "U001", "g": "G101", "date": "2026-08-01", "rating": 4.5},
        {"u": "U001", "g": "G108", "date": "2026-08-14", "rating": 4.0},
        {"u": "U002", "g": "G103", "date": "2026-08-05", "rating": 5.0},
        {"u": "U002", "g": "G102", "date": "2026-08-18", "rating": 4.5},
        {"u": "U003", "g": "G103", "date": "2026-08-07", "rating": 4.0},
        {"u": "U003", "g": "G104", "date": "2026-08-20", "rating": 5.0},
        {"u": "U004", "g": "G105", "date": "2026-08-09", "rating": 5.0},
        {"u": "U004", "g": "G103", "date": "2026-08-24", "rating": 4.8},
        {"u": "U005", "g": "G107", "date": "2026-08-11", "rating": 4.0},
        {"u": "U006", "g": "G106", "date": "2026-08-12", "rating": 4.2},
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row.u}), (g:Game {game_id: row.g})
        MERGE (u)-[r:PLAYED]->(g)
        SET r.play_date = date(row.date), r.rating = row.rating
        """,
        {"rows": played}, write=True,
    )

    likes_genres = [
        ["U001", "Action RPG"], ["U001", "Open World"],
        ["U002", "Cyberpunk"], ["U002", "Turn-Based Strategy"],
        ["U003", "Turn-Based Strategy"], ["U003", "Open World"],
        ["U004", "Cyberpunk"], ["U004", "Sci-Fi"],
        ["U005", "Survival"], ["U006", "Action RPG"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {user_id: row[0]}), (gn:Genre {name: row[1]})
        MERGE (u)-[:LIKES_GENRE]->(gn)
        """,
        {"rows": likes_genres}, write=True,
    )

    game_genres = [
        ["G101", "Action RPG"], ["G101", "Open World"],
        ["G102", "Cyberpunk"], ["G102", "Sci-Fi"],
        ["G103", "Turn-Based Strategy"], ["G103", "Sci-Fi"],
        ["G104", "Open World"], ["G104", "Action RPG"],
        ["G105", "Cyberpunk"], ["G106", "Survival"],
        ["G107", "Sci-Fi"], ["G108", "Action RPG"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (g:Game {game_id: row[0]}), (gn:Genre {name: row[1]})
        MERGE (g)-[:IN_GENRE]->(gn)
        """,
        {"rows": game_genres}, write=True,
    )

    developers_games = [
        ["D01", "G101"], ["D02", "G102"], ["D03", "G103"], ["D04", "G104"],
        ["D02", "G105"], ["D01", "G106"], ["D03", "G107"], ["D04", "G108"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (d:Developer {developer_id: row[0]}), (g:Game {game_id: row[1]})
        MERGE (d)-[:DEVELOPED]->(g)
        """,
        {"rows": developers_games}, write=True,
    )


# ───────────────────────── Dashboard ─────────────────────────
def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        RETURN COUNT { (:User) } AS users,
               COUNT { (:Game) } AS games,
               COUNT { ()-[:PLAYED]->() } AS plays,
               COUNT { ()-[:FRIEND_OF]->() } AS friendships
        """
    )
    return rows[0] if rows else {"users": 0, "games": 0, "plays": 0, "friendships": 0}


def top_games(limit: int = 8) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (g:Game)
        OPTIONAL MATCH (:User)-[r:PLAYED]->(g)
        RETURN g.title AS title, count(r) AS players, round(coalesce(avg(r.rating), 0.0) * 100) / 100.0 AS avg_rating
        ORDER BY players DESC, avg_rating DESC, title
        LIMIT $limit
        """,
        {"limit": int(limit)},
    )


def genre_stats() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (gn:Genre)
        RETURN gn.name AS name,
               COUNT { (:Game)-[:IN_GENRE]->(gn) } AS games,
               COUNT { (:User)-[:LIKES_GENRE]->(gn) } AS fans
        ORDER BY name
        """
    )


# ───────────────────────── Users ─────────────────────────
def get_users() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)
        RETURN u.user_id AS user_id, u.name AS name, u.platform AS platform, u.level AS level,
               COUNT { (u)-[:PLAYED]->() } AS games,
               COUNT { (u)-[:FRIEND_OF]-() } AS friends
        ORDER BY u.user_id
        """
    )


def get_profile(user_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH (u)-[:LIKES_GENRE]->(gn:Genre)
        WITH u, collect(DISTINCT gn.name) AS interests
        OPTIONAL MATCH (u)-[r:PLAYED]->(g:Game)
        RETURN u.user_id AS user_id, u.name AS name, u.platform AS platform, u.level AS level,
               interests,
               collect(DISTINCT {game_id:g.game_id, title:g.title, rating:r.rating,
                                 play_date:toString(r.play_date)}) AS played
        """,
        {"user_id": user_id},
    )
    if not rows:
        return None
    row = rows[0]
    row["played"] = [x for x in row["played"] if x.get("game_id")]
    return row


def save_user(user_id: str, name: str, platform: str, level: int, interests: list[str]) -> None:
    """Create or update a user, and replace the user's liked genres."""
    query(
        """
        MERGE (u:User {user_id:$user_id})
        SET u.name = $name, u.platform = $platform, u.level = $level
        """,
        {"user_id": user_id, "name": name, "platform": platform, "level": int(level)},
        write=True,
    )
    query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH (u)-[old:LIKES_GENRE]->(g:Genre) WHERE NOT g.name IN $genres
        DELETE old
        WITH DISTINCT u
        UNWIND $genres AS name
        MATCH (gn:Genre {name:name})
        MERGE (u)-[:LIKES_GENRE]->(gn)
        """,
        {"user_id": user_id, "genres": interests},
        write=True,
    )


def delete_user(user_id: str) -> None:
    query("MATCH (u:User {user_id:$id}) DETACH DELETE u", {"id": user_id}, write=True)


def list_friends(user_id: str) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (:User {user_id:$id})-[:FRIEND_OF]-(f:User)
        RETURN DISTINCT f.user_id AS user_id, f.name AS name, f.platform AS platform
        ORDER BY f.user_id
        """,
        {"id": user_id},
    )


def add_friend(a: str, b: str) -> None:
    query(
        """
        MATCH (x:User {user_id:$a}), (y:User {user_id:$b})
        WHERE x <> y AND NOT (x)-[:FRIEND_OF]-(y)
        MERGE (x)-[:FRIEND_OF]->(y)
        """,
        {"a": a, "b": b}, write=True,
    )


def remove_friend(a: str, b: str) -> None:
    query(
        "MATCH (:User {user_id:$a})-[r:FRIEND_OF]-(:User {user_id:$b}) DELETE r",
        {"a": a, "b": b}, write=True,
    )


# ───────────────────────── Games ─────────────────────────
def search_games(keyword: str = "", genre: str | None = None) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (g:Game)
        OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
        OPTIONAL MATCH (g)-[:IN_GENRE]->(gn:Genre)
        WITH g, collect(DISTINCT d.name) AS developers, collect(DISTINCT gn.name) AS genres
        WHERE ($keyword = '' OR toLower(g.title) CONTAINS toLower($keyword)
               OR any(x IN developers WHERE toLower(x) CONTAINS toLower($keyword)))
          AND ($genre = '' OR $genre IN genres)
        RETURN g.game_id AS game_id, g.title AS title, g.year AS year,
               developers, genres,
               COUNT { (:User)-[:PLAYED]->(g) } AS players
        ORDER BY g.title
        """,
        {"keyword": keyword.strip(), "genre": genre or ""},
    )


def get_game_detail(game_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (g:Game {game_id:$id})
        RETURN g.game_id AS game_id, g.title AS title, g.year AS year,
               [(d:Developer)-[:DEVELOPED]->(g) | d.developer_id] AS developer_ids,
               [(g)-[:IN_GENRE]->(gn:Genre) | gn.name] AS genres
        """,
        {"id": game_id},
    )
    return rows[0] if rows else None


def save_game(game_id: str, title: str, year: int | None, developer_ids: list[str], genres: list[str]) -> None:
    """Create or update a game together with its developers and genres."""
    query(
        "MERGE (g:Game {game_id:$id}) SET g.title = $title, g.year = $year",
        {"id": game_id, "title": title, "year": year},
        write=True,
    )
    query(
        """
        MATCH (g:Game {game_id:$id})
        OPTIONAL MATCH (d0:Developer)-[old:DEVELOPED]->(g) WHERE NOT d0.developer_id IN $dids
        DELETE old
        WITH DISTINCT g
        UNWIND $dids AS did
        MATCH (d:Developer {developer_id:did})
        MERGE (d)-[:DEVELOPED]->(g)
        """,
        {"id": game_id, "dids": developer_ids}, write=True,
    )
    query(
        """
        MATCH (g:Game {game_id:$id})
        OPTIONAL MATCH (g)-[old:IN_GENRE]->(g0:Genre) WHERE NOT g0.name IN $genres
        DELETE old
        WITH DISTINCT g
        UNWIND $genres AS name
        MATCH (gn:Genre {name:name})
        MERGE (g)-[:IN_GENRE]->(gn)
        """,
        {"id": game_id, "genres": genres}, write=True,
    )


def delete_game(game_id: str) -> None:
    query("MATCH (g:Game {game_id:$id}) DETACH DELETE g", {"id": game_id}, write=True)


# ───────────────────────── Developers ─────────────────────────
def list_developers() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (d:Developer)
        RETURN d.developer_id AS developer_id, d.name AS name,
               COUNT { (d)-[:DEVELOPED]->() } AS games
        ORDER BY d.developer_id
        """
    )


def save_developer(developer_id: str, name: str) -> None:
    query(
        "MERGE (d:Developer {developer_id:$id}) SET d.name = $name",
        {"id": developer_id, "name": name}, write=True,
    )


def delete_developer(developer_id: str) -> None:
    query("MATCH (d:Developer {developer_id:$id}) DETACH DELETE d", {"id": developer_id}, write=True)


# ───────────────────────── Genres ─────────────────────────
def list_genres() -> list[str]:
    return [row["name"] for row in query("MATCH (gn:Genre) RETURN gn.name AS name ORDER BY gn.name")]


def add_genre(name: str) -> None:
    query("MERGE (:Genre {name:$name})", {"name": name}, write=True)


def rename_genre(old: str, new: str) -> None:
    query("MATCH (gn:Genre {name:$old}) SET gn.name = $new", {"old": old, "new": new}, write=True)


def delete_genre(name: str) -> None:
    query("MATCH (gn:Genre {name:$name}) DETACH DELETE gn", {"name": name}, write=True)


# ───────────────────────── Plays ─────────────────────────
def list_plays(user_id: str = "") -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)-[r:PLAYED]->(g:Game)
        WHERE $user_id = '' OR u.user_id = $user_id
        RETURN u.user_id AS user_id, u.name AS user_name, g.game_id AS game_id, g.title AS title,
               toString(r.play_date) AS play_date, r.rating AS rating
        ORDER BY r.play_date DESC, u.user_id
        """,
        {"user_id": user_id},
    )


def record_play(user_id: str, game_id: str, play_date: str, rating: float | None = None) -> None:
    """Create or update a PLAYED relationship. rating=None removes the rating."""
    query(
        """
        MATCH (u:User {user_id:$user_id}), (g:Game {game_id:$game_id})
        MERGE (u)-[r:PLAYED]->(g)
        SET r.play_date = date($play_date), r.rating = $rating
        """,
        {"user_id": user_id, "game_id": game_id, "play_date": play_date, "rating": rating},
        write=True,
    )


def delete_play(user_id: str, game_id: str) -> None:
    query(
        "MATCH (:User {user_id:$u})-[r:PLAYED]->(:Game {game_id:$g}) DELETE r",
        {"u": user_id, "g": game_id}, write=True,
    )


# ───────────────────────── Recommendations & graph ─────────────────────────
def recommend_games(user_id: str, limit: int = 8) -> list[dict[str, Any]]:
    """Explainable hybrid score for games: friends + genres + popularity + ratings."""
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        MATCH (g:Game)
        WHERE NOT (u)-[:PLAYED]->(g)

        OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:User)-[:PLAYED]->(g)
        WITH u, g, count(DISTINCT f) AS friend_count,
             [x IN collect(DISTINCT f.name) WHERE x IS NOT NULL][0..3] AS friend_names

        OPTIONAL MATCH (u)-[:LIKES_GENRE]->(gn:Genre)<-[:IN_GENRE]-(g)
        WITH g, friend_count, friend_names,
             count(DISTINCT gn) AS genre_matches,
             [x IN collect(DISTINCT gn.name) WHERE x IS NOT NULL] AS matched_genres

        OPTIONAL MATCH (:User)-[pr:PLAYED]->(g)
        WITH g, friend_count, friend_names, genre_matches, matched_genres,
             count(pr) AS popularity,
             avg(pr.rating) AS avg_rating

        WITH g, friend_count, friend_names, genre_matches, matched_genres,
             popularity, coalesce(avg_rating, 0.0) AS avg_rating,
             (friend_count * 3.0) + (genre_matches * 2.0) +
             (popularity * 0.20) + (coalesce(avg_rating, 0.0) * 0.50) AS score
        WHERE friend_count > 0 OR genre_matches > 0 OR popularity > 0

        OPTIONAL MATCH (d:Developer)-[:DEVELOPED]->(g)
        OPTIONAL MATCH (g)-[:IN_GENRE]->(allg:Genre)
        RETURN g.game_id AS game_id, g.title AS title, g.year AS year,
               collect(DISTINCT d.name) AS developers,
               collect(DISTINCT allg.name) AS genres,
               friend_count, friend_names, genre_matches, matched_genres,
               popularity, round(avg_rating * 100) / 100.0 AS avg_rating,
               round(score * 100) / 100.0 AS score
        ORDER BY score DESC, g.title
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": int(limit)},
    )


def graph_neighborhood(user_id: str, limit: int = 60) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|PLAYED|LIKES_GENRE|IN_GENRE|DEVELOPED*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN elementId(s) AS source_id, labels(s)[0] AS source_label,
               coalesce(s.name, s.title, s.user_id, s.game_id) AS source_name,
               type(r) AS relationship,
               elementId(t) AS target_id, labels(t)[0] AS target_label,
               coalesce(t.name, t.title, t.user_id, t.game_id) AS target_name
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": int(limit)},
    )


# ───────────────────────── Images (stored as data-URI on the node) ─────────────────────────
_IMG_KEYS = {"User": "user_id", "Game": "game_id"}


def get_images(label: str) -> dict[str, str]:
    """Return {id: data_uri} for every User/Game that has an image."""
    key = _IMG_KEYS[label]
    rows = query(f"MATCH (n:{label}) WHERE n.image IS NOT NULL RETURN n.{key} AS id, n.image AS image")
    return {r["id"]: r["image"] for r in rows}


def set_image(label: str, item_id: str, data_uri: str) -> None:
    key = _IMG_KEYS[label]
    query(f"MATCH (n:{label} {{{key}:$id}}) SET n.image = $img", {"id": item_id, "img": data_uri}, write=True)


def remove_image(label: str, item_id: str) -> None:
    key = _IMG_KEYS[label]
    query(f"MATCH (n:{label} {{{key}:$id}}) REMOVE n.image", {"id": item_id}, write=True)
