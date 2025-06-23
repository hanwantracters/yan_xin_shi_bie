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
    
    analysis_complete = pyqtSignal(dict)

    def __init__(self):
        """初始化控制器。"""
        super().__init__()
        self.image_processor = ImageProcessor()
        self.unit_converter = UnitConverter()
        self.current_image = None
        self.current_dpi = None
        self.current_image_path = None
        self.threshold_method = 'global'
        self.threshold_value = 128
        self.adaptive_params = {'block_size': 11, 'c': 2}
        self.analysis_results = {}
        self.current_analysis_stage = None
        self.morphology_params = {
            'kernel_shape': 'rect',
            'kernel_size': 5,
            'iterations': 1
        }
    
    def load_image_from_file(self, file_path):
        """从文件加载图像。
        
        Args:
            file_path (str): 图像文件的路径。
            
        Returns:
            tuple: 包含以下元素的元组:
                - success (bool): 是否成功加载图像
                - message (str): 成功或错误信息
                
        """
        try:
            # 使用ImageProcessor加载图像并获取DPI信息
            image, dpi = self.image_processor.load_image(file_path)
            
            # 更新控制器状态
            self.current_image = image
            self.current_dpi = dpi
            self.current_image_path = file_path
            # 重置阈值参数
            self.threshold_method = 'global'
            self.threshold_value = 128
            self.adaptive_params = {'block_size': 11, 'c': 2}
            self.morphology_params = {
                'kernel_shape': 'rect',
                'kernel_size': 5,
                'iterations': 1
            }
            
            # 清除之前的分析结果
            self.clear_analysis_results()
            
            # 保存原始图像结果
            self.save_analysis_result(AnalysisStage.ORIGINAL, {
                'image': image,
                'path': file_path,
                'dpi': dpi
            })
            
            # 生成灰度图并保存
            gray_image = self.image_processor.convert_to_grayscale(image)
            self.save_analysis_result(AnalysisStage.GRAYSCALE, {
                'image': gray_image,
                'method': 'standard'
            })
            
            return True, f"成功加载图像: {file_path}, DPI: {dpi}"
        except FileNotFoundError as e:
            return False, str(e)
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"加载图像时发生错误: {str(e)}"
    
    def get_current_image(self):
        """获取当前加载的图像。
        
        Returns:
            numpy.ndarray: 当前图像数据，如果没有加载图像则返回None。
        """
        return self.current_image
    
    def get_current_dpi(self):
        """获取当前图像的DPI信息。
        
        Returns:
            tuple: 当前图像的DPI信息，如果没有DPI信息则返回None。
        """
        return self.current_dpi
        
    def set_threshold_method(self, method: str):
        """设置阈值方法。"""
        self.threshold_method = method

    def set_threshold_value(self, value: int):
        """设置全局阈值。"""
        self.threshold_value = value

    def set_adaptive_params(self, params: dict):
        """设置自适应阈值参数。"""
        self.adaptive_params = params

    def set_morphology_params(self, params: dict):
        """设置形态学参数。"""
        self.morphology_params.update(params)

    def apply_threshold_segmentation(self):
        """应用阈值分割并保存结果。"""
        if self.current_image is None:
            return None
        
        # 检查是否已有保存的结果
        saved_result = self.get_analysis_result(AnalysisStage.THRESHOLD)
        # 如果已有结果且参数没变,直接返回
        if saved_result:
            method = saved_result.get('method')
            params = saved_result.get('params', {})
            
            if method == self.threshold_method:
                if method == 'global' and params.get('threshold') == self.threshold_value:
                    return saved_result
                elif method == 'adaptive_gaussian' and params == self.adaptive_params:
                    return saved_result
                elif method == 'otsu':
                    return saved_result
            
        # 否则重新计算
        params = {}
        if self.threshold_method == 'global':
            params['threshold'] = self.threshold_value
        elif self.threshold_method == 'adaptive_gaussian':
            params = self.adaptive_params
        
        result = self.image_processor.apply_threshold(
            self.current_image, 
            method=self.threshold_method, 
            params=params
        )
        
        # 保存计算结果
        self.save_analysis_result(AnalysisStage.THRESHOLD, result)
        return result
    
    def apply_morphological_processing(self):
        """应用形态学处理并保存结果。"""
        threshold_result = self.get_analysis_result(AnalysisStage.THRESHOLD)
        if not threshold_result or 'binary' not in threshold_result:
            # 如果没有阈值分割结果，则先执行
            threshold_result = self.apply_threshold_segmentation()
            if not threshold_result:
                return None

        binary_image = threshold_result['binary']
        
        # 获取参数
        params = self.morphology_params
        kernel_size_val = params.get('kernel_size', 5)

        # 应用处理
        result = self.image_processor.apply_morphological_postprocessing(
            binary_image,
            kernel_shape=params.get('kernel_shape', 'rect'),
            kernel_size=(kernel_size_val, kernel_size_val),
            iterations=params.get('iterations', 1)
        )
        
        # 保存结果
        self.save_analysis_result(AnalysisStage.MORPHOLOGY, result)
        return result
    
    def run_fracture_analysis(self, min_aspect_ratio: float):
        """驱动完整的裂缝分析流程。
        
        Args:
            min_aspect_ratio (float): 用于过滤噪声的最小长宽比。
        """
        # 1. 检查DPI和形态学结果是否就绪
        if self.current_dpi is None:
            print("错误：无法进行分析，缺少DPI信息。")
            # 可以在此发射一个错误信号
            return

        morphology_result = self.get_analysis_result(AnalysisStage.MORPHOLOGY)
        if not morphology_result or 'image' not in morphology_result:
            print("错误：无法进行分析，缺少形态学处理结果。")
            # 可以先尝试运行
            morphology_result = self.apply_morphological_processing()
            if not morphology_result:
                print("错误：形态学处理失败。")
                return

        binary_image = morphology_result['image']

        # 2. 调用核心分析算法
        fractures_pixels = self.image_processor.analyze_fractures(
            binary_image, 
            min_aspect_ratio=min_aspect_ratio
        )
        
        # 3. 单位转换
        measurement_details = []
        dpi = self.current_dpi[0]
        for fracture in fractures_pixels:
            area_mm2 = self.unit_converter.convert_area(fracture['area_pixels'], dpi)
            length_mm = self.unit_converter.pixels_to_mm(fracture['length_pixels'], dpi)
            measurement_details.append({
                'area_mm2': round(area_mm2, 4),
                'length_mm': round(length_mm, 4),
                'angle': round(fracture['angle'], 2),
            })

        # 4. 保存详细测量数据
        measurement_summary = {
            'count': len(measurement_details),
            'total_area_mm2': round(sum(item['area_mm2'] for item in measurement_details), 4),
            'total_length_mm': round(sum(item['length_mm'] for item in measurement_details), 4),
            'details': measurement_details
        }
        self.save_analysis_result(AnalysisStage.MEASUREMENT, measurement_summary)

        # 5. 创建并保存可视化结果图像
        original_image_data = self.get_analysis_result(AnalysisStage.ORIGINAL)
        visualized_image = self.image_processor.draw_analysis_results(
            original_image_data['image'],
            fractures_pixels
        )
        self.save_analysis_result(AnalysisStage.DETECTION, {
            'image': visualized_image,
            'fracture_count': len(fractures_pixels)
        })

        # 6. 发射完成信号
        self.analysis_complete.emit(self.get_all_analysis_results())

    def save_analysis_result(self, stage, result_data):
        """保存分析阶段的结果。
        
        Args:
            stage (AnalysisStage): 分析阶段
            result_data (dict): 包含结果数据和元数据的字典
        """
        self.analysis_results[stage] = result_data
        self.current_analysis_stage = stage
        
    def convert_pixels_to_mm(self, pixels):
        """将像素值转换为毫米值。
        
        Args:
            pixels: 要转换的像素值，可以是单个数值或NumPy数组
            
        Returns:
            转换后的毫米值，保持与输入相同的数据类型
            
        Raises:
            ValueError: 如果当前没有有效的DPI信息
        """
        if self.current_dpi is None:
            raise ValueError("没有有效的DPI信息，无法进行单位转换")
        
        # 使用x轴DPI进行转换（通常x和y的DPI是相同的）
        dpi_value = self.current_dpi[0]
        return self.unit_converter.pixels_to_mm(pixels, dpi_value)
        
    def convert_mm_to_pixels(self, mm):
        """将毫米值转换为像素值。
        
        Args:
            mm: 要转换的毫米值，可以是单个数值或NumPy数组
            
        Returns:
            转换后的像素值，保持与输入相同的数据类型
            
        Raises:
            ValueError: 如果当前没有有效的DPI信息
        """
        if self.current_dpi is None:
            raise ValueError("没有有效的DPI信息，无法进行单位转换")
        
        # 使用x轴DPI进行转换（通常x和y的DPI是相同的）
        dpi_value = self.current_dpi[0]
        return self.unit_converter.mm_to_pixels(mm, dpi_value)
        
    def convert_point(self, point):
        """将像素坐标点转换为毫米坐标点。
        
        Args:
            point: 像素坐标点，格式为(x, y)
            
        Returns:
            毫米坐标点，格式为(x_mm, y_mm)
            
        Raises:
            ValueError: 如果当前没有有效的DPI信息
        """
        if self.current_dpi is None:
            raise ValueError("没有有效的DPI信息，无法进行单位转换")
        
        # 使用x轴DPI进行转换（通常x和y的DPI是相同的）
        dpi_value = self.current_dpi[0]
        return self.unit_converter.convert_point(point, dpi_value)
        
    def convert_distance(self, pixel_distance):
        """将像素距离转换为毫米距离。
        
        Args:
            pixel_distance: 像素单位的距离
            
        Returns:
            毫米单位的距离
            
        Raises:
            ValueError: 如果当前没有有效的DPI信息
        """
        if self.current_dpi is None:
            raise ValueError("没有有效的DPI信息，无法进行单位转换")
        
        # 使用x轴DPI进行转换（通常x和y的DPI是相同的）
        dpi_value = self.current_dpi[0]
        return self.unit_converter.convert_distance(pixel_distance, dpi_value)
        
    def convert_area(self, pixel_area):
        """将像素面积转换为平方毫米面积。
        
        Args:
            pixel_area: 像素单位的面积
            
        Returns:
            平方毫米单位的面积
            
        Raises:
            ValueError: 如果当前没有有效的DPI信息
        """
        if self.current_dpi is None:
            raise ValueError("没有有效的DPI信息，无法进行单位转换")
        
        # 使用x轴DPI进行转换（通常x和y的DPI是相同的）
        dpi_value = self.current_dpi[0]
        return self.unit_converter.convert_area(pixel_area, dpi_value)
    
    def get_analysis_result(self, stage):
        """获取特定阶段的分析结果。
        
        Args:
            stage (AnalysisStage): 分析阶段
            
        Returns:
            dict: 该阶段的分析结果字典，如果没有结果则返回None
        """
        return self.analysis_results.get(stage)
    
    def get_all_analysis_results(self):
        """获取所有分析阶段的结果。
        
        Returns:
            dict: 包含所有分析阶段结果的字典
        """
        return self.analysis_results
        
    def clear_analysis_results(self):
        """清除所有分析结果。"""
        self.analysis_results.clear()
        self.current_analysis_stage = None 