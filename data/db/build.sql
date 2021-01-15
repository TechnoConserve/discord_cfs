CREATE TABLE IF NOT EXISTS guilds (
    GuildID integer PRIMARY KEY,
    Prefix text DEFAULT "!"
);

CREATE TABLE IF NOT EXISTS users (
    UserID integer PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS stations (
    StationID integer PRIMARY KEY,
    StationName text
);

CREATE TABLE IF NOT EXISTS subscriptions (
    UserID integer,
    StationID integer,
    UNIQUE(UserID, StationID)
    FOREIGN KEY(UserID) REFERENCES users(UserID) ON DELETE CASCADE,
    FOREIGN KEY(StationID) REFERENCES stations(StationID) ON DELETE CASCADE
);