import numpy as np
from typing import List

from qilib.data_set import DataSet
from qilib.utils import PythonJsonStructure
from qilib.configuration_helper import InstrumentAdapterFactory
from qcodes.instrument_drivers.Spectrum.M4i import M4i

from qtt.new.acquisition.interfaces import AcquisitionScopeInterface


class M4iScopeReader(AcquisitionScopeInterface):

    settable_channels = {'Channel 1': 0, 'Channel 2': 1, 'Channel 3': 2, 'Channel 4': 3}

    def __init__(self, address):
        self._adapter = InstrumentAdapterFactory.get_instrument_adapter('M4iInstrumentAdapter', address)
        self._scope = self._adapter.instrument

        self.number_of_averages = 100
        self.channels = ['Channel 1']
        self.output_range = 2000
        self.period = 1e-6

    def initialize(self, configuration: PythonJsonStructure) -> None:
        self._adapter.apply(configuration)
        self._check_sample_rate()

    def apply_settings(self):
        self.__user_settings = self._set_memory_size()
        (memory_size, pre_trigger, signal_start, signal_end) = self.__user_settings
        read_channels = self._convert_channels()
        self._adapter.instrument.initialize_channels(read_channels, mV_range=self.output_range,
                                                     memsize=memory_size, termination=1)

    def acquire(self):
        post_trigger = self._adapter.instrument.posttrigger_memory_size()
        user_settings = self.__user_settings
        raw_data = self._adapter.instrument.blockavg_hardware_trigger_acquisition(
                    mV_range=self.output_range, nr_averages=self.number_of_averages,
                    post_trigger=post_trigger)
        #if isinstance(raw_data, tuple):
        #    dataraw = raw_data[0]
        #    data = np.transpose(np.reshape(raw_data, [-1, len(read_ch)]))
        #    data = data[:, signal_start:signal_end]
        data_set = DataSet() # convert data to dataset.
        return data_set

    def _check_sample_rate(self) -> None:
        maximum_sample_rate = self._adapter.instrument.max_sample_rate()
        sample_rate = self._adapter.instrument.sample_rate()

        if sample_rate == 0:
            error_text = 'Sample rate is zero! Please reset the digitizer...'
            raise ValueError(error_text)

        if sample_rate > maximum_sample_rate:
            error_text = 'Sample rate > {0} MHz! Not supported...'.format(maximum_sample_rate // 1e6)
            raise ValueError(error_text)

    def _set_memory_size(self) -> float:
        """
        Returns:
            memsize (int): total memory size selected
            pre_trigger (int): size of pretrigger selected
            signal_start (int): starting position of signal in pixels
            signal_start (int): end position of signal in pixels
        """
        basic_pretrigger_size = 16
        number_points_period = int(self.period * self._adapter.instrument.sample_rate())
        base_segment_size = int(np.ceil((number_points_period) / 16) * 16) + basic_pretrigger_size

        memory_size = base_segment_size
        if memory_size > self._adapter.instrument.memory():
            raise ValueError('Trying to acquire too many points. Reduce sampling rate, period or number segments')

        pre_trigger = 16
        post_trigger = int(np.ceil((base_segment_size - pre_trigger) // 16) * 16)

        signal_start = basic_pretrigger_size
        signal_end = signal_start + number_points_period

        self._adapter.instrument.data_memory_size.set(memory_size)
        self._adapter.instrument.posttrigger_memory_size(post_trigger)
        return memory_size, pre_trigger, signal_start, signal_end

    def _convert_channels(self):
        channel_numbers = []
        for value_channel in self.channels:
            channel_numbers.append(M4iScopeReader.settable_channels[value_channel])
        return channel_numbers
