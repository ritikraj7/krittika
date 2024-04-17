import numpy as np
import math
from collections import deque


from scalesim.memory.double_buffered_scratchpad_mem import double_buffered_scratchpad
from scalesim.compute.operand_matrix import operand_matrix
from krittika.config.krittika_config import KrittikaConfig

from krittika.chiplet_system import ChipletSys

#Inputs
    #List of chiplets that are going to be used
    #chiplet sys

#Outputs
    #Dependency Matrix
    #Latency Matrix


class Scheduler:
    '''
        The objective of this class
        1. Read the chiplets that are going to be used
        2. Partition the matrices
        3. Generate the dependency matrices
        4. Calculate the latency
    '''

    def __init__(self):

        #Member Objects
        self.chiplet_sys = ChipletSys()
        self.op_mat_obj = operand_matrix()
        self.config_obj = KrittikaConfig() 
        self.dependency_matrix = []
        self.status_matrix = [] #(x,y,z) x-inp_dependency, y-acc_dependency, z-run-status
        self.ready_to_run = deque()
        self.latency_matrix = None
        #set these two in set_params
        #set this based on DRAM to SRAM latency
        self.init_latency = 5
        #hyper parameter
        self.cycles_per_sec = (1/1.8)
        self.bandwidth = math.pow(2,33)

        #Flags
        self.verbose = True

    #
    def set_params(self,
                   chiplet_sys = ChipletSys(),
                   op_mat_obj = operand_matrix(),
                   config_obj = KrittikaConfig(),
                   verbosity=True):
        self.chiplet_sys = chiplet_sys
        self.op_mat_obj = op_mat_obj
        self.config_obj = config_obj
        self.verbose = verbosity

    #
    def count_non_negative(self, list):
        negative_values = sum(sublist.count(-1) for sublist in list)
        total_values = sum(len(sublist) for sublist in list)
        non_negative = total_values - negative_values
        return non_negative

    #
    def workload_distribution(self, uniform = 1):
        ifmap_matrix, filter_matrix, ofmap_matrix = self.op_mat_obj.get_all_operand_matrix()

        if(uniform):
            input_rows_per_part = math.ceil(ifmap_matrix.shape[0] / self.chiplet_sys.num_input_part)
            filter_cols_per_part = math.ceil(filter_matrix.shape[1] / self.chiplet_sys.num_filter_part)

            self.latency_matrix = np.zeros((self.chiplet_sys.num_input_part, self.chiplet_sys.num_filter_part))

            for inp_part in range(self.chiplet_sys.num_input_part):
                ifmap_row_start = inp_part * input_rows_per_part
                ifmap_row_end = min(ifmap_row_start + input_rows_per_part, ifmap_matrix.shape[0])

                ifmap_part = ifmap_matrix[ifmap_row_start:ifmap_row_end,:]
                this_row_dependency = []
                this_row_status = []
                this_row_latency = []

                for filt_part in range(self.chiplet_sys.num_filter_part):
                    filt_col_start = filt_part * filter_cols_per_part
                    filt_col_end = min(filt_col_start + filter_cols_per_part, filter_matrix.shape[1])

                    filter_part = filter_matrix[:, filt_col_start: filt_col_end]
                    ofmap_part = ofmap_matrix[ifmap_row_start: ifmap_row_end, filt_col_start:filt_col_end]

                    #Assign the work to Chiplet
                    self.chiplet_sys.chiplet_matrix[inp_part][filt_part].compute_node.set_operands(ifmap_opmat=ifmap_part,
                                                                                                    filter_opmat=filter_part,
                                                                                                    ofmap_opmat=ofmap_part)
                    
                    #the sizes of the ifmap and filt for this part of the communication
                    ifmap_part_size = np.sum(ifmap_part != -1)
                    # filt_part_size = np.sum(filt_part != -1)
                    # print("ifmap:")
                    # print(ifmap_part_size)
                    # print("filt:")
                    # print(filt_part_size)


                    # if((inp_part == 0)):
                    #     # acc_dep_coord = (-1, -1)
                    #     if(filt_part == 0):
                    #         inp_dep_coord = (-1, -1)
                    #         this_row_status.append([1,0])
                    #     else:
                    #         inp_dep_coord = (inp_part, filt_part - 1)
                    #         this_row_status.append([0,0])
                    # elif((filt_part == 0)):
                    #     inp_dep_coord = (-1, -1)
                    #     this_row_status.append([1,0])
                    # else:
                    #     inp_dep_coord = (inp_part, filt_part - 1)
                    #     this_row_status.append([0,0])

                    if(filt_part == 0):
                        inp_dep_coord = (-1, -1)
                        this_row_status.append([1,0])
                        self.latency_matrix[inp_part][filt_part] = self.init_latency
                    else:
                        inp_dep_coord = (inp_part, filt_part - 1)
                        this_row_status.append([0,0])
                        self.latency_matrix[inp_part][filt_part] = self.latency_matrix[inp_part][filt_part-1] + np.ceil((ifmap_part_size*8/self.bandwidth)*self.cycles_per_sec)


                    if(inp_dep_coord == (-1,-1)):
                        self.ready_to_run.append((inp_part, filt_part))

                    this_row_dependency.append((inp_dep_coord))
                self.dependency_matrix.append(this_row_dependency)
                self.status_matrix.append(this_row_status)

        print("Dependency matrix:")
        print(self.dependency_matrix)
        print("Status Matrix")
        print(self.status_matrix)
        print("Latency Matrix")
        print(self.latency_matrix)

    #
    def set_memory_dependency(self):
        for row in range(self.chiplet_sys.num_input_part):
            for col in range(self.chiplet_sys.num_filter_part):
                dep_coordinate = self.dependency_matrix[row][col]
                if(dep_coordinate[0] == -1 and dep_coordinate[1] == -1):
                    pass
                else:
                    self.chiplet_sys.chiplet_matrix[row][col].scratch_pad.set_ifmap_backing_buffer( self.chiplet_sys.chiplet_matrix[dep_coordinate[0]][dep_coordinate[1]].scratch_pad.ifmap_buf)
            
        

    def run_chiplet(self):
        bandwidth_mode = self.config_obj.get_bandwidth_use_mode()
        per_core_ifmap_buf_size, per_core_fitler_buf_size, per_core_ofmap_buf_size \
            = ([i * 1024 for i in self.config_obj.get_per_unit_sram_sizes_kb()])

        per_core_ifmap_bw, per_core_filter_bw, per_core_ofmap_bw\
            = self.config_obj.get_interface_bandwidths()
       
        chiplet_node = self.chiplet_sys.chiplet_matrix[self.ready_to_run[0][0]][self.ready_to_run[0][1]]
        print("Chiplet being Run: ", self.ready_to_run[0][0], self.ready_to_run[0][1])
        nop_latency = self.latency_matrix[self.ready_to_run[0][0]][self.ready_to_run[0][1]]

        chiplet_node.scratch_pad.set_params(verbose=self.verbose,
                                 estimate_bandwidth_mode=bandwidth_mode,
                                 ifmap_buf_size_bytes=per_core_ifmap_buf_size,
                                 filter_buf_size_bytes=per_core_fitler_buf_size,
                                 ofmap_buf_size_bytes=per_core_ofmap_buf_size,
                                 ifmap_backing_buf_bw=per_core_ifmap_bw,
                                 filter_backing_buf_bw=per_core_filter_bw,
                                 ofmap_backing_buf_bw=per_core_ofmap_bw
                                 )

        # Demand mat
        this_node_ifmap_demand_mat, this_node_filter_demand_mat, this_node_ofmap_demand_mat \
            = chiplet_node.compute_node.get_demand_matrices()

        this_node_ifmap_fetch_mat, this_node_filter_fetch_mat = chiplet_node.compute_node.get_prefetch_matrices()
        if (self.config_obj.get_bandwidth_use_mode()=="USER"):
            chiplet_node.scratch_pad.set_read_buf_prefetch_matrices(ifmap_prefetch_mat=this_node_ifmap_fetch_mat,
                                                     filter_prefetch_mat=this_node_filter_fetch_mat
                                                     )
        temp = chiplet_node.scratch_pad.service_memory_requests(this_node_ifmap_demand_mat,
                                             this_node_filter_demand_mat,
                                             this_node_ofmap_demand_mat,
                                             nop_latency)

        print("Latency is: ", temp)


    def run_sys(self):
        while len(self.ready_to_run):
            #pass the latency of the chiplet to run _chiplet (to account for traces start time)
            self.run_chiplet()
            present_chiplet = self.ready_to_run.popleft()
            self.status_matrix[present_chiplet[0]][present_chiplet[1]][1] = 1
    
            #update the ready_to_run with new chiplets that are ready to run
            for i in range(len(self.dependency_matrix)):
                row = self.dependency_matrix[i]
                for j in range(len(row)):
                    ele = self.dependency_matrix[i][j]
                    if(ele == present_chiplet):
                        self.status_matrix[i][j][0] = 1
                    if(self.status_matrix[i][j] == [1,0]):
                        self.ready_to_run.append((i,j))
                        self.ready_to_run = deque(set(self.ready_to_run))
            # print(self.ready_to_run)
