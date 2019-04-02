from qtt.new.acquisition import M4iScopeReader
from qtt.new.configuration_helper import M4iInstrumentAdapter, load_adapter, save_adapter


scope = M4iScopeReader(address = 'spcm0')

configuration = load_adapter(file_path='d:/Users/lucblom/data/m4i_adapter.dat')
scope.initialize(configuration)

scope.number_of_averages = 1
scope.apply_settings()

scope.acquire()

