#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试控制器模块。
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.core.controller import Controller
from src.app.core.analysis_stages import AnalysisStage

class TestController(unittest.TestCase):
    """测试Controller类的功能。"""
    
    def setUp(self):
        """测试前的设置。"""
        self.controller = Controller()

    def test_run_fracture_analysis_params_reachability(self):
        """测试run_fracture_analysis是否正确转换并传递参数。"""
        # 1. 设置模拟对象
        with patch.object(self.controller, 'image_processor', Mock()) as mock_image_processor, \
             patch.object(self.controller, 'unit_converter', Mock()) as mock_unit_converter:
            
            # 模拟返回值
            mock_image_processor.analyze_fractures.return_value = []
            mock_unit_converter.mm_to_pixels.return_value = 150.0 # 模拟转换后的像素值

            # 2. 准备测试输入
            min_aspect_ratio = 5.0
            min_length_mm = 10.0
            test_dpi = (300, 300)
            
            # 为控制器设置必要的属性，以通过前置检查
            self.controller.current_dpi = test_dpi
            # 模拟一个有效的形态学和原始图像结果
            self.controller.analysis_results = {
                AnalysisStage.MORPHOLOGY: {'image': np.zeros((10,10), dtype=np.uint8)},
                AnalysisStage.ORIGINAL: {'image': np.zeros((10,10), dtype=np.uint8)}
            }
            
            # 3. 调用被测试的函数
            self.controller.run_fracture_analysis(
                min_aspect_ratio=min_aspect_ratio,
                min_length=min_length_mm
            )

            # 4. 断言
            # 验证单位转换是否以正确的参数被调用
            mock_unit_converter.mm_to_pixels.assert_called_once_with(min_length_mm, test_dpi[0])
            
            # 验证裂缝分析是否以正确的参数被调用
            mock_image_processor.analyze_fractures.assert_called_once()
            call_args = mock_image_processor.analyze_fractures.call_args[1]
            
            self.assertEqual(call_args['min_aspect_ratio'], min_aspect_ratio)
            self.assertEqual(call_args['min_length_pixels'], 150.0) # 验证传递的是转换后的像素值

if __name__ == "__main__":
    unittest.main() 