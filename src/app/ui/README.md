# UI层: 用户界面

该目录包含应用程序的所有用户界面 (UI) 组件。UI层负责接收用户输入、展示图像和数据，并通过信号与槽机制与业务逻辑层的`Controller`进行通信。

## 组件结构

-   **`main_window.py`**: 应用程序的主窗口，作为所有UI组件的容器。
-   **`control_panel.py`**: 主控制面板，负责模式选择和参数面板的动态加载。
-   **`result_panel.py`**: 结果显示面板。
-   **`multi_stage_preview_widget.py`**: 核心的**多阶段预览窗口**，能够响应实时参数调整，并以多标签页的形式展示从原始图像到最终结果的所有中间处理步骤。
-   **`measurement_dialog.py`**: 一个用于手动测量的简单对话框。
-   **`style_manager.py`**: 集中管理应用程序的QSS样式，实现主题切换。
-   **`parameter_panels/`**: 存放不同分析器对应的参数面板的容器目录。
    -   `fracture_params_panel.py`: "裂缝分析"模式对应的参数面板。
    -   `pore_params_panel.py`: "孔洞分析"模式对应的参数面板。
-   **`dialogs/`**:
    - `base_result_dialog.py`: 新增的**结果工作台基类**。它定义了一个标准的、带有多标签页的对话框结构，并实现了处理不同预览状态（加载中、就绪、空）的通用逻辑。
    - `fracture_result_dialog.py`: 裂缝分析的**专属工作台**。继承自 `BaseResultDialog`，并添加了裂缝分析特有的结果标签页。
    - `pore_result_dialog.py`: 孔洞分析的**专属工作台**。继承自 `BaseResultDialog`，并添加了孔洞分析特有的结果标签页。

## 核心交互流程

1. **加载图像**: 用户通过`MainWindow`菜单或`ControlPanel`上的按钮加载图像。
2. **选择分析器**: 用户在`ControlPanel`中通过下拉框选择"裂缝分析"或"孔洞分析"。
3. **参数调整**: `ControlPanel`会动态加载与所选分析器对应的参数面板（例如 `FractureParameterPanel`）。当用户调整参数时：
    - 参数面板发射 `parameter_changed` 和 `realtime_preview_requested` 信号。
    - `ControlPanel` 捕获信号并调用 `Controller` 的方法来更新参数。
    - `Controller` 在更新后，如果参数标记为 `realtime`，则立即运行预览分析。
    - `Controller` 发射 `preview_state_changed` 信号，其中包含所有中间步骤的图像数据。
    - **`MainWindow`** 捕获此信号，并将数据传递给当前激活的**结果工作台**（例如 `FractureResultDialog`）。
    - 结果工作台的 `update_content` 方法被调用，它根据接收到的状态（如 `READY`）和图像数据，动态更新其内部的标签页。
4. **执行分析**: 用户点击"开始分析"按钮，触发完整的分析流程。
5. **显示结果**: 分析完成后，`Controller` 发射 `analysis_complete` 信号，`MainWindow`捕获后：
    - 将最终的**定量测量数据**发送给 `ResultPanel` 进行表格和摘要展示。
    - 将包含**最终可视化图像**的完整结果集发送给**结果工作台**，更新其"最终结果"标签页。
    - 将最终的可视化图像也显示在 `MainWindow` 的主预览区。

这种设计将重量级的、多阶段的预览功能从主窗口中分离出来，放到了独立的、可扩展的对话框中，使得主窗口结构更清晰，也为未来添加更多复杂的分析模块提供了便利。

## 设计原则

-   **UI与核心逻辑分离**: UI组件不直接修改业务状态，只负责发出"参数变更意图"和"请求预览"的信号。
-   **`Controller`作为中枢**: `