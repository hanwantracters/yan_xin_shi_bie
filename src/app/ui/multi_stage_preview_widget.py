"""简化后的单一图像预览窗口组件。

该模块仅提供一个用于显示单张图像的QLabel，
并提供简单的公共接口来更新或清除图像。
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import cv2


class MultiStagePreviewWidget(QWidget):
    """一个简单的、用于显示单张图像的预览组件。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI组件。"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel("请加载图像以开始分析")
        self.image_label.setAlignment(Qt.AlignCenter)
        font = self.image_label.font()
        font.setPointSize(16)
        self.image_label.setFont(font)
        
        self.main_layout.addWidget(self.image_label)

    def show_image(self, image_data: np.ndarray):
        """核心公共API，在标签上显示给定的图像。"""
        if image_data is None:
            self.clear()
            return
            
        height, width = image_data.shape[:2]
        
        if len(image_data.shape) == 2:
            qimg = QImage(image_data.data, width, height, width, QImage.Format_Grayscale8)
        else:
            rgb_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb_image.data, width, height, 3 * width, QImage.Format_RGB888)
            
        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))

    def clear(self):
        """清空预览并显示初始提示信息。"""
        self.image_label.clear()
        self.image_label.setText("请加载图像以开始分析") 