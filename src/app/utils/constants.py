"""应用程序范围内的常量定义。

该模块定义了所有跨模块通信时使用的枚举和常量，
以避免使用"魔术字符串"，增强代码的可读性和可维护性。
"""

from enum import Enum, auto

class ResultKeys(Enum):
    """分析结果字典的键名。
    
    中文翻译:
    - VISUALIZATION: 可视化结果
    - MEASUREMENTS: 测量数据
    - PREVIEWS: 预览图像
    """
    VISUALIZATION = 'visualization'
    MEASUREMENTS = 'measurements'
    PREVIEWS = 'previews'

class StageKeys(Enum):
    """预览阶段的名称。"""
    ORIGINAL = 'original'
    GRAY = 'gray'
    BINARY = 'binary'
    MORPH = 'morph'
    DETECTION = 'detection'

class PreviewState(Enum):
    """预览窗口状态的类型。"""
    LOADING = auto()
    READY = auto()
    EMPTY = auto()
    ERROR = auto() 