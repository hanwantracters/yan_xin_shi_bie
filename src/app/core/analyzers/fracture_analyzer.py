"""裂缝分析器模块。

该模块实现了BaseAnalyzer接口，专门用于识别和分析图像中的裂缝。
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
from skimage.morphology import skeletonize

from .base_analyzer import BaseAnalyzer
from .. import image_operations as ops
from ...utils.constants import ResultKeys, StageKeys
from ..unit_converter import UnitConverter

class FractureAnalyzer(BaseAnalyzer):
    """
    裂缝分析器，负责执行所有与裂缝相关的计算和处理。
    """
    def __init__(self):
        super().__init__()
        self.unit_converter = UnitConverter()

    def get_name(self) -> str:
        return "裂缝分析"

    def get_id(self) -> str:
        return "fracture"

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'threshold': {
                'method': 'sauvola',
                'value': 128,
                'block_size': 51,
                'c': 2,
                'window_size': 51,
                'k': 0.2,
                'r': 128,
                'ui_hints': {'realtime': True}
            },
            'morphology': {
                'opening': {
                    'enabled': True,
                    'kernel_shape': 'rect',
                    'kernel_size': (3, 3),
                    'iterations': 2,
                    'min_area': 10,
                },
                'closing': {
                    'enabled': True,
                    'kernel_shape': 'rect',
                    'kernel_size': (3, 3),
                    'iterations': 1,
                },
                'ui_hints': {'realtime': True}
            },
            'filtering': {
                'min_aspect_ratio': 5.0,
                'min_length_pixels': 10.0,
                'ui_hints': {'realtime': False}
            }
        }
    
    def run_analysis(self, image: np.ndarray, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行裂缝分析的完整流程。"""
        # 1. 预处理
        gray = ops.convert_to_grayscale(image)
        blurred = ops.apply_gaussian_blur(gray)

        # 2. 阈值分割
        binary = self._apply_threshold(blurred, params.get('threshold', {}))
        
        # 3. 形态学处理
        binary_processed = ops.apply_morphological_postprocessing(
            binary,
            opening_params=params.get('morphology', {}).get('opening'),
            closing_params=params.get('morphology', {}).get('closing')
        )
        
        # 4. 裂缝分析与过滤
        fractures = self._analyze_and_filter_fractures(
            binary_processed,
            params.get('filtering', {})
        )
        
        # 5. 结果可视化
        visualization = self._draw_analysis_results(image.copy(), fractures)
        
        # 6. 定量测量
        measurements = self._calculate_measurements(fractures)

        final_result = {
            ResultKeys.VISUALIZATION.value: visualization,
            ResultKeys.MEASUREMENTS.value: measurements,
            ResultKeys.PREVIEWS.value: {
                StageKeys.GRAY.value: gray,
                StageKeys.BINARY.value: binary,
                StageKeys.MORPH.value: binary_processed,
            }
        }
        print(f"[DEBUG FractureAnalyzer] Returning result with keys: {final_result.keys()}")
        return final_result

    def _apply_threshold(self, image: np.ndarray, params: dict) -> np.ndarray:
        """根据参数应用不同的阈值算法（带弹性查找）。"""
        method = params.get('method', 'sauvola')
        defaults = self.get_default_parameters()['threshold']

        if method == 'global':
            value = params.get('global_value', params.get('value', defaults['value']))
            return ops.apply_global_threshold(image, value)

        elif method == 'adaptive_gaussian':
            block_size = params.get('adaptive_block_size', params.get('block_size', defaults['block_size']))
            c = params.get('adaptive_c_value', params.get('c', defaults['c']))
            return ops.apply_adaptive_gaussian_threshold(image, block_size, c)

        elif method == 'otsu':
            binary, _ = ops.apply_otsu_threshold(image)
            return binary

        elif method == 'niblack':
            window_size = params.get('niblack_window_size', params.get('window_size', defaults['window_size']))
            k = params.get('niblack_k', params.get('k', defaults['k']))
            return ops.apply_niblack_threshold(image, window_size, k)

        elif method == 'sauvola':
            window_size = params.get('sauvola_window_size', params.get('window_size', defaults['window_size']))
            k = params.get('sauvola_k', params.get('k', defaults['k']))
            r = params.get('sauvola_r', params.get('r', defaults['r']))
            return ops.apply_sauvola_threshold(image, window_size, k, r)
            
        return image

    def _analyze_and_filter_fractures(self, binary_image: np.ndarray, params: dict) -> List[Dict]:
        """从二值图中分析和过滤裂缝。"""
        min_aspect_ratio = params.get('min_aspect_ratio', 5.0)
        min_length_pixels = params.get('min_length_pixels', 0.0)

        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_fractures = []
        for contour in contours:
            if len(contour) < 5:
                continue

            area = cv2.contourArea(contour)
            rect = cv2.minAreaRect(contour)
            (w, h) = rect[1]
            if w == 0 or h == 0:
                continue
            
            aspect_ratio = max(w, h) / min(w, h)
            
            # 骨架化计算精确长度
            mask = np.zeros(binary_image.shape, np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            skeleton = skeletonize(mask / 255)
            length_pixels = np.sum(skeleton)

            if aspect_ratio >= min_aspect_ratio and length_pixels >= min_length_pixels:
                valid_fractures.append({
                    'contour': contour,
                    'area_pixels': area,
                    'length_pixels': length_pixels,
                    'aspect_ratio': aspect_ratio,
                    'angle': rect[2]
                })
        return valid_fractures
        
    def _draw_analysis_results(self, original_image: np.ndarray, fractures: List[Dict]) -> np.ndarray:
        """将分析结果绘制在原始图像上。"""
        if not fractures:
            return original_image
            
        result_image = original_image.copy()
        for fracture in fractures:
            cv2.drawContours(result_image, [fracture['contour']], -1, (0, 255, 0), 2)
        return result_image

    def _calculate_measurements(self, fractures: List[Dict]) -> Dict:
        """计算最终的测量统计数据。"""
        count = len(fractures)
        total_area = sum(f['area_pixels'] for f in fractures)
        total_length = sum(f['length_pixels'] for f in fractures)

        measurements = {
            'count': count,
            'total_area_pixels': total_area,
            'total_length_pixels': total_length,
            'details': fractures
        }

        print(f"[DEBUG FractureAnalyzer] 生成的测量数据: {measurements}")
        return measurements

    def is_result_empty(self, results: Dict[str, Any]) -> bool:
        """检查裂缝分析结果是否为空。"""
        measurements = results.get(ResultKeys.MEASUREMENTS.value, {})
        return measurements.get('count', 0) == 0

    def get_empty_message(self) -> str:
        """返回裂缝分析的空结果消息。"""
        return "未检测到有效裂缝"

    def post_process_measurements(self, results: Dict[str, Any], dpi: float) -> Dict[str, Any]:
        """将裂缝测量的像素单位转换为物理单位（毫米）。"""
        measurements = results.get(ResultKeys.MEASUREMENTS.value, {})
        if not measurements or not dpi:
            return results

        converted_measurements = measurements.copy()
        
        if 'total_area_pixels' in measurements:
            converted_measurements['total_area_mm2'] = self.unit_converter.convert_area(
                measurements['total_area_pixels'], dpi
            )
        if 'total_length_pixels' in measurements:
            converted_measurements['total_length_mm'] = self.unit_converter.convert_distance(
                measurements['total_length_pixels'], dpi
            )

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
            
        final_results = results.copy()
        final_results[ResultKeys.MEASUREMENTS.value] = converted_measurements
        return final_results 