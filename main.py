#!/usr/bin/env python3
import datetime as dt

from etl_feed.feed import extract, transform, load
from etl_feed.feed import temp_mapping_dict



###~  VARIABLES INICIALES  ~###
activos = ["BTC", "ENS"] # TODO: enum contratos
temporalidades = ["4h", "1h", "15m", "5m"]
now = dt.datetime.now()
start_time_list = [temp_mapping_dict[temp] for temp in temporalidades]
end_time = int(dt.datetime.timestamp(now) * 1000)


if __name__ == "__main__":
    data = extract(activos, temporalidades, start_time_list, end_time)
    data_transformed = transform(data)
    load(data_transformed)
    print("ETL completado")
