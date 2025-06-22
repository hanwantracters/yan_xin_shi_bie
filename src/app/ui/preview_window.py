"""预览窗口组件，用于显示图像和处理结果。

该模块提供了一个图像显示区域，用于预览原始图像和处理后的图像。
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import numpy as np


class PreviewWindow(QWidget):
    """预览窗口类，用于显示图像。
    
    该类包含一个QLabel用于显示图像，支持更新显示不同的图像。
    
    Attributes:
        image_label: QLabel对象，用于显示图像
    """
    
    def __init__(self, parent=None):
        """初始化预览窗口。
        
        Args:
            parent: 父窗口对象
        """
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        # 创建图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)  # 设置最小尺寸
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        self.image_label.setText("请加载图像...")
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        
        self.setLayout(main_layout)
        
    def update_image(self, image):
        """更新显示的图像。
        
        Args:
            image: 可以是QImage、QPixmap、numpy数组或文件路径
        """
        if image is None:
            self.image_label.setText("无图像可显示")
            return
            
        pixmap = None
        
        # 处理不同类型的输入
        if isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        elif isinstance(image, QPixmap):
            pixmap = image
        elif isinstance(image, np.ndarray):
            # 将numpy数组转换为QImage
            height, width = image.shape[:2]
            
            # 根据图像通道数选择合适的QImage格式
            if len(image.shape) == 2:  # 灰度图像
                qimg = QImage(image.data, width, height, width, QImage.Format_Grayscale8)
            else:  # 彩色图像
                bytes_per_line = 3 * width
                qimg = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                
            pixmap = QPixmap.fromImage(qimg)
        elif isinstance(image, str):  # 假设是文件路径
            pixmap = QPixmap(image)
            
        if pixmap and not pixmap.isNull():
            # 调整图像大小以适应标签，保持纵横比
            pixmap = pixmap.scaled(
                self.image_label.width(), 
                self.image_label.height(),
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("图像加载失败") 