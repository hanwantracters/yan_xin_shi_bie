#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
岩石裂缝分析系统的主入口点。

该模块创建并启动应用程序的主窗口。
"""

import sys
from PyQt5.QtWidgets import QApplication
from src.app.ui.main_window import MainWindow


def main():
    """应用程序主函数。"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建主窗口实例
    window = MainWindow()
    
    # 显示主窗口
    window.show()
    
    # 进入应用程序主循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 