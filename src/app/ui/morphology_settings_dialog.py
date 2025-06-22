"""形态学参数设置对话框。

该模块提供一个非模态对话框，用于调整形态学处理的参数，
如核形状、大小和迭代次数。
"""

from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGroupBox,
    QComboBox,
    QSlider,
    QLabel,
    QHBoxLayout,
    QWidget,
)
from PyQt5.QtCore import Qt


class MorphologySettingsDialog(QDialog):
    """形态学参数设置对话框类。

    该对话框允许用户调整形态学后处理的参数。
    当参数变化时，会发出相应的信号。

    Signals:
        paramsChanged (pyqtSignal): 当任何参数发生变化时发出，携带一个包含所有参数的字典。
    """

    paramsChanged = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化对话框。

        Args:
            parent (Optional[QWidget]): 父窗口对象。
        """
        super().__init__(parent)
        self.setWindowTitle("形态学参数设置")
        self.setModal(False)  # 设置为非模态对话框

        self._init_ui()
        self._connect_signals()
        
        # 首次发出默认参数
        self._emit_params()

    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)

        # 创建参数设置组
        params_group = QGroupBox("形态学后处理参数")
        group_layout = QVBoxLayout()

        # 1. 核形状 (Kernel Shape)
        shape_layout = QHBoxLayout()
        self.shape_label = QLabel("核形状:")
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["矩形 (Rect)", "椭圆 (Ellipse)", "十字 (Cross)"])
        shape_layout.addWidget(self.shape_label)
        shape_layout.addWidget(self.shape_combo)
        group_layout.addLayout(shape_layout)

        # 2. 核大小 (Kernel Size)
        size_layout = QHBoxLayout()
        self.size_label = QLabel("核大小:")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(3, 15)
        self.size_slider.setSingleStep(2)  # 步长为2，确保是奇数
        self.size_slider.setValue(5)
        self.size_value_label = QLabel(str(self.size_slider.value()))
        size_layout.addWidget(self.size_label)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_value_label)
        group_layout.addLayout(size_layout)

        # 3. 迭代次数 (Iterations)
        iter_layout = QHBoxLayout()
        self.iter_label = QLabel("迭代次数:")
        self.iter_slider = QSlider(Qt.Horizontal)
        self.iter_slider.setRange(1, 5)
        self.iter_slider.setValue(1)
        self.iter_value_label = QLabel(str(self.iter_slider.value()))
        iter_layout.addWidget(self.iter_label)
        iter_layout.addWidget(self.iter_slider)
        iter_layout.addWidget(self.iter_value_label)
        group_layout.addLayout(iter_layout)

        params_group.setLayout(group_layout)
        main_layout.addWidget(params_group)

    def _connect_signals(self):
        """连接内部信号和槽。"""
        self.shape_combo.currentIndexChanged.connect(self._emit_params)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        self.iter_slider.valueChanged.connect(self._on_iter_changed)

    def _on_size_changed(self, value):
        """处理核大小滑块变化。"""
        # 确保值为奇数
        if value % 2 == 0:
            value += 1
            self.size_slider.setValue(value)
            return  # setValue会再次触发valueChanged，所以直接返回
        self.size_value_label.setText(str(value))
        self._emit_params()

    def _on_iter_changed(self, value):
        """处理迭代次数滑块变化。"""
        self.iter_value_label.setText(str(value))
        self._emit_params()

    def _emit_params(self):
        """收集所有参数并发出信号。"""
        shape_map = {
            "矩形 (Rect)": "rect",
            "椭圆 (Ellipse)": "ellipse",
            "十字 (Cross)": "cross",
        }
        params = {
            "kernel_shape": shape_map.get(self.shape_combo.currentText()),
            "kernel_size": self.size_slider.value(),
            "iterations": self.iter_slider.value(),
        }
        self.paramsChanged.emit(params) 