"""结果面板组件，用于显示岩石裂缝分析的结果。

该模块提供了一个文本区域，用于展示分析结果，包括裂缝数量、
总面积和总长度等信息。
"""

from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from typing import Dict, Any


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
        
        # 创建文本编辑器
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)  # 设置为只读
        
        # 设置默认文本
        self.result_text.setText("请加载图像并开始分析...")
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.result_text)
        
        self.setLayout(main_layout)
        
    def update_results(self, results: Dict[str, Any]) -> None:
        """更新分析结果。
        
        接收分析结果字典并更新到文本编辑器中显示。
        
        Args:
            results: 包含分析结果的字典，可能包含以下键:
                    - count: 裂缝数量
                    - total_area_mm2: 总面积(平方毫米)
                    - total_length_mm: 总长度(毫米)
        """
        # 清空当前文本
        self.result_text.clear()
        
        # 如果结果为空，显示提示信息
        if not results:
            self.result_text.setText("未检测到有效结果。")
            return
        
        # 构建结果文本
        result_str = "分析结果:\n\n"
        
        if 'count' in results:
            result_str += f"裂缝数量: {results['count']}\n"
            
        if 'total_area_mm2' in results:
            result_str += f"总面积: {results['total_area_mm2']:.2f} 平方毫米\n"
            
        if 'total_length_mm' in results:
            result_str += f"总长度: {results['total_length_mm']:.2f} 毫米\n"
        
        # 添加其他可能的结果项
        for key, value in results.items():
            if key not in ['count', 'total_area_mm2', 'total_length_mm']:
                result_str += f"{key}: {value}\n"
        
        # 更新文本
        self.result_text.setText(result_str) 