"""控制器模块，连接UI和业务逻辑。

该模块负责协调UI层和核心处理层之间的交互。
它接收用户操作，调用相应的业务逻辑，并更新UI。

"""

from .image_processor import ImageProcessor
from .unit_converter import UnitConverter
from .analysis_stages import AnalysisStage

class Controller:
    """应用程序控制器类，协调UI和业务逻辑。"""
    
    def __init__(self):
        """初始化控制器。"""
        self.image_processor = ImageProcessor()
        self.unit_converter = UnitConverter()
        self.current_image = None
        self.current_dpi = None
        self.current_image_path = None
        self.threshold_method = 'global'
        self.threshold_value = 128
        self.adaptive_params = {'block_size': 11, 'c': 2}
        
        # 添加分析结果存储
        self.analysis_results = {}  # 存储各个处理阶段的结果
        self.current_analysis_stage = None  # 当前分析阶段
    
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
            
            # 清空之前的分析结果
            self.clear_analysis_results()
            
            # 保存原始图像作为第一个分析阶段
            self.save_analysis_result(AnalysisStage.ORIGINAL, {
                'image': image,
                'params': {},
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
    
    def save_analysis_result(self, stage, result_data):
        """保存分析阶段的结果。
        
        Args:
            stage (AnalysisStage): 分析阶段
            result_data (dict): 包含结果数据和元数据的字典
        """
        self.analysis_results[stage] = result_data
        self.current_analysis_stage = stage

    def get_analysis_result(self, stage):
        """获取指定分析阶段的结果。
        
        Args:
            stage (AnalysisStage): 要获取的分析阶段
            
        Returns:
            dict: 该阶段的结果数据,如果不存在则返回None
        """
        return self.analysis_results.get(stage)

    def clear_analysis_results(self):
        """清除所有分析结果。"""
        self.analysis_results.clear()
        self.current_analysis_stage = None
        
    def start_analysis(self):
        """执行完整的图像分析流程。
        
        Returns:
            tuple: (success, message) 表示操作的成功状态和相关消息
        """
        if self.current_image is None:
            return False, "没有加载图像,无法开始分析"
            
        # 清空之前的分析结果
        self.clear_analysis_results()
        
        # 保存原始图像
        self.save_analysis_result(AnalysisStage.ORIGINAL, {
            'image': self.current_image,
            'params': {},
            'stage_name': AnalysisStage.get_stage_name(AnalysisStage.ORIGINAL)
        })
        
        # 1. 灰度化与去噪
        processed_image = self.image_processor.process_image(self.current_image)
        self.save_analysis_result(AnalysisStage.GRAYSCALE, {
            'image': processed_image,
            'params': {'kernel_size': self.image_processor.DEFAULT_GAUSSIAN_KERNEL},
            'stage_name': AnalysisStage.get_stage_name(AnalysisStage.GRAYSCALE)
        })
        
        # 2. 阈值分割 - 使用当前设置的阈值参数
        threshold_result = self.apply_threshold_segmentation()
        # 结果已在apply_threshold_segmentation中保存
        
        # 注意: 以下步骤尚未实现,未来会添加形态学处理和裂缝检测功能
        
        return True, "分析完成"
        
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