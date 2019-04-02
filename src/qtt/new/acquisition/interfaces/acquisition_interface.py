from abc import ABC, abstractmethod
from typing import Any, List

from qilib.data_set.data_set import DataSet


class AcquisitionInterface(ABC):

    @abstractmethod
    def __init__(self, instrument_name: str) -> None:
       pass

    @abstractmethod
    def initialize(self, channels: List[str]) -> None:
       pass

    @abstractmethod
    def acquire(self) -> DataSet:
       pass
