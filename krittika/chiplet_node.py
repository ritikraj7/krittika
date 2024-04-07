import math
import os.path 
import numpy as np

from scalesim.compute.operand_matrix import operand_matrix
from scalesim.memory.double_buffered_scratchpad_mem import double_buffered_scratchpad

from krittika.compute.compute_node import ComputeNode

class ChipletNode:
    def __init__(self):
        #Member Objects
        self.compute_node = ComputeNode()
        self.scratch_pad = double_buffered_scratchpad()
        self.x = 0
        self.y = 0

    #Flags

    #
    def set_params(self,
                   x = 0,
                   y = 0):
        self.x = x
        self.y = y

    #
    def  get_compute_node(self):
        return self.compute_node

    #
    def get_scratch_pad(self):
        return self.scratch_pad
        
