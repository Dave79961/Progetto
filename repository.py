import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent.parent / "fanta.db"

def load_players():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row

    try:
        rows = con.execute(
            """
            SELECT
                name,
                role,
                team,
                league,
                price,
                expected_bonus,
                expected_malus,
                availability
            FROM players
            """
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        con.close()