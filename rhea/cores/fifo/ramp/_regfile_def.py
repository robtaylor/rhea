
from ....system import RegisterFile, Register


regfile = RegisterFile()

# -- a basic configuration register --
regcfg = Register('cfg', 8, 'rw', default=0, addr=0x00)
regcfg.comment = "fifo ramp configuration register"
regcfg.add_namedbits('enable', slice(1, 0), "enable fifo ramp")
regfile.add_register(regcfg)

# -- division register 0 --
# 32-bit clock division register
for ii, regname in enumerate(('div3', 'div2', 'div1', 'div0')):
    regdiv = Register(regname, 8, 'rw', default=0, addr=0x04+ii)
    regdiv.comment = "division register most significant byte"
    regdiv.add_namedbits('%sb' % (regname), slice(8, 0), "rate control divisor")
    regfile.add_register(regdiv)

# -- number of ramps completed --
# 32-bit 
for ii, regname in enumerate(('cnt3', 'cnt2', 'cnt1', 'cnt0')):
    regcnt = Register(regname, 8, 'ro', default=0, addr=0x08+ii)
    regcnt.comment = "the number of ramp cycles completed"
    regcnt.add_namedbits('%sb' % (regname,), slice(8, 0), "count")
    regfile.add_register(regcnt)
