#!/usr/bin/env python3
import datetime as dt

from etl_feed.extract import extract
from etl_feed.load import load
from etl_feed.load_volume import load_volume
from etl_feed.transform import transform
from etl_feed.transform_OP import transform_OP
from etl_preprocess.reload_plots import reload_plots
from etl_preprocess.sqzm_optimization_process import optimize_sqzm_parameters
from schemas.temporality import TempMappingModel
from tools.dates import past_timestamp
from utils.utils import obtain_most_recent_download_directory_paths


### ~  VARIABLES INICIALES  ~###
def settings():
    """
    Configuración inicial
    """
    global activos, temporalidades, download_html_plot, include_volume, OPTIMIZE_SQZM, REPLOT
    activos = ["APE", "LTC", "ADA", "ENS", "ICP", "DOGE", "LINK"]
    activos = ["ICP"]
    activos = ["ENS"]
    activos = ["BTC", "ETH"]
    activos = ["BTC"]

    temporalidades = []  # empty list = all temporalities
    # temporalidades += ["5m"]
    # temporalidades += ["15m"]
    temporalidades += ["30m"]
    # temporalidades += ["1h"]
    temporalidades += ["4h"]
    temporalidades += ["1d"]
    temporalidades += ["1w"]
    download_html_plot = True
    include_volume = True
    OPTIMIZE_SQZM = True
    REPLOT = True


def main():
    global activos, temporalidades, download_html_plot, include_volume

    # Step 1:
    # Extract data from Exchange
    # Ajuste manual de las ventana de extracción
    temp_mapping = TempMappingModel(
        t_1w=past_timestamp(600, "days"),
        t_4h=past_timestamp(60, "days"),
        t_1h=past_timestamp(30, "days"),
        t_30m=past_timestamp(4, "days"),
        t_15m=past_timestamp(3, "days"),
        t_5m=past_timestamp(2, "days"),
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

    if OPTIMIZE_SQZM:
        print("Iniciando optimización de parámetros")
        optimize_sqzm_parameters()
        print("Optimización de parámetros completada")

        if REPLOT:
            print("Recargando gráficos")
            download_paths = obtain_most_recent_download_directory_paths()
            reload_plots()
            print("Recarga de gráficos completada")
