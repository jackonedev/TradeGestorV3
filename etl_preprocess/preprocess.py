from functools import partial
from itertools import count

import pandas as pd

from tools.optimizer import many_partial_processes
from tools.technical_indicators import squeeze_momentum_indicator
from utils.utils import obtain_download_files_structure

## INITIAL VARIABLES ##
DATASETS_PATH_DICT = obtain_download_files_structure()
DATASETS_DF_DICT = {}
for k, v in DATASETS_PATH_DICT.items():
    DATASETS_DF_DICT[k] = {}
    for kk, vv in v.items():
        DATASETS_DF_DICT[k][kk] = pd.read_parquet(vv)


## OPTIMIZING SQUEEZE MOMENTUM INDICATOR PARAMETERS ##
DATASETS_PARTIAL_DICT = {}
PARTIAL_CALL_LIST = []
PARAMETROS_ORIGINALES = dict(
    length=20, mult=2, length_KC=20, mult_KC=1.5, n_atr=10, use_EMA=True
)
length_KCs = [12, 14, 18, 20, 22]
for activo, temporalidad_dict in DATASETS_DF_DICT.items():
    DATASETS_PARTIAL_DICT[activo] = {}
    for temporalidad, df in temporalidad_dict.items():
        DATASETS_PARTIAL_DICT[activo][temporalidad] = {}
        for l in length_KCs:
            p = PARAMETROS_ORIGINALES.copy()
            p.update({"length_KC": l})
            DATASETS_PARTIAL_DICT[activo][temporalidad][l] = None
            PARTIAL_CALL_LIST.append(partial(squeeze_momentum_indicator, df, **p))

results = many_partial_processes(PARTIAL_CALL_LIST)
c = count()
for activo, temporalidad_dict in DATASETS_PARTIAL_DICT.items():
    for temporalidad, df in temporalidad_dict.items():
        for l in length_KCs:
            DATASETS_PARTIAL_DICT[activo][temporalidad][l] = results[next(c)]

## CONTINUAR OPTIMIZACION:
# Medir la correlación de los resultados con el precio de cierre
# obtener el valor de ventana que optimiza el valor del indicador
# ajustar el resto de los indicadores a esa ventana
# almacenar el valor de la ventana para cada temporalidad.
