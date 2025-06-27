"""阈值参数设置对话框。

提供一个独立的窗口，用于调整所有与阈值分割相关的参数。
"""

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal as Signal, QTimer
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
    QDoubleSpinBox,
    QSpinBox
)

from src.app.core.controller import Controller
from src.app.utils.constants import StageKeys

class ThresholdSettingsDialog(QDialog):
    """用于设置阈值参数的对话框。"""
    
    parameter_changed = Signal(str, object)
    realtime_preview_requested = Signal(str)

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
        self._init_preview_timer()

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
        spinbox = QSpinBox(objectName="threshold.global_value_spinbox"); spinbox.setRange(0, 255)
        
        # 建立双向连接
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        
        layout.addRow("阈值:", slider)
        layout.addRow("当前值:", spinbox)
        return widget

    def _create_adaptive_gaussian_widget(self) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        
        # Block Size 控件组
        bs_slider = QSlider(Qt.Horizontal, objectName="threshold.adaptive_block_size")
        bs_slider.setRange(3, 51); bs_slider.setSingleStep(2)
        bs_spinbox = QSpinBox(objectName="threshold.adaptive_block_size_spinbox")
        bs_spinbox.setRange(3, 51); bs_spinbox.setSingleStep(2)
        
        # 确保Block Size为奇数
        def ensure_odd_bs(value):
            if value % 2 == 0:
                bs_spinbox.blockSignals(True)
                bs_spinbox.setValue(value + 1)
                bs_spinbox.blockSignals(False)
                return value + 1
            return value
            
        # 双向连接带奇数校验
        bs_slider.valueChanged.connect(lambda v: bs_spinbox.setValue(ensure_odd_bs(v)))
        bs_spinbox.valueChanged.connect(lambda v: bs_slider.setValue(ensure_odd_bs(v)))
        
        layout.addRow("Block Size:", bs_slider)
        layout.addRow("当前值:", bs_spinbox)
        
        # C Value 控件组
        c_slider = QSlider(Qt.Horizontal, objectName="threshold.adaptive_c_value")
        c_slider.setRange(-10, 10)
        c_spinbox = QSpinBox(objectName="threshold.adaptive_c_value_spinbox")
        c_spinbox.setRange(-10, 10)
        
        # 双向连接
        c_slider.valueChanged.connect(c_spinbox.setValue)
        c_spinbox.valueChanged.connect(c_slider.setValue)
        
        layout.addRow("C Value:", c_slider)
        layout.addRow("当前值:", c_spinbox)
        
        return widget
        
    def _create_niblack_sauvola_widget(self, is_sauvola: bool) -> QWidget:
        widget = QWidget(); layout = QFormLayout(widget)
        
        # Window Size 控件组
        ws_slider = QSlider(Qt.Horizontal, objectName="threshold.window_size")
        ws_slider.setRange(3, 101); ws_slider.setSingleStep(2)
        ws_spinbox = QSpinBox(objectName="threshold.window_size_spinbox")
        ws_spinbox.setRange(3, 101); ws_spinbox.setSingleStep(2)
        
        # 确保Window Size为奇数
        def ensure_odd_ws(value):
            if value % 2 == 0:
                ws_spinbox.blockSignals(True)
                ws_spinbox.setValue(value + 1)
                ws_spinbox.blockSignals(False)
                return value + 1
            return value
            
        # 双向连接带奇数校验
        ws_slider.valueChanged.connect(lambda v: ws_spinbox.setValue(ensure_odd_ws(v)))
        ws_spinbox.valueChanged.connect(lambda v: ws_slider.setValue(ensure_odd_ws(v)))
        
        layout.addRow("Window Size:", ws_slider)
        layout.addRow("当前值:", ws_spinbox)

        # K Value 控件组 (保持使用QDoubleSpinBox，因为需要小数)
        k_spinbox = QDoubleSpinBox(objectName="threshold.k")
        k_spinbox.setRange(-2.0, 2.0); k_spinbox.setSingleStep(0.05)
        layout.addRow("K Value:", k_spinbox)
        
        # Sauvola特有的R Value控件组
        if is_sauvola:
            r_slider = QSlider(Qt.Horizontal, objectName="threshold.r")
            r_slider.setRange(0, 255)
            r_spinbox = QSpinBox(objectName="threshold.r_spinbox")
            r_spinbox.setRange(0, 255)
            
            # 双向连接
            r_slider.valueChanged.connect(r_spinbox.setValue)
            r_spinbox.valueChanged.connect(r_slider.setValue)
            
            layout.addRow("R Value:", r_slider)
            layout.addRow("当前值:", r_spinbox)
            
        return widget

    def _init_preview_timer(self):
        """初始化用于延迟实时预览的计时器。"""
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        # The timer now triggers a method that emits the correct stage key
        self.preview_timer.timeout.connect(self._request_binary_preview)

    def _connect_signals(self):
        self.threshold_method_combo.currentIndexChanged.connect(self.threshold_params_stack.setCurrentIndex)
        
        all_param_widgets = self.findChildren((QComboBox, QSlider, QDoubleSpinBox, QSpinBox))
        for widget in all_param_widgets:
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._on_parameter_changed)
            elif isinstance(widget, (QSlider, QDoubleSpinBox, QSpinBox)):
                # 对于QSpinBox，我们只监听valueChanged信号
                # 滑块和QSpinBox之间的双向连接在各个创建方法中已经建立
                if isinstance(widget, QSpinBox) and "_spinbox" in widget.objectName():
                    continue  # 跳过spinbox对象，避免重复触发_on_parameter_changed
                widget.valueChanged.connect(self._on_parameter_changed)

    def _on_parameter_changed(self, value=None):
        sender = self.sender()
        if not (sender and sender.objectName()): return
        
        # 跳过所有辅助性SpinBox的信号处理，避免双重触发
        if isinstance(sender, QSpinBox) and "_spinbox" in sender.objectName():
            return

        param_path = sender.objectName()
        
        # [修复] 重新实现清晰的逻辑来获取值
        if isinstance(sender, QComboBox):
            value = self.threshold_method_map.get(sender.currentIndex())
        elif isinstance(sender, (QSlider, QDoubleSpinBox, QSpinBox)):
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
            print(f"[DEBUG Dialog] Parameter changed: {param_path} = {value}")
            self.parameter_changed.emit(param_path, value)

            # 检查是否需要触发实时预览
            current_params = self.controller.get_current_parameters()
            param_group = param_path.split('.')[0] # e.g., 'threshold'
            
            hints = current_params.get(param_group, {}).get('ui_hints', {})
            print(f"[DEBUG Dialog] Checking ui_hints for realtime preview: {hints}")
            if hints.get('realtime', False):
                print(f"[DEBUG Dialog] Realtime hint is True. Starting preview timer.")
                # 先停止计时器，确保多次快速变更只触发一次预览
                self.preview_timer.stop()
                self.preview_timer.start(500)

    def _request_binary_preview(self):
        """发射一个请求二值化阶段预览的信号。"""
        self.realtime_preview_requested.emit(StageKeys.BINARY.value)

    def update_controls(self, params: dict):
        print("DEBUG Dialog: update_controls CALLED.")
        p = params.get('threshold', {})
        if not p: 
            print("DEBUG Dialog: update_controls exiting, no threshold params found.")
            return
        
        all_param_widgets = self.findChildren((QComboBox, QSlider, QDoubleSpinBox, QSpinBox))
        for widget in all_param_widgets: widget.blockSignals(True)

        try:
            method = p.get('method', 'adaptive_gaussian')
            rev_map = {v: k for k, v in self.threshold_method_map.items()}
            self.threshold_method_combo.setCurrentIndex(rev_map.get(method, 0))
            
            # 设置滑块值
            self.findChild(QSlider, "threshold.global_value").setValue(p.get('value', 127))
            self.findChild(QSlider, "threshold.adaptive_block_size").setValue(p.get('block_size', 11))
            self.findChild(QSlider, "threshold.adaptive_c_value").setValue(p.get('c', 2))
            self.findChild(QSlider, "threshold.window_size").setValue(p.get('window_size', 25))
            self.findChild(QDoubleSpinBox, "threshold.k").setValue(p.get('k', -0.2))
            self.findChild(QSlider, "threshold.r").setValue(p.get('r', 128))
            
            # 设置对应的SpinBox值 (需要确保SpinBox存在)
            spinboxes = [
                ("threshold.global_value_spinbox", p.get('value', 127)),
                ("threshold.adaptive_block_size_spinbox", p.get('block_size', 11)),
                ("threshold.adaptive_c_value_spinbox", p.get('c', 2)),
                ("threshold.window_size_spinbox", p.get('window_size', 25)),
                ("threshold.r_spinbox", p.get('r', 128)),
            ]
            
            for name, value in spinboxes:
                spinbox = self.findChild(QSpinBox, name)
                if spinbox:
                    spinbox.setValue(value)
            
        finally:
            for widget in all_param_widgets: widget.blockSignals(False) 