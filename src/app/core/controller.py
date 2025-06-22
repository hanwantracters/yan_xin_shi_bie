"""控制器模块，连接UI和业务逻辑。

该模块负责协调UI层和核心处理层之间的交互。
它接收用户操作，调用相应的业务逻辑，并更新UI。

"""

from .image_processor import ImageProcessor
from .unit_converter import UnitConverter

class Controller:
    """应用程序控制器类，协调UI和业务逻辑。"""
    
    def __init__(self):
        """初始化控制器。"""
        self.image_processor = ImageProcessor()
        self.unit_converter = UnitConverter()
        self.current_image = None
        self.current_dpi = None
        self.current_image_path = None
    
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