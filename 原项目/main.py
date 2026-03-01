#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能考务系统主程序入口
"""

import sys
import random
import time
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QCursor

# 导入UI组件
from ui.main_window import MainWindow   
from client_license import NetworkTimeLicenseManager, LicenseManagerUI

class AppController(QObject):
    """应用程序控制器，协调许可证验证与主窗口显示"""
    
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.window = None
        self.license_window = None
        self.license_manager = NetworkTimeLicenseManager()
        
    def run(self):
        """运行应用程序"""
        # 设置随机种子
        random.seed(time.time())

        # 检查许可证
        if os.path.exists(self.license_manager.cert_file):
            cert_valid, _, err_msg = self.license_manager._verify_cert_file()
            if cert_valid:
                self.show_main_window()
                return sys.exit(self.app.exec_())
        
        # 显示许可证验证界面
        self.show_license_window()
        return sys.exit(self.app.exec_())
    
    def show_main_window(self):
        """显示主窗口"""
        try:
            self.window = MainWindow()
            self._center_widget(self.window, pre_show=True)
            self.window.show()
        except Exception as e:
            QMessageBox.critical(None, "启动失败", f"无法启动主程序: {str(e)}")
            sys.exit(1)
    
    def show_license_window(self):
        """显示许可证验证窗口"""
        try:
            self.license_window = LicenseManagerUI()
            self.license_window.license_verified.connect(self.on_license_verified)
            self._center_widget(self.license_window, pre_show=True)
            self.license_window.show()
        except Exception as e:
            QMessageBox.critical(None, "启动失败", f"许可证界面加载失败: {str(e)}")
            sys.exit(1)

    def _center_widget(self, widget, pre_show=False):
        try:
            if widget is None or widget.isMaximized() or widget.isFullScreen():
                return
            screen = None
            if hasattr(self.app, "screenAt"):
                screen = self.app.screenAt(QCursor.pos())
            if screen is None:
                screen = self.app.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            if pre_show:
                size = widget.size()
                if size.width() <= 1 or size.height() <= 1:
                    size = widget.sizeHint()
                if size.width() <= 1 or size.height() <= 1:
                    return
                x = geo.center().x() - (size.width() // 2)
                y = geo.center().y() - (size.height() // 2)
                widget.move(x, y)
            else:
                frame = widget.frameGeometry()
                frame.moveCenter(geo.center())
                widget.move(frame.topLeft())
        except Exception:
            return
    
    @pyqtSlot()
    def on_license_verified(self):
        """许可证验证成功后的处理"""
        if self.license_window:
            self.license_window.close()
        self.show_main_window()

def main():
    controller = AppController()
    controller.run()

if __name__ == '__main__':
    main()
