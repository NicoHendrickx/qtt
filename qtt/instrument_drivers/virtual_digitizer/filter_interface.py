from abc import ABC

import numpy as np


class FilterInterface(ABC):

    def __init__(self):
        self._filter_functions = list()

    def apply_filters(self, measurement_data: np.ndarray) -> np.ndarray:
        pass

    def bind_filter_function(self, filter_function: FilterInterface) -> None:
        self._filter_functions.append(filter_function)

    def remove_filter_function(self, filter_function: FilterInterface) -> None:
        self._filter_functions.remove(filter_function)
