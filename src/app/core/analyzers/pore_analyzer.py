"""孔洞分析器模块。

该模块实现了BaseAnalyzer接口，专门用于识别和分析图像中的孔洞。
它使用分水岭算法来分割粘连的孔洞。
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
from skimage.feature import peak_local_max
from scipy import ndimage

from .base_analyzer import BaseAnalyzer
from .. import image_operations as ops
from ...utils.constants import ResultKeys, StageKeys
from ..unit_converter import UnitConverter

class PoreAnalyzer(BaseAnalyzer):
    """
    孔洞分析器，使用分水岭算法处理孔洞粘连问题。
    """

    def __init__(self):
        super().__init__()
        self.unit_converter = UnitConverter()

    def get_name(self) -> str:
        return "孔洞分析 (分水岭)"

    def get_id(self) -> str:
        return "pore_watershed"

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'threshold': {
                'method': 'otsu',
                'value': 128,
                'block_size': 51,
                'c': 2,
                'window_size': 51,
                'k': 0.2,
                'r': 128,
                'ui_hints': {'realtime': True}
            },
            'morphology': {
                'opening_ksize': 3,
                'sure_bg_ksize': 3,
                'ui_hints': {'realtime': True}
            },
            'filtering': {
                'min_solidity': 0.85,
                'min_area_pixels': 20,
                'ui_hints': {'realtime': False}
            }
        }

    def run_analysis(self, image: np.ndarray, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行孔洞分析的完整流程。"""
        # 1. 预处理
        gray = ops.convert_to_grayscale(image)
        blurred = ops.apply_gaussian_blur(gray, kernel_size=(7, 7))

        # 2. 阈值分割
        thresh = ops.apply_otsu_threshold(blurred)[0]

        # 3. 形态学处理与分水岭准备
        markers, sure_fg, sure_bg, unknown = self._prepare_for_watershed(
            thresh, params.get('morphology', {})
        )

        # 4. 执行分水岭算法
        markers = cv2.watershed(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), markers)
        
        # 5. 分析和过滤孔洞
        pores = self._analyze_and_filter_pores(
            markers, image, params.get('filtering', {})
        )
        
        # 6. 可视化和测量
        visualization = self._draw_analysis_results(image.copy(), pores)
        measurements = self._calculate_measurements(pores, image.shape[0] * image.shape[1])

        return {
            ResultKeys.VISUALIZATION.value: visualization,
            ResultKeys.MEASUREMENTS.value: measurements,
            ResultKeys.PREVIEWS.value: {
                StageKeys.GRAY.value: gray,
                StageKeys.BINARY.value: thresh,
            }
        }
        
    def _prepare_for_watershed(self, thresh: np.ndarray, params: dict) -> Tuple:
        """为分水岭算法准备标记。"""
        # 开运算去噪声
        kernel = np.ones((params.get('opening_ksize', 3),) * 2, np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

        # 确定背景
        sure_bg = cv2.dilate(opening, kernel, iterations=params.get('sure_bg_ksize', 3))

        # 距离变换确定前景
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.6 * dist_transform.max(), 255, 0)
        
        # 寻找未知区域
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)

        # 创建标记
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        
        return markers, sure_fg, sure_bg, unknown
        
    def _analyze_and_filter_pores(self, markers: np.ndarray, image: np.ndarray, params: dict) -> List[Dict]:
        """分析、过滤分水岭算法分割出的区域。"""
        min_solidity = params.get('min_solidity', 0.85)
        min_area = params.get('min_area_pixels', 20)
        
        valid_pores = []
        labels = np.unique(markers)
        
        for label in labels:
            if label < 2:  # 0是未知区域, 1是背景
                continue

            mask = np.zeros(markers.shape, dtype="uint8")
            mask[markers == label] = 255
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            
            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)
            hull_area = cv2.contourArea(cv2.convexHull(contour))
            
            if area < min_area or hull_area == 0:
                continue

            solidity = area / hull_area
            if solidity < min_solidity:
                continue
            
            valid_pores.append({
                'contour': contour,
                'area_pixels': area,
                'solidity': solidity,
            })
        return valid_pores

    def _draw_analysis_results(self, image: np.ndarray, pores: List[Dict]) -> np.ndarray:
        """可视化结果。"""
        for pore in pores:
            color = np.random.randint(0, 255, size=(3,)).tolist()
            cv2.drawContours(image, [pore['contour']], -1, color, 2)
            cv2.fillPoly(image, [pore['contour']], color)
        return image

    def _calculate_measurements(self, pores: List[Dict], image_area_pixels: int) -> Dict:
        """计算测量数据。"""
        count = len(pores)
        total_area = sum(p['area_pixels'] for p in pores)
        porosity = total_area / image_area_pixels if image_area_pixels > 0 else 0

        return {
            'count': count,
            'total_area_pixels': total_area,
            'porosity': porosity,
            'details': pores
        }

    def is_result_empty(self, results: Dict[str, Any]) -> bool:
        """检查孔洞分析结果是否为空。"""
        return results.get(ResultKeys.MEASUREMENTS.value, {}).get('count', 0) == 0

    def get_empty_message(self) -> str:
        """返回孔洞分析的空结果消息。"""
        return "未检测到有效孔洞"

    def post_process_measurements(self, results: Dict[str, Any], dpi: float) -> Dict[str, Any]:
        """将孔洞测量的像素单位转换为物理单位。"""
        measurements = results.get(ResultKeys.MEASUREMENTS.value, {})
        if not measurements or not dpi:
            return results

        converted_measurements = measurements.copy()

        if 'total_area_pixels' in measurements:
            converted_measurements['total_area_mm2'] = self.unit_converter.convert_area(
                measurements['total_area_pixels'], dpi
            )

        if 'details' in measurements:
            converted_details = []
            for detail in measurements['details']:
                new_detail = detail.copy()
                if 'area_pixels' in new_detail:
                    new_detail['area_mm2'] = self.unit_converter.convert_area(
                        new_detail['area_pixels'], dpi
                    )
                converted_details.append(new_detail)
            converted_measurements['details'] = converted_details
            
        final_results = results.copy()
        final_results[ResultKeys.MEASUREMENTS.value] = converted_measurements
        return final_results 