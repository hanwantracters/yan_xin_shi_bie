"""测量对话框组件，用于显示岩石裂缝的测量结果。

该模块提供了一个对话框，用于展示像素长度、DPI和物理长度等测量信息。
"""

from PyQt5.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton,
    QGridLayout,
    QFrame
)
from PyQt5.QtCore import Qt


class MeasurementDialog(QDialog):
    """测量对话框类，用于显示测量结果。
    
    该类创建一个对话框，展示像素长度、DPI和物理长度等信息。
    
    Attributes:
        pixel_len: 像素长度
        dpi: 每英寸点数
        physical_len: 物理长度
    """
    
    def __init__(self, pixel_len: float, dpi: float, physical_len: float, parent=None):
        """初始化测量对话框。
        
        Args:
            pixel_len: 像素长度
            dpi: 每英寸点数
            physical_len: 物理长度(毫米)
            parent: 父窗口对象
        """
        super().__init__(parent)
        
        self.pixel_len = pixel_len
        self.dpi = dpi
        self.physical_len = physical_len
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        # 设置窗口标题
        self.setWindowTitle("测量结果")
        self.setMinimumWidth(300)
        
        # 创建网格布局
        grid_layout = QGridLayout()
        
        # 添加标题行
        title_label = QLabel("裂缝测量结果")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        grid_layout.addWidget(title_label, 0, 0, 1, 2)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        grid_layout.addWidget(separator, 1, 0, 1, 2)
        
        # 添加数据行
        grid_layout.addWidget(QLabel("像素长度:"), 2, 0)
        grid_layout.addWidget(QLabel(f"{self.pixel_len:.2f} 像素"), 2, 1)
        
        grid_layout.addWidget(QLabel("DPI:"), 3, 0)
        grid_layout.addWidget(QLabel(f"{self.dpi:.2f}"), 3, 1)
        
        grid_layout.addWidget(QLabel("物理长度:"), 4, 0)
        grid_layout.addWidget(QLabel(f"{self.physical_len:.2f} 毫米"), 4, 1)
        
        # 添加计算公式说明
        formula_label = QLabel("计算公式: 物理长度 = 像素长度 / DPI * 25.4")
        formula_label.setStyleSheet("color: #666; font-style: italic;")
        grid_layout.addWidget(formula_label, 5, 0, 1, 2)
        
        # 添加确定按钮
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(grid_layout)
        main_layout.addWidget(ok_button, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout) 