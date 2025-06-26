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
│       ├── ui/                     # UI层: 包含所有用户界面组件
│       │   ├── README.md            # UI层架构说明
│       │   ├── __init__.py
│       │   ├── main_window.py       # UI层: 主窗口
│       │   ├── control_panel.py     # UI层: 控制面板，负责模式选择和参数面板切换
│       │   ├── result_panel.py      # UI层: 结果面板组件
│       │   ├── multi_stage_preview_widget.py # UI层: 多阶段预览窗口
│       │   ├── measurement_dialog.py# UI层: 测量对话框组件
│       │   ├── morphology_settings_dialog.py # UI层: 形态学参数对话框
│       │   ├── filtering_settings_dialog.py  # UI层: 过滤参数对话框
│       │   ├── threshold_settings_dialog.py  # UI层: 阈值参数对话框
│       │   ├── style_manager.py     # UI层: 样式表管理器
│       │   ├── dialogs/             # UI层: 存放各种设置对话框
│       │   │   └── pore_filtering_dialog.py  # UI层: 孔洞过滤参数对话框
│       │   └── parameter_panels/    # UI层: 存放不同分析器对应的参数面板
│       │       ├── __init__.py
│       │       ├── fracture_params_panel.py # UI层: 裂缝分析器的参数面板
│       │       └── pore_params_panel.py # UI层: 孔洞分析器的参数面板
│       │
│       ├── core/                   # 业务与数据层: 包含核心业务逻辑与数据处理
│       │   ├── README.md            # 核心逻辑层架构说明
│       │   ├── __init__.py
│       │   ├── controller.py        # 业务逻辑层: 流程控制器，管理分析策略
│       │   ├── image_operations.py  # 数据处理层: 原子化的图像处理函数
│       │   ├── unit_converter.py    # 工具: 像素和物理单位转换器
│       │   └── analyzers/           # 策略层: 包含所有具体的分析策略 (Analyzer)
│       │       ├── __init__.py
│       │       ├── base_analyzer.py # 策略接口: 定义分析器的通用接口
│       │       ├── fracture_analyzer.py # 具体策略: 裂缝分析的实现
│       │       └── pore_analyzer.py # 具体策略: 孔洞分析的实现
│       │
│       └── utils/                  # 通用工具: 包含自定义异常、常量等
│           ├── README.md            # 通用工具模块说明
│           ├── __init__.py
│           ├── constants.py         # 通用工具: 定义项目中使用的常量
│           └── exceptions.py        # 通用工具: 自定义异常类等
│
└── tests/
    ├── __init__.py
    ├── test_architecture_wiring.py # 测试代码: 验证架构中核心组件的连接
    ├── test_control_panel_wiring.py# 测试代码: 验证控制面板的信号连接
    └── test_refactoring_integrity.py# 测试代码: 确保重构后接口一致性