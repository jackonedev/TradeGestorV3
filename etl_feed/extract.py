import concurrent.futures
from typing import Dict, List

import requests

from utils.config import KLINES_LIMIT as LIMIT
from utils.config import KLINES_SERVICE as SERVICE


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
