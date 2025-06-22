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
    """

    # 定义信号
    loadImageClicked = pyqtSignal(str)  # 修改为传递文件路径
    startAnalysisClicked = pyqtSignal()
    measureToolClicked = pyqtSignal()
    thresholdChanged = pyqtSignal(int)

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

        # 创建阈值相关控件
        self.threshold_label = QLabel("阈值:")
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(128)  # 默认值
        self.threshold_value_label = QLabel(str(self.threshold_slider.value()))

        # 设置阈值控件布局
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_image_btn)
        main_layout.addWidget(self.start_analysis_btn)
        main_layout.addWidget(self.measure_btn)
        main_layout.addLayout(threshold_layout)
        main_layout.addStretch(1)  # 添加弹性空间

        self.setLayout(main_layout)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self) -> None:
        """连接所有内部信号和槽。"""
        self.load_image_btn.clicked.connect(self._on_load_image_clicked)
        self.start_analysis_btn.clicked.connect(self.startAnalysisClicked)
        self.measure_btn.clicked.connect(self.measureToolClicked)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

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