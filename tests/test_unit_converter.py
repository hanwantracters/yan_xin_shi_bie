"""UnitConverter类的单元测试。

该模块包含对UnitConverter类的所有方法的测试用例。
"""

import unittest
import numpy as np
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.core.unit_converter import UnitConverter


class TestUnitConverter(unittest.TestCase):
    """UnitConverter类的测试用例。"""
    
    def test_pixels_to_mm_single_value(self):
        """测试pixels_to_mm方法处理单个数值的情况。"""
        # 测试整数
        result = UnitConverter.pixels_to_mm(100, 72)
        self.assertAlmostEqual(result, 35.27777777777778)
        
        # 测试浮点数
        result = UnitConverter.pixels_to_mm(100.5, 72)
        self.assertAlmostEqual(result, 35.454166666666666)
    
    def test_pixels_to_mm_array(self):
        """测试pixels_to_mm方法处理NumPy数组的情况。"""
        pixels = np.array([100, 200, 300])
        result = UnitConverter.pixels_to_mm(pixels, 96)
        expected = np.array([26.458333333333332, 52.916666666666664, 79.375])
        np.testing.assert_almost_equal(result, expected)
    
    def test_mm_to_pixels_single_value(self):
        """测试mm_to_pixels方法处理单个数值的情况。"""
        # 测试整数
        result = UnitConverter.mm_to_pixels(10, 72)
        self.assertAlmostEqual(result, 28.346456692913385)
        
        # 测试浮点数
        result = UnitConverter.mm_to_pixels(10.5, 72)
        self.assertAlmostEqual(result, 29.763779527559054)
    
    def test_mm_to_pixels_array(self):
        """测试mm_to_pixels方法处理NumPy数组的情况。"""
        mm = np.array([10, 20, 30])
        result = UnitConverter.mm_to_pixels(mm, 96)
        expected = np.array([37.795275590551178, 75.590551181102362, 113.38582677165354])
        np.testing.assert_almost_equal(result, expected)
    
    def test_convert_point(self):
        """测试convert_point方法。"""
        point = (100, 200)
        result = UnitConverter.convert_point(point, 72)
        expected = (35.27777777777778, 70.55555555555556)
        self.assertAlmostEqual(result[0], expected[0])
        self.assertAlmostEqual(result[1], expected[1])
    
    def test_convert_distance(self):
        """测试convert_distance方法。"""
        distance = 150
        result = UnitConverter.convert_distance(distance, 96)
        expected = 39.6875
        self.assertAlmostEqual(result, expected)
    
    def test_convert_area(self):
        """测试convert_area方法。"""
        area = 10000  # 100x100像素的面积
        result = UnitConverter.convert_area(area, 72)
        expected = 1244.5216049382714 # (25.4/72)^2 * 10000
        self.assertAlmostEqual(result, expected)
    
    def test_zero_dpi_error(self):
        """测试DPI为0时抛出ValueError异常。"""
        with self.assertRaises(ValueError):
            UnitConverter.pixels_to_mm(100, 0)
        
        with self.assertRaises(ValueError):
            UnitConverter.mm_to_pixels(10, 0)
        
        with self.assertRaises(ValueError):
            UnitConverter.convert_area(1000, 0)
    
    def test_negative_dpi_error(self):
        """测试DPI为负值时抛出ValueError异常。"""
        with self.assertRaises(ValueError):
            UnitConverter.pixels_to_mm(100, -72)
        
        with self.assertRaises(ValueError):
            UnitConverter.mm_to_pixels(10, -96)


if __name__ == '__main__':
    unittest.main() 