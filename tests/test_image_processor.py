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
        
        # 测试图片路径
        self.test_images_dir = Path(__file__).parent / "test_pic"
        self.test_image_path = str(self.test_images_dir / "1.png")
        
        # 输出目录
        self.output_dir = Path(__file__).parent / "output"
        os.makedirs(self.output_dir, exist_ok=True)
        
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


if __name__ == "__main__":
    unittest.main() 