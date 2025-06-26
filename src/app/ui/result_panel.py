"""结果面板组件，用于显示岩石裂缝分析的结果。

该模块提供了一个文本区域，用于展示分析结果，包括裂缝数量、
总面积和总长度等信息。
"""

from PyQt5.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from typing import Dict, Any, Optional, Tuple


class ResultPanel(QWidget):
    """结果面板类，用于显示分析结果。
    
    该类包含一个只读的文本编辑器，用于展示分析结果的详细信息。
    
    Attributes:
        result_text: QTextEdit对象，用于显示结果文本
    """
    
    def __init__(self, parent=None):
        """初始化结果面板。
        
        Args:
            parent: 父窗口对象
        """
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        # 创建标题标签
        title_label = QLabel("分析结果")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setProperty("title", "true")  # 添加属性以便样式表识别
        
        # 创建Tab小部件
        self.tabs = QTabWidget()

        # 创建摘要文本编辑器
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setText("请加载图像并开始分析...")
        
        # 创建详细结果表格
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(4)
        self.details_table.setHorizontalHeaderLabels(["ID", "面积 (mm²)", "长度 (mm)", "角度 (°)"])
        self.details_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # 添加Tab
        self.tabs.addTab(self.summary_text, "摘要")
        self.tabs.addTab(self.details_table, "详细数据")

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.tabs)
        
        self.setLayout(main_layout)
        
    def update_analysis_results(self, results: Dict[str, Any]) -> None:
        """更新分析结果，包括摘要和详细数据。
        
        Args:
            results: 包含分析结果的字典。
        """
        # --- 调试打印 ---
        print(f"[DEBUG ResultPanel] 收到更新数据: {results}")

        # --- 更新摘要 ---
        summary_str = "分析摘要:\n\n"
        # 注意：这里我们暂时保留错误的键名，以便观察问题
        summary_str += f"裂缝数量: {results.get('fracture_count', '未找到')}\n"
        summary_str += f"总面积: {results.get('total_area_mm2', 0):.4f} mm²\n"
        summary_str += f"总长度: {results.get('total_length_mm', 0):.4f} mm\n"
        self.summary_text.setText(summary_str)
        
        # --- 更新详细数据表格 ---
        # 注意：这里我们暂时保留错误的键名，以便观察问题
        details = results.get('detailed_fractures', [])
        self.details_table.setRowCount(len(details))
        
        for row, item in enumerate(details):
            self.details_table.setItem(row, 0, QTableWidgetItem(str(item.get('id', row + 1))))
            self.details_table.setItem(row, 1, QTableWidgetItem(f"{item.get('area_mm2', 0):.4f}"))
            self.details_table.setItem(row, 2, QTableWidgetItem(f"{item.get('length_mm', 0):.4f}"))
            self.details_table.setItem(row, 3, QTableWidgetItem(f"{item.get('angle_degrees', 0):.2f}"))

    def update_dpi_info(self, dpi: Optional[Tuple[float, float]]) -> None:
        """更新图像DPI信息。
        
        Args:
            dpi: 图像的DPI信息，格式为(x_dpi, y_dpi)，如果为None则显示未知DPI
        """
        # 清空所有
        self.summary_text.clear()
        self.details_table.setRowCount(0)
        
        if dpi is None:
            dpi_text = "图像DPI: 未知"
        else:
            x_dpi, y_dpi = dpi
            dpi_text = f"图像DPI: {x_dpi}" if x_dpi == y_dpi else f"图像DPI: X={x_dpi}, Y={y_dpi}"
        
        self.summary_text.setText(f"{dpi_text}\n\n请开始分析...")

    def clear_results(self):
        """清空所有结果显示。"""
        self.summary_text.setText("请加载图像并开始分析...")
        self.details_table.setRowCount(0)

# 移除旧的 update_results 方法，因为它被 update_analysis_results 替代了。
# 为了简洁，这里直接注释掉了，但在实际编辑中会删除它。
#
#    def update_results(self, results: Dict[str, Any]) -> None:
#        ...
        