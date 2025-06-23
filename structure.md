rock-fracture-analyzer/
│
├── .gitignore              # Git忽略文件配置
├── mermaid.md              # Mermaid图表文档
├── readme.md               # 项目说明文档
├── requirements.txt        # Python依赖包列表
├── requirement_status.md   # 项目需求列表
├── run.py                  # 应用程序主入口脚本
├── structure.md            # (本文档) 项目结构说明
│
├── src/
│   └── app/
│       ├── __init__.py
│       │
│       ├── ui/                     # UI层: 包含所有用户界面组件 (详见该目录下的README.md)
│       │   ├── __init__.py
│       │   ├── main_window.py       # UI层: 主窗口
│       │   ├── control_panel.py     # UI层: 控制面板组件
│       │   ├── result_panel.py      # UI层: 结果面板组件
│       │   ├── preview_window.py    # UI层: 预览窗口组件
│       │   ├── analysis_preview_window.py # UI层: 分析预览窗口组件
│       │   ├── threshold_settings_dialog.py # UI层: 二值化参数设置对话框
│       │   ├── morphology_settings_dialog.py # UI层: 形态学参数设置对话框
│       │   ├── filtering_settings_dialog.py # UI层: 过滤与合并参数设置对话框
│       │   ├── measurement_dialog.py# UI层: 测量对话框组件
│       │   └── style_manager.py     # UI层: 样式表管理器
│       │
│       ├── core/                   # 业务与数据层: 包含核心业务逻辑与数据处理 (详见该目录下的README.md)
│       │   ├── __init__.py
│       │   ├── controller.py        # 业务逻辑层: 流程控制器
│       │   ├── image_processor.py   # 数据处理层: 图像处理函数
│       │   ├── analysis_stages.py   # 数据模型: 分析阶段枚举定义
│       │   └── unit_converter.py    # 工具: 像素和物理单位转换器
│       │
│       └── utils/                  # 通用工具: 包含自定义异常等 (详见该目录下的README.md)
│           ├── __init__.py
│           └── exceptions.py        # 通用工具: 自定义异常类等
│
└── tests/
    ├── __init__.py
    ├── test_controller.py          # 测试代码: 对控制器逻辑进行单元测试
    ├── test_image_processor.py     # 测试代码: 对核心图像算法进行单元测试
    ├── test_unit_converter.py      # 测试代码: 对单位转换器进行单元测试
    └── test_dialog_opening.py      # 测试代码: 验证设置对话框能被正确打开