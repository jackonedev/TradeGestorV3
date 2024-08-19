import datetime as dt
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
