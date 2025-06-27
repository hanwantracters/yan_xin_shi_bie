"""孔洞分析模式的参数设置面板。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QGroupBox

from ...core.controller import Controller
from ..dialogs.pore_filtering_dialog import PoreFilteringSettingsDialog
from ..dialogs.pore_morphology_dialog import PoreMorphologyDialog
# We can reuse threshold and morphology dialogs if their logic is generic enough
from ..threshold_settings_dialog import ThresholdSettingsDialog


class PoreParamsPanel(QWidget):
    """为孔洞分析提供参数调整入口的UI面板。"""
    parameter_changed = Signal(str, object)
    realtime_preview_requested = Signal(str)

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.controller = controller

        self.threshold_dialog: Optional[ThresholdSettingsDialog] = None
        self.morphology_dialog: Optional[PoreMorphologyDialog] = None
        self.filtering_dialog: Optional[PoreFilteringSettingsDialog] = None

        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """初始化UI。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("孔洞参数调整")
        group_layout = QVBoxLayout(group)
        
        self.threshold_btn = QPushButton("二值化参数...")
        self.morphology_btn = QPushButton("形态学与分水岭参数...")
        self.filtering_btn = QPushButton("孔洞过滤参数...")
        
        group_layout.addWidget(self.threshold_btn)
        group_layout.addWidget(self.morphology_btn)
        group_layout.addWidget(self.filtering_btn)
        
        layout.addWidget(group)
        self.setLayout(layout)

    def _connect_signals(self):
        """连接信号。"""
        self.threshold_btn.clicked.connect(self._open_threshold_dialog)
        self.morphology_btn.clicked.connect(self._open_morphology_dialog)
        self.filtering_btn.clicked.connect(self._open_filtering_dialog)

    def on_parameters_updated(self, params: dict):
        """当控制器参数更新时，同步所有对话框。"""
        if self.threshold_dialog:
            self.threshold_dialog.update_controls(params)
        if self.morphology_dialog:
            self.morphology_dialog.update_controls(params)
        if self.filtering_dialog:
            self.filtering_dialog.update_controls(params)

    def _open_threshold_dialog(self):
        if self.threshold_dialog is None:
            self.threshold_dialog = ThresholdSettingsDialog(self.controller, self)
            self.threshold_dialog.parameter_changed.connect(self.parameter_changed)
            self.threshold_dialog.realtime_preview_requested.connect(self.realtime_preview_requested)
        self.threshold_dialog.update_controls(self.controller.get_current_parameters())
        self.threshold_dialog.show()

    def _open_morphology_dialog(self):
        if self.morphology_dialog is None:
            self.morphology_dialog = PoreMorphologyDialog(self.controller, self)
            self.morphology_dialog.parameter_changed.connect(self.parameter_changed)
            self.morphology_dialog.realtime_preview_requested.connect(self.realtime_preview_requested)
        self.morphology_dialog.update_controls(self.controller.get_current_parameters())
        self.morphology_dialog.show()

    def _open_filtering_dialog(self):
        if self.filtering_dialog is None:
            self.filtering_dialog = PoreFilteringSettingsDialog(self.controller, self)
            self.filtering_dialog.parameter_changed.connect(self.parameter_changed)
        self.filtering_dialog.update_controls(self.controller.get_current_parameters())
        self.filtering_dialog.show() 