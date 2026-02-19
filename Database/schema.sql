-- schema.sql

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    venue TEXT,
    team1 TEXT,
    team2 TEXT,
    toss_winner TEXT,
    toss_decision TEXT,
    result TEXT
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team TEXT
);

CREATE TABLE IF NOT EXISTS innings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    batting_team TEXT,
    FOREIGN KEY (match_id) REFERENCES matches (id)
);

CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    innings_id INTEGER,
    over INTEGER,
    ball INTEGER,
    batsman_id INTEGER,
    bowler_id INTEGER,
    runs_off_bat INTEGER,
    extras INTEGER,
    wide INTEGER DEFAULT 0,
    noball INTEGER DEFAULT 0,
    wicket INTEGER DEFAULT 0,
    wagon_zone TEXT, -- 'cover', 'long_on', etc.
    phase TEXT,      -- 'powerplay', 'middle', 'death'
    is_boundary INTEGER DEFAULT 0,
    is_six INTEGER DEFAULT 0,
    is_dot INTEGER DEFAULT 0,
    FOREIGN KEY (innings_id) REFERENCES innings (id),
    FOREIGN KEY (batsman_id) REFERENCES players (id),
    FOREIGN KEY (bowler_id) REFERENCES players (id)
);