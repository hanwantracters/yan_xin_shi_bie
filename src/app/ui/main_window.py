"""主窗口模块，应用程序的主界面。

该模块组装了所有UI组件，包括控制面板、结果面板和预览窗口等，
构成了应用程序的完整界面。
"""

from PyQt5.QtWidgets import (
    QMainWindow, 
    QAction, 
    QSplitter, 
    QVBoxLayout, 
    QWidget,
    QFileDialog,
    QMessageBox,
    QLabel,
    QDialog,
    QApplication
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import numpy as np

# 导入本地UI组件
from .control_panel import ControlPanel
from .result_panel import ResultPanel
from .multi_stage_preview_widget import MultiStagePreviewWidget
from .measurement_dialog import MeasurementDialog
from .style_manager import style_manager  # 导入样式管理器
from .dialogs.fracture_result_dialog import FractureResultDialog
from .dialogs.pore_result_dialog import PoreResultDialog

# 导入控制器和枚举
from ..core.controller import Controller
from ..utils.constants import StageKeys, PreviewState, ResultKeys


class MainWindow(QMainWindow):
    """主窗口类，应用程序的主界面。
    
    该类组装了所有UI组件，处理组件间的交互逻辑，
    并提供菜单栏等功能。
    
    Attributes:
        control_panel: 控制面板实例
        result_panel: 结果面板实例
        main_preview_window: 主预览窗口实例
        controller: 应用程序控制器实例
    """
    
    def __init__(self):
        """初始化主窗口。"""
        super().__init__()
        # 创建控制器
        self.controller = Controller()
        self.current_result_dialog = None
        self.result_dialog_classes = {
            'fracture': FractureResultDialog,
            'pore_watershed': PoreResultDialog
        }
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        # 设置窗口标题和大小
        self.setWindowTitle("岩石裂缝分析系统")
        self.resize(1000, 600)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建水平分割器
        h_splitter = QSplitter(Qt.Horizontal)
        
        # 创建预览窗口
        self.main_preview_window = MultiStagePreviewWidget()
        h_splitter.addWidget(self.main_preview_window)
        
        # 创建垂直分割器
        v_splitter = QSplitter(Qt.Vertical)
        
        # 创建控制面板
        self.control_panel = ControlPanel(self.controller, self)
        v_splitter.addWidget(self.control_panel)
        
        # 创建结果面板
        self.result_panel = ResultPanel()
        v_splitter.addWidget(self.result_panel)
        
        # 添加垂直分割器到水平分割器
        h_splitter.addWidget(v_splitter)
        
        # 设置分割器的初始大小比例
        h_splitter.setSizes([700, 300])
        v_splitter.setSizes([300, 300])
        
        # 添加水平分割器到主布局
        main_layout.addWidget(h_splitter)
        
        # 连接信号
        self._connect_signals()
        
        # 应用样式到整个应用程序
        style_manager.apply_style_to_application()
        
    def _create_menu_bar(self):
        """创建菜单栏。"""
        # 创建文件菜单
        file_menu = self.menuBar().addMenu("文件")
        
        # 添加打开图像动作
        open_action = QAction("打开图像", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_menu_open_image)
        file_menu.addAction(open_action)
        
        # 添加保存结果动作
        save_action = QAction("保存结果", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_results)
        file_menu.addAction(save_action)
        
        # 添加分隔线
        file_menu.addSeparator()
        
        # 添加退出动作
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 创建帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        # 添加关于动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _connect_signals(self):
        """连接组件信号。"""
        # --- 控制面板信号 ---
        # 图像与分析
        self.control_panel.image_load_requested.connect(self._on_load_image)
        self.control_panel.analysis_requested.connect(self._on_start_analysis)
        self.control_panel.measure_tool_clicked.connect(self._on_measure_tool)
        self.control_panel.analyzer_changed.connect(self._on_analyzer_changed)

        # 参数管理
        self.control_panel.import_parameters_requested.connect(self._handle_import_parameters)
        self.control_panel.export_parameters_requested.connect(self._handle_export_parameters)
        
        # --- 控制器信号 ---
        self.controller.analysis_complete.connect(self._on_analysis_complete)
        self.controller.preview_state_changed.connect(self._on_preview_updated)
        self.controller.error_occurred.connect(self._on_error_occurred)

    def _on_menu_open_image(self):
        """菜单栏打开图像处理函数。"""
        # 复用加载逻辑
        self._on_load_image()

    def _on_load_image(self):
        """响应加载图像请求，打开文件对话框，并处理图像加载。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择一张岩心图像", "", "Image Files (*.png *.jpg *.bmp *.jpeg)"
        )
        if not file_path:
            return

        self.statusBar().showMessage(f"正在加载图像: {file_path}...")
        
        # 使用控制器加载图像
        success, message = self.controller.load_image_from_file(file_path)
        
        if success:
            # 状态栏更新
            self.statusBar().showMessage(message)
            
            # 更新结果面板显示DPI信息
            dpi = self.controller.get_current_dpi()
            self.result_panel.update_dpi_info(dpi)
            
            # 加载成功后，立即在预览窗口中显示原始图像
            original_image = self.controller.get_current_image()
            if original_image is not None:
                self.main_preview_window.show_image(original_image)
                # 同时触发结果对话框的创建和显示
                self._on_analyzer_changed()

            print(f"图像已成功加载: {file_path}")
        else:
            # 显示错误消息
            self._on_error_occurred(message)
            self.statusBar().showMessage("加载图像失败")
        
    def _on_save_results(self):
        """保存结果处理函数。"""
        # 这里只是UI演示，实际功能需要与控制器连接
        self.statusBar().showMessage("保存结果...")
        
    def _on_start_analysis(self):
        """开始分析处理函数，直接使用控制器中的参数执行。"""
        if self.controller.get_current_image() is None:
            QMessageBox.warning(self, "操作无效", "请先加载一张图像再开始分析。")
            return

        self.statusBar().showMessage("正在执行裂缝分析...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # 直接调用控制器的分析方法，无需传递参数
        self.controller.run_full_analysis()
        
        QApplication.restoreOverrideCursor()
        
    def _handle_import_parameters(self):
        """处理导入参数的请求。"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入参数文件", "", "JSON Files (*.json)"
        )
        if filepath:
            self.controller.load_parameters(filepath)
            self.statusBar().showMessage(f"已从 {filepath} 加载参数。")

    def _handle_export_parameters(self):
        """处理导出参数的请求。"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出参数文件", "", "JSON Files (*.json)"
        )
        if filepath:
            self.controller.save_parameters(filepath)
            self.statusBar().showMessage(f"参数已保存至 {filepath}。")

    def _on_analysis_complete(self, results: dict):
        """分析完成处理函数。
        
        Args:
            results (dict): 分析结果字典。
        """
        self.statusBar().showMessage("分析完成")
        
        # 将量化结果分发给结果面板
        self.result_panel.update_analysis_results(results)

        # 将完整结果（包括预览图和最终图像）分发给工作台
        if self.current_result_dialog:
            self.current_result_dialog.update_content({
                'state': PreviewState.READY,
                'payload': results
            })
        
    def _on_error_occurred(self, message: str):
        """错误发生处理函数。"""
        # 恢复光标，以防错误发生在耗时操作期间
        QApplication.restoreOverrideCursor()
        
        # 使用QMessageBox显示错误信息
        QMessageBox.critical(self, "发生错误", message)
        self.statusBar().showMessage("处理失败")

    def _on_measure_tool(self):
        """启动手动测量工具。"""
        # 这里只是UI演示，实际功能需要与控制器连接
        dialog = MeasurementDialog(self)
        dialog.exec_()
        
    def _show_about(self):
        """显示关于对话框。"""
        QMessageBox.about(
            self,
            "关于岩石裂缝分析系统",
            "版本 1.0\n\n"
            "一个用于自动分析岩心图像裂缝的桌面应用。\n"
            "基于 PyQt5 和 OpenCV 构建。"
        )

    def _on_analyzer_changed(self):
        """处理分析器切换的槽函数。"""
        # 清空旧的预览和结果
        print("[DEBUG MainWindow] Analyzer changed, clearing old results.")
        self.main_preview_window.clear()
        self.result_panel.clear_results()
        
        # 如果有图像，则显示原图
        original_image = self.controller.get_current_image()
        if original_image is not None:
            self.main_preview_window.show_image(original_image)

        # 根据当前分析器创建新的结果对话框
        analyzer_id = self.controller.get_current_analyzer_id()
        print(f"[DEBUG MainWindow] Current analyzer ID: {analyzer_id}")
        if analyzer_id in self.result_dialog_classes:
            # 如果已存在一个对话框，先关闭并删除
            if self.current_result_dialog:
                print("[DEBUG MainWindow] Closing existing result dialog.")
                self.current_result_dialog.close()
                self.current_result_dialog.deleteLater()

            dialog_class = self.result_dialog_classes[analyzer_id]
            print(f"[DEBUG MainWindow] Creating new result dialog: {dialog_class.__name__}")
            self.current_result_dialog = dialog_class(self.controller, self)
            self.current_result_dialog.show()
        
    def _on_preview_updated(self, payload: dict):
        """处理实时预览更新的槽函数。"""
        print(f"[DEBUG MainWindow] Received preview_state_changed signal. Payload state: {payload.get('state')}")
        if self.current_result_dialog:
            print("[DEBUG MainWindow] Forwarding payload to current result dialog.")
            self.current_result_dialog.update_content(payload)
        
    def closeEvent(self, event):
        """确保在主窗口关闭时，结果对话框也一并关闭。"""
        if self.current_result_dialog:
            self.current_result_dialog.close()
        super().closeEvent(event)