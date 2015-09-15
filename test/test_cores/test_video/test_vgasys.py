

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

"""
"""

import argparse
from argparse import Namespace

import pytest

from myhdl import *

import rhea
from rhea.system import Clock
from rhea.system import Reset
from rhea.system import Global
from rhea.cores.video import VGA

# a video display model to check the timings
from rhea.models.video import VGADisplay

from rhea.utils.test import *

# local wrapper to build a VGA system
from mm_vgasys import mm_vgasys
from mm_vgasys import convert


def test_vgasys():
    args = Namespace(resolution=(80, 60), 
                     color_depth=(10, 10, 10),
                     line_rate=4000,
                     refresh_rate=60)
    tb_vgasys(args)


def tb_vgasys(args=None):

    if args is None:
        args = Namespace()
        resolution = (80, 60)
        line_rate = 4000
        refresh_rate = 60
        color_depth = (10, 10, 10)
    else:
        # @todo: retrieve these from ...
        resolution = args.resolution
        refresh_rate = args.refresh_rate
        line_rate = args.line_rate
        color_depth = args.color_depth

    clock = Clock(0, frequency=1e6)
    reset = Reset(0, active=0, async=False)
    vselect = Signal(bool(0))

    vga = VGA(color_depth=color_depth )

    def _test():
        # top-level VGA system 
        tbdut = mm_vgasys(clock, reset, vselect, 
                          vga.hsync, vga.vsync, 
                          vga.red, vga.green, vga.blue,
                          vga.pxlen, vga.active,
                          resolution=resolution,
                          color_depth=color_depth,
                          refresh_rate=refresh_rate,
                          line_rate=line_rate)

        # group global signals
        glbl = Global(clock=clock, reset=reset)

        # a display for each dut        
        mvd = VGADisplay(frequency=clock.frequency,
                         resolution=resolution,
                         refresh_rate=refresh_rate,
                         line_rate=line_rate,
                         color_depth=color_depth)

        # connect VideoDisplay model to the VGA signals
        tbvd = mvd.process(glbl, vga)
        # clock generator
        tbclk = clock.gen()

        @instance
        def tbstim():
            reset.next = reset.active
            yield delay(18)
            reset.next = not reset.active
            
            # Wait till a full screen has been updated
            while mvd.update_cnt < 3:
                 yield delay(1000)

            # @todo: verify video system memory is correct!
            # @todo: (self checking!).  Read one of the frame
            # @todo: png's and verify a couple bars are expected

            raise StopSimulation

        return tbclk, tbvd, tbstim, tbdut

    vcd = tb_clean_vcd('_test')
    traceSignals.timescale = '1ns'
    traceSignals.name = vcd
    Simulation(traceSignals(_test)).run()


@pytest.mark.xfail
def test_vgasys_conversion():
    convert()


if __name__ == '__main__':
    args = Namespace(resolution=(80, 60), 
                     color_depth=(10, 10, 10),
                     line_rate=4000,
                     refresh_rate=60)
    tb_vgasys(args)
    convert()
