import unittest
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QWidget

# We need a QApplication instance for any widget tests
app = QApplication([])

from src.app.ui.control_panel import ControlPanel
from src.app.ui.parameter_panels.fracture_params_panel import FractureParamsPanel


class MockFracturePanel(FractureParamsPanel):
    """一个用于测试的、真正的QWidget子类，但其方法可以被模拟。"""
    def __init__(self, controller):
        # We must call QWidget's init, but we can skip FractureParamsPanel's
        # complex UI setup by calling its superclass's __init__ directly.
        QWidget.__init__(self)
        self.controller = controller
        # Replace the real signal with a mock for assertion purposes
        self.parameter_changed = MagicMock()
        self.parameter_changed.connect = MagicMock()


class TestArchitectureWiring(unittest.TestCase):
    """
    测试新的解耦架构中，UI组件之间的信号-槽连接是否正确。
    """

    @patch('src.app.ui.control_panel.FractureParamsPanel', new=MockFracturePanel)
    def test_control_panel_connects_signal_to_controller_slot(self):
        """
        验证当分析模式切换时，ControlPanel是否正确地将
        新参数面板的'parameter_changed'信号连接到控制器的'update_parameter'槽。
        """
        # 1. 准备 (Arrange)
        # 创建一个模拟的 Controller
        mock_controller = MagicMock()
        mock_controller.update_parameter = MagicMock() # 模拟槽函数

        # 模拟控制器已注册了一个分析器
        mock_controller.analyzers_registered.connect = MagicMock()

        # 2. 操作 (Act)
        # 创建 ControlPanel 实例。@patch会确保它使用我们的MockFracturePanel
        panel = ControlPanel(controller=mock_controller)

        # 手动调用模式切换方法，模拟用户操作
        # 假设组合框的第一项 (index 0) 的用户数据是 "fracture"
        panel.mode_selector_combo.itemData = MagicMock(return_value='fracture')
        panel._on_mode_changed(0)

        # 3. 断言 (Assert)
        # 验证ControlPanel是否创建了我们的面板实例
        self.assertIsInstance(panel.params_stack.widget(0), MockFracturePanel)
        
        # 获取被创建的面板实例
        panel_instance = panel.params_stack.widget(0)

        # !!! 核心断言 !!!
        # 验证新创建的面板实例的 `parameter_changed` 信号
        # 是否连接到了 mock_controller 的 `update_parameter` 方法
        panel_instance.parameter_changed.connect.assert_called_once_with(
            mock_controller.update_parameter
        )

if __name__ == '__main__':
    unittest.main() 