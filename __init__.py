from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import re
import sqlite3
import unicodedata


app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    },
)


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fantacalcio.db"


OFFICIAL_TEAMS = {
    "atalanta": "Atalanta",
    "bologna": "Bologna",
    "cagliari": "Cagliari",
    "como": "Como",
    "fiorentina": "Fiorentina",
    "frosinone": "Frosinone",
    "genoa": "Genoa",
    "inter": "Inter",
    "juventus": "Juventus",
    "lazio": "Lazio",
    "lecce": "Lecce",
    "milan": "Milan",
    "monza": "Monza",
    "napoli": "Napoli",
    "parma": "Parma",
    "roma": "Roma",
    "sassuolo": "Sassuolo",
    "torino": "Torino",
    "udinese": "Udinese",
    "venezia": "Venezia",
}


TEAM_ALIASES = {
    "froinone": "Frosinone",
    "frosinoni": "Frosinone",
    "frosinone": "Frosinone",
    "udine": "Udinese",
    "udinese": "Udinese",
    "sassuolo": "Sassuolo",
    "saspaziouolo": "Sassuolo",
    "saspazioulo": "Sassuolo",
    "saspaziouolo": "Sassuolo",
    "juve": "Juventus",
    "juventu": "Juventus",
    "juventus": "Juventus",
}


PLAYER_ALIASES = {
    "caadei": "Casadei",
    "casadei": "Casadei",
}


def clean_text(value):
    if value is None:
        return ""

    text = str(value)
    text = text.replace(" ", " ")
    text = text.replace("’", "'")
    text = re.sub(r"s+", " ", text)

    return text.strip()


def text_key(value):
    text = clean_text(value).lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )

    text = re.sub(
        r"[^a-z0-9]",
        "",
        text
    )

    return text


def clean_team(value):
    team = clean_text(value)
    key = text_key(team)

    if key in OFFICIAL_TEAMS:
        return OFFICIAL_TEAMS[key]

    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]

    return team


def clean_player_name(value):
    name = clean_text(value)
    name = re.sub(r"'+$", "", name)

    key = text_key(name)

    if key in PLAYER_ALIASES:
        return PLAYER_ALIASES[key]

    return name


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def player_to_dict(row):
    player = dict(row)

    player["nome"] = clean_player_name(
        player.get("nome")
    )

    player["squadra"] = clean_team(
        player.get("squadra")
    )

    player["role"] = player.pop("ruolo", "")
    player["team"] = player.pop("squadra", "")
    player["name"] = player.pop("nome", "")

    player["price"] = round(
        max(
            1,
            float(player.get("fantamedia", 0)) * 10
        ),
        1
    )

    player["availability"] = min(
        10,
        round(
            float(player.get("presenze", 0)) / 4,
            1
        )
    )

    player["expected_bonus"] = round(
        (
            float(player.get("gol_fatti", 0)) * 3
            + float(player.get("assist", 0))
            + float(player.get("rigori_segnati", 0)) * 3
        ) / 10,
        2
    )

    player["expected_malus"] = round(
        (
            float(player.get("ammonizioni", 0)) * 0.5
            + float(player.get("espulsioni", 0))
            + float(player.get("autogol", 0)) * 2
            + float(player.get("rigori_sbagliati", 0)) * 3
        ) / 10,
        2
    )

    return player


def ranking_key(player):
    return (
        -player.get("expected_bonus", 0),
        player.get("expected_malus", 0),
        -player.get("fantamedia", 0),
        -player.get("presenze", 0),
    )


def market_score(player):
    return (
        player.get("expected_bonus", 0)
        - player.get("expected_malus", 0)
        + (player.get("fantamedia", 0) - 6) * 2
        + player.get("availability", 0) * 0.4
    )


def load_current_players(role=None, team=None, search=None):
    query = """
        SELECT *
        FROM current_players
        WHERE 1 = 1
    """

    parameters = []

    if role:
        query += " AND ruolo = ?"
        parameters.append(role.upper())

    if team:
        query += " AND LOWER(squadra) = ?"
        parameters.append(team.lower())

    if search:
        query += " AND LOWER(nome) LIKE ?"
        parameters.append(
            f"%{search.lower()}%"
        )

    query += " ORDER BY ruolo, nome"

    connection = get_connection()

    try:
        rows = connection.execute(
            query,
            parameters
        ).fetchall()

        return [
            player_to_dict(row)
            for row in rows
        ]
    finally:
        connection.close()


@app.route("/api/health")
def health_check():
    connection = get_connection()

    try:
        current_count = connection.execute(
            "SELECT COUNT(*) FROM current_players"
        ).fetchone()[0]

        history_count = connection.execute(
            "SELECT COUNT(*) FROM player_history"
        ).fetchone()[0]

        return jsonify({
            "status": "ok",
            "current_players_loaded": current_count,
            "history_records_loaded": history_count,
            "database": str(DATABASE_PATH),
        })
    finally:
        connection.close()


@app.route("/api/players/current")
def get_current_players():
    role = request.args.get("ruolo")
    team = request.args.get("squadra")
    search = request.args.get("search")

    players = load_current_players(
        role=role,
        team=team,
        search=search,
    )

    return jsonify({
        "count": len(players),
        "items": players,
    })


@app.route("/api/players/history/<int:player_id>")
def get_player_history(player_id):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM player_history
            WHERE player_id = ?
            ORDER BY stagione DESC
            """,
            (player_id,)
        ).fetchall()

        return jsonify({
            "player_id": player_id,
            "count": len(rows),
            "items": [
                player_to_dict(row)
                for row in rows
            ],
        })
    finally:
        connection.close()


@app.route("/api/auction")
def get_auction_rankings():
    role = request.args.get("ruolo")
    team = request.args.get("squadra")
    search = request.args.get("search")

    players = load_current_players(
        role=role,
        team=team,
        search=search,
    )

    ranked_players = sorted(
        players,
        key=ranking_key
    )

    return jsonify({
        "count": len(ranked_players),
        "items": ranked_players,
    })


@app.route("/api/lineup")
def get_suggested_lineup():
    players = load_current_players()

    roles_order = [
        ("P", 1),
        ("D", 3),
        ("C", 4),
        ("A", 3),
    ]

    lineup = []

    for role, count in roles_order:
        candidates = [
            player
            for player in players
            if player.get("role") == role
        ]

        candidates = sorted(
            candidates,
            key=ranking_key
        )

        lineup.extend(candidates[:count])

    return jsonify({
        "count": len(lineup),
        "formation": "3-4-3",
        "items": lineup,
    })


@app.route("/api/market")
def get_market_moves():
    players = load_current_players()

    ranked_players = sorted(
        players,
        key=market_score,
        reverse=True,
    )

    buy_candidates = ranked_players[:15]
    sell_candidates = list(
        reversed(ranked_players[-15:])
    )

    return jsonify({
        "players_evaluated": len(players),
        "candidates_per_list": 15,
        "buy_candidates": buy_candidates,
        "sell_candidates": sell_candidates,
    })