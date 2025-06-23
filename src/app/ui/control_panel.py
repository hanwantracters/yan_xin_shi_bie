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
    QComboBox,
    QStackedWidget,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox
)

from .morphology_settings_dialog import MorphologySettingsDialog


class ControlPanel(QWidget):
    """控制面板类，提供用户交互控制界面。

    该类包含加载图像、开始分析和测量等按钮，以及阈值调节控件。
    通过信号机制与主窗口进行通信。

    Attributes:
        loadImageClicked (pyqtSignal): 加载图像按钮点击时发出，携带文件路径字符串。
        startAnalysisClicked (pyqtSignal): 开始分析按钮点击时发出。
        measureToolClicked (pyqtSignal): 测量工具按钮点击时发出。
        thresholdParamsChanged (pyqtSignal): 阈值参数变化时发出，携带一个参数字典。
        morphologyParamsChanged (pyqtSignal): 形态学参数变化时发出，携带一个参数字典。
        mergeFracturesToggled (pyqtSignal): 合并裂缝按钮点击时发出，携带一个布尔值。
    """

    # 定义信号
    loadImageClicked = pyqtSignal(str)
    startAnalysisClicked = pyqtSignal()
    measureToolClicked = pyqtSignal()
    thresholdParamsChanged = pyqtSignal(dict)
    morphologyParamsChanged = pyqtSignal(dict)
    mergeFracturesToggled = pyqtSignal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初始化控制面板。

        Args:
            parent (Optional[QWidget]): 父窗口对象。默认为 None。
        """
        super().__init__(parent)
        self._init_ui()
        self.morphology_dialog = None # 用于持有对话框实例

    def _init_ui(self) -> None:
        """初始化UI组件和布局。"""
        # 创建按钮
        self.load_image_btn = QPushButton("加载图像")
        self.start_analysis_btn = QPushButton("开始分析")
        self.measure_btn = QPushButton("测量")
        self.morphology_settings_btn = QPushButton("形态学设置...")
        self.merge_fractures_checkbox = QCheckBox("启用轮廓智能合并")

        # 创建阈值设置组
        self._create_threshold_group()

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.load_image_btn)
        main_layout.addWidget(self.start_analysis_btn)
        main_layout.addWidget(self.measure_btn)
        main_layout.addWidget(self.morphology_settings_btn)
        main_layout.addWidget(self.merge_fractures_checkbox)
        main_layout.addWidget(self.threshold_group)
        main_layout.addStretch(1)  # 添加弹性空间

        self.setLayout(main_layout)

        # 连接信号
        self._connect_signals()
        
        # 首次触发参数信号
        self._emit_threshold_params()

    def _create_threshold_group(self):
        """创建完整的阈值设置UI组。"""
        self.threshold_group = QGroupBox("阈值方法")
        layout = QVBoxLayout(self.threshold_group)

        # 1. 方法选择下拉框
        self.threshold_method_combo = QComboBox()
        self.threshold_method_combo.addItems([
            "全局阈值 (Global)",
            "Otsu 自动阈值",
            "自适应高斯 (Adaptive Gaussian)",
            "Niblack",
            "Sauvola"
        ])
        layout.addWidget(self.threshold_method_combo)

        # 2. 参数设置堆叠窗口
        self.threshold_params_stack = QStackedWidget()
        self.global_threshold_widget = self._create_global_threshold_widget()
        self.otsu_widget = QWidget() # Otsu无参数，使用空QWidget
        self.adaptive_widget = self._create_adaptive_gaussian_widget()
        self.niblack_widget = self._create_niblack_sauvola_widget()
        self.sauvola_widget = self._create_niblack_sauvola_widget(is_sauvola=True)
        
        self.threshold_params_stack.addWidget(self.global_threshold_widget)
        self.threshold_params_stack.addWidget(self.otsu_widget)
        self.threshold_params_stack.addWidget(self.adaptive_widget)
        self.threshold_params_stack.addWidget(self.niblack_widget)
        self.threshold_params_stack.addWidget(self.sauvola_widget)

        layout.addWidget(self.threshold_params_stack)

    def _create_global_threshold_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        slider = QSlider(Qt.Horizontal, objectName="threshold_slider")
        slider.setRange(0, 255); slider.setValue(128)
        label = QLabel("128", objectName="value_label")
        slider.valueChanged.connect(lambda v, lbl=label: lbl.setText(str(v)))
        layout.addWidget(QLabel("阈值:"))
        layout.addWidget(slider); layout.addWidget(label)
        return widget

    def _create_adaptive_gaussian_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        
        # Block Size
        bs_layout = QHBoxLayout()
        bs_slider = QSlider(Qt.Horizontal, objectName="block_size_slider")
        bs_slider.setRange(3, 51); bs_slider.setSingleStep(2); bs_slider.setValue(11)
        bs_label = QLabel("11", objectName="value_label")
        bs_slider.valueChanged.connect(lambda v, lbl=bs_label: lbl.setText(str(v)))
        bs_layout.addWidget(QLabel("Block Size:"))
        bs_layout.addWidget(bs_slider); bs_layout.addWidget(bs_label)
        
        # C Value
        c_layout = QHBoxLayout()
        c_slider = QSlider(Qt.Horizontal, objectName="c_value_slider")
        c_slider.setRange(-10, 10); c_slider.setValue(2)
        c_label = QLabel("2", objectName="value_label")
        c_slider.valueChanged.connect(lambda v, lbl=c_label: lbl.setText(str(v)))
        c_layout.addWidget(QLabel("C Value:"))
        c_layout.addWidget(c_slider); c_layout.addWidget(c_label)
        
        layout.addLayout(bs_layout); layout.addLayout(c_layout)
        return widget

    def _create_niblack_sauvola_widget(self, is_sauvola: bool = False) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        
        # Window Size
        ws_layout = QHBoxLayout()
        ws_slider = QSlider(Qt.Horizontal, objectName="window_size_slider")
        ws_slider.setRange(3, 101); ws_slider.setSingleStep(2); ws_slider.setValue(25)
        ws_label = QLabel("25", objectName="value_label")
        ws_slider.valueChanged.connect(lambda v, lbl=ws_label: lbl.setText(str(v)))
        ws_layout.addWidget(QLabel("Window Size:"))
        ws_layout.addWidget(ws_slider); ws_layout.addWidget(ws_label)
        layout.addLayout(ws_layout)

        # K Value
        k_layout = QHBoxLayout()
        k_spinbox = QDoubleSpinBox(objectName="k_spinbox")
        k_spinbox.setRange(-1.0, 1.0); k_spinbox.setSingleStep(0.05); k_spinbox.setValue(0.2)
        k_layout.addWidget(QLabel("K Value:"))
        k_layout.addWidget(k_spinbox)
        layout.addLayout(k_layout)
        
        if is_sauvola:
            # R Value (only for Sauvola)
            r_layout = QHBoxLayout()
            r_slider = QSlider(Qt.Horizontal, objectName="r_slider")
            r_slider.setRange(0, 255); r_slider.setValue(128)
            r_label = QLabel("128", objectName="value_label")
            r_slider.valueChanged.connect(lambda v, lbl=r_label: lbl.setText(str(v)))
            r_layout.addWidget(QLabel("R Value:"))
            r_layout.addWidget(r_slider); r_layout.addWidget(r_label)
            layout.addLayout(r_layout)
            
        return widget


    def _connect_signals(self) -> None:
        """连接所有内部信号和槽。"""
        self.load_image_btn.clicked.connect(self._on_load_image_clicked)
        self.start_analysis_btn.clicked.connect(self.startAnalysisClicked)
        self.measure_btn.clicked.connect(self.measureToolClicked)
        self.morphology_settings_btn.clicked.connect(self._on_morphology_settings_clicked)
        self.merge_fractures_checkbox.toggled.connect(self.mergeFracturesToggled)
        
        # 阈值信号
        self.threshold_method_combo.currentIndexChanged.connect(self.threshold_params_stack.setCurrentIndex)
        self.threshold_method_combo.currentIndexChanged.connect(self._emit_threshold_params)

        # 连接所有参数控件
        for widget in self.threshold_params_stack.findChildren(QWidget):
            if isinstance(widget, QSlider):
                widget.valueChanged.connect(self._emit_threshold_params)
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(self._emit_threshold_params)

    def _emit_threshold_params(self):
        """收集当前阈值参数并发出信号。"""
        index = self.threshold_method_combo.currentIndex()
        method_map = {
            0: 'global', 1: 'otsu', 2: 'adaptive_gaussian', 3: 'niblack', 4: 'sauvola'
        }
        method = method_map.get(index)
        params = {}
        
        if method == 'global':
            w = self.global_threshold_widget
            params['threshold'] = w.findChild(QSlider, 'threshold_slider').value()
        elif method == 'adaptive_gaussian':
            w = self.adaptive_widget
            bs = w.findChild(QSlider, 'block_size_slider').value()
            params['block_size'] = bs if bs % 2 != 0 else bs + 1 # 确保奇数
            params['c'] = w.findChild(QSlider, 'c_value_slider').value()
        elif method == 'niblack':
            w = self.niblack_widget
            ws = w.findChild(QSlider, 'window_size_slider').value()
            params['window_size'] = ws if ws % 2 != 0 else ws + 1 # 确保奇数
            params['k'] = w.findChild(QDoubleSpinBox, 'k_spinbox').value()
        elif method == 'sauvola':
            w = self.sauvola_widget
            ws = w.findChild(QSlider, 'window_size_slider').value()
            params['window_size'] = ws if ws % 2 != 0 else ws + 1 # 确保奇数
            params['k'] = w.findChild(QDoubleSpinBox, 'k_spinbox').value()
            params['r'] = w.findChild(QSlider, 'r_slider').value()
            
        self.thresholdParamsChanged.emit({'method': method, 'params': params})

    def _on_morphology_settings_clicked(self):
        """处理形态学设置按钮点击事件。"""
        if not self.morphology_dialog:
            self.morphology_dialog = MorphologySettingsDialog(self)
            self.morphology_dialog.paramsChanged.connect(self.morphologyParamsChanged)
        
        if self.morphology_dialog.isHidden():
            self.morphology_dialog.show()
        else:
            self.morphology_dialog.activateWindow()

    def _on_load_image_clicked(self) -> None:
        """处理加载图像按钮点击事件。"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图像文件",
            "",
            "图像文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*)"
        )
        
        if file_path:
            self.loadImageClicked.emit(file_path) 