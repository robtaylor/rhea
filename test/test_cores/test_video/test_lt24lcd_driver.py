
from __future__ import absolute_import

from random import randint

# @todo: fix, only import what is needed
from myhdl import *

from rhea.system import Global, Clock, Reset
from rhea.cores.video.lcd import LT24Interface
from rhea.cores.video.lcd._lt24lcd_driver import lt24lcd_driver
from rhea.models.video import LT24LCDDisplay
from rhea.cores.misc import glbl_timer_ticks
from rhea.utils.test import tb_clean_vcd, run_testbench


def test_lt24lcd_driver():
    tb_lt24lcd_driver()


def tb_lt24lcd_driver(args=None):
    clock = Clock(0, frequency=50e6)
    reset = Reset(0, active=1, async=False)
    glbl = Global(clock, reset)
    lcd = LT24Interface()
    display = LT24LCDDisplay()

    cmd = Signal(intbv(0)[8:])
    datalen = Signal(intbv(0, min=0, max=lcd.number_of_pixels+1))
    data = Signal(intbv(0)[16:])
    datasent = Signal(bool(0))
    datalast = Signal(bool(0))
    cmd_in_progress = Signal(bool(0))
    
    def _bench_lt24lcd_driver():
        tbdut = lt24lcd_driver(glbl, lcd, cmd, datalen, data,
                               datasent, datalast, cmd_in_progress,
                               maxlen=lcd.number_of_pixels)
        gtck = glbl_timer_ticks(glbl)
        tbmdl = display.process(glbl, lcd)
        
        tbclk = clock.gen()
        
        @instance
        def tbstim():
            yield reset.pulse(111)
            yield clock.posedge

            # --------------------------------------------
            # send a column write command
            cmd.next = 0x2A
            bytes = [0, 0, 0, 239]
            data.next = bytes[0]
            datalen.next = 4 
            
            for ii in range(4):
                yield datasent.posedge
                data.next = bytes[ii+1] if ii < 3 else 0
            cmd.next = 0
            yield cmd_in_progress.negedge
            yield clock.posedge

            # --------------------------------------------
            # send a page address write command
            cmd.next = 0x2B
            bytes = [0, 0, 1, 0x40]
            data.next = bytes[0]
            datalen.next = 4

            for ii in range(4):
                yield datasent.posedge
                data.next = bytes[ii+1] if ii < 3 else 0
            cmd.next = 0
            yield cmd_in_progress.negedge
            yield clock.posedge

            # --------------------------------------------
            # write display memory, full update
            cmd.next = 0x2C
            data.next = randint(0, data.max-1)
            datalen.next = lcd.number_of_pixels

            for ii in range(lcd.number_of_pixels):
                yield datasent.posedge
                data.next = randint(0, data.max-1)
            cmd.next = 0
            yield cmd_in_progress.negedge
            yield clock.posedge

            # --------------------------------------------
            # @todo: verify the display received an image
            yield delay(100)

            raise StopSimulation
            
        return tbdut, tbmdl, tbclk, tbstim, gtck

    run_testbench(_bench_lt24lcd_driver)
    
    
if __name__ == '__main__':
    tb_lt24lcd_driver(None)
