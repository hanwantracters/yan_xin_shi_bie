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
        # self.unit_converter = UnitConverter()

    def get_name(self) -> str:
        return "孔洞分析 (分水岭)"

    def get_id(self) -> str:
        return "pore_watershed"

    def run_analysis(self, image: np.ndarray, params: Dict[str, Any], dpi: float = 0.0) -> Dict[str, Any]:
        """执行孔洞分析的完整流程。"""
        print("[DEBUG PoreAnalyzer] --- run_analysis START ---")
        # 1. 预处理
        gray = ops.convert_to_grayscale(image)
        blurred = ops.apply_gaussian_blur(gray, kernel_size=(7, 7))

        # 2. 阈值分割
        thresh = self._apply_threshold(blurred, params.get('threshold', {}))

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

        final_result = {
            ResultKeys.VISUALIZATION.value: visualization,
            ResultKeys.MEASUREMENTS.value: measurements,
            ResultKeys.PREVIEWS.value: {
                StageKeys.GRAY.value: gray,
                StageKeys.BINARY.value: thresh,
            }
        }
        print(f"[DEBUG PoreAnalyzer] Returning result with keys: {final_result.keys()} and preview keys: {final_result[ResultKeys.PREVIEWS.value].keys()}")
        print("[DEBUG PoreAnalyzer] --- run_analysis END ---")
        return final_result

    def run_staged_analysis(self, image: np.ndarray, params: Dict[str, Any], stage_key: str) -> Dict[str, Any]:
        """执行到指定阶段的孔洞分析，用于预览。"""
        # 1. 预处理
        gray = ops.convert_to_grayscale(image)
        blurred = ops.apply_gaussian_blur(gray, kernel_size=(7, 7))

        # 2. 阈值分割
        binary = self._apply_threshold(blurred, params.get('threshold', {}))
        
        previews = {
            StageKeys.GRAY.value: gray,
            StageKeys.BINARY.value: binary
        }

        if stage_key == StageKeys.BINARY.value:
            return { ResultKeys.PREVIEWS.value: previews }

        # 3. 形态学处理 (用于预览)
        morph_params = params.get('morphology', {})
        ksize = morph_params.get('opening_ksize', 3)
        iterations = morph_params.get('opening_iterations', 2)
        kernel = np.ones((ksize, ksize), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=iterations)
        
        previews[StageKeys.MORPH.value] = opening

        # 对于孔洞分析，目前预览只支持到形态学处理
        return { ResultKeys.PREVIEWS.value: previews }
        
    def _apply_threshold(self, image: np.ndarray, params: dict) -> np.ndarray:
        """根据参数应用不同的阈值算法（带弹性查找）。"""
        method = params.get('method')

        if method == 'global':
            value = params.get('global_value', params.get('value'))
            return ops.apply_global_threshold(image, value)

        elif method == 'adaptive_gaussian':
            block_size = params.get('adaptive_block_size', params.get('block_size'))
            c = params.get('adaptive_c_value', params.get('c'))
            return ops.apply_adaptive_gaussian_threshold(image, block_size, c)

        elif method == 'otsu':
            binary, _ = ops.apply_otsu_threshold(image)
            return binary

        elif method == 'niblack':
            window_size = params.get('niblack_window_size', params.get('window_size'))
            k = params.get('niblack_k', params.get('k'))
            return ops.apply_niblack_threshold(image, window_size, k)

        elif method == 'sauvola':
            window_size = params.get('sauvola_window_size', params.get('window_size'))
            k = params.get('sauvola_k', params.get('k'))
            r = params.get('sauvola_r', params.get('r'))
            return ops.apply_sauvola_threshold(image, window_size, k, r)
            
        # 如果方法未知或未提供，则返回原始图像以避免崩溃
        print(f"警告: 未知的阈值方法 '{method}' 或参数不足。")
        return image
        
    def _prepare_for_watershed(self, thresh: np.ndarray, params: dict) -> Tuple:
        """为分水岭算法准备标记。"""
        # 开运算去噪声
        ksize = params.get('opening_ksize', 3)
        iterations = params.get('opening_iterations', 2)
        kernel = np.ones((ksize, ksize), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=iterations)

        # 确定背景
        bg_ksize = params.get('sure_bg_ksize', 3)
        bg_kernel = np.ones((bg_ksize, bg_ksize), np.uint8)
        sure_bg = cv2.dilate(opening, bg_kernel, iterations=1) # 通常背景膨胀迭代1次就够

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
            converted_measurements['total_area_mm2'] = UnitConverter.convert_area(
                measurements['total_area_pixels'], dpi
            )

        if 'details' in measurements:
            converted_details = []
            for detail in measurements['details']:
                new_detail = detail.copy()
                if 'area_pixels' in new_detail:
                    new_detail['area_mm2'] = UnitConverter.convert_area(
                        new_detail['area_pixels'], dpi
                    )
                converted_details.append(new_detail)
            converted_measurements['details'] = converted_details
            
        final_results = results.copy()
        final_results[ResultKeys.MEASUREMENTS.value] = converted_measurements
        return final_results 