"""单位换算引擎模块。

该模块提供像素单位和物理单位（毫米）之间的转换功能，
基于图像的DPI信息进行精确换算。

这是业务逻辑层的核心组件之一，负责确保所有测量结果
能够以物理单位呈现给用户。
"""

from typing import Union, Tuple, List, Dict, Optional, Any
import numpy as np


class UnitConverter:
    """单位换算引擎，负责在像素单位和物理单位之间进行转换。
    
    此类提供从像素到毫米的转换功能，基于图像的DPI信息。
    所有需要单位转换的组件都应使用此类。
    
    Attributes:
        MM_PER_INCH (float): 每英寸的毫米数，固定为25.4
    """
    
    MM_PER_INCH = 25.4
    
    @staticmethod
    def pixels_to_mm(pixels: Union[int, float, np.ndarray], dpi: float) -> Union[float, np.ndarray]:
        """将像素值转换为毫米值。
        
        Args:
            pixels: 要转换的像素值，可以是单个数值或NumPy数组
            dpi: 图像的DPI值（每英寸点数）
            
        Returns:
            转换后的毫米值，保持与输入相同的数据类型
            
        Raises:
            ValueError: 当DPI值小于或等于0时抛出
        """
        if dpi <= 0:
            raise ValueError("DPI值必须大于0")
        return pixels / dpi * UnitConverter.MM_PER_INCH
    
    @staticmethod
    def mm_to_pixels(mm: Union[int, float, np.ndarray], dpi: float) -> Union[float, np.ndarray]:
        """将毫米值转换为像素值。
        
        Args:
            mm: 要转换的毫米值，可以是单个数值或NumPy数组
            dpi: 图像的DPI值（每英寸点数）
            
        Returns:
            转换后的像素值，保持与输入相同的数据类型
            
        Raises:
            ValueError: 当DPI值小于或等于0时抛出
        """
        if dpi <= 0:
            raise ValueError("DPI值必须大于0")
        return mm * dpi / UnitConverter.MM_PER_INCH
    
    @staticmethod
    def convert_point(point: Tuple[int, int], dpi: float) -> Tuple[float, float]:
        """将像素坐标点转换为毫米坐标点。
        
        Args:
            point: 像素坐标点，格式为(x, y)
            dpi: 图像的DPI值
            
        Returns:
            毫米坐标点，格式为(x_mm, y_mm)
            
        Raises:
            ValueError: 当DPI值小于或等于0时抛出
        """
        x, y = point
        x_mm = UnitConverter.pixels_to_mm(x, dpi)
        y_mm = UnitConverter.pixels_to_mm(y, dpi)
        return (x_mm, y_mm)
    
    @staticmethod
    def convert_distance(pixel_distance: float, dpi: float) -> float:
        """将像素距离转换为毫米距离。
        
        Args:
            pixel_distance: 像素单位的距离
            dpi: 图像的DPI值
            
        Returns:
            毫米单位的距离
            
        Raises:
            ValueError: 当DPI值小于或等于0时抛出
        """
        return UnitConverter.pixels_to_mm(pixel_distance, dpi)
    
    @staticmethod
    def convert_area(pixel_area: float, dpi: float) -> float:
        """将像素面积转换为平方毫米面积。
        
        Args:
            pixel_area: 像素单位的面积
            dpi: 图像的DPI值
            
        Returns:
            平方毫米单位的面积
            
        Raises:
            ValueError: 当DPI值小于或等于0时抛出
        """
        if dpi <= 0:
            raise ValueError("DPI值必须大于0")
        # 面积转换需要考虑平方关系
        mm_per_pixel = UnitConverter.MM_PER_INCH / dpi
        return pixel_area * (mm_per_pixel ** 2) 