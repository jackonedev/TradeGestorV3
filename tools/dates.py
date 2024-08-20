import datetime as dt


def past_timestamp(cantidad, periodo, date=dt.datetime.now()):
    "Devuelve en milisegundos el timestamp de hace 'cantidad' 'periodo'"
    if periodo == "mins":
        delta = dt.timedelta(minutes=cantidad)
    elif periodo == "hours":
        delta = dt.timedelta(hours=cantidad)
    elif periodo == "days":
        delta = dt.timedelta(days=cantidad)
    else:
        raise ValueError("Período inválido")

    past = date - delta
    timestamp = dt.datetime.timestamp(past)
    return int(timestamp * 1000)
