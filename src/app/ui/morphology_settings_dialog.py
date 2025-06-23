"""形态学参数设置对话框。

该模块提供一个非模态对话框，用于调整形态学处理的参数。
支持为"去噪"和"连接"阶段选择不同的策略和参数。
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
    QStackedWidget,
    QSpinBox,
)
from PyQt5.QtCore import Qt


class MorphologySettingsDialog(QDialog):
    """形态学参数设置对话框类。

    该对话框允许用户为开运算（去噪）和闭运算（连接）
    分别设置不同的处理策略和参数。
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

    def _create_kernel_params_widget(
        self, size_default: int, iter_default: int
    ) -> QWidget:
        """创建一个用于设置核参数的通用小部件。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)

        # 1. 核形状
        shape_layout = QHBoxLayout()
        shape_combo = QComboBox()
        shape_combo.addItems(["矩形 (Rect)", "椭圆 (Ellipse)", "十字 (Cross)"])
        shape_combo.setObjectName("shape_combo")
        shape_layout.addWidget(QLabel("核形状:"))
        shape_layout.addWidget(shape_combo)
        layout.addLayout(shape_layout)

        # 2. 核大小
        size_layout = QHBoxLayout()
        size_slider = QSlider(Qt.Horizontal)
        size_slider.setRange(3, 21)
        size_slider.setSingleStep(2)
        size_slider.setValue(size_default)
        size_slider.setObjectName("size_slider")
        size_value_label = QLabel(str(size_default))
        size_value_label.setObjectName("size_value_label")
        size_layout.addWidget(QLabel("核大小:"))
        size_layout.addWidget(size_slider)
        size_layout.addWidget(size_value_label)
        layout.addLayout(size_layout)

        # 3. 迭代次数
        iter_layout = QHBoxLayout()
        iter_slider = QSlider(Qt.Horizontal)
        iter_slider.setRange(1, 10)
        iter_slider.setValue(iter_default)
        iter_slider.setObjectName("iter_slider")
        iter_value_label = QLabel(str(iter_default))
        iter_value_label.setObjectName("iter_value_label")
        iter_layout.addWidget(QLabel("迭代次数:"))
        iter_layout.addWidget(iter_slider)
        iter_layout.addWidget(iter_value_label)
        layout.addLayout(iter_layout)
        
        # 连接内部信号
        size_slider.valueChanged.connect(lambda v, lbl=size_value_label: lbl.setText(str(v)))
        iter_slider.valueChanged.connect(lambda v, lbl=iter_value_label: lbl.setText(str(v)))

        return widget

    def _create_area_params_widget(self, min_area_default: int) -> QWidget:
        """创建一个用于设置面积阈值的通用小部件。"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        
        area_spinbox = QSpinBox()
        area_spinbox.setRange(1, 1000)
        area_spinbox.setValue(min_area_default)
        area_spinbox.setSuffix(" px")
        area_spinbox.setObjectName("area_spinbox")
        
        layout.addWidget(QLabel("最小保留面积:"))
        layout.addWidget(area_spinbox)
        layout.addStretch()
        
        return widget

    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)

        # --- 去噪策略组 ---
        opening_group = QGroupBox("去噪策略 (开运算)")
        opening_layout = QVBoxLayout(opening_group)
        
        self.opening_strategy_combo = QComboBox()
        self.opening_strategy_combo.addItems(["标准开运算", "基于面积去噪"])
        opening_layout.addWidget(self.opening_strategy_combo)

        self.opening_params_stack = QStackedWidget()
        self.opening_standard_widget = self._create_kernel_params_widget(size_default=3, iter_default=1)
        self.opening_area_widget = self._create_area_params_widget(min_area_default=25)
        self.opening_params_stack.addWidget(self.opening_standard_widget)
        self.opening_params_stack.addWidget(self.opening_area_widget)
        opening_layout.addWidget(self.opening_params_stack)
        
        main_layout.addWidget(opening_group)
        
        # --- 连接策略组 ---
        closing_group = QGroupBox("连接策略 (闭运算)")
        closing_layout = QVBoxLayout(closing_group)

        self.closing_strategy_combo = QComboBox()
        self.closing_strategy_combo.addItems(["标准闭运算", "强力闭运算"])
        closing_layout.addWidget(self.closing_strategy_combo)
        
        self.closing_params_stack = QStackedWidget()
        self.closing_standard_widget = self._create_kernel_params_widget(size_default=3, iter_default=1)
        self.closing_strong_widget = self._create_kernel_params_widget(size_default=7, iter_default=2) # 更强的默认值
        self.closing_params_stack.addWidget(self.closing_standard_widget)
        self.closing_params_stack.addWidget(self.closing_strong_widget)
        closing_layout.addWidget(self.closing_params_stack)
        
        main_layout.addWidget(closing_group)

    def _connect_signals(self):
        """连接内部信号和槽。"""
        # 策略选择器
        self.opening_strategy_combo.currentIndexChanged.connect(self.opening_params_stack.setCurrentIndex)
        self.closing_strategy_combo.currentIndexChanged.connect(self.closing_params_stack.setCurrentIndex)
        
        self.opening_strategy_combo.currentIndexChanged.connect(self._emit_params)
        self.closing_strategy_combo.currentIndexChanged.connect(self._emit_params)

        # 连接所有子控件的信号
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QSlider):
                widget.valueChanged.connect(self._emit_params)
            elif isinstance(widget, QComboBox):
                # 排除策略选择器，因为它们已经连接过了
                if widget not in [self.opening_strategy_combo, self.closing_strategy_combo]:
                    widget.currentIndexChanged.connect(self._emit_params)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self._emit_params)


    def _emit_params(self):
        """收集所有参数并发出信号。"""
        shape_map = { "矩形 (Rect)": "rect", "椭圆 (Ellipse)": "ellipse", "十字 (Cross)": "cross" }

        # --- 获取去噪参数 ---
        opening_strategy = 'standard'
        op_params = {}
        if self.opening_strategy_combo.currentIndex() == 0: # 标准
            opening_strategy = 'standard'
            w = self.opening_standard_widget
            val = w.findChild(QSlider, "size_slider").value()
            op_params = {
                'kernel_shape': shape_map.get(w.findChild(QComboBox, "shape_combo").currentText()),
                'kernel_size': (val, val),
                'iterations': w.findChild(QSlider, "iter_slider").value()
            }
        else: # 面积
            opening_strategy = 'area_based'
            w = self.opening_area_widget
            op_params = {'min_area': w.findChild(QSpinBox, "area_spinbox").value()}

        # --- 获取连接参数 ---
        closing_strategy = 'standard'
        cl_params = {}
        if self.closing_strategy_combo.currentIndex() == 0: # 标准
            closing_strategy = 'standard'
            w = self.closing_standard_widget
            val = w.findChild(QSlider, "size_slider").value()
            cl_params = {
                'kernel_shape': shape_map.get(w.findChild(QComboBox, "shape_combo").currentText()),
                'kernel_size': (val, val),
                'iterations': w.findChild(QSlider, "iter_slider").value()
            }
        else: # 强力
            closing_strategy = 'strong'
            w = self.closing_strong_widget
            val = w.findChild(QSlider, "size_slider").value()
            cl_params = {
                'kernel_shape': shape_map.get(w.findChild(QComboBox, "shape_combo").currentText()),
                'kernel_size': (val, val),
                'iterations': w.findChild(QSlider, "iter_slider").value()
            }

        # --- 组装最终参数字典 ---
        final_params = {
            "opening_strategy": opening_strategy,
            "closing_strategy": closing_strategy,
            "params": {
                "standard_opening": op_params if opening_strategy == 'standard' else {},
                "area_based_opening": op_params if opening_strategy == 'area_based' else {},
                "standard_closing": cl_params if closing_strategy == 'standard' else {},
                "strong_closing": cl_params if closing_strategy == 'strong' else {}
            }
        }
        self.paramsChanged.emit(final_params) 