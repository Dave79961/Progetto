from flask import Blueprint, request
from ..services.repository import load_players
from ..services.auction_engine import rank_players
auction_bp = Blueprint('auction', __name__)
@auction_bp.get('/rankings')
def get_rankings():
    budget_factor=float(request.args.get('budgetFactor', 1.0))
    return {'items': rank_players(load_players(), budget_factor)}
