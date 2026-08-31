
from pathlib import Path
import csv
import re
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

SOURCE_FILE = BASE_DIR / "data" / "Statistiche_Fantacalcio_Stagione_2026_27.xlsx"

OUTPUT_DIR = BASE_DIR / "data" / "normalized"
OUTPUT_FILE = OUTPUT_DIR / "players_current_2026_27.csv"


def clean_text(value):
    if pd.isna(value):
        return ""

    value = str(value)
    value = value.replace(" ", " ")
    value = value.replace("’", "'")
    value = re.sub(r"s+", " ", value)

    return value.strip()


def clean_name(value):
    value = clean_text(value)
    value = re.sub(r"'+$", "", value)

    return value.strip()


def clean_number(value):
    if pd.isna(value):
        return 0.0

    value = str(value).strip().replace(",", ".")

    if value == "":
        return 0.0

    try:
        return float(value)
    except ValueError:
        return 0.0


def normalize_role(value):
    value = clean_text(value).upper()

    if value.startswith("P"):
        return "P"

    if value.startswith("D"):
        return "D"

    if value.startswith("C"):
        return "C"

    if value.startswith("A"):
        return "A"

    return ""


def find_sheet_and_header(file_path):
    excel = pd.ExcelFile(file_path)

    for sheet_name in excel.sheet_names:
        raw = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=None
        )

        for row_index, row in raw.iterrows():
            values = [
                clean_text(value)
                for value in row.tolist()
            ]

            if (
                "Id" in values
                and "Nome" in values
                and "Squadra" in values
            ):
                return sheet_name, row_index

    raise ValueError(
        "Non trovo l'intestazione del file Excel 2026/27."
    )


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"File non trovato: {SOURCE_FILE}"
        )

    OUTPUT_DIR.mkdir(exist_ok=True)

    sheet_name, header_row = find_sheet_and_header(
        SOURCE_FILE
    )

    data = pd.read_excel(
        SOURCE_FILE,
        sheet_name=sheet_name,
        header=header_row
    )

    data.columns = [
        clean_text(column)
        for column in data.columns
    ]

    rows = []

    for _, row in data.iterrows():
        player_id = pd.to_numeric(
            row.get("Id"),
            errors="coerce"
        )

        role = normalize_role(row.get("R"))
        name = clean_name(row.get("Nome"))
        team = clean_text(row.get("Squadra"))

        if pd.isna(player_id):
            continue

        if name == "" or team == "" or role == "":
            continue

        rows.append({
            "stagione": "2026/27",
            "player_id": int(player_id),
            "nome": name,
            "squadra": team,
            "ruolo": role,
            "ruolo_originale": clean_text(row.get("R")),
            "presenze": clean_number(row.get("Pv")),
            "media_voto": clean_number(row.get("Mv")),
            "fantamedia": clean_number(row.get("Fm")),
            "gol_fatti": clean_number(row.get("Gf")),
            "gol_subiti": clean_number(row.get("Gs")),
            "rigori_segnati": clean_number(row.get("Rp")),
            "rigori_sbagliati": clean_number(row.get("Rc")),
            "assist": clean_number(row.get("Ass")),
            "ammonizioni": clean_number(row.get("Amm")),
            "espulsioni": clean_number(row.get("Esp")),
            "autogol": clean_number(row.get("Au")),
            "disponibile_serie_a": True,
            "stato_dato": "corrente_pre_stagione",
            "file_origine": SOURCE_FILE.name
        })

    fieldnames = [
        "stagione",
        "player_id",
        "nome",
        "squadra",
        "ruolo",
        "ruolo_originale",
        "presenze",
        "media_voto",
        "fantamedia",
        "gol_fatti",
        "gol_subiti",
        "rigori_segnati",
        "rigori_sbagliati",
        "assist",
        "ammonizioni",
        "espulsioni",
        "autogol",
        "disponibile_serie_a",
        "stato_dato",
        "file_origine"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print("CSV corrente creato correttamente.")
    print(f"Giocatori 2026/27: {len(rows)}")
    print(f"File: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()