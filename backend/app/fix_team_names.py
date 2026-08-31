from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fantacalcio.db"


TEAM_FIXES = {
    "Udine": "Udinese",
    "Udine ": "Udinese",
    "Udinesi": "Udinese",
    "Froinone": "Frosinone",
    "Frosinoni": "Frosinone",
    "Frosinone ": "Frosinone",
    "Sa-uolo": "Sassuolo",
    "Sasuolo": "Sassuolo",
    "Sassuolo ": "Sassuolo",
    "Juventù": "Juventus",
    "Juventu": "Juventus",
}


PLAYER_FIXES = {
    "Ca Adei": "Casadei",
    "Ca-Adei": "Casadei",
}


def update_table(connection, table_name):
    cursor = connection.cursor()
    team_updates = 0
    player_updates = 0

    for wrong_name, correct_name in TEAM_FIXES.items():
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET squadra = ?
            WHERE squadra = ?
            """,
            (correct_name, wrong_name)
        )

        team_updates += cursor.rowcount

    for wrong_name, correct_name in PLAYER_FIXES.items():
        cursor.execute(
            f"""
            UPDATE {table_name}
            SET nome = ?
            WHERE nome = ?
            """,
            (correct_name, wrong_name)
        )

        player_updates += cursor.rowcount

    return team_updates, player_updates


def main():
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database non trovato: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        current_teams, current_players = update_table(
            connection,
            "current_players"
        )

        history_teams, history_players = update_table(
            connection,
            "player_history"
        )

        connection.commit()

        print()
        print("Correzione database completata.")
        print(
            "Squadre corrette in current_players:",
            current_teams
        )
        print(
            "Giocatori corretti in current_players:",
            current_players
        )
        print(
            "Squadre corrette in player_history:",
            history_teams
        )
        print(
            "Giocatori corretti in player_history:",
            history_players
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
