from abc import ABC, abstractmethod
from typing import Any, List

from qtt.new.acquisition.interfaces import AcquisitionInterface


class AcquisitionScopeInterface(AcquisitionInterface):

    @property
    @abstractmethod
    def number_of_averages(self)-> int:
        pass

    @property
    @abstractmethod
    def sampling_rate(self)-> float:
        pass

    @property
    @abstractmethod
    def period(self)-> float:
        pass

    @property
    @abstractmethod
    def input_range(self)-> float:
        pass
