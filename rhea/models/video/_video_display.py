
import os
from array import array
from copy import deepcopy
from datetime import datetime
from myhdl import intbv, now
from PIL import Image


class VideoDisplay(object):
    def __init__(self, 
                 resolution=(640,480,), 
                 refresh_rate = 60,
                 line_rate = 31250,
                 color_depth=(10, 10, 10,)
             ):
        """
        """
        self.resolution = res = resolution
        self.num_hpxl, self.num_vpxl = self.resolution
        self.name = 'unknown'
        self.update_cnt = 0
        self._col, self._row = 0, 0

        if max(color_depth) <= 8:
            arraytype = 'B'
        elif max(color_depth) <= 16:
            arraytype = 'H'
        elif max(color_depth) <= 32:
            arraytype = 'L'

        # create a container to emulate the video display
        # in the process of updating image
        #self.uvmem = [array(arraytype, [0 for _ in range(res[0])])
        #              for _ in range(res[1])]
        self._uvmem = [[None for _ in range(res[0])]
                        for _ in range(res[1])]
        # static image
        #self.vvmem = [array(arraytype, [0 for _ in range(res[0])])
        #              for _ in range(res[1])]
        self._vvmem = [[None for _ in range(res[0])]
                        for _ in range(res[1])]
                        
        # emulating video displays takes considerable simulation time, track
        # the simulation real time. 
        self.time_start = datetime.now()
        self.time_last = datetime.now()

    def get_time(self):
        """ get the amount of real time from creation to now """
        return datetime.now() - self.time_start
        
    def reset_cursor(self):
        self._col, self._row = 0, 0

    def update_next_pixel(self, val):
        col, row = self._col, self._row
        assert col < self.num_hpxl
        assert row < self.num_vpxl

        if isinstance(val, int):
            nbits = sum(self.color_depth)
            val = intbv(val)[nbits:]
            cd = self.color_depth
            rgb = (val[nbits:nbits-cd[0]],
                   val[nbits-cd[0]:cd[2]],
                   val[cd[2]:0],)
        elif isinstance(val, tuple):
            rgb = val
        else:
            raise ValueError

        self._uvmem[row][col] = rgb

        col += 1
        if col == self.num_hpxl:
            col = 0
            row += 1
        if row == self.num_vpxl:
            row = 0

        if col == 0 and row == 0:
            # @todo: remove print add option to create png or not
            self.update_cnt += 1
            td = datetime.now() - self.time_last
            print("{:<10d}: full display update {} ({})".format(now(), self.update_cnt, td))
            self._vvmem = deepcopy(self._uvmem)
            self.create_save_image()
            self.time_last = datetime.now()
            
        self._col, self._row = col, row
        return 

    def set_pixel(self, col, row, rgb, last=False):
        """
        :param col:
        :param row:
        :return:
        """
        assert col < self.num_hpxl
        assert row < self.num_vpxl
        self._uvmem[row][col] = rgb
        if last:
            self._vvmem = deepcopy(self._uvmem)


    def _adjust_color_depth(self, rgb):
        argb = rgb
        if self.color_depth != (8, 8, 8):
            argb = [(vv/cc)*256 for vv,cc in zip(rgb, self.color_depth)]
            argb = list(map(int, argb))
        return argb

    def create_save_image(self):
        """ 
        :param framen: frame number
        :param frame: 2D frame container (list, array)
        """
        framen = self.update_cnt   # latest display update
        frame = self._vvmem        # display memory
        im = Image.new('RGB', self.resolution)
        for rr, row in enumerate(frame):
            for cc, rgb in enumerate(row):
                rgb = self._adjust_color_depth(rgb)
                im.putpixel((cc, rr), tuple(rgb))
                
        if not os.path.isdir("output"):
            os.makedirs("output")
        imgpath = os.path.join("output/", "{}_frame_{}.png".format(
            self.name, framen))
        im.save(imgpath)

    def process(self, glbl, vga):
        """ emulate the behavior of the display """
        raise NotImplemented

