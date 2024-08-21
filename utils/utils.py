import datetime as dt
import itertools
import os
import random

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


def obtain_download_files_structure() -> dict:
    "Devuelve la lista de nombres de los archivos de descarga"
    DATASETS_NAME = obtain_most_recent_download_name()
    DATASETS_DIR = os.path.join(DATASETS_PATH, DATASETS_NAME)
    CURRENCY_LIST = os.listdir(DATASETS_DIR)
    TEMPORALITY_LIST = os.listdir(os.path.join(DATASETS_DIR, CURRENCY_LIST[0]))

    structure = {}
    for currency in CURRENCY_LIST:
        structure[currency] = {}
        for temporalidad in TEMPORALITY_LIST:
            structure[currency][temporalidad] = os.path.join(
                DATASETS_DIR, currency, temporalidad, "data.parquet"
            )

    return structure
