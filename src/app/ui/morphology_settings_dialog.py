"""形态学参数设置对话框。

提供一个独立的窗口，用于调整所有与形态学后处理相关的参数。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QSpinBox
)

from src.app.core.controller import Controller


class MorphologySettingsDialog(QDialog):
    """用于设置形态学参数的对话框。"""
    
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
        
        self.setWindowTitle("调整形态学参数")
        self.setMinimumWidth(300)
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)
        group_box = QGroupBox("形态学后处理")
        layout = QFormLayout(group_box)

        open_ksize_spinbox = QSpinBox(objectName="morphology.open_kernel_size")
        open_ksize_spinbox.setRange(1, 31); open_ksize_spinbox.setSingleStep(2)
        
        open_iter_spinbox = QSpinBox(objectName="morphology.open_iterations")
        open_iter_spinbox.setRange(1, 10)
        
        close_ksize_spinbox = QSpinBox(objectName="morphology.close_kernel_size")
        close_ksize_spinbox.setRange(1, 31); close_ksize_spinbox.setSingleStep(2)
        
        close_iter_spinbox = QSpinBox(objectName="morphology.close_iterations")
        close_iter_spinbox.setRange(1, 10)

        layout.addRow("开运算核大小:", open_ksize_spinbox)
        layout.addRow("开运算迭代次数:", open_iter_spinbox)
        layout.addRow("闭运算核大小:", close_ksize_spinbox)
        layout.addRow("闭运算迭代次数:", close_iter_spinbox)
        
        main_layout.addWidget(group_box)

    def _connect_signals(self):
        """连接所有参数控件的信号。"""
        for spinbox in self.findChildren(QSpinBox):
            spinbox.valueChanged.connect(self._on_parameter_changed)

    def _on_parameter_changed(self, value: int):
        """当参数变化时，通知控制器。"""
        sender = self.sender()
        if not (sender and sender.objectName()): return

        param_path = sender.objectName()
        self.parameter_changed.emit(param_path, value)

        # 检查是否需要触发实时预览
        current_params = self.controller.get_current_parameters()
        param_group = param_path.split('.')[0] # e.g., 'morphology'
        
        hints = current_params.get(param_group, {}).get('ui_hints', {})
        if hints.get('realtime', False):
            self.realtime_preview_requested.emit()

    def update_controls(self, params: dict):
        """根据给定的参数字典更新所有UI控件的值。"""
        p = params.get('morphology', {})
        if not p: return

        for spinbox in self.findChildren(QSpinBox):
            spinbox.blockSignals(True)

        try:
            self.findChild(QSpinBox, "morphology.open_kernel_size").setValue(p.get('open_kernel_size', 3))
            self.findChild(QSpinBox, "morphology.open_iterations").setValue(p.get('open_iterations', 1))
            self.findChild(QSpinBox, "morphology.close_kernel_size").setValue(p.get('close_kernel_size', 3))
            self.findChild(QSpinBox, "morphology.close_iterations").setValue(p.get('close_iterations', 1))
        finally:
            for spinbox in self.findChildren(QSpinBox):
                spinbox.blockSignals(False) 