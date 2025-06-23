"""测试主窗口的UI更新逻辑

该模块包含针对 MainWindow 中与UI更新相关的槽函数的单元测试。
它验证当控制器发出信号时，主窗口是否正确地调用了
其子组件（如ResultPanel, PreviewWindow）的更新方法。
"""
import unittest
from unittest.mock import Mock, patch, MagicMock

# 模拟PyQt5导入，因为在测试环境中我们不运行GUI
# 这必须在导入被测模块之前完成
import sys
mock_pyqt = MagicMock()
sys.modules['PyQt5'] = mock_pyqt
sys.modules['PyQt5.QtWidgets'] = mock_pyqt.QtWidgets
sys.modules['PyQt5.QtGui'] = mock_pyqt.QtGui
sys.modules['PyQt5.QtCore'] = mock_pyqt.QtCore


# 模拟本地模块的导入
# 我们只需要测试 MainWindow 的逻辑，不需要真实的UI或Core组件
sys.modules['src.app.ui.control_panel'] = MagicMock()
sys.modules['src.app.ui.result_panel'] = MagicMock()
sys.modules['src.app.ui.preview_window'] = MagicMock()
sys.modules['src.app.ui.analysis_preview_window'] = MagicMock()
sys.modules['src.app.ui.measurement_dialog'] = MagicMock()
sys.modules['src.app.ui.style_manager'] = MagicMock()
sys.modules['src.app.core.controller'] = MagicMock()
# sys.modules['src.app.ui.main_window'] = MagicMock() # <-- 这一行是错误的，我们需要真实的MainWindow

# 现在可以安全地导入被测模块了
from src.app.ui.main_window import MainWindow
from src.app.core.analysis_stages import AnalysisStage


class TestMainWindowUpdates(unittest.TestCase):
    """测试MainWindow的信号响应和UI更新调用。"""

    @patch('src.app.core.controller.Controller')
    def setUp(self, MockController):
        """为每个测试用例设置环境。"""
        # 阻止 MainWindow 的 UI 初始化和信号连接
        with patch.object(MainWindow, '_init_ui', return_value=None), \
             patch.object(MainWindow, '_connect_signals', return_value=None):

            # 实例化 MainWindow
            # 它会调用被 patch 的 _init_ui，所以不会创建真实UI
            self.main_window = MainWindow()

            # 现在手动设置模拟的控制器和UI组件
            self.mock_controller = MockController()
            self.main_window.controller = self.mock_controller
            self.main_window.result_panel = Mock()
            self.main_window.preview_window = Mock()
            self.main_window.analysis_preview_window = Mock()
            self.main_window.statusBar = Mock() # statusBar 也是在 _init_ui 中创建的


    def test_on_analysis_complete_updates_result_panel(self):
        """测试 _on_analysis_complete 是否调用 result_panel 的更新方法。"""
        # 1. 准备
        test_results = {'count': 10, 'total_area_mm2': 50.5}
        
        # 2. 调用
        # 直接调用槽函数，模拟从控制器接收到信号
        self.main_window._on_analysis_complete(test_results)
        
        # 3. 验证
        # 检查 result_panel.update_analysis_results 是否被以正确的参数调用了一次
        self.main_window.result_panel.update_analysis_results.assert_called_once_with(test_results)

    def test_on_preview_stage_updated_for_detection_updates_main_preview(self):
        """测试 _on_preview_stage_updated 在DETECTION阶段是否更新主预览窗口。"""
        # 1. 准备
        stage = AnalysisStage.DETECTION
        mock_image = "mock_detection_image"
        result_data = {"image": mock_image}
        
        # 2. 调用
        self.main_window._on_preview_stage_updated(stage, result_data)
        
        # 3. 验证
        # 验证主预览窗口的 update_image 被调用
        self.main_window.preview_window.update_image.assert_called_once_with(mock_image)
        # 验证分析预览窗口也被调用
        self.main_window.analysis_preview_window.update_stage_preview.assert_called_once()


    def test_on_preview_stage_updated_for_measurement_uses_detection_image(self):
        """测试 _on_preview_stage_updated 在MEASUREMENT阶段是否使用DETECTION图像。"""
        # 1. 准备
        stage = AnalysisStage.MEASUREMENT
        summary_text = "summary"
        result_data = {"summary": summary_text}
        
        mock_detection_image = "final_detection_image"
        # 设置模拟的控制器状态，使其在被查询时能返回DETECTION图像
        self.mock_controller.analysis_results.get.return_value = {"image": mock_detection_image}

        # 2. 调用
        self.main_window._on_preview_stage_updated(stage, result_data)

        # 3. 验证
        # 验证 analysis_preview_window 是用DETECTION图像和摘要文本调用的
        self.main_window.analysis_preview_window.update_stage_preview.assert_called_once_with(
            stage, mock_detection_image, summary_text
        )
        # 验证 get 是用 AnalysisStage.DETECTION 调用的
        self.mock_controller.analysis_results.get.assert_called_once_with(AnalysisStage.DETECTION, {})


if __name__ == '__main__':
    unittest.main() 