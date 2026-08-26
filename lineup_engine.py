ROLE_LIMITS={'P':1,'D':3,'C':4,'A':3}
def compute_lineup_score(player):
    return round(player['expected_bonus']*5 + player['availability']*2 - player['expected_malus']*2, 2)
def suggest_lineup(players):
    out=[]
    counts={k:0 for k in ROLE_LIMITS}
    for p in sorted(players, key=compute_lineup_score, reverse=True):
        if counts[p['role']] < ROLE_LIMITS[p['role']]:
            item=dict(p)
            item['lineup_score']=compute_lineup_score(p)
            out.append(item)
            counts[p['role']]+=1
    return out
