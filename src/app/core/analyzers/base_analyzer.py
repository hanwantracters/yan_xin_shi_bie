"""分析器抽象基类定义。

该模块定义了所有分析策略模块必须遵循的抽象基类 (ABC)。
它规定了分析器的统一接口，确保了Controller可以与任何具体的分析器进行交互。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

import numpy as np
from PyQt5.QtWidgets import QWidget

class BaseAnalyzer(ABC):
    """
    抽象基类，定义了所有分析器的标准接口。
    """

    @abstractmethod
    def get_name(self) -> str:
        """返回一个用于UI显示的、人类可读的分析名称。
        
        例如: "裂缝分析"。
        
        Returns:
            str: 分析模式的名称。
        """
        pass

    @abstractmethod
    def get_id(self) -> str:
        """返回一个程序内部使用的、唯一的字符串ID。
        
        例如: "fracture_analysis"。
        
        Returns:
            str: 分析模式的唯一ID。
        """
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """返回一个包含该分析模式所需全部默认参数的字典。
        
        Returns:
            Dict[str, Any]: 包含默认参数的字典。
        """
        pass

    @abstractmethod
    def run_analysis(self, image: np.ndarray, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整的分析流程。
        
        Args:
            image (np.ndarray): 待分析的原始图像。
            params (Dict[str, Any]): 用于分析的参数字典。

        Returns:
            Dict[str, Any]: 一个包含结果的字典，通常应包括
                             可视化图像 ('visualization') 和测量数据 ('measurements')。
        """
        pass 