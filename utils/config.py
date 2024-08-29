import os

# Configuración de variables de entorno
# para hacer requests al exchange BingX
URL = "https://open-api.bingx.com"
KLINES_SERVICE = URL + "/openApi/swap/v2/quote/klines"
KLINES_LIMIT = 1000


# Configuración de directorios del proyecto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_PATH = os.path.join(PROJECT_ROOT, "datasets")

if not os.path.exists(DATASETS_PATH):
    os.makedirs(DATASETS_PATH)

TRADE_GESTOR_PATH = os.path.join(PROJECT_ROOT, "tg")
CONTRACTS_PATH = os.path.join(TRADE_GESTOR_PATH, "contracts")
if not os.path.exists(CONTRACTS_PATH):
    os.makedirs(CONTRACTS_PATH)
