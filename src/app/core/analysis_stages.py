"""分析阶段定义模块。

该模块定义了图像处理的各个分析阶段，用于标识处理流程中的不同步骤。
"""

from enum import Enum, auto

class AnalysisStage(Enum):
    """定义图像分析的各个处理阶段。"""
    ORIGINAL = auto()  # 原始图像
    GRAYSCALE = auto()  # 灰度图像
    THRESHOLD = auto()  # 阈值分割
    MORPHOLOGY = auto()  # 形态学处理
    DETECTION = auto()  # 裂缝检测
    MEASUREMENT = auto()  # 测量结果
    
    @staticmethod
    def get_stage_name(stage):
        """获取分析阶段的显示名称。
        
        Args:
            stage (AnalysisStage): 枚举值
            
        Returns:
            str: 该阶段的中文显示名称
        """
        names = {
            AnalysisStage.ORIGINAL: "原始图像",
            AnalysisStage.GRAYSCALE: "灰度处理",
            AnalysisStage.THRESHOLD: "阈值分割",
            AnalysisStage.MORPHOLOGY: "形态学处理",
            AnalysisStage.DETECTION: "裂缝检测",
            AnalysisStage.MEASUREMENT: "结果测量"
        }
        return names.get(stage, "未知阶段") 