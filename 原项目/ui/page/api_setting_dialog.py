import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QFormLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon

from ..ai.zhipu_client import ZhipuChatClient, ZhipuApiError

class ApiTestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def run(self):
        try:
            client = ZhipuChatClient(api_key=self.api_key)
            # 发送一个简单的测试请求
            payload = {
                "model": "glm-4-flash", # 使用轻量级模型测试
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            client.create_chat_completion(payload)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

class ApiSettingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 设置")
        self.setFixedSize(400, 300)
        self.init_ui()
        self.worker = None

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("配置 AI 助手")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 表单区域
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 厂商
        vendor_label = QLabel("智谱清言")
        vendor_label.setStyleSheet("color: #666;")
        form_layout.addRow("厂商：", vendor_label)

        # 模型
        model_label = QLabel("GLM-4.6V-Flash")
        model_label.setStyleSheet("color: #666;")
        form_layout.addRow("模型：", model_label)

        # API KEY
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 API KEY")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API KEY：", self.api_key_input)

        layout.addLayout(form_layout)

        # 获取网址
        link_label = QLabel('<a href="https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys">获取 API KEY (智谱开放平台)</a>')
        link_label.setOpenExternalLinks(True)
        link_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(link_label)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("验证并保存")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
            }
        """)
        self.save_btn.clicked.connect(self.verify_and_save)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def verify_and_save(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请输入 API KEY")
            return

        self.save_btn.setEnabled(False)
        self.save_btn.setText("正在验证...")
        
        self.worker = ApiTestWorker(api_key)
        self.worker.finished.connect(self.on_verify_finished)
        self.worker.start()

    def on_verify_finished(self, success, error_msg):
        self.save_btn.setEnabled(True)
        self.save_btn.setText("验证并保存")

        if success:
            if self.save_api_key(self.api_key_input.text().strip()):
                QMessageBox.information(self, "成功", "验证通过，设置已保存")
                self.accept()
            else:
                QMessageBox.critical(self, "错误", "保存配置文件失败")
        else:
            QMessageBox.critical(self, "验证失败", f"无法连接到 API，原因：\n{error_msg}")

    def save_api_key(self, api_key):
        try:
            # 假设 license.cert 在当前工作目录或与可执行文件同级
            cert_path = "license.cert"
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.getcwd()
            
            full_path = os.path.join(base_path, cert_path)
            
            # 读取现有内容
            lines = []
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            # 确保第一行存在（保留许可证）
            if not lines:
                return False # 文件不存在或为空，无法写入附加信息（因为这应该是一个已授权的软件）
            
            # 准备新内容
            new_lines = [lines[0].rstrip() + "\n"] # 保留第一行并确保只有一个换行
            new_lines.append(f"API_KEY:{api_key}\n")
            
            # 写入文件
            with open(full_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            print(f"Save API Key Error: {e}")
            return False
