"""控制器模块，连接UI和业务逻辑。

该模块负责协调UI层和核心处理层之间的交互。
它接收用户操作，调用相应的业务逻辑，并更新UI。

"""

import json
from PyQt5.QtCore import QObject, pyqtSignal

from .image_processor import ImageProcessor
from .unit_converter import UnitConverter
from .analysis_stages import AnalysisStage

class Controller(QObject):
    """应用程序控制器类，协调UI和业务逻辑。"""
    
    # 信号
    analysis_complete = pyqtSignal(dict)
    preview_stage_updated = pyqtSignal(AnalysisStage, dict)
    error_occurred = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)

    def __init__(self):
        """初始化控制器。"""
        super().__init__()
        self.image_processor = ImageProcessor()
        self.unit_converter = UnitConverter()
        
        # 状态变量
        self.current_image = None
        self.current_dpi = None
        self.current_image_path = None
        self.analysis_results = {}
        self.analysis_params = {}
        
        self._load_default_parameters()

    def _load_default_parameters(self):
        """加载默认分析参数。"""
        try:
            with open('config/default_params.json', 'r', encoding='utf-8') as f:
                self.analysis_params = json.load(f)
            print("成功加载默认参数。")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.error_occurred.emit(f"无法加载默认参数文件: {e}")
            # 在没有默认文件时提供一组基本参数
            self.analysis_params = {
                "version": "1.0",
                "analysis_parameters": {
                    "threshold": {
                        "method": "adaptive_gaussian",
                        "global_value": 127,
                        "adaptive_block_size": 11,
                        "adaptive_c_value": 2,
                        "niblack_window_size": 25,
                        "niblack_k": -0.2,
                        "sauvola_window_size": 25,
                        "sauvola_k": 0.2,
                        "sauvola_r": 128
                    },
                    "morphology": {
                        "open_kernel_size": 3,
                        "open_iterations": 1,
                        "close_kernel_size": 3,
                        "close_iterations": 1
                    },
                    "filtering": {
                        "min_length_mm": 5.0,
                        "min_aspect_ratio": 3.0
                    },
                    "merging": {
                        "enabled": False,
                        "merge_distance_mm": 2.0
                    }
                }
            }

    def load_parameters(self, filepath: str):
        """从文件加载分析参数。"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.analysis_params = json.load(f)
            print(f"成功从 {filepath} 加载参数。")
            self.parameters_updated.emit(self.analysis_params)
            # 参数加载后，触发一次完整的预览更新
            self.on_threshold_params_changed()
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
            
    def update_parameter(self, param_path: str, value):
        """更新一个分析参数，并触发相应的预览更新。
        
        Args:
            param_path (str): 参数的路径, e.g., "threshold.method"
            value: 新的参数值
        """
        keys = param_path.split('.')
        d = self.analysis_params['analysis_parameters']
        for key in keys[:-1]:
            d = d[key]
        d[keys[-1]] = value
        
        print(f"参数已更新: {param_path} = {value}")

        # 根据被修改的参数决定更新哪个预览
        if keys[0] == 'threshold':
            self.on_threshold_params_changed()
        elif keys[0] == 'morphology':
            self.on_morphology_params_changed()

    def load_image_from_file(self, file_path: str) -> tuple:
        """从文件加载图像。
        
        Args:
            file_path (str): 图像文件的路径。
            
        Returns:
            tuple: 包含是否成功和消息的元组。
        """
        try:
            image, dpi = self.image_processor.load_image(file_path)
            
            self.current_image = image
            self.current_dpi = dpi
            self.current_image_path = file_path
            self.clear_analysis_results()
            
            self.save_analysis_result(AnalysisStage.ORIGINAL, {
                'image': image, 'path': file_path, 'dpi': dpi
            })
            
            gray_image = self.image_processor.convert_to_grayscale(image)
            self.save_analysis_result(AnalysisStage.GRAYSCALE, {
                'image': gray_image, 'method': 'standard'
            })
            
            # 通知UI更新原始图像和灰度图
            print(f"[Controller] Emitting preview_stage_updated for ORIGINAL and GRAYSCALE.")
            self.preview_stage_updated.emit(AnalysisStage.ORIGINAL, self.get_analysis_result(AnalysisStage.ORIGINAL))
            self.preview_stage_updated.emit(AnalysisStage.GRAYSCALE, self.get_analysis_result(AnalysisStage.GRAYSCALE))
            
            # 触发一次默认的阈值和形态学处理，以填充预览窗口
            print("[Controller] Triggering initial threshold and morphology processing.")
            self.on_threshold_params_changed()

            return True, f"成功加载图像: {file_path}, DPI: {dpi}"
        except (FileNotFoundError, ValueError) as e:
            return False, str(e)
        except Exception as e:
            return False, f"加载图像时发生意外错误: {str(e)}"
    
    def on_threshold_params_changed(self):
        """根据当前的参数状态，重新应用阈值处理。"""
        print(f"[Controller] Slot on_threshold_params_changed called.")
        if self.current_image is None:
            return

        try:
            params = self.analysis_params['analysis_parameters']['threshold']
            method = params['method']
            
            threshold_params = {}
            if method == 'global':
                threshold_params = {'value': params['global_value']}
            elif method == 'adaptive_gaussian':
                threshold_params = {'block_size': params['adaptive_block_size'], 'c': params['adaptive_c_value']}
            elif method == 'niblack':
                threshold_params = {'window_size': params['niblack_window_size'], 'k': params['niblack_k']}
            elif method == 'sauvola':
                threshold_params = {
                    'window_size': params['sauvola_window_size'], 
                    'k': params['sauvola_k'], 
                    'r': params['sauvola_r']
                }

            result = self.image_processor.apply_threshold(
                self.current_image, 
                method=method,
                params=threshold_params
            )
            self.save_analysis_result(AnalysisStage.THRESHOLD, result)
            self.preview_stage_updated.emit(AnalysisStage.THRESHOLD, result)

            # 阈值变化后，形态学结果也需要更新
            print("[Controller] Triggering chained update to morphology.")
            self.on_morphology_params_changed()
            print("[Controller] Chained update to morphology finished.")

        except Exception as e:
            error_msg = f"阈值处理失败: {e}"
            self.error_occurred.emit(error_msg)
            print(error_msg)

    def _get_formatted_morphology_params(self) -> dict:
        """从主参数字典中读取形态学参数并将其格式化为处理函数所需的结构。"""
        morph_p = self.analysis_params['analysis_parameters'].get('morphology', {})
        
        # 这个结构必须与 image_processor.apply_morphological_postprocessing 的期望相符
        return {
            'opening': {
                'kernel_size': morph_p.get('open_kernel_size', 0),
                'kernel_shape': morph_p.get('open_kernel_shape', 'rect'),
                'iterations': morph_p.get('open_iterations', 1),
                'min_area': morph_p.get('min_area', 100)
            },
            'closing': {
                'kernel_size': morph_p.get('close_kernel_size', 0),
                'kernel_shape': morph_p.get('close_kernel_shape', 'rect'),
                'iterations': morph_p.get('close_iterations', 1)
            }
        }

    def on_morphology_params_changed(self):
        """根据当前的参数状态，重新应用形态学处理。"""
        print(f"[Controller] Slot on_morphology_params_changed called.")
        
        threshold_result = self.get_analysis_result(AnalysisStage.THRESHOLD)
        if not threshold_result or 'binary' not in threshold_result:
            print("[Controller] Morphology cannot proceed, dependent threshold result is missing.")
            return # 依赖的阈值结果不存在

        try:
            # [REFACTOR] 使用统一的参数格式化方法
            processing_params = self._get_formatted_morphology_params()
            binary_image = threshold_result['binary']
            
            result = self.image_processor.apply_morphological_postprocessing(
                binary_image,
                # opening_strategy 和 closing_strategy 理论上也可以来自参数
                opening_strategy="standard", 
                closing_strategy="standard",
                params=processing_params
            )
            self.save_analysis_result(AnalysisStage.MORPHOLOGY, result)
            self.preview_stage_updated.emit(AnalysisStage.MORPHOLOGY, result)
        except Exception as e:
            error_msg = f"形态学处理失败: {e}"
            self.error_occurred.emit(error_msg)
            print(error_msg)

    def on_merge_fractures_toggled(self, enabled: bool):
        """设置是否启用轮廓合并。"""
        self.merge_fractures_enabled = enabled
        print(f"轮廓合并设置为: {'启用' if enabled else '禁用'}")

    def get_current_image(self):
        """获取当前加载的图像。"""
        return self.current_image
    
    def get_current_dpi(self):
        """获取当前图像的DPI信息。"""
        return self.current_dpi
        
    def run_fracture_analysis(self):
        """
        [REFACTORED] 执行一个完整的、自包含的裂缝分析流水线。
        
        该方法从头开始执行所有处理步骤，不依赖于任何预先存在的预览结果。
        它将按顺序执行阈值分割、形态学处理、裂缝分析、合并和最终计算，
        并在每个关键阶段保存结果并更新UI预览。
        """
        if self.current_image is None:
            self.error_occurred.emit("没有加载图像，无法开始分析。")
            return

        try:
            # --- 前置检查: 确保DPI信息可用 ---
            if not self.current_dpi or self.current_dpi[0] <= 0:
                raise ValueError("无法进行单位换算：DPI信息无效或为0。")
            dpi = self.current_dpi[0]  # 假设x和y的DPI相同

            # --- 步骤 1: 阈值分割 ---
            print("[Pipeline] Running Step 1: Thresholding")
            thresh_params_flat = self.analysis_params['analysis_parameters']['threshold']
            method = thresh_params_flat['method']
            
            thresh_params_structured = {}
            if method == 'global':
                thresh_params_structured = {'value': thresh_params_flat['global_value']}
            elif method == 'adaptive_gaussian':
                thresh_params_structured = {'block_size': thresh_params_flat['adaptive_block_size'], 'c': thresh_params_flat['adaptive_c_value']}
            elif method == 'niblack':
                thresh_params_structured = {'window_size': thresh_params_flat['niblack_window_size'], 'k': thresh_params_flat['niblack_k']}
            elif method == 'sauvola':
                thresh_params_structured = {
                    'window_size': thresh_params_flat['sauvola_window_size'], 
                    'k': thresh_params_flat['sauvola_k'], 
                    'r': thresh_params_flat['sauvola_r']
                }

            threshold_result = self.image_processor.apply_threshold(
                self.current_image, method=method, params=thresh_params_structured
            )
            self.save_analysis_result(AnalysisStage.THRESHOLD, threshold_result)
            self.preview_stage_updated.emit(AnalysisStage.THRESHOLD, threshold_result)
            
            # --- 步骤 2: 形态学处理 ---
            print("[Pipeline] Running Step 2: Morphological Post-processing")
            binary_image = threshold_result['binary']
            morphology_params = self._get_formatted_morphology_params()
            
            morphology_result = self.image_processor.apply_morphological_postprocessing(
                binary_image,
                opening_strategy="standard",
                closing_strategy="standard",
                params=morphology_params
            )
            self.save_analysis_result(AnalysisStage.MORPHOLOGY, morphology_result)
            self.preview_stage_updated.emit(AnalysisStage.MORPHOLOGY, morphology_result)
            
            processed_binary_image = morphology_result['binary']

            # --- 步骤 3: 裂缝过滤与分析 ---
            print("[Pipeline] Running Step 3: Fracture Analysis")
            filtering_params = self.analysis_params['analysis_parameters'].get('filtering', {})
            min_length_pixels = self.unit_converter.mm_to_pixels(
                filtering_params.get('min_length_mm', 0), dpi
            )

            valid_fractures = self.image_processor.analyze_fractures(
                processed_binary_image,
                min_aspect_ratio=filtering_params.get('min_aspect_ratio', 3.0),
                min_length_pixels=min_length_pixels
            )

            # --- 步骤 4: (可选) 轮廓合并 ---
            merging_params = self.analysis_params['analysis_parameters'].get('merging', {})
            if merging_params.get('enabled', False):
                print("[Pipeline] Running Step 4: Merging Fractures")
                merge_distance_pixels = self.unit_converter.mm_to_pixels(
                    merging_params.get('merge_distance_mm', 0), dpi
                )
                valid_fractures = self.image_processor.merge_fractures(
                    valid_fractures,
                    max_distance=merge_distance_pixels,
                    max_angle_diff=15.0  # 暂时硬编码
                )

            # --- 步骤 5: 结果可视化 ---
            print("[Pipeline] Running Step 5: Visualizing Results")
            detection_image = self.image_processor.draw_analysis_results(self.current_image, valid_fractures)
            detection_result = {'image': detection_image, 'fractures': valid_fractures}
            self.save_analysis_result(AnalysisStage.DETECTION, detection_result)
            self.preview_stage_updated.emit(AnalysisStage.DETECTION, detection_result)

            # --- 步骤 6: 定量计算 ---
            print("[Pipeline] Running Step 6: Quantitative Measurement")
            total_area_pixels = sum(f['area_pixels'] for f in valid_fractures)
            total_length_pixels = sum(f['length_pixels'] for f in valid_fractures)
            
            measurement_result = {
                'fracture_count': len(valid_fractures),
                'total_area_mm2': self.unit_converter.convert_area(total_area_pixels, dpi),
                'total_length_mm': self.unit_converter.pixels_to_mm(total_length_pixels, dpi),
                'detailed_fractures': [
                    {
                        'id': i + 1,
                        'length_mm': self.unit_converter.pixels_to_mm(f['length_pixels'], dpi),
                        'area_mm2': self.unit_converter.convert_area(f['area_pixels'], dpi),
                        'angle_degrees': f['angle']
                    }
                    for i, f in enumerate(valid_fractures)
                ]
            }
            
            # DEBUG: 打印测量结果的内容
            print("[DEBUG] Measurement result:")
            print(f"  - fracture_count: {measurement_result['fracture_count']}")
            print(f"  - total_area_mm2: {measurement_result['total_area_mm2']}")
            print(f"  - total_length_mm: {measurement_result['total_length_mm']}")
            print(f"  - valid_fractures count: {len(valid_fractures)}")
            
            # 新增DEBUG: 确认即将发送的数据
            print(f"[DEBUG][Controller] Emitting 'analysis_complete' with keys: {list(measurement_result.keys())}")
            
            self.save_analysis_result(AnalysisStage.MEASUREMENT, measurement_result)
            self.analysis_complete.emit(measurement_result)
            print("[Pipeline] Analysis finished successfully.")

        except Exception as e:
            error_msg = f"分析流程执行失败: {e}"
            self.error_occurred.emit(error_msg)
            print(error_msg)

    def save_analysis_result(self, stage, result_data):
        """保存指定分析阶段的结果。"""
        self.analysis_results[stage] = result_data
    
    def get_analysis_result(self, stage):
        """获取指定分析阶段的结果。"""
        return self.analysis_results.get(stage)

    def get_all_analysis_results(self):
        """获取所有分析阶段的结果。"""
        return self.analysis_results

    def clear_analysis_results(self):
        """清除所有分析结果。"""
        self.analysis_results = {}
        self.merge_fractures_enabled = False 