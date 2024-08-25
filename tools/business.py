from schemas.targets import TargetResults


def calculate_targets(df, real_price=None, precision=2):
    results = TargetResults.calculate(df, real_price, precision)
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
