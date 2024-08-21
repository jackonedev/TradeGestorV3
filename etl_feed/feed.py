import concurrent.futures
from typing import Dict, List

import pandas as pd
import requests

from tools.plots import (
    create_band,
    create_bar_figure,
    create_candlestick,
    create_price_figure,
    create_SQZMOM_bar,
    download_html,
    make_subplots,
)
from tools.technical_indicators import (
    adx,
    avg_true_range,
    moving_averages,
    squeeze_momentum_indicator,
)
from utils.config import KLINES_LIMIT as LIMIT
from utils.config import KLINES_SERVICE as SERVICE
from utils.utils import create_download_folders


def extract(
    activos: List[str],
    temporalidades: List[str],
    start_time_list: List[int],
    end_time: int,
) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Extraer datos de BingX
    """

    data = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_submit = []
        for activo in activos:
            symbol = activo + "-USDT"
            for i, interval in enumerate(temporalidades):
                futures_submit.append(
                    executor.submit(
                        requests.get,
                        SERVICE,
                        params={
                            "symbol": symbol,
                            "interval": interval,
                            "limit": LIMIT,
                            "startTime": start_time_list[i],
                            "endTime": end_time,
                        },
                    )
                )
        # Guardar los datos en un diccionario
        for i, activo in enumerate(activos):
            data[activo] = {}
            for j, interval in enumerate(temporalidades):
                response = futures_submit[i * len(temporalidades) + j].result()
                data[activo][interval] = response.json().get("data")
    print("Extracción de datos completada")
    return data


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
            df = squeeze_momentum_indicator(df)
            df = adx(df)
            df = avg_true_range(df)
            results[activo][temporalidad] = df.copy()
    print("Transformación de datos completada")
    return results


def load(results: Dict[str, Dict[str, pd.DataFrame]], plots: bool = True) -> None:
    """
    Guardar datos en disco
    """
    download_folders = create_download_folders(results)
    activos = list(results.keys())
    temporalidades = list(results[activos[0]].keys())
    for i, activo in enumerate(activos):
        for j, temporalidad in enumerate(temporalidades):
            # Download Data
            results[activo][temporalidad].to_parquet(
                download_folders[i * len(temporalidades) + j] + "/data.parquet"
            )
            # Create plots
            # Download HTML
            if not plots:
                continue
            candlestick = create_candlestick(results[activo][temporalidad])
            upper_band = create_band(
                results[activo][temporalidad], "upper_BB", "upper_BB", "red"
            )
            lower_band = create_band(
                results[activo][temporalidad], "lower_BB", "lower_BB", "red"
            )
            upper_KC = create_band(
                results[activo][temporalidad], "upper_KC", "upper_KC", "blue"
            )
            lower_KC = create_band(
                results[activo][temporalidad], "lower_KC", "lower_KC", "blue"
            )

            # TODO: FutureWarning: Series.__getitem__ treating keys as positions is deprecated.
            bar = create_SQZMOM_bar(results[activo][temporalidad])

            fig1 = create_price_figure(
                data=results[activo][temporalidad],
                graph_objects=[candlestick, upper_band, lower_band, upper_KC, lower_KC],
                title=f"{activo} {temporalidad}",
            )
            fig2 = create_bar_figure(results[activo][temporalidad], [bar])
            plot_name = f"{activo}_{temporalidad}"
            subplot_fig = make_subplots([fig1, fig2], title=plot_name)
            filename = (
                download_folders[i * len(temporalidades) + j] + f"/{plot_name}.html"
            )
            download_html(subplot_fig, filename)
    print("Descarga de datos completada")
