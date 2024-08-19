import datetime

import pandas as pd


def past_timestamp(cantidad, periodo, date):
    "Devuelve en milisegundos el timestamp de hace 'cantidad' 'periodo'"
    if periodo == "mins":
        delta = datetime.timedelta(minutes=cantidad)
    elif periodo == "hours":
        delta = datetime.timedelta(hours=cantidad)
    elif periodo == "days":
        delta = datetime.timedelta(days=cantidad)
    else:
        raise ValueError("Período inválido")

    past = date - delta
    timestamp = datetime.datetime.timestamp(past)
    return timestamp * 1000
