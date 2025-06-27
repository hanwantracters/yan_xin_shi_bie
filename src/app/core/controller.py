"""控制器模块，连接UI和业务逻辑。

该模块负责协调UI层和核心处理层之间的交互。
它接收用户操作，调用相应的业务逻辑，并更新UI。

"""

import json
from typing import Dict, Any, List, Optional, Tuple
import copy

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
import cv2
from PIL import Image

from .unit_converter import UnitConverter
from .analyzers.base_analyzer import BaseAnalyzer
from .analyzers.fracture_analyzer import FractureAnalyzer
from .analyzers.pore_analyzer import PoreAnalyzer
from ..utils.constants import PreviewState, ResultKeys, StageKeys

class Controller(QObject):
    """应用程序控制器类，协调UI和业务逻辑。"""
    
    # 信号
    analysis_complete = pyqtSignal(dict)
    preview_state_changed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)

    def __init__(self):
        """初始化控制器。"""
        super().__init__()
        # self.unit_converter = UnitConverter()
        
        # 状态变量
        self.current_image = None
        self.current_dpi = None
        self.current_image_path = None
        self.analysis_params: Dict[str, Any] = {}
        self.default_params: Dict[str, Any] = {}

        # 分析器管理
        self.analyzers: Dict[str, BaseAnalyzer] = {}
        self.active_analyzer: Optional[BaseAnalyzer] = None
        
        self._load_all_default_params()
        self._register_analyzers()

    def _load_all_default_params(self):
        """从配置文件加载所有分析器的默认参数。"""
        try:
            # 假设 config 目录与 run.py 在同一级
            with open('config/default_params.json', 'r', encoding='utf-8') as f:
                self.default_params = json.load(f)
            print("成功加载所有默认参数。")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.error_occurred.emit(f"加载默认参数文件失败: {e}")
            self.default_params = {} # 确保在失败时是个空字典

    def _register_analyzers(self):
        """扫描并注册所有可用的分析器。"""
        # 目前硬编码注册，未来可改为动态扫描
        fracture_analyzer = FractureAnalyzer()
        self.analyzers[fracture_analyzer.get_id()] = fracture_analyzer
        
        pore_analyzer = PoreAnalyzer()
        self.analyzers[pore_analyzer.get_id()] = pore_analyzer

        # 默认激活第一个分析器
        if self.analyzers:
            first_analyzer_id = next(iter(self.analyzers))
            self.set_active_analyzer(first_analyzer_id)

    def get_registered_analyzers(self) -> List[Tuple[str, str]]:
        """获取所有已注册分析器的ID和名称。"""
        return [(analyzer.get_id(), analyzer.get_name()) for analyzer in self.analyzers.values()]

    def set_active_analyzer(self, analyzer_id: str):
        """设置当前激活的分析器，并加载其默认参数。"""
        if analyzer_id in self.analyzers:
            self.active_analyzer = self.analyzers[analyzer_id]
            # 从集中加载的字典中获取默认参数
            default_params = self.default_params.get(analyzer_id, {})
            # 深拷贝以确保每个分析实例有独立的参数副本
            self.analysis_params = copy.deepcopy(default_params)
            self.parameters_updated.emit(self.analysis_params)
            print(f"激活分析器: {self.active_analyzer.get_name()}")
        else:
            self.error_occurred.emit(f"未找到ID为 '{analyzer_id}' 的分析器")

    def get_active_analyzer(self) -> Optional[BaseAnalyzer]:
        return self.active_analyzer

    def load_parameters(self, filepath: str):
        """从文件加载分析参数。"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                params = json.load(f)
            # TODO: 未来可以增加版本和分析器类型校验
            self.analysis_params = params
            print(f"成功从 {filepath} 加载参数。")
            self.parameters_updated.emit(self.analysis_params)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.error_occurred.emit(f"加载参数文件失败: {e}")

    def save_parameters(self, filepath: str):
        """将当前分析参数保存到文件。"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_params, f, ensure_ascii=False, indent=4)
            print(f"参数成功保存至 {filepath}。")
        except IOError as e:
            self.error_occurred.emit(f"保存参数文件失败: {e}")
            
    def update_parameter(self, param_path: str, value: Any):
        """更新一个分析参数，并触发预览。"""
        keys = param_path.split('.')
        d = self.analysis_params
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        
        self.parameters_updated.emit(self.analysis_params)

    def request_realtime_preview(self, stage_key: Optional[str] = None):
        """响应UI的请求，执行一次预览。"""
        self.run_preview(stage_key=stage_key)

    def load_image_from_file(self, file_path: str):
        """从文件加载图像。"""
        try:
            # 图像加载现在是通用功能，不依赖特定处理器
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"无法使用OpenCV加载图像: {file_path}")
            
            with Image.open(file_path) as pil_image:
                dpi_info = pil_image.info.get('dpi')
                self.current_dpi = tuple(map(float, dpi_info)) if dpi_info else (None, None)
            
            self.current_image = image
            self.current_image_path = file_path
            
            return True, f"成功加载图像: {file_path}, DPI: {self.current_dpi}"
        except Exception as e:
            self.error_occurred.emit(f"加载图像时发生错误: {str(e)}")
            return False, f"加载图像时发生错误: {str(e)}"
    


    def run_preview(self, stage_key: Optional[str] = None):
        """使用当前激活的分析器运行一次预览并更新UI。"""
        if self.current_image is None or self.active_analyzer is None:
            return

        self.preview_state_changed.emit({'state': PreviewState.LOADING, 'payload': '正在生成预览...'})
        try:
            
            dpi = self.current_dpi[0] if self.current_dpi and self.current_dpi[0] else 0.0

            if stage_key:
                print(f"[DEBUG Controller] Running STAGED analysis for stage: {stage_key}")
                results = self.active_analyzer.run_staged_analysis(self.current_image, self.analysis_params, stage_key)
                is_empty = not results.get(ResultKeys.PREVIEWS.value)
            else:
                print("[DEBUG Controller] Running FULL analysis for preview.")
                results = self.active_analyzer.run_analysis(self.current_image, self.analysis_params, dpi)
                is_empty = self.active_analyzer.is_result_empty(results)

            if is_empty:
                state_to_emit = {
                    'state': PreviewState.EMPTY,
                    'payload': self.active_analyzer.get_empty_message()
                }
                self.preview_state_changed.emit(state_to_emit)
            else:
                state_to_emit = {
                    'state': PreviewState.READY,
                    'payload': results
                }
                self.preview_state_changed.emit(state_to_emit)

        except Exception as e:
            state_to_emit = {
                'state': PreviewState.ERROR,
                'payload': f"分析时发生错误: {e}"
            }
            self.preview_state_changed.emit(state_to_emit)
            print(f"预览更新失败: {e}")

    def run_full_analysis(self):
        """执行一次完整的分析并发出最终结果。"""
        print("DEBUG: Controller.run_full_analysis() triggered.")
        if self.current_image is None or self.active_analyzer is None:
            self.error_occurred.emit("请先加载一张图像再开始分析。")
            return
            
        try:
            dpi = self.current_dpi[0] if self.current_dpi and self.current_dpi[0] else 0.0
            results = self.active_analyzer.run_analysis(self.current_image, self.analysis_params, dpi)
            
            # 单位转换现在委托给分析器
            final_results = results
            if self.current_dpi and self.current_dpi[0]:
                final_results = self.active_analyzer.post_process_measurements(results, self.current_dpi[0])

          
            self.analysis_complete.emit(final_results)
            print("分析完成。")
        except Exception as e:
            self.error_occurred.emit(f"分析失败: {e}")
            print(f"分析失败: {e}")

    def get_current_image(self):
        return self.current_image
    
    def get_current_dpi(self):
        return self.current_dpi

    def get_current_analyzer_id(self) -> str:
        """获取当前激活的分析器的ID。"""
        return self.active_analyzer.get_id()

    def get_current_parameters(self) -> Dict[str, Any]:
        """获取当前分析器的所有参数。"""
        return self.analysis_params