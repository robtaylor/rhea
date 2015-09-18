

from __future__ import division

from myhdl import Signal, intbv, always_seq, always


def timer_counter(glbl, counter, increment, overflow):
    clock, reset = glbl.clock, glbl.reset
    count_max = counter.max

    @always_seq(clock.posedge, reset=reset)
    def rtl_count():
        if increment:
            if counter == count_max-1:
                counter.next = 0
            else:
                counter.next = counter + 1

    @always(clock.posedge)
    def rtl_overflow():
        if increment and counter == count_max-2:
            overflow.next = True
        else:
            overflow.next = False

    return rtl_count, rtl_overflow


def glbl_timer_ticks(glbl, include_seconds=True, user_timer=None, tick_div=1):
    """ generate 1 ms and 1 sec ticks

    :param glbl:
    :param include_seconds: generate the one second tick
    :param user_timer: generate a custom timer tick in milleseconds
    :return:
    """
    gens = tuple()

    clock, reset = glbl.clock, glbl.reset

    # define the number of clock ticks per strobe
    ticks_per_ms = int(glbl.clock.frequency//1000)
    ms_per_sec = 1000
    ms_per_user = int(user_timer) if user_timer is not None else 1

    # simulation mode, remove the dead time, the ticks
    # will be considerably shorter than actual
    if tick_div > 1:
        ticks_per_ms = int(ticks_per_ms // tick_div)

    mscnt = Signal(intbv(0, min=0, max=ticks_per_ms))
    seccnt = Signal(intbv(0, min=0, max=ms_per_sec))
    usercnt = Signal(intbv(0, min=0, max=ms_per_user))

    g1 = timer_counter(glbl, counter=mscnt, increment=True,
                       overflow=glbl.tick_ms)

    if include_seconds:
        g2 = timer_counter(glbl, counter=seccnt, 
                           increment=glbl.tick_ms,
                           overflow=glbl.tick_sec)
    else:
        glbl.tick_sec = None
        g2 = []

    if user_timer is not None:
        g3 = timer_counter(glbl, counter=usercnt, 
                           increment=glbl.tick_ms,
                           overflow=glbl.tick_user)
    else:
        glbl.tick_user = None
        g3 = []

    return g1, g2, g3
