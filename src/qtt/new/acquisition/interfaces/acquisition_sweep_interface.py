from abc import ABC, abstractmethod
from typing import Any, List

from qtt.new.acquisition.interfaces import AcquisitionInterface


class AcquisitionSweepInterface(AcquisitionInterface):

    @property
    @abstractmethod
    def start_value(self)-> float:
        pass

    @property
    @abstractmethod
    def stop_value(self)-> float:
        pass

    @property
    @abstractmethod
    def steps(self)-> int:
        pass
