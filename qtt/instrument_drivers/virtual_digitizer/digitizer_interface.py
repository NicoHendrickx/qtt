from abc import ABC, abstractmethod
from typing import Optional, List

import numpy as np

from qcodes import Instrument
from qtt.instrument_drivers.virtual_digitizer import FilterInterface


class DigitizerInterface(ABC):

    def __init__(self, digitizer: Instrument):
        self._all_measurement_channels = dict()
        self._measurement_channels = None
        self._digitizer = digitizer

    @property
    @abstractmethod
    def sample_rate(self):  # float
        pass

    @property
    @abstractmethod
    def period(self):  # float
        pass

    @property
    @abstractmethod
    def number_of_averages(self):  # int
        pass

    @property
    @abstractmethod
    def input_range(self):  # float
        pass

    @abstractmethod
    def measure_segment(self, filters: Optional[FilterInterface]) -> np.array:
        pass

    def get_measurement_channels(self):
        if not self._measurement_channels:
            raise ValueError('No measurement channels specified!')
        return [self._all_measurement_channels[key] for key in self._measurement_channels]

    def set_measurement_channels(self, channels: List[str]) -> None:
        if any(ch not in self._all_measurement_channels.keys() for ch in channels):
            self._measurement_channels = None
            raise ValueError('Invalid channel name specified!')
        self._measurement_channels = channels
