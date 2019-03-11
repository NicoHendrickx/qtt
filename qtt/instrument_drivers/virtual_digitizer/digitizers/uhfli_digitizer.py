import numpy as np

from qcodes.instrument_drivers.ZI.ZIUHFLI import ZIUHFLI
from qtt.instrument_drivers.virtual_digitizer import DigitizerInterface


class UhfliDigitizer(DigitizerInterface):

    def __init__(self, uhfli: ZIUHFLI) -> None:
        super().__init__(uhfli)

    @property
    def sample_rate(self) -> float:
        self._digitizer.scope_samplingrate()

    @sample_rate.setter
    def sample_rate(self, value: float):
        self._digitizer.scope_samplingrate.get(value)

    @property
    def period(self) -> float:
        self._digitizer.scope_duration()

    @period.setter
    def period(self, value: float):
        self._digitizer.scope_duration.set(value)

    @property
    def number_of_averages(self) -> int:
        return self._digitizer.scope_average_weight()

    @number_of_averages.setter
    def number_of_averages(self, value: int) -> None:
        self._digitizer.scope_average_weight.set(value)

    @property
    def input_range(self) -> float:
        raise NotImplementedError()

    def measure_segment(self, filters=None) -> np.array:
        self._digitizer.Scope.prepare_scope()
        if not self._digitizer.scope_correctly_built():
            raise ValueError('Invalid scope settings!')

        scope_data = self._digitizer.Scope.get()
        # do filtering here...

        return scope_data
