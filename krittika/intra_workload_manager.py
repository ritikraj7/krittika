import math
import os.path
import numpy as np

from krittika.chiplet_system import ChipletSys
from scalesim.compute.operand_matrix import operand_matrix

class IntraWorkloadManager:
    def __init__(self):
        self.chiplet_sys =  ChipletSys()
        self.op_mat_obj = operand_matrix()

    #
    def set_params(self,
                   chiplet_sys = ChipletSys(),
                   op_mat_obj = operand_matrix()):
        self.chiplet_sys = chiplet_sys
        self.op_mat_obj = op_mat_obj

    #
    def uniform_distribution(self):
        ifmap_matrix, filter_matrix, ofmap_matrix = self.op_mat_obj.get_all_operand_matrix()
        input_rows_per_part = math.ceil(ifmap_matrix.shape[0] / self.chiplet_sys.num_input_part)
        filter_cols_per_part = math.ceil(filter_matrix.shape[1] / self.chiplet_sys.num_filter_part)

        for inp_part in range(self.chiplet_sys.num_input_part):
            ifmap_row_start = inp_part * input_rows_per_part
            ifmap_row_end = min(ifmap_row_start + input_rows_per_part, ifmap_matrix.shape[0])

            ifmap_part = ifmap_matrix[ifmap_row_start:ifmap_row_end,:]

            for filt_part in range(self.chiplet_sys.num_filter_part):

                filt_col_start = filt_part * filter_cols_per_part
                filt_col_end = min(filt_col_start + filter_cols_per_part, filter_matrix.shape[1])

                filter_part = filter_matrix[:, filt_col_start: filt_col_end]
                ofmap_part = ofmap_matrix[ifmap_row_start: ifmap_row_end, filt_col_start:filt_col_end]

                #Assign the work to Chiplet
                self.chiplet_sys.chiplet_matrix[inp_part][filt_part].compute_node.set_operands(ifmap_opmat=ifmap_part,
                                                                                                filter_opmat=filter_part,
                                                                                                ofmap_opmat=ofmap_part)


    #
    #def non_uniform_distribution():

    #
    #def uniform_simd_distribution():

    #
    #def non_uniform_simd_distribution():
                

 
                
