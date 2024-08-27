from typing import Dict

import pandas as pd

from tools.final_plots import load_3r_plots
from utils.utils import (
    create_download_folders,
    obtain_most_recent_download_directory_paths,
)


def load_volume(
    results: Dict[str, Dict[str, pd.DataFrame]], plots: bool = True
) -> None:
    """
    Guarda los datos en disco y crea gráficos si se especifica.
    Parameters:
        results (Dict[str, Dict[str, pd.DataFrame]]): Un diccionario que contiene los resultados de los datos.
            La estructura del diccionario es la siguiente:
            {
                'activo1': {
                    'temporalidad1': DataFrame1,
                    'temporalidad2': DataFrame2,
                    ...
                },
                'activo2': {
                    'temporalidad1': DataFrame3,
                    'temporalidad2': DataFrame4,
                    ...
                },
                ...
            }
        plots (bool, optional): Indica si se deben crear gráficos. Por defecto es True.
    Returns:
        None
    """

    create_download_folders(results)
    download_paths = obtain_most_recent_download_directory_paths()

    for activo, temporalidad_dict in download_paths.items():
        for temporalidad, path in temporalidad_dict.items():
            df = results[activo][temporalidad].copy()
            df.to_parquet(path + "/data.parquet")

            if not plots:
                continue

            load_3r_plots(df, activo, temporalidad, path)
