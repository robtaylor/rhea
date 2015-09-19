
from __future__ import division

"""
This module contains a video driver for the terasic LT24
LCD display ...
"""
from myhdl import Signal, intbv, enum, always_seq, concat

from ._lt24intf import LT24Interface
from ._lt24lcd_init_sequence import init_sequence, build_init_rom
from ._lt24lcd_driver import lt24lcd_driver

def lt24lcd(glbl, vmem, lcd):
    """
    RGB 5-6-5 (8080-system 16bit parallel bus)
    """
    assert isinstance(lcd, LT24Interface)
    resolution, refresh_rate = (240, 320), 60
    number_of_pixels = resolution[0] * resolution[1]

    # local references to signals in interfaces
    clock, reset = glbl.clock, glbl.reset

    # make sure the user timer is configured
    assert glbl.tick_user is not None

    # write out a new VMEM to the LCD display, a write cycle
    # consists of putting the video data on the bus and latching
    # with the `wrx` signal.  Init (write once) the column and
    # page addresses (cmd = 2A, 2B) then write mem (2C)
    states = enum(
        'init_wait_reset',      # wait for the controller to reset the LCD
        'init_start',           # start the display init sequence
        'init_start_cmd',       # send a command, port of the display seq
        'init_next',            # determine if another command

        'write_cmd_start',       # command subroutine
        'write_cmd',             # command subroutine

        'display_update_start',  # update the display
        'display_update',
        'display_update_next',
        'display_update_end'
    )

    state = Signal(states.init_wait_reset)
    cmd = Signal(intbv(0)[8:])
    return_state = Signal(states.init_wait_reset)

    num_hor_pxl, num_ver_pxl = resolution
    print("resolution {}x{} = {} number of pixes".format(
          num_hor_pxl, num_ver_pxl, number_of_pixels))
    hcnt = intbv(0, min=0, max=num_hor_pxl)
    vcnt = intbv(0, min=0, max=num_ver_pxl)

    # signals to start a new command transaction to the LCD
    datalen = Signal(intbv(0, min=0, max=number_of_pixels+1))
    data = Signal(intbv(0)[16:])
    datasent = Signal(bool(0))
    datalast = Signal(bool(0))
    cmd_in_progress = Signal(bool(0))

    # --------------------------------------------------------
    # LCD driver
    gdrv = lt24lcd_driver(glbl, lcd, cmd, datalen, data,
                          datasent, datalast, cmd_in_progress)

    # --------------------------------------------------------
    # build the display init sequency ROM
    rom, romlen, maxpause = build_init_rom(init_sequence)
    offset = Signal(intbv(0, min=0, max=romlen+1))
    pause = Signal(intbv(0, min=0, max=maxpause+1))

    # --------------------------------------------------------
    # state-machine

    @always_seq(clock.posedge, reset=reset)
    def rtl_state_machine():

        if state == states.init_wait_reset:
            if lcd.reset_complete:
                state.next = states.init_start

        elif state == states.init_start:
            v = rom[offset]
            # @todo: change the table to only contain the number of
            # @todo: bytes to be transferred
            datalen.next = v - 3
            p = rom[offset+1]
            pause.next = p
            offset.next = offset + 2
            state.next = states.init_start_cmd

        elif state == states.init_start_cmd:
            v = rom[offset]
            cmd.next = v
            if datalen > 0:
                v = rom[offset+1]
                data.next = v
                offset.next = offset + 2
            else:
                offset.next = offset + 1
            state.next = states.write_cmd_start
            return_state.next = states.init_next

        elif state == states.init_next:
            if pause == 0:
                if offset == romlen:
                    state.next = states.display_update_start
                else:
                    state.next = states.init_start
            elif glbl.tick_ms:
                    pause.next = pause - 1

        elif state == states.write_cmd_start:
            state.next = states.write_cmd

        elif state == states.write_cmd:
            if cmd_in_progress:
                if datasent and not datalast:
                    v = rom[offset]
                    data.next = v
                    offset.next = offset+1
            else:
                cmd.next = 0
                state.next = return_state

        elif state == states.display_update_start:
            if glbl.tick_user:
                cmd.next = 0x2C
                state.next = states.display_update
                datalen.next = number_of_pixels

        elif state == states.display_update:
            if vcnt == num_ver_pxl-1:
                hcnt[:] = 0
                vcnt[:] = 0
            elif hcnt == num_hor_pxl-1:
                hcnt[:] = 0
                vcnt[:] = vcnt + 1
            else:
                hcnt[:] = hcnt + 1

            # this will be the pixel for the next write cycle
            vmem.hpxl.next = hcnt
            vmem.vpxl.next = vcnt

            # this is the pixel for the current write cycle
            if hcnt == 0 and vcnt == 0:
                state.next = states.display_update_end
            else:
                data.next = concat(vmem.red, vmem.green, vmem.blue)
                state.next = states.display_update_next

        elif state == states.display_update_next:
            if cmd_in_progress:
                if datasent and not datalast:
                    state.next = states.display_update
            else:
                cmd.next = 0
                state.next = states.display_update_end

        elif state == states.display_update_end:
            # @todo: wait for next update
            if not cmd_in_progress:
                state.next = states.display_update

    return gdrv, rtl_state_machine


