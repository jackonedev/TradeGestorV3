import json
import os
from functools import partial

from etl_preprocess.calculate_positions import (
    adjust_positions_leverage,
    return_positions,
    return_targets,
)
from tg.trade_gestor_v1 import (
    actualizar_contratos,
    cargar_contrato,
    get_account_balance,
)
from tg.trade_gestor_v2 import get_current_orders, switch_leverage, post_order
# from tg.trade_gestor_v3 import place_batch
from tools.optimizer import many_partial_threads
from utils.config import CONTRACTS_PATH
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)


def account_settings():
    global acc_vol, risk_pct, op_vol
    acc_vol = get_account_balance()
    risk_pct = 0.1
    op_vol = acc_vol * risk_pct


def trade_settings():
    global direction, currency, live, market, limit
    direction = "short"
    currency = "USDT"
    live = True
    market = True
    limit = True


def check_for_contracts():
    contracts = os.listdir(CONTRACTS_PATH)
    if not contracts:
        actualizar_contratos()


def _asset_settings(asset):
    global par, currency, symbol, qty_precision, price_precision, max_leverage_l, max_leverage_s
    contract = cargar_contrato(f"{asset}-{currency}")
    assert contract, f"No se encontró el contrato para {asset}"
    par = contract["asset"]
    symbol = contract["symbol"]
    qty_precision = contract["quantityPrecision"]
    price_precision = contract["pricePrecision"]
    max_leverage_l = int(contract["maxLongLeverage"])
    max_leverage_s = int(contract["maxShortLeverage"])


if __name__ == "__main__":
    account_settings()
    trade_settings()
    check_for_contracts()

    download_paths = obtain_most_recent_download_directory_paths()
    downloaded_dfs = obtain_most_recent_downloaded_datasets()

    targets = return_targets(downloaded_dfs, live)
    positions = return_positions(targets, direction, op_vol, market, limit, live)
    adj_positions = adjust_positions_leverage(positions, direction, live)

    # Creación del batch de órdenes
    for asset, orders_list in adj_positions.items():
        _asset_settings(asset)
        # .1. Ajustar apalancamiento para el par

        current_orders = get_current_orders(symbol)
        existing_orders = current_orders.get("data", {}).get("orders", [])
        if len(existing_orders) > 0:
            for ord in existing_orders:
                if ord.get("symbol") == symbol:
                    print("Existen posiciones previas, se cancela la ejecución")
                    raise Exception("Existen posiciones previas")

        lev = orders_list[0].get("lev")
        lev_res = switch_leverage(symbol, direction.upper(), lev)
        assert (
            lev_res.get("code") == 0
        ), f"Error al ajustar el apalancamiento: {lev_res}"

        # # .2. Verificar volumen mínimo permitido y margen disponible
        # vol_per_trade = orders_list[0].get("vol_per_entry")
        # #TODO: check min volume allowed

    for asset, orders_list in adj_positions.items():
        _asset_settings(asset)
        asset_path = download_paths.get(asset)
        temp = list(asset_path.keys())[0]
        ASSET_PATH = asset_path.get(temp).rsplit("/", 1)[0]

        # .1. Ajustar apalancamiento para el par
        current_orders = get_current_orders(symbol)
        existing_orders = current_orders.get("data", {}).get("orders", [])
        if len(existing_orders) > 0:
            for ord in existing_orders:
                if ord.get("symbol") == symbol:
                    print("Existen posiciones previas, se cancela la ejecución")
                    raise Exception("Existen posiciones previas")

        lev = orders_list[0].get("lev")
        lev_res = switch_leverage(symbol, direction.upper(), lev)
        assert (
            lev_res.get("code") == 0
        ), f"Error al ajustar el apalancamiento: {lev_res}"

        # # .2. Verificar volumen mínimo permitido y margen disponible
        # vol_per_trade = orders_list[0].get("vol_per_entry")
        # #TODO: check min volume allowed

        orden_batches = []
        trailing_batches = []
        partial_calls = []
        for order in orders_list:
            # .3. Obtener la cantidad de activo por orden
            qty_list = order.get("qty_per_entry")
            for i, target in enumerate(order.get("operations").values()):
                # .4. Obtener targets y cantidad
                sl, entry, tp = target
                qty = qty_list[i]

                # .5. Crear Request
                if direction == "long":
                    orden = {
                        "symbol": symbol,
                        "side": "BUY",
                        "positionSide": "LONG",
                        "type": "LIMIT",
                        "stopPrice": entry,
                        "price": entry,
                        "quantity": qty,
                        "takeProfit": json.dumps(
                            {
                                "type": "TAKE_PROFIT_MARKET",
                                "stopPrice": tp,
                                "price": tp,
                                "workingType": "MARK_PRICE",
                            }
                        ),
                        "stopLoss": json.dumps(
                            {
                                "type": "STOP_MARKET",
                                "stopPrice": sl,
                                "price": sl,
                                "workingType": "MARK_PRICE",
                            }
                        ),
                    }

                elif direction == "short":
                    orden = {
                        "symbol": symbol,
                        "side": "SELL",
                        "positionSide": "SHORT",
                        "type": "LIMIT",
                        "stopPrice": entry,
                        "price": entry,
                        "quantity": qty,
                        "stopLoss": json.dumps(
                            {
                                "type": "STOP_MARKET",
                                "stopPrice": sl,
                                "price": sl,
                                "workingType": "MARK_PRICE",
                            }
                        ),
                        "takeProfit": json.dumps(
                            {
                                "type": "TAKE_PROFIT_MARKET",
                                "stopPrice": tp,
                                "price": tp,
                                "workingType": "MARK_PRICE",
                            }
                        ),
                    }
                    
                    partial_calls.append(partial(post_order, **orden))

                take_profit = {
                    "symbol": symbol,
                    "side": "SELL",
                    "positionSide": "LONG",
                    "type": "TRAILING_TP_SL",
                    "priceRate": 0.03,
                    "stopPrice": tp,
                    "price": tp,
                    "quantity": qty,
                }
                orden_batches.append(orden)
                trailing_batches.append(take_profit)

        # .7. Enviar Batch
        # .8. Almacenar batch en datasets/
        try:
            # res = place_batch(orden_batches)
            res_list = many_partial_threads(partial_calls)
            for i, res in enumerate(res_list):
                with open(f"{ASSET_PATH}/response_{i+1}.json", "w") as f:
                    f.write(json.dumps(res, indent=2))
                
            # place_batch(takeprofit_batches)
            print(f"Batch enviado: {res}")
        except Exception as e:
            print(f"Error al enviar el batch: {e}")
            with open(f"{ASSET_PATH}/error.txt", "w") as f:
                f.write(str(e))
        finally:
            with open(f"{ASSET_PATH}/trailing.json", "w") as f:
                f.write(json.dumps(trailing_batches, indent=2))
            with open(f"{ASSET_PATH}/orders.json", "w") as f:
                f.write(json.dumps(orders_list, indent=2))
