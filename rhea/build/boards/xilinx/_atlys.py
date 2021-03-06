

from ..._fpga import _fpga
from ...toolflow import ISE 

class Atlys(_fpga):
    vendor = 'xilinx'
    family = 'spartan6'
    device = 'XC6SLX45'
    package = 'CSG324'
    speed = -3
    _name = 'atlys'
    
    default_clocks = {
        'clock': dict(frequency=50e6, pins=('L15',)),
    }
    
    default_ports = {
        'led': dict(pins=('U18', 'M14', 'N14', 'L14', 
                          'M13', 'D4', 'P16', 'N12',)),
        'btn': dict(pins=('T15', 'N4', 'P4', 'P3', 'F6', 'F5',)),
    }

    def get_flow(self, top=None):
        return ISE(brd=self, top=top)