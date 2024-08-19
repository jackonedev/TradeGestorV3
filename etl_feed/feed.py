import concurrent.futures
import datetime as dt
from typing import Dict, List

import pandas as pd
import requests

from tools.dates import past_timestamp
from utils.utils import create_download_folders

### ~  VARIABLES DE ENTORNO  ~###
# .1. Preparacion del request #TODO: (.env)
URL = "https://open-api.bingx.com"
PATH = "/openApi/swap/v2/quote/klines"
SERVICE = URL + PATH
LIMIT = 555
# .2. Determinación de los periodos de cada temporalidad
now = dt.datetime.now()
temp_mapping_dict = {  # TODO: pydantic
    "1w": int(past_timestamp(400, "days", now)),
    "1d": int(past_timestamp(180, "days", now)),
    "4h": int(past_timestamp(30, "days", now)),
    "1h": int(past_timestamp(8, "days", now)),
    "15m": int(past_timestamp(36, "hours", now)),
    "5m": int(past_timestamp(12, "hours", now)),
}


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
    for i, activo in enumerate(activos):
        results[activo] = {}
        for j, temporalidad in enumerate(temporalidades):
            df = pd.DataFrame(data[activo][temporalidad])
            df["time"] = pd.to_datetime(df["time"], unit="ms")
            df["time"] = df["time"] - pd.DateOffset(hours=3)
            df = df.set_index("time")
            # TODO: APLICAR INDICADORES
            results[activo][temporalidad] = df.copy()
    print("Transformación de datos completada")
    return results


def load(results: Dict[str, Dict[str, pd.DataFrame]]) -> None:
    """
    Guardar datos en disco
    """
    download_folders = create_download_folders(results)
    activos = list(results.keys())
    temporalidades = list(results[activos[0]].keys())
    for i, activo in enumerate(activos):
        for j, temporalidad in enumerate(temporalidades):
            results[activo][temporalidad].to_parquet(
                download_folders[i * len(temporalidades) + j] + "/data.parquet"
            )
    print("Descarga de datos completada")
