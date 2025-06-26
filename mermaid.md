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
            PPP[PoreParamsPanel_孔洞参数面板]
            style FPP fill:#cde4ff
            style PPP fill:#cde4ff
        end
    end

    subgraph Core_核心逻辑层
        C[Controller_控制器]
        subgraph Analyzers_策略
            BA[BaseAnalyzer_分析器基类]
            FA[FractureAnalyzer_裂缝分析器]
            PA[PoreAnalyzer_孔洞分析器]
            style FA fill:#cde4ff
            style PA fill:#cde4ff
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
    CP --> PPP
    
    C --> BA
    C -- "Manages" --> FA
    C -- "Manages" --> PA
    FA -- "Uses" --> IO
    PA -- "Uses" --> IO
    C -- "Uses" --> UC
    C --> Const
    FA --> Const
    PA --> Const
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
    ParamPanel->>Controller: 调用 update_parameter(key, value)
    Controller->>Controller: 更新内部参数
    
    alt 参数需要实时预览 (ui_hints.realtime=true)
        Controller->>Controller: 调用 run_preview()
        Controller->>PreviewWidget: 发送 preview_state_changed(state='LOADING')
        PreviewWidget->>PreviewWidget: 显示 "加载中..."
        
        Controller->>Analyzer: 调用 run_analysis(image, params)
        Analyzer->>Analyzer: 执行图像处理...
        Analyzer-->>Controller: 返回结果字典
        
        alt 未检测到有效结果
            Controller->>PreviewWidget: 发送 preview_state_changed(state='EMPTY')
            PreviewWidget->>PreviewWidget: 显示 "未检测到有效结果"
        else 检测到有效结果
            Controller->>PreviewWidget: 发送 preview_state_changed(state='READY', payload=结果)
            PreviewWidget->>PreviewWidget: 解析payload并显示所有阶段预览图
        end
    else 参数不需要实时预览
        Controller->>Controller: 仅更新参数，不触发预览
    end
``` 

## 3. 参数实时预览控制流程 (Parameter Real-time Preview Control Flow)

此图展示了如何通过参数定义中的 ui_hints 属性来控制不同参数的实时预览行为。

```mermaid
graph TD
    subgraph 参数定义
        P1[参数1: ui_hints.realtime=true]
        P2[参数2: ui_hints.realtime=false]
    end
    
    subgraph 控制器
        UP[update_parameter方法]
        RP[run_preview方法]
        FA[run_full_analysis方法]
    end
    
    subgraph 用户界面
        UI1[参数调整控件]
        UI2[一键分析按钮]
        PV[预览窗口]
    end
    
    UI1 -->|参数变更| UP
    UP -->|检查ui_hints| C{需要实时预览?}
    C -->|是| RP
    C -->|否| D[仅更新参数]
    
    UI2 -->|点击| FA
    FA -->|总是触发| PV
    RP -->|触发| PV
``` 