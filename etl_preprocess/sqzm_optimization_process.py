import json
from functools import partial
from itertools import product
from random import randint

from tools.optimizer import many_partial_processes
from tools.technical_indicators import squeeze_momentum_indicator
from utils.utils import (
    obtain_most_recent_download_directory_paths,
    obtain_most_recent_downloaded_datasets,
)


def load_data():
    """Load the dataset and the corresponding download paths"""
    download_paths = obtain_most_recent_download_directory_paths()
    downloaded_dfs = obtain_most_recent_downloaded_datasets()
    return download_paths, downloaded_dfs


def generate_parameter_combinations():
    """Generate a combination of possible parameters to be assigned to the Squeeze Momentum Indicator"""
    original_params = {
        "length": 20,
        "mult": 1.5,
        "length_KC": 20,
        "mult_KC": 1,
        "n_atr": 12,
        "use_EMA": True,
    }
    length_bbs = [8, 12, 14, 18, 20, 22, 26]
    mult_range = [1.5]
    length_kcs = [8, 12, 14, 18, 20, 22, 26]
    mult_kc_range = [1]
    param_combinations = list(
        product(length_bbs, mult_range, length_kcs, mult_kc_range)
    )
    return original_params, param_combinations


def apply_squeeze_momentum_indicator(
    downloaded_dfs, original_params, param_combinations
):
    """Apply the Squeeze Momentum Indicator to the datasets with different parameter combinations"""
    datasets_partial_dict = {}
    datasets_param_dict = {}
    for asset, timeframe_dict in downloaded_dfs.items():
        datasets_partial_dict[asset] = {}
        datasets_param_dict[asset] = {}
        for timeframe, df in timeframe_dict.items():
            partial_list = []
            param_list = []
            for x in param_combinations:
                params = original_params.copy()
                params.update(dict(zip(["length", "mult", "length_KC", "mult_KC"], x)))
                partial_list.append(partial(squeeze_momentum_indicator, df, **params))
                param_list.append(params.copy())
            datasets_partial_dict[asset][timeframe] = partial_list.copy()
            datasets_param_dict[asset][timeframe] = param_list.copy()
    return datasets_partial_dict, datasets_param_dict


def execute_optimization(datasets_partial_dict, datasets_param_dict):
    """Execute the optimization using multiple processes"""
    result_dict = {}
    for asset, timeframe_dict in datasets_partial_dict.items():
        result_dict[asset] = {}
        for timeframe, partial_list in timeframe_dict.items():
            result_dict[asset][timeframe] = {}
            results = many_partial_processes(partial_list)
            result_list = []
            for i, result in enumerate(results):
                result_list.append(
                    (datasets_param_dict[asset][timeframe][i], result.copy())
                )
            result_dict[asset][timeframe] = result_list.copy()
    return result_dict


def calculate_correlation(result_dict):
    """Calculate the correlation between the close price and the Squeeze Momentum Indicator"""
    best_corr_dict = {}
    corr_dict = {}
    for asset, timeframe_dict in result_dict.items():
        best_corr_dict[asset] = {}
        corr_dict[asset] = {}
        for timeframe, results_list in timeframe_dict.items():
            best_corr = 0
            best_params = None
            corr_list = []
            for params, df in results_list:
                corr = df["close"].corr(df["SQZMOM_value"])
                corr_list.append({"corr": corr, "params": params})
                if corr > best_corr:
                    best_corr = corr
                    best_params = params.copy()

            corr_dict[asset][timeframe] = corr_list
            best_corr_dict[asset][timeframe] = {
                "best_corr": best_corr,
                "best_params": best_params,
            }
    return best_corr_dict, corr_dict


def save_results(download_paths, best_corr_dict, corr_dict):
    """Save the results to JSON files"""
    for asset, timeframe_dict in best_corr_dict.items():
        for timeframe, corr in timeframe_dict.items():
            dir_path = download_paths[asset][timeframe]
            rand = randint(100, 999)
            with open(
                f"{dir_path}/{asset}_{timeframe}_sqzmom_best_params_{rand}.json", "w"
            ) as f:
                json.dump(corr, f)
            with open(
                f"{dir_path}/{asset}_{timeframe}_sqzmom_params_{rand}.json", "w"
            ) as f:
                json.dump(json.dumps(corr_dict[asset][timeframe], indent=2), f)


def optimize_sqzm_parameters():
    """Execute the optimization process of the Squeeze Momentum Indicator parameters"""
    download_paths, downloaded_dfs = load_data()
    original_params, param_combinations = generate_parameter_combinations()
    datasets_partial_dict, datasets_param_dict = apply_squeeze_momentum_indicator(
        downloaded_dfs, original_params, param_combinations
    )
    result_dict = execute_optimization(datasets_partial_dict, datasets_param_dict)
    best_corr_dict, corr_dict = calculate_correlation(result_dict)
    save_results(download_paths, best_corr_dict, corr_dict)
