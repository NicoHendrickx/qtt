from qcodes.instrument_drivers.ZI.ZIUHFLI import ZIUHFLI


class UHFLIWrapper(ZIUHFLI):
    
    def __init__(self, name: str, device_ID: str, **kwargs):
        super().__init__(name, device_ID, **kwargs)

    def signal_outputs_off(self):
        self.signal_output1_on('OFF')
        self.uhfli.signal_output2_on('OFF')
                
    def enable_output(self, channel):
        if channel not in [1, 2]:
            raise ValueError('Invalid channel {}'.format(channel))
        signal_output = getattr(self, 'signal_output_{}_on'.format(channel))
        signal_output('ON')

    def scope_samplingrate(self, sample_rate):
        pass
        