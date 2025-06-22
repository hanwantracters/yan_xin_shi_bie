"""控制面板组件，包含图像处理和分析的控制按钮和参数调节。

该模块提供了应用程序的主要控制界面，用户可以通过此面板加载图像、
开始分析和调整处理参数。遵循 Google 风格的 Docstrings 和类型提示。
"""

from typing import Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QGroupBox,
    QRadioButton,
)


class ControlPanel(QWidget):
    """控制面板类，提供用户交互控制界面。

    该类包含加载图像、开始分析和测量等按钮，以及阈值调节滑块。
    通过信号机制与主窗口进行通信。

    Attributes:
        loadImageClicked (pyqtSignal): 加载图像按钮点击时发出，携带文件路径字符串。
        startAnalysisClicked (pyqtSignal): 开始分析按钮点击时发出。
        measureToolClicked (pyqtSignal): 测量工具按钮点击时发出。
        thresholdChanged (pyqtSignal): 阈值滑块值变化时发出，携带整数值。
        thresholdMethodChanged (pyqtSignal): 阈值方法变化时发出，携带字符串。
        adaptiveParamsChanged (pyqtSignal): 自适应阈值参数变化时发出，携带字典。
    """

    # 定义信号
    loadImageClicked = pyqtSignal(str)  # 修改为传递文件路径
    startAnalysisClicked = pyqtSignal()
    measureToolClicked = pyqtSignal()
    thresholdChanged = pyqtSignal(int)
    thresholdMethodChanged = pyqtSignal(str)
    adaptiveParamsChanged = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化控制面板。

        Args:
            parent (Optional[QWidget]): 父窗口对象。默认为 None。
        """
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化UI组件和布局。"""
        # 创建按钮
        self.load_image_btn = QPushButton("加载图像")
        self.start_analysis_btn = QPushButton("开始分析")
        self.measure_btn = QPushButton("测量")

        # 创建阈值方法选择组
        self._create_threshold_method_group()

        # 创建全局阈值相关控件
        self._create_global_threshold_controls()

        # 创建自适应阈值相关控件
        self._create_adaptive_threshold_controls()

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_image_btn)
        main_layout.addWidget(self.start_analysis_btn)
        main_layout.addWidget(self.measure_btn)
        main_layout.addWidget(self.threshold_method_group)
        main_layout.addWidget(self.global_threshold_widget)
        main_layout.addWidget(self.adaptive_threshold_widget)
        main_layout.addStretch(1)  # 添加弹性空间

        self.setLayout(main_layout)

        # 连接信号
        self._connect_signals()
        
        # 初始状态更新
        self._on_threshold_method_changed()

    def _create_threshold_method_group(self):
        """创建阈值方法选择组。"""
        self.threshold_method_group = QGroupBox("阈值方法")
        layout = QVBoxLayout()
        self.global_radio = QRadioButton("全局阈值")
        self.adaptive_radio = QRadioButton("自适应高斯")
        self.otsu_radio = QRadioButton("Otsu自动阈值")
        self.global_radio.setChecked(True)
        layout.addWidget(self.global_radio)
        layout.addWidget(self.adaptive_radio)
        layout.addWidget(self.otsu_radio)
        self.threshold_method_group.setLayout(layout)

    def _create_global_threshold_controls(self):
        """创建全局阈值控件。"""
        self.global_threshold_widget = QWidget()
        layout = QHBoxLayout()
        self.threshold_label = QLabel("阈值:")
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(128)
        self.threshold_value_label = QLabel(str(self.threshold_slider.value()))
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.threshold_slider)
        layout.addWidget(self.threshold_value_label)
        self.global_threshold_widget.setLayout(layout)

    def _create_adaptive_threshold_controls(self):
        """创建自适应阈值控件。"""
        self.adaptive_threshold_widget = QWidget()
        layout = QVBoxLayout()
        
        # Block Size
        block_size_layout = QHBoxLayout()
        self.block_size_label = QLabel("Block Size:")
        self.block_size_slider = QSlider(Qt.Horizontal)
        self.block_size_slider.setRange(3, 51)
        self.block_size_slider.setSingleStep(2)
        self.block_size_slider.setValue(11)
        self.block_size_value_label = QLabel(str(self.block_size_slider.value()))
        block_size_layout.addWidget(self.block_size_label)
        block_size_layout.addWidget(self.block_size_slider)
        block_size_layout.addWidget(self.block_size_value_label)
        
        # C Value
        c_value_layout = QHBoxLayout()
        self.c_value_label = QLabel("C Value:")
        self.c_value_slider = QSlider(Qt.Horizontal)
        self.c_value_slider.setRange(-10, 10)
        self.c_value_slider.setValue(2)
        self.c_value_value_label = QLabel(str(self.c_value_slider.value()))
        c_value_layout.addWidget(self.c_value_label)
        c_value_layout.addWidget(self.c_value_slider)
        c_value_layout.addWidget(self.c_value_value_label)
        
        layout.addLayout(block_size_layout)
        layout.addLayout(c_value_layout)
        self.adaptive_threshold_widget.setLayout(layout)

    def _connect_signals(self) -> None:
        """连接所有内部信号和槽。"""
        self.load_image_btn.clicked.connect(self._on_load_image_clicked)
        self.start_analysis_btn.clicked.connect(self.startAnalysisClicked)
        self.measure_btn.clicked.connect(self.measureToolClicked)
        
        # 阈值信号
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self.global_radio.toggled.connect(self._on_threshold_method_changed)
        self.adaptive_radio.toggled.connect(self._on_threshold_method_changed)
        self.otsu_radio.toggled.connect(self._on_threshold_method_changed)
        self.block_size_slider.valueChanged.connect(self._on_adaptive_params_changed)
        self.c_value_slider.valueChanged.connect(self._on_adaptive_params_changed)

    def _on_threshold_method_changed(self):
        """处理阈值方法变化的槽函数。"""
        method = self.get_selected_threshold_method()
        self.global_threshold_widget.setVisible(method == 'global')
        self.adaptive_threshold_widget.setVisible(method == 'adaptive_gaussian')
        self.thresholdMethodChanged.emit(method)
        
    def _on_adaptive_params_changed(self):
        """处理自适应阈值参数变化的槽函数。"""
        block_size = self.block_size_slider.value()
        if block_size % 2 == 0: # 确保为奇数
            block_size +=1
            self.block_size_slider.setValue(block_size)

        self.block_size_value_label.setText(str(block_size))
        c_value = self.c_value_slider.value()
        self.c_value_value_label.setText(str(c_value))
        
        params = {'block_size': block_size, 'c': c_value}
        self.adaptiveParamsChanged.emit(params)

    def get_selected_threshold_method(self) -> str:
        """获取当前选择的阈值方法。"""
        if self.global_radio.isChecked():
            return 'global'
        if self.adaptive_radio.isChecked():
            return 'adaptive_gaussian'
        if self.otsu_radio.isChecked():
            return 'otsu'
        return 'global' # 默认

    def _on_threshold_changed(self, value: int) -> None:
        """处理阈值滑块值变化的槽函数。

        更新显示阈值的标签，并发出带有新值的信号。

        Args:
            value (int): 滑块的新整数值。
        """
        self.threshold_value_label.setText(str(value))
        self.thresholdChanged.emit(value)
        
    def _on_load_image_clicked(self) -> None:
        """处理加载图像按钮点击事件。
        
        打开文件选择对话框，让用户选择图像文件，然后发出带有文件路径的信号。
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像文件",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
        )
        
        if file_path:
            # 如果用户选择了文件，发出信号并携带文件路径
            self.loadImageClicked.emit(file_path) 