CREATE TABLE games (
    id INTEGER PRIMARY KEY,
    player_name TEXT,
    pgn_file TEXT,
    blunder_rate FLOAT,
    avg_score FLOAT,
    platform TEXT,  -- Nuevo campo
    date_analyzed TIMESTAMP
);