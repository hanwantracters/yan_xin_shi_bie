rock-fracture-analyzer/
│
├── .gitignore              # Git忽略文件配置
├── mermaid.md              # Mermaid图表文档
├── readme.md               # 项目说明文档
├── requirements.md         # 项目需求列表
├── run.py                  # 应用程序主入口脚本
├── structure.md            # (本文档) 项目结构说明
│
├── src/
│   └── app/
│       ├── __init__.py
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py       # UI层: 主窗口
│       │   ├── control_panel.py     # UI层: 控制面板组件
│       │   ├── result_panel.py      # UI层: 结果面板组件
│       │   ├── preview_window.py    # UI层: 预览窗口组件
│       │   ├── analysis_preview_window.py # UI层: 分析预览窗口组件
│       │   ├── measurement_dialog.py# UI层: 测量对话框组件
│       │   └── style_manager.py     # UI层: 样式表管理器
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── controller.py        # 业务逻辑层: 流程控制器
│       │   ├── image_processor.py   # 数据处理层: 图像处理函数
│       │   ├── analysis_stages.py   # 数据模型: 分析阶段枚举定义
│       │   └── unit_converter.py    # 工具: 像素和物理单位转换器
│       │
│       └── utils/
│           ├── __init__.py
│           └── exceptions.py        # 通用工具: 自定义异常类等
│
└── tests/
    ├── __init__.py
    └── test_image_processor.py     # 测试代码: 对核心算法进行单元测试