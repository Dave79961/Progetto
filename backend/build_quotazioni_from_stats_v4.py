from pathlib import Path
import math
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "app" / "data"
DEST_FILE = DATA_DIR / "quotazioni_serieA_from_stats.csv"
ROLE_MAP = {"P": "P", "D": "D", "C": "C", "A": "A"}


def find_source_file():
    preferred = DATA_DIR / "Statistiche_Fantacalcio_Stagione_2025_26.xlsx"
    if preferred.exists():
        return preferred

    candidates = list(DATA_DIR.glob("*.xlsx"))
    if len(candidates) == 1:
        return candidates[0]

    available = ", ".join(file.name for file in candidates) or "nessun file .xlsx"
    raise FileNotFoundError(f"File Excel trovati in {DATA_DIR}: {available}")


def text(value, default=""):
    if pd.isna(value):
        return default
    return str(value).strip()


def number(value, default=0.0):
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_value(row, *names, default=0.0):
    for name in names:
        if name in row.index:
            return row[name]
    return default


def calculate_price(role, fm, pv, gf, ass):
    base = {"P": 12, "D": 10, "C": 14, "A": 18}[role]
    performance = max(fm - 5.5, 0) * 7
    presence = min(pv, 38) * 0.25
    attack = gf * 2.5 + ass * 1.2
    return max(1, round(base + performance + presence + attack))


def build_csv():
    source_file = find_source_file()
    df = pd.read_excel(source_file,header=1)
    df.columns = [text(column) for column in df.columns]

    needed = {"R", "Nome", "Squadra", "Pv", "Mv", "Fm"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(
            "Colonne essenziali mancanti: " + ", ".join(sorted(missing))
            + " | Colonne trovate: " + ", ".join(df.columns)
        )

    output = []
    for _, row in df.iterrows():
        name = text(get_value(row, "Nome", default=""))
        if not name:
            continue

        role = ROLE_MAP.get(text(get_value(row, "R", default="C")).upper(), "C")
        pv = number(get_value(row, "Pv"))
        mv = number(get_value(row, "Mv"))
        fm = number(get_value(row, "Fm"))
        gf = number(get_value(row, "Gf", "GF"))
        ass = number(get_value(row, "Ass", "AS"))
        amm = number(get_value(row, "Amm", "AMM"))
        esp = number(get_value(row, "Esp", "ESP"))
        price = calculate_price(role, fm, pv, gf, ass)

        output.append({
            "Nome": name,
            "Ruolo": role,
            "Squadra": text(get_value(row, "Squadra", default="")),
            "Lega": "Serie A",
            "Prezzo": price,
            "CostoOfferta": price,
            "Eta": "",
            "ExpectedBonus": round(max(fm - 5.5, 0) + gf * 0.15 + ass * 0.08, 2),
            "ExpectedMalus": round(amm * 0.03 + esp * 0.25, 2),
            "Availability": round(min(max(pv, 0) / 38, 1), 2),
            "ChancesCreated": 0,
            "AssistRate": round(ass / pv, 2) if pv else 0,
            "Presenze": int(pv),
            "MediaVoto": mv,
            "Fantamedia": fm,
            "GolFatti": int(gf),
            "Assist": int(ass),
            "Ammonizioni": int(amm),
            "Espulsioni": int(esp),
        })

    pd.DataFrame(output).to_csv(DEST_FILE, index=False, sep=";", encoding="utf-8-sig")
    print(f"[OK] Excel trovato: {source_file.name}")
    print(f"[OK] Colonne lette: {', '.join(df.columns)}")
    print(f"[OK] Creato: {DEST_FILE}")
    print(f"[OK] Giocatori elaborati: {len(output)}")


if __name__ == "__main__":
    build_csv()