from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

ROLE_ORDER = ("P", "D", "C", "A")
DEFAULT_LIMITS = {"P": 3, "D": 8, "C": 8, "A": 6, "TOTALE": 25}
DEFAULT_BUDGET = 500.0
DEFAULT_MODE = "listone"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _normalise_mode(value: Any) -> str:
    mode = str(value or DEFAULT_MODE).strip().lower()
    if mode not in {"listone", "asta"}:
        raise ValueError("mode deve essere 'listone' oppure 'asta'")
    return mode


def _number(value: Any, field: str, minimum: float = 0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} deve essere un numero") from error
    if number < minimum:
        raise ValueError(f"{field} non puÃ² essere inferiore a {minimum}")
    return number


def _integer(value: Any, field: str, minimum: int = 0) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} deve essere un numero intero") from error
    if number < minimum:
        raise ValueError(f"{field} non puÃ² essere inferiore a {minimum}")
    return number


def initialise_roster_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS personal_roster_settings (
            profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
            league_name TEXT NOT NULL DEFAULT 'La mia lega',
            mode TEXT NOT NULL DEFAULT 'listone',
            budget_initial REAL NOT NULL DEFAULT 500,
            limit_p INTEGER NOT NULL DEFAULT 3,
            limit_d INTEGER NOT NULL DEFAULT 8,
            limit_c INTEGER NOT NULL DEFAULT 8,
            limit_a INTEGER NOT NULL DEFAULT 6,
            limit_total INTEGER NOT NULL DEFAULT 25,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS personal_roster_players (
            player_id INTEGER PRIMARY KEY,
            player_name TEXT NOT NULL,
            role TEXT NOT NULL,
            team TEXT NOT NULL,
            purchase_price REAL NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'listone',
            acquired_at TEXT NOT NULL,
            FOREIGN KEY (player_id) REFERENCES current_players(player_id)
        )
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO personal_roster_settings (
            profile_id, league_name, mode, budget_initial,
            limit_p, limit_d, limit_c, limit_a, limit_total, updated_at
        ) VALUES (1, 'La mia lega', 'listone', 500, 3, 8, 8, 6, 25, ?)
        """,
        (_now(),),
    )
    connection.commit()


def _settings(connection: sqlite3.Connection) -> dict[str, Any]:
    initialise_roster_schema(connection)
    settings = _as_dict(
        connection.execute(
            "SELECT * FROM personal_roster_settings WHERE profile_id = 1"
        ).fetchone()
    )
    return settings or {}


def _limits(settings: dict[str, Any]) -> dict[str, int]:
    return {
        "P": int(settings["limit_p"]),
        "D": int(settings["limit_d"]),
        "C": int(settings["limit_c"]),
        "A": int(settings["limit_a"]),
        "TOTALE": int(settings["limit_total"]),
    }


def _roster_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT player_id, player_name, role, team, purchase_price, source, acquired_at
        FROM personal_roster_players
        ORDER BY
            CASE role
                WHEN 'P' THEN 1
                WHEN 'D' THEN 2
                WHEN 'C' THEN 3
                WHEN 'A' THEN 4
                ELSE 5
            END,
            player_name COLLATE NOCASE
        """
    ).fetchall()
    return [dict(row) for row in rows]


def roster_summary(connection: sqlite3.Connection) -> dict[str, Any]:
    settings = _settings(connection)
    limits = _limits(settings)
    players = _roster_rows(connection)
    by_role = {role: 0 for role in ROLE_ORDER}
    spent = 0.0

    for player in players:
        role = player["role"]
        if role in by_role:
            by_role[role] += 1
        spent += float(player["purchase_price"] or 0)

    budget_initial = float(settings["budget_initial"])
    remaining_slots = {
        role: max(0, limits[role] - by_role[role])
        for role in ROLE_ORDER
    }

    return {
        "settings": {
            "league_name": settings["league_name"],
            "mode": settings["mode"],
            "budget_initial": budget_initial,
            "limits": limits,
            "updated_at": settings["updated_at"],
        },
        "players": players,
        "count": len(players),
        "by_role": by_role,
        "remaining_slots": remaining_slots,
        "spent": round(spent, 2),
        "budget_remaining": round(budget_initial - spent, 2),
    }


def update_settings(
    connection: sqlite3.Connection,
    payload: dict[str, Any],
) -> dict[str, Any]:
    current = _settings(connection)
    limits = _limits(current)

    league_name = str(
        payload.get("league_name", current["league_name"])
    ).strip()
    if not league_name:
        raise ValueError("league_name non puÃ² essere vuoto")

    mode = _normalise_mode(payload.get("mode", current["mode"]))
    budget_initial = _number(
        payload.get("budget_initial", current["budget_initial"]),
        "budget_initial",
    )

    incoming_limits = payload.get("limits", {})
    if incoming_limits is None:
        incoming_limits = {}
    if not isinstance(incoming_limits, dict):
        raise ValueError("limits deve essere un oggetto")

    for role in ROLE_ORDER:
        if role in incoming_limits:
            limits[role] = _integer(
                incoming_limits[role],
                f"limits.{role}",
                1,
            )

    if "TOTALE" in incoming_limits:
        limits["TOTALE"] = _integer(
            incoming_limits["TOTALE"],
            "limits.TOTALE",
            11,
        )

    if sum(limits[role] for role in ROLE_ORDER) != limits["TOTALE"]:
        raise ValueError(
            "limits.TOTALE deve coincidere con la somma dei ruoli"
        )

    existing = roster_summary(connection)
    if existing["count"] > limits["TOTALE"]:
        raise ValueError(
            "I nuovi limiti non possono escludere giocatori giÃ  presenti"
        )

    for role in ROLE_ORDER:
        if existing["by_role"][role] > limits[role]:
            raise ValueError(
                f"I nuovi limiti non possono escludere giocatori giÃ  presenti nel ruolo {role}"
            )

    connection.execute(
        """
        UPDATE personal_roster_settings
        SET league_name = ?, mode = ?, budget_initial = ?,
            limit_p = ?, limit_d = ?, limit_c = ?, limit_a = ?,
            limit_total = ?, updated_at = ?
        WHERE profile_id = 1
        """,
        (
            league_name,
            mode,
            budget_initial,
            limits["P"],
            limits["D"],
            limits["C"],
            limits["A"],
            limits["TOTALE"],
            _now(),
        ),
    )
    connection.commit()
    return roster_summary(connection)


def add_player(
    connection: sqlite3.Connection,
    payload: dict[str, Any],
) -> dict[str, Any]:
    settings = _settings(connection)
    player_id = _integer(payload.get("player_id"), "player_id", 1)
    source = _normalise_mode(payload.get("source", settings["mode"]))
    purchase_price = _number(
        payload.get("purchase_price", 0),
        "purchase_price",
    )

    player = connection.execute(
        "SELECT player_id, nome, ruolo, squadra FROM current_players WHERE player_id = ?",
        (player_id,),
    ).fetchone()
    if player is None:
        raise ValueError("Giocatore non trovato nel database")

    existing = connection.execute(
        "SELECT player_id FROM personal_roster_players WHERE player_id = ?",
        (player_id,),
    ).fetchone()
    if existing is not None:
        raise ValueError("Questo giocatore Ã¨ giÃ  nella rosa personale")

    summary = roster_summary(connection)
    role = str(player["ruolo"] or "").upper()
    if role not in ROLE_ORDER:
        raise ValueError("Ruolo del giocatore non valido")

    limits = summary["settings"]["limits"]
    if summary["count"] >= limits["TOTALE"]:
        raise ValueError("Hai giÃ  raggiunto il numero massimo di giocatori in rosa")
    if summary["by_role"][role] >= limits[role]:
        raise ValueError(f"Hai giÃ  raggiunto il limite per il ruolo {role}")
    if purchase_price > summary["budget_remaining"]:
        raise ValueError("Budget insufficiente per questo acquisto")

    connection.execute(
        """
        INSERT INTO personal_roster_players (
            player_id, player_name, role, team, purchase_price, source, acquired_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(player["player_id"]),
            str(player["nome"] or ""),
            role,
            str(player["squadra"] or ""),
            purchase_price,
            source,
            _now(),
        ),
    )
    connection.commit()
    return roster_summary(connection)


def remove_player(
    connection: sqlite3.Connection,
    player_id: int,
) -> dict[str, Any]:
    _settings(connection)
    result = connection.execute(
        "DELETE FROM personal_roster_players WHERE player_id = ?",
        (player_id,),
    )
    if result.rowcount == 0:
        raise ValueError("Giocatore non presente nella rosa personale")
    connection.commit()
    return roster_summary(connection)


def clear_roster(connection: sqlite3.Connection) -> dict[str, Any]:
    _settings(connection)
    connection.execute("DELETE FROM personal_roster_players")
    connection.commit()
    return roster_summary(connection)


def request_json(request: Any) -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Il corpo della richiesta deve essere un oggetto JSON")
    return payload
