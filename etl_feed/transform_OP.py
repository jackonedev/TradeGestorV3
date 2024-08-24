from functools import partial
from itertools import count
from typing import Dict, List

import pandas as pd

from tools.optimizer import many_partial_processes
from tools.technical_indicators import (
    adx,
    avg_true_range,
    moving_averages,
    squeeze_momentum_indicator,
)


def transform_OP(
    data: Dict[str, Dict[str, List[Dict]]]
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Transformar datos
    """
    activos = list(data.keys())
    temporalidades = list(data[activos[0]].keys())
    data_dict = {}
    # Set index
    # Convert to numeric
    # Calculate moving averages
    for activo in activos:
        data_dict[activo] = {}
        for temporalidad in temporalidades:
            df = pd.DataFrame(data[activo][temporalidad])
            df["time"] = pd.to_datetime(df["time"], unit="ms")
            df["time"] = df["time"] - pd.DateOffset(hours=3)
            df = df.set_index("time")
            df = df.astype(float)
            df = pd.concat(
                [
                    df,
                    moving_averages(df, n=12).loc[:, ["WMA_12", "DEMA_12", "TEMA_12"]],
                ],
                axis=1,
            )
            df = pd.concat(
                [df, moving_averages(df, n=55).loc[:, [f"EMA_55", f"TRIMA_L_55"]]],
                axis=1,
            )
            data_dict[activo][temporalidad] = df.copy()

    # Obtención de los parámetros optimizados del indicador Squeeze Momentum Indicator
    sqzm_partial_dict = {}
    sqzm_partial_list = []
    sqzm_length_KCs = [12, 14, 18, 20, 22]
    sqzm_default_params = dict(
        length=20,
        mult=2,
        length_KC=20,
        mult_KC=1.5,
        n_atr=10,
        use_EMA=True,
    )
    for activo, temporalidad_dict in data_dict.items():
        sqzm_partial_dict[activo] = {}
        for temporalidad, df in temporalidad_dict.items():
            sqzm_partial_dict[activo][temporalidad] = {}
            for l in sqzm_length_KCs:
                p = sqzm_default_params.copy()
                p.update({"length_KC": l})
                sqzm_partial_dict[activo][temporalidad][l] = None
                sqzm_partial_list.append(partial(squeeze_momentum_indicator, df, **p))
    results = many_partial_processes(sqzm_partial_list)
    c = count()
    for activo, temporalidad_dict in sqzm_partial_dict.items():
        for temporalidad, df in temporalidad_dict.items():
            for l in sqzm_length_KCs:
                sqzm_partial_dict[activo][temporalidad][l] = results[next(c)]

    CORR_DICT = {}
    for activo, temporalidad_dict in sqzm_partial_dict.items():
        CORR_DICT[activo] = {}
        best_corr = 0
        best_params = None
        for temporalidad, asset_dict in temporalidad_dict.items():
            for l in sqzm_length_KCs:
                p = sqzm_default_params.copy()
                p.update({"length_KC": l})
                corr = asset_dict[l]["close"].corr(asset_dict[l]["SQZMOM_value"])
                if corr > best_corr:
                    best_corr = corr
                    best_params = p.copy()
            if best_params is None:
                best_params = sqzm_default_params.copy()
                print(f"length_KC no pudo optimizarse para {activo} {temporalidad}")
            CORR_DICT[activo][temporalidad] = {
                "best_corr": best_corr,
                "best_params": best_params,
            }

    # Aplicación de los parámetros optimizados a los indicadores técnicos
    # Squeeze Momentum Indicator, ADX y ATR
    results_dict = {}
    for activo, temporalidad_dict in data_dict.items():
        results_dict[activo] = {}
        for temporalidad, df in temporalidad_dict.items():
            best_window = CORR_DICT[activo][temporalidad]["best_params"]["length_KC"]
            df = squeeze_momentum_indicator(df, length_KC=best_window)
            df = adx(df, n=best_window)
            df = avg_true_range(df, n=best_window, use_EMA=False)
            results_dict[activo][temporalidad] = df.copy()
    return results_dict
