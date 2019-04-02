import numpy as np
from typing import List, Any

from qcodes import Measure
from qcodes.instrument_drivers.ZI.ZIUHFLI import ZIUHFLI
from qilib.data_set import DataSet, DataArray
from qilib.utils import PythonJsonStructure
from qilib.configuration_helper import InstrumentAdapterFactory

from qtt.new.acquisition.interfaces import AcquisitionScopeInterface


class UhfliScopeReader(AcquisitionScopeInterface):

    def __init__(self, address):
        self._adapter = InstrumentAdapterFactory.get_instrument_adapter(ZIUHFLI.__name__, address)
        self.sampling_rate = self._adapter.instrument.scope_samplingrate_float()
        self.period = self._adapter.instrument.scope_duration()
        self.number_of_averages = 100
        self.channels = [0]

    def initialize(self, config: PythonJsonStructure, channels: List[str]) -> None:
        self._adapter.apply(config)
        # set channels (how to deal with 4 digitizer ch. and 2 uhfli ch. ?)
        self._adapter.instrument.Scope.prepare_scope()
        if not self._adapter.instrument.scope_correctly_built:
            raise ValueError('Invalid scope setting! Scope cannot acquire.')

    def acquire(self, storage_writer: Any = None, storage_reader: Any = None) -> DataSet:
        _ = self._adapter.instrument.scope_trig_holdoffseconds.get()
        qcodes_dataset = Measure(self._adapter.instrument.Scope)
        # convert to qilib DataSet...
        return UhfliScopeReader.convert_data_set(qcodes_dataset, storage_reader, storage_reader)

    @staticmethod
    def convert_data_set(qcodes_dataset, storage_writer: Any = None, storage_reader: Any = None):
        qcodes_dataset
        return DataSet(storage_writer, storage_reader)
