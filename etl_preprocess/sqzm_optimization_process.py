import json
from functools import partial
from itertools import count, product
from random import randint

import numpy as np

from tools.optimizer import many_partial_processes
from tools.technical_indicators import squeeze_momentum_indicator
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)

## INITIAL VARIABLES ##
download_paths = obtain_most_recent_download_directory_paths()
downloaded_dfs = obtain_most_recent_downloaded_datasets()


## OPTIMIZING SQUEEZE MOMENTUM INDICATOR PARAMETERS ##
DATASETS_PARTIAL_DICT = {}
PARTIAL_CALL_LIST = []
PARAMETROS_ORIGINALES = dict(
    length=20, mult=2, length_KC=20, mult_KC=1.5, n_atr=10, use_EMA=True
)
length_BBs = [12, 14, 18, 20, 22]
mult_range = np.arange(1.5, 2.6, 0.25)
length_KCs = [12, 14, 18, 20, 22]
mult_KC_range = np.arange(1, 2.1, 0.25)
param_combinations = list(product(length_BBs, mult_range, length_KCs, mult_KC_range))

## APPLY SQUEEZE MOMENTUM INDICATOR ##
for activo, temporalidad_dict in downloaded_dfs.items():
    DATASETS_PARTIAL_DICT[activo] = {}
    for temporalidad, df in temporalidad_dict.items():
        DATASETS_PARTIAL_DICT[activo][temporalidad] = {}
        c = count()
        for x in param_combinations:
            p = PARAMETROS_ORIGINALES.copy()
            p.update(dict(zip(["length", "mult", "length_KC", "mult_KC"], x)))
            DATASETS_PARTIAL_DICT[activo][temporalidad][next(c)] = None
            PARTIAL_CALL_LIST.append(partial(squeeze_momentum_indicator, df, **p))
# Ejecutar optimización
results = many_partial_processes(PARTIAL_CALL_LIST)
# Actualizar diccionario
c = count()
for activo, temporalidad_dict in DATASETS_PARTIAL_DICT.items():
    for temporalidad, df in temporalidad_dict.items():
        for i in range(len(param_combinations)):
            DATASETS_PARTIAL_DICT[activo][temporalidad][i] = results[next(c)]

## OBTENER CORRELACION Y MEJORES PARAMETROS ##
CORR_DICT = {}
for activo, temporalidad_dict in DATASETS_PARTIAL_DICT.items():
    CORR_DICT[activo] = {}
    best_corr = 0
    best_params = None
    for temporalidad, asset_dict in temporalidad_dict.items():
        for i in range(len(param_combinations)):
            p = PARAMETROS_ORIGINALES.copy()
            p.update(
                dict(
                    zip(
                        ["length", "mult", "length_KC", "mult_KC"],
                        param_combinations[i],
                    )
                )
            )
            corr = asset_dict[i]["close"].corr(asset_dict[i]["SQZMOM_value"])
            if corr > best_corr:
                best_corr = corr
                best_params = p.copy()
        CORR_DICT[activo][temporalidad] = {
            "best_corr": best_corr,
            "best_params": best_params,
        }

## GUARDAR RESULTADOS ##
for activo, temporalidad_dict in CORR_DICT.items():
    for temporalidad, corr_dict in temporalidad_dict.items():
        dir_path = download_paths[activo][temporalidad]
        with open(f"{dir_path}/sqzmom_params_{randint(100,999)}.json", "w") as f:
            json.dump(corr_dict, f)
