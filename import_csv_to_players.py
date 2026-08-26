import csv
import json
import os


# Percorsi base rispetto a questo file
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "data", "quotazioni.csv")
JSON_PATH = os.path.join(BASE_DIR, "backend", "app", "players.json")


def import_csv_to_players():
    players = []

    # Apri il CSV con separatore ; e encoding UTF-8
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                player = {
                    "name": row["Nome"],
                    "role": row["Ruolo"],
                    "team": row["Squadra"],
                    "price": int(row["Quotazione"]),
                    "expected_bonus": float(row.get("ExpectedBonus", 0) or 0),
                    "expected_malus": float(row.get("ExpectedMalus", 0) or 0),
                    "availability": float(row.get("Availability", 0) or 0),
                }
                players.append(player)
            except KeyError as e:
                print(f"Colonna mancante nel CSV: {e}")
            except ValueError as e:
                print(f"Errore di conversione per riga {row}: {e}")

    # Scrivi il JSON nel formato usato dal backend
    with open(JSON_PATH, "w", encoding="utf-8") as out:
        json.dump(players, out, ensure_ascii=False, indent=2)

    print(f"Import completato: {len(players)} giocatori scritti in {JSON_PATH}")


if __name__ == "__main__":
    print(f"Leggo il CSV da: {CSV_PATH}")
    print(f"Scrivo il JSON in: {JSON_PATH}")
    import_csv_to_players()