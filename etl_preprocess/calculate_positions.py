from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from tg.trade_gestor_v1 import cargar_contrato, get_price
from tools.business import calculate_targets, leverage, liq_price, split_targets


def return_targets(
    df_asset_dict: Dict[str, Dict[str, pd.DataFrame]],
    live: bool = False,
) -> Dict[str, Dict[str, Dict[str, Dict[str, List[Tuple]]]]]:
    """
    E.g.

    {
        "BTC": {
            "1h": {
                "market": {
                    "long": [(sl,), (entry,), (tp1, tp2)],
                    "short": [(sl,), (entry,), (tp1, tp2)]
                },
                "limit": {
                    "long": [(sl1, sl2), (entry1, entry2), (tp1, tp2, tp3)],
                    "short": [(sl1, sl2), (entry1, entry2), (tp1, tp2, tp3)]
                },
            },
            "15m": {
                "market": {
                    ...
                },
                "limit": {
                    ...
                }
            }
        },
        "ENS" : {
            "1h": {
                "market": {
                    "long": [(,), (,), (,)],
                    "short": [...]
                },
                "limit": {
                    "long": [(,), (,), (,)],
                    "short": [...]
                }
            },
            "15m": {
                "market": {
                    ...
                },
                "limit": {
                    ...
                }
            }
        }
    }

    """
    targets = {}
    for activo, temporalidad_dict in df_asset_dict.items():
        targets[activo] = {}
        if live:
            contract = cargar_contrato(activo)
            real_price = get_price(contract["symbol"])
            price_precision = contract["pricePrecision"]
        else:
            real_price = None
            price_precision = 2

        for temporalidad, df in temporalidad_dict.items():
            targets[activo][temporalidad] = calculate_targets(
                df, real_price, price_precision
            )
    return targets


def return_positions(
    targets,
    direction: str = "long",
    operation_volume: float = 100.0,
    market: bool = True,
    limit: bool = True,
    live: bool = False,
) -> Dict[str, Dict[str, Dict]]:

    if direction.lower() not in ["long", "short"]:
        raise ValueError("Direction must be 'long' or 'short'")

    direction = direction.lower()
    positions = {}
    activo_list = list(targets.keys())
    temporalidad_list = list(targets[activo_list[0]].keys())
    for activo, temporalidad_dict in targets.items():
        positions[activo] = {}
        operation_volume_activo = operation_volume / len(activo_list)
        if live:
            contract = cargar_contrato(activo)
            qty_precision = contract["quantityPrecision"]
            price_precision = contract["pricePrecision"]
        else:
            qty_precision: int = 5
            price_precision: int = 2

        for temporalidad, target_dict in temporalidad_dict.items():
            operation_volume_temporalidad = operation_volume_activo / len(
                temporalidad_list
            )

            market_targets = target_dict.get("market")
            limit_targets = target_dict.get("limit")
            market_long = market_targets.get("long")
            market_short = market_targets.get("short")
            limit_long = limit_targets.get("long")
            limit_short = limit_targets.get("short")

            market_long_operations = split_targets(market_long)
            market_short_operations = split_targets(market_short)
            limit_long_operations = split_targets(limit_long)
            limit_short_operations = split_targets(limit_short)

            if direction == "long":
                if market and limit:
                    operations = market_long_operations + limit_long_operations
                elif market:
                    operations = market_long_operations
                elif limit:
                    operations = limit_long_operations
                sl = min([op[0] for op in operations])
                rb = [
                    "1:{}".format(round((op[2] - op[1]) / (op[1] - op[0]), 2))
                    for op in operations
                ]

            elif direction == "short":
                if market and limit:
                    operations = market_short_operations + limit_short_operations
                elif market:
                    operations = market_short_operations
                elif limit:
                    operations = limit_short_operations
                sl = max([op[0] for op in operations])
                rb = [
                    "1:{}".format(round((op[1] - op[2]) / (op[0] - op[1]), 2))
                    for op in operations
                ]

            entry = np.mean([op[1] for op in operations])
            mean_sl_pct = round(
                abs(entry - np.mean([op[0] for op in operations])) / entry * 100, 2
            )
            mean_tp_pct = round(
                abs(entry - np.mean([op[2] for op in operations])) / entry * 100, 2
            )
            lev = leverage(entry, sl)
            liq = liq_price(lev, entry, direction)
            vol_unidad = operation_volume_temporalidad / len(operations)
            qty_per_entry = [
                round(vol_unidad / abs(x[0] - x[1]), qty_precision) for x in operations
            ]
            operations_dict = {
                f"operation_{i+1}": list(op) for i, op in enumerate(operations)
            }

            positions[activo][temporalidad] = {
                "asset": activo,
                "temporality": temporalidad,
                "direction": direction,
                "operations": operations_dict,
                "mean_stoploss_pct": mean_sl_pct,
                "mean_takeprofit_pct": mean_tp_pct,
                "lev": lev,
                "liq": round(liq, price_precision),
                "qty_per_entry": qty_per_entry,
                "vol_per_entry": round(vol_unidad, price_precision),
                "vol_trade": round(operation_volume_temporalidad, price_precision),
                "RB": rb,
            }

    return positions


def adjust_positions_leverage(
    positions: Dict[str, Dict[str, Dict]], direction: str, live: bool = False
) -> Dict[str, List[Dict]]:
    """
    Adjusts the leverage of all positions to the minimum leverage in the asset list.
    """

    adj_positions_by_asset = {}
    for asset in positions:
        operations = list(positions[asset].values())
        if live:
            contract = cargar_contrato(asset)
            max_leverage_l = int(contract["maxLongLeverage"])
            max_leverage_s = int(contract["maxShortLeverage"])
            qty_precision = contract["quantityPrecision"]
        else:
            max_leverage_l = 100
            max_leverage_s = 100
            qty_precision = 5

        if direction == "long":
            max_leverage = max_leverage_l
        elif direction == "short":
            max_leverage = max_leverage_s

        if max_leverage == 0:
            print("\nWARNING: The maximum leverage is 0. Setting default value of 20.")
            if input("Do you want to continue? (y/n): ").lower() != "y":
                raise ValueError("Operation canceled by user.")
            max_leverage = 20  # TODO: Caso BNB -> apalancamiento 0

        min_lev = min(pos["lev"] for pos in operations)
        min_liq = min(pos["liq"] for pos in operations)

        if min_lev >= max_leverage:
            print(f"UTILIZANDO APALANCAMIENTO MAXIMO: {max_leverage}")  # TODO: Borrar
            min_lev = max_leverage
            min_liq = "Not calculated"

        positions_adj = []
        for pos in operations:
            lev_actual = pos["lev"]

            if lev_actual == min_lev:
                positions_adj.append(pos)
                continue

            adj_factor = lev_actual / min_lev

            qty_per_entry_ajustada = np.array([qty * 1 for qty in pos["qty_per_entry"]])
            # )#TODO: me apalanco más para comprar más o me apalanco más para comprar lo mismo?
            # qty_per_entry_ajustada = np.array(
            #     [qty * adj_factor for qty in pos["qty_per_entry"]]
            vol_per_entry_ajustada = pos["vol_per_entry"] * adj_factor
            vol_trade = pos["vol_trade"] * adj_factor

            pos_adj = pos.copy()
            pos_adj["lev"] = min_lev
            pos_adj["liq"] = min_liq
            pos_adj["qty_per_entry"] = qty_per_entry_ajustada.round(
                qty_precision
            ).tolist()
            pos_adj["vol_per_entry"] = vol_per_entry_ajustada
            pos_adj["vol_trade"] = vol_trade

            positions_adj.append(pos_adj)
        adj_positions_by_asset[asset] = positions_adj

    return adj_positions_by_asset
