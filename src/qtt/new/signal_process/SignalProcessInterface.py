from abc import ABC, abstractmethod
from qilib.data_set import DataSet


class SignalProcessInterface(ABC):

    def run_process(self, data_set: DataSet):
        pass