#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试图像处理器模块。

该模块包含对ImageProcessor类的单元测试，
特别是测试灰度化和去噪功能。
"""

import unittest
import os
import sys
import cv2
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入被测试的模块
from src.app.core.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):
    """测试ImageProcessor类的功能。"""
    
    def setUp(self):
        """测试前的设置。"""
        self.image_processor = ImageProcessor()
        
        # 创建一个简单的灰度测试图像 (numpy array)
        self.gray_test_image = np.zeros((100, 100), dtype=np.uint8)
        self.gray_test_image[20:40, 20:40] = 150  # 一个灰度方块
        
        # 创建一个简单的二值测试图像 (numpy array)
        self.binary_test_image = np.zeros((100, 100), dtype=np.uint8)
        self.binary_test_image[10:15, 10:15] = 255 # 小的白色噪点区域
        self.binary_test_image[30:60, 30:60] = 255 # 较大的白色对象区域

        # 测试图片路径 (保留给旧测试)
        self.test_images_dir = Path(__file__).parent / "test_pic"
        self.test_image_path = str(self.test_images_dir / "1.png")
        
        # 输出目录
        self.output_dir = Path(__file__).parent / "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def test_analyze_fractures_with_length_filter(self):
        """测试analyze_fractures函数是否能根据长度正确过滤裂缝。"""
        # 1. 准备一个测试图像
        # 创建一个黑底图像
        test_image = np.zeros((200, 200), dtype=np.uint8)
        
        # 在图像上绘制两条白色的"裂缝"，一条长，一条短
        # 短裂缝 (长度约10像素)
        cv2.line(test_image, (20, 20), (20, 30), 255, 2) 
        # 长裂缝 (长度约50像素)
        cv2.line(test_image, (50, 50), (50, 100), 255, 2)
        
        # 由于analyze_fractures需要的是黑色的裂缝，所以反转图像
        binary_image = cv2.bitwise_not(test_image)

        # 2. 调用 analyze_fractures 并设置长度阈值
        # 阈值设置为15像素，应该可以过滤掉短裂缝
        min_len_pixels = 15.0
        fractures = self.image_processor.analyze_fractures(
            binary_image, 
            min_aspect_ratio=1.0, # 设置一个低的长宽比以确保裂缝被检测
            min_length_pixels=min_len_pixels
        )
        
        # 3. 验证结果
        # 应该只检测到一条裂缝
        self.assertEqual(len(fractures), 1, "应该只检测到一条长度大于阈值的裂缝")
        
        # 验证被检测到的裂缝长度确实大于阈值
        self.assertGreater(fractures[0]['length_pixels'], min_len_pixels, "检测到的裂缝长度应大于最小长度阈值")

    def test_convert_to_grayscale(self):
        """测试将彩色图像转换为灰度图的功能。"""
        # 加载测试图片
        image, _ = self.image_processor.load_image(self.test_image_path)
        
        # 转换为灰度图
        gray_image = self.image_processor.convert_to_grayscale(image)
        
        # 验证结果是灰度图
        self.assertEqual(len(gray_image.shape), 2, "灰度图应该只有两个维度")
        
        # 保存灰度图
        output_path = str(self.output_dir / "grayscale_output.png")
        cv2.imwrite(output_path, gray_image)
        print(f"灰度图已保存到: {output_path}")
        
    def test_apply_gaussian_blur(self):
        """测试高斯滤波去噪功能。"""
        # 加载测试图片
        image, _ = self.image_processor.load_image(self.test_image_path)
        
        # 转换为灰度图
        gray_image = self.image_processor.convert_to_grayscale(image)
        
        # 应用高斯滤波
        blurred_image = self.image_processor.apply_gaussian_blur(gray_image)
        
        # 验证结果图像形状与灰度图相同
        self.assertEqual(blurred_image.shape, gray_image.shape, 
                         "滤波后的图像形状应与输入图像相同")
        
        # 保存滤波后的图像
        output_path = str(self.output_dir / "gaussian_blur_output.png")
        cv2.imwrite(output_path, blurred_image)
        print(f"高斯滤波后的图像已保存到: {output_path}")
        
    def test_process_image(self):
        """测试完整的图像处理流程（灰度化和去噪）。"""
        # 加载测试图片
        image, _ = self.image_processor.load_image(self.test_image_path)
        
        # 处理图像
        processed_image = self.image_processor.process_image(image)
        
        # 验证结果
        self.assertEqual(len(processed_image.shape), 2, 
                         "处理后的图像应该是灰度图，只有两个维度")
        
        # 保存处理后的图像
        output_path = str(self.output_dir / "processed_image_output.png")
        cv2.imwrite(output_path, processed_image)
        print(f"处理后的图像已保存到: {output_path}")
        
    def test_apply_threshold_new_methods_callable(self):
        """测试新增的阈值方法(Niblack, Sauvola)是否可调用。"""
        # 准备一个process_image的输出
        processed_image = self.image_processor.process_image(self.gray_test_image)

        # 测试 Niblack
        niblack_params = {'method': 'niblack', 'params': {'window_size': 25, 'k': 0.2}}
        niblack_result = self.image_processor.apply_threshold(processed_image, **niblack_params)
        self.assertIn('binary', niblack_result)
        self.assertEqual(niblack_result['binary'].shape, self.gray_test_image.shape)
        
        # 测试 Sauvola
        sauvola_params = {'method': 'sauvola', 'params': {'window_size': 25, 'k': 0.2, 'r': 128}}
        sauvola_result = self.image_processor.apply_threshold(processed_image, **sauvola_params)
        self.assertIn('binary', sauvola_result)
        self.assertEqual(sauvola_result['binary'].shape, self.gray_test_image.shape)

    def test_apply_morphological_postprocessing_new_strategies_callable(self):
        """测试新的形态学策略(area_based, strong)是否可调用。"""
        # [FIX] 更新参数结构以匹配新的函数签名
        area_params = {
            'opening_strategy': 'area_based',
            'params': {
                'opening': {'min_area': 50, 'kernel_size': 3} # kernel_size > 0 才会触发
            }
        }
        area_result = self.image_processor.apply_morphological_postprocessing(self.binary_test_image, **area_params)
        # [FIX] 更新期望的返回键名 'image' -> 'binary'
        self.assertIn('binary', area_result)
        self.assertEqual(area_result['binary'].shape, self.binary_test_image.shape)

        # [FIX] 更新参数结构和期望的返回键名
        # "strong" 策略已在重构中移除，此处改为测试一个有效的标准闭运算
        strong_params = {
            'closing_strategy': 'standard',
            'params': {
                'closing': {'kernel_size': 7, 'iterations': 3}
            }
        }
        strong_result = self.image_processor.apply_morphological_postprocessing(self.binary_test_image, **strong_params)
        self.assertIn('binary', strong_result)
        self.assertEqual(strong_result['binary'].shape, self.binary_test_image.shape)

    def test_merge_fractures_callable(self):
        """测试merge_fractures存根函数是否可调用。"""
        # 这是一个存根，我们只测试它是否可以被调用并返回一个列表
        result = self.image_processor.merge_fractures([], max_distance=10, max_angle_diff=15)
        self.assertIsInstance(result, list)
        
    def test_all_test_images(self):
        """测试目录中的所有测试图片。"""
        # 获取所有测试图片
        test_images = [f for f in os.listdir(self.test_images_dir) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        for image_name in test_images:
            # 构建完整路径
            image_path = str(self.test_images_dir / image_name)
            
            # 加载图片
            try:
                image, _ = self.image_processor.load_image(image_path)
            except Exception as e:
                print(f"加载图片 {image_name} 时出错: {str(e)}")
                continue
                
            # 处理图像
            processed_image = self.image_processor.process_image(image)
            
            # 保存处理后的图像
            output_name = f"processed_{image_name}"
            output_path = str(self.output_dir / output_name)
            cv2.imwrite(output_path, processed_image)
            print(f"图片 {image_name} 处理后的结果已保存到: {output_path}")

    def test_morphological_operations_logic(self):
        """测试形态学开运算和闭运算的逻辑是否正确。
        
        开运算应该移除小的黑色物体（噪点）。
        闭运算应该填充黑色物体内部的小孔洞。
        """
        # 1. 准备一个专门的测试图像（黑底白字的反转模式）
        # 背景为白色 (255)，前景裂缝为黑色 (0)
        test_image = np.full((30, 30), 255, dtype=np.uint8)
        # 添加一个 2x2 的黑色噪点
        test_image[3:5, 3:5] = 0
        # 添加一个 10x10 的主裂缝
        test_image[10:20, 10:20] = 0
        # 在主裂缝中添加一个 2x2 的白色孔洞
        test_image[14:16, 14:16] = 255

        # 2. 测试开运算（去噪）
        # 开运算的核应该足够大以移除噪点，但又不能大到移除主裂缝
        opening_params = {
            'opening_strategy': 'standard',
            'closing_strategy': 'standard', # 不影响本次测试
            'params': {
                'opening': {'kernel_size': 3, 'iterations': 1},
                'closing': {'kernel_size': 0} # 关闭闭运算
            }
        }
        result_opening = self.image_processor.apply_morphological_postprocessing(test_image.copy(), **opening_params)
        opened_image = result_opening['binary']

        # 验证：噪点应该被移除（变回白色）
        self.assertEqual(opened_image[3, 3], 255, "开运算后，噪点区域应变为白色")
        # 验证：主裂缝应该被保留（保持黑色）
        self.assertEqual(opened_image[11, 11], 0, "开运算后，主裂缝区域应保持黑色")
        # 验证：孔洞应该不受影响
        self.assertEqual(opened_image[15, 15], 255, "开运算不应影响主裂缝内部的孔洞")

        # 3. 测试闭运算（填充孔洞）
        closing_params = {
            'opening_strategy': 'standard', # 不影响本次测试
            'closing_strategy': 'standard',
            'params': {
                'opening': {'kernel_size': 0}, # 关闭开运算
                'closing': {'kernel_size': 3, 'iterations': 1}
            }
        }
        result_closing = self.image_processor.apply_morphological_postprocessing(test_image.copy(), **closing_params)
        closed_image = result_closing['binary']

        # 验证：孔洞应该被填充（变为黑色）
        self.assertEqual(closed_image[15, 15], 0, "闭运算后，孔洞区域应被填充为黑色")
        # 验证：噪点应该不受影响
        self.assertEqual(closed_image[3, 3], 0, "闭运算不应影响外部噪点")


if __name__ == "__main__":
    unittest.main() 