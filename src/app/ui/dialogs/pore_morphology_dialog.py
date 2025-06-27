"""孔洞分析的形态学参数设置对话框。

此对话框专为孔洞分析(分水岭)模式定制，提供调整
开运算和背景膨胀等参数的接口。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal as Signal, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox
)

from src.app.core.controller import Controller
from src.app.utils.constants import StageKeys


class PoreMorphologyDialog(QDialog):
    """用于设置孔洞分水岭算法形态学参数的对话框。"""
    
    parameter_changed = Signal(str, object)
    realtime_preview_requested = Signal(str)

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.controller = controller
        
        self.setWindowTitle("调整分水岭参数")
        self.setMinimumWidth(300)
        
        self._init_ui()
        self._connect_signals()
        self._init_preview_timer()

    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)
        group_box = QGroupBox("分水岭形态学处理")
        layout = QFormLayout(group_box)

        # 这些控件的objectName必须与PoreAnalyzer期望的参数键匹配
        self.opening_ksize_spinbox = QSpinBox(objectName="morphology.opening_ksize")
        self.opening_ksize_spinbox.setRange(1, 31); self.opening_ksize_spinbox.setSingleStep(2)
        
        self.opening_iter_spinbox = QSpinBox(objectName="morphology.opening_iterations")
        self.opening_iter_spinbox.setRange(1, 10)
        
        self.sure_bg_ksize_spinbox = QSpinBox(objectName="morphology.sure_bg_ksize")
        self.sure_bg_ksize_spinbox.setRange(1, 31); self.sure_bg_ksize_spinbox.setSingleStep(2)
        
        self.dist_ratio_spinbox = QDoubleSpinBox(objectName="morphology.distance_transform_threshold_ratio")
        self.dist_ratio_spinbox.setRange(0.0, 1.0); self.dist_ratio_spinbox.setSingleStep(0.05)
        self.dist_ratio_spinbox.setDecimals(2)

        layout.addRow("前景开运算 - 核大小:", self.opening_ksize_spinbox)
        layout.addRow("前景开运算 - 迭代:", self.opening_iter_spinbox)
        layout.addRow("背景膨胀 - 核大小:", self.sure_bg_ksize_spinbox)
        layout.addRow("前景识别比例:", self.dist_ratio_spinbox)
        
        main_layout.addWidget(group_box)

    def _init_preview_timer(self):
        """初始化用于延迟实时预览的计时器。"""
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._request_morph_preview)

    def _connect_signals(self):
        """连接所有参数控件的信号。"""
        for spinbox in self.findChildren((QSpinBox, QDoubleSpinBox)):
            spinbox.valueChanged.connect(self._on_parameter_changed)

    def _on_parameter_changed(self, value: int):
        """当参数变化时，通知控制器。"""
        sender = self.sender()
        if not (sender and sender.objectName()): return

        param_path = sender.objectName()
        self.parameter_changed.emit(param_path, value)

        current_params = self.controller.get_current_parameters()
        param_group = param_path.split('.')[0] # 'morphology'
        
        hints = current_params.get(param_group, {}).get('ui_hints', {})
        if hints.get('realtime', False):
            self.preview_timer.stop()
            self.preview_timer.start(500)

    def _request_morph_preview(self):
        """发射一个请求预览的信号。"""
        # 对于孔洞分析，形态学预览和二值化预览效果相同
        self.realtime_preview_requested.emit(StageKeys.MORPH.value)

    def update_controls(self, params: dict):
        """根据给定的参数字典更新所有UI控件的值。"""
        p = params.get('morphology', {})
        if not p: return

        for spinbox in self.findChildren(QSpinBox):
            spinbox.blockSignals(True)
        try:
            self.opening_ksize_spinbox.setValue(p.get('opening_ksize', 3))
            self.opening_iter_spinbox.setValue(p.get('opening_iterations', 2))
            self.sure_bg_ksize_spinbox.setValue(p.get('sure_bg_ksize', 3))
            self.dist_ratio_spinbox.setValue(p.get('distance_transform_threshold_ratio', 0.6))
        finally:
            for spinbox in self.findChildren(QSpinBox):
                spinbox.blockSignals(False) 