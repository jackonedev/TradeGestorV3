# Data del año 2021~2022
import hashlib
import hmac
import json
import os
import time
from http.client import HTTPException

import numpy as np
import requests
from dotenv import load_dotenv

from utils.config import CONTRACTS_PATH  # , API_KEY, SECRET_KEY

load_dotenv()

try:
    API_KEY = os.environ["API_KEY"]
    SECRET_KEY = os.environ["SECRET_KEY"]
except KeyError:
    print("\n-CUENTA ONLINE INHABILITADA-\n")

URL = "https://open-api.bingx.com"

BINGX_ERRORS = {
    100001: "signature verification failed",
    100500: "Internal system error",
    80001: "request failed",
    80012: "service unavailable",
    80014: "Invalid parameter",
    80016: "Order does not exist",
    80017: "position does not exist",
}

services = {
    "GET_1": "/openApi/swap/v2/quote/contracts",
    "GET_2": "/openApi/swap/v2/user/balance",
    "GET_3": "/openApi/swap/v2/quote/price",
    "POST_1": "/openApi/swap/v2/trade/order",
    "POST_2": "/openApi/swap/v2/trade/leverage",
    "GET_4": "/openApi/swap/v2/trade/openOrders",
    "GET_5": "/openApi/swap/v2/trade/leverage",
}


def generate_signature(secret_key, query_params):
    """Generar firma encriptada"""
    signature = hmac.new(
        key=secret_key.encode("utf-8"),
        msg=query_params.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return signature


def api_request(service, method="GET", query_params=None, header=False, sign=False):
    """Esta función solo sirve para crear otras funciones, nunca debe ser utilizada por si sola"""
    url = f"{URL}{service}"
    headers = {"Content-Type": "application/json"}
    if header:
        headers.update({"X-BX-APIKEY": API_KEY})

    timestamp = int(time.time() * 1000)
    params = f"timestamp={timestamp}"
    if query_params:
        params += f"&{query_params}"

    if sign:
        signature = generate_signature(SECRET_KEY, params)
        params += f"&signature={signature}"

    url += f"?{params}"
    if method == "GET":
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers)

    if response.status_code != 200:
        print(f"status_code: {response.status_code}")
        print(f"message: {response.text}")
        raise HTTPException()

    response = response.json()
    if "success" in response and not response.get("success"):
        print("status_code=400")
        print(f'detail={BINGX_ERRORS.get(response.get("code"))}')
        raise HTTPException()
    return response


def cargar_contrato(par):
    """Se carga desde los contratos guardados localmente"""

    name_contract = list(
        filter(lambda x: x.startswith(par.upper()), os.listdir(CONTRACTS_PATH))
    )
    if len(name_contract) == 0:
        print("No existen contratos almacenados en el directorio")
        return
    name_contract = name_contract[0]
    file_dir = os.path.join(CONTRACTS_PATH, name_contract)
    with open(file_dir, "r") as f:
        contract = json.load(f)
    return contract


def actualizar_contratos():
    """Se conecta a la API de BingX y descarga todos los contratos futuros disponibles en el disco local"""
    contracts = api_request(services["GET_1"], header=False)
    data = contracts["data"]
    for i in range(len(data)):
        name_asset = contracts["data"][i]["symbol"]
        dir_name = os.path.join(CONTRACTS_PATH, f"{name_asset}.json")
        with open(dir_name, "w") as f:
            json.dump(data[i], f)


def get_account_balance():
    account_balance = api_request(
        services["GET_2"], method="GET", header=True, sign=True
    )
    return np.floor(float(account_balance["data"]["balance"]["balance"]))


def get_price(symbol):
    try:
        return float(
            api_request(services["GET_3"], query_params=f"symbol={symbol}")["data"][
                "price"
            ]
        )
    except:
        print("Error al obtener precio...\nPor favor ingreselo manualmente")
        return float(input("Precio de {} = ".format(symbol)))
