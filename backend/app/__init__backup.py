from flask import Flask, jsonify
import json
import os

app = Flask(__name__)


def load_players():
    # players.json si trova in backend/app/players.json
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "players_stats_test.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/api/auction")
def get_auction_rankings():
    players = load_players()

    # Esempio: ordina per expected_bonus (discendente), poi per price (crescente)
    players_sorted = sorted(
        players,
        key=lambda p: (-p.get("expected_bonus", 0), p.get("price", 0))
    )

    return jsonify({"items": players_sorted})


@app.route("/api/lineup")
def get_suggested_lineup():
    players = load_players()

    # Semplice esempio di formazione (1-3-3-3)
    roles_order = [
        ("P", 1),  # portieri
        ("D", 3),  # difensori
        ("C", 3),  # centrocampisti
        ("A", 3),  # attaccanti
    ]

    lineup = []
    for role, count in roles_order:
        candidates = [
            p for p in players
            if p.get("role") == role
        ]
        candidates_sorted = sorted(
            candidates,
            key=lambda p: (-p.get("expected_bonus", 0), p.get("price", 0))
        )
        lineup.extend(candidates_sorted[:count])

    return jsonify({"items": lineup})


@app.route("/api/market")
def get_market_moves():
    players = load_players()

    # Esempio:
    # - candidati da vendere: quelli con expected_bonus basso e expected_malus alto
    # - candidati da comprare: expected_bonus alto e expected_malus basso
    sorted_players = sorted(
        players,
        key=lambda p: (
            p.get("expected_bonus", 0) - p.get("expected_malus", 0)
        )
    )

    # Prima metà: peggiori → da vendere
    # Seconda metà: migliori → da comprare
    mid = len(sorted_players) // 2
    sell = sorted_players[:mid]
    buy = list(reversed(sorted_players[mid:]))

    return jsonify({
        "sell_candidates": sell,
        "buy_candidates": buy,
    })