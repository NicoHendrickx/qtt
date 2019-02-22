import matplotlib.pyplot as plt
from itertools import cycle

from qcodes import Station
from qcodes import Measure
from qcodes.instrument_drivers.ZI.ZIUHFLI import ZIUHFLI

color_cycler = cycle('bgrcmk')


def plot_1D_dataset(dataset, name_x, names_y, label_x, label_y, fig=100):
    x_data = getattr(dataset, name_x)

    if isinstance(names_y, str):
        y_data_list = [getattr(dataset, names_y)]
    elif isinstance(names_y, list):
        y_data_list = [getattr(dataset, n) for n in names_y]
    else:
        raise ValueError('Invalid name_y_data argument! Must be list[str] or str!')

    plt.figure(num=fig)
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

start_frequency = 100e6
stop_frequency = 200e6
sweep_steps = 250

uhfli.sweeper_param('Osc 1 Frequency')
uhfli.sweeper_xmapping('lin')

uhfli.sweeper_start(start_frequency)
uhfli.sweeper_stop(stop_frequency)
uhfli.sweeper_samplecount(sweep_steps)

uhfli.sweeper_BWmode('fixed')
uhfli.sweeper_BW(250)
uhfli.sweeper_order(4)

uhfli.add_signal_to_sweeper(1, 'phase')
uhfli.add_signal_to_sweeper(1, 'R')
uhfli.add_signal_to_sweeper(1, 'X')
uhfli.add_signal_to_sweeper(1, 'Y')

uhfli.demod1_trigger('Continuous')
uhfli.demod1_signalin('Sig In 1')
uhfli.Sweep.build_sweep()

uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)
uhfli.daq.setInt('/dev2338/demods/0/enable', 1)
uhfli.daq.setInt('/dev2338/sigouts/0/enables/0', 1)
uhfli.signal_output1_on('ON')

not_logarithmic = 0
uhfli.sweeper.set('sweep/xmapping', not_logarithmic)

uhfli.print_sweeper_settings()

#%%

# SWEEPING
sweep_data = Measure(uhfli.Sweep).run()

plot_1D_dataset(sweep_data, 'Hz_set', 'QTD1242_R', 'frequency [Hz]', 'Amplitude [V]')
plot_1D_dataset(sweep_data, 'Hz_set', 'QTD1242_phase', 'frequency [Hz]', 'Phase [-Pi, Pi]')
plot_1D_dataset(sweep_data, 'Hz_set', ['QTD1242_X', 'QTD1242_Y'], 'frequency [Hz]', 'Amplitude [V]')

# RESONANCE FREQ: 154.8 MHz

#%%

# OSCILLATOR
uhfli.oscillator1_freq(145e6)
uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)

uhfli.daq.setDouble('/dev2338/sigouts/0/amplitudes/0', 0.1)
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

