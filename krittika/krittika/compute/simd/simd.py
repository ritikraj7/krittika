import numpy as np
import math
from krittika.config.krittika_config import KrittikaConfig
from krittika.partition_manager import PartitionManager


# Treat this as a macro for initialization
dummy_matrix = np.ones((1, 1)) * -1


class simd:
    def __init__(self):
        # Compute Unit
        self.simd_length = 1
        self.config_obj = KrittikaConfig()
        self.partition_obj = PartitionManager()
        self.topology_obj = None
        self.simd_op = "RELU"
        self.avg_mapping_efficiency = 0
        self.compute_cycles = 0
       
        
        # Operand matrix
        self.op_matrix = dummy_matrix

        # Flags
        self.params_set = False
        self.operands_valid = False

    #
    def set_params(self, config = KrittikaConfig(), partition = PartitionManager(), num_units=1, simd_op = "RELU", ):

        assert num_units > 0, 'Invalid number of units'
        self.simd_length = num_units
        self.simd_op = simd_op 
        self.partition_obj = partition
        self.config_obj =config
        self.params_set = True

    #
    def set_operands(self, op_matrix=dummy_matrix):

        assert self.params_set, 'Params are not set'

        assert op_matrix.shape[0] > 0, 'Input vector cannot be None'

        self.op_matrix = op_matrix
        self.operands_valid = True
    
    #
    # def calc_simd_unit(self):
    #     assert self.operands_valid, 'Set the operands first'
    #     op_matrix_size = self.op_matrix.shape[0] * self.op_matrix.shape[1]
    #    # print(f"inside calc simd unit function: the simd op is: {self.simd_op}")
    #     #print(op_matrix_size)
    #     cycles_per_op = 1
      

    #     if self.simd_op == "relu":
    #         cycles_per_op = 5
            
    #     if self.simd_op == 'adde':
    #         cycles_per_op = 1

    #     self.avg_mapping_efficiency = ((op_matrix_size // self.simd_length) * self.simd_length + op_matrix_size \
    #                                    % self.simd_length) / (math.ceil(op_matrix_size / self.simd_length) * self.simd_length)
    #     self.compute_cycles =  math.ceil(op_matrix_size / self.simd_length) * cycles_per_op
    #     if self.simd_op == 'maxpool':
    #         #print("Entering if condition for maxpool")
    #         for i in self.partition_obj.workload.topo_list:
    #             if i[2] == 'maxpool':
    #                 layer_id = i[1]
    #                 break
            
    #         cycles_per_op = 5 * self.partition_obj.workload.topo_list[layer_id][5] # 5 * num_cahnnels
    #         self.compute_cycles =  1000
    #        # print(f"Maxpool compute cycles are: {self.compute_cycles}")
    def calc_simd_unit(self):
        assert self.operands_valid, 'Set the operands first'
        op_matrix_size = self.op_matrix.shape[0] * self.op_matrix.shape[1]
        
        cycles_per_op = 3
        if self.simd_op == 'maxpool':
            for i in self.partition_obj.workload.topo_list:
                if i[2] == 'maxpool':
                    layer_id = i[1]
                    break
            pool_w = self.partition_obj.workload.topo_list[layer_id][4]
            pool_h = self.partition_obj.workload.topo_list[layer_id][3]
            pool_s = self.partition_obj.workload.topo_list[layer_id][6]
            input_w = self.partition_obj.workload.topo_list[layer_id-1][2]
            input_h = self.partition_obj.workload.topo_list[layer_id-1][3]
            # print(input_h)
            # input_h = self.op_matrix.shape[1]/input_w 
            # print(input_h)
           #```````````````````````````````````                   cc  ` print(self.op_matrix.shape)
            operations_W = (self.op_matrix.shape[0] - pool_w) // pool_s + 1
            operations_H = ( self.op_matrix.shape[1] - pool_h) // pool_s + 1
            num_windows = operations_H*operations_W
           # windows_per_core = math.ceil(num_windows / (self.config_obj.num_compute_cores))
            #print(self.config_obj.num_compute_cores)
            #num_channels = self.partition_obj.workload.topo_list[layer_id][5]
            # current_elements = pool_h*pool_w
            # stages = 0
            # total_comparators_used = 0
            # efficiencies = []
           
            
            # while current_elements > 1:
            #     if current_elements / 2 <= self.simd_length:
            #         num_comparators_used = math.ceil(current_elements / 2)
            #     else:
            #         num_comparators_used = self.simd_length
            #     # Calculate efficiency for this stage
            #     efficiency = (num_comparators_used / self.simd_length)
            #     efficiencies.append(efficiency)
            #     # Update the number of elements that will be compared in the next stage
            #     current_elements = math.ceil(current_elements / 2)
            #     stages += 1
            #     total_comparators_used += num_comparators_used
            
            # Calculate the total cycles needed for the computation
            total_cycles = cycles_per_op * num_windows //self.simd_length
            self.compute_cycles = total_cycles
            
            
            # Calculate average efficiency
            #average_efficiency = sum(efficiencies) / len(efficiencies)
            self.avg_mapping_efficiency = ((op_matrix_size // self.simd_length) * self.simd_length + op_matrix_size \
                                        % self.simd_length) / (math.ceil(op_matrix_size / self.simd_length) * self.simd_length)


        if self.simd_op == "adde":
            cycles_per_op = 1

            self.avg_mapping_efficiency = ((op_matrix_size // self.simd_length) * self.simd_length + op_matrix_size \
                                        % self.simd_length) / (math.ceil(op_matrix_size / self.simd_length) * self.simd_length)
            self.compute_cycles = math.ceil(op_matrix_size / self.simd_length) * cycles_per_op
            #print(self.compute_cycles)

        if self.simd_op == "relu":
            cycles_per_op = 5

            self.avg_mapping_efficiency = ((op_matrix_size // self.simd_length) * self.simd_length + op_matrix_size \
                                        % self.simd_length) / (math.ceil(op_matrix_size / self.simd_length) * self.simd_length)
            self.compute_cycles = math.ceil(op_matrix_size / self.simd_length) * cycles_per_op     
    #
    def get_avg_mapping_efficiency(self):
        assert self.operands_valid, 'Set the operands first'
        return self.avg_mapping_efficiency

    #
    def get_avg_compute_utilization(self):
        assert self.operands_valid, 'Set the operands first'
        return self.avg_mapping_efficiency

    
    def get_compute_cycles(self):
        assert self.operands_valid, 'Set the operands first'
        return self.compute_cycles