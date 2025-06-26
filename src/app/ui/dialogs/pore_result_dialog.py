"""孔洞分析结果的专属对话框。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QWidget

from .base_result_dialog import BaseResultDialog
from ...core.controller import Controller
from ...utils.constants import ResultKeys


class PoreResultDialog(BaseResultDialog):
    """
    用于显示孔洞分析结果的对话框。
    
    它继承自 BaseResultDialog，并添加了孔洞分析特有的标签页。
    """
    def __init__(self, controller: Controller, parent: QWidget = None):
        super().__init__(controller, parent)
        self.setWindowTitle("孔洞分析结果")

    def _populate_tabs(self):
        """添加孔洞分析专属的标签页。"""
        # 1. 创建最终结果标签页
        final_result_label = QLabel()
        final_result_label.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(final_result_label, "最终结果")
        self.tabs[ResultKeys.VISUALIZATION.value] = final_result_label

        # 2. 创建其他专属标签页 (暂用QLabel占位)
        tab_titles = ["数量分析", "尺寸分布", "形态数据", "分水岭处理"]
        for title in tab_titles:
            placeholder_label = QLabel(f"{title}将在此处显示...")
            placeholder_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.tab_widget.addTab(placeholder_label, title) 