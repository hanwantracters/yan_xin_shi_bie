"""通用结果对话框基类。

该模块定义了一个可扩展的对话框基类，用于显示各种分析结果。
它内置了状态管理（加载、就绪、空）和通用预览标签页的创建逻辑。
"""

from typing import Dict, Any

from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QTabWidget,
    QLabel,
    QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import cv2

from ...core.controller import Controller
from ...utils.constants import PreviewState, ResultKeys, StageKeys

class BaseResultDialog(QDialog):
    """
    所有结果对话框的基类。

    该类提供了核心功能：
    - 一个用于在状态消息和标签页之间切换的 QStackedWidget。
    - 一个用于显示预览图像的 QTabWidget。
    - 一个公共的 `update_content` 方法来驱动UI状态变化。
    - 自动创建所有分析器共享的通用预览标签页。
    """
    def __init__(self, controller: Controller, parent: QWidget = None):
        super().__init__(parent)
        self.controller = controller
        self.tabs: Dict[str, QLabel] = {} # 用于存储对标签页图像控件的引用

        self._init_ui()
        self._create_common_preview_tabs()
        self._populate_tabs()

    def _init_ui(self):
        """初始化UI组件和布局。"""
        self.setMinimumSize(600, 480)
        self.setWindowTitle("分析结果")
        self.setModal(False) # 非模态，允许与主窗口交互

        main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # 状态标签 (页面 0)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        font = self.status_label.font(); font.setPointSize(16); self.status_label.setFont(font)
        self.stacked_widget.addWidget(self.status_label)

        # 标签页容器 (页面 1)
        self.tab_widget = QTabWidget()
        self.stacked_widget.addWidget(self.tab_widget)

    def update_content(self, state_payload: Dict[str, Any]):
        """
        核心公共API，根据控制器发送的状态和数据负载更新对话框内容。
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        state = state_payload.get('state')
        payload = state_payload.get('payload', {})
        
        if state in [PreviewState.LOADING, PreviewState.EMPTY, PreviewState.ERROR]:
            self.status_label.setText(str(payload))
            self.stacked_widget.setCurrentWidget(self.status_label)
        elif state == PreviewState.READY:
            self.stacked_widget.setCurrentWidget(self.tab_widget)
            self._update_all_tabs(payload)
            
        QApplication.restoreOverrideCursor()

    def _create_common_preview_tabs(self):
        """创建所有结果窗口共享的通用预览标签页。"""
        common_tabs_info = {
            StageKeys.ORIGINAL.value: "原图",
            StageKeys.GRAY.value: "灰度图",
            StageKeys.BINARY.value: "二值图",
            StageKeys.MORPH.value: "形态学处理",
        }
        for key, title in common_tabs_info.items():
            image_label = QLabel(); image_label.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(image_label, title)
            self.tabs[key] = image_label

    def _update_all_tabs(self, payload: Dict[str, Any]):
        """使用数据负载中的图像更新所有标签页。"""
        previews = payload.get(ResultKeys.PREVIEWS.value, {})
        # 将顶层的可视化结果也添加到previews中，方便统一处理
        if ResultKeys.VISUALIZATION.value in payload:
            previews[ResultKeys.VISUALIZATION.value] = payload[ResultKeys.VISUALIZATION.value]
            
        for key, image_label in self.tabs.items():
            if key in previews:
                self._set_image_on_label(image_label, previews[key])

    @staticmethod
    def _set_image_on_label(label: QLabel, image_data: np.ndarray):
        """将Numpy数组格式的图像设置到QLabel上。"""
        if image_data is None: return
        
        height, width = image_data.shape[:2]
        
        if len(image_data.shape) == 2:
            qimg = QImage(image_data.data, width, height, width, QImage.Format_Grayscale8)
        else:
            rgb_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb_image.data, width, height, 3 * width, QImage.Format_RGB888)
            
        pixmap = QPixmap.fromImage(qimg)
        label.setPixmap(pixmap.scaled(
            label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def _populate_tabs(self):
        """
        抽象方法，由子类实现以添加其特有的标签页。
        """
        raise NotImplementedError("Subclasses must implement '_populate_tabs' to add their specific tabs.") 