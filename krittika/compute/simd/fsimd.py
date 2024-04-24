import numpy as np
import math
from krittika_config import KrittikaConfig

dummy_matrix = np.ones((1, 1)) * -1

class simd:
    def __init__(self):
        self.simd_length = 1
        self.config_obj = KrittikaConfig()
        self.topology_obj = None
        self.simd_op = "RELU"
        self.avg_mapping_efficiency = 0
        self.op_matrix = dummy_matrix
        self.params_set = False
        self.operands_valid = False

    def set_params(self, num_units=1, simd_op="RELU"):
        assert num_units > 0, 'Invalid number of units'
        self.simd_length = num_units
        self.simd_op = simd_op
        self.params_set = True

    def set_operands(self, op_matrix=dummy_matrix):
        assert self.params_set, 'Params are not set'
        assert op_matrix.shape[0] > 0 and op_matrix.ndim == 2, 'Input vector must be two-dimensional'
        self.op_matrix = op_matrix
        self.operands_valid = True

    def calc_simd_unit(self):
        assert self.operands_valid, 'Set the operands first'
        result = None
        if self.simd_op == "RELU":
            result = np.maximum(0, self.op_matrix)
        elif self.simd_op == "GELU":
            result = 0.5 * self.op_matrix * (1 + np.tanh(np.sqrt(2 / np.pi) * (self.op_matrix + 0.044715 * np.power(self.op_matrix, 3))))
        elif self.simd_op == "TANH":
            result = np.tanh(self.op_matrix)
        elif self.simd_op == "SELU":
            lambda_ = 1.0507
            alpha = 1.67326
            result = lambda_ * np.where(self.op_matrix >= 0, self.op_matrix, alpha * (np.exp(self.op_matrix) - 1))
        elif self.simd_op == "SIGMOID":
            result = 1 / (1 + np.exp(-self.op_matrix))
        elif self.simd_op == "SOFTMAX":
            e_x = np.exp(self.op_matrix - np.max(self.op_matrix))
            result = e_x / e_x.sum(axis=0)
        elif self.simd_op == "ELU":
            alpha = 1.0
            result = np.where(self.op_matrix >= 0, self.op_matrix, alpha * (np.exp(self.op_matrix) - 1))
        elif self.simd_op == "SWISH":
            result = self.op_matrix * (1 / (1 + np.exp(-self.op_matrix)))
        elif self.simd_op == "MISH":
            result = self.op_matrix * np.tanh(np.log(1 + np.exp(self.op_matrix)))
        elif self.simd_op == "SOFTPLUS":
            result = np.log1p(np.exp(self.op_matrix))
        elif self.simd_op == "SOFTSIGN":
            result = self.op_matrix / (1 + np.abs(self.op_matrix))
        elif self.simd_op == "SINUSOID":
            result = np.sin(self.op_matrix)
        else:
            raise ValueError("Unsupported SIMD operation")
        return result

    def get_avg_mapping_efficiency(self):
        assert self.operands_valid, 'Set the operands first'
        return self.avg_mapping_efficiency

    def get_compute_cycles(self):
        assert self.operands_valid, 'Set the operands first'
        return self.compute_cycles
