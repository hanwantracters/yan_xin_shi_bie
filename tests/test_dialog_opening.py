#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试控制面板上的按钮是否能正确打开对话框。
"""

import unittest
from unittest.mock import patch, MagicMock

# 将src目录添加到sys.path以进行绝对导入
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 在导入PyQt之前，模拟 QApplication
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from src.app.ui.control_panel import ControlPanel
from src.app.core.controller import Controller

class TestDialogOpening(unittest.TestCase):
    """测试ControlPanel中按钮打开对话框的功能。"""

    def setUp(self):
        """设置测试环境。"""
        # 模拟Controller和QObject的初始化
        with patch('PyQt5.QtCore.QObject.__init__'):
            self.mock_controller = Controller()
        
        # 模拟parameters_updated信号
        self.mock_controller.parameters_updated = MagicMock()
        
        # 创建待测试的ControlPanel实例
        self.control_panel = ControlPanel(self.mock_controller)

    @patch('src.app.ui.control_panel.ThresholdSettingsDialog')
    def test_open_threshold_dialog_button(self, MockThresholdDialog):
        """测试: 点击二值化参数按钮是否会实例化并显示对话框。"""
        # 模拟对话框实例和方法
        mock_dialog_instance = MockThresholdDialog.return_value
        
        # 第一次点击
        self.control_panel.threshold_btn.click()
        MockThresholdDialog.assert_called_once_with(self.mock_controller, self.control_panel)
        mock_dialog_instance.show.assert_called_once()
        mock_dialog_instance.activateWindow.assert_called_once()

        # 第二次点击，不应再次创建实例
        self.control_panel.threshold_btn.click()
        MockThresholdDialog.assert_called_once() # 确认构造函数仍只被调用一次
        self.assertEqual(mock_dialog_instance.show.call_count, 2)
        self.assertEqual(mock_dialog_instance.activateWindow.call_count, 2)

    @patch('src.app.ui.control_panel.MorphologySettingsDialog')
    def test_open_morphology_dialog_button(self, MockMorphologyDialog):
        """测试: 点击形态学参数按钮是否会实例化并显示对话框。"""
        mock_dialog_instance = MockMorphologyDialog.return_value
        self.control_panel.morphology_btn.click()
        MockMorphologyDialog.assert_called_once_with(self.mock_controller, self.control_panel)
        mock_dialog_instance.show.assert_called_once()

    @patch('src.app.ui.control_panel.FilteringSettingsDialog')
    def test_open_filtering_dialog_button(self, MockFilteringDialog):
        """测试: 点击过滤参数按钮是否会实例化并显示对话框。"""
        mock_dialog_instance = MockFilteringDialog.return_value
        self.control_panel.filtering_btn.click()
        MockFilteringDialog.assert_called_once_with(self.mock_controller, self.control_panel)
        mock_dialog_instance.show.assert_called_once()

if __name__ == '__main__':
    unittest.main() 