"""多阶段预览窗口组件。

该模块提供了一个可以并排显示多个分析阶段图像的UI组件，
并能根据控制器发出的状态（加载中、错误、空、就绪）显示不同内容。
"""
from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout, 
    QGridLayout, 
    QScrollArea, 
    QApplication,
    QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import cv2

from ..utils.constants import PreviewState, ResultKeys, StageKeys

class _SinglePreview(QWidget):
    """内部使用的小型单图像预览窗口，带标题。"""
    def __init__(self, title: str, image: np.ndarray, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 150)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        
        self.set_image(image)

    def set_image(self, image_data: np.ndarray):
        """将Numpy数组转换为Pixmap并显示。"""
        if image_data is None:
            return
            
        height, width = image_data.shape[:2]
        
        if len(image_data.shape) == 2:
            qimg = QImage(image_data.data, width, height, width, QImage.Format_Grayscale8)
        else:
            rgb_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
            qimg = QImage(rgb_image.data, width, height, 3 * width, QImage.Format_RGB888)
            
        pixmap = QPixmap.fromImage(qimg)
        # 动态调整以适应可用空间
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))

class MultiStagePreviewWidget(QWidget):
    """多阶段预览组件，使用网格布局显示所有预览。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 状态标签，用于显示Loading, Error, Empty等信息
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        font = self.status_label.font()
        font.setPointSize(16)
        self.status_label.setFont(font)
        
        # 滚动区域，用于容纳网格布局
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 网格布局的容器
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll_area.setWidget(self.grid_container)

        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.scroll_area)
        
        self.clear_all()

    def display_state(self, state_payload: dict):
        """核心公共API，根据状态更新UI。"""
        print(f"[DEBUG PreviewWidget] Received state payload: {state_payload}") # 调试打印
        state = state_payload.get('state')
        payload = state_payload.get('payload')

        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        if state == PreviewState.LOADING:
            self.status_label.setText("正在分析中，请稍候...")
            self.status_label.setVisible(True)
            self.scroll_area.setVisible(False)
        elif state == PreviewState.ERROR:
            self.status_label.setText(f"错误: {payload}")
            self.status_label.setVisible(True)
            self.scroll_area.setVisible(False)
        elif state == PreviewState.EMPTY:
            self.status_label.setText(str(payload))
            self.status_label.setVisible(True)
            self.scroll_area.setVisible(False)
        elif state == PreviewState.READY:
            self.status_label.setVisible(False)
            self.scroll_area.setVisible(True)
            self._populate_grid(payload)
        
        QApplication.restoreOverrideCursor()

    def _populate_grid(self, results: dict):
        """用分析结果填充网格。"""
        self._clear_grid()

        # [修复] 使用 .value 访问正确的字符串键
        previews = results.get(ResultKeys.PREVIEWS.value, {})
        visualization = results.get(ResultKeys.VISUALIZATION.value)
        
        # [调试] 验证修复是否成功
        print(f"[DEBUG PreviewWidget] Correctly extracted previews dict keys: {previews.keys()}")
        
        # 定义显示顺序和标题
        display_order = [
            (StageKeys.ORIGINAL, "原始图像"),
            (StageKeys.GRAY, "灰度图"),
            (StageKeys.BINARY, "二值图"),
            (StageKeys.MORPH, "形态学处理后"),
            (StageKeys.DETECTION, "最终结果")
        ]
        
        # 将detection图也加入previews方便统一处理
        if visualization is not None:
             previews[StageKeys.DETECTION.value] = visualization

        col_count = 2  # 每行显示2个预览
        row, col = 0, 0
        
        for key_enum, title in display_order:
            if isinstance(key_enum, StageKeys) and key_enum.value in previews:
                image_data = previews[key_enum.value]
                preview_widget = _SinglePreview(title, image_data)
                self.grid_layout.addWidget(preview_widget, row, col)
                col += 1
                if col >= col_count:
                    col = 0
                    row += 1
            # 兼容旧的字符串key（以防万一）
            elif isinstance(key_enum, str) and key_enum in previews:
                 image_data = previews[key_enum]
                 preview_widget = _SinglePreview(title, image_data)
                 self.grid_layout.addWidget(preview_widget, row, col)
                 col += 1
                 if col >= col_count:
                    col = 0
                    row += 1


    def clear_all(self):
        """清空所有内容，恢复到初始状态。"""
        self._clear_grid()
        self.status_label.setText("请加载图像并开始分析")
        self.status_label.setVisible(True)
        self.scroll_area.setVisible(False)

    def _clear_grid(self):
        """清空网格布局中的所有子控件。"""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater() 