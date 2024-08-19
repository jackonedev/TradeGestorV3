import concurrent.futures
import datetime

import pandas as pd
import requests

from tools.dates import past_timestamp
from utils.utils import create_download_folders

# Variables iniciales
activos = ["BTC", "LTC", "XRP", "ETH"]
temporalidades = ["1w", "1d", "4h", "1h", "15m", "5m"]
# Filtros:
temp_altas = temporalidades[:3]
temp_bajas = temporalidades[3:]
now = datetime.datetime.now()
start_time_list = [
    int(past_timestamp(400, "days", now)),
    int(past_timestamp(180, "days", now)),
    int(past_timestamp(30, "days", now)),
    int(past_timestamp(8, "days", now)),
    int(past_timestamp(36, "hours", now)),
    int(past_timestamp(12, "hours", now)),
]

# Preparacion del request
URL = "https://open-api.bingx.com"
PATH = "/openApi/swap/v2/quote/klines"
SERVICE = URL + PATH
LIMIT = 555
end_time = int(datetime.datetime.timestamp(now) * 1000)

# Ejecución del request
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

    for i, activo in enumerate(activos):
        data[activo] = {}
        for j, interval in enumerate(temporalidades):
            response = futures_submit[i * len(temporalidades) + j].result()
            df = pd.DataFrame(response.json().get("data"))
            df["time"] = pd.to_datetime(df["time"], unit="ms")
            data[activo][interval] = df.copy()

print("Extracción de datos completada")


# df = df.set_index("time")
# print("Transformación de datos completada")


# Descargar datos
download_folders = create_download_folders(data)
for i, activo in enumerate(activos):
    for j, temporalidad in enumerate(temporalidades):
        data[activo][temporalidad].to_parquet(
            download_folders[i * len(temporalidades) + j] + "/data.parquet"
        )
print("Descarga de datos completada")
