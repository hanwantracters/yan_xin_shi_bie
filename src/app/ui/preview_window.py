"""预览窗口组件，用于显示图像和处理结果。

该模块提供了一个图像显示区域，用于预览原始图像和处理后的图像。
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
import cv2

from ..core.analysis_stages import AnalysisStage


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
            
            qimg = None # 初始化qimg
            
            # 根据图像通道数选择合适的QImage格式
            if len(image.shape) == 2:  # 灰度图像
                # 确保数据在内存中是连续的
                contiguous_image = np.ascontiguousarray(image)
                qimg = QImage(contiguous_image.data, width, height, width, QImage.Format_Grayscale8)
            elif len(image.shape) == 3 and image.shape[2] == 3:  # 彩色图像
                # OpenCV图像是BGR格式，需要转换为RGB
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # 确保数据在内存中是连续的
                contiguous_image = np.ascontiguousarray(rgb_image)
                bytes_per_line = 3 * width
                qimg = QImage(contiguous_image.data, width, height, bytes_per_line, QImage.Format_RGB888)

            if qimg:
                pixmap = QPixmap.fromImage(qimg)
            else:
                pixmap = None # 图像格式不受支持
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
            
    def clear_image(self):
        """清除显示的图像，并重置标签文本。"""
        self.image_label.clear()
        self.image_label.setText("请加载图像...")
            
    def display_image(self, image):
        """显示图像，是update_image的别名。
        
        Args:
            image: 可以是QImage、QPixmap、numpy数组或文件路径
        """
        self.update_image(image) 

    def update_preview(self, analysis_results):
        """更新预览窗口以显示分析结果。
        
        Args:
            analysis_results: 分析结果字典
        """
        print("接收到的分析结果阶段:", [stage.name for stage in analysis_results.keys()])
        for stage in analysis_results:
            print(f"阶段{stage.name}结果包含字段:", list(analysis_results[stage].keys()))
        
        # 获取阈值分割结果并显示
        threshold_result = analysis_results.get(AnalysisStage.THRESHOLD)
        if threshold_result and 'binary' in threshold_result:
            # 显示二值图像
            self.update_image(threshold_result['binary'])
        else:
            self.image_label.setText("无有效的阈值分割结果") 