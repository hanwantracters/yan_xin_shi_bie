# UI层: 用户界面

该目录包含应用程序的所有用户界面 (UI) 组件。UI层负责接收用户输入、展示图像和数据，并通过信号与槽机制与业务逻辑层的`Controller`进行通信。

## 组件结构

-   **`main_window.py`**: 应用程序的主窗口，作为所有UI组件的容器。它负责整体布局、菜单栏管理，并协调其他所有UI组件与`Controller`的交互。
-   **`control_panel.py`**: 主控制面板，位于主窗口中，提供核心操作的入口，如加载图像、开始分析、参数导入/导出等。
-   **`result_panel.py`**: 结果显示面板，以**摘要**和**详细数据表格**两种形式清晰地展示最终的量化分析结果。
-   **`preview_window.py`**: 基础的图像显示组件，被其他窗口复用。
-   **`analysis_preview_window.py`**: **多标签页**的分析预览窗口。它允许用户并排查看图像在处理流程中（如灰度、阈值、形态学、最终检测）的各个中间结果及相关参数，实现了所见即所得的**实时参数调优**。
-   **参数设置对话框**:
    -   `threshold_settings_dialog.py`: 二值化参数设置对话框。
    -   `morphology_settings_dialog.py`: 形态学参数设置对话框。
    -   `filtering_settings_dialog.py`: 裂缝过滤与合并参数设置对话框。
-   **`measurement_dialog.py`**: (待实现) 手动测量工具的对话框。
-   **`style_manager.py`**: 样式管理器，集中管理应用的QSS样式表，确保界面风格的统一性。

## 核心交互流程

1.  **加载图像**:
    -   用户通过`ControlPanel`或菜单栏点击"加载图像"。
    -   `MainWindow`调用`Controller`的`load_image_from_file`方法。
    -   `Controller`处理图像后，发出`preview_stage_updated`信号。
    -   `MainWindow`的槽函数接收此信号，并将原始图像和灰度图更新到`AnalysisPreviewWindow`中。

2.  **实时参数调整**:
    -   用户从`ControlPanel`打开一个参数设置对话框（如`ThresholdSettingsDialog`）。
    -   对话框中的任何参数变动，都会调用`Controller`的`update_parameter`方法。
    -   `Controller`重新计算受影响的分析阶段（例如，阈值改变会触发阈值和形态学的重新计算），并发出`preview_stage_updated`信号。
    -   `AnalysisPreviewWindow`接收信号并实时更新对应标签页的预览图像和参数信息。

3.  **最终分析**:
    -   用户在`ControlPanel`点击"开始分析"。
    -   `MainWindow`调用`Controller`的`run_fracture_analysis`方法。
    -   `Controller`执行完整的分析流水线，并在每个阶段发出`preview_stage_updated`信号来更新`AnalysisPreviewWindow`。
    -   分析完成后，`Controller`发出`analysis_complete`信号，其中包含最终的量化数据。
    -   `ResultPanel`接收此信号并更新摘要和详细数据表格。

## 设计原则

-   **职责分离**: UI组件只负责显示和输入，不包含业务逻辑。所有计算和状态管理都委托给`Controller`。
-   **信号驱动**: 组件间的通信完全通过Qt的信号与槽机制实现，降低了耦合度。
-   **即时反馈**: 用户的每一个参数调整都能立即在`AnalysisPreviewWindow`中看到视觉效果，提升了用户体验。
-   **模块化**: 复杂的参数设置被封装在独立的对话框中，使得主界面保持简洁，逻辑更清晰。

## 预览窗口设计

系统包含两种预览窗口：
1. `PreviewWindow`: 基础图像显示组件，用于展示单张图像
2. `AnalysisPreviewWindow`: 多标签页预览组件，用于展示各个分析阶段的结果

`AnalysisPreviewWindow`通过标签页组织不同阶段的处理结果，每个标签页包含：
- 图像预览区域(使用`PreviewWindow`)
- 参数信息显示区域

## 控制面板设计

控制面板(`ControlPanel`)提供了以下功能：
- 图像加载按钮
- 开始分析按钮
- 阈值模式选择(全局阈值、自适应阈值、Otsu阈值)
- 阈值参数调整滑块
- 测量工具按钮 