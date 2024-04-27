import unittest
from simd import simd  # Ensure this path is correct based on your project structure
import numpy as np

class TestSIMDOperations(unittest.TestCase):
    def setUp(self):
        self.instance = simd()
        self.instance.set_params(num_units=2, simd_op="RELU")  # Set parameters appropriately

    def test_gelu(self):
        self.instance.set_params(num_units=2, simd_op="GELU")
        input_matrix = np.array([[0, 1]])  # Ensure the input is two-dimensional
        self.instance.set_operands(input_matrix)
        expected_results = np.array([[0, 0.8413]])
        result = self.instance.calc_simd_unit() # Capture result to verify
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_tanh(self):
    	self.instance.set_params(num_units=2, simd_op="TANH")
    	input_matrix = np.array([[0, 1]])  # Ensure input is two-dimensional
    	self.instance.set_operands(input_matrix)
    	expected_results = np.array([[0, 0.7616]])
    	result = self.instance.calc_simd_unit()  # Capture result to verify
    	np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_selu(self):
    	self.instance.set_params(num_units=2, simd_op="SELU")
    	input_matrix = np.array([[0, -1]])  # Ensure input is two-dimensional
    	self.instance.set_operands(input_matrix)
    	expected_results = np.array([[0, -1.1113]])
    	result = self.instance.calc_simd_unit()  # Capture result to verify
    	np.testing.assert_almost_equal(result, expected_results, decimal=4)


    def test_sigmoid(self):
        self.instance.set_params(num_units=2, simd_op="SIGMOID")
        input_matrix = np.array([[0, -1], [1, 3]])  # Example input
        self.instance.set_operands(input_matrix)
        expected_results = 1 / (1 + np.exp(-input_matrix))
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_softmax(self):
        self.instance.set_params(num_units=2, simd_op="SOFTMAX")
        input_matrix = np.array([[1, 2]])
        self.instance.set_operands(input_matrix)
        e_x = np.exp(input_matrix - np.max(input_matrix))
        expected_results = e_x / e_x.sum(axis=0)
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_elu(self):
        self.instance.set_params(num_units=2, simd_op="ELU")
        input_matrix = np.array([[-1, 1], [0, -2]])
        self.instance.set_operands(input_matrix)
        alpha = 1.0
        expected_results = np.where(input_matrix >= 0, input_matrix, alpha * (np.exp(input_matrix) - 1))
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_swish(self):
        self.instance.set_params(num_units=2, simd_op="SWISH")
        input_matrix = np.array([[0, 1]])
        self.instance.set_operands(input_matrix)
        expected_results = input_matrix * (1 / (1 + np.exp(-input_matrix)))
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_mish(self):
        self.instance.set_params(num_units=2, simd_op="MISH")
        input_matrix = np.array([[0, 1]])
        self.instance.set_operands(input_matrix)
        expected_results = input_matrix * np.tanh(np.log(1 + np.exp(input_matrix)))
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_softplus(self):
        self.instance.set_params(num_units=2, simd_op="SOFTPLUS")
        input_matrix = np.array([[0, 1]])
        self.instance.set_operands(input_matrix)
        expected_results = np.log1p(np.exp(input_matrix))
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_softsign(self):
        self.instance.set_params(num_units=2, simd_op="SOFTSIGN")
        input_matrix = np.array([[0, 1]])
        self.instance.set_operands(input_matrix)
        expected_results = input_matrix / (1 + np.abs(input_matrix))
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

    def test_sinusoid(self):
        self.instance.set_params(num_units=2, simd_op="SINUSOID")
        input_matrix = np.array([[0, np.pi/2], [np.pi, 3*np.pi/2]])
        self.instance.set_operands(input_matrix)
        expected_results = np.sin(input_matrix)
        result = self.instance.calc_simd_unit()
        np.testing.assert_almost_equal(result, expected_results, decimal=4)

if __name__ == '__main__':
    unittest.main()
