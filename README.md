# ⚽ Sports Realtime Platform

> End-to-end real-time sports data pipeline — from event generation to interactive dashboard.
> Built with **Python · Apache Kafka · PostgreSQL · FastAPI · Streamlit · Docker**

---

## 🏗️ Architecture

```
Mock Producer
     │  generates match events
     ▼
Apache Kafka  (3 topics)
     │  event streaming
     ▼
Python Consumer
     │  persists to database
     ▼
PostgreSQL
     │  stores all data
     ▼
FastAPI  →  REST endpoints
     │
     ▼
Streamlit Dashboard  →  live analytics
```

### Kafka Topics

| Topic | Description |
|---|---|
| `sports.matches` | Match lifecycle events (start, update, end) |
| `sports.stats` | Per-minute match statistics snapshots |
| `sports.player_events` | Individual player events (goals, cards, shots) |

---

## 🗂️ Project Structure

```
sports-realtime-platform/
├── producer/          # Generates mock match events → Kafka
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── consumer/          # Kafka → PostgreSQL persistence
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── backend/           # FastAPI REST API
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── dashboard/         # Streamlit live dashboard
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   ├── schema.sql     # Full DB schema
│   └── seed.sql       # Initial teams & players
├── infra/             # Cloud / CI configs
├── tests/
├── docker-compose.yml
└── .github/
    └── workflows/
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) + Docker Compose
- Git

### Run locally

```bash
# 1. Clone the repo
git clone https://github.com/LucasCunha00/sports-realtime-platform.git
cd sports-realtime-platform

# 2. Start all services
docker compose up --build

# 3. Watch the pipeline in action
docker logs producer -f
docker logs consumer -f
```

### Services

| Service | URL | Description |
|---|---|---|
| Kafka UI | http://localhost:8081 | Browse Kafka topics & messages |
| PostgreSQL | localhost:5432 | Database (sportsdb) |
| FastAPI Docs | http://localhost:8000/docs | Interactive API documentation |
| Dashboard | http://localhost:8501 | Live sports analytics dashboard |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/teams` | List all teams |
| GET | `/teams/{id}` | Get team details |
| GET | `/matches` | List all matches |
| GET | `/matches/{id}` | Get match details |
| GET | `/matches/{id}/stats` | Full stats per minute |
| GET | `/matches/{id}/players` | Player events *(in progress)* |
| GET | `/matches/{id}/timeline` | Score evolution (for charts) |

---

## 🗃️ Database Schema

```
teams ──────┐
            ├── matches ──── match_stats
players ────┘         └──── player_stats
```

**Tables:** `teams` · `players` · `matches` · `match_stats` · `player_stats`

---

## 📋 Roadmap

- [x] **Fase 1** — Producer → Kafka → Consumer → PostgreSQL
- [x] **Fase 2** — FastAPI REST endpoints
- [x] **Fase 3** — Streamlit live dashboard
- [x] **Fase 4** — Full Docker Compose (all services)
- [ ] **Fase 5** — Cloud deploy (AWS) + CI/CD GitHub Actions

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Event streaming | Apache Kafka |
| Data persistence | PostgreSQL 16 |
| Backend API | FastAPI |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker + Compose |
| Language | Python 3.12 |
| Cloud | AWS *(Fase 5)* |

---

## 📄 License

MIT — feel free to use and adapt.