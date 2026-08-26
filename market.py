from flask import Blueprint
from ..services.repository import load_players
from ..services.market_engine import suggest_market_moves
market_bp = Blueprint('market', __name__)
@market_bp.get('/moves')
def get_market_moves():
    return suggest_market_moves(load_players())
