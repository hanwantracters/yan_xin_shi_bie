# UI层: 用户界面

该目录包含应用程序的所有用户界面 (UI) 组件。UI层负责接收用户输入、展示图像和数据，并通过信号与槽机制与业务逻辑层的`Controller`进行通信。

## 组件结构

-   **`main_window.py`**: 应用程序的主窗口，作为所有UI组件的容器。
-   **`control_panel.py`**: 主控制面板，负责模式选择和参数面板的动态加载。
-   **`result_panel.py`**: 结果显示面板。
-   **`multi_stage_preview_widget.py`**: 一个高级预览组件，能够根据控制器发送的状态（如加载中、就绪、无结果）自动管理和展示多个分析阶段的图像。
-   **`dialogs/`**: 存放各类可复用或独立的参数设置对话框。
    -   `threshold_settings_dialog.py`, `morphology_settings_dialog.py`
    -   `pore_filtering_dialog.py`: "孔洞分析"模式专用的过滤参数对话框。
-   **`measurement_dialog.py`**: (待实现) 手动测量工具的对话框。
-   **`style_manager.py`**: 样式管理器，集中管理应用的QSS样式表。
-   **`parameter_panels/`**: 存放不同分析器对应的参数面板的容器目录。
    -   `fracture_params_panel.py`: "裂缝分析"模式对应的参数面板。
    -   `pore_params_panel.py`: "孔洞分析"模式对应的参数面板。

## 核心交互流程: 参数修改与实时预览

系统采用一个健壮的、由分析器驱动的单向数据流来处理参数修改。

1.  **用户输入**: 用户在某个参数对话框中调整一个控件（如`QSlider`）。
2.  **信号发射**: 该控件的信号被连接到一个本地的 `_on_parameter_changed` 方法。
3.  **预览决策与信号冒泡**:
    -   `_on_parameter_changed` 方法会检查`Controller`中当前`Analyzer`为该参数定义的`ui_hints`元数据。
    -   如果`'realtime'`为`True`，对话框会发射一个`realtime_preview_requested`信号。
    -   同时，一个包含参数变更详情的`parameter_changed`信号也会被发射。
4.  **意图告知 `Controller`**: `ControlPanel`（作为参数面板的创建者）捕获这两个信号：
    -   `parameter_changed`信号会调用`controller.update_parameter(key, value)`。
    -   `realtime_preview_requested`信号会调用`controller.request_realtime_preview()`。
5.  **`Controller` 处理与广播**: `Controller` 更新其内部参数字典，然后广播一个全局的 `parameters_updated` 信号。
6.  **UI同步**: 所有相关的UI组件（包括打开的参数对话框）都监听 `parameters_updated` 信号，并调用各自的 `update_controls` 方法来刷新界面显示。

这个流程形成了一个封闭、可预测的循环 (`UI -> Controller -> UI`)，确保了数据的一致性，同时将实时预览的决策权下放给了最了解业务的`Analyzer`。

## 核心交互流程: 最终分析

-   **加载图像**: 用户点击"加载图像"后，`MainWindow` 会响应，调用 `Controller` 加载图像，并立刻在 `MultiStagePreviewWidget` 中显示原始图像。**不会触发自动分析**。
-   **最终分析**: 用户点击"一键执行分析"后，`controller.run_full_analysis()` 被调用，执行完整的分析流程，并通过信号将最终结果分发给 `ResultPanel` 和 `MultiStagePreviewWidget`。

## 设计原则

-   **UI与核心逻辑分离**: UI组件不直接修改业务状态，只负责发出"参数变更意图"和"请求预览"的信号。
-   **`Controller`作为中枢**: `