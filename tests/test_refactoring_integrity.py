"""测试重构后架构的完整性。

该测试模块旨在验证大规模重构后，新的基于策略模式的架构
是否能够正确初始化、连接并执行核心分析流程。
"""

import unittest
import numpy as np
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QWidget

# 确保在GUI组件实例化之前有一个QApplication实例
app = QApplication.instance()
if app is None:
    app = QApplication([])

from src.app.core.controller import Controller
from src.app.ui.control_panel import ControlPanel

class TestRefactoringIntegrity(unittest.TestCase):
    """测试用例，验证重构后的架构完整性。"""

    def setUp(self):
        """在每个测试用例前执行。"""
        self.controller = Controller()

    def test_analyzer_registration(self):
        """测试1: 验证Controller是否能成功注册FractureAnalyzer。"""
        self.assertIn("fracture", self.controller.analyzers)
        self.assertIsNotNone(self.controller.active_analyzer)
        self.assertEqual(self.controller.active_analyzer.get_id(), "fracture")
        print("[Test OK] FractureAnalyzer successfully registered and activated.")

    @patch('src.app.core.analyzers.fracture_analyzer.FractureAnalyzer.create_parameter_widget')
    def test_ui_dynamic_setup(self, mock_create_widget):
        """测试2: 验证ControlPanel是否能根据注册的分析器动态构建UI。"""
        # 创建一个模拟的QWidget，因为我们不想真的创建UI
        mock_widget = QWidget()
        mock_create_widget.return_value = mock_widget

        # 模拟信号/槽连接
        control_panel = ControlPanel(self.controller)
        # 手动调用槽函数，因为我们没有运行Qt事件循环
        control_panel._on_analyzers_registered(
            [(analyzer.get_id(), analyzer.get_name()) for analyzer in self.controller.analyzers.values()]
        )
        
        self.assertEqual(control_panel.mode_selector_combo.count(), 1)
        self.assertEqual(control_panel.mode_selector_combo.itemText(0), "裂缝分析")
        self.assertEqual(control_panel.mode_selector_combo.itemData(0), "fracture")
        self.assertEqual(control_panel.params_stack.count(), 1)
        self.assertEqual(control_panel.params_stack.currentWidget(), mock_widget)
        print("[Test OK] ControlPanel UI dynamically set up for FractureAnalyzer.")

    def test_analysis_execution(self):
        """测试3: 验证核心分析流程是否能被完整调用并返回预期格式的结果。"""
        # 创建一个100x100的黑色虚拟图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.controller.current_image = test_image
        self.controller.current_dpi = (300, 300) # 模拟DPI

        # 直接调用完整的分析方法
        # 使用MagicMock来捕获analysis_complete信号发出的数据
        mock_slot = MagicMock()
        self.controller.analysis_complete.connect(mock_slot)
        
        self.controller.run_full_analysis()

        # 验证信号被调用了一次
        mock_slot.assert_called_once()
        # 获取信号发出的参数
        result = mock_slot.call_args[0][0]

        # 验证返回结果的结构是否正确
        self.assertIsInstance(result, dict)
        self.assertIn('count', result)
        self.assertIn('total_area_mm2', result)
        self.assertIn('total_length_mm', result)
        self.assertIn('details', result)
        print("[Test OK] Full analysis execution call successful with correct result structure.")

if __name__ == '__main__':
    unittest.main() 