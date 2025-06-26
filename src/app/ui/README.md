# UI层: 用户界面

该目录包含应用程序的所有用户界面 (UI) 组件。UI层负责接收用户输入、展示图像和数据，并通过信号与槽机制与业务逻辑层的`Controller`进行通信。

## 组件结构

-   **`main_window.py`**: 应用程序的主窗口，作为所有UI组件的容器。它负责整体布局、菜单栏管理，并组装其他所有UI组件。
-   **`control_panel.py`**: 主控制面板。它不再包含具体的参数控件，而是提供了一个**分析模式选择器(QComboBox)**和一个**参数面板区域(QStackedWidget)**。
-   **`result_panel.py`**: 结果显示面板，以摘要和详细数据表格两种形式清晰地展示最终的量化分析结果。
-   **`multi_stage_preview_widget.py`**: 一个高级预览组件，能够根据控制器发送的状态（如加载中、就绪、无结果）自动管理和展示多个分析阶段（原始、二值化、结果等）的图像。
-   **`measurement_dialog.py`**: (待实现) 手动测量工具的对话框。
-   **`style_manager.py`**: 样式管理器，集中管理应用的QSS样式表。
-   **`parameter_panels/`**:
    -   `fracture_params_panel.py`: "裂缝分析"模式对应的参数面板，包含所有与裂缝分析相关的UI控件（如阈值算法选择、形态学参数调节等）。

## 核心交互流程

1.  **初始化与模式选择**:
    -   `ControlPanel`在初始化时，主动调用`Controller`的`get_registered_analyzers()`方法，获取所有可用的分析器列表。
    -   列表被填充到分析模式选择器（下拉框）中。
    -   当用户通过下拉框选择一个分析模式（如"裂缝分析"）时，`ControlPanel`会：
        1.  通知`Controller`设置对应的分析器为**激活状态**。
        2.  实例化该分析模式对应的**参数面板**（如`FractureParamsPanel`）。
        3.  将新创建的参数面板显示在界面上。

2.  **实时参数调整**:
    -   用户在参数面板上调整参数，触发`Controller`的`run_preview`方法。
    -   `Controller`不再发送一系列独立的预览图像，而是发送一个包含**当前状态**的信号`preview_state_changed`。
    -   信号的载荷是一个字典，格式为`{'state': PreviewState, 'payload': ...}`，其中`state`可以是`LOADING`、`READY`、`EMPTY`或`ERROR`。
    -   `MainWindow`将此信号直接连接到`MultiStagePreviewWidget`的`display_state`槽。
    -   `MultiStagePreviewWidget`根据接收到的状态，自行决定是显示加载动画、"无结果"提示，还是从`payload`中提取并展示所有阶段的预览图像。

3.  **最终分析**:
    -   用户在`ControlPanel`点击"一键执行分析"。
    -   `Controller`调用当前**激活分析器**的`run_analysis`方法。
    -   分析完成后，`Controller`发出`analysis_complete`信号，其中包含最终的量化数据和可视化结果。
    -   `ResultPanel`接收此信号并更新其显示。

## 设计原则

-   **UI与核心逻辑分离**: UI层只负责发出"参数变更"的信号，并将`Controller`的状态信号直接传递给专门的预览组件。
-   **封装预览逻辑**: `MultiStagePreviewWidget`完全封装了处理不同预览状态（加载中、成功、失败、无结果）的所有逻辑，极大地简化了`MainWindow`。
-   **可扩展性**: 添加新的分析类型时，只需创建新的参数面板和`Analyzer`，UI的整体交互逻辑保持不变。

## 预览窗口设计 (重构后)

系统现在使用单一的`MultiStagePreviewWidget`组件来负责所有预览显示。它采用**状态驱动**的设计：
-   **监听状态**: 它不直接接收图像，而是监听`Controller`发出的`preview_state_changed`信号。
-   **自我管理**: 根据接收到的`state`值，它内部管理着多个`PreviewWindow`实例（可能在标签页中），并负责：
    -   显示"加载中"的提示。
    -   在`READY`状态时，从`payload`中解析出所有阶段的图像并分别显示。
    -   显示"未检测到裂缝"或错误信息。
    -   在切换分析器时，清空所有预览。
这种设计将复杂的UI状态管理逻辑从`MainWindow`中移除，使其高度内聚和可重用。

## 控制面板设计

控制面板(`ControlPanel`)提供了以下功能：
- 图像加载按钮
- 开始分析按钮
- 阈值模式选择(全局阈值、自适应阈值、Otsu阈值)
- 阈值参数调整滑块
- 测量工具按钮 