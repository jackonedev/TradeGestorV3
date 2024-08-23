from typing import Dict

import numpy as np
import pandas as pd

from tools.plots import (
    create_bar,
    create_bar_figure,
    create_candlestick,
    create_price_figure,
    create_scatter,
    create_SQZMOM_bar,
    download_html,
    make_3r_subplots,
)
from utils.utils import create_download_folders


def load_volume(
    results: Dict[str, Dict[str, pd.DataFrame]], plots: bool = True
) -> None:
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
    
            # Figure 1
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
            fig1 = create_price_figure(
                data=results[activo][temporalidad],
                graph_objects=objects1,
                title=f"{activo} {temporalidad}",
            )
            fig1.update_yaxes(autorange=False)

            # Figure 2
            volume = create_bar(
                results[activo][temporalidad], "volume", "Volume", "blue", hover=True
            )
            objects2 = [volume]
            fig2 = create_bar_figure(
                data=results[activo][temporalidad],
                graph_objects=objects2,
                title=f"{activo} {temporalidad}",
            )
            fig2.update_yaxes(autorange=False)

            # Figure 3
            sqzm_bar = create_SQZMOM_bar(results[activo][temporalidad], normalize=True)
            adx_line = create_scatter(
                results[activo][temporalidad] - 50, "adx", "ADX", "black", hover=True
            )
            plus_di = create_scatter(
                results[activo][temporalidad] - 50,
                "plus_di",
                "plus_DI",
                "green",
                hover=True,
            )
            minus_di = create_scatter(
                results[activo][temporalidad] - 50,
                "minus_di",
                "minus_DI",
                "red",
                hover=True,
            )
            results[activo][temporalidad]["squeeze_on"] = np.where(results[activo][temporalidad]["squeeze_on"] == 1, 0, None)
            sqz_signal = create_scatter(
                results[activo][temporalidad], "squeeze_on", "SQZ Signal", "blue", hover=True
            )
            # sqz_signal.update(
            #     dict(marker=dict(size=10)),
            #     overwrite=True
            # )

            objects3 = [sqzm_bar, adx_line, plus_di, minus_di, sqz_signal]

            fig3 = create_bar_figure(
                data=results[activo][temporalidad], graph_objects=objects3
            )
            fig3.update_yaxes(autorange=False)
            
            
            # Subplot
            last_atr = results[activo][temporalidad]["atr"].iloc[-1]
            plot_name = f"{activo}_{temporalidad} - [ATR] = {last_atr}"
            subplot_fig = make_3r_subplots([fig1, fig2, fig3], title=plot_name)
            filename = (
                download_folders[i * len(temporalidades) + j]
                + f"/{plot_name.split('-')[0].strip()}.html"
            )
            download_html(subplot_fig, filename)
