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
    
    # 定义默认的高斯滤波核大小
    DEFAULT_GAUSSIAN_KERNEL = (5, 5)
    
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
    
    def convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """将彩色图像转换为灰度图。
        
        Args:
            image (numpy.ndarray): 输入的彩色图像。
            
        Returns:
            numpy.ndarray: 转换后的灰度图像。
        """
        # 检查图像是否已经是灰度图
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            return image
            
        # 将彩色图像转换为灰度图
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray_image
    
    def apply_gaussian_blur(self, image: np.ndarray, kernel_size: Tuple[int, int] = None) -> np.ndarray:
        """对图像应用高斯滤波以减少噪点。
        
        Args:
            image (numpy.ndarray): 输入图像，可以是彩色图像或灰度图像。
            kernel_size (tuple, optional): 高斯核大小，格式为(width, height)。
                如果为None，则使用默认值DEFAULT_GAUSSIAN_KERNEL。
                
        Returns:
            numpy.ndarray: 应用高斯滤波后的图像。
        """
        # 如果未指定核大小，则使用默认值
        if kernel_size is None:
            kernel_size = self.DEFAULT_GAUSSIAN_KERNEL
            
        # 应用高斯滤波
        blurred_image = cv2.GaussianBlur(image, kernel_size, 0)
        return blurred_image
        
    def process_image(self, image: np.ndarray) -> np.ndarray:
        """处理图像以识别裂缝。
        
        将图像转换为灰度图，并应用高斯滤波减少噪点。
        这是图像处理流程的第一步。
        
        Args:
            image (numpy.ndarray): 输入图像。
            
        Returns:
            numpy.ndarray: 处理后的图像（灰度图，已去噪）。
        """
        # 1. 将图像转换为灰度图
        gray_image = self.convert_to_grayscale(image)
        
        # 2. 应用高斯滤波减少噪点
        processed_image = self.apply_gaussian_blur(gray_image)
        
        return processed_image

    def apply_global_threshold(self, image: np.ndarray, threshold_value: int = 128) -> np.ndarray:
        """应用全局阈值分割。
        
        Args:
            image: 输入的灰度图像
            threshold_value: 阈值 (0-255)
            
        Returns:
            二值图像
        """
        _, binary = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)
        return binary

    def apply_adaptive_gaussian_threshold(self, image: np.ndarray, block_size: int = 11, c: int = 2) -> np.ndarray:
        """应用自适应高斯阈值分割。
        
        Args:
            image: 输入的灰度图像
            block_size: 局部区域大小，必须是奇数
            c: 从平均值或加权平均值中减去的常数
            
        Returns:
            二值图像
        """
        # 确保block_size是奇数
        if block_size % 2 == 0:
            block_size += 1
            
        binary = cv2.adaptiveThreshold(
            image, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            block_size, 
            c
        )
        return binary

    def apply_otsu_threshold(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """应用Otsu阈值分割。
        
        Args:
            image: 输入的灰度图像
            
        Returns:
            tuple: (二值图像, 计算出的最优阈值)
        """
        otsu_thresh, binary = cv2.threshold(
            image, 
            0,  # 初始阈值，会被Otsu方法忽略
            255, 
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binary, int(otsu_thresh)

    def apply_threshold(self, image: np.ndarray, method: str = 'global', params: dict = None) -> dict:
        """应用阈值分割，将灰度图像转换为二值图像。
        
        Args:
            image: 输入的灰度图像
            method: 阈值方法，可选值: 'global', 'adaptive_gaussian', 'otsu'
            params: 方法参数字典，根据不同方法需要不同的参数
                - global: {'threshold': 阈值(0-255)}
                - adaptive_gaussian: {'block_size': 块大小, 'c': 常数}
                - otsu: 不需要参数
            
        Returns:
            dict: 包含以下键的字典:
                - 'binary': 二值图像
                - 'threshold': 使用的阈值(对于otsu方法)
                - 'method': 使用的方法名称
                - 'params': 使用的参数
        """
        if params is None:
            params = {}
            
        result = {
            'binary': None,
            'threshold': None,
            'method': method,
            'params': params
        }
        
        processed_image = self.process_image(image)
        
        if method == 'global':
            threshold = params.get('threshold', 128)
            result['binary'] = self.apply_global_threshold(processed_image, threshold)
            result['threshold'] = threshold
            
        elif method == 'adaptive_gaussian':
            block_size = params.get('block_size', 11)
            c = params.get('c', 2)
            result['binary'] = self.apply_adaptive_gaussian_threshold(processed_image, block_size, c)
            
        elif method == 'otsu':
            binary, otsu_thresh = self.apply_otsu_threshold(processed_image)
            result['binary'] = binary
            result['threshold'] = otsu_thresh
        
        print("阈值分割结果:", result);
        return result 