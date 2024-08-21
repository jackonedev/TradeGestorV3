#!/usr/bin/env python3
import datetime as dt

from etl_feed.feed import extract, load, transform
from schemas.temporality import TempMappingModel
from tools.dates import past_timestamp

### ~  VARIABLES INICIALES  ~###
activos = ["BTC", "ENS"]  # TODO: enum contratos
temporalidades = ["4h", "1h", "15m", "5m"]

temp_mapping = TempMappingModel(
    t_1h=past_timestamp(10, "days"),
)

start_time_list = [temp_mapping.to_dict()[temp] for temp in temporalidades]
end_time = int(dt.datetime.timestamp(temp_mapping._now) * 1000)


if __name__ == "__main__":
    data = extract(activos, temporalidades, start_time_list, end_time)
    data_transformed = transform(data)
    load(data_transformed)
    print("ETL completado")
