import datetime as dt
import os
import random

import pandas as pd

from utils.config import DATASETS_PATH


def create_download_folders(data):
    os.system("make create_enum_folder")
    download_folders = os.listdir(DATASETS_PATH)
    fecha = dt.datetime.now().strftime("%Y-%m-%d")
    n = max([int(c.split("_")[-1]) for c in download_folders if c.startswith(fecha)])
    working_folder = f"{fecha}_{n}"
    activos = data.keys()
    temporalidades = data.get(random.choice(list(data.keys()))).keys()
    final_folders = []
    for activo in activos:
        for temporalidad in temporalidades:
            folder_name = os.path.join(
                DATASETS_PATH, working_folder, activo, temporalidad
            )
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, exist_ok=True)
            final_folders.append(folder_name)

    return final_folders


def obtain_most_recent_download_name():
    "Devuelve el nombre del directorio de desarga más reciente en DATASETS_PATH"
    lista = os.listdir(DATASETS_PATH)
    lista_ordenada = sorted(
        lista,
        key=lambda x: (
            dt.datetime.strptime(x.split("_")[0], "%Y-%m-%d"),
            int(x.split("_")[1]),
        ),
        reverse=True,
    )
    return lista_ordenada[0]


def obtain_most_recent_download_directory_paths() -> dict:
    "Devuelve la lista de nombres de los archivos de descarga"
    dir_name = obtain_most_recent_download_name()
    dir_path = os.path.join(DATASETS_PATH, dir_name)
    currency_list = os.listdir(dir_path)
    temporality_list = os.listdir(os.path.join(dir_path, currency_list[0]))
    structure = {}
    for currency in currency_list:
        structure[currency] = {}
        for temporalidad in temporality_list:
            structure[currency][temporalidad] = os.path.join(
                dir_path, currency, temporalidad
            )
    return structure


def obtain_most_recent_downloaded_datasets():
    datasets_path_dict = obtain_most_recent_download_directory_paths()
    datasets_df_dict = {}
    for k, v in datasets_path_dict.items():
        datasets_df_dict[k] = {}
        for kk, vv in v.items():
            if os.path.isdir(vv):
                datasets_df_dict[k][kk] = pd.read_parquet(f"{vv}/data.parquet")

    return datasets_df_dict
