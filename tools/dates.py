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


def retrasar_horas(fecha, hora=3):
    """Comprueba si la fecha y hora están completas y les resta tres horas"""
    # Comprobar si es una cadena de texto
    if isinstance(fecha, str):
        if fecha.find(":") == -1:
            # No es una fecha y hora completa, no se aplica el retraso
            return fecha
    fecha_hora_retrasada = pd.to_datetime(fecha) - datetime.timedelta(hours=hora)
    return fecha_hora_retrasada.strftime("%Y-%m-%d %H:%M:%S")
