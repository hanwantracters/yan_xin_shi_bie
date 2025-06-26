"""控制器模块，连接UI和业务逻辑。

该模块负责协调UI层和核心处理层之间的交互。
它接收用户操作，调用相应的业务逻辑，并更新UI。

"""

import json
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
import cv2
from PIL import Image

from .unit_converter import UnitConverter
from .analyzers.base_analyzer import BaseAnalyzer
from .analyzers.fracture_analyzer import FractureAnalyzer
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
        self.unit_converter = UnitConverter()
        
        # 状态变量
        self.current_image = None
        self.current_dpi = None
        self.current_image_path = None
        self.analysis_params: Dict[str, Any] = {}

        # 分析器管理
        self.analyzers: Dict[str, BaseAnalyzer] = {}
        self.active_analyzer: Optional[BaseAnalyzer] = None
        self._register_analyzers()

    def _register_analyzers(self):
        """扫描并注册所有可用的分析器。"""
        # 目前硬编码注册，未来可改为动态扫描
        fracture_analyzer = FractureAnalyzer()
        self.analyzers[fracture_analyzer.get_id()] = fracture_analyzer
        
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
            self.analysis_params = self.active_analyzer.get_default_parameters()
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
        
        print(f"参数已更新: {param_path} = {value}")
        self.parameters_updated.emit(self.analysis_params)

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
    
    def run_preview(self):
        """使用当前激活的分析器运行一次预览并更新UI。"""
        if self.current_image is None or self.active_analyzer is None:
            return

        self.preview_state_changed.emit({'state': PreviewState.LOADING})
        try:
            results = self.active_analyzer.run_analysis(self.current_image, self.analysis_params)
            
            measurements = results.get(ResultKeys.MEASUREMENTS.value, {})
            if not measurements or measurements.get('count', 0) == 0:
                state_to_emit = {
                    'state': PreviewState.EMPTY,
                    'payload': '未检测到有效裂缝'
                }
                print(f"DEBUG Controller: Emitting EMPTY state. Payload: {state_to_emit}")
                self.preview_state_changed.emit(state_to_emit)
            else:
                state_to_emit = {
                    'state': PreviewState.READY,
                    'payload': results
                }
                print(f"DEBUG Controller: Emitting READY state with payload keys: {results.keys()}")
                self.preview_state_changed.emit(state_to_emit)

        except Exception as e:
            state_to_emit = {
                'state': PreviewState.ERROR,
                'payload': f"分析时发生错误: {e}"
            }
            print(f"DEBUG Controller: Emitting ERROR state. Payload: {state_to_emit}")
            self.preview_state_changed.emit(state_to_emit)
            print(f"预览更新失败: {e}")

    def run_full_analysis(self):
        """执行一次完整的分析并发出最终结果。"""
        print("DEBUG: Controller.run_full_analysis() triggered.")
        if self.current_image is None or self.active_analyzer is None:
            self.error_occurred.emit("请先加载一张图像再开始分析。")
            return
            
        try:
            results = self.active_analyzer.run_analysis(self.current_image, self.analysis_params)
            
            # 如果有DPI信息，则进行单位转换
            final_results = results
            if self.current_dpi and self.current_dpi[0]:
                final_results = self._convert_measurements_to_mm(results, self.current_dpi[0])

            self.analysis_complete.emit(final_results)
            print("分析完成。")
        except Exception as e:
            self.error_occurred.emit(f"分析失败: {e}")
            print(f"分析失败: {e}")

    def _convert_measurements_to_mm(self, results: Dict, dpi: float) -> Dict:
        """使用UnitConverter将结果字典中的像素单位转换为物理单位。"""
        
        measurements = results.get(ResultKeys.MEASUREMENTS.value, {})
        if not measurements:
            return results

        # 创建一个新的字典来存储转换后的结果，以免修改原始结果
        converted_measurements = measurements.copy()
        
        # 转换总面积和总长度
        if 'total_area_pixels' in measurements:
            converted_measurements['total_area_mm2'] = self.unit_converter.convert_area(
                measurements['total_area_pixels'], dpi
            )
        if 'total_length_pixels' in measurements:
            converted_measurements['total_length_mm'] = self.unit_converter.convert_distance(
                measurements['total_length_pixels'], dpi
            )

        # 转换每个裂缝的详细信息
        if 'details' in measurements:
            converted_details = []
            for detail in measurements['details']:
                new_detail = detail.copy()
                if 'area_pixels' in new_detail:
                    new_detail['area_mm2'] = self.unit_converter.convert_area(
                        new_detail['area_pixels'], dpi
                    )
                if 'length_pixels' in new_detail:
                    new_detail['length_mm'] = self.unit_converter.convert_distance(
                        new_detail['length_pixels'], dpi
                    )
                converted_details.append(new_detail)
            converted_measurements['details'] = converted_details
            
        # 将转换后的测量结果放回主结果字典
        final_results = results.copy()
        final_results[ResultKeys.MEASUREMENTS.value] = converted_measurements
        return final_results

    def get_current_image(self):
        return self.current_image
    
    def get_current_dpi(self):
        return self.current_dpi

    def get_current_parameters(self) -> Dict[str, Any]:
        """获取当前激活分析器的参数。"""
        return self.analysis_params