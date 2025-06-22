"""样式表管理模块，提供统一的UI样式控制。

该模块负责集中管理应用程序的样式表，包括字体大小、颜色等UI元素的样式。
通过这种方式，可以确保整个应用程序的UI风格保持一致。
"""

from typing import Dict, Optional, List
from PyQt5.QtWidgets import QApplication, QWidget


class StyleManager:
    """样式表管理类，提供统一的样式控制功能。
    
    该类使用Qt样式表(QSS)来统一管理应用程序中各种UI控件的样式，
    特别是字体大小设置。
    
    Attributes:
        _base_font_size (int): 基础字体大小，单位为像素
        _font_scale_factor (float): 字体缩放因子，用于整体调整字体大小
    """
    
    def __init__(self, base_font_size: int = 12, font_scale_factor: float = 1.0):
        """初始化样式管理器。
        
        Args:
            base_font_size (int): 基础字体大小，单位为像素，默认为12
            font_scale_factor (float): 字体缩放因子，默认为1.0
        """
        self._base_font_size = base_font_size
        self._font_scale_factor = font_scale_factor
        self._style_sheets: Dict[str, str] = {}
        
    def set_font_scale_factor(self, scale_factor: float) -> None:
        """设置字体缩放因子。
        
        Args:
            scale_factor (float): 新的字体缩放因子
        """
        self._font_scale_factor = scale_factor
        
    def get_scaled_font_size(self) -> int:
        """获取经过缩放的字体大小。
        
        Returns:
            int: 经过缩放的字体大小，单位为像素
        """
        return int(self._base_font_size * self._font_scale_factor)
    
    def generate_button_style(self) -> str:
        """生成按钮的样式表。
        
        Returns:
            str: 按钮的样式表字符串
        """
        font_size = self.get_scaled_font_size()
        return f"""
            QPushButton {{
                font-size: {font_size}px;
                padding: 5px;
            }}
        """
    
    def generate_label_style(self) -> str:
        """生成标签的样式表。
        
        Returns:
            str: 标签的样式表字符串
        """
        font_size = self.get_scaled_font_size()
        return f"""
            QLabel {{
                font-size: {font_size}px;
            }}
        """
    
    def generate_text_edit_style(self) -> str:
        """生成文本编辑器的样式表。
        
        Returns:
            str: 文本编辑器的样式表字符串
        """
        font_size = self.get_scaled_font_size()
        return f"""
            QTextEdit {{
                font-size: {font_size}px;
            }}
        """
    
    def generate_title_style(self) -> str:
        """生成标题的样式表。
        
        Returns:
            str: 标题的样式表字符串
        """
        font_size = int(self.get_scaled_font_size() * 1.2)  # 标题字体稍大
        return f"""
            QLabel[title="true"] {{
                font-size: {font_size}px;
                font-weight: bold;
            }}
        """
    
    def generate_complete_style(self) -> str:
        """生成完整的样式表。
        
        将所有样式组合成一个完整的样式表字符串。
        
        Returns:
            str: 完整的样式表字符串
        """
        styles = [
            self.generate_button_style(),
            self.generate_label_style(),
            self.generate_text_edit_style(),
            self.generate_title_style()
        ]
        return "\n".join(styles)
    
    def apply_style_to_widget(self, widget: QWidget) -> None:
        """将样式应用到指定的控件。
        
        Args:
            widget (QWidget): 要应用样式的控件
        """
        widget.setStyleSheet(self.generate_complete_style())
    
    def apply_style_to_application(self) -> None:
        """将样式应用到整个应用程序。"""
        QApplication.instance().setStyleSheet(self.generate_complete_style())


# 创建全局样式管理器实例，默认字体大小为14px，缩放因子为1.5（增大50%）
style_manager = StyleManager(base_font_size=18, font_scale_factor=1.5) 