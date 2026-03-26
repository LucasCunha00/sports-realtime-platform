
CREATE TABLE IF NOT EXISTS teams (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    short_name  VARCHAR(10)  NOT NULL,
    country     VARCHAR(50),
    stadium     VARCHAR(100),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS players (
    id          SERIAL PRIMARY KEY,
    team_id     INT REFERENCES teams(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    position    VARCHAR(30),  -- GK, DEF, MID, FWD
    number      INT,
    nationality VARCHAR(50),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS matches (
    id              SERIAL PRIMARY KEY,
    match_id        VARCHAR(50) UNIQUE NOT NULL,  -- external / mock ID
    home_team_id    INT REFERENCES teams(id),
    away_team_id    INT REFERENCES teams(id),
    status          VARCHAR(20) DEFAULT 'SCHEDULED', -- SCHEDULED, LIVE, FINISHED
    match_date      TIMESTAMP,
    venue           VARCHAR(100),
    competition     VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS match_stats (
    id              SERIAL PRIMARY KEY,
    match_id        INT REFERENCES matches(id) ON DELETE CASCADE,
    home_score      INT DEFAULT 0,
    away_score      INT DEFAULT 0,
    home_possession INT DEFAULT 50,
    away_possession INT DEFAULT 50,
    home_shots      INT DEFAULT 0,
    away_shots      INT DEFAULT 0,
    home_shots_on_target INT DEFAULT 0,
    away_shots_on_target INT DEFAULT 0,
    home_corners    INT DEFAULT 0,
    away_corners    INT DEFAULT 0,
    home_fouls      INT DEFAULT 0,
    away_fouls      INT DEFAULT 0,
    home_yellow_cards INT DEFAULT 0,
    away_yellow_cards INT DEFAULT 0,
    home_red_cards  INT DEFAULT 0,
    away_red_cards  INT DEFAULT 0,
    minute          INT DEFAULT 0,
    recorded_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS player_stats (
    id              SERIAL PRIMARY KEY,
    match_id        INT REFERENCES matches(id) ON DELETE CASCADE,
    player_id       INT REFERENCES players(id) ON DELETE CASCADE,
    goals           INT DEFAULT 0,
    assists         INT DEFAULT 0,
    shots           INT DEFAULT 0,
    passes          INT DEFAULT 0,
    pass_accuracy   FLOAT DEFAULT 0.0,
    minutes_played  INT DEFAULT 0,
    yellow_card     BOOLEAN DEFAULT FALSE,
    red_card        BOOLEAN DEFAULT FALSE,
    recorded_at     TIMESTAMP DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_match_stats_match_id ON match_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_match_id ON player_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player_id ON player_stats(player_id);