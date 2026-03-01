import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextBrowser, QVBoxLayout


class TemplateSuccessDialog(QDialog):
    """模板生成成功对话框"""

    def __init__(self, parent, generated_files, html_content, folder_path):
        super().__init__(parent)
        self.setWindowTitle("模板生成成功")
        self.resize(600, 500)
        self.folder_path = folder_path

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 顶部成功提示
        header_layout = QHBoxLayout()
        # 这里可以使用简单的文本或者图标
        success_label = QLabel("✅ 模板文件已成功生成！")
        success_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2e7d32; font-family: 'Microsoft YaHei';")
        header_layout.addWidget(success_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 内容展示区
        self.text_browser = QTextBrowser()
        self.text_browser.setHtml(html_content)
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.setStyleSheet(
            """
            QTextBrowser {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                background-color: #ffffff;
                padding: 10px;
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """
        )
        layout.addWidget(self.text_browser)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_folder_btn = QPushButton("打开文件夹")
        open_folder_btn.setCursor(Qt.PointingHandCursor)
        open_folder_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #409eff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QPushButton:pressed {
                background-color: #3a8ee6;
            }
        """
        )
        open_folder_btn.clicked.connect(self.open_folder)

        close_btn = QPushButton("关闭")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                color: #606266;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #e6e8eb;
                color: #409eff;
                border-color: #c6e2ff;
            }
            QPushButton:pressed {
                background-color: #dcdfe6;
            }
        """
        )
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(open_folder_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def open_folder(self):
        try:
            if os.path.exists(self.folder_path):
                os.startfile(self.folder_path)
            else:
                QMessageBox.warning(self, "警告", "文件夹不存在！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件夹: {str(e)}")

