"""阈值参数设置对话框。

提供一个独立的窗口，用于调整所有与阈值分割相关的参数。
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QStackedWidget,
    QSlider,
    QLabel,
    QDoubleSpinBox
)

from src.app.core.controller import Controller

class ThresholdSettingsDialog(QDialog):
    """用于设置阈值参数的对话框。"""
    
    parameter_changed = Signal(str, object)
    realtime_preview_requested = Signal()

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None):
        """初始化对话框。

        Args:
            controller (Controller): 应用程序控制器实例。
            parent (Optional[QWidget]): 父窗口对象。
        """
        super().__init__(parent)
        self.controller = controller
        
        self.setWindowTitle("调整二值化参数")
        self.setMinimumWidth(350)
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)
        self._create_threshold_group()
        main_layout.addWidget(self.threshold_group)
        
    def _create_threshold_group(self):
        """创建完整的阈值设置UI组。"""
        self.threshold_group = QGroupBox("阈值方法")
        layout = QVBoxLayout(self.threshold_group)

        self.threshold_method_combo = QComboBox(objectName="threshold.method")
        self.threshold_method_map = {
            0: "adaptive_gaussian", 1: "otsu", 2: "global", 3: "niblack", 4: "sauvola"
        }
        self.threshold_method_combo.addItems([
            "自适应高斯 (Adaptive Gaussian)", "Otsu 自动阈值", "全局阈值 (Global)", "Niblack", "Sauvola"
        ])
        layout.addWidget(self.threshold_method_combo)

        self.threshold_params_stack = QStackedWidget()
        self.adaptive_widget = self._create_adaptive_gaussian_widget()
        self.otsu_widget = QWidget() 
        self.global_threshold_widget = self._create_global_threshold_widget()
        self.niblack_widget = self._create_niblack_sauvola_widget(is_sauvola=False)
        self.sauvola_widget = self._create_niblack_sauvola_widget(is_sauvola=True)
        
        self.threshold_params_stack.addWidget(self.adaptive_widget)
        self.threshold_params_stack.addWidget(self.otsu_widget)
        self.threshold_params_stack.addWidget(self.global_threshold_widget)
        self.threshold_params_stack.addWidget(self.niblack_widget)
        self.threshold_params_stack.addWidget(self.sauvola_widget)

        layout.addWidget(self.threshold_params_stack)

    def _create_global_threshold_widget(self) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        slider = QSlider(Qt.Horizontal, objectName="threshold.global_value"); slider.setRange(0, 255)
        label = QLabel()
        slider.valueChanged.connect(label.setNum)
        layout.addRow("阈值:", slider); layout.addRow("当前值:", label)
        return widget

    def _create_adaptive_gaussian_widget(self) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        bs_slider = QSlider(Qt.Horizontal, objectName="threshold.adaptive_block_size"); bs_slider.setRange(3, 51); bs_slider.setSingleStep(2)
        bs_label = QLabel()
        bs_slider.valueChanged.connect(bs_label.setNum)
        layout.addRow("Block Size:", bs_slider); layout.addRow("当前值:", bs_label)
        
        c_slider = QSlider(Qt.Horizontal, objectName="threshold.adaptive_c_value"); c_slider.setRange(-10, 10)
        c_label = QLabel()
        c_slider.valueChanged.connect(c_label.setNum)
        layout.addRow("C Value:", c_slider); layout.addRow("当前值:", c_label)
        return widget
        
    def _create_niblack_sauvola_widget(self, is_sauvola: bool) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        
        ws_slider = QSlider(Qt.Horizontal, objectName="threshold.window_size")
        ws_slider.setRange(3, 101); ws_slider.setSingleStep(2)
        ws_label = QLabel()
        ws_slider.valueChanged.connect(ws_label.setNum)
        layout.addRow("Window Size:", ws_slider); layout.addRow("当前值:", ws_label)

        k_spinbox = QDoubleSpinBox(objectName="threshold.k")
        k_spinbox.setRange(-2.0, 2.0); k_spinbox.setSingleStep(0.05)
        layout.addRow("K Value:", k_spinbox)
        
        if is_sauvola:
            r_slider = QSlider(Qt.Horizontal, objectName="threshold.r"); r_slider.setRange(0, 255)
            r_label = QLabel()
            r_slider.valueChanged.connect(r_label.setNum)
            layout.addRow("R Value:", r_slider); layout.addRow("当前值:", r_label)
            
        return widget

    def _connect_signals(self):
        self.threshold_method_combo.currentIndexChanged.connect(self.threshold_params_stack.setCurrentIndex)
        
        all_param_widgets = self.findChildren((QComboBox, QSlider, QDoubleSpinBox))
        for widget in all_param_widgets:
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._on_parameter_changed)
            elif isinstance(widget, QSlider):
                widget.sliderReleased.connect(self._on_parameter_changed)
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self._on_parameter_changed)

    def _on_parameter_changed(self, value=None):
        sender = self.sender()
        if not (sender and sender.objectName()): return

        param_path = sender.objectName()
        
        # [修复] 重新实现清晰的逻辑来获取值
        if isinstance(sender, QComboBox):
            value = self.threshold_method_map.get(sender.currentIndex())
        elif isinstance(sender, (QSlider, QDoubleSpinBox)):
            # value is passed directly by the signal
            pass
        else:
            return # Should not happen

        # 确保窗口大小是奇数
        if "window_size" in param_path and value % 2 == 0:
            value += 1
            # 临时阻止信号以避免递归设置
            sender.blockSignals(True)
            sender.setValue(value)
            sender.blockSignals(False)

        if value is not None:
            self.parameter_changed.emit(param_path, value)

            # 检查是否需要触发实时预览
            current_params = self.controller.get_current_parameters()
            param_group = param_path.split('.')[0] # e.g., 'threshold'
            
            hints = current_params.get(param_group, {}).get('ui_hints', {})
            if hints.get('realtime', False):
                self.realtime_preview_requested.emit()

    def update_controls(self, params: dict):
        print("DEBUG Dialog: update_controls CALLED.")
        p = params.get('threshold', {})
        if not p: 
            print("DEBUG Dialog: update_controls exiting, no threshold params found.")
            return
        
        all_param_widgets = self.findChildren((QComboBox, QSlider, QDoubleSpinBox))
        for widget in all_param_widgets: widget.blockSignals(True)

        try:
            method = p.get('method', 'adaptive_gaussian')
            rev_map = {v: k for k, v in self.threshold_method_map.items()}
            self.threshold_method_combo.setCurrentIndex(rev_map.get(method, 0))
            
            # Set values for all widgets regardless of visibility
            self.findChild(QSlider, "threshold.global_value").setValue(p.get('value', 127))
            self.findChild(QSlider, "threshold.adaptive_block_size").setValue(p.get('block_size', 11))
            self.findChild(QSlider, "threshold.adaptive_c_value").setValue(p.get('c', 2))
            self.findChild(QSlider, "threshold.window_size").setValue(p.get('window_size', 25))
            self.findChild(QDoubleSpinBox, "threshold.k").setValue(p.get('k', -0.2))
            self.findChild(QSlider, "threshold.r").setValue(p.get('r', 128))
        finally:
            for widget in all_param_widgets: widget.blockSignals(False)
            
            # [修复] 移除以下手动发射信号的代码。
            # 这些代码是造成无限递归和程序崩溃的根源。
            # 它们在update_controls的末尾重新触发了连接到_on_parameter_changed的信号，
            # 导致 "update -> emit -> update" 的死循环。
            # print("DEBUG Dialog: update_controls is now manually emitting signals to update UI labels.")
            # self.threshold_method_combo.currentIndexChanged.emit(self.threshold_method_combo.currentIndex())
            # for slider in self.findChildren(QSlider):
            #     slider.valueChanged.emit(slider.value())
            # print("DEBUG Dialog: update_controls FINISHED.") 