DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS batting_stats;

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE batting_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    runs INTEGER NOT NULL,
    balls INTEGER NOT NULL,
    fours INTEGER DEFAULT 0,
    sixes INTEGER DEFAULT 0,
    match_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (player_id) REFERENCES players (id)
);