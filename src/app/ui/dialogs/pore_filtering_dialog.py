"""孔洞过滤参数设置对话框。

提供一个独立的窗口，用于调整所有与孔洞过滤相关的参数。
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QFormLayout, QSlider, QLabel, QDoubleSpinBox
)

from src.app.core.controller import Controller

class PoreFilteringSettingsDialog(QDialog):
    """用于设置孔洞过滤参数的对话框。"""
    
    parameter_changed = Signal(str, object)
    realtime_preview_requested = Signal()

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.controller = controller
        
        self.setWindowTitle("调整孔洞过滤参数")
        self.setMinimumWidth(350)
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI组件。"""
        layout = QFormLayout(self)

        # Solidity Slider
        self.solidity_slider = QSlider(Qt.Horizontal, objectName="filtering.min_solidity")
        self.solidity_slider.setRange(0, 100) # Representing 0.0 to 1.0
        self.solidity_label = QLabel()
        self.solidity_slider.valueChanged.connect(lambda v: self.solidity_label.setText(f"{v/100:.2f}"))
        layout.addRow("最小坚实度 (Min Solidity):", self.solidity_slider)
        layout.addRow("当前值:", self.solidity_label)
        
        # Area Slider
        self.area_slider = QSlider(Qt.Horizontal, objectName="filtering.min_area_pixels")
        self.area_slider.setRange(0, 500)
        self.area_label = QLabel()
        self.area_slider.valueChanged.connect(self.area_label.setNum)
        layout.addRow("最小面积 (像素):", self.area_slider)
        layout.addRow("当前值:", self.area_label)

    def _connect_signals(self):
        """连接信号。"""
        self.solidity_slider.sliderReleased.connect(self._on_parameter_changed)
        self.area_slider.sliderReleased.connect(self._on_parameter_changed)

    def _on_parameter_changed(self):
        """当参数变化时发射信号。"""
        sender = self.sender()
        if not (sender and sender.objectName()): return

        param_path = sender.objectName()
        
        if param_path == "filtering.min_solidity":
            value = sender.value() / 100.0
        else:
            value = sender.value()
        
        self.parameter_changed.emit(param_path, value)

        current_params = self.controller.get_current_parameters()
        param_group = param_path.split('.')[0] # 'filtering'
        
        hints = current_params.get(param_group, {}).get('ui_hints', {})
        if hints.get('realtime', False):
            self.realtime_preview_requested.emit()

    def update_controls(self, params: dict):
        """用给定的参数更新UI控件。"""
        p = params.get('filtering', {})
        if not p: return
        
        self.solidity_slider.blockSignals(True)
        self.area_slider.blockSignals(True)
        
        self.solidity_slider.setValue(int(p.get('min_solidity', 0.85) * 100))
        self.area_slider.setValue(p.get('min_area_pixels', 20))
        
        self.solidity_slider.blockSignals(False)
        self.area_slider.blockSignals(False)

        # Manually update labels
        self.solidity_label.setText(f"{self.solidity_slider.value()/100:.2f}")
        self.area_label.setNum(self.area_slider.value()) 