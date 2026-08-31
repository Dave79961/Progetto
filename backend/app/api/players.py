from flask import Blueprint
from ..services.repository import load_players
players_bp = Blueprint('players', __name__)
@players_bp.get('/')
def list_players():
    return {'items': load_players()}
