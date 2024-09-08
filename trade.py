import datetime as dt
import json
import os
import time
from functools import partial
from itertools import count

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
from tg.trade_gestor_v2 import get_current_orders, post_order, switch_leverage
from tg.trade_gestor_v3 import get_orders
from tools.optimizer import many_partial_threads
from utils.config import CONTRACTS_PATH
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)


def account_settings():
    global acc_vol, risk_pct, op_vol
    acc_vol = get_account_balance()
    risk_pct = 0.005
    op_vol = acc_vol * risk_pct


def trade_settings():
    global direction, currency, live, execute, market, limit
    direction = "long"
    currency = "USDT"
    live = True
    execute = False
    market = True
    limit = True


def check_for_contracts():
    contracts = os.listdir(CONTRACTS_PATH)
    if not contracts:
        actualizar_contratos()


def _asset_settings(asset):
    global par, currency, symbol
    contract = cargar_contrato(f"{asset}-{currency}")
    assert contract, f"No se encontró el contrato para {asset}"
    symbol = contract["symbol"]


if __name__ == "__main__":
    account_settings()
    trade_settings()
    check_for_contracts()

    download_paths = obtain_most_recent_download_directory_paths()
    downloaded_dfs = obtain_most_recent_downloaded_datasets()

    targets = return_targets(downloaded_dfs, live)
    n_assets = len(targets)
    n_temporlaties = len(targets[list(targets.keys())[0]])
    if market and limit:
        op_vol *= 8
    elif market:
        op_vol *= 2
    elif limit:
        op_vol *= 6
    op_vol *= n_assets * n_temporlaties
    positions = return_positions(targets, direction, op_vol, market, limit, live)
    adj_positions = adjust_positions_leverage(positions, direction, live)

    for asset, orders_list in adj_positions.items():
        _asset_settings(asset)
        asset_path = download_paths.get(asset)
        temp = list(asset_path.keys())[0]
        ASSET_PATH = asset_path.get(temp).rsplit("/", 1)[0]

        # .1. Ajustar apalancamiento para el par
        current_orders = get_orders(symbol)
        existing_orders = current_orders.get("data", {}).get("orders", [])
        if direction.upper() in [r["positionSide"] for r in existing_orders]:
            raise ValueError("Ya existen ordenes en el sentido indicado")

        lev = orders_list[0].get("lev")
        # handling edge cases
        lev_res = switch_leverage(symbol, direction.upper(), lev)
        # if lev_res.get("code") == 80014 and lev_res.get("msg") == "Invalid parameters, err:leverage: Key: 'APISetLeverageRequest.Leverage' Error:Field validation for 'Leverage' failed on the 'gt' tag.":
        #    print("Probablemente estés operando en demasiadas temporalidades de forma simultánea")
        #    print("Probablemente la temporalidad 1w falle, la cosa es 1d + 1w tiró el mismo error")
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
            batch_size = 3
            counter = count()
            for i in range(0, len(partial_calls), batch_size):
                batch = partial_calls[i : i + batch_size]
                if live and execute:
                    res_list = many_partial_threads(batch)
                    pass

                for j in range(len(batch)):  # usar len(batch)
                    c = next(counter)
                    with open(f"{ASSET_PATH}/{asset}_request_{c+1}.json", "w") as f:
                        f.write(json.dumps(orden_batches[c], indent=2))
                    if live and execute:
                        with open(
                            f"{ASSET_PATH}/{asset}_response_{c+1}.json", "w"
                        ) as f:
                            f.write(json.dumps(res_list[j], indent=2))
                time.sleep(0.25)

                # for res in res_list:
                #     c = next(counter)
                #     with open(f"{ASSET_PATH}/{asset}_request_{c+1}.json", "w") as f:
                #         f.write(json.dumps(orden_batches[c], indent=2))
                #     with open(f"{ASSET_PATH}/{asset}_response_{c+1}.json", "w") as f:
                #         f.write(json.dumps(res, indent=2))
                # time.sleep(0.2)

        except Exception as e:
            print(f"Error al enviar el batch: {e}")
            with open(f"{ASSET_PATH}/error.txt", "a") as f:
                f.write(str(e) + "\n")
        finally:
            with open(f"{ASSET_PATH}/acc_init_balance.txt", "w") as f:
                date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Fecha: {date}\n Balance Cta: {acc_vol}")
            with open(f"{ASSET_PATH}/trailing.json", "w") as f:
                f.write(json.dumps(trailing_batches, indent=2))
            with open(f"{ASSET_PATH}/orders.json", "w") as f:
                f.write(json.dumps(orders_list, indent=2))
