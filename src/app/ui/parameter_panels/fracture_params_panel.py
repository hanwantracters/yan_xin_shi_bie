"""裂缝分析模式的参数设置面板。

该模块定义了`FractureParamsPanel`类，它是一个QWidget，
包含了用于调整裂缝分析所有相关参数（二值化、形态学、过滤）的按钮。
这些按钮会打开相应的参数设置对话框。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox

from ...core.controller import Controller
from ..threshold_settings_dialog import ThresholdSettingsDialog
from ..morphology_settings_dialog import MorphologySettingsDialog
from ..filtering_settings_dialog import FilteringSettingsDialog

class FractureParamsPanel(QWidget):
    """
    为裂缝分析提供参数调整入口的UI面板。
    """
    parameter_changed = Signal(str, object)

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.controller = controller

        # 对话框实例
        self.threshold_dialog: Optional[ThresholdSettingsDialog] = None
        self.morphology_dialog: Optional[MorphologySettingsDialog] = None
        self.filtering_dialog: Optional[FilteringSettingsDialog] = None

        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """初始化UI组件。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("裂缝参数调整")
        group_layout = QVBoxLayout(group)
        
        self.threshold_btn = QPushButton("二值化参数...")
        self.morphology_btn = QPushButton("形态学参数...")
        self.filtering_btn = QPushButton("过滤与合并参数...")
        
        group_layout.addWidget(self.threshold_btn)
        group_layout.addWidget(self.morphology_btn)
        group_layout.addWidget(self.filtering_btn)
        
        layout.addWidget(group)
        self.setLayout(layout)

    def _connect_signals(self):
        """连接所有UI控件的信号。"""
        self.threshold_btn.clicked.connect(self._open_threshold_dialog)
        self.morphology_btn.clicked.connect(self._open_morphology_dialog)
        self.filtering_btn.clicked.connect(self._open_filtering_dialog)
        
    def on_parameters_updated(self, params: dict):
        """当控制器中的参数更新时，更新所有已打开的对话框。"""
        if self.threshold_dialog:
            self.threshold_dialog.update_controls(params)
        if self.morphology_dialog:
            self.morphology_dialog.update_controls(params)
        if self.filtering_dialog:
            self.filtering_dialog.update_controls(params)

    def _open_threshold_dialog(self):
        """打开二值化参数设置对话框。"""
        if self.threshold_dialog is None:
            self.threshold_dialog = ThresholdSettingsDialog(self)
            self.threshold_dialog.parameter_changed.connect(self.parameter_changed)
            # 连接控制器信号，以便在参数从外部（如加载文件）更新时，对话框能同步更新
            self.controller.parameters_updated.connect(self.threshold_dialog.update_controls)

        # 每次打开时都确保它显示的是最新的参数
        self.threshold_dialog.update_controls(self.controller.get_current_parameters())
        self.threshold_dialog.show()
        self.threshold_dialog.activateWindow()
        
    def _open_morphology_dialog(self):
        """打开形态学参数设置对话框。"""
        if self.morphology_dialog is None:
            self.morphology_dialog = MorphologySettingsDialog(self)
            self.morphology_dialog.parameter_changed.connect(self.parameter_changed)
            self.controller.parameters_updated.connect(self.morphology_dialog.update_controls)

        self.morphology_dialog.update_controls(self.controller.get_current_parameters())
        self.morphology_dialog.show()
        self.morphology_dialog.activateWindow()

    def _open_filtering_dialog(self):
        """打开过滤与合并参数设置对话框。"""
        if self.filtering_dialog is None:
            self.filtering_dialog = FilteringSettingsDialog(self)
            self.filtering_dialog.parameter_changed.connect(self.parameter_changed)
            self.controller.parameters_updated.connect(self.filtering_dialog.update_controls)
            
        self.filtering_dialog.update_controls(self.controller.get_current_parameters())
        self.filtering_dialog.show()
        self.filtering_dialog.activateWindow() 