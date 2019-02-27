import matplotlib.pyplot as plt
from itertools import cycle

from qcodes import Station
from qcodes import Measure
from qcodes.instrument_drivers.ZI.ZIUHFLI import ZIUHFLI
import qtt
import qcodes
import time

color_cycler = cycle('bgrcmk')


def plot_1D_dataset(dataset, name_x, names_y, label_x, label_y, fig=100):
    x_data = getattr(dataset, name_x)

    if isinstance(names_y, str):
        y_data_list = [getattr(dataset, names_y)]
    elif isinstance(names_y, list):
        y_data_list = [getattr(dataset, n) for n in names_y]
    else:
        raise ValueError('Invalid name_y_data argument! Must be list[str] or str!')

    plt.figure(num=fig); plt.clf()
    for y_data in y_data_list:
        plt.plot(x_data.flatten(), y_data.flatten(), color=next(color_cycler), label=y_data.name)

    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.legend(loc='upper right')
    plt.show()

#%%

uhfli = ZIUHFLI('QTD1242', 'DEV2338')
station = Station(uhfli, update_snapshot=False)


#%%

def uhfli_no_output():
    uhfli.signal_output1_on('OFF')
    uhfli.signal_output2_on('OFF')

def reset_demodulator(uhfli, demodulator):
    for idx in [0,1]:
        uhfli.daq.setInt('/dev2338/sigouts/%d/enables/%d' % (idx,demodulator-1), 0)

    # more?
    
    
if 0:
    # how to clear a sweeper?
    uhfli.sweeper.clear()
    
uhfli_no_output()
for demodulator in range(1,9):
    reset_demodulator(uhfli, demodulator)
    
channel = 1
demodulator=1
oscillator=1

start_frequency = 60e6; stop_frequency = 150e6
start_frequency = 86e6; stop_frequency = 88e6
start_frequency = 80e6; stop_frequency = 92e6
#start_frequency = 92e6; stop_frequency = 80e6
sweep_steps = 250

uhfli.sweeper_param('Osc %d Frequency' % oscillator)
uhfli.sweeper_xmapping('lin')

uhfli.sweeper_start(start_frequency)
uhfli.sweeper_stop(stop_frequency)
uhfli.sweeper_samplecount(sweep_steps)

uhfli.sweeper_BWmode('fixed')
uhfli.sweeper_BW(250)
uhfli.sweeper_order(4)

uhfli.add_signal_to_sweeper(demodulator, 'phase')
uhfli.add_signal_to_sweeper(demodulator, 'R')
uhfli.add_signal_to_sweeper(demodulator, 'X')
uhfli.add_signal_to_sweeper(demodulator, 'Y')


getattr(uhfli, 'demod%d_trigger' % demodulator )('Continuous')
getattr(uhfli, 'demod%d_signalin' % demodulator )('Sig In %d' % channel)
uhfli.Sweep.build_sweep()

uhfli.daq.setInt('/dev2338/demods/%d/enable' % (demodulator-1,), 1)
uhfli.daq.setDouble('/dev2338/sigouts/%d/amplitudes/%d' % (channel-1,demodulator-1), 0.036)

for idx in [0,1]:
    uhfli.daq.setInt('/dev2338/sigouts/%d/enables/%d' % (idx,demodulator-1), 0)
uhfli.daq.setInt('/dev2338/sigouts/%d/enables/%d' % (channel-1,demodulator-1), 1)

uhfli.daq.setDouble('/dev2338/sigins/%d/range' % (demodulator-1,), 0.01);

not_logarithmic = 0
uhfli.sweeper.set('sweep/xmapping', not_logarithmic)

uhfli.print_sweeper_settings()


#%%

# SWEEPING
for idx in [1,2]:
    getattr(uhfli, 'signal_output%d_on' % (idx,) )( 'OFF')

getattr(uhfli, 'signal_output%d_on' % (channel,))('ON')


sweep_data = Measure(uhfli.Sweep).run()
uhfli_no_output()

plot_1D_dataset(sweep_data, 'Hz_set', uhfli.name+'_R', 'frequency [Hz]', 'Amplitude [V]', fig=101)
plot_1D_dataset(sweep_data, 'Hz_set', uhfli.name+'_phase', 'frequency [Hz]', 'Phase [-Pi, Pi]', fig=102)
plot_1D_dataset(sweep_data, 'Hz_set', [uhfli.name+'_X', uhfli.name+'_Y'], 'frequency [Hz]', 'Amplitude [V]', fig=103)

#addPPTslide(fig=103, title='IQ of uhfli') # TODO: refactor code to generate readable snapshot notes=str(uhfli.snapshot()))

if 0:
    addPPTslide(fig=103, title='IQ of uhfli')
    addPPTslide(fig=101, title='R of uhfli')
    addPPTslide(fig=102, title='Phase of uhfli')

#%%
#
# uhfli.frequency() -> parameter [DONE, it is oscillator1_freq]
# uhfli.power() -> parameter (amplitude): is signal_input1_scaling

# demodulation gain: might be signal_output1_amplitude, but it behaves as a power and not an amplitude
# --> uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)


# measuresegment() -> single_software_trigger_acquisition
# measuresegment() -> single_trigger_acquisition
# measuresegment() -> block_trigger_acquisition
#
# different: input: sampling rate + time (old method: sampling rate + memsize) -> not really a problem
# different: how to specify channels? 
#

import qtt

print('uhfli.signal_output1_ampdef() %s' % uhfli.signal_output1_ampdef())
print('uhfli.signal_input1_scaling() %s' % uhfli.signal_input1_scaling())


#gates=qtt.instrument_drivers.gates.VirtualDAC('dummy2',[], {})
#station.add_component(gates)
#station.gates=gates

uhfli.signal_output1_amplitude(0.5) # ???? why does this modify the "Output Amplitude Amp1 Vpk" of lockin 4?


scanjob=qtt.measurements.scans.scanjob_t()
scanjob.add_sweep(param=uhfli.oscillator1_freq, start=125e6, end=165e6, step=.2e6)
#scanjob.add_minstrument(uhfli.demod1_R)
scanjob.add_minstrument(uhfli.demod1_x)
ds=qtt.measurements.scans.scan1D(station, scanjob)

#
#%%
# OSCILLATOR
uhfli.oscillator1_freq(145e6)
uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)

#uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)
uhfli.daq.setInt('/dev2338/demods/0/enable', 1)
uhfli.daq.setInt('/dev2338/sigouts/0/enables/0', 1)
uhfli.signal_output1_on('ON')

# HORIZONTAL
uhfli.scope_mode.set('Time Domain')
uhfli.scope_samplingrate('27.5 kHz')  # starting value for example
uhfli.scope_duration(1.0) # seconds

# VERTICAL
uhfli.scope_segments('ON')
uhfli.scope_channel1_input.set('Demod 1 R')
uhfli.scope_channels.set(1)  # 1: Chan1 only, 2: Chan2 only, 3: Chan1 + Chan2
uhfli.scope_average_weight(1)  # Number of averages

# TRIGGER OFF
uhfli.scope_trig_enable.set('OFF')

# CHECK SETTINGS
uhfli.Scope.prepare_scope()
if not uhfli.scope_correctly_built:
    raise ValueError('Invalid scope setting! Scope cannot acquire.')

#%%

# TRIGGERING
trigger_on = False

if trigger_on:
    uhfli.scope_trig_enable.set('ON')

    uhfli.scope_trig_signal.set('Trig Input 1')

    uhfli.scope_trig_slope.set('Rise')
    uhfli.scope_trig_level.set(20e-6)  # Volts if the input is volts

    uhfli.scope_trig_hystmode.set('absolute')
    uhfli.scope_trig_hystabsolute.set(3e-6)  # Volts if the input is volts

    uhfli.scope_trig_gating_enable.set('OFF')
    uhfli.scope_trig_gating_source.set('Trigger In 4 Low')

    uhfli.scope_trig_holdoffmode.set('s')  # QCoDeS currently does not support a holdoff in events. 
    uhfli.scope_trig_holdoffseconds.set(2e-5)

    uhfli.scope_trig_reference.set(0)  # Sets the reference for the delay in percent of the trace duration, i.e. 0 is at the trigger
    uhfli.scope_trig_delay.set(1e-4)  # Sets the delay for the acquisition

    # CHECK SETTINGS
    uhfli.Scope.prepare_scope()
    if not uhfli.scope_correctly_built:
        raise ValueError('Invalid scope setting! Scope cannot acquire.')

#%%

# ACQUISITION
_ = uhfli.scope_trig_holdoffseconds.get()
scope_data = Measure(uhfli.Scope).run()

plot_1D_dataset(scope_data, 'Time_set', 'QTD1242_Demodulator 1 R', 'Time [sec.]', 'Amplitude [V]')


#%%

# DISCONNECT DEVICE
uhfli.signal_output1_on('OFF')
uhfli.daq.setInt('/dev2338/demods/0/enable', 0)
uhfli.daq.setInt('/dev2338/sigouts/0/enables/0', 0)
uhfli.close()


#%% Test measuresegment like

uhfli.scope_trig_holdoffseconds.get()
uhfli.scope_mode.set('Time Domain')
uhfli.scope_samplingrate('27.5 kHz')  # starting value for example
uhfli.scope_duration(1.0) # seconds

uhfli.scope_length(21500) # seconds

print('uhfli.scope_duration() %f'  % uhfli.scope_duration())
print('uhfli.scope_samplingrate() %s'  % uhfli.scope_samplingrate())
print('uhfli.scope_length() %f'  % uhfli.scope_length())

uhfli.scope_channel1_input.set('Demod 1 R')
uhfli.scope_channel1_input.set('Signal Input 1')
uhfli.scope_channels.set(1)  # 1: Chan1 only, 2: Chan2 only, 3: Chan1 + Chan2
uhfli.scope_average_weight(1)  # Number of averages

uhfli.Scope.prepare_scope()

xx=uhfli.Scope.get()

data=xx[0]
print('got %d points' % data.size)

#%%
from qtt.measurements.scans import get_uhfli_scope_records

class VirtualDigitizer(qcodes.Instrument):
    
    def __init__(self, name, instrument, **kwargs):
        super().__init__(name, **kwargs)
        self._instrument = instrument
        
    def _prepare_triggering(self):
        uhfli=self._instrument
        uhfli.scope_trig_enable.set('ON')
    
        uhfli.scope_trig_signal.set('Trig Input 1')
    
        uhfli.scope_trig_slope.set('Rise')
        uhfli.scope_trig_level.set(20e-6)  # Volts if the input is volts
    
        uhfli.scope_trig_hystmode.set('absolute')
        uhfli.scope_trig_hystabsolute.set(3e-6)  # Volts if the input is volts
    
        uhfli.scope_trig_gating_enable.set('OFF')
        uhfli.scope_trig_gating_source.set('Trigger In 4 Low')
    
        uhfli.scope_trig_holdoffmode.set('s')  # QCoDeS currently does not support a holdoff in events. 
        uhfli.scope_trig_holdoffseconds.set(2e-5)
    
        uhfli.scope_trig_reference.set(0)  # Sets the reference for the delay in percent of the trace duration, i.e. 0 is at the trigger
        uhfli.scope_trig_delay.set(1e-4)  # Sets the delay for the acquisition
            
    def prepare_demodulation(self):
        raise NotImplementedError


    def measuresegment_demodulation(self):
        uhfli.scope_mode.set('Time Domain')
        uhfli.scope_samplingrate('27.5 kHz')  # starting value for example
        uhfli.scope_duration(1.0) # seconds
        
        uhfli.scope_length(21500) # seconds
        
        print('uhfli.scope_duration() %f'  % uhfli.scope_duration())
        print('uhfli.scope_samplingrate() %s'  % uhfli.scope_samplingrate())
        print('uhfli.scope_length() %f'  % uhfli.scope_length())
        
        uhfli.scope_channel1_input.set('Demod 1 R')
        uhfli.scope_channels.set(1)  # 1: Chan1 only, 2: Chan2 only, 3: Chan1 + Chan2
        uhfli.scope_average_weight(1)  # Number of averages
    

    def prepare_measuresegment(self, verbose=1):
        uhfli.scope_mode.set('Time Domain')
        uhfli.daq.setInt('/dev2338/demods/0/enable', 1)
        uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)
        uhfli.daq.setInt('/dev2338/sigouts/0/enables/0', 1)
        uhfli.signal_output1_on('ON')
        uhfli.scope_trig_enable.set('OFF')
        
        if verbose:
            print('uhfli.scope_duration() %f'  % uhfli.scope_duration())
            print('uhfli.scope_samplingrate() %s'  % uhfli.scope_samplingrate())
            print('uhfli.scope_length() %f'  % uhfli.scope_length())

    def measuresegment_trigger(self, number_of_points, channels, number_of_averages = 1, verbose=1):
        raise NotImplementedError

    def measuresegment(self, number_of_points, channels, number_of_averages = 1, verbose=1):
        uhfli.scope_length(number_of_points)
        
        if verbose:
            sampling_rate = self._instrument.scope_samplingrate_float()
            period = number_of_points / sampling_rate
            print('measuresegment: sampling_rate %f period %f [s]' % (sampling_rate, period))
   
        if 1 in channels:
            uhfli.scope_channel1_input.set('Signal Input 1')
        if 2 in channels:
            uhfli.scope_channel2_input.set('Signal Input 2')
        uhfli.scope_channels.set(sum(channels))  # 1: Chan1 only, 2: Chan2 only, 3: Chan1 + Chan2


        # what is the difference between these two???
        uhfli.scope_segments_count.set(1)
        uhfli.scope_average_weight(number_of_averages)  # Number of averages

        if not uhfli.scope_correctly_built:
            print('prepare_scope!')        
            uhfli.Scope.prepare_scope()
    

        t0=time.time()
        data=uhfli.Scope.get()
        # should be use a modified version of get_uhfli_scope_records???
        #scope_records = get_uhfli_scope_records(uhfli.device, uhfli.daq, uhfli.scope, 1)
        dt=time.time()-t0
        if verbose:
            print('uhfli.Scope.get(): %f [s]' % dt)        
        return data
    
digitizer = VirtualDigitizer(qtt.measurements.scans.instrumentName('vd'), uhfli)
self=digitizer
    

self.prepare_measuresegment()

#%%

number_of_points = 40960
number_of_averages=2

print('start measurement: number_of_points %d' % (number_of_points,))
t0=time.time()
data=digitizer.measuresegment(number_of_points, channels=[1,2], number_of_averages =number_of_averages)
dt=time.time()-t0
print('expected time: %.1f [s], actual %.1f [s]'  % (uhfli.scope_duration()*number_of_averages, dt))
# --> 

#%%
#qtt.measurements.scans.measure_segment_uhfli -> ok for scan1Dfast with SPI rack, but needs to be tested

#missing: low level measure function (with and without trigger) for R/phase/I/Q

#%%


# TRIGGER OFF
uhfli.scope_trig_enable.set('OFF')

# CHECK SETTINGS
uhfli.Scope.prepare_scope()
uhfli.print_sweeper_settings()



xx=uhfli.Sweep.get()

plt.plot(xx[0])