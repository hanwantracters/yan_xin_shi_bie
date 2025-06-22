"""分析预览窗口，用于显示各个分析阶段的结果。

该窗口提供标签页，让用户可以切换查看不同分析阶段的结果。
"""

from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtCore import Qt
import numpy as np

from .preview_window import PreviewWindow
from ..core.analysis_stages import AnalysisStage


class StagePreviewPanel(QWidget):
    """单个阶段的预览面板。
    
    包含图像预览区域和参数信息显示区域。
    
    Attributes:
        preview: 图像预览窗口
        param_content: 参数信息文本编辑器
    """
    
    def __init__(self, parent=None):
        """初始化阶段预览面板。
        
        Args:
            parent: 父窗口对象
        """
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建预览窗口
        self.preview = PreviewWindow()
        layout.addWidget(self.preview)
        
        # 创建参数标签
        param_label = QLabel("参数信息")
        param_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(param_label)
        
        # 创建参数内容显示
        self.param_content = QTextEdit()
        self.param_content.setReadOnly(True)
        self.param_content.setMaximumHeight(120)
        layout.addWidget(self.param_content)
        
        self.setLayout(layout)


class AnalysisPreviewWindow(QMainWindow):
    """分析预览窗口类。
    
    提供标签页界面，展示各个分析阶段的结果。
    
    Attributes:
        tab_widget: 标签页组件
        preview_panels: 各阶段预览面板的字典
    """
    
    def __init__(self, parent=None):
        """初始化分析预览窗口。
        
        Args:
            parent: 父窗口对象
        """
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件和布局。"""
        # 设置窗口属性
        self.setWindowTitle("分析结果预览")
        self.resize(600, 500)
        
        # 创建标签页组件
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # 存储各阶段预览面板
        self.preview_panels = {}
        
        # 为每个分析阶段创建标签页
        stages = [
            AnalysisStage.ORIGINAL,
            AnalysisStage.GRAYSCALE,
            AnalysisStage.THRESHOLD,
            AnalysisStage.MORPHOLOGY,
            AnalysisStage.DETECTION,
            AnalysisStage.MEASUREMENT
        ]
        
        for stage in stages:
            # 创建阶段预览面板
            panel = StagePreviewPanel()
            
            # 获取阶段名称
            stage_name = AnalysisStage.get_stage_name(stage)
            
            # 添加到标签页
            self.tab_widget.addTab(panel, stage_name)
            
            # 存储到字典
            self.preview_panels[stage] = panel
    
    def update_stage(self, stage: AnalysisStage, image: 'np.ndarray', params: dict):
        """更新指定分析阶段的预览。

        Args:
            stage (AnalysisStage): 要更新的分析阶段。
            image (np.ndarray): 要显示的图像。
            params (dict): 与该阶段相关的参数字典。
        """
        if stage in self.preview_panels:
            panel = self.preview_panels[stage]
            panel.preview.display_image(image)
            
            # 格式化参数并显示
            param_text = "\n".join([f"{key}: {value}" for key, value in params.items()])
            panel.param_content.setText(param_text if param_text else "无参数信息")

    def clear_all(self):
        """清除所有预览面板的内容。"""
        for panel in self.preview_panels.values():
            panel.preview.clear_image()
            panel.param_content.clear()
            
    def _format_parameters(self, result_data):
        """格式化参数信息。
        
        Args:
            result_data: 分析结果数据
            
        Returns:
            str: 格式化的参数信息文本
        """
        # 排除图像数据
        exclude_keys = ['image', 'binary']
        param_lines = []
        
        for key, value in result_data.items():
            if key not in exclude_keys:
                # 对于method和params等常见键进行特殊处理
                if key == 'method':
                    param_lines.append(f"方法: {value}")
                elif key == 'params' and isinstance(value, dict):
                    for param_key, param_value in value.items():
                        param_lines.append(f"{param_key}: {param_value}")
                elif key == 'threshold':
                    param_lines.append(f"阈值: {value}")
                else:
                    param_lines.append(f"{key}: {value}")
        
        return "\n".join(param_lines) if param_lines else "无参数信息" 