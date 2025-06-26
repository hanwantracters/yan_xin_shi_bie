# 核心模块: 业务与数据层

该目录是应用程序的大脑，封装了所有业务逻辑和数据处理功能。它采用**策略设计模式 (Strategy Design Pattern)**，将不同的分析类型（如裂缝分析、孔洞分析）解耦为可互换的"分析器"策略。

## 文件结构

-   **`controller.py`**: **业务逻辑层**。作为应用程序的中心协调器，负责管理和切换当前激活的分析策略。
-   **`image_operations.py`**: **数据处理层**。提供了一系列原子化、可重用的图像处理函数（如高斯模糊、阈值算法等）。
-   **`unit_converter.py`**: **工具**。提供像素单位与物理单位（毫米）之间的转换功能。
-   **`constants.py`**: **通用工具**。定义了项目范围内使用的常量，如字典键名(`ResultKeys`)和预览状态(`PreviewState`)，以避免硬编码。
-   **`analyzers/`**: **策略层**。
    -   `base_analyzer.py`: 定义了所有分析器必须遵守的抽象基类 `BaseAnalyzer` 接口。
    -   `fracture_analyzer.py`: `BaseAnalyzer` 的一个具体实现，封装了所有与"裂缝分析"相关的处理流程和参数。

## 架构设计：策略模式 (Analyzer)

本项目的核心是基于策略模式的分析器 `(Analyzer)` 架构。

-   **`BaseAnalyzer` (策略接口)**: 定义了一个所有分析器都必须实现的通用接口，主要包括：
    -   `get_id()`: 返回分析器的唯一标识符 (如 `'fracture'`)。
    -   `get_name()`: 返回用于在UI上显示的名称 (如 `'裂缝分析'`)。
    -   `get_default_parameters()`: 返回该分析器所需的默认参数结构。
    -   `run_analysis()`: 执行该策略特有的完整分析流程，并返回一个包含可视化图像和测量数据的字典。

-   **具体分析器 (具体策略)**: 如 `FractureAnalyzer`，它继承自 `BaseAnalyzer` 并提供了 `run_analysis` 方法的具体实现。它从 `image_operations` 模块中调用所需的原子函数，按照特定顺序组合它们，以完成裂缝的识别和测量。

这种设计的优势在于**可扩展性**和**解耦**。未来若要添加"孔洞分析"功能，只需创建一个新的 `PoreAnalyzer` 类，实现 `BaseAnalyzer` 接口，并将其在 `Controller` 中注册即可，无需修改现有代码。

## Controller 设计

`Controller` 的角色是**策略的管理者 (Context)**。它不关心具体分析算法的实现细节。其核心职责包括：

-   **分析器注册与管理**: 在启动时，扫描并注册所有可用的 `Analyzer` 实例。
-   **状态管理**:
    -   持有当前加载的图像 (`current_image`) 和DPI信息。
    -   维护当前**激活的分析器** (`active_analyzer`)。
    -   管理当前激活分析器所需的参数 (`analysis_params`)。
-   **流程驱动**:
    -   响应UI请求，调用 `active_analyzer.run_analysis()` 方法，将图像和参数传递给它。
    -   接收分析器返回的结果。
-   **结果分发**:
    -   **状态化预览**: 不再逐个发送预览图像，而是发送一个包含当前处理状态的信号 `preview_state_changed`。该信号的载荷是一个字典 `{'state': PreviewState, 'payload': ...}`，`payload`中包含了完整的分析结果。UI层根据此状态来更新自己。
    -   **最终结果**: 在进行单位换算后，将最终的测量数据通过信号 (`analysis_complete`) 发送给UI层。
    -   **统一键名**: 所有分析结果的字典键都使用 `constants.ResultKeys` 中定义的常量，确保了模块间交互的一致性。

## 图像处理流水线

具体的图像处理流水线不再由 `Controller` 或单个 `ImageProcessor` 硬编码。**每个分析器内部都定义了自己的流水线**。

例如，在 `FractureAnalyzer` 的 `run_analysis` 方法中，其流水线大致如下：
1.  图像预处理（灰度、模糊）。
2.  阈值分割。
3.  形态学处理。
4.  轮廓分析与过滤（根据长宽比等裂缝特有属性）。
5.  结果可视化与测量。

## 数据结构

分析器返回的、并在`Controller`中流转的核心数据结构是一个字典，其键名由`utils/constants.py`中的枚举`ResultKeys`和`StageKeys`统一定义。一个典型的结果字典如下：
```python
{
    ResultKeys.VISUALIZATION: <可视化结果图像>,
    ResultKeys.MEASUREMENTS: { ...测量数据... },
    ResultKeys.PREVIEWS: {
        StageKeys.GRAY: <灰度图>,
        StageKeys.BINARY: <二值图>,
        ...
    }
}
```
这种方式避免了硬编码字符串，提高了代码的健壮性和可维护性。 