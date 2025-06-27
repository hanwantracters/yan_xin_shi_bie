"""结果面板组件，用于显示分析结果。

该模块提供了一个包含摘要和详细数据视图的面板，
并提供了将结果导出为CSV或Word文档的功能。
"""
import io
from PIL import Image

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QHBoxLayout, QFileDialog, QFormLayout
)
from PyQt5.QtCore import Qt
from typing import Dict, Any, Optional

from ..utils.exporter import Exporter

class ResultPanel(QWidget):
    """结果面板类，用于显示、管理和导出分析结果。"""
    
    KEY_MAP = {
        'count': '总数量',
        'total_area_pixels': '总面积 (像素)',
        'total_area_mm2': '总面积 (mm²)',
        'total_length_pixels': '总长度 (像素)',
        'total_length_mm': '总长度 (mm)',
        'porosity': '孔隙度 (%)',
        'avg_length_mm': '平均长度 (mm)',
        'avg_width_mm': '平均宽度 (mm)',
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_results: Dict[str, Any] = {}
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("分析结果")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setProperty("title", "true")
        main_layout.addWidget(title_label)
        
        # 标签页
        self.tabs = QTabWidget()
        self.summary_widget = QWidget()
        self.summary_layout = QFormLayout(self.summary_widget)
        
        self.details_table = QTableWidget()
        
        self.tabs.addTab(self.summary_widget, "摘要")
        self.tabs.addTab(self.details_table, "详细数据")
        main_layout.addWidget(self.tabs)

        # 导出按钮
        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("导出为CSV")
        self.export_word_btn = QPushButton("导出为Word")
        self.export_csv_btn.setEnabled(False)
        self.export_word_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.export_word_btn)
        main_layout.addLayout(export_layout)

        self.setLayout(main_layout)
        self.clear_results()

    def _connect_signals(self):
        self.export_csv_btn.clicked.connect(self._handle_export_csv)
        self.export_word_btn.clicked.connect(self._handle_export_word)

    def update_analysis_results(self, results: Dict[str, Any]) -> None:
        """根据新的分析结果更新整个面板。"""
        print(f"[DEBUG ResultPanel] Received analysis results: {results}")
        self.current_results = results
        # 直接从顶层 results 字典中获取 'measurements'
        measurements = results.get('measurements', {})
        details = measurements.get('details', [])
        
        self._update_summary_tab(measurements)
        self._update_details_tab(details)
        
        # 仅当结果有效时才启用按钮
        if measurements:
            self.export_csv_btn.setEnabled(True)
            self.export_word_btn.setEnabled(True)
        else:
            self.export_csv_btn.setEnabled(False)
            self.export_word_btn.setEnabled(False)

    def _update_summary_tab(self, measurements: Dict[str, Any]):
        """动态更新摘要信息。"""
        # 清空旧布局
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 动态添加新行
        for key, value in measurements.items():
            if key == 'details': continue # 不在摘要中显示详情
            
            label = self.KEY_MAP.get(key, key)
            
            if isinstance(value, float):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)
                
            self.summary_layout.addRow(QLabel(f"{label}:"), QLabel(value_str))

    def _update_details_tab(self, details: list):
        """更新详细数据表格。"""
        if not details:
            self.details_table.setRowCount(0)
            self.details_table.setColumnCount(0)
            return

        headers = list(details[0].keys())
        self.details_table.setRowCount(len(details))
        self.details_table.setColumnCount(len(headers))
        self.details_table.setHorizontalHeaderLabels([self.KEY_MAP.get(h, h) for h in headers])

        for row, item in enumerate(details):
            for col, key in enumerate(headers):
                value = item.get(key)
                if isinstance(value, float):
                    value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                self.details_table.setItem(row, col, QTableWidgetItem(value_str))
        
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def clear_results(self):
        """清空所有结果并禁用导出按钮。"""
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.summary_layout.addRow(QLabel("请加载图像并开始分析..."))
        self.details_table.setRowCount(0)
        self.details_table.setColumnCount(0)
        self.export_csv_btn.setEnabled(False)
        self.export_word_btn.setEnabled(False)
        self.current_results = {}

    def _handle_export_csv(self):
        """处理导出CSV文件的逻辑。"""
        details_data = self.current_results.get('measurements', {}).get('details')
        if not details_data:
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "保存CSV文件", "", "CSV Files (*.csv)")
        if not filepath: return
        
        try:
            Exporter.export_to_csv(details_data, filepath)
        except Exception as e:
            # 在未来版本中，这里应该显示一个错误对话框
            print(f"导出CSV失败: {e}")

    def _handle_export_word(self):
        """处理导出Word文档的逻辑。"""
        if not self.current_results: return

        filepath, _ = QFileDialog.getSaveFileName(self, "保存Word文档", "", "Word Documents (*.docx)")
        if not filepath: return

        try:
            Exporter.export_to_word(
                summary_data=self.current_results.get('measurements', {}),
                image_data=self.current_results.get('visualization'),
                key_map=self.KEY_MAP,
                filepath=filepath
            )
        except Exception as e:
            print(f"导出Word失败: {e}")

    def update_dpi_info(self, dpi: Optional[tuple]):
        """在加载新图像时更新DPI信息并清空旧结果。"""
        self.clear_results()
        dpi_text = "未知"
        if dpi:
            x_dpi, y_dpi = dpi
            dpi_text = f"{x_dpi}" if x_dpi == y_dpi else f"X={x_dpi}, Y={y_dpi}"
        
        self.summary_layout.addRow(QLabel("图像DPI:"), QLabel(dpi_text))
        self.summary_layout.addRow(QLabel("状态:"), QLabel("请开始分析..."))

# 移除旧的 update_results 方法，因为它被 update_analysis_results 替代了。
# 为了简洁，这里直接注释掉了，但在实际编辑中会删除它。
#
#    def update_results(self, results: Dict[str, Any]) -> None:
#        ...
        