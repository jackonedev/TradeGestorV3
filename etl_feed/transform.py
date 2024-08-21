from typing import Dict, List

import pandas as pd

from tools.technical_indicators import (
    adx,
    avg_true_range,
    moving_averages,
    squeeze_momentum_indicator,
)


def transform(
    data: Dict[str, Dict[str, List[Dict]]]
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Transformar datos
    """
    activos = list(data.keys())
    temporalidades = list(data[activos[0]].keys())
    results = {}
    for activo in activos:
        results[activo] = {}
        for temporalidad in temporalidades:
            df = pd.DataFrame(data[activo][temporalidad])
            # Set index
            df["time"] = pd.to_datetime(df["time"], unit="ms")
            df["time"] = df["time"] - pd.DateOffset(hours=3)
            df = df.set_index("time")
            # Convert to numeric
            df = df.astype(float)
            # Calculate technical indicators
            df = moving_averages(df, n=12)
            df = moving_averages(df, n=55)
            # TODO: optimizar parametros SQZMOM
            # TODO: optimizar ejecución por procesos paralelos
            df = squeeze_momentum_indicator(df)
            df = adx(df)
            df = avg_true_range(df)
            results[activo][temporalidad] = df.copy()
    print("Transformación de datos completada")
    return results
