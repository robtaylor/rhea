
from __future__ import print_function

from argparse import Namespace

import pytest

from myhdl import (Signal, intbv, instance, now, StopSimulation,
                   traceSignals, Simulation)

from rhea.system import Clock, Reset, Global
from rhea.cores.video.lcd import LT24Interface

# a video display model to check timing
from myhdl import (Signal, intbv, instance, delay,
                   traceSignals, Simulation)

from rhea.system import Clock, Reset, Global

# @todo: add LT24 display model
from rhea.models.video import LT24LCDDisplay
from rhea.utils.test import run_testbench

from mm_lt24lcdsys import mm_lt24lcdsys
from mm_lt24lcdsys import convert


def test_lt24lcd():
    args = Namespace()
    tb_lt24lcd(args=args)


def tb_lt24lcd(args=None):

    clock = Clock(0, frequency=50e6)
    reset = Reset(0, active=0, async=True)
    glbl = Global(clock, reset)

    lcd_on = Signal(bool(0))
    lcd_resetn = Signal(bool(0))
    lcd_csn = Signal(bool(0))
    lcd_rs = Signal(bool(0))
    lcd_wrn = Signal(bool(0))
    lcd_rdn = Signal(bool(0))
    lcd_data = Signal(intbv(0)[16:])

    lcd = LT24Interface()
    resolution = lcd.resolution
    color_depth = lcd.color_depth
    # assign the ports to the interface
    lcd.assign(lcd_on, lcd_resetn, lcd_csn, lcd_rs, lcd_wrn,
               lcd_rdn, lcd_data)
    mvd = LT24LCDDisplay()

    def _bench_lt24lcdsys():
        tbdut = mm_lt24lcdsys(clock, reset, lcd_on, lcd_resetn, 
                              lcd_csn, lcd_rs, lcd_wrn, lcd_rdn, 
                              lcd_data)
        tbvd = mvd.process(glbl, lcd)   # LCD display model 
        tbclk = clock.gen()

        @instance
        def tbstim():
            yield reset.pulse(33)
            yield clock.posedge
            timeout = 33000
            while mvd.update_cnt < 3 and timeout > 0:
                yield delay(1000)
                timeout -= 1

            yield delay(100)
            print("{:<10d}: simulation real time {}".format(now(), mvd.get_time()))
            raise StopSimulation

        return tbdut, tbvd, tbclk, tbstim

    run_testbench(_bench_lt24lcdsys)


def test_conversion():
    convert()


if __name__ == '__main__':
    args = Namespace()
    tb_lt24lcd(args)
    test_conversion()
