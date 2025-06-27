"""控制面板组件，包含图像处理和分析的控制按钮和参数调节。

该模块提供了应用程序的主要控制界面，用户可以通过此面板加载图像、
开始分析和调整处理参数。遵循 Google 风格的 Docstrings 和类型提示。
"""

from typing import Optional, List, Tuple

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QComboBox,
    QStackedWidget,
    QLabel,
    QMessageBox
)

from ..core.controller import Controller
from .parameter_panels.fracture_params_panel import FractureParamsPanel
from .parameter_panels.pore_params_panel import PoreParamsPanel


class ControlPanel(QWidget):
    """控制面板类，提供用户交互控制界面。

    该类包含加载图像、开始分析和测量等按钮，以及所有分析参数的调节控件。
    通过信号机制与主窗口进行通信。
    """

    # 定义信号
    image_load_requested = pyqtSignal()
    analysis_requested = pyqtSignal()
    measure_tool_clicked = pyqtSignal()
    import_parameters_requested = pyqtSignal()
    export_parameters_requested = pyqtSignal()
    analyzer_changed = pyqtSignal(str)

    def __init__(self, controller: Controller, parent: Optional[QWidget] = None) -> None:
        """初始化控制面板。"""
        super().__init__(parent)
        self.controller = controller
        
        # 分析器ID到其UI面板类的映射
        self.analyzer_panel_map = {
            'fracture': FractureParamsPanel,
            'pore_watershed': PoreParamsPanel
        }

        self._init_ui()
        self._connect_signals()
        self._populate_analyzer_selector() # 主动填充分析器列表

    def _init_ui(self) -> None:
        """初始化UI组件和布局。"""
        self.load_image_btn = QPushButton("加载图像")
        self.start_analysis_btn = QPushButton("一键执行分析")
        self.measure_btn = QPushButton("手动测量")

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.load_image_btn)
        main_layout.addWidget(self.start_analysis_btn)
        main_layout.addWidget(self.measure_btn)
        main_layout.addWidget(self._create_parameter_management_group())
        main_layout.addWidget(self._create_analysis_mode_group())
        main_layout.addStretch(1)

        self.setLayout(main_layout)

    def _create_parameter_management_group(self) -> QGroupBox:
        """创建参数导入/导出组。"""
        group = QGroupBox("参数管理")
        layout = QHBoxLayout(group)
        self.import_btn = QPushButton("导入参数")
        self.export_btn = QPushButton("导出参数")
        layout.addWidget(self.import_btn)
        layout.addWidget(self.export_btn)
        return group

    def _create_analysis_mode_group(self) -> QGroupBox:
        """创建分析模式选择和参数调整的组合框。"""
        group = QGroupBox("分析模式")
        layout = QVBoxLayout(group)
        
        # 模式选择下拉框
        self.mode_selector_combo = QComboBox()
        
        # 参数面板的堆叠窗口
        self.params_stack = QStackedWidget()

        layout.addWidget(QLabel("选择分析类型:"))
        layout.addWidget(self.mode_selector_combo)
        layout.addWidget(self.params_stack)
        
        return group

    def _connect_signals(self):
        """连接所有UI控件的信号。"""
        # 主功能按钮
        self.load_image_btn.clicked.connect(self.image_load_requested)
        self.start_analysis_btn.clicked.connect(self.analysis_requested)
        self.measure_btn.clicked.connect(self.measure_tool_clicked)
        
        # 参数管理
        self.import_btn.clicked.connect(self.import_parameters_requested)
        self.export_btn.clicked.connect(self.export_parameters_requested)
        
        # 分析器和模式选择
        self.mode_selector_combo.currentIndexChanged.connect(self._on_mode_changed)

    def _populate_analyzer_selector(self):
        """从控制器获取并填充分析器选择器。"""
        # 主动从控制器拉取分析器列表
        analyzers = self.controller.get_registered_analyzers()
        print(f"[DEBUG ControlPanel] 从控制器获取分析器列表: {analyzers}")

        # 断开信号，以防在填充时意外触发
        self.mode_selector_combo.currentIndexChanged.disconnect(self._on_mode_changed)

        self.mode_selector_combo.clear()
        for analyzer_id, analyzer_name in analyzers:
            self.mode_selector_combo.addItem(analyzer_name, userData=analyzer_id)
        
        # 重新连接信号
        self.mode_selector_combo.currentIndexChanged.connect(self._on_mode_changed)
        
        # 手动触发一次模式切换，以加载默认的分析器面板
        if self.mode_selector_combo.count() > 0:
            self.mode_selector_combo.setCurrentIndex(0)
            self._on_mode_changed(0) # 明确调用，确保加载

    def _on_mode_changed(self, index: int):
        """当用户切换分析模式时，创建并显示对应的参数面板。"""
        if index == -1:
            return
            
        analyzer_id = self.mode_selector_combo.itemData(index)
        if not analyzer_id:
            return

        # 1. 通知控制器切换激活的分析器
        self.controller.set_active_analyzer(analyzer_id)
        
        # 2. 清空旧的参数面板
        while self.params_stack.count() > 0:
            widget = self.params_stack.widget(0)
            self.params_stack.removeWidget(widget)
            widget.deleteLater()

        # 3. 使用映射表查找并创建新的参数面板
        PanelClass = self.analyzer_panel_map.get(analyzer_id)
        if PanelClass:
            panel_instance = PanelClass(self.controller)
            
            # 4. 执行关键连接：
            #   - 将面板的信号连接到控制器的槽 (UI -> Controller)
            panel_instance.parameter_changed.connect(self.controller.update_parameter)
            panel_instance.realtime_preview_requested.connect(self.controller.request_realtime_preview)
            #   - 将控制器的信号连接到面板的槽 (Controller -> UI)
            #   - 这确保了从文件加载参数时，对话框能够同步更新
            self.controller.parameters_updated.connect(panel_instance.on_parameters_updated)

            # 5. 将新面板添加到堆叠窗口并显示
            self.params_stack.addWidget(panel_instance)
            self.params_stack.setCurrentWidget(panel_instance)
            print(f"UI已切换到分析模式: {self.mode_selector_combo.currentText()}")
            self.analyzer_changed.emit(analyzer_id)
        else:
            print(f"警告: 未找到分析器ID '{analyzer_id}' 对应的参数面板类。")
        
    def _on_load_image_clicked(self) -> None:
        """打开文件对话框让用户选择图像，并发射信号。"""
        # 这个方法现在应该由MainWindow处理，这里只发射信号
        self.image_load_requested.emit()

    def _on_analyzers_registered(self, analyzers: List[Tuple[str, str]]):
        """当控制器注册了分析器后，仅更新模式选择下拉框。"""
        # 断开信号，以防在填充时意外触发
        self.mode_selector_combo.currentIndexChanged.disconnect(self._on_mode_changed)

        self.mode_selector_combo.clear()
        for analyzer_id, analyzer_name in analyzers:
            self.mode_selector_combo.addItem(analyzer_name, userData=analyzer_id)
        
        # 重新连接信号
        self.mode_selector_combo.currentIndexChanged.connect(self._on_mode_changed)
        
        # 手动触发一次模式切换，以加载默认的分析器面板
        if self.mode_selector_combo.count() > 0:
            self.mode_selector_combo.setCurrentIndex(0)
            self._on_mode_changed(0) # 明确调用，确保加载 