from flask import Blueprint
from ..services.repository import load_players
from ..services.lineup_engine import suggest_lineup
lineup_bp = Blueprint('lineup', __name__)
@lineup_bp.get('/suggested')
def get_suggested_lineup():
    return {'items': suggest_lineup(load_players())}
