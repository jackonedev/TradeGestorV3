import json
from functools import partial
from itertools import count, product
from random import randint

from tools.optimizer import many_partial_processes
from tools.technical_indicators import squeeze_momentum_indicator
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)


def optimize_sqzm_parameters():
    ## INITIAL VARIABLES ##
    download_paths = obtain_most_recent_download_directory_paths()
    downloaded_dfs = obtain_most_recent_downloaded_datasets()

    ## OPTIMIZING SQUEEZE MOMENTUM INDICATOR PARAMETERS ##
    PARAMETROS_ORIGINALES = dict(
        length=20, mult=1.5, length_KC=20, mult_KC=1, n_atr=10, use_EMA=True
    )
    length_BBs = [8, 12, 14, 18, 20, 22, 26]
    mult_range = [1.5]
    length_KCs = [8, 12, 14, 18, 20, 22, 26]
    mult_KC_range = [1]
    param_combinations = list(
        product(length_BBs, mult_range, length_KCs, mult_KC_range)
    )

    ## APPLY SQUEEZE MOMENTUM INDICATOR ##
    DATASETS_PARTIAL_DICT = {}
    DATASETS_PARAM_DICT = {}
    for activo, temporalidad_dict in downloaded_dfs.items():
        DATASETS_PARTIAL_DICT[activo] = {}
        DATASETS_PARAM_DICT[activo] = {}
        for temporalidad, df in temporalidad_dict.items():
            c = count()
            PARTIAL_LIST = []
            PARAM_LIST = []
            for x in param_combinations:
                p = PARAMETROS_ORIGINALES.copy()
                p.update(dict(zip(["length", "mult", "length_KC", "mult_KC"], x)))
                PARTIAL_LIST.append(partial(squeeze_momentum_indicator, df, **p))
                PARAM_LIST.append(p.copy())
            DATASETS_PARTIAL_DICT[activo][temporalidad] = PARTIAL_LIST.copy()
            DATASETS_PARAM_DICT[activo][temporalidad] = PARAM_LIST.copy()
    # Ejecutar optimización
    RESULT_DICT = {}
    for activo, temporalidad_dict in DATASETS_PARTIAL_DICT.items():
        RESULT_DICT[activo] = {}
        for temporalidad, partial_list in temporalidad_dict.items():
            RESULT_DICT[activo][temporalidad] = {}
            results = many_partial_processes(partial_list)
            RESULT_LIST = []
            for i, result in enumerate(results):
                RESULT_LIST.append(
                    (DATASETS_PARAM_DICT[activo][temporalidad][i], result.copy())
                )
            RESULT_DICT[activo][temporalidad] = RESULT_LIST.copy()

    ## OBTENER CORRELACION Y MEJORES PARAMETROS ##
    BEST_CORR_DICT = {}
    CORR_DICT = {}
    for activo, temporalidad_dict in RESULT_DICT.items():
        BEST_CORR_DICT[activo] = {}
        CORR_DICT[activo] = {}
        for temporalidad, results_list in temporalidad_dict.items():
            best_corr = 0
            best_params = None
            CORR_LIST = []
            for params, df in results_list:
                p = PARAMETROS_ORIGINALES.copy()
                p.update(
                    dict(
                        zip(
                            ["length", "mult", "length_KC", "mult_KC"],
                            params.values(),
                        )
                    )
                )
                corr = df["close"].corr(df["SQZMOM_value"])
                CORR_LIST.append({"corr": corr, "params": p})
                if corr > best_corr:
                    best_corr = corr
                    best_params = p.copy()

            CORR_DICT[activo][temporalidad] = CORR_LIST
            BEST_CORR_DICT[activo][temporalidad] = {
                "best_corr": best_corr,
                "best_params": best_params,
            }

    ## GUARDAR RESULTADOS ##
    for activo, temporalidad_dict in BEST_CORR_DICT.items():
        for temporalidad, corr_dict in temporalidad_dict.items():
            dir_path = download_paths[activo][temporalidad]
            rand = randint(100, 999)
            with open(
                f"{dir_path}/{activo}_{temporalidad}_sqzmom_best_params_{rand}.json",
                "w",
            ) as f:
                json.dump(corr_dict, f)
            with open(
                f"{dir_path}/{activo}_{temporalidad}_sqzmom_params_{rand}.json", "w"
            ) as f:
                json.dump(json.dumps(CORR_DICT[activo][temporalidad], indent=2), f)
