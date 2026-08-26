def suggest_market_moves(players):
    sells=[p for p in players if p['availability']<0.45][:5]
    buys=[p for p in players if p['expected_bonus']>1.2 and p['price']<=35][:5]
    return {'sell_candidates': sells, 'buy_candidates': buys}
