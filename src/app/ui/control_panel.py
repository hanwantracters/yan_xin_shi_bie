"""控制面板组件，包含图像处理和分析的控制按钮和参数调节。

该模块提供了应用程序的主要控制界面，用户可以通过此面板加载图像、
开始分析和调整处理参数。遵循 Google 风格的 Docstrings 和类型提示。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QFormLayout
)

from ..core.controller import Controller
from .threshold_settings_dialog import ThresholdSettingsDialog
from .morphology_settings_dialog import MorphologySettingsDialog
from .filtering_settings_dialog import FilteringSettingsDialog


class ControlPanel(QWidget):
    """控制面板类，提供用户交互控制界面。

    该类包含加载图像、开始分析和测量等按钮，以及所有分析参数的调节控件。
    通过信号机制与主窗口进行通信。

    Attributes:
        loadImageClicked (pyqtSignal): 加载图像按钮点击时发出，携带文件路径字符串。
        startAnalysisClicked (pyqtSignal): 开始分析按钮点击时发出。
        measureToolClicked (pyqtSignal): 测量工具按钮点击时发出。
        import_parameters_requested (pyqtSignal): 请求导入参数时发出。
        export_parameters_requested (pyqtSignal): 请求导出参数时发出。
    """

    # 定义信号
    loadImageClicked = pyqtSignal(str)
    startAnalysisClicked = pyqtSignal()
    measureToolClicked = pyqtSignal()
    import_parameters_requested = pyqtSignal()
    export_parameters_requested = pyqtSignal()

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None) -> None:
        """初始化控制面板。

        Args:
            controller (Controller): 应用程序控制器实例。
            parent (Optional[QWidget]): 父窗口对象。默认为 None。
        """
        super().__init__(parent)
        self.controller = controller
        
        # 对话框实例
        self.threshold_dialog: Optional[ThresholdSettingsDialog] = None
        self.morphology_dialog: Optional[MorphologySettingsDialog] = None
        self.filtering_dialog: Optional[FilteringSettingsDialog] = None
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """初始化UI组件和布局。"""
        self.load_image_btn = QPushButton("加载图像")
        self.start_analysis_btn = QPushButton("一键执行分析")
        self.measure_btn = QPushButton("手动测量")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_image_btn)
        main_layout.addWidget(self.start_analysis_btn)
        main_layout.addWidget(self.measure_btn)
        main_layout.addWidget(self._create_parameter_management_group())
        main_layout.addWidget(self._create_parameter_adjustment_group())
        main_layout.addStretch(1)

        self.setLayout(main_layout)

    def _create_parameter_management_group(self) -> QGroupBox:
        """创建参数导入/导出组。"""
        group = QGroupBox("参数管理")
        layout = QHBoxLayout(group)
        self.import_btn = QPushButton("导入参数")
        self.export_btn = QPushButton("导出参数")
        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)
        return group

    def _create_parameter_adjustment_group(self) -> QGroupBox:
        """创建用于打开参数调整对话框的按钮组。"""
        group = QGroupBox("参数调整")
        layout = QVBoxLayout(group)
        
        self.threshold_btn = QPushButton("二值化参数...")
        self.morphology_btn = QPushButton("形态学参数...")
        self.filtering_btn = QPushButton("过滤与合并参数...")
        
        layout.addWidget(self.threshold_btn)
        layout.addWidget(self.morphology_btn)
        layout.addWidget(self.filtering_btn)
        
        return group

    def _connect_signals(self):
        """连接所有UI控件的信号。"""
        # 主功能按钮
        self.load_image_btn.clicked.connect(self._on_load_image_clicked)
        self.start_analysis_btn.clicked.connect(self.startAnalysisClicked)
        self.measure_btn.clicked.connect(self.measureToolClicked)
        
        # 参数管理
        self.import_btn.clicked.connect(self.import_parameters_requested)
        self.export_btn.clicked.connect(self.export_parameters_requested)
        
        # 参数调整对话框
        self.threshold_btn.clicked.connect(self._open_threshold_dialog)
        self.morphology_btn.clicked.connect(self._open_morphology_dialog)
        self.filtering_btn.clicked.connect(self._open_filtering_dialog)

    def _open_threshold_dialog(self):
        """打开二值化参数设置对话框。"""
        if self.threshold_dialog is None:
            self.threshold_dialog = ThresholdSettingsDialog(self.controller, self)
            self.controller.parameters_updated.connect(self.threshold_dialog.update_controls)
            self.threshold_dialog.update_controls(self.controller.analysis_params)
        self.threshold_dialog.show()
        self.threshold_dialog.activateWindow()
        
    def _open_morphology_dialog(self):
        """打开形态学参数设置对话框。"""
        if self.morphology_dialog is None:
            self.morphology_dialog = MorphologySettingsDialog(self.controller, self)
            self.controller.parameters_updated.connect(self.morphology_dialog.update_controls)
            self.morphology_dialog.update_controls(self.controller.analysis_params)
        self.morphology_dialog.show()
        self.morphology_dialog.activateWindow()

    def _open_filtering_dialog(self):
        """打开过滤与合并参数设置对话框。"""
        if self.filtering_dialog is None:
            self.filtering_dialog = FilteringSettingsDialog(self.controller, self)
            self.controller.parameters_updated.connect(self.filtering_dialog.update_controls)
            self.filtering_dialog.update_controls(self.controller.analysis_params)
        self.filtering_dialog.show()
        self.filtering_dialog.activateWindow()

    def _on_load_image_clicked(self) -> None:
        """打开文件对话框让用户选择图像。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择一张岩心图像", "", "Image Files (*.png *.jpg *.bmp *.jpeg)"
        )
        if file_path:
            self.loadImageClicked.emit(file_path) 