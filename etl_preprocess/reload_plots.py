import json
import os

from tools.final_plots import load_3r_plots
from tools.technical_indicators import squeeze_momentum_indicator
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)


def reload_plots():
    """
    Recarga los gráficos de los activos y temporalidades más recientes
    utilizando parámetros óptimos para el indicador Squeeze Momentum.
    """

    ## INITIAL VARIABLES ##
    download_paths = obtain_most_recent_download_directory_paths()
    downloaded_dfs = obtain_most_recent_downloaded_datasets()

    for activo, temporalidad_dict in download_paths.items():
        for temporalidad, path in temporalidad_dict.items():

            df = downloaded_dfs[activo][temporalidad]
            print(os.listdir(path))
            best_params_file = [f for f in os.listdir(path) if "best_params" in f][0]
            with open(os.path.join(path, best_params_file)) as f:
                best_params = json.load(f)
            params = best_params["best_params"]
            df = squeeze_momentum_indicator(df, **params)
            load_3r_plots(df, activo, temporalidad, path)
