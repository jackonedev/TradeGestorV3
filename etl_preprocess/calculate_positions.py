from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from tools.business import calculate_targets, leverage, liq_price, split_targets
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)

download_paths = obtain_most_recent_download_directory_paths()
downloaded_dfs = obtain_most_recent_downloaded_datasets()

# obtener una muestra
df = downloaded_dfs["BTC"]["5m"].copy()


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
        # Obtener real-price: if "live"
        # TODO - if live: real_price = get_real_price(activo)
        # Es importante porque la data de analisis tiene delay
        for temporalidad, df in temporalidad_dict.items():
            targets[activo][temporalidad] = calculate_targets(df, real_price=None)
    return targets


def return_positions(
    targets,
    direction: str = "long",
    operation_volume: float = 100.0,
    market: bool = True,
    limit: bool = True
) -> None:
    if direction.lower() not in ["long", "short"]:
        raise ValueError
    direction = direction.lower()
    positions = {}
    activo_list = list(targets.keys())
    temporalidad_list = list(targets[activo_list[0]].keys())
    for activo, temporalidad_dict in targets.items():
        positions[activo] = {}
        operation_volume_activo = operation_volume / len(activo_list)
        qty_precision: int = 5  # TODO: descargar contratos
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
                rb = ["1:{}".format(round((op[2] - op[1]) / (op[1] - op[0]), 2)) for op in operations]

            elif direction == "short":
                if market and limit:
                    operations = market_short_operations + limit_short_operations
                elif market:
                    operations = market_short_operations
                elif limit:
                    operations = limit_short_operations
                sl = max([op[0] for op in operations])
                rb = ["1:{}".format(round((op[1] - op[2]) / (op[0] - op[1]), 2)) for op in operations]
            
            entry = np.mean([op[1] for op in operations])
            mean_sl_pct = round(abs(entry - np.mean([op[0] for op in operations])) / entry * 100, 2)
            mean_tp_pct = round(abs(entry - np.mean([op[2] for op in operations])) / entry * 100, 2)
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
                "operations": operations_dict,
                "mean_stoploss_pct": mean_sl_pct,
                "mean_takeprofit_pct": mean_tp_pct,
                "lev": lev,
                "liq": liq,
                "qty_per_entry": qty_per_entry,
                "vol_per_entry": vol_unidad,
                "vol_trade": operation_volume_temporalidad,
                "RB": rb,
            }
    
    return positions
