rock-fracture-analyzer/
│
├── .gitignore              # Git忽略文件配置
├── README.md               # 项目说明文档
├── requirements.txt        # 项目依赖库列表
├── run.py                  # 应用程序主入口脚本
├── structure.md            # (本文档) 项目结构说明
│
├── src/
│   └── app/
│       ├── __init__.py
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   └── main_window.py    # UI层: 主窗口和界面控件
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── controller.py     # 业务逻辑层: 流程控制器
│       │   └── image_processor.py# 数据处理层: 图像处理函数
│       │
│       └── utils/
│           ├── __init__.py
│           └── exceptions.py     # 通用工具: 自定义异常类等
│
└── tests/
    ├── __init__.py
    └── test_image_processor.py # 测试代码: 对核心算法进行单元测试