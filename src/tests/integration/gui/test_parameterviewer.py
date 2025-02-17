import sys
import pytest
import unittest
from qtt.gui.parameterviewer import ParameterViewer
import pyqtgraph
import qtt.measurements.scans
from qtt.instrument_drivers.virtual_instruments import VirtualIVVI


class TestParameterViewer(unittest.TestCase):

    @pytest.mark.skipif(sys.version_info >= (3, 7), reason="do not run with python3.7 or higher")
    def test_parameterviewer(self):
        qtapp = pyqtgraph.mkQApp()

        ivvi = VirtualIVVI(name=qtt.measurements.scans.instrumentName('dummyivvi'), model=None)
        p = ParameterViewer(instruments=[ivvi])
        p.show()
        p.updatecallback()
        self.assertTrue(p.is_running())
        p.setGeometry(10, 10, 360, 600)

        p.set_parameter_properties(minimum_value=0)

        ivvi.close()
        p.stop()
        p.close()
        qtapp.processEvents()
