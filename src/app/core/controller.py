"""控制器模块，连接UI和业务逻辑。

该模块负责协调UI层和核心处理层之间的交互。
它接收用户操作，调用相应的业务逻辑，并更新UI。

"""

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
        self.merge_fractures_enabled = False

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
            default_threshold_params = {'method': 'otsu', 'params': {}}
            self.on_threshold_params_changed(default_threshold_params)

            return True, f"成功加载图像: {file_path}, DPI: {dpi}"
        except (FileNotFoundError, ValueError) as e:
            return False, str(e)
        except Exception as e:
            return False, f"加载图像时发生意外错误: {str(e)}"
    
    def on_threshold_params_changed(self, params: dict):
        """响应阈值参数变化的槽函数。"""
        print(f"[Controller] Slot on_threshold_params_changed called with: {params}")
        if self.current_image is None:
            return
            
        try:
            result = self.image_processor.apply_threshold(
                self.current_image, 
                method=params.get('method'), 
                params=params.get('params')
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

    def on_morphology_params_changed(self, params: dict = None):
        """响应形态学参数变化的槽函数。"""
        # 如果没有传入新参数，尝试使用已保存的参数
        print(f"[Controller] Slot on_morphology_params_changed called with: {params}")
        if params:
            self.morphology_params = params # 保存最新参数
        
        morphology_params = getattr(self, 'morphology_params', None)
        if not morphology_params:
            print("[Controller] Morphology params not set yet, initializing with default.")
            # 如果没有已存参数（通常是首次链式调用），则创建默认参数
            self.morphology_params = {
                "opening_strategy": "standard",
                "closing_strategy": "standard",
                "params": {
                    "standard_opening": {'kernel_shape': 'rect', 'kernel_size': (3, 3), 'iterations': 1},
                    "area_based_opening": {},
                    "standard_closing": {'kernel_shape': 'rect', 'kernel_size': (3, 3), 'iterations': 1},
                    "strong_closing": {}
                }
            }
            morphology_params = self.morphology_params

        threshold_result = self.get_analysis_result(AnalysisStage.THRESHOLD)
        if not threshold_result or 'binary' not in threshold_result:
            print("[Controller] Morphology cannot proceed, dependent threshold result is missing.")
            return # 依赖的阈值结果不存在

        try:
            binary_image = threshold_result['binary']
            result = self.image_processor.apply_morphological_postprocessing(
                binary_image,
                opening_strategy=morphology_params.get('opening_strategy'),
                closing_strategy=morphology_params.get('closing_strategy'),
                params=morphology_params.get('params')
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
        
    def run_fracture_analysis(self, min_aspect_ratio: float, min_length: float, merge_params: dict = None):
        """驱动完整的裂缝分析流程。
        
        Args:
            min_aspect_ratio (float): 用于过滤噪声的最小长宽比。
            min_length (float): 过滤裂缝的最小长度（单位：毫米）。
            merge_params (dict): 轮廓合并参数, e.g., {'max_distance': 10, 'max_angle_diff': 15}
        """
        if self.current_dpi is None:
            self.error_occurred.emit("无法分析：缺少DPI信息。")
            return

        morphology_result = self.get_analysis_result(AnalysisStage.MORPHOLOGY)
        if not morphology_result or 'image' not in morphology_result:
            self.error_occurred.emit("无法分析：缺少形态学处理结果。")
            return

        binary_image = morphology_result['image']

        # 将最小长度从毫米转换为像素
        dpi = self.current_dpi[0] if self.current_dpi else 0
        if dpi == 0:
            self.error_occurred.emit("无法进行长度过滤：DPI为0或无效。")
            min_length_pixels = 0
        else:
            min_length_pixels = self.unit_converter.mm_to_pixels(min_length, dpi)

        fractures_pixels = self.image_processor.analyze_fractures(
            binary_image, 
            min_aspect_ratio=min_aspect_ratio,
            min_length_pixels=min_length_pixels
        )
        
        # (可选) 智能合并轮廓
        if self.merge_fractures_enabled and merge_params:
            fractures_pixels = self.image_processor.merge_fractures(
                fractures_pixels,
                max_distance=merge_params.get('max_distance', 10),
                max_angle_diff=merge_params.get('max_angle_diff', 15)
            )
        
        # 单位转换
        if not self.current_dpi or self.current_dpi[0] == 0:
            self.error_occurred.emit("无法计算物理尺寸：DPI为0或无效。")
            return
            
        dpi = self.current_dpi[0]
        measurement_details = []
        for fracture in fractures_pixels:
            area_mm2 = self.unit_converter.convert_area(fracture['area_pixels'], dpi)
            length_mm = self.unit_converter.pixels_to_mm(fracture['length_pixels'], dpi)
            measurement_details.append({
                'area_mm2': round(area_mm2, 4),
                'length_mm': round(length_mm, 4),
                'angle': round(fracture['angle'], 2),
            })

        measurement_summary = {
            'count': len(measurement_details),
            'total_area_mm2': round(sum(item['area_mm2'] for item in measurement_details), 4),
            'total_length_mm': round(sum(item['length_mm'] for item in measurement_details), 4),
            'details': measurement_details
        }
        self.save_analysis_result(AnalysisStage.MEASUREMENT, measurement_summary)

        original_image_data = self.get_analysis_result(AnalysisStage.ORIGINAL)
        visualized_image = self.image_processor.draw_analysis_results(
            original_image_data['image'],
            fractures_pixels
        )
        self.save_analysis_result(AnalysisStage.DETECTION, {
            'image': visualized_image,
            'fracture_count': len(fractures_pixels)
        })

        self.analysis_complete.emit(self.get_all_analysis_results())

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