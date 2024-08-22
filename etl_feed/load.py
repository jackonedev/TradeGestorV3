from typing import Dict

import pandas as pd

from tools.plots import (
    create_bar_figure,
    create_candlestick,
    create_price_figure,
    create_scatter,
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
            upper_band = create_scatter(
                results[activo][temporalidad], "upper_BB", "upper_BB", "red"
            )
            lower_band = create_scatter(
                results[activo][temporalidad], "lower_BB", "lower_BB", "red"
            )
            upper_KC = create_scatter(
                results[activo][temporalidad], "upper_KC", "upper_KC", "blue"
            )
            lower_KC = create_scatter(
                results[activo][temporalidad], "lower_KC", "lower_KC", "blue"
            )
            WMA_12 = create_scatter(
                results[activo][temporalidad], "WMA_12", "WMA_12", "yellow"
            )
            DEMA_12 = create_scatter(
                results[activo][temporalidad], "DEMA_12", "DEMA_12", "yellow"
            )
            TEMA_12 = create_scatter(
                results[activo][temporalidad],
                "TEMA_12",
                "TEMA_12",
                "yellow",
                hover=True,
            )
            EMA_55 = create_scatter(
                results[activo][temporalidad], "EMA_55", "EMA_55", "brown", hover=True
            )
            TRIMA_L_55 = create_scatter(
                results[activo][temporalidad], "TRIMA_L_55", "TRIMA_L_55", "brown"
            )
            objects1 = [
                candlestick,
                upper_band,
                lower_band,
                upper_KC,
                lower_KC,
                WMA_12,
                DEMA_12,
                TEMA_12,
                EMA_55,
                TRIMA_L_55,
            ]

            sqzm_bar = create_SQZMOM_bar(results[activo][temporalidad], normalize=True)
            adx_line = create_scatter(
                results[activo][temporalidad] - 50, "adx", "ADX", "black", hover=True
            )
            plus_di = create_scatter(
                results[activo][temporalidad] - 50, "plus_di", "plus_DI", "green", hover=True
            )
            minus_di = create_scatter(
                results[activo][temporalidad] - 50, "minus_di", "minus_DI", "red", hover=True
            )
            objects2 = [sqzm_bar, adx_line, plus_di, minus_di]
            fig1 = create_price_figure(
                data=results[activo][temporalidad],
                graph_objects=objects1,
                title=f"{activo} {temporalidad}",
            )
            fig2 = create_bar_figure(
                data=results[activo][temporalidad], graph_objects=objects2
            )
            plot_name = f"{activo}_{temporalidad}"
            subplot_fig = make_2r_subplots([fig1, fig2], title=plot_name)
            filename = (
                download_folders[i * len(temporalidades) + j] + f"/{plot_name}.html"
            )
            download_html(subplot_fig, filename)

