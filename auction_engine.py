def compute_auction_score(player, budget_factor=1.0):
    raw = player['expected_bonus']*4 - player['expected_malus']*2 + player['availability']*3
    return round(raw - (player['price']/10)*budget_factor, 2)

def rank_players(players, budget_factor=1.0):
    rows=[]
    for p in players:
        item=dict(p)
        item['auction_score']=compute_auction_score(item, budget_factor)
        rows.append(item)
    return sorted(rows, key=lambda x: x['auction_score'], reverse=True)
