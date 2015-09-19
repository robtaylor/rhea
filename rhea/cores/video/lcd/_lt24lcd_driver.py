

from myhdl import Signal, intbv, enum, always_seq, concat


def lt24lcd_driver(glbl, lcd, cmd, datalen, data, 
                   datasent, datalast, cmd_in_progress, maxlen=76800):
    """
    :param glbl:
    :param lcd:
    :param cmd: 
    :param datalen: number of data xfer to do
    :param data: data to be sent
    :param data_sent: one cycle strobe indicating the data xfered
    :param cmd_in_progress:
    :return:
    
    Typical confgiruration write
       clock:             /--\__/--\__/--\__/--\__/--\__/--\__/--\__
       cmd:               0x00    | 0x2B 
       cmd_in_progress:   ____________/----------------
                                            ^ cmd latched
                                                  ^ first data byte for command
       datasent           ________________________/----\_____
       
    The transaction is started by setting the `cmd` signal to nonzero,
    the command byte is transferred and then the frist data, when then
    first data is transferred the `datasent` is strobe, this indicates 
    to the source (producer) to update `data` to the next value. 
    The `cmd` must go to zero before the next transfer can occur. 
    
    Future enhancements:
    @todo: add read commands 
    """
    
    # local references
    clock, reset = glbl.clock, glbl.reset 

    states = enum(
        'reset_start',
        'reset',
        'reset_wait',
        'wait', 
        'write_command_start', 
        'write_command_data', 
        'write_command_xsetup', 
        'write_command_xlatch',
        'end'
    )

    state = Signal(states.reset_start)
    xfercnt = Signal(intbv(0, min=0, max=maxlen+1))
    lcd.reset_complete = Signal(bool(0))

    @always_seq(clock.posedge, reset=reset)
    def rtl_state_machine():

        if state == states.reset_start:
            lcd.resetn.next = True
            lcd.csn.next = True
            lcd.wrn.next = True
            lcd.rdn.next = True
            lcd.dcn.next = True        
            lcd.on.next = True
            xfercnt.next = 2  # used as ms counter
            lcd.reset_complete.next = False
            state.next = states.reset

        elif state == states.reset:
            if glbl.tick_ms:
                if xfercnt == 0:
                    lcd.resetn.next = False
                    xfercnt.next = 10  # used as ms counter
                    state.next = states.reset_wait
                else:
                    xfercnt.next = xfercnt - 1

        elif state == states.reset_wait:
            if glbl.tick_ms:
                if xfercnt == 0:
                    lcd.resetn.next = True
                    state.next = states.wait
                    lcd.reset_complete.next = True
                else:
                    xfercnt.next = xfercnt - 1

        # wait for a new command
        elif state == states.wait:
            datasent.next = False
            if cmd != 0x00:
                lcd.csn.next = False
                lcd.wrn.next = False
                lcd.dcn.next = False
                lcd.data.next = cmd 
                state.next = states.write_command_start
                cmd_in_progress.next = True
            else:
                cmd_in_progress.next = False
                lcd.csn.next = True
                lcd.wrn.next = True
                lcd.rdn.next = True
                lcd.dcn.next = True                
                
        # start a write command
        elif state == states.write_command_start:
            lcd.wrn.next = True
            state.next = states.write_command_data

        # setup the data portion of the command
        elif state == states.write_command_data:
            lcd.dcn.next = True
            xfercnt.next = 0
            if datalen == 0:
                lcd.wrn.next = True
                state.next = states.end
            else:
                lcd.wrn.next = False
                state.next = states.write_command_xsetup

        # transfer the data setup
        elif state == states.write_command_xsetup:
            lcd.wrn.next = False
            lcd.data.next = data 
            datasent.next = True
            if xfercnt == datalen-1:
                datalast.next = True
            xfercnt.next = xfercnt + 1
            state.next = states.write_command_xlatch

        # transfer the data latch
        elif state == states.write_command_xlatch:
            lcd.wrn.next = True
            datasent.next = False
            datalast.next = False
            if xfercnt == datalen:
                state.next = states.end
            else:
                state.next = states.write_command_xsetup

        # end of the transaction
        elif state == states.end:
            lcd.csn.next = True
            cmd_in_progress.next = False
            if cmd == 0:
                state.next = states.wait
                
        else:
            assert False, "Invalid state %s" % (state,)
            
    return rtl_state_machine
