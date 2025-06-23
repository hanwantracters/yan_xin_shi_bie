"""形态学参数设置对话框。

提供一个独立的窗口，用于调整所有与形态学后处理相关的参数。
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QSpinBox
)

from ..core.controller import Controller

class MorphologySettingsDialog(QDialog):
    """用于设置形态学参数的对话框。"""
    
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

    def _on_parameter_changed(self):
        """当参数变化时，通知控制器。"""
        sender = self.sender()
        if not (sender and sender.objectName()): return

        param_path = sender.objectName()
        value = sender.value()
        self.controller.update_parameter(param_path, value)

    def update_controls(self, params: dict):
        """根据给定的参数字典更新所有UI控件的值。"""
        p = params.get('analysis_parameters', {}).get('morphology', {})
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
            
            # 手动触发一次信号以确保UI同步
            for spinbox in self.findChildren(QSpinBox):
                spinbox.valueChanged.emit(spinbox.value()) 