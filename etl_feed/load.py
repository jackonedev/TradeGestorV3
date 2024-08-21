from typing import Dict

import pandas as pd

from tools.plots import (
    create_band,
    create_bar_figure,
    create_candlestick,
    create_price_figure,
    create_SQZMOM_bar,
    download_html,
    make_2r_subplots,
)
from utils.utils import create_download_folders


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
            bar = create_SQZMOM_bar(results[activo][temporalidad])
            fig1 = create_price_figure(
                data=results[activo][temporalidad],
                graph_objects=[candlestick, upper_band, lower_band, upper_KC, lower_KC],
                title=f"{activo} {temporalidad}",
            )
            fig2 = create_bar_figure(results[activo][temporalidad], [bar])
            plot_name = f"{activo}_{temporalidad}"
            subplot_fig = make_2r_subplots([fig1, fig2], title=plot_name)
            filename = (
                download_folders[i * len(temporalidades) + j] + f"/{plot_name}.html"
            )
            download_html(subplot_fig, filename)
    print("Descarga de datos completada")
