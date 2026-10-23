
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Store the database inside the backend folder
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "certificates.db"


def get_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the certificates table if it does not exist."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id TEXT NOT NULL UNIQUE,
                participant_name TEXT NOT NULL,
                event TEXT NOT NULL,
                organization TEXT NOT NULL,
                certificate_date TEXT NOT NULL,
                achievement TEXT NOT NULL,
                generated_at TEXT NOT NULL
            )
        """)


def save_certificate(
    certificate_id,
    name,
    event,
    organization,
    certificate_date,
    achievement
):
    """Save one generated certificate record."""
    generated_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO certificates (
                certificate_id,
                participant_name,
                event,
                organization,
                certificate_date,
                achievement,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            certificate_id,
            name,
            event,
            organization,
            certificate_date,
            achievement,
            generated_at
        ))


def get_all_certificates():
    """Return all saved certificates, newest first."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM certificates
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def get_certificate(certificate_id):
    """Find one certificate using its unique ID."""
    with get_connection() as connection:
        row = connection.execute("""
            SELECT *
            FROM certificates
            WHERE certificate_id = ?
        """, (certificate_id,)).fetchone()

        return dict(row) if row else None


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DB_PATH}")
