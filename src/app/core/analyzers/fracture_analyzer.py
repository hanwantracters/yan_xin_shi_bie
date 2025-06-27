"""裂缝分析器模块。

该模块实现了BaseAnalyzer接口，专门用于识别和分析图像中的裂缝。
"""

import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
from skimage.morphology import skeletonize
from src.app.core.analyzers.base_analyzer import BaseAnalyzer
from src.app.core import image_operations as ops
from src.app.utils.constants import ResultKeys, StageKeys
from src.app.core.unit_converter import UnitConverter

class FractureAnalyzer(BaseAnalyzer):
    """
    裂缝分析器，负责执行所有与裂缝相关的计算和处理。
    """
    def __init__(self):
        super().__init__()
        # UnitConverter 都是静态方法，不再需要实例
        # self.unit_converter = UnitConverter()

    def get_name(self) -> str:
        return "裂缝分析"

    def get_id(self) -> str:
        return "fracture"

    def run_analysis(self, image: np.ndarray, params: Dict[str, Any], dpi: float = 0.0) -> Dict[str, Any]:
        """执行裂缝分析的完整流程。"""
        print("[DEBUG FractureAnalyzer] --- run_analysis START ---")
        
        # 1. 预处理
        gray = ops.convert_to_grayscale(image)
        blurred = ops.apply_gaussian_blur(gray)
        print("[DEBUG FractureAnalyzer] Grayscale conversion and blurring complete.")

        # 2. 阈值分割
        binary = self._apply_threshold(blurred, params.get('threshold', {}))
        print("[DEBUG FractureAnalyzer] Thresholding complete.")
        
        # 3. 形态学处理 (参数适配)
        opening_params, closing_params = self._prepare_morph_params(params.get('morphology', {}))
        binary_processed = ops.apply_morphological_postprocessing(
            binary,
            opening_params=opening_params,
            closing_params=closing_params
        )
        print("[DEBUG FractureAnalyzer] Morphological processing complete.")
        
        # 4. 裂缝分析与过滤
        fractures = self._analyze_and_filter_fractures(
            binary_processed,
            params.get('filtering', {})
        )
        print(f"[DEBUG FractureAnalyzer] Contour analysis complete. Found {len(fractures)} fractures.")

        # 5. 合并裂缝
        merged_fractures = self._merge_fractures(fractures, params.get('merging', {}), dpi)
        print(f"[DEBUG FractureAnalyzer] Merging complete. Resulted in {len(merged_fractures)} fractures.")
        
        # 6. 结果可视化
        visualization = self._draw_analysis_results(image.copy(), merged_fractures)
        
        # 7. 定量测量
        measurements = self._calculate_measurements(merged_fractures)

        final_result = {
            ResultKeys.VISUALIZATION.value: visualization,
            ResultKeys.MEASUREMENTS.value: measurements,
            ResultKeys.PREVIEWS.value: {
                StageKeys.GRAY.value: gray,
                StageKeys.BINARY.value: binary,
                StageKeys.MORPH.value: binary_processed,
            }
        }
        print("[DEBUG FractureAnalyzer] --- run_analysis END ---")
        print(f"[DEBUG FractureAnalyzer] Returning result with keys: {final_result.keys()}")
        return final_result

    def run_staged_analysis(self, image: np.ndarray, params: Dict[str, Any], stage_key: str) -> Dict[str, Any]:
        """执行到指定阶段的裂缝分析，用于预览。"""
        # 1. 预处理
        gray = ops.convert_to_grayscale(image)
        blurred = ops.apply_gaussian_blur(gray)

        # 2. 阈值分割
        binary = self._apply_threshold(blurred, params.get('threshold', {}))
        
        previews = {
            StageKeys.GRAY.value: gray,
            StageKeys.BINARY.value: binary
        }

        if stage_key == StageKeys.BINARY.value:
            return { ResultKeys.PREVIEWS.value: previews }

        # 3. 形态学处理 (参数适配)
        opening_params, closing_params = self._prepare_morph_params(params.get('morphology', {}))
        binary_processed = ops.apply_morphological_postprocessing(
            binary,
            opening_params=opening_params,
            closing_params=closing_params
        )
        previews[StageKeys.MORPH.value] = binary_processed
        
        if stage_key == StageKeys.MORPH.value:
            return { ResultKeys.PREVIEWS.value: previews }
            
        # 对于裂缝分析，分阶段预览不执行任何更深的操作
        return { ResultKeys.PREVIEWS.value: previews }

    def _prepare_morph_params(self, morph_params: Dict[str, Any]) -> Tuple[Dict, Dict]:
        """从混合的参数字典中准备开运算和闭运算的参数。"""
        # 深拷贝以避免修改传入的字典
        import copy
        
        # 使用传入字典中的子字典作为基础
        opening_params = copy.deepcopy(morph_params.get('opening', {}))
        closing_params = copy.deepcopy(morph_params.get('closing', {}))

        # 从顶级 'morphology' 字典中获取值并覆盖
        open_ksize = morph_params.get('open_kernel_size')
        if open_ksize:
            opening_params['kernel_size'] = (open_ksize, open_ksize)
        
        open_iter = morph_params.get('open_iterations')
        if open_iter is not None:
            opening_params['iterations'] = open_iter
            
        close_ksize = morph_params.get('close_kernel_size')
        if close_ksize:
            closing_params['kernel_size'] = (close_ksize, close_ksize)
            
        close_iter = morph_params.get('close_iterations')
        if close_iter is not None:
            closing_params['iterations'] = close_iter

        return opening_params, closing_params

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
        
    def _merge_fractures(self, fractures: List[Dict], params: Dict, dpi: float) -> List[Dict]:
        """根据距离和角度合并接近的裂缝。"""
        if not params.get('enabled', False) or len(fractures) < 2:
            return fractures

        merge_dist_mm = params.get('merge_distance_mm', 2.0)
        max_angle_diff = params.get('max_angle_diff', 15.0)
        
        # 将合并距离从毫米转换为像素 (静态调用)
        if dpi <= 0: # 如果没有有效的DPI，则不进行合并
            print("[WARNING FractureAnalyzer] No valid DPI found, skipping merge.")
            return fractures
        merge_dist_pixels = UnitConverter.mm_to_pixels(merge_dist_mm, dpi)

        merged_fractures = []
        fractures_to_merge = fractures.copy()
        
        while fractures_to_merge:
            base_fracture = fractures_to_merge.pop(0)
            base_endpoints = ops.get_contour_endpoints(base_fracture['contour'])
            
            merged = False
            for i in range(len(merged_fractures)):
                target_fracture = merged_fractures[i]
                target_endpoints = ops.get_contour_endpoints(target_fracture['contour'])
                
                # 检查角度差异
                angle_diff = abs(base_fracture['angle'] - target_fracture['angle'])
                # 角度差异需要考虑环绕（例如 179度 和 -179度 很接近）
                angle_diff = min(angle_diff, 180 - angle_diff)

                if angle_diff > max_angle_diff:
                    continue

                # 检查端点距离
                min_dist = float('inf')
                for p1 in base_endpoints:
                    for p2 in target_endpoints:
                        dist = np.linalg.norm(np.array(p1) - np.array(p2))
                        if dist < min_dist:
                            min_dist = dist
                
                if min_dist < merge_dist_pixels:
                    # 合并轮廓
                    new_contour = ops.merge_contours(base_fracture['contour'], target_fracture['contour'])
                    
                    # 重新计算属性
                    new_area = cv2.contourArea(new_contour)
                    new_rect = cv2.minAreaRect(new_contour)
                    (w, h) = new_rect[1]
                    new_aspect_ratio = max(w, h) / min(w, h) if min(w,h) > 0 else 0
                    
                    # 重新计算骨架长度
                    mask = np.zeros_like(base_fracture['contour'], shape=(1024,1024)) # 假设一个最大尺寸
                    cv2.drawContours(mask, [new_contour], -1, 255, -1)
                    skeleton = skeletonize(mask / 255)
                    new_length = np.sum(skeleton)
                    
                    merged_fractures[i] = {
                        'contour': new_contour,
                        'area_pixels': new_area,
                        'length_pixels': new_length,
                        'aspect_ratio': new_aspect_ratio,
                        'angle': new_rect[2]
                    }
                    merged = True
                    break # 跳出内层循环，继续处理下一个待合并的裂缝

            if not merged:
                merged_fractures.append(base_fracture)

        return merged_fractures

    def _draw_analysis_results(self, original_image: np.ndarray, fractures: List[Dict]) -> np.ndarray:
        """将分析结果绘制在原始图像上。"""
        print("[DEBUG Analyzer] Drawing analysis results...")
        if not fractures:
            print("[DEBUG Analyzer] No fractures to draw.")
            return original_image
            
        result_image = original_image.copy()
        print(f"[DEBUG Analyzer] Drawing {len(fractures)} contours with BGR color: (0, 0, 255)")
        for fracture in fractures:
            cv2.drawContours(result_image, [fracture['contour']], -1, (0, 0, 255), 2)
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
            converted_measurements['total_area_mm2'] = UnitConverter.convert_area(
                measurements['total_area_pixels'], dpi
            )
        if 'total_length_pixels' in measurements:
            converted_measurements['total_length_mm'] = UnitConverter.convert_distance(
                measurements['total_length_pixels'], dpi
            )

        if 'details' in measurements:
            converted_details = []
            for detail in measurements['details']:
                new_detail = detail.copy()
                if 'area_pixels' in new_detail:
                    new_detail['area_mm2'] = UnitConverter.convert_area(
                        new_detail['area_pixels'], dpi
                    )
                if 'length_pixels' in new_detail:
                    new_detail['length_mm'] = UnitConverter.convert_distance(
                        new_detail['length_pixels'], dpi
                    )
                converted_details.append(new_detail)
            converted_measurements['details'] = converted_details
            
        final_results = results.copy()
        final_results[ResultKeys.MEASUREMENTS.value] = converted_measurements
        return final_results 