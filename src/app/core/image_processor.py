"""该模块包含所有核心的图像处理功能。

它负责从图像中识别裂缝，并计算其相关参数。
这是数据处理层的核心部分。

Attributes:
    DEFAULT_GAUSSIAN_KERNEL (tuple): 高斯滤波的默认核大小。
"""

import cv2
import numpy as np
from PIL import Image
import os
from typing import Tuple, Optional

class ImageProcessor:
    """图像处理器类，包含所有图像处理相关的方法。"""
    
    def __init__(self):
        """初始化图像处理器。"""
        self.image = None
        self.dpi = None
    
    def load_image(self, file_path: str) -> Tuple[np.ndarray, Optional[Tuple[float, float]]]:
        """加载图像并获取DPI信息。
        
        使用OpenCV加载图像数据，使用PIL获取DPI信息。
        
        Args:
            file_path (str): 图像文件的路径。
            
        Returns:
            tuple: 包含以下元素的元组:
                - image (numpy.ndarray): OpenCV格式的图像数据
                - dpi (tuple): 图像的DPI信息，格式为(x_dpi, y_dpi)，如果无法获取则为None
                
        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件格式不支持
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        # 检查文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
            raise ValueError(f"不支持的文件格式: {ext}")
            
        # 使用OpenCV加载图像
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError(f"无法加载图像: {file_path}")
            
        # 使用PIL获取DPI信息
        dpi = None
        try:
            with Image.open(file_path) as pil_image:
                dpi_info = pil_image.info.get('dpi')
                if dpi_info and isinstance(dpi_info, tuple) and len(dpi_info) == 2:
                    # 确保DPI值是有效的浮点数
                    x_dpi, y_dpi = float(dpi_info[0]), float(dpi_info[1])
                    if x_dpi > 0 and y_dpi > 0:
                        dpi = (x_dpi, y_dpi)
        except Exception as e:
            print(f"获取DPI信息时出错: {str(e)}")
            
        # 更新实例变量
        self.image = image
        self.dpi = dpi
        
        return image, dpi
        
    def process_image(self, image):
        """处理图像以识别裂缝。
        
        Args:
            image (numpy.ndarray): 输入图像。
            
        Returns:
            numpy.ndarray: 处理后的图像。
        """
        # 实现图像处理逻辑
        pass 