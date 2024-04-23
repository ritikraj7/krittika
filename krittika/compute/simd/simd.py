import numpy as np
import math
from krittika_config import KrittikaConfig


# Treat this as a macro for initialization
dummy_matrix = np.ones((1, 1)) * -1


class simd:
    def __init__(self):
        # Compute Unit
        self.simd_length = 1
        self.config_obj = KrittikaConfig()
        self.topology_obj = None
        self.simd_op = "RELU"
        self.avg_mapping_efficiency = 0


        # Operand matrix
        self.op_matrix = dummy_matrix

        # Flags
        self.params_set = False
        self.operands_valid = False

    def gelu(self, x):
        """ Gaussian Error Linear Unit (GELU) non-linear activation function """
        c = math.sqrt(2 / math.pi)
        return 0.5 * x * (1 + np.tanh(c * (x + 0.044715 * x**3)))

    def tanh(self, x):
        """ Hyperbolic tangent non-linear activation function """
        return np.tanh(x)

    def selu(self, x):
        """ Scaled Exponential Linear Unit (SELU) non-linear activation function """
        lambda_ = 1.0507
        alpha = 1.67326
        return lambda_ * (x if x >= 0 else alpha * (math.exp(x) - 1))
    #
    def set_params(self, num_units=1, simd_op = "RELU"):

        assert num_units > 0, 'Invalid number of units'
        self.simd_length = num_units
        self.simd_op = simd_op

        self.params_set = True

    #
    def set_operands(self, op_matrix=dummy_matrix):

        assert self.params_set, 'Params are not set'

        assert op_matrix.shape[0] > 0, 'Input vector cannot be None'

        self.op_matrix = op_matrix
        self.operands_valid = True
    
    #
    def calc_simd_unit(self):
        assert self.operands_valid, 'Set the operands first'
        op_matrix_size = self.op_matrix.shape[0] * self.op_matrix.shape[1]

        cycles_per_op = 1
        if self.simd_op == "RELU":
            cycles_per_op = 5
        elif self.simd_op == "GELU":
            result = self.gelu(self.op_matrix)
        elif self.simd_op == "TANH":
            result = self.tanh(self.op_matrix)
        elif self.simd_op == "SELU":
            result = self.selu(self.op_matrix)
        else:
            result = np.maximum(0, self.op_matrix)  # Default to RELU if operation not recognized
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
