from pathlib import Path
import csv
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "normalized"
DATABASE_PATH = BASE_DIR / "fantacalcio.db"

HISTORY_FILE = DATA_DIR / "players_normalized.csv"
CURRENT_FILE = DATA_DIR / "players_current_2026_27.csv"


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def read_csv(file_path):
    with open(
        file_path,
        mode="r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def create_tables(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stagione TEXT NOT NULL,
            player_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            squadra TEXT NOT NULL,
            ruolo TEXT NOT NULL,
            ruolo_originale TEXT,
            presenze INTEGER DEFAULT 0,
            media_voto REAL DEFAULT 0,
            fantamedia REAL DEFAULT 0,
            gol_fatti INTEGER DEFAULT 0,
            gol_subiti INTEGER DEFAULT 0,
            rigori_segnati INTEGER DEFAULT 0,
            rigori_sbagliati INTEGER DEFAULT 0,
            assist INTEGER DEFAULT 0,
            ammonizioni INTEGER DEFAULT 0,
            espulsioni INTEGER DEFAULT 0,
            autogol INTEGER DEFAULT 0,
            disponibile_serie_a INTEGER DEFAULT 1,
            stato_dato TEXT,
            file_origine TEXT,
            UNIQUE(stagione, player_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS current_players (
            player_id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            squadra TEXT NOT NULL,
            ruolo TEXT NOT NULL,
            ruolo_originale TEXT,
            presenze INTEGER DEFAULT 0,
            media_voto REAL DEFAULT 0,
            fantamedia REAL DEFAULT 0,
            gol_fatti INTEGER DEFAULT 0,
            gol_subiti INTEGER DEFAULT 0,
            rigori_segnati INTEGER DEFAULT 0,
            rigori_sbagliati INTEGER DEFAULT 0,
            assist INTEGER DEFAULT 0,
            ammonizioni INTEGER DEFAULT 0,
            espulsioni INTEGER DEFAULT 0,
            autogol INTEGER DEFAULT 0,
            disponibile_serie_a INTEGER DEFAULT 1,
            stato_dato TEXT,
            file_origine TEXT
        )
    """)

    connection.commit()


def import_history(connection, rows):
    cursor = connection.cursor()

    cursor.execute("DELETE FROM player_history")

    for row in rows:
        cursor.execute("""
            INSERT INTO player_history (
                stagione,
                player_id,
                nome,
                squadra,
                ruolo,
                ruolo_originale,
                presenze,
                media_voto,
                fantamedia,
                gol_fatti,
                gol_subiti,
                rigori_segnati,
                rigori_sbagliati,
                assist,
                ammonizioni,
                espulsioni,
                autogol,
                disponibile_serie_a,
                stato_dato,
                file_origine
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row.get("stagione", ""),
            to_int(row.get("player_id")),
            row.get("nome", ""),
            row.get("squadra", ""),
            row.get("ruolo", ""),
            row.get("ruolo_originale", ""),
            to_int(row.get("presenze")),
            to_float(row.get("media_voto")),
            to_float(row.get("fantamedia")),
            to_int(row.get("gol_fatti")),
            to_int(row.get("gol_subiti")),
            to_int(row.get("rigori_segnati")),
            to_int(row.get("rigori_sbagliati")),
            to_int(row.get("assist")),
            to_int(row.get("ammonizioni")),
            to_int(row.get("espulsioni")),
            to_int(row.get("autogol")),
            1 if row.get("disponibile_serie_a") == "True" else 0,
            row.get("stato_dato", ""),
            row.get("file_origine", "")
        ))

    connection.commit()


def import_current_players(connection, rows):
    cursor = connection.cursor()

    cursor.execute("DELETE FROM current_players")

    for row in rows:
        cursor.execute("""
            INSERT INTO current_players (
                player_id,
                nome,
                squadra,
                ruolo,
                ruolo_originale,
                presenze,
                media_voto,
                fantamedia,
                gol_fatti,
                gol_subiti,
                rigori_segnati,
                rigori_sbagliati,
                assist,
                ammonizioni,
                espulsioni,
                autogol,
                disponibile_serie_a,
                stato_dato,
                file_origine
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            to_int(row.get("player_id")),
            row.get("nome", ""),
            row.get("squadra", ""),
            row.get("ruolo", ""),
            row.get("ruolo_originale", ""),
            to_int(row.get("presenze")),
            to_float(row.get("media_voto")),
            to_float(row.get("fantamedia")),
            to_int(row.get("gol_fatti")),
            to_int(row.get("gol_subiti")),
            to_int(row.get("rigori_segnati")),
            to_int(row.get("rigori_sbagliati")),
            to_int(row.get("assist")),
            to_int(row.get("ammonizioni")),
            to_int(row.get("espulsioni")),
            to_int(row.get("autogol")),
            1 if row.get("disponibile_serie_a") == "True" else 0,
            row.get("stato_dato", ""),
            row.get("file_origine", "")
        ))

    connection.commit()


def count_rows(connection, table_name):
    cursor = connection.cursor()

    cursor.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    )

    return cursor.fetchone()[0]


def main():
    if not HISTORY_FILE.exists():
        raise FileNotFoundError(
            f"File storico non trovato: {HISTORY_FILE}"
        )

    if not CURRENT_FILE.exists():
        raise FileNotFoundError(
            f"File corrente non trovato: {CURRENT_FILE}"
        )

    history_rows = read_csv(HISTORY_FILE)
    current_rows = read_csv(CURRENT_FILE)

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        create_tables(connection)

        import_history(
            connection,
            history_rows
        )

        import_current_players(
            connection,
            current_rows
        )

        history_count = count_rows(
            connection,
            "player_history"
        )

        current_count = count_rows(
            connection,
            "current_players"
        )

        print()
        print("=" * 60)
        print("IMPORTAZIONE DATABASE COMPLETATA")
        print("=" * 60)
        print(f"Archivio storico importato: {history_count} righe")
        print(f"Giocatori 2026/27 importati: {current_count} righe")
        print(f"Database: {DATABASE_PATH}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
