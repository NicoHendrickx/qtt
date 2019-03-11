import numpy as np

from qtt.instrument_drivers.virtual_digitizer import DigitizerInterface


class M4iDigitizer(DigitizerInterface):

    def __init__(self, m4i):
        super().__init__(self, m4i)
        self._all_measurement_channels = {
            0: 'channel1',
            1: 'channel2',
            2: 'channel3',
            3: 'channel4'
        }
        self.number_of_averages = 1
        self.input_range = 2000
        self.period = 1e-3

    @property
    def sample_rate(self) -> float:
        sample_rate = self._digitizer.sampling_rate()
        if sample_rate == 0:
            raise ValueError('Sample rate is zero! Please reset the digitizer...')
        return sample_rate

    @sample_rate.setter
    def sample_rate(self, value: float) -> None:
        _ = self.sample_rate
        maximum_sample_rate = self._digitizer.max_sample_rate()
        if value > maximum_sample_rate:
            error_text = 'Sample rate > {0} MHz! Not supported...'.format(maximum_sample_rate // 1e6)
            raise ValueError(error_text)

    def measure_segment(self, filters=None) -> np.array:
        memory_size = self._set_memory_size()
        post_trigger = self._digitizer.posttrigger_memory_size()
        measurement_channels = self.get_measurement_channels()

        self._digitizer.initialize_channels(measurement_channels, mV_range=self.input_range,
                                            memsize=memory_size)
        raw_data = self._digitizer.blockavg_hardware_trigger_acquisition(mV_range=self.input_range,
                                                                         nr_averages=self.number_of_averages,
                                                                         post_trigger=post_trigger)
        return raw_data

    def _set_memory_size(self):
        measurement_points = int(self.period * self.sample_rate)
        memory_size = int(np.ceil(measurement_points / 16) * 16)
        post_trigger_size = int(np.ceil((memory_size - 2 * 16) // 16) * 16)

        if memory_size > self._digitizer.memory():
            error_text = 'Trying to acquire too many points! Reduce sampling rate or period...'
            raise ValueError(error_text)

        self._digitizer.data_memory_size.set(memory_size)
        self._digitizer.posttrigger_memory_size(post_trigger_size)
        return memory_size
