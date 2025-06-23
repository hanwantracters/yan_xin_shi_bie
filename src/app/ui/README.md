# UI组件

该目录包含应用程序的所有用户界面组件。

## 文件说明

- `main_window.py`: 主窗口，负责组装所有UI组件，并通过**信号与槽机制**协调它们与`Controller`的交互。
- `control_panel.py`: 控制面板，提供所有用户操作的入口，包括多种**阈值算法选择**、参数实时调整、形态学设置和裂缝合并选项。
- `preview_window.py`: 基础图像预览窗口，用于显示单张图像。
- `analysis_preview_window.py`: **多标签页**的分析预览窗口，可并排查看图像在处理流程中（如灰度、阈值、形态学）的各个中间结果。
- `analysis_wizard.py`: 分析向导，在执行最终分析前，引导用户输入**裂缝过滤参数**（如最小长度、最小长宽比）。
- `result_panel.py`: 结果显示面板，以表格和摘要形式清晰地展示最终的量化分析数据。
- `measurement_dialog.py`: 手动测量对话框，允许用户在图像上手动绘制标尺并查看物理长度。
- `morphology_settings_dialog.py`: 形态学参数设置对话框，提供对开/闭运算等高级参数的精细控制。
- `style_manager.py`: 样式管理器，集中管理应用的QSS样式表，确保界面风格的统一性。

## 组件交互

- **核心协调者**: `MainWindow` 持有 `Controller` 的实例，并将来自 `ControlPanel` 的用户操作信号转发给 `Controller` 的槽函数。
- **即时预览**: `ControlPanel` 中的任何参数调整（如阈值滑块）都会发出信号。`Controller` 接收信号后，重新处理图像并将更新后的中间结果图像发回 `AnalysisPreviewWindow` 的相应标签页中，实现了所见即所得的**实时参数调优**。
- **向导式分析**: 点击"开始分析"按钮时，会弹出 `AnalysisWizard`。用户确认参数后，`MainWindow` 调用 `Controller` 的 `run_fracture_analysis` 方法，并将最终结果通过信号传递给 `ResultPanel` 和 `PreviewWindow`（用于显示叠加结果的图像）进行展示。

## 界面设计原则

- **简洁清晰**: 界面布局直观，将主要操作集中在左侧控制面板，右侧用于结果展示。
- **即时反馈**: 用户的每一个参数调整都能立即在分析预览窗口中看到效果。
- **分阶段展示**: `AnalysisPreviewWindow` 的设计让用户能够清晰地理解图像处理的每一个步骤及其对最终结果的影响。

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