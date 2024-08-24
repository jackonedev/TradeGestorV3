from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from tools.business import calculate_targets
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
    limit: bool = True,
) -> None:
    if direction.lower() not in ["long", "short"]:
        raise ValueError
    direction = direction.lower()
    positions = {}
    activo_list = list(target_dict.keys())
    temporalidad_list = list(target_dict[activo_list[0]].keys())
    for activo, temporalidad_dict in targets.items():
        positions[activo] = {}
        operation_volume_activo = operation_volume / len(activo_list)
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

            market_long_sl: tuple = market_long[0]
            market_long_entry: tuple = market_long[1]
            market_long_tp: tuple = market_long[2]

            market_short_sl: tuple = market_short[0]
            market_short_entry: tuple = market_short[1]
            market_short_tp: tuple = market_short[2]

            limit_long_sl: tuple = limit_long[0]
            limit_long_entry: tuple = limit_long[1]
            limit_long_tp: tuple = limit_long[2]

            limit_short_sl: tuple = limit_short[0]
            limit_short_entry: tuple = limit_short[1]
            limit_short_tp: tuple = limit_short[2]

            long_sl = market_long_sl + limit_long_sl
            long_entry = market_long_entry + limit_long_entry
            long_tp = market_long_tp + limit_long_tp

            short_sl = market_short_sl + limit_short_sl
            short_entry = market_short_entry + limit_short_entry
            short_tp = market_short_tp + limit_short_tp

            if direction == "long":
                if market and limit:
                    sl = min(long_sl)
                    entry = np.mean(long_entry)
                    tp = long_tp
                    vol_unidad = operation_volume_temporalidad / len(long_entry)
                    # qty_per_entry = [ #TODO
                    #     NotImplemented
                    # ]
                elif market:
                    sl = min(market_long_sl)
                    entry = np.mean(market_long_entry)
                    tp = market_long_tp
                    vol_unidad = operation_volume_temporalidad / len(market_long_entry)
                elif limit:
                    sl = min(limit_long_sl)
                    entry = np.mean(limit_long_entry)
                    tp = limit_long_tp
                    vol_unidad = operation_volume_temporalidad / len(limit_long_entry)
            elif direction == "short":
                if market and limit:
                    sl = min(short_sl)
                    entry = np.mean(short_entry)
                    tp = short_tp
                    vol_unidad = operation_volume_temporalidad / len(short_entry)
                elif market:
                    sl = min(market_short_sl)
                    entry = np.mean(market_short_entry)
                    tp = market_short_tp
                    vol_unidad = operation_volume_temporalidad / len(market_short_entry)
                elif limit:
                    sl = min(limit_short_sl)
                    entry = np.mean(limit_short_entry)
                    tp = limit_short_tp
                    vol_unidad = operation_volume_temporalidad / len(limit_short_entry)

            porcentaje_sl = round(abs(entry - sl) / entry * 100, 2)
            apal_x, precio_liq = apalancamiento(entry, sl, direction)  # TODO
            # Consideramos que cada entrada posee el mismo peso dentro del trade
            # qty_entradas = ...
            """
            El PROBLEMA:
            `qty_per_entry` (conocida como `qty_entradas`) se encarga de dividir el volumen por unidad (entrada) por la diferencia entre entry y sl
            La entry en type "market" tiene dos sl, y el type "limit" tiene dos entry, cada uno con su propio sl.
            
            
            El otro PROBLEMA:            
            EL VOLUMEN POR UNIDAD DEBE CONSIDERAR DIVIR EL VOLUMEN DE OPERACION DEBE ENTRE LAS N ENTRADAS, LAS TEMPORALIDADES, Y LA CANTIDAD DE ACTIVOS
            """

            # TODO: Descargar contratos de futuros:
            # if direccion_trade == 'LONG' and apal_x > max_leverage_l: f'El apalancamiento máximo para este par es de {max_leverage_l}'
