from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


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


def create_schema() -> None:
    statements = [
        "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT game_id_unique IF NOT EXISTS FOR (g:Game) REQUIRE g.game_id IS UNIQUE",
        "CREATE CONSTRAINT developer_id_unique IF NOT EXISTS FOR (d:Developer) REQUIRE d.developer_id IS UNIQUE",
        "CREATE CONSTRAINT genre_name_unique IF NOT EXISTS FOR (gn:Genre) REQUIRE gn.name IS UNIQUE",
    ]
    for stmt in statements:
        query(stmt, write=True)


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

    # ชื่อเกมสมมติ (Fictional Games)
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
    ]

    genres = ["Action RPG", "Cyberpunk", "Turn-Based Strategy", "Survival", "Sci-Fi", "Open World"]

    query(
        """
        UNWIND $rows AS row
        MERGE (u:User {user_id: row.user_id})
        SET u.name = row.name, u.platform = row.platform, u.level = row.level
        """,
        {"rows": users},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (g:Game {game_id: row.game_id})
        SET g.title = row.title, g.year = row.year
        """,
        {"rows": games},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (d:Developer {developer_id: row.developer_id})
        SET d.name = row.name
        """,
        {"rows": developers},
        write=True,
    )
    query(
        "UNWIND $rows AS name MERGE (:Genre {name:name})",
        {"rows": genres},
        write=True,
    )

    friendships = [
        ["U001", "U002"], ["U001", "U003"], ["U001", "U004"],
        ["U002", "U005"], ["U003", "U004"], ["U004", "U006"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (a:User {user_id: row[0]}), (b:User {user_id: row[1]})
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": friendships},
        write=True,
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
        {"rows": played},
        write=True,
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
        {"rows": likes_genres},
        write=True,
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
        {"rows": game_genres},
        write=True,
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
        {"rows": developers_games},
        write=True,
    )


def get_users() -> list[dict[str, Any]]:
    return query("MATCH (u:User) RETURN u.user_id AS user_id, u.name AS name, u.platform AS platform, u.level AS level ORDER BY u.user_id")


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        MATCH (u:User) WITH count(u) AS users
        MATCH (g:Game) WITH users, count(g) AS games
        MATCH ()-[r:PLAYED]->() WITH users, games, count(r) AS plays
        MATCH ()-[f:FRIEND_OF]->()
        RETURN users, games, plays, count(f) AS friendships
        """
    )
    return rows[0] if rows else {"users": 0, "games": 0, "plays": 0, "friendships": 0}


def get_profile(user_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH (u)-[:LIKES_GENRE]->(gn:Genre)
        OPTIONAL MATCH (u)-[:PLAYED]->(g:Game)
        RETURN u.user_id AS user_id, u.name AS name, u.platform AS platform, u.level AS level,
               collect(DISTINCT gn.name) AS interests,
               collect(DISTINCT {game_id:g.game_id, title:g.title}) AS played
        """,
        {"user_id": user_id},
    )
    if not rows:
        return None
    row = rows[0]
    row["played"] = [x for x in row["played"] if x.get("game_id")]
    return row


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
               developers, genres
        ORDER BY g.title
        """,
        {"keyword": keyword.strip(), "genre": genre or ""},
    )


def list_genres() -> list[str]:
    return [row["name"] for row in query("MATCH (gn:Genre) RETURN gn.name AS name ORDER BY gn.name")]


def record_play(user_id: str, game_id: str, play_date: str, rating: float | None = None) -> None:
    query(
        """
        MATCH (u:User {user_id:$user_id}), (g:Game {game_id:$game_id})
        MERGE (u)-[r:PLAYED]->(g)
        SET r.play_date = date($play_date)
        FOREACH (_ IN CASE WHEN $rating IS NULL THEN [] ELSE [1] END | SET r.rating = $rating)
        """,
        {"user_id": user_id, "game_id": game_id, "play_date": play_date, "rating": rating},
        write=True,
    )


def graph_neighborhood(user_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {user_id:$user_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|PLAYED|LIKES_GENRE*1..2]-(x)
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