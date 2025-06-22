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
    QLabel
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

# 导入本地UI组件
from .control_panel import ControlPanel
from .result_panel import ResultPanel
from .preview_window import PreviewWindow
from .measurement_dialog import MeasurementDialog


class MainWindow(QMainWindow):
    """主窗口类，应用程序的主界面。
    
    该类组装了所有UI组件，处理组件间的交互逻辑，
    并提供菜单栏等功能。
    
    Attributes:
        control_panel: 控制面板实例
        result_panel: 结果面板实例
        preview_window: 预览窗口实例
    """
    
    def __init__(self):
        """初始化主窗口。"""
        super().__init__()
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
        
    def _create_menu_bar(self):
        """创建菜单栏。"""
        # 创建文件菜单
        file_menu = self.menuBar().addMenu("文件")
        
        # 添加打开图像动作
        open_action = QAction("打开图像", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_image)
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
        # 连接控制面板信号
        self.control_panel.loadImageClicked.connect(self._on_open_image)
        self.control_panel.startAnalysisClicked.connect(self._on_start_analysis)
        self.control_panel.measureToolClicked.connect(self._on_measure_tool)
        self.control_panel.thresholdChanged.connect(self._on_threshold_changed)
        
    def _on_open_image(self):
        """打开图像处理函数。"""
        # 这里只是UI演示，实际功能需要与控制器连接
        self.statusBar().showMessage("打开图像...")
        
    def _on_save_results(self):
        """保存结果处理函数。"""
        # 这里只是UI演示，实际功能需要与控制器连接
        self.statusBar().showMessage("保存结果...")
        
    def _on_start_analysis(self):
        """开始分析处理函数。"""
        # 这里只是UI演示，实际功能需要与控制器连接
        self.statusBar().showMessage("开始分析...")
        
    def _on_measure_tool(self):
        """测量工具处理函数。"""
        # 这里只是UI演示，创建一个测量对话框
        dialog = MeasurementDialog(100.0, 96.0, 26.46, self)
        dialog.exec_()
        
    def _on_threshold_changed(self, value):
        """阈值变化处理函数。"""
        # 这里只是UI演示，实际功能需要与控制器连接
        self.statusBar().showMessage(f"阈值已调整为: {value}")
        
    def _show_about(self):
        """显示关于对话框。"""
        QMessageBox.about(
            self, 
            "关于", 
            "岩石裂缝分析系统\n\n版本: 1.0.0\n\n用于分析岩石裂缝的图像处理软件"
        ) 