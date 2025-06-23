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

# 导入本地UI组件
from .control_panel import ControlPanel
from .result_panel import ResultPanel
from .preview_window import PreviewWindow
from .analysis_preview_window import AnalysisPreviewWindow
from .measurement_dialog import MeasurementDialog
from .style_manager import style_manager  # 导入样式管理器

# 导入控制器和枚举
from ..core.controller import Controller
from ..core.analysis_stages import AnalysisStage


class MainWindow(QMainWindow):
    """主窗口类，应用程序的主界面。
    
    该类组装了所有UI组件，处理组件间的交互逻辑，
    并提供菜单栏等功能。
    
    Attributes:
        control_panel: 控制面板实例
        result_panel: 结果面板实例
        preview_window: 预览窗口实例
        analysis_preview_window: 分析预览窗口实例
        controller: 应用程序控制器实例
    """
    
    def __init__(self):
        """初始化主窗口。"""
        super().__init__()
        # 创建控制器
        self.controller = Controller()
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
        self.preview_window = PreviewWindow()
        h_splitter.addWidget(self.preview_window)
        
        # 创建分析预览窗口
        self.analysis_preview_window = AnalysisPreviewWindow()
        self.analysis_preview_window.hide() # 默认隐藏
        
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
        
        # 创建视图菜单
        view_menu = self.menuBar().addMenu("视图")
        
        # 添加显示分析预览窗口选项
        show_analysis_preview_action = QAction("显示分析预览窗口", self)
        show_analysis_preview_action.setCheckable(True)
        show_analysis_preview_action.setChecked(False)
        show_analysis_preview_action.triggered.connect(self._toggle_analysis_preview)
        view_menu.addAction(show_analysis_preview_action)
        
        # 创建帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        # 添加关于动作
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _connect_signals(self):
        """连接组件信号。"""
        # 连接控制面板信号
        self.control_panel.loadImageClicked.connect(self._on_load_image)
        self.control_panel.startAnalysisClicked.connect(self._on_start_analysis)
        self.control_panel.measureToolClicked.connect(self._on_measure_tool)
        self.control_panel.import_parameters_requested.connect(self._handle_import_parameters)
        self.control_panel.export_parameters_requested.connect(self._handle_export_parameters)
        
        # 连接控制器信号
        self.controller.analysis_complete.connect(self._on_analysis_complete)
        self.controller.preview_stage_updated.connect(self._on_preview_stage_updated)
        self.controller.error_occurred.connect(self._on_error_occurred)
        
    def _on_menu_open_image(self):
        """菜单栏打开图像处理函数。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像文件",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
        )
        
        if file_path:
            self._on_load_image(file_path)
        
    def _on_load_image(self, file_path):
        """加载图像处理函数。
        
        Args:
            file_path (str): 图像文件的路径。
        """
        self.statusBar().showMessage(f"正在加载图像: {file_path}...")
        
        # 使用控制器加载图像
        success, message = self.controller.load_image_from_file(file_path)
        
        if success:
            # 获取加载的图像和DPI信息
            image = self.controller.get_current_image()
            dpi = self.controller.get_current_dpi()
            
            # 在预览窗口显示图像
            self.preview_window.display_image(image)
            
            # 更新状态栏
            self.statusBar().showMessage(message)
            
            # 更新结果面板显示DPI信息
            self.result_panel.update_dpi_info(dpi)
            
            # 清除分析预览窗口，后续更新由信号驱动
            self.analysis_preview_window.clear_all()
            
            print(f"图像已成功加载: {file_path}")
        else:
            # 显示错误消息
            QMessageBox.warning(self, "加载错误", message)
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
        self.controller.run_fracture_analysis()
        
        QApplication.restoreOverrideCursor()
        
    def _handle_import_parameters(self):
        """处理导入参数请求。"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入参数文件", "", "JSON Files (*.json)"
        )
        if filepath:
            self.controller.load_parameters(filepath)
            self.statusBar().showMessage(f"已从 {filepath} 加载参数。")

    def _handle_export_parameters(self):
        """处理导出参数请求。"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出参数文件", "analysis_params.json", "JSON Files (*.json)"
        )
        if filepath:
            self.controller.save_parameters(filepath)
            self.statusBar().showMessage(f"参数已保存至 {filepath}。")

    def _on_analysis_complete(self, results: dict):
        """分析完成处理函数。
        
        Args:
            results (dict): 分析结果，包括裂缝数量、总面积、总长度等。
        """
        self.statusBar().showMessage("裂缝分析完成。")
        self.result_panel.update_analysis_results(results)

    def _on_preview_stage_updated(self, stage: AnalysisStage, result_data: dict):
        """预览阶段更新处理函数。
        
        Args:
            stage (AnalysisStage): 当前分析阶段。
            result_data (dict): 包含图像或数据的字典。
        """
        # 1. 更新多阶段预览窗口
        # 特殊处理：当是MEASUREMENT阶段时，我们希望显示最终的DETECTION图像
        if stage == AnalysisStage.MEASUREMENT:
            # 从控制器获取DETECTION阶段的结果，里面包含图像
            detection_result = self.controller.analysis_results.get(AnalysisStage.DETECTION, {})
            display_image = detection_result.get("image")
            
            # 创建一个新的字典，合并DETECTION图像和MEASUREMENT的统计数据
            combined_data = result_data.copy()
            if display_image is not None:
                combined_data['image'] = display_image
            
            self.analysis_preview_window.update_stage_preview(stage, combined_data)
        else:
            # 对于其他所有阶段，直接传递收到的结果字典
            self.analysis_preview_window.update_stage_preview(stage, result_data)

        # 2. 如果是最终检测阶段，也更新主预览窗口
        image = result_data.get("image")
        if stage == AnalysisStage.DETECTION and image is not None:
            self.preview_window.update_image(image)
        
    def _on_error_occurred(self, message: str):
        """错误处理函数。"""
        QMessageBox.warning(self, "错误", message)
        self.statusBar().showMessage(f"操作失败: {message}", 5000)

    def _on_measure_tool(self):
        """测量工具处理函数。"""
        self.statusBar().showMessage("测量工具（待实现）")
        
    def _toggle_analysis_preview(self, checked):
        """切换分析预览窗口的可见性。"""
        if checked:
            self.analysis_preview_window.show()
        else:
            self.analysis_preview_window.hide()
            
    def _update_all_analysis_previews(self):
        """使用控制器中的所有当前结果刷新分析预览窗口。"""
        all_results = self.controller.get_all_analysis_results()
        self.analysis_preview_window.clear_all()
        for stage, result_data in all_results.items():
            if result_data:
                self.analysis_preview_window.update_stage_preview(stage, result_data)

    def _show_about(self):
        """显示关于对话框。"""
        QMessageBox.about(self, "关于", "岩石裂缝分析系统 v1.0\n\n一个用于岩心图像裂缝分析的桌面工具。") 