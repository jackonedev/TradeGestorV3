from schemas.targets import TargetResults


def calculate_targets(df, real_price=None):
    results = TargetResults.calculate(df, real_price)
    return results.dict()


def split_targets(targets, n_takeprofits_per_group=3):
    stoplosses = targets[0]
    entries = targets[1]
    takeprofits = targets[2]

    operations = []
    for i in range(len(stoplosses)):
        stoploss = stoplosses[i]
        entry = entries[i]
        takeprofit_group = takeprofits[
            i * n_takeprofits_per_group : (i + 1) * n_takeprofits_per_group
        ]

        for tp in takeprofit_group:
            operations.append((stoploss, entry, tp))

    return operations


def leverage(entry, sl, adj_factor=0.1, safety_margin=2):
    delta = abs(1 - entry / sl)
    lev = int((1 - adj_factor) / delta)
    adj_lev = lev - safety_margin
    return adj_lev


def liq_price(lev, entry, direction):
    distance = entry * (1 / lev) * 0.9
    if direction == "long":
        liq = entry - distance
    elif direction == "short":
        liq = entry + distance
    return liq


def adjust_positions_by_minimum_leverage(positions_list):
    min_lev = min(pos["lev"] for pos in positions_list)
    min_liq = min(pos["liq"] for pos in positions_list)
    
    
    positions_adj = []
    for pos in positions_list:
        lev_actual = pos["lev"]
        
        if lev_actual == min_lev:
            positions_adj.append(pos)
            continue
        
        adj_factor = lev_actual / min_lev
        
        qty_per_entry_ajustada = [qty * adj_factor for qty in pos["qty_per_entry"]]
        vol_per_entry_ajustada = pos["vol_per_entry"] * adj_factor
        vol_trade = pos["vol_trade"] * adj_factor
        
        
        pos_adj = pos.copy()
        pos_adj["lev"] = min_lev
        pos_adj["liq"] = min_liq
        pos_adj["qty_per_entry"] = qty_per_entry_ajustada
        pos_adj["vol_per_entry"] = vol_per_entry_ajustada
        pos_adj["vol_trade"] = vol_trade
        
        positions_adj.append(pos_adj)
    
    return positions_adj
