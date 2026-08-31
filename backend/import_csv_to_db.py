import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "app" / "data" / "quotazioni_serieA.csv"
DB_FILE = BASE_DIR / "fanta.db"

REQUIRED_COLUMNS = {
    "Nome",
    "Ruolo",
    "Squadra",
    "Lega",
    "Prezzo",
    "ExpectedBonus",
    "ExpectedMalus",
}

ROLE_PRICES = {
    "P": 20,
    "D": 18,
    "C": 25,
    "A": 30,
}


def to_int(value, default=0):
    try:
        return int(float((value or "").strip()))
    except ValueError:
        return default


def to_float(value, default=0.0):
    try:
        return float((value or "").strip().replace(",", "."))
    except ValueError:
        return default


def normalize_role(value):
    role = (value or "").strip().upper()

    mapping = {
        "G": "P",
        "P": "P",
        "D": "D",
        "M": "C",
        "C": "C",
        "F": "A",
        "A": "A",
    }

    return mapping.get(role, "C")


def load_rows():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV non trovato: {CSV_FILE}")

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")

        if not reader.fieldnames:
            raise ValueError("Il CSV non contiene intestazioni.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            columns = ", ".join(sorted(missing))
            raise ValueError(f"Colonne mancanti nel CSV: {columns}")

        players = []

        for line_number, row in enumerate(reader, start=2):
            name = (row.get("Nome") or "").strip()

            if not name:
                print(f"[AVVISO] Riga {line_number} saltata: nome mancante.")
                continue

            role = normalize_role(row.get("Ruolo"))
            price = to_int(row.get("Prezzo"), ROLE_PRICES[role])

            players.append(
                (
                    name,
                    role,
                    (row.get("Squadra") or "").strip(),
                    (row.get("Lega") or "Serie A").strip(),
                    price,
                    to_float(row.get("ExpectedBonus")),
                    to_float(row.get("ExpectedMalus")),
                    to_float(row.get("Availability"), 1.0),
                )
            )

    return players


def create_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            team TEXT,
            league TEXT,
            price INTEGER NOT NULL,
            expected_bonus REAL NOT NULL DEFAULT 0,
            expected_malus REAL NOT NULL DEFAULT 0,
            availability REAL NOT NULL DEFAULT 1
        )
        """
    )


def import_players():
    players = load_rows()

    if not players:
        raise ValueError("Nessun giocatore valido trovato nel CSV.")

    with sqlite3.connect(DB_FILE) as connection:
        create_table(connection)

        connection.execute("DELETE FROM players")

        connection.executemany(
            """
            INSERT INTO players (
                name,
                role,
                team,
                league,
                price,
                expected_bonus,
                expected_malus,
                availability
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            players,
        )

        count = connection.execute(
            "SELECT COUNT(*) FROM players"
        ).fetchone()[0]

    print(f"[OK] Database aggiornato: {count} giocatori importati.")
    print(f"[INFO] CSV usato: {CSV_FILE}")
    print(f"[INFO] Database: {DB_FILE}")


if __name__ == "__main__":
    try:
        import_players()
    except Exception as error:
        print(f"[ERRORE] {error}")
