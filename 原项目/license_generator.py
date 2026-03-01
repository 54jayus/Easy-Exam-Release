import hashlib
import datetime
import base64
import sys
from typing import Tuple

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QSpinBox,
    QMessageBox
)
from PyQt5.QtCore import Qt

class LicenseGenerator:
    """注册码生成器"""
    
    def __init__(self, app_secret: str = "54lanyue"):
        """
        初始化注册码生成器
        
        Args:
            app_secret (str): 应用程序密钥
        """
        self.app_secret = app_secret

    def generate_reg_code(self, machine_code: str, days: int, salt: str) -> Tuple[str, datetime.datetime]:
        """
        生成带时间限制的注册码
        
        Args:
            machine_code (str): 机器码
            days (int): 有效天数
            salt (str): 盐值
            
        Returns:
            Tuple[str, datetime.datetime]: 注册码和过期时间
        """
        current_time = datetime.datetime.now()
        expire_date = current_time + datetime.timedelta(days=days)
        expire_timestamp = int(expire_date.timestamp())
        
        # 组合关键信息并生成SHA256哈希值
        combined = f"{machine_code}|{expire_timestamp}|{self.app_secret}|{salt}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        hash_b64 = base64.urlsafe_b64encode(hash_bytes).decode().rstrip('=')
        
        # 注册码格式：时间戳-Base64哈希
        reg_code = f"{expire_timestamp}-{hash_b64}"
        
        return reg_code, expire_date


class LicenseGeneratorUI(QMainWindow):
    """注册码生成器界面"""
    
    def __init__(self):
        """初始化注册码生成器界面"""
        super().__init__()
        self.generator = LicenseGenerator()
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("注册码生成器")
        self.setGeometry(700, 400, 600, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 机器码输入区域
        machine_group = QGroupBox("机器码输入")
        machine_layout = QVBoxLayout()
        self.machine_code_input = QLineEdit()
        self.machine_code_input.setPlaceholderText("请输入16位机器码")
        machine_layout.addWidget(self.machine_code_input)
        machine_group.setLayout(machine_layout)
        main_layout.addWidget(machine_group)
        
        # 参数设置区域
        param_group = QGroupBox("参数设置")
        param_layout = QVBoxLayout()
        
        # 有效期设置
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("有效期(天):"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(-100, 3650)  # 1天到10年
        self.days_spin.setValue(30)  # 默认1年
        days_layout.addWidget(self.days_spin)
        days_layout.addStretch()
        param_layout.addLayout(days_layout)
        
        # 盐值设置
        salt_layout = QHBoxLayout()
        salt_layout.addWidget(QLabel("盐值:"))
        self.salt_input = QLineEdit()
        self.salt_input.setText("paijiankao2025")  # 默认盐值
        salt_layout.addWidget(self.salt_input)
        salt_layout.addStretch()
        param_layout.addLayout(salt_layout)
        
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)
        
        # 生成按钮
        generate_btn = QPushButton("生成注册码")
        generate_btn.clicked.connect(self.generate_license)
        main_layout.addWidget(generate_btn)
        
        # 结果显示区域
        result_group = QGroupBox("生成结果")
        result_layout = QVBoxLayout()
        self.result_text = QLineEdit()
        self.result_text.setReadOnly(True)
        # 设置结果文本框可选择和复制
        self.result_text.setFocusPolicy(Qt.StrongFocus)
        self.result_text.setEchoMode(QLineEdit.Normal)
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        # 过期时间显示
        expire_group = QGroupBox("过期时间")
        expire_layout = QVBoxLayout()
        self.expire_label = QLabel("未生成注册码")
        expire_layout.addWidget(self.expire_label)
        expire_group.setLayout(expire_layout)
        main_layout.addWidget(expire_group)
    
    def generate_license(self):
        """生成注册码"""
        # 获取输入参数
        machine_code = self.machine_code_input.text().strip().upper()
        days = self.days_spin.value()
        salt = self.salt_input.text()
        
        # 验证机器码
        if not machine_code:
            QMessageBox.warning(self, "输入错误", "请输入机器码")
            return
            
        if len(machine_code) != 16:
            QMessageBox.warning(self, "输入错误", "机器码应为16位字符")
            return
        
        try:
            # 生成注册码
            reg_code, expire_date = self.generator.generate_reg_code(machine_code, days, salt)
            
            # 显示结果
            self.result_text.setText(reg_code)
            self.expire_label.setText(f"过期时间: {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 提示成功
            QMessageBox.information(self, "生成成功", "注册码已生成")
        except Exception as e:
            QMessageBox.critical(self, "生成失败", f"生成注册码时出错:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LicenseGeneratorUI()
    window.show()
    sys.exit(app.exec_())