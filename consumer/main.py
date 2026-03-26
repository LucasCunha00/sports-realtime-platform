"""
consumer/main.py
────────────────
Consumes events from Kafka topics and persists them to PostgreSQL.
Handles three topics: sports.matches | sports.stats | sports.player_events
"""

import json
import time
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CONSUMER] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
KAFKA_BROKER = "kafka:29092"
TOPICS = [
    "sports.matches",
    "sports.stats",
    "sports.player_events",
]

DB_CONFIG = {
    "host":     "postgres",
    "port":     5432,
    "dbname":   "sportsdb",
    "user":     "sports_user",
    "password": "sports_pass",
}

# ── DB connection ──────────────────────────────────────────────────────────────
def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.autocommit = False
            log.info("✅ Connected to PostgreSQL")
            return conn
        except psycopg2.OperationalError as e:
            log.warning("⏳ PostgreSQL not ready (%s). Retrying in 3s…", e)
            time.sleep(3)


# ── Kafka consumer ─────────────────────────────────────────────────────────────
def build_consumer() -> KafkaConsumer:
    while True:
        try:
            consumer = KafkaConsumer(
                *TOPICS,
                bootstrap_servers=KAFKA_BROKER,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="sports-consumer-group",
            )
            log.info("✅ Kafka consumer subscribed to: %s", TOPICS)
            return consumer
        except KafkaError as e:
            log.warning("⏳ Kafka not ready (%s). Retrying in 3s…", e)
            time.sleep(3)


# ── Handlers ───────────────────────────────────────────────────────────────────
def handle_match_event(cur, data: dict):
    """Insert or update a match record."""
    home = data["home_team"]
    away = data["away_team"]

    # Upsert teams
    for team in [home, away]:
        cur.execute("""
            INSERT INTO teams (id, name, short_name, country, stadium)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name,
                    short_name = EXCLUDED.short_name
        """, (team["id"], team["name"], team["short"], "Unknown", "Unknown"))

    # Upsert match
    cur.execute("""
        INSERT INTO matches (match_id, home_team_id, away_team_id, status,
                             match_date, venue, competition)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (match_id) DO UPDATE
            SET status     = EXCLUDED.status,
                updated_at = NOW()
    """, (
        data["match_id"],
        home["id"],
        away["id"],
        data["status"],
        data["timestamp"],
        data["venue"],
        data["competition"],
    ))

    log.info(
        "📝 Match upserted [%s] %s vs %s — %s",
        data["event_type"], home["name"], away["name"], data["status"]
    )


def handle_stats_event(cur, data: dict):
    """Insert a match stats snapshot."""
    # Resolve internal match primary key
    cur.execute("SELECT id FROM matches WHERE match_id = %s", (data["match_id"],))
    row = cur.fetchone()
    if not row:
        log.warning("⚠️  Match %s not found in DB — skipping stats", data["match_id"])
        return

    match_pk = row[0]
    cur.execute("""
        INSERT INTO match_stats (
            match_id,
            home_score, away_score,
            home_possession, away_possession,
            home_shots, away_shots,
            home_shots_on_target, away_shots_on_target,
            home_corners, away_corners,
            home_fouls, away_fouls,
            home_yellow_cards, away_yellow_cards,
            home_red_cards, away_red_cards,
            minute
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        match_pk,
        data["home_score"],    data["away_score"],
        data["home_possession"], data["away_possession"],
        data["home_shots"],    data["away_shots"],
        data["home_shots_on"], data["away_shots_on"],
        data["home_corners"],  data["away_corners"],
        data["home_fouls"],    data["away_fouls"],
        data["home_yellow"],   data["away_yellow"],
        data["home_red"],      data["away_red"],
        data["minute"],
    ))

    log.info(
        "📊 Stats recorded — min %02d | %d-%d | possession %d%%",
        data["minute"], data["home_score"], data["away_score"], data["home_possession"]
    )


def handle_player_event(cur, data: dict):
    """Insert a player event."""
    cur.execute("SELECT id FROM matches WHERE match_id = %s", (data["match_id"],))
    row = cur.fetchone()
    if not row:
        log.warning("⚠️  Match %s not found — skipping player event", data["match_id"])
        return

    match_pk  = row[0]
    player    = data["player"]
    event_type = data["event_type"]

    # Upsert player
    cur.execute("""
        INSERT INTO players (id, team_id, name, position)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name
    """, (player["id"], data["team_id"], player["name"], player["position"]))

    # Map event type to stat columns
    goals        = 1 if event_type == "GOAL" else 0
    shots        = 1 if event_type == "SHOT" else 0
    yellow_card  = event_type == "YELLOW_CARD"
    red_card     = event_type == "RED_CARD"

    cur.execute("""
        INSERT INTO player_stats (
            match_id, player_id, goals, shots,
            yellow_card, red_card, minutes_played
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        match_pk, player["id"],
        goals, shots,
        yellow_card, red_card,
        data["minute"],
    ))

    log.info(
        "🎯 Player event: %s — %s (min %d)",
        event_type, player["name"], data["minute"]
    )


# ── Router ─────────────────────────────────────────────────────────────────────
HANDLERS = {
    "sports.matches":      handle_match_event,
    "sports.stats":        handle_stats_event,
    "sports.player_events": handle_player_event,
}


# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    conn     = get_db_connection()
    consumer = build_consumer()

    log.info("🚀 Consumer running — waiting for events…")

    for message in consumer:
        topic = message.topic
        data  = message.value

        handler = HANDLERS.get(topic)
        if not handler:
            log.warning("No handler for topic: %s", topic)
            continue

        try:
            with conn.cursor() as cur:
                handler(cur, data)
            conn.commit()
        except Exception as e:
            conn.rollback()
            log.error("❌ Error processing message from %s: %s", topic, e)
            log.error("   Payload: %s", json.dumps(data, indent=2))


if __name__ == "__main__":
    main()