import sys
import os
import cv2
import numpy as np
import pandas as pd
from skimage import measure, morphology, filters, feature
from skimage.filters import threshold_otsu, gaussian
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QTabWidget, QTableWidget,
                             QTableWidgetItem, QMessageBox, QGraphicsView, QGraphicsScene,
                             QGroupBox, QSlider, QSplitter, QSizePolicy, QComboBox, QCheckBox)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QSize


class GeologicalCoreAnalysisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("海底地质岩心孔洞、粒度、裂缝图文分析系统")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                background-color: #34495e;
                color: #ecf0f1;
                font-family: Arial;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
            QTabWidget::pane {
                border: 1px solid #2c3e50;
                background: #34495e;
            }
            QTabBar::tab {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3498db;
            }
            QTableWidget {
                background-color: #2c3e50;
                gridline-color: #7f8c8d;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 4px;
                border: none;
            }
            QGroupBox {
                border: 1px solid #3498db;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: #3498db;
                color: white;
                border-radius: 3px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #7f8c8d;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)

        # 初始化变量
        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.display_image = None
        self.current_analysis_type = "porosity"  # porosity, grain, fracture
        self.analysis_results = {
            'porosity': {'count': 0, 'areas': [], 'perimeters': [], 'circularity': []},
            'grain': {'count': 0, 'sizes': [], 'sphericity': []},
            'fracture': {'count': 0, 'lengths': [], 'widths': [], 'orientation': []}
        }
        self.analysis_params = {
            'porosity_threshold': 128,
            'porosity_min_area': 20,
            'grain_threshold': 128,
            'grain_min_size': 10,
            'fracture_threshold': 50,
            'fracture_min_length': 30
        }

        # 创建主界面
        self.initUI()

    def initUI(self):
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板 - 图像显示
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # 图像显示区域
        image_group = QGroupBox("岩心图像")
        image_layout = QVBoxLayout()
        self.image_view = QGraphicsView()
        self.image_view.setMinimumSize(700, 500)
        self.image_view.setRenderHint(QPainter.Antialiasing)
        self.scene = QGraphicsScene()
        self.image_view.setScene(self.scene)
        image_layout.addWidget(self.image_view)

        # 图像控制按钮
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("加载岩心图像")
        self.load_btn.clicked.connect(self.load_image)
        self.original_btn = QPushButton("原始图像")
        self.original_btn.clicked.connect(self.show_original_image)
        self.analyzed_btn = QPushButton("分析结果")
        self.analyzed_btn.clicked.connect(self.show_analyzed_image)

        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.original_btn)
        btn_layout.addWidget(self.analyzed_btn)
        image_layout.addLayout(btn_layout)
        image_group.setLayout(image_layout)
        left_layout.addWidget(image_group)

        # 分析参数控制
        params_group = QGroupBox("分析参数设置")
        params_layout = QVBoxLayout()

        # 分析类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("分析类型:")
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["孔洞分析", "粒度分析", "裂缝分析"])
        self.analysis_type.currentIndexChanged.connect(self.change_analysis_type)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.analysis_type)
        params_layout.addLayout(type_layout)

        # 孔洞分析参数
        self.porosity_params = QWidget()
        porosity_layout = QVBoxLayout()
        porosity_layout.addWidget(QLabel("孔洞检测阈值:"))
        self.porosity_threshold = QSlider(Qt.Horizontal)
        self.porosity_threshold.setRange(0, 255)
        self.porosity_threshold.setValue(128)
        self.porosity_threshold.valueChanged.connect(self.update_porosity_params)
        porosity_layout.addWidget(self.porosity_threshold)

        porosity_layout.addWidget(QLabel("最小孔洞面积:"))
        self.porosity_min_area = QSlider(Qt.Horizontal)
        self.porosity_min_area.setRange(1, 100)
        self.porosity_min_area.setValue(20)
        self.porosity_min_area.valueChanged.connect(self.update_porosity_params)
        porosity_layout.addWidget(self.porosity_min_area)

        self.porosity_params.setLayout(porosity_layout)

        # 粒度分析参数
        self.grain_params = QWidget()
        grain_layout = QVBoxLayout()
        grain_layout.addWidget(QLabel("粒度检测阈值:"))
        self.grain_threshold = QSlider(Qt.Horizontal)
        self.grain_threshold.setRange(0, 255)
        self.grain_threshold.setValue(128)
        self.grain_threshold.valueChanged.connect(self.update_grain_params)
        grain_layout.addWidget(self.grain_threshold)

        grain_layout.addWidget(QLabel("最小颗粒尺寸:"))
        self.grain_min_size = QSlider(Qt.Horizontal)
        self.grain_min_size.setRange(1, 50)
        self.grain_min_size.setValue(10)
        self.grain_min_size.valueChanged.connect(self.update_grain_params)
        grain_layout.addWidget(self.grain_min_size)

        self.grain_params.setLayout(grain_layout)

        # 裂缝分析参数
        self.fracture_params = QWidget()
        fracture_layout = QVBoxLayout()
        fracture_layout.addWidget(QLabel("裂缝检测阈值:"))
        self.fracture_threshold = QSlider(Qt.Horizontal)
        self.fracture_threshold.setRange(0, 100)
        self.fracture_threshold.setValue(50)
        self.fracture_threshold.valueChanged.connect(self.update_fracture_params)
        fracture_layout.addWidget(self.fracture_threshold)

        fracture_layout.addWidget(QLabel("最小裂缝长度:"))
        self.fracture_min_length = QSlider(Qt.Horizontal)
        self.fracture_min_length.setRange(10, 200)
        self.fracture_min_length.setValue(30)
        self.fracture_min_length.valueChanged.connect(self.update_fracture_params)
        fracture_layout.addWidget(self.fracture_min_length)

        self.fracture_params.setLayout(fracture_layout)

        # 添加参数控件并隐藏
        params_layout.addWidget(self.porosity_params)
        params_layout.addWidget(self.grain_params)
        params_layout.addWidget(self.fracture_params)
        self.grain_params.hide()
        self.fracture_params.hide()

        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)

        # 右侧面板 - 控制和分析结果
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        # 分析按钮
        analyze_btn_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("执行分析")
        self.analyze_btn.setIconSize(QSize(24, 24))
        self.analyze_btn.clicked.connect(self.analyze_image)
        self.analyze_btn.setEnabled(False)
        self.export_btn = QPushButton("导出分析结果")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)

        analyze_btn_layout.addWidget(self.analyze_btn)
        analyze_btn_layout.addWidget(self.export_btn)
        right_layout.addLayout(analyze_btn_layout)

        # 选项卡
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { height: 30px; }")
        right_layout.addWidget(self.tabs)

        # 孔洞分析结果
        self.porosity_tab = QWidget()
        porosity_tab_layout = QVBoxLayout()
        self.porosity_table = QTableWidget()
        self.porosity_table.setColumnCount(4)
        self.porosity_table.setHorizontalHeaderLabels(['孔洞ID', '面积(像素)', '周长(像素)', '圆度'])
        porosity_tab_layout.addWidget(self.porosity_table)

        # 孔洞统计信息
        porosity_stats = QHBoxLayout()
        self.porosity_count = QLabel("孔洞数量: 0")
        self.porosity_avg_area = QLabel("平均面积: 0")
        self.porosity_porosity = QLabel("孔隙度: 0%")
        porosity_stats.addWidget(self.porosity_count)
        porosity_stats.addWidget(self.porosity_avg_area)
        porosity_stats.addWidget(self.porosity_porosity)
        porosity_tab_layout.addLayout(porosity_stats)

        self.porosity_tab.setLayout(porosity_tab_layout)
        self.tabs.addTab(self.porosity_tab, "孔洞分析")

        # 粒度分析结果
        self.grain_tab = QWidget()
        grain_tab_layout = QVBoxLayout()
        self.grain_table = QTableWidget()
        self.grain_table.setColumnCount(3)
        self.grain_table.setHorizontalHeaderLabels(['颗粒ID', '等效直径(像素)', '球度'])
        grain_tab_layout.addWidget(self.grain_table)

        # 粒度统计信息
        grain_stats = QHBoxLayout()
        self.grain_count = QLabel("颗粒数量: 0")
        self.grain_avg_size = QLabel("平均直径: 0")
        self.grain_size_dist = QLabel("粒径分布: ")
        grain_stats.addWidget(self.grain_count)
        grain_stats.addWidget(self.grain_avg_size)
        grain_stats.addWidget(self.grain_size_dist)
        grain_tab_layout.addLayout(grain_stats)

        self.grain_tab.setLayout(grain_tab_layout)
        self.tabs.addTab(self.grain_tab, "粒度分析")

        # 裂缝分析结果
        self.fracture_tab = QWidget()
        fracture_tab_layout = QVBoxLayout()
        self.fracture_table = QTableWidget()
        self.fracture_table.setColumnCount(4)
        self.fracture_table.setHorizontalHeaderLabels(['裂缝ID', '长度(像素)', '宽度(像素)', '方向(度)'])
        fracture_tab_layout.addWidget(self.fracture_table)

        # 裂缝统计信息
        fracture_stats = QHBoxLayout()
        self.fracture_count = QLabel("裂缝数量: 0")
        self.fracture_avg_length = QLabel("平均长度: 0")
        self.fracture_avg_width = QLabel("平均宽度: 0")
        fracture_stats.addWidget(self.fracture_count)
        fracture_stats.addWidget(self.fracture_avg_length)
        fracture_stats.addWidget(self.fracture_avg_width)
        fracture_tab_layout.addLayout(fracture_stats)

        self.fracture_tab.setLayout(fracture_tab_layout)
        self.tabs.addTab(self.fracture_tab, "裂缝分析")

        # 设置分割器比例
        splitter.setSizes([900, 500])

    def change_analysis_type(self, index):
        # 隐藏所有参数面板
        self.porosity_params.hide()
        self.grain_params.hide()
        self.fracture_params.hide()

        # 根据选择的类型显示对应面板
        if index == 0:  # 孔洞分析
            self.porosity_params.show()
            self.current_analysis_type = "porosity"
        elif index == 1:  # 粒度分析
            self.grain_params.show()
            self.current_analysis_type = "grain"
        elif index == 2:  # 裂缝分析
            self.fracture_params.show()
            self.current_analysis_type = "fracture"

        # 如果图像已加载，重新分析
        if self.original_image is not None:
            self.analyze_image()

    def update_porosity_params(self):
        self.analysis_params['porosity_threshold'] = self.porosity_threshold.value()
        self.analysis_params['porosity_min_area'] = self.porosity_min_area.value()
        if self.original_image is not None:
            self.analyze_image()

    def update_grain_params(self):
        self.analysis_params['grain_threshold'] = self.grain_threshold.value()
        self.analysis_params['grain_min_size'] = self.grain_min_size.value()
        if self.original_image is not None:
            self.analyze_image()

    def update_fracture_params(self):
        self.analysis_params['fracture_threshold'] = self.fracture_threshold.value()
        self.analysis_params['fracture_min_length'] = self.fracture_min_length.value()
        if self.original_image is not None:
            self.analyze_image()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择岩心图像", "",
            "图像文件 (*.jpg *.jpeg *.png *.tif *.tiff *.bmp)"
        )

        if file_path:
            self.image_path = file_path
            self.original_image = cv2.imread(file_path)
            if self.original_image is not None:
                # 预处理图像 - 调整大小
                h, w = self.original_image.shape[:2]
                if w > 1200 or h > 800:
                    scale = min(1200 / w, 800 / h)
                    self.original_image = cv2.resize(self.original_image,
                                                     (int(w * scale), int(h * scale)))

                # 创建用于显示的图像
                self.display_image = self.original_image.copy()
                self.processed_image = self.original_image.copy()

                # 显示图像
                self.show_image(self.original_image)
                self.analyze_btn.setEnabled(True)
                self.export_btn.setEnabled(False)
                # 重置分析结果
                self.reset_analysis_results()
            else:
                QMessageBox.warning(self, "错误", "无法加载图像文件")

    def show_image(self, image):
        if image is None:
            return

        # 将OpenCV图像转换为Qt图像
        if len(image.shape) == 2:  # 灰度图像
            q_img = QImage(image.data, image.shape[1], image.shape[0],
                           image.shape[1], QImage.Format_Grayscale8)
        else:  # 彩色图像
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # 清除场景并添加新图像
        self.scene.clear()
        pixmap = QPixmap.fromImage(q_img)
        self.scene.addPixmap(pixmap)
        self.image_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def show_original_image(self):
        if self.original_image is not None:
            self.show_image(self.original_image)

    def show_analyzed_image(self):
        if self.processed_image is not None:
            self.show_image(self.processed_image)

    def reset_analysis_results(self):
        self.analysis_results = {
            'porosity': {'count': 0, 'areas': [], 'perimeters': [], 'circularity': []},
            'grain': {'count': 0, 'sizes': [], 'sphericity': []},
            'fracture': {'count': 0, 'lengths': [], 'widths': [], 'orientation': []}
        }

    def analyze_image(self):
        if self.original_image is None:
            return

        # 转换为灰度图像
        gray_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)

        # 应用高斯滤波降噪
        gray_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

        # 创建一个处理图像的副本
        self.processed_image = self.original_image.copy()

        # 根据当前分析类型执行分析
        if self.current_analysis_type == "porosity":
            self.analyze_porosity(gray_image)
            self.tabs.setCurrentIndex(0)
        elif self.current_analysis_type == "grain":
            self.analyze_grain_size(gray_image)
            self.tabs.setCurrentIndex(1)
        elif self.current_analysis_type == "fracture":
            self.analyze_fractures(gray_image)
            self.tabs.setCurrentIndex(2)

        # 显示分析后的图像
        self.show_image(self.processed_image)

        # 更新结果表格
        self.update_results_tables()

        # 启用导出按钮
        self.export_btn.setEnabled(True)

    def analyze_porosity(self, gray_image):
        # 使用自适应阈值进行二值化
        binary = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # 形态学操作去除小噪点
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        # 找到孔洞区域
        contours, _ = cv2.findContours(
            cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # 存储结果
        min_area = self.analysis_params['porosity_min_area']
        self.analysis_results['porosity']['count'] = 0
        self.analysis_results['porosity']['areas'] = []
        self.analysis_results['porosity']['perimeters'] = []
        self.analysis_results['porosity']['circularity'] = []

        # 在原图上绘制孔洞轮廓和编号
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

            # 过滤掉非孔洞形状
            if circularity < 0.5:
                continue

            self.analysis_results['porosity']['count'] += 1
            self.analysis_results['porosity']['areas'].append(area)
            self.analysis_results['porosity']['perimeters'].append(perimeter)
            self.analysis_results['porosity']['circularity'].append(circularity)

            # 绘制轮廓
            cv2.drawContours(self.processed_image, [cnt], -1, (0, 0, 255), 1)

            # 添加编号
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv2.putText(self.processed_image, str(i + 1), (cX, cY),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 计算孔隙度
        total_area = gray_image.shape[0] * gray_image.shape[1]
        porosity_area = sum(self.analysis_results['porosity']['areas'])
        porosity = (porosity_area / total_area) * 100 if total_area > 0 else 0

        # 更新统计信息
        self.porosity_count.setText(f"孔洞数量: {self.analysis_results['porosity']['count']}")
        avg_area = np.mean(self.analysis_results['porosity']['areas']) if self.analysis_results['porosity'][
            'areas'] else 0
        self.porosity_avg_area.setText(f"平均面积: {avg_area:.2f} 像素")
        self.porosity_porosity.setText(f"孔隙度: {porosity:.2f}%")

    def analyze_grain_size(self, gray_image):
        # 使用Otsu阈值法进行二值化
        _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 形态学操作去除小噪点
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)

        # 确定背景区域
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # 距离变换
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.5 * dist_transform.max(), 255, 0)

        # 找到未知区域
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)

        # 标记连通区域
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        # 分水岭算法
        markers = cv2.watershed(cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB), markers)
        self.processed_image[markers == -1] = [0, 0, 255]  # 标记边界为红色

        # 分析颗粒大小
        min_size = self.analysis_params['grain_min_size']
        self.analysis_results['grain']['count'] = 0
        self.analysis_results['grain']['sizes'] = []
        self.analysis_results['grain']['sphericity'] = []

        # 为每个颗粒添加标签
        for i in range(2, np.max(markers) + 1):
            # 创建当前颗粒的掩码
            mask = np.zeros_like(gray_image, dtype=np.uint8)
            mask[markers == i] = 255

            # 找到轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue

            cnt = contours[0]
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            sphericity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

            # 计算等效直径
            equivalent_diameter = np.sqrt(4 * area / np.pi)

            if equivalent_diameter < min_size:
                continue

            self.analysis_results['grain']['count'] += 1
            self.analysis_results['grain']['sizes'].append(equivalent_diameter)
            self.analysis_results['grain']['sphericity'].append(sphericity)

            # 添加颗粒编号
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                cv2.putText(self.processed_image, str(self.analysis_results['grain']['count']),
                            (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # 更新统计信息
        self.grain_count.setText(f"颗粒数量: {self.analysis_results['grain']['count']}")
        avg_size = np.mean(self.analysis_results['grain']['sizes']) if self.analysis_results['grain']['sizes'] else 0
        self.grain_avg_size.setText(f"平均直径: {avg_size:.2f} 像素")

        # 计算粒径分布
        if self.analysis_results['grain']['sizes']:
            sizes = np.array(self.analysis_results['grain']['sizes'])
            small = np.sum(sizes < 15)
            medium = np.sum((sizes >= 15) & (sizes < 30))
            large = np.sum(sizes >= 30)
            self.grain_size_dist.setText(f"粒径分布: 小颗粒({small}), 中颗粒({medium}), 大颗粒({large})")
        else:
            self.grain_size_dist.setText("粒径分布: 无颗粒")

    def analyze_fractures(self, gray_image):
        # 边缘检测
        edges = cv2.Canny(gray_image,
                          self.analysis_params['fracture_threshold'],
                          self.analysis_params['fracture_threshold'] * 2)

        # 形态学操作增强裂缝
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)

        # 霍夫变换检测直线
        lines = cv2.HoughLinesP(
            dilated_edges, 1, np.pi / 180, threshold=50,
            minLineLength=self.analysis_params['fracture_min_length'],
            maxLineGap=10
        )

        # 存储结果
        self.analysis_results['fracture']['count'] = 0
        self.analysis_results['fracture']['lengths'] = []
        self.analysis_results['fracture']['widths'] = []
        self.analysis_results['fracture']['orientation'] = []

        if lines is not None:
            for i, line in enumerate(lines):
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

                # 计算方向（角度）
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                if angle < 0:
                    angle += 180

                # 计算裂缝宽度（简化方法）
                roi = gray_image[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
                if roi.size > 0:
                    # 使用边缘检测结果估计宽度
                    roi_edges = cv2.Canny(roi, 50, 150)
                    non_zero = np.count_nonzero(roi_edges)
                    if non_zero > 0:
                        width = non_zero / length
                    else:
                        width = 2.0  # 默认值
                else:
                    width = 2.0

                self.analysis_results['fracture']['count'] += 1
                self.analysis_results['fracture']['lengths'].append(length)
                self.analysis_results['fracture']['widths'].append(width)
                self.analysis_results['fracture']['orientation'].append(angle)

                # 在原图上绘制裂缝
                cv2.line(self.processed_image, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.putText(self.processed_image, str(i + 1),
                            ((x1 + x2) // 2, (y1 + y2) // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 更新统计信息
        self.fracture_count.setText(f"裂缝数量: {self.analysis_results['fracture']['count']}")
        avg_length = np.mean(self.analysis_results['fracture']['lengths']) if self.analysis_results['fracture'][
            'lengths'] else 0
        avg_width = np.mean(self.analysis_results['fracture']['widths']) if self.analysis_results['fracture'][
            'widths'] else 0
        self.fracture_avg_length.setText(f"平均长度: {avg_length:.2f} 像素")
        self.fracture_avg_width.setText(f"平均宽度: {avg_width:.2f} 像素")

    def update_results_tables(self):
        # 更新孔洞分析表格
        self.update_porosity_table()

        # 更新粒度分析表格
        self.update_grain_table()

        # 更新裂缝分析表格
        self.update_fracture_table()

    def update_porosity_table(self):
        porosity_data = self.analysis_results['porosity']
        self.porosity_table.setRowCount(porosity_data['count'])

        for i in range(porosity_data['count']):
            self.porosity_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.porosity_table.setItem(i, 1, QTableWidgetItem(f"{porosity_data['areas'][i]:.2f}"))
            self.porosity_table.setItem(i, 2, QTableWidgetItem(f"{porosity_data['perimeters'][i]:.2f}"))
            self.porosity_table.setItem(i, 3, QTableWidgetItem(f"{porosity_data['circularity'][i]:.3f}"))

    def update_grain_table(self):
        grain_data = self.analysis_results['grain']
        self.grain_table.setRowCount(grain_data['count'])

        for i in range(grain_data['count']):
            self.grain_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.grain_table.setItem(i, 1, QTableWidgetItem(f"{grain_data['sizes'][i]:.2f}"))
            self.grain_table.setItem(i, 2, QTableWidgetItem(f"{grain_data['sphericity'][i]:.3f}"))

    def update_fracture_table(self):
        fracture_data = self.analysis_results['fracture']
        self.fracture_table.setRowCount(fracture_data['count'])

        for i in range(fracture_data['count']):
            self.fracture_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.fracture_table.setItem(i, 1, QTableWidgetItem(f"{fracture_data['lengths'][i]:.2f}"))
            self.fracture_table.setItem(i, 2, QTableWidgetItem(f"{fracture_data['widths'][i]:.2f}"))
            self.fracture_table.setItem(i, 3, QTableWidgetItem(f"{fracture_data['orientation'][i]:.1f}"))

    def export_results(self):
        if not any(self.analysis_results[key]['count'] > 0 for key in self.analysis_results):
            QMessageBox.warning(self, "警告", "没有可导出的分析结果")
            return

        # 获取保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存分析结果", "", "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )

        if save_path:
            try:
                # 创建多个DataFrame
                dfs = {}

                # 孔洞数据
                porosity_data = self.analysis_results['porosity']
                porosity_df = pd.DataFrame({
                    '孔洞ID': range(1, porosity_data['count'] + 1),
                    '面积(像素)': porosity_data['areas'],
                    '周长(像素)': porosity_data['perimeters'],
                    '圆度': porosity_data['circularity']
                })
                dfs['孔洞分析'] = porosity_df

                # 粒度数据
                grain_data = self.analysis_results['grain']
                grain_df = pd.DataFrame({
                    '颗粒ID': range(1, grain_data['count'] + 1),
                    '等效直径(像素)': grain_data['sizes'],
                    '球度': grain_data['sphericity']
                })
                dfs['粒度分析'] = grain_df

                # 裂缝数据
                fracture_data = self.analysis_results['fracture']
                fracture_df = pd.DataFrame({
                    '裂缝ID': range(1, fracture_data['count'] + 1),
                    '长度(像素)': fracture_data['lengths'],
                    '宽度(像素)': fracture_data['widths'],
                    '方向(度)': fracture_data['orientation']
                })
                dfs['裂缝分析'] = fracture_df

                # 根据文件类型保存
                if save_path.endswith('.xlsx'):
                    with pd.ExcelWriter(save_path) as writer:
                        for sheet_name, df in dfs.items():
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # 对于CSV，创建目录保存多个文件
                    base_path = os.path.splitext(save_path)[0]
                    os.makedirs(base_path, exist_ok=True)
                    for name, df in dfs.items():
                        df.to_csv(os.path.join(base_path, f"{name}.csv"), index=False)

                QMessageBox.information(self, "成功", f"结果已保存到: {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = GeologicalCoreAnalysisApp()
    window.show()
    sys.exit(app.exec_())