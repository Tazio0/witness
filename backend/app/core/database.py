import sqlite3
import os

# The database file lives in the backend folder
DATABASE_URL = os.getenv("DATABASE_URL", "witness.db")


def get_db():
    """Get a database connection. Always call conn.close() when done."""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Lets us access columns by name
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    conn = get_db()
    cursor = conn.cursor()

    # --- Users table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    UNIQUE NOT NULL,
            password_hash TEXT  NOT NULL,
            username    TEXT    NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Categories table (crime, fire, accident, hazard, etc.) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    UNIQUE NOT NULL,
            icon  TEXT    NOT NULL  -- emoji or icon code for the map pin
        )
    """)

    # --- Reports table ---
    # NOTE: visible = 0 until 5 people report the same incident
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            category_id  INTEGER NOT NULL,
            title        TEXT    NOT NULL,
            description  TEXT,
            latitude     REAL    NOT NULL,
            longitude    REAL    NOT NULL,
            vote_count   INTEGER DEFAULT 1,
            visible      INTEGER DEFAULT 0,  -- 0 = hidden, 1 = shown on map
            severity     TEXT    DEFAULT 'low',  -- low, medium, high
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at   TIMESTAMP,  -- reports expire after 24 hours by default
            FOREIGN KEY (user_id)     REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # --- Votes table: prevents the same user voting on the same report twice ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            report_id INTEGER NOT NULL,
            voted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, report_id),  -- one vote per user per report
            FOREIGN KEY (user_id)   REFERENCES users(id),
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    """)

    # Seed default categories if the table is empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        categories = [
            ("Crime",     "🚨"),
            ("Accident",  "🚗"),
            ("Fire",      "🔥"),
            ("Hazard",    "⚠️"),
            ("Protest",   "📢"),
            ("Flooding",  "💧"),
            ("Load Shedding", "💡"),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, icon) VALUES (?, ?)", categories
        )

    conn.commit()
    conn.close()
    print("✅ Database initialised")
