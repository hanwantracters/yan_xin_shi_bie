# 核心模块: 业务与数据层

该目录是应用程序的大脑，封装了所有业务逻辑和数据处理功能。它采用**策略设计模式 (Strategy Design Pattern)**，将不同的分析类型（如裂缝分析、孔洞分析）解耦为可互换的"分析器"策略。

## 文件结构

-   **`controller.py`**: **业务逻辑层**。作为应用程序的中心协调器，负责管理分析策略和所有分析参数，并将具体业务逻辑**委托**给分析器。
-   **`image_operations.py`**: **数据处理层**。提供了一系列原子化、可重用的通用图像处理函数（如高斯模糊、阈值算法等）。
-   **`unit_converter.py`**: **工具**。提供像素单位与物理单位（毫米）之间的转换功能。
-   **`constants.py`**: **通用工具**。定义了项目范围内使用的常量，如字典键名(`ResultKeys`)和预览状态(`PreviewState`)，以避免硬编码。
-   **`analyzers/`**: **策略层**。
    -   `base_analyzer.py`: 定义了所有分析器必须遵守的抽象基类 `BaseAnalyzer` 接口。
    -   `fracture_analyzer.py`: `BaseAnalyzer` 的一个具体实现，封装了所有与"裂缝分析"相关的逻辑。
    -   `pore_analyzer.py`: `BaseAnalyzer` 的一个具体实现，封装了所有与"孔洞分析"相关的逻辑。

## 架构设计：策略模式 (Analyzer)

本项目的核心是基于策略模式的分析器 `(Analyzer)` 架构，并且该接口经过了扩展，以实现更高的内聚和解耦。

-   **`BaseAnalyzer` (策略接口)**: 定义了一个所有分析器都必须实现的通用接口，主要包括：
    -   `get_id()` / `get_name()`: 返回分析器的唯一ID和显示名称。
    -   `get_default_parameters()`: 返回该分析器所需的默认参数结构，其中可包含`ui_hints`元数据以驱动UI行为（如实时预览）。
    -   `run_analysis()`: 执行该策略特有的完整分析流程。
    -   **新增接口**:
        -   `is_result_empty(results)`: 由分析器自行判断其分析结果是否为空。
        -   `get_empty_message()`: 当结果为空时，返回定制化的提示信息。
        -   `post_process_measurements(results, dpi)`: 封装所有与单位转换相关的后处理逻辑。

-   **具体分析器 (具体策略)**: 如 `FractureAnalyzer` 和 `PoreAnalyzer`，它们继承自 `BaseAnalyzer` 并提供了所有接口的具体实现。特定于某个分析的工具函数（如孔洞圆度计算）应作为其私有方法，而不是放在通用的`image_operations.py`中。

这种设计的优势在于**可扩展性**和**责任分离**。`Controller` 完全不了解任何具体分析的实现细节，它只负责调用 `BaseAnalyzer` 的标准接口。

## Controller 设计

`Controller` 的角色是**策略和参数的中心管理者**，以及UI和核心逻辑之间的**通用协调器**。

-   **分析器注册与管理**: 在启动时，扫描并注册所有可用的 `Analyzer` 实例。
-   **参数管理 (唯一事实来源)**:
    -   维护当前激活分析器所需的所有参数 (`analysis_params`)。
    -   提供统一的 `update_parameter` 方法作为参数的**唯一修改入口**。
-   **流程驱动 (职责分离与委托)**:
    -   `Controller` 的核心职责是响应UI请求，然后调用 `active_analyzer` 的相应方法，将所有业务决策**委托**出去。
    -   例如，`run_preview` 方法现在只负责调用 `active_analyzer.run_analysis()`，然后使用 `active_analyzer.is_result_empty()` 来判断结果，而不是自己硬编码判断逻辑。
-   **结果分发**:
    -   **状态化预览**: 通过 `preview_state_changed` 信号分发预览结果，UI层根据此信号更新显示。
    -   **最终结果**: 通过 `analysis_complete` 信号分发由`Analyzer`完成单位转换的最终测量数据。

## 图像处理流水线

具体的图像处理流水线不再由 `Controller` 硬编码。**每个分析器内部都定义了自己的流水线**。

例如，在 `PoreAnalyzer` 的 `run_analysis` 方法中，其流水线可能采用分水岭算法来处理粘连的孔洞，这与 `FractureAnalyzer` 的流水线完全不同。

## 图像处理算法

本项目实现了多种图像处理算法，特别是在阈值分割方面，提供了多种可选方法以适应不同的图像特征和裂缝类型：

### 阈值分割方法

1. **全局阈值 (Global Thresholding)**
   - 简单直接的二值化方法，使用单一阈值将整个图像分为前景和背景
   - 适用于光照均匀、对比度高的图像
   - 参数：`threshold_value` - 像素值高于此阈值被视为前景(255)，低于则为背景(0)

2. **Otsu阈值 (Otsu's Method)**
   - 自动计算最优全局阈值的方法，通过最小化前景和背景类间方差
   - 适用于双峰直方图图像（前景和背景有明显灰度差异）
   - 无需手动设置阈值参数

3. **自适应高斯阈值 (Adaptive Gaussian Thresholding)**
   - 根据像素邻域计算局部阈值，能适应图像中不同区域的光照变化
   - 参数：`block_size` - 计算阈值的邻域大小，`C` - 从均值中减去的常数

4. **Niblack阈值 (Niblack's Method)**
   - 局部自适应阈值方法，考虑局部区域的均值和标准差
   - 公式：`threshold = mean + k * standard_deviation`
   - 参数：`window_size` - 局部区域大小，`k` - 权重因子（通常为负值）
   - 适用于光照不均匀的图像

5. **Sauvola阈值 (Sauvola's Method)**
   - Niblack方法的改进版，增加了动态范围参数，减少噪声影响
   - 公式：`threshold = mean * (1 + k * ((standard_deviation / r) - 1))`
   - 参数：`window_size` - 局部区域大小，`k` - 权重因子，`r` - 动态范围参数
   - 默认方法，特别适用于非均匀背景和微小裂缝的识别

### 形态学处理

在阈值分割后，应用形态学操作以改善二值图像质量：

1. **开运算 (Opening)**
   - 先腐蚀后膨胀的组合操作
   - 用途：移除小的噪点，平滑轮廓，断开细小连接
   - 参数：`kernel_shape`、`kernel_size`、`iterations`、`min_area`

2. **闭运算 (Closing)**
   - 先膨胀后腐蚀的组合操作
   - 用途：填充小孔洞，连接断开的轮廓
   - 参数：`kernel_shape`、`kernel_size`、`iterations`

### 裂缝特征提取

1. **轮廓分析**
   - 使用OpenCV的`findContours`函数提取二值图像中的轮廓
   - 计算每个轮廓的面积、最小外接矩形、长宽比等特征

2. **骨架化 (Skeletonization)**
   - 使用scikit-image的`skeletonize`函数将裂缝轮廓简化为单像素宽的骨架
   - 用于精确计算裂缝长度

3. **几何特征过滤**
   - 基于长宽比(`min_aspect_ratio`)过滤非裂缝对象
   - 基于最小长度(`min_length_pixels`)过滤过小的裂缝

这种多样化的算法选择使系统能够适应不同类型的岩石材料和裂缝特征，提高了识别的准确性和鲁棒性。

## 数据结构

分析器返回的、并在`Controller`中流转的核心数据结构是一个字典，其键名由`utils/constants.py`中的枚举`ResultKeys`和`StageKeys`统一定义。一个典型的结果字典如下：
```python
{
    ResultKeys.VISUALIZATION.value: <可视化结果图像>,
    ResultKeys.MEASUREMENTS.value: { ...测量数据... },
    ResultKeys.PREVIEWS.value: {
        StageKeys.GRAY.value: <灰度图>,
        StageKeys.BINARY.value: <二值图>,
        ...
    }
}
```
这种方式避免了硬编码字符串，提高了代码的健壮性和可维护性。 