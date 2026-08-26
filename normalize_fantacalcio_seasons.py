from pathlib import Path
import re
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "normalized"

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_ALL = OUTPUT_DIR / "players_normalized.csv"
OUTPUT_CURRENT = OUTPUT_DIR / "players_current_2026_27.csv"


NUMERIC_COLUMNS = {
    "Pv": "presenze",
    "Mv": "media_voto",
    "Fm": "fantamedia",
    "Gf": "gol_fatti",
    "Gs": "gol_subiti",
    "Rp": "rigori_segnati",
    "Rc": "rigori_sbagliati",
    "Ass": "assist",
    "Amm": "ammonizioni",
    "Esp": "espulsioni",
    "Au": "autogol",
}


def clean_text(value):
    if pd.isna(value):
        return ""

    text = str(value)
    text = text.replace(" ", " ")
    text = text.replace("’", "'")
    text = re.sub(r"s+", " ", text)

    return text.strip()


def clean_name(value):
    text = clean_text(value)
    text = re.sub(r"'+$", "", text)

    return text.strip()


def clean_number(value):
    if pd.isna(value):
        return 0.0

    text = str(value).strip()
    text = text.replace(",", ".")

    if text == "":
        return 0.0

    try:
        return float(text)
    except ValueError:
        return 0.0


def extract_season(filename):
    """
    Riconosce:
    2015_16
    2016_17
    2024_25
    2025_26
    2026_27
    """

    filename = str(filename)

    match = re.search(
        r"(20[0-9]{2})[_-]([0-9]{2})",
        filename
    )

    if match is None:
        return None

    first_year = match.group(1)
    second_year = match.group(2)

    return f"{first_year}/{second_year}"


def normalize_role(value):
    text = clean_text(value).upper()

    if text.startswith("P"):
        return "P"

    if text.startswith("D"):
        return "D"

    if text.startswith("C"):
        return "C"

    if text.startswith("A"):
        return "A"

    return ""


def find_valid_sheet(file_path):
    excel = pd.ExcelFile(file_path)

    for sheet_name in excel.sheet_names:
        raw_data = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=None
        )

        for _, row in raw_data.iterrows():
            values = [
                clean_text(value)
                for value in row.tolist()
            ]

            if (
                "Id" in values
                and "Nome" in values
                and "Squadra" in values
            ):
                return sheet_name, len(values)

    return None, None


def find_header_row(file_path, sheet_name):
    raw_data = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=None
    )

    for row_index, row in raw_data.iterrows():
        values = [
            clean_text(value)
            for value in row.tolist()
        ]

        if (
            "Id" in values
            and "Nome" in values
            and "Squadra" in values
        ):
            return row_index

    return None


def read_excel_file(file_path):
    sheet_name, _ = find_valid_sheet(file_path)

    if sheet_name is None:
        raise ValueError(
            f"Nessun foglio valido trovato in {file_path.name}"
        )

    header_row = find_header_row(
        file_path,
        sheet_name
    )

    if header_row is None:
        raise ValueError(
            f"Intestazione non trovata in {file_path.name}"
        )

    data = pd.read_excel(
        file_path,
        sheet_name=sheet_name,
        header=header_row
    )

    data.columns = [
        clean_text(column)
        for column in data.columns
    ]

    return data


def normalize_file(file_path, season):
    data = read_excel_file(file_path)

    required_columns = [
        "Id",
        "R",
        "Nome",
        "Squadra"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{file_path.name}: colonne mancanti: "
            + ", ".join(missing_columns)
        )

    result = pd.DataFrame()

    result["stagione"] = season

    result["player_id"] = pd.to_numeric(
        data["Id"],
        errors="coerce"
    )

    result["nome"] = data["Nome"].map(clean_name)
    result["squadra"] = data["Squadra"].map(clean_text)

    result["ruolo_originale"] = data["R"].map(clean_text)
    result["ruolo"] = data["R"].map(normalize_role)

    for source_column, output_column in NUMERIC_COLUMNS.items():
        if source_column in data.columns:
            result[output_column] = data[
                source_column
            ].map(clean_number)
        else:
            result[output_column] = 0.0

    result["disponibile_serie_a"] = True

    if season == "2026/27":
        result["stato_dato"] = "corrente_pre_stagione"
    else:
        result["stato_dato"] = "storico"

    result["file_origine"] = file_path.name

    result = result.dropna(
        subset=["player_id"]
    )

    result["player_id"] = result[
        "player_id"
    ].astype(int)

    result = result[
        result["nome"] != ""
    ]

    result = result[
        result["squadra"] != ""
    ]

    result = result[
        result["ruolo"].isin(
            ["P", "D", "C", "A"]
        )
    ]

    return result


def choose_files():
    excel_files = sorted(
        DATA_DIR.glob("*.xlsx")
    )

    selected_files = {}

    print()
    print("FILE XLSX TROVATI:")

    for file_path in excel_files:
        print(f"- {file_path.name}")

    for file_path in excel_files:
        season = extract_season(
            file_path.name
        )

        if season is None:
            print(
                "Saltato file senza stagione "
                f"riconoscibile: {file_path.name}"
            )
            continue

        if season not in selected_files:
            selected_files[season] = file_path
            continue

        old_file = selected_files[season]

        old_is_duplicate = "-1" in old_file.stem
        new_is_duplicate = "-1" in file_path.stem

        if old_is_duplicate and not new_is_duplicate:
            selected_files[season] = file_path

    return selected_files


def main():
    selected_files = choose_files()

    if not selected_files:
        raise FileNotFoundError(
            "Nessun Excel con stagione riconosciuta."
        )

    print()
    print("STAGIONI RICONOSCIUTE:")

    for season in sorted(selected_files):
        print(
            f"{season} -> "
            f"{selected_files[season].name}"
        )

    all_data = []

    for season in sorted(selected_files):
        file_path = selected_files[season]

        print()
        print(
            f"Importazione stagione {season}: "
            f"{file_path.name}"
        )

        try:
            normalized = normalize_file(
                file_path,
                season
            )

            all_data.append(normalized)

            print(
                f"Giocatori importati: "
                f"{len(normalized)}"
            )

        except Exception as error:
            print(
                f"ERRORE nel file "
                f"{file_path.name}: {error}"
            )

    if not all_data:
        raise RuntimeError(
            "Nessun file importato correttamente."
        )

    players = pd.concat(
        all_data,
        ignore_index=True
    )

    players = players.drop_duplicates(
        subset=[
            "stagione",
            "player_id"
        ],
        keep="first"
    )

    players = players.sort_values(
        by=[
            "stagione",
            "ruolo",
            "nome"
        ]
    )

    players.to_csv(
        OUTPUT_ALL,
        index=False,
        encoding="utf-8-sig"
    )

    current_players = players[
        players["stagione"] == "2026/27"
    ].copy()

    current_players.to_csv(
        OUTPUT_CURRENT,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 60)
    print("NORMALIZZAZIONE COMPLETATA")
    print("=" * 60)
    print(f"Righe totali: {len(players)}")
    print(f"File completo: {OUTPUT_ALL}")
    print(f"File corrente: {OUTPUT_CURRENT}")
    print("normalizzazione completata senza errori.")
    


if __name__ == "__main__":
    main()