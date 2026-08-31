from pathlib import Path
import csv
import json

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "app" / "data"
SOURCE_FILE = DATA_DIR / "quotazioni_serieA_from_stats.csv"
DEST_FILE = DATA_DIR / "players_stats_test.json"


def number(value, default=0):
    try:
        return float(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def integer(value, default=0):
    return int(number(value, default))


def convert():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"File non trovato: {SOURCE_FILE}")

    players = []
    with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            players.append(
                {
                    "name": row.get("Nome", "").strip(),
                    "role": row.get("Ruolo", "").strip(),
                    "team": row.get("Squadra", "").strip(),
                    "price": integer(row.get("Prezzo")),
                    "expected_bonus": number(row.get("ExpectedBonus")),
                    "expected_malus": number(row.get("ExpectedMalus")),
                    "availability": number(row.get("Availability")),
                    "presenze": integer(row.get("Presenze")),
                    "media_voto": number(row.get("MediaVoto")),
                    "fantamedia": number(row.get("Fantamedia")),
                    "gol_fatti": integer(row.get("GolFatti")),
                    "assist": integer(row.get("Assist")),
                    "ammonizioni": integer(row.get("Ammonizioni")),
                    "espulsioni": integer(row.get("Espulsioni")),
                }
            )

    with DEST_FILE.open("w", encoding="utf-8") as file:
        json.dump(players, file, ensure_ascii=False, indent=2)

    print(f"[OK] Creato: {DEST_FILE}")
    print(f"[OK] Giocatori convertiti: {len(players)}")


if __name__ == "__main__":
    convert()