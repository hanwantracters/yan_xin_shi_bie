# 核心模块

该目录包含应用程序的业务逻辑层和数据处理层组件。

## 文件说明

- `controller.py`: 应用程序控制器，协调UI和业务逻辑
- `image_processor.py`: 图像处理功能实现，包含裂缝检测算法
- `analysis_stages.py`: 分析阶段枚举定义
- `unit_converter.py`: 像素和物理单位转换工具

## 图像处理流程

图像处理遵循以下步骤：
1. 加载原始图像并提取DPI信息
2. 转换为灰度图像
3. 应用阈值分割获取二值图像
4. 应用形态学操作改善裂缝识别
5. 检测裂缝轮廓并计算参数

## 控制器设计

`Controller`类是本模块的中心，负责：
- 管理图像处理流程
- 保存和获取各个分析阶段的结果
- 协调UI层与数据处理层的交互
- 提供单位转换功能

## 分析阶段

系统定义了以下处理阶段（在`analysis_stages.py`中）：
- `ORIGINAL`: 原始图像
- `GRAYSCALE`: 灰度图像
- `THRESHOLD`: 阈值分割
- `MORPHOLOGY`: 形态学处理
- `DETECTION`: 裂缝检测
- `MEASUREMENT`: 测量结果

每个阶段的处理结果都保存在控制器的`analysis_results`字典中，以便在UI层展示和后续处理。 