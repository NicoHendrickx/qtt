import numpy as np
from typing import List

from qilib.utils import PythonJsonStructure
from qilib.configuration_helper import InstrumentAdapterFactory
from qcodes.instrument_drivers.Spectrum.M4i import M4i

from qtt.new.acquisition.interfaces import AcquisitionScopeInterface


class M4iScopeReader(AcquisitionScopeInterface):

    settable_channels = {'Channel 1': 0, 'Channel 2': 1, 'Channel 3': 2, 'Channel 4': 3}

    def __init__(self, address):
        self._adapter = InstrumentAdapterFactory.get_instrument_adapter(M4i.__name__, address)
        self._scope = self._adapter.instrument
        self.sampling_rate = self._adapter.instrument.sampling_rate()
        self.number_of_averages = 100
        self.channels = ['Channel 1']
        self.period = 1e-6

    def acquire(self):
        self._scope.sample_rate(self.sampling_rate)
        self._check_sample_rate()

    def initialize(self, config: PythonJsonStructure) -> None:
        self._adapter.apply(config)
        self._check_sample_rate()

    def _check_sample_rate(self) -> None:
        maximum_sample_rate = self._scope.max_sample_rate()
        sample_rate = self._scope.sampling_rate()

        if sample_rate == 0:
            error_text = 'Sample rate is zero! Please reset the digitizer...'
            raise ValueError(error_text)

        if sample_rate > maximum_sample_rate:
            error_text = 'Sample rate > {0} MHz! Not supported...'.format(maximum_sample_rate // 1e6)
            raise ValueError(error_text)

    def _set_memory_size(self) -> float:
        measurement_points = int(self.period * self.sampling_rate)
        memory_size = int(np.ceil(measurement_points / 16) * 16)
        post_trigger_size = int(np.ceil((memory_size - 2 * 16) // 16) * 16)

        if memory_size > self._scope.memory():
            error_text = 'Trying to acquire too many points! Reduce sampling rate or period...'
            raise ValueError(error_text)

        self._scope.data_memory_size.set(memory_size)
        self._scope.posttrigger_memory_size(post_trigger_size)
        return memory_size
