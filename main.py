#!/usr/bin/env python3
import datetime as dt

from etl_feed.extract import extract
from etl_feed.load import load
from etl_feed.load_volume import load_volume
from etl_feed.transform import transform
from etl_feed.transform_OP import transform_OP
from schemas.temporality import TempMappingModel
from tools.dates import past_timestamp


### ~  VARIABLES INICIALES  ~###
def settings():
    """
    Configuración inicial
    """
    global activos, temporalidades, download_html_plot, include_volume
    activos = ["BTC", "ENS"]
    temporalidades = []  # empty list = all temporalities
    temporalidades = ["4h"]  # Auxiliar
    temporalidades = ["1h", "15m", "5m"]
    temporalidades = ["5m"]
    download_html_plot = True
    include_volume = False


def main():
    global activos, temporalidades, download_html_plot, include_volume
    
    # Step 1:
    # Extract data from Exchange
    # Ajuste manual de las ventana de extracción
    temp_mapping = TempMappingModel(
        t_1w=past_timestamp(600, "days"),
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
    print("Extracción de datos completada")

    # Step 2:
    # Apply technical indicators
    data_transformed = transform_OP(data)
    print("Transformación de datos completada")

    # Step 3:
    # load data locally in parquet format
    # load plots in html format
    if include_volume:
        load_volume(data_transformed, download_html_plot)
    else:
        load(data_transformed, download_html_plot)
    print("Descarga de datos completada")


if __name__ == "__main__":
    settings()
    main()
    print("ETL completado")
