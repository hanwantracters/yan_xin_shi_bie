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
from .analysis_wizard import AnalysisWizard

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
        self.control_panel = ControlPanel()
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
        self.control_panel.thresholdChanged.connect(self._on_threshold_changed)
        self.control_panel.thresholdMethodChanged.connect(self._on_threshold_method_changed)
        self.control_panel.adaptiveParamsChanged.connect(self._on_adaptive_params_changed)
        self.control_panel.morphologyParamsChanged.connect(self._on_morphology_params_changed)
        
        # 连接控制器信号
        self.controller.analysis_complete.connect(self._on_analysis_complete)
        
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
            
            # 清除并更新分析预览窗口
            self.analysis_preview_window.clear_all()
            self._update_analysis_preview()
            
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
        """开始分析处理函数，启动分析向导。"""
        if self.controller.get_current_image() is None:
            QMessageBox.warning(self, "操作无效", "请先加载一张图像再开始分析。")
            return

        wizard = AnalysisWizard(self)
        if wizard.exec_() == QDialog.Accepted:
            params = wizard.get_parameters()
            self.statusBar().showMessage("正在执行裂缝分析...")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            self.controller.run_fracture_analysis(params['min_aspect_ratio'])
            
            QApplication.restoreOverrideCursor()

    def _on_analysis_complete(self, results: dict):
        """分析完成后的处理函数。"""
        self.statusBar().showMessage("裂缝分析完成。", 5000)
        
        # 更新结果面板
        measurement_result = results.get(AnalysisStage.MEASUREMENT)
        if measurement_result:
            self.result_panel.update_analysis_results(measurement_result)
            
        # 更新预览窗口为最终的可视化结果
        detection_result = results.get(AnalysisStage.DETECTION)
        if detection_result and 'image' in detection_result:
            self.preview_window.display_image(detection_result['image'])
        
        # 更新多阶段分析预览窗口
        self._update_analysis_preview()
        
    def _on_measure_tool(self):
        """测量工具处理函数。"""
        # 这里只是UI演示，创建一个测量对话框
        dialog = MeasurementDialog(100.0, 96.0, 26.46, self)
        dialog.exec_()
        
    def _on_threshold_changed(self, value):
        """阈值变化处理函数。"""
        self.controller.set_threshold_value(value)
        self._update_analysis_preview()
        
    def _on_threshold_method_changed(self, method):
        """阈值方法变化处理函数。"""
        self.controller.set_threshold_method(method)
        self._update_analysis_preview()

    def _on_adaptive_params_changed(self, params):
        """自适应阈值参数变化处理函数。"""
        self.controller.set_adaptive_params(params)
        self._update_analysis_preview()

    def _on_morphology_params_changed(self, params):
        """形态学参数变化处理函数。"""
        self.controller.set_morphology_params(params)
        self._update_analysis_preview()

    def _toggle_analysis_preview(self, checked):
        """切换分析预览窗口的显示和隐藏。"""
        if checked:
            self.analysis_preview_window.show()
            self._update_analysis_preview() # 打开时立即更新一次
        else:
            self.analysis_preview_window.hide()

    def _update_analysis_preview(self):
        """更新分析预览窗口的内容。"""
        if not self.analysis_preview_window.isVisible() or self.controller.get_current_image() is None:
            return

        # 1. 原始图像
        original_result = self.controller.get_analysis_result(AnalysisStage.ORIGINAL)
        if original_result:
            self.analysis_preview_window.update_stage(
                AnalysisStage.ORIGINAL,
                original_result.get('image'),
                {
                    'Path': original_result.get('path', 'N/A'),
                    'DPI': str(original_result.get('dpi', 'N/A'))
                }
            )

        # 2. 灰度图像
        grayscale_result = self.controller.get_analysis_result(AnalysisStage.GRAYSCALE)
        if grayscale_result:
            self.analysis_preview_window.update_stage(
                AnalysisStage.GRAYSCALE,
                grayscale_result.get('image'),
                {'Method': grayscale_result.get('method', 'standard')}
            )

        # 3. 阈值分割
        threshold_result = self.controller.apply_threshold_segmentation()
        if threshold_result:
            self.analysis_preview_window.update_stage(
                AnalysisStage.THRESHOLD,
                threshold_result.get('binary'),
                {
                    'Method': threshold_result.get('method', 'N/A'),
                    'Threshold': threshold_result.get('threshold', 'N/A'),
                    'Params': str(threshold_result.get('params', {}))
                }
            )
        
        # 4. 形态学处理
        morphology_result = self.controller.apply_morphological_processing()
        if morphology_result:
            self.analysis_preview_window.update_stage(
                AnalysisStage.MORPHOLOGY,
                morphology_result.get('image'),
                {
                    'Kernel Shape': morphology_result.get('kernel_shape', 'N/A'),
                    'Kernel Size': str(morphology_result.get('kernel_size', 'N/A')),
                    'Iterations': morphology_result.get('iterations', 'N/A')
                }
            )

        # 5. 裂缝检测 (新增)
        detection_result = self.controller.get_analysis_result(AnalysisStage.DETECTION)
        if detection_result:
            self.analysis_preview_window.update_stage(
                AnalysisStage.DETECTION,
                detection_result.get('image'),
                {
                    'Fracture Count': detection_result.get('fracture_count', 'N/A'),
                }
            )

    def _show_about(self):
        """显示关于对话框。"""
        QMessageBox.about(
            self, 
            "关于", 
            "岩石裂缝分析系统\n\n版本: 1.0.0\n\n用于分析岩石裂缝的图像处理软件"
        ) 