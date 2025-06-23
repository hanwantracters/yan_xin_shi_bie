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
    
    def update_stage_preview(self, stage: AnalysisStage, result_data: dict):
        """更新指定分析阶段的预览。

        此方法会从结果字典中自动提取图像和参数进行显示。

        Args:
            stage (AnalysisStage): 要更新的分析阶段。
            result_data (dict): 包含该阶段结果的完整字典。
        """
        print(f"[AnalysisPreviewWindow] Updating preview for stage: {stage.name}")
        
        # DEBUG: 打印阶段的结果数据键
        print(f"[DEBUG] {stage.name} result_data keys: {list(result_data.keys() if result_data else [])}")
        
        if stage not in self.preview_panels:
            return

        panel = self.preview_panels[stage]
        
        # 1. 提取图像
        image = None
        if 'image' in result_data:
            image = result_data['image']
            print(f"[DEBUG] {stage.name} has 'image' data: {type(image)}, shape: {getattr(image, 'shape', 'unknown')}")
        elif 'binary' in result_data:
            image = result_data['binary']
            print(f"[DEBUG] {stage.name} has 'binary' data: {type(image)}, shape: {getattr(image, 'shape', 'unknown')}")
        else:
            print(f"[DEBUG] {stage.name} has no image data")
        
        if image is not None:
            panel.preview.display_image(image)
        else:
            # 如果没有图像，可以清空或显示提示
            panel.preview.clear_image()

        # 2. 格式化并显示参数
        param_text = self._format_parameters(stage, result_data)
        panel.param_content.setText(param_text)

    def clear_all(self):
        """清除所有预览面板的内容。"""
        for panel in self.preview_panels.values():
            panel.preview.clear_image()
            panel.param_content.clear()
            
    def _format_parameters(self, stage: AnalysisStage, result_data: dict) -> str:
        """根据阶段和结果数据，智能地格式化参数信息。
        
        Args:
            stage (AnalysisStage): 当前分析阶段。
            result_data (dict): 分析结果数据。
            
        Returns:
            str: 格式化的参数信息文本。
        """
        if not result_data:
            return "无参数信息"

        param_lines = []

        # DEBUG: 打印格式化参数的输入
        print(f"[DEBUG] Formatting parameters for stage: {stage.name}")
        print(f"[DEBUG] result_data type: {type(result_data)}")

        # 特殊处理测量阶段，只显示摘要
        if stage == AnalysisStage.MEASUREMENT:
            param_lines.append(f"裂缝数量: {result_data.get('fracture_count', result_data.get('count', 'N/A'))}")
            param_lines.append(f"总面积 (mm²): {result_data.get('total_area_mm2', 'N/A')}")
            param_lines.append(f"总长度 (mm): {result_data.get('total_length_mm', 'N/A')}")
            if result_data.get('details') or result_data.get('detailed_fractures'):
                 param_lines.append(f"\n详情请在主面板查看。")
            return "\n".join(param_lines)
        
        # 特殊处理检测阶段，显示裂缝统计信息
        if stage == AnalysisStage.DETECTION:
            if 'fractures' in result_data:
                fractures = result_data.get('fractures', [])
                param_lines.append(f"检测到的裂缝数量: {len(fractures)}")
                if len(fractures) > 0:
                    param_lines.append(f"裂缝详细信息请在主面板查看。")
                else:
                    param_lines.append("未检测到任何裂缝。")
                return "\n".join(param_lines)

        # 通用格式化逻辑
        def format_dict(d, indent=0):
            lines = []
            exclude_keys = ['image', 'binary', 'details', 'contour', 'centroid_pixels']
            
            for key, value in d.items():
                if key in exclude_keys:
                    continue
                
                prefix = "  " * indent
                if isinstance(value, dict) and value:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(format_dict(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
            return lines

        param_lines = format_dict(result_data)
        
        return "\n".join(param_lines) if param_lines else "无参数信息" 