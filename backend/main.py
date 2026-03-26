"""
backend/main.py
───────────────
FastAPI REST API — reads from PostgreSQL and exposes sports data endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras
import os

app = FastAPI(
    title="Sports Realtime Platform API",
    description="REST API for real-time sports statistics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB connection ──────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "sportsdb"),
        user=os.getenv("DB_USER", "sports_user"),
        password=os.getenv("DB_PASSWORD", "sports_pass"),
    )

def query(sql: str, params=None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()

def query_one(sql: str, params=None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchone()
    finally:
        conn.close()

# ── Routes ─────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "Sports Realtime Platform API"}


@app.get("/teams")
def list_teams():
    rows = query("SELECT * FROM teams ORDER BY name")
    return {"teams": [dict(r) for r in rows]}


@app.get("/teams/{team_id}")
def get_team(team_id: int):
    row = query_one("SELECT * FROM teams WHERE id = %s", (team_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    return dict(row)


@app.get("/matches")
def list_matches():
    rows = query("""
        SELECT
            m.id, m.match_id, m.status, m.match_date,
            m.venue, m.competition,
            ht.name AS home_team, ht.short_name AS home_short,
            at.name AS away_team, at.short_name AS away_short,
            ms.home_score, ms.away_score, ms.minute
        FROM matches m
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        LEFT JOIN LATERAL (
            SELECT home_score, away_score, minute
            FROM match_stats
            WHERE match_id = m.id
            ORDER BY minute DESC
            LIMIT 1
        ) ms ON true
        ORDER BY m.match_date DESC
    """)
    return {"matches": [dict(r) for r in rows]}


@app.get("/matches/{match_id}")
def get_match(match_id: int):
    row = query_one("""
        SELECT
            m.id, m.match_id, m.status, m.match_date,
            m.venue, m.competition,
            ht.name AS home_team, ht.short_name AS home_short,
            at.name AS away_team, at.short_name AS away_short
        FROM matches m
        JOIN teams ht ON ht.id = m.home_team_id
        JOIN teams at ON at.id = m.away_team_id
        WHERE m.id = %s
    """, (match_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Match not found")
    return dict(row)


@app.get("/matches/{match_id}/stats")
def get_match_stats(match_id: int):
    rows = query("""
        SELECT * FROM match_stats
        WHERE match_id = %s
        ORDER BY minute ASC
    """, (match_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="No stats found for this match")
    return {"match_id": match_id, "stats": [dict(r) for r in rows]}


@app.get("/matches/{match_id}/players")
def get_match_players(match_id: int):
    rows = query("""
        SELECT
            ps.*,
            p.name AS player_name,
            p.position,
            t.name AS team_name
        FROM player_stats ps
        JOIN players p ON p.id = ps.player_id
        JOIN teams t ON t.id = p.team_id
        WHERE ps.match_id = %s
        ORDER BY ps.minutes_played ASC
    """, (match_id,))
    return {"match_id": match_id, "player_events": [dict(r) for r in rows]}


@app.get("/matches/{match_id}/timeline")
def get_match_timeline(match_id: int):
    """Returns score evolution minute by minute — great for charts."""
    rows = query("""
        SELECT minute, home_score, away_score,
               home_possession, away_possession,
               home_shots, away_shots
        FROM match_stats
        WHERE match_id = %s
        ORDER BY minute ASC
    """, (match_id,))
    return {"match_id": match_id, "timeline": [dict(r) for r in rows]}