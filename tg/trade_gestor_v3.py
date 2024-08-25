import hmac
import json
import os
import time
from hashlib import sha256

import requests
from dotenv import load_dotenv

load_dotenv()

APIURL = "https://open-api.bingx.com"
APIKEY = os.environ.get("API_KEY")
SECRETKEY = os.environ.get("SECRET_KEY")


def place_batch(batch):
    """
    Funciona correctamente PERO cuando se envía stopLoss junto con takeProfit, el sistema no lo acepta.
    Entonces sirve solo para asegurar la posición de un solo lado.

    """
    payload = {}
    path = "/openApi/swap/v2/trade/batchOrders"
    method = "POST"
    paramsMap = {"batchOrders": json.dumps(batch)}
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload)


def get_sign(api_secret, payload):
    signature = hmac.new(
        api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256
    ).hexdigest()
    return signature


def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    headers = {
        "X-BX-APIKEY": APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text


def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "":
        return paramsStr + "&timestamp=" + str(int(time.time() * 1000))
    else:
        return paramsStr + "timestamp=" + str(int(time.time() * 1000))
