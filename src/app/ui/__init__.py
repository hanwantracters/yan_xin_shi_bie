"""UI层模块的初始化文件。"""

print("DEBUG: Initializing src.app.ui package")

# 导入所有UI组件，方便从app.ui直接访问
from .control_panel import ControlPanel
from .main_window import MainWindow
from .multi_stage_preview_widget import MultiStagePreviewWidget
from .result_panel import ResultPanel
from .style_manager import style_manager

"""UI组件包，包含应用程序的所有用户界面组件。

该包包含主窗口、控制面板、结果面板等UI组件，以及样式管理器。
"""

from .measurement_dialog import MeasurementDialog 