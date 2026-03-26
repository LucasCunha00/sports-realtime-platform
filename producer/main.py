"""
producer/main.py
────────────────
Generates realistic mock sports events and publishes them to Kafka.
Simulates live match updates every few seconds.
"""

import json
import time
import random
import logging
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from kafka import KafkaProducer
from kafka.errors import KafkaError

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PRODUCER] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
KAFKA_BROKER   = "kafka:29092"
TOPIC_MATCHES  = "sports.matches"
TOPIC_STATS    = "sports.stats"
TOPIC_PLAYERS  = "sports.player_events"
PUBLISH_INTERVAL = 5  # seconds between updates

# ── Mock data ──────────────────────────────────────────────────────────────────
TEAMS = [
    {"id": 1, "name": "Manchester City",   "short": "MCI"},
    {"id": 2, "name": "Arsenal",           "short": "ARS"},
    {"id": 3, "name": "Real Madrid",       "short": "RMA"},
    {"id": 4, "name": "Barcelona",         "short": "BAR"},
    {"id": 5, "name": "Bayern Munich",     "short": "BAY"},
    {"id": 6, "name": "Borussia Dortmund", "short": "BVB"},
    {"id": 7, "name": "PSG",               "short": "PSG"},
    {"id": 8, "name": "Inter Milan",       "short": "INT"},
]

PLAYERS = {
    1: [
        {"id": 1, "name": "Ederson",         "position": "GK"},
        {"id": 2, "name": "Rúben Dias",      "position": "DEF"},
        {"id": 3, "name": "Rodri",           "position": "MID"},
        {"id": 4, "name": "Kevin De Bruyne", "position": "MID"},
        {"id": 5, "name": "Erling Haaland",  "position": "FWD"},
    ],
    2: [
        {"id": 6,  "name": "David Raya",        "position": "GK"},
        {"id": 7,  "name": "William Saliba",    "position": "DEF"},
        {"id": 8,  "name": "Martin Ødegaard",   "position": "MID"},
        {"id": 9,  "name": "Bukayo Saka",       "position": "FWD"},
        {"id": 10, "name": "Gabriel Martinelli","position": "FWD"},
    ],
    3: [
        {"id": 11, "name": "Thibaut Courtois", "position": "GK"},
        {"id": 12, "name": "Dani Carvajal",    "position": "DEF"},
        {"id": 13, "name": "Luka Modric",      "position": "MID"},
        {"id": 14, "name": "Jude Bellingham",  "position": "MID"},
        {"id": 15, "name": "Vinícius Jr.",     "position": "FWD"},
    ],
    4: [
        {"id": 16, "name": "ter Stegen",         "position": "GK"},
        {"id": 17, "name": "Ronald Araújo",      "position": "DEF"},
        {"id": 18, "name": "Pedri",              "position": "MID"},
        {"id": 19, "name": "Gavi",               "position": "MID"},
        {"id": 20, "name": "Robert Lewandowski", "position": "FWD"},
    ],
}

COMPETITIONS = [
    "UEFA Champions League",
    "Premier League",
    "La Liga",
    "Bundesliga",
]

EVENT_TYPES = ["GOAL", "YELLOW_CARD", "RED_CARD", "SUBSTITUTION", "SHOT", "CORNER"]


# ── Data classes ───────────────────────────────────────────────────────────────
@dataclass
class MatchEvent:
    event_id:    str
    match_id:    str
    event_type:  str            # MATCH_START | MATCH_UPDATE | MATCH_END
    status:      str            # SCHEDULED | LIVE | FINISHED
    home_team:   dict
    away_team:   dict
    competition: str
    venue:       str
    minute:      int
    timestamp:   str


@dataclass
class StatsEvent:
    event_id:         str
    match_id:         str
    minute:           int
    home_score:       int
    away_score:       int
    home_possession:  int
    away_possession:  int
    home_shots:       int
    away_shots:       int
    home_shots_on:    int
    away_shots_on:    int
    home_corners:     int
    away_corners:     int
    home_fouls:       int
    away_fouls:       int
    home_yellow:      int
    away_yellow:      int
    home_red:         int
    away_red:         int
    timestamp:        str


@dataclass
class PlayerEvent:
    event_id:   str
    match_id:   str
    player:     dict
    team_id:    int
    event_type: str   # GOAL | YELLOW_CARD | RED_CARD | SHOT | etc.
    minute:     int
    timestamp:  str


# ── Match state simulator ──────────────────────────────────────────────────────
class MatchSimulator:
    def __init__(self, match_id: str, home: dict, away: dict, competition: str):
        self.match_id    = match_id
        self.home        = home
        self.away        = away
        self.competition = competition
        self.venue       = f"{home['name']} Stadium"
        self.minute      = 0
        self.status      = "LIVE"

        # Running stats
        self.home_score      = 0
        self.away_score      = 0
        self.home_possession = 50
        self.home_shots      = 0
        self.away_shots      = 0
        self.home_shots_on   = 0
        self.away_shots_on   = 0
        self.home_corners    = 0
        self.away_corners    = 0
        self.home_fouls      = 0
        self.away_fouls      = 0
        self.home_yellow     = 0
        self.away_yellow     = 0
        self.home_red        = 0
        self.away_red        = 0

    def tick(self) -> tuple[StatsEvent, PlayerEvent | None]:
        """Advance match by one minute and generate events."""
        self.minute += 1
        if self.minute > 90:
            self.status = "FINISHED"

        # Randomize stats each tick
        self._update_stats()

        stats = self._build_stats_event()
        player_event = self._maybe_player_event()
        return stats, player_event

    def _update_stats(self):
        self.home_possession = random.randint(40, 65)
        if random.random() < 0.3:
            self.home_shots += 1
            if random.random() < 0.4:
                self.home_shots_on += 1
                if random.random() < 0.25:
                    self.home_score += 1
        if random.random() < 0.25:
            self.away_shots += 1
            if random.random() < 0.35:
                self.away_shots_on += 1
                if random.random() < 0.2:
                    self.away_score += 1
        if random.random() < 0.15:
            self.home_corners += 1
        if random.random() < 0.12:
            self.away_corners += 1
        if random.random() < 0.1:
            self.home_fouls += 1
        if random.random() < 0.1:
            self.away_fouls += 1
        if random.random() < 0.03:
            self.home_yellow += 1
        if random.random() < 0.03:
            self.away_yellow += 1

    def _build_stats_event(self) -> StatsEvent:
        return StatsEvent(
            event_id        = str(uuid.uuid4()),
            match_id        = self.match_id,
            minute          = self.minute,
            home_score      = self.home_score,
            away_score      = self.away_score,
            home_possession = self.home_possession,
            away_possession = 100 - self.home_possession,
            home_shots      = self.home_shots,
            away_shots      = self.away_shots,
            home_shots_on   = self.home_shots_on,
            away_shots_on   = self.away_shots_on,
            home_corners    = self.home_corners,
            away_corners    = self.away_corners,
            home_fouls      = self.home_fouls,
            away_fouls      = self.away_fouls,
            home_yellow     = self.home_yellow,
            away_yellow     = self.away_yellow,
            home_red        = self.home_red,
            away_red        = self.away_red,
            timestamp       = datetime.now(timezone.utc).isoformat(),
        )

    def _maybe_player_event(self) -> "PlayerEvent | None":
        if random.random() > 0.2:
            return None

        event_type = random.choice(EVENT_TYPES)
        is_home    = random.random() > 0.5
        team       = self.home if is_home else self.away
        team_id    = team["id"]
        squad      = PLAYERS.get(team_id, [])
        if not squad:
            return None

        player = random.choice(squad)
        return PlayerEvent(
            event_id   = str(uuid.uuid4()),
            match_id   = self.match_id,
            player     = player,
            team_id    = team_id,
            event_type = event_type,
            minute     = self.minute,
            timestamp  = datetime.now(timezone.utc).isoformat(),
        )


# ── Kafka producer ─────────────────────────────────────────────────────────────
def build_producer() -> KafkaProducer:
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
            )
            log.info("✅ Connected to Kafka broker at %s", KAFKA_BROKER)
            return producer
        except KafkaError as e:
            log.warning("⏳ Kafka not ready yet (%s). Retrying in 3s…", e)
            time.sleep(3)


def publish(producer: KafkaProducer, topic: str, payload: dict):
    future = producer.send(topic, value=payload)
    try:
        future.get(timeout=10)
    except KafkaError as e:
        log.error("❌ Failed to publish to %s: %s", topic, e)


# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    producer = build_producer()

    # Pick two random teams for a live match
    home, away = random.sample(TEAMS, 2)
    match_id   = str(uuid.uuid4())
    competition = random.choice(COMPETITIONS)

    simulator = MatchSimulator(match_id, home, away, competition)

    # Publish MATCH_START event
    match_start = MatchEvent(
        event_id   = str(uuid.uuid4()),
        match_id   = match_id,
        event_type = "MATCH_START",
        status     = "LIVE",
        home_team  = home,
        away_team  = away,
        competition= competition,
        venue      = simulator.venue,
        minute     = 0,
        timestamp  = datetime.now(timezone.utc).isoformat(),
    )
    publish(producer, TOPIC_MATCHES, asdict(match_start))
    log.info("🏟️  Match started: %s vs %s [%s]", home["name"], away["name"], competition)

    # Simulate match minute by minute
    while simulator.status == "LIVE":
        stats, player_event = simulator.tick()

        publish(producer, TOPIC_STATS, asdict(stats))
        log.info(
            "⚽ Min %02d | %s %d-%d %s | Possession %d%%-%d%%",
            stats.minute,
            home["short"], stats.home_score,
            stats.away_score, away["short"],
            stats.home_possession, stats.away_possession,
        )

        if player_event:
            publish(producer, TOPIC_PLAYERS, asdict(player_event))
            log.info(
                "🎯 %s — %s (%s) min %d",
                player_event.event_type,
                player_event.player["name"],
                player_event.player["position"],
                player_event.minute,
            )

        time.sleep(PUBLISH_INTERVAL)

    # Publish MATCH_END event
    match_end = MatchEvent(
        event_id   = str(uuid.uuid4()),
        match_id   = match_id,
        event_type = "MATCH_END",
        status     = "FINISHED",
        home_team  = home,
        away_team  = away,
        competition= competition,
        venue      = simulator.venue,
        minute     = 90,
        timestamp  = datetime.now(timezone.utc).isoformat(),
    )
    publish(producer, TOPIC_MATCHES, asdict(match_end))
    log.info(
        "🏁 Match finished: %s %d-%d %s",
        home["name"], simulator.home_score,
        simulator.away_score, away["name"],
    )

    producer.flush()
    producer.close()


if __name__ == "__main__":
    main()