import unittest
from nsimd import simd  # Import simd class from simd module
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

if __name__ == '__main__':
    unittest.main()
