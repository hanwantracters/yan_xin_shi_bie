# UI组件

该目录包含应用程序的所有用户界面组件。

## 文件说明

- `main_window.py`: 主窗口，组织所有UI组件
- `control_panel.py`: 控制面板，包含操作按钮和参数调整控件
- `preview_window.py`: 图像预览窗口，显示图像
- `analysis_preview_window.py`: 分析预览窗口，显示各个处理阶段的结果
- `threshold_preview_window.py`: 阈值预览窗口(已弃用，由analysis_preview_window替代)
- `result_panel.py`: 结果显示面板，展示分析数据
- `measurement_dialog.py`: 测量对话框，实现手动测量功能
- `morphology_settings_dialog.py`: 形态学参数设置对话框
- `style_manager.py`: 样式管理器，统一管理应用的样式表

## 组件交互

UI组件通过Qt信号槽机制进行交互，主窗口负责协调各组件之间的通信。
主窗口持有控制器实例，并将用户操作转发给控制器处理。

## 界面设计原则

- 简洁清晰: 减少视觉干扰，突出重要信息
- 即时反馈: 操作后立即显示结果
- 分阶段展示: 通过分析预览窗口，用户可查看处理的每个阶段

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