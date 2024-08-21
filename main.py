#!/usr/bin/env python3
import datetime as dt

from etl_feed.extract import extract
from etl_feed.load import load
from etl_feed.transform import transform
from schemas.temporality import TempMappingModel
from tools.dates import past_timestamp

### ~  VARIABLES INICIALES  ~###
activos = ["BTC", "ENS"]  # TODO: Enum contratos
temporalidades = ["4h", "1h", "15m", "5m"]  # empty list = all temporalities


if __name__ == "__main__":
    # Ejemplo ajustando solo 1h para obtener datos de los últimos 10 días
    # el resto de las temporalidades tomarán los valores por default
    temp_mapping = TempMappingModel(
        t_1h=past_timestamp(10, "days"),
    )

    if len(temporalidades) == 0:
        temporalidades = list(temp_mapping.to_dict().keys())

    start_time_list = (
        [temp_mapping.to_dict()[temp] for temp in temporalidades]
        if len(temporalidades) > 0
        else list(temp_mapping.to_dict().values())
    )
    end_time = int(dt.datetime.timestamp(temp_mapping._now) * 1000)

    data = extract(activos, temporalidades, start_time_list, end_time)
    data_transformed = transform(data)
    load(data_transformed)
    print("ETL completado")
