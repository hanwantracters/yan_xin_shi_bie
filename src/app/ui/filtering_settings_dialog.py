"""裂缝过滤与合并参数设置对话框。

提供一个独立的窗口，用于调整所有与最终裂缝筛选相关的参数。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal as Signal, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QDoubleSpinBox,
    QCheckBox
)

from src.app.core.controller import Controller

class FilteringSettingsDialog(QDialog):
    """用于设置过滤与合并参数的对话框。"""
    
    parameter_changed = Signal(str, object)

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None):
        """初始化对话框。

        Args:
            controller (Controller): 应用程序控制器实例。
            parent (Optional[QWidget]): 父窗口对象。
        """
        super().__init__(parent)
        self.controller = controller
        
        self.setWindowTitle("调整过滤与合并参数")
        self.setMinimumWidth(300)
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)
        group_box = QGroupBox("裂缝过滤与合并")
        layout = QFormLayout(group_box)

        min_len_spinbox = QDoubleSpinBox(objectName="filtering.min_length_mm")
        min_len_spinbox.setRange(0, 1000); min_len_spinbox.setDecimals(2); min_len_spinbox.setSingleStep(0.1)
        
        min_ar_spinbox = QDoubleSpinBox(objectName="filtering.min_aspect_ratio")
        min_ar_spinbox.setRange(1, 100); min_ar_spinbox.setDecimals(1); min_ar_spinbox.setSingleStep(0.5)
        
        merge_checkbox = QCheckBox("启用轮廓智能合并", objectName="merging.enabled")
        
        merge_dist_spinbox = QDoubleSpinBox(objectName="merging.merge_distance_mm")
        merge_dist_spinbox.setRange(0, 100); merge_dist_spinbox.setDecimals(2)
        merge_dist_spinbox.setEnabled(False) # 初始禁用
        
        merge_angle_spinbox = QDoubleSpinBox(objectName="merging.max_angle_diff")
        merge_angle_spinbox.setRange(0, 90); merge_angle_spinbox.setDecimals(1)
        merge_angle_spinbox.setEnabled(False) # 初始禁用
        
        merge_checkbox.toggled.connect(merge_dist_spinbox.setEnabled)
        merge_checkbox.toggled.connect(merge_angle_spinbox.setEnabled)

        layout.addRow("最小长度 (mm):", min_len_spinbox)
        layout.addRow("最小长宽比:", min_ar_spinbox)
        layout.addRow(merge_checkbox)
        layout.addRow("合并距离 (mm):", merge_dist_spinbox)
        layout.addRow("最大角度差 (度):", merge_angle_spinbox)
        
        main_layout.addWidget(group_box)

    def _connect_signals(self):
        """连接所有参数控件的信号。"""
        all_widgets = self.findChildren((QDoubleSpinBox, QCheckBox))
        for widget in all_widgets:
            if isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self._on_parameter_changed)
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(self._on_parameter_changed)

    def _on_parameter_changed(self, value):
        """当参数变化时，通知控制器。"""
        sender = self.sender()
        if not (sender and sender.objectName()): return

        param_path = sender.objectName()
        
        if value is not None:
            self.parameter_changed.emit(param_path, value)

    def update_controls(self, params: dict):
        """根据给定的参数字典更新所有UI控件的值。"""
        p_filter = params.get('filtering', {})
        p_merge = params.get('merging', {})
        if not (p_filter and p_merge): return

        all_widgets = self.findChildren((QDoubleSpinBox, QCheckBox))
        for widget in all_widgets: widget.blockSignals(True)

        try:
            self.findChild(QDoubleSpinBox, "filtering.min_length_mm").setValue(p_filter.get('min_length_mm', 5.0))
            self.findChild(QDoubleSpinBox, "filtering.min_aspect_ratio").setValue(p_filter.get('min_aspect_ratio', 3.0))
            self.findChild(QCheckBox, "merging.enabled").setChecked(p_merge.get('enabled', False))
            self.findChild(QDoubleSpinBox, "merging.merge_distance_mm").setValue(p_merge.get('merge_distance_mm', 2.0))
            self.findChild(QDoubleSpinBox, "merging.max_angle_diff").setValue(p_merge.get('max_angle_diff', 15.0))
        finally:
            for widget in all_widgets: widget.blockSignals(False) 