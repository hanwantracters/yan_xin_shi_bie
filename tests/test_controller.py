#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试控制器模块。
"""

import unittest
import json
import os
from unittest.mock import MagicMock, patch
import numpy as np

# 将src目录添加到sys.path以进行绝对导入
import sys
# 确保即使从tests目录运行，也能找到src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 在导入PyQt之前，模拟/创建 QApplication
from PyQt5.QtWidgets import QApplication
# 防止在CI/CD或无头环境中运行测试时出错
if QApplication.instance() is None:
    app = QApplication(sys.argv)

from src.app.core.controller import Controller
from src.app.core.analysis_stages import AnalysisStage

class TestControllerParams(unittest.TestCase):
    """测试Controller类的新增参数管理功能。"""

    def setUp(self):
        """为每个测试用例设置一个新的Controller实例。"""
        self.controller = Controller()
        
        # 确保有一个默认的参数结构
        self.controller._load_default_parameters()
        
        # 创建一个临时文件用于测试保存和加载
        self.temp_params_file = "temp_test_params.json"

    def tearDown(self):
        """在每个测试用例后清理临时文件。"""
        if os.path.exists(self.temp_params_file):
            os.remove(self.temp_params_file)

    def test_load_default_parameters_exists_and_has_keys(self):
        """测试: Controller初始化时，默认参数是否成功加载并包含必要的键。"""
        self.assertIsNotNone(self.controller.analysis_params)
        self.assertIn("version", self.controller.analysis_params)
        self.assertIn("analysis_parameters", self.controller.analysis_params)
        self.assertIn("threshold", self.controller.analysis_params["analysis_parameters"])

    def test_update_parameter_modifies_nested_value(self):
        """测试: update_parameter 是否能正确修改一个嵌套的参数值。"""
        new_block_size = 25
        self.controller.update_parameter("threshold.block_size", new_block_size)
        
        retrieved_block_size = self.controller.analysis_params["analysis_parameters"]["threshold"]["block_size"]
        self.assertEqual(retrieved_block_size, new_block_size)

    def test_save_and_load_parameters_e2e(self):
        """测试: save_parameters 和 load_parameters 的端到端功能。"""
        # 1. 修改一个参数并保存
        self.controller.update_parameter("filtering.min_length_mm", 99.9)
        self.controller.save_parameters(self.temp_params_file)
        
        self.assertTrue(os.path.exists(self.temp_params_file))

        # 2. 创建一个新的控制器实例来加载
        new_controller = Controller()
        
        # 模拟信号发射
        new_controller.parameters_updated = MagicMock()
        
        new_controller.load_parameters(self.temp_params_file)

        # 3. 验证加载的参数是否正确，以及信号是否被发射
        loaded_value = new_controller.analysis_params["analysis_parameters"]["filtering"]["min_length_mm"]
        self.assertEqual(loaded_value, 99.9)
        new_controller.parameters_updated.emit.assert_called_once()
        
    def test_update_new_parameters(self):
        """测试: update_parameter 是否能正确修改新增的嵌套参数值。"""
        # 测试 Niblack k 值
        new_niblack_k = -0.5
        self.controller.update_parameter("threshold.niblack_k", new_niblack_k)
        retrieved_niblack_k = self.controller.analysis_params["analysis_parameters"]["threshold"]["niblack_k"]
        self.assertEqual(retrieved_niblack_k, new_niblack_k)

        # 测试 Sauvola r 值
        new_sauvola_r = 100
        self.controller.update_parameter("threshold.sauvola_r", new_sauvola_r)
        retrieved_sauvola_r = self.controller.analysis_params["analysis_parameters"]["threshold"]["sauvola_r"]
        self.assertEqual(retrieved_sauvola_r, new_sauvola_r)

        # 测试形态学迭代次数
        new_open_iterations = 5
        self.controller.update_parameter("morphology.open_iterations", new_open_iterations)
        retrieved_open_iterations = self.controller.analysis_params["analysis_parameters"]["morphology"]["open_iterations"]
        self.assertEqual(retrieved_open_iterations, new_open_iterations)

    @patch('src.app.core.controller.ImageProcessor')
    def test_full_analysis_pipeline_with_mocked_processor(self, MockImageProcessor):
        """测试: 完整分析流程中，参数是否被正确传递给ImageProcessor。"""
        # 准备: 模拟 ImageProcessor 实例和它的方法
        mock_processor_instance = MockImageProcessor.return_value
        mock_processor_instance.analyze_fractures.return_value = [{'dummy': 'fracture'}]
        mock_processor_instance.merge_fractures.return_value = [{'area_pixels': 1, 'length_pixels': 1, 'angle': 1}]
        mock_processor_instance.draw_analysis_results.return_value = 'final_image'

        # 将模拟的处理器实例注入到控制器中
        self.controller.image_processor = mock_processor_instance
        
        # 准备: 设置分析所需的前置状态
        self.controller.current_dpi = (25.4, 25.4) # 1 mm = 1 pixel
        self.controller.analysis_results[AnalysisStage.MORPHOLOGY] = {'image': 'dummy_binary_image'}
        self.controller.analysis_results[AnalysisStage.ORIGINAL] = {'image': 'dummy_original_image'}

        # 准备: 设置自定义参数
        test_aspect_ratio = 20.0
        test_merge_dist_mm = 5.0
        test_angle_diff = 30.0
        self.controller.update_parameter("filtering.min_aspect_ratio", test_aspect_ratio)
        self.controller.update_parameter("merging.enabled", True)
        self.controller.update_parameter("merging.merge_distance_mm", test_merge_dist_mm)
        self.controller.update_parameter("merging.max_angle_diff", test_angle_diff)
        
        # 执行
        self.controller.run_fracture_analysis()

        # 验证: analyze_fractures 是否被正确调用
        mock_processor_instance.analyze_fractures.assert_called_once()
        _, kwargs_analyze = mock_processor_instance.analyze_fractures.call_args
        self.assertEqual(kwargs_analyze.get('min_aspect_ratio'), test_aspect_ratio)

        # 验证: merge_fractures 是否被正确调用
        mock_processor_instance.merge_fractures.assert_called_once()
        _, kwargs_merge = mock_processor_instance.merge_fractures.call_args
        self.assertEqual(kwargs_merge.get('max_distance'), test_merge_dist_mm) # 1mm = 1px, so 5.0
        self.assertEqual(kwargs_merge.get('max_angle_diff'), test_angle_diff)
        
        # 验证: draw_analysis_results 是否被正确调用
        mock_processor_instance.draw_analysis_results.assert_called_once()


if __name__ == '__main__':
    unittest.main() 