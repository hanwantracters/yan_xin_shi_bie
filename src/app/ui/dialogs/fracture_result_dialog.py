"""裂缝分析结果的专属对话框。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QWidget

from .base_result_dialog import BaseResultDialog
from ...core.controller import Controller
from ...utils.constants import ResultKeys

class FractureResultDialog(BaseResultDialog):
    """
    用于显示裂缝分析结果的对话框。
    
    它继承自 BaseResultDialog，并添加了裂缝分析特有的标签页。
    """
    def __init__(self, controller: Controller, parent: QWidget = None):
        super().__init__(controller, parent)
        self.setWindowTitle("裂缝分析结果")

    def _populate_tabs(self):
        """添加裂缝分析专属的标签页。"""
        # 1. 创建最终结果标签页
        final_result_label = QLabel()
        final_result_label.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(final_result_label, "最终结果")
        # 将其添加到 self.tabs 字典中以便 update_content 可以更新它
        self.tabs[ResultKeys.VISUALIZATION.value] = final_result_label
        
        # 2. 创建定量数据标签页 (暂用QLabel占位)
        quantitative_data_label = QLabel("定量数据将在此处显示...")
        quantitative_data_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.tab_widget.addTab(quantitative_data_label, "定量数据")
        # 注意: 该标签页的数据更新需要在 update_content 中单独处理 