import math
import numpy as np

from krittika.chiplet_node import ChipletNode

class ChipletSys:
    def __init__(self):
        self.chiplet_matrix = []
        self.num_input_part = 1
        self.num_filter_part = 1

    #
    def set_params(self,
                   num_input_part = 1,
                   num_filter_part = 1):

        self.num_input_part = num_input_part
        self.num_filter_part = num_filter_part

        for i in range(num_input_part):
            chiplet_array = []
            for j in range(num_filter_part):
                #Create a chiplet node
                this_chiplet_node = ChipletNode()
                #Assign the x,y coordinates of the chiplet in the system
                this_chiplet_node.x = j
                this_chiplet_node.y = i
                chiplet_array.append(this_chiplet_node)
            self.chiplet_matrix.append(chiplet_array)
                

    #
    def return_chiplet_sys(self):
        return self.chiplet_matrix
