# Mermaid 图表

本文档包含了项目的主要架构图和流程图，使用Mermaid语法绘制。

## 1. 系统架构图 (System Architecture)

该图展示了应用的主要组件分层和它们之间的依赖关系。

```mermaid
graph TD
    subgraph UI_用户界面层
        MW[MainWindow_主窗口]
        CP[ControlPanel_控制面板]
        RP[ResultPanel_结果面板]
        MSPW[MultiStagePreviewWidget_多阶段预览]
        subgraph ParameterPanels [参数面板]
            FPP[FractureParamsPanel_裂缝参数面板]
            style FPP fill:#cde4ff
        end
    end

    subgraph Core_核心逻辑层
        C[Controller_控制器]
        subgraph Analyzers_策略
            BA[BaseAnalyzer_分析器基类]
            FA[FractureAnalyzer_裂缝分析器]
            style FA fill:#cde4ff
        end
        UC[UnitConverter_单位转换器]
        IO[ImageOperations_图像操作]
        Const[Constants_常量]
    end

    %% Dependencies
    MW --> C
    MW --> CP
    MW --> RP
    MW --> MSPW
    CP --> C
    CP --> FPP
    
    C --> BA
    C -- "Manages" --> FA
    FA -- "Uses" --> IO
    C -- "Uses" --> UC
    C --> Const
    FA --> Const
    MSPW -.-> Const
```

## 2. 实时预览数据流 (Real-time Preview Data Flow)

该序列图详细描述了当用户调整参数时，系统内部的数据流动和方法调用顺序，以实现状态驱动的实时预览。

```mermaid
sequenceDiagram
    participant User as 用户
    participant ParamPanel as 参数面板
    participant Controller as 控制器
    participant Analyzer as 当前分析器
    participant PreviewWidget as 多阶段预览

    User->>ParamPanel: 调整参数 (如移动滑块)
    ParamPanel->>Controller: 调用 update_parameter()
    Controller->>Controller: 更新内部参数
    Controller->>Controller: 调用 run_preview()
    Controller->>PreviewWidget: 发送 preview_state_changed(state='LOADING')
    PreviewWidget->>PreviewWidget: 显示 "加载中..."
    
    Controller->>Analyzer: 调用 run_analysis(image, params)
    Analyzer->>Analyzer: 执行图像处理...
    Analyzer-->>Controller: 返回结果字典
    
    alt 未检测到裂缝
        Controller->>PreviewWidget: 发送 preview_state_changed(state='EMPTY')
        PreviewWidget->>PreviewWidget: 显示 "未检测到有效裂缝"
    else 检测到裂缝
        Controller->>PreviewWidget: 发送 preview_state_changed(state='READY', payload=结果)
        PreviewWidget->>PreviewWidget: 解析payload并显示所有阶段预览图
    end
``` 