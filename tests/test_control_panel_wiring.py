import unittest
from unittest.mock import Mock, MagicMock
import sys

from PyQt5.QtWidgets import QApplication

# 确保在测试环境中可以找到src目录
sys.path.insert(0, '.')

from src.app.core.controller import Controller
from src.app.ui.control_panel import ControlPanel
from src.app.ui.parameter_panels.fracture_params_panel import FractureParamsPanel

class TestControlPanelWiring(unittest.TestCase):
    """
    测试ControlPanel是否能正确地将参数面板的信号连接到控制器的槽。
    """
    @classmethod
    def setUpClass(cls):
        """为所有测试创建一个共享的QApplication实例。"""
        cls.app = QApplication(sys.argv)

    def test_fracture_panel_signal_is_wired_to_controller(self):
        """
        验证当FractureParamsPanel被加载时，其parameter_changed信号
        被成功连接到controller.update_parameter方法。
        """
        # 1. 准备
        controller = Controller()
        # 使用Mock替换真实的方法以便于断言
        controller.update_parameter = MagicMock()
        
        control_panel = ControlPanel(controller)
        
        # 2. 触发动作
        # 手动触发模式切换，这会加载FractureParamsPanel
        control_panel._on_mode_changed(0) 
        
        # 从堆叠窗口中获取被加载的面板实例
        loaded_panel = control_panel.params_stack.currentWidget()
        
        self.assertIsInstance(
            loaded_panel, 
            FractureParamsPanel,
            "加载的面板不是FractureParamsPanel的实例"
        )
        
        # 定义要发送的测试数据
        test_key = "test.param.key"
        test_value = 12345
        
        # 从面板发射信号
        loaded_panel.parameter_changed.emit(test_key, test_value)

        # 3. 断言
        # 验证被Mock的controller.update_parameter方法是否被调用
        controller.update_parameter.assert_called_once_with(test_key, test_value)

if __name__ == '__main__':
    unittest.main() 