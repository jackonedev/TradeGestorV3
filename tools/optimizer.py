import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from typing import Callable, Iterable, List, Tuple


def run_func(
    func: Callable, args: Tuple, results: List, index: int, verbose: bool = False
):
    """
    Run a function with given arguments and store the result in the shared list.

    Args:
        func (Callable): The function to be executed.
        args (Iterable): The arguments to be passed to the function.
        results (List): The shared list to store the results.
        index (int): The index at which to store the result.
    """
    if verbose:
        print(f'Initializing "{func.__name__}" execution with index [{index}]')
    result = func(*args)
    results.append((index, result))


def run_partial_mp(func: Callable, results: List, index: int, verbose: bool = False):
    """
    Run a partial function and store the result in the shared list.

    Args:
        func (Callable): The partial function to be executed.
        results (List): The shared list to store the results.
        index (int): The index at which to store the result.
    """
    if verbose:
        print(
            f'Initializing "{func.func.__name__}" multiprocessing execution with index [{index}]'
        )
    result = func()
    results.append((index, result))


def run_partial_th(func: Callable, index: int, verbose: bool = False):
    """
    Ejecuta una función parcial y devuelve el resultado junto con su índice.

    Args:
        func (Callable): La función parcial a ejecutar.
        index (int): El índice del resultado.

    Returns:
        tuple: Una tupla que contiene el índice y el resultado de la función.
    """
    if verbose:
        print(f'Executing "{func.func.__name__}" at thread index [{index}]')
    result = func()
    return index, result


def sort_results(original_list):
    """
    Sort results by the index.

    Args:
        results (List): A list of tuples containing index and result.

    Returns:
        List: A sorted list of results.
    """
    sorted_list = sorted(original_list, key=lambda x: x[0])
    ordered_results = [result[1] for result in sorted_list]
    return ordered_results


def one_func_many_args(
    func: Callable,
    args: List[Tuple],
    num_workers: int = mp.cpu_count(),
    verbose: bool = False,
):
    """
    Multiprocessing, parallelism: Execute the same function with many different arguments.

    Args:
        func (Callable): The function to be executed.
        args (List[Tuple]): A list of tuples containing the arguments for each function call.
        num_workers (int, optional): The number of worker processes to use. Defaults to the number of CPUs.

    Returns:
        List: A sorted list of results from each function call.
    """

    assert isinstance(args, list), "args must be a list of arguments"
    assert isinstance(args[0], tuple), "args must be a list of tuples"

    with mp.Manager() as manager:
        results = manager.list()
        with mp.Pool(num_workers) as pool:
            for i, arg in enumerate(args):
                pool.apply_async(run_func, args=(func, arg, results, i, verbose))
            pool.close()
            pool.join()

        return sort_results(list(results))


def many_funcs_one_arg(
    funcs: List[Callable],
    *args: Iterable,
    num_workers: int = mp.cpu_count(),
    verbose: bool = False,
):
    """
    Multiprocessing, parallelism: Execute many functions with the same arguments.

    Args:
        funcs (List[Callable]): A list of functions to be executed.
        *args (Iterable): The arguments to be passed to the functions.
        num_workers (int, optional): The number of worker processes to use. Defaults to the number of CPUs.

    Returns:
        List: A sorted list of the results from executing the functions.
    """

    if len(funcs) > 4:
        print("This function will execute a maximum of 4 functions")
        raise SystemError

    with mp.Manager() as manager:
        results = manager.list()
        with mp.Pool(num_workers) as pool:
            for i, func in enumerate(funcs):
                pool.apply_async(run_func, args=(func, args, results, i, verbose))
            pool.close()
            pool.join()

        return sort_results(list(results))


def many_partial_processes(
    partial_funcs: List[Callable],
    num_workers: int = mp.cpu_count(),
    verbose: bool = False,
):
    """
    Execute a list of partial functions in parallel.

    Args:
        partial_funcs (List[Callable]): A list of partial function objects to be executed.
        num_workers (int, optional): The number of worker processes to use. Defaults to the number of CPUs.

    Returns:
        List: A sorted list of results from each partial function call.
    """
    assert isinstance(
        partial_funcs, list
    ), "partial_funcs must be a list of partial functions"
    assert all(
        isinstance(func, partial) for func in partial_funcs
    ), "All elements in partial_funcs must be partial objects"

    with mp.Manager() as manager:
        results = manager.list()
        with mp.Pool(num_workers) as pool:
            for i, func in enumerate(partial_funcs):
                pool.apply_async(run_partial_mp, args=(func, results, i, verbose))
            pool.close()
            pool.join()

        return sort_results(list(results))


def many_partial_threads(
    partial_funcs: List[Callable], max_workers: int = None, verbose: bool = False
) -> List:
    """
    Ejecuta una lista de funciones parciales en paralelo utilizando hilos.

    Args:
        partial_funcs (List[Callable]): Una lista de objetos de función parcial.
        max_workers (int, optional): El número máximo de hilos a utilizar. Si no se especifica,
                                    se determinará automáticamente.

    Returns:
        List: Una lista ordenada de resultados de cada función parcial.
    """
    assert isinstance(
        partial_funcs, list
    ), "partial_funcs debe ser una lista de funciones parciales"
    assert all(
        isinstance(func, partial) for func in partial_funcs
    ), "Todos los elementos de partial_funcs deben ser objetos partial"

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(run_partial_th, func, i, verbose): i
            for i, func in enumerate(partial_funcs)
        }

        for future in as_completed(future_to_index):
            index, result = future.result()
            results.append((index, result))

    results.sort(key=lambda x: x[0])
    return [result[1] for result in results]
