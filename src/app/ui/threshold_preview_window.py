"""阈值分割预览窗口组件，用于显示二值化后的图像和相关信息。
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from .preview_window import PreviewWindow

class ThresholdPreviewWindow(PreviewWindow):
    """阈值分割预览窗口类。
    
    继承自PreviewWindow，增加了显示阈值方法和参数信息的功能。
    
    Attributes:
        info_label: QLabel对象，用于显示阈值信息
    """
    
    def __init__(self, parent=None):
        """初始化阈值预览窗口。
        
        Args:
            parent: 父窗口对象
        """
        super().__init__(parent)
        self.setWindowTitle("阈值分割预览")
        self._init_additional_ui()
        
    def _init_additional_ui(self):
        """初始化额外的信息显示UI。"""
        self.info_label = QLabel("方法: - | 参数: -")
        self.info_label.setAlignment(Qt.AlignCenter)
        
        # 将信息标签添加到布局中
        self.layout().addWidget(self.info_label)
        
    def update_preview(self, binary_image, method_info: str):
        """更新预览图像和信息。
        
        Args:
            binary_image: 二值图像 (numpy.ndarray)
            method_info: 阈值方法和参数信息 (str)
        """
        self.display_image(binary_image)
        self.info_label.setText(method_info) 