from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, 
    QDialogButtonBox, QLabel
)

class AnalysisWizard(QDialog):
    """分析向导对话框，用于设置裂缝分析的参数。"""
    
    def __init__(self, parent=None):
        """初始化分析向导。"""
        super().__init__(parent)
        
        self.setWindowTitle("裂缝分析参数设置")
        self.setMinimumWidth(350)
        
        # --- 布局和控件 ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 描述标签
        description_label = QLabel(
            "请为裂缝分析设置以下参数。\n"
            "这些参数将用于从图像中过滤和识别有效的裂缝。"
        )
        description_label.setWordWrap(True)
        
        # 最小长宽比输入
        self.aspect_ratio_spinbox = QDoubleSpinBox()
        self.aspect_ratio_spinbox.setRange(1.0, 1000.0)
        self.aspect_ratio_spinbox.setValue(5.0)  # 默认值
        self.aspect_ratio_spinbox.setSuffix(" : 1")
        
        # 最小裂缝长度输入
        self.min_length_spinbox = QDoubleSpinBox()
        self.min_length_spinbox.setRange(0.0, 10000.0)
        self.min_length_spinbox.setValue(1.0) # 默认值
        self.min_length_spinbox.setSuffix(" mm")
        
        form_layout.addRow("最小长宽比 (Min Aspect Ratio):", self.aspect_ratio_spinbox)
        form_layout.addRow("最小裂缝长度 (Min Length):", self.min_length_spinbox)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # --- 组装布局 ---
        layout.addWidget(description_label)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_parameters(self) -> dict:
        """获取用户设置的参数。"""
        return {
            'min_aspect_ratio': self.aspect_ratio_spinbox.value(),
            'min_length': self.min_length_spinbox.value()
        }

if __name__ == '__main__':
    # 用于独立测试
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    wizard = AnalysisWizard()
    if wizard.exec_() == QDialog.Accepted:
        print("分析参数:", wizard.get_parameters())
    else:
        print("分析已取消。") 