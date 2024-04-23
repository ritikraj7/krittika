import unittest
from nsimd import simd  # Adjust this import based on your project structure
import numpy as np

class TestSIMDOperations(unittest.TestCase):
    def setUp(self):
        # Set up is done before each test function execution.
        self.instance = simd()
        self.instance.set_params(num_units=2)  # Set any necessary parameters

    def test_gelu(self):
        #imput_matrix = np.array([[0,1]])
        self.instance.set_operands(np.array([[0, 1]]))
        expected_results = np.array([0, 0.8413])
        np.testing.assert_almost_equal(self.instance.calc_simd_unit(), expected_results, decimal=4)

    def test_tanh(self):
        self.instance.set_operands(np.array([[0, 1]]))
        expected_results = np.array([0, 0.7616])
        np.testing.assert_almost_equal(self.instance.calc_simd_unit(), expected_results, decimal=4)

    def test_selu(self):
        self.instance.set_operands(np.array([[0, -1]]))
        expected_results = np.array([0, -1.1113])
        np.testing.assert_almost_equal(self.instance.calc_simd_unit(), expected_results, decimal=4)

if __name__ == '__main__':
    unittest.main()
