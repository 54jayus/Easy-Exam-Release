import hashlib
import platform
import uuid
import datetime
import base64
import requests
import time
import os
import sys
from typing import Tuple, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QMessageBox, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime, QTimer
from PyQt5.QtGui import QFont, QIcon

class NetworkTimeLicenseManager:
    """使用网络时间验证的带时间限制注册码管理类（含证书文件管理）"""
    
    def __init__(self):
        """初始化许可证管理器"""
        self.app_secret = "54lanyue"
        self.salt = "paijiankao2025"  # 盐值，用于增强安全性
        # 网络时间服务器列表（增加HTTPS和NTP服务器）
        self.time_servers = [
            "https://www.baidu.com",
            "https://www.taobao.com",
            "https://time1.aliyun.com",
            "https://www.163.com",
            "https://www.google.com"
        ]
        self.timeout = 3  # 缩短超时时间提高响应速度
        self.cached_network_time = None  # 缓存的网络时间
        self.cache_expiry = 3600  # 缓存过期时间（秒）
        self.cert_file = "license.cert"  # 证书文件路径
        self.last_error = ""  # 记录最后一次错误信息

    def get_machine_code(self) -> str:
        """获取当前设备的机器码（唯一标识符）"""
        try:
            system_info = platform.system() # 用于获取当前操作系统的名称
            node_info = platform.node() # 获取当前计算机的网络名称
            processor_info = platform.processor() # 获取当前计算机的处理器信息
            disk_serial = ""
            
            if system_info == "Windows":
                # Windows系统获取磁盘序列号
                import wmi
                c = wmi.WMI()
                for disk in c.Win32_LogicalDisk(DeviceID="C:"):
                    disk_serial = disk.VolumeSerialNumber or ""
            elif system_info == "Linux":
                # Linux系统读取machine-id
                if os.path.exists("/etc/machine-id"):
                    with open("/etc/machine-id", "r") as f:
                        disk_serial = f.read().strip()
            elif system_info == "Darwin":  # macOS
                # macOS系统获取平台UUID
                import subprocess
                result = subprocess.run(
                    ["ioreg", "-l", "-d", "2", "-w", "0", "-c", "IOPlatformExpertDevice"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "IOPlatformUUID" in line:
                        disk_serial = line.split("=")[1].strip().strip('"')
                        break
            else:
                # 其他系统使用MAC地址
                disk_serial = str(uuid.getnode())
            
            # 组合硬件信息并生成MD5哈希值
            hardware_info = f"{system_info}-{node_info}-{processor_info}-{disk_serial}" # 硬件信息组合
            machine_code = hashlib.md5(hardware_info.encode()).hexdigest()[:16] # 截取前16位作为机器码
            
            return machine_code.upper() 
        except Exception as e:
            self.last_error = f"获取机器码失败: {str(e)}"
            print(self.last_error)
            # 出错时返回随机生成的机器码
            return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()
    
    def get_beijing_time(self) -> Optional[datetime.datetime]:
        """获取北京时间（UTC+8）"""
        # 检查缓存是否有效
        if self.cached_network_time and time.time() < self.cache_expiry:
            return self.cached_network_time
        
        # 尝试从多个时间服务器获取时间
        for server in self.time_servers:
            try:
                response = requests.head(server, timeout=self.timeout, allow_redirects=True)
                if 'Date' in response.headers:
                    # 解析HTTP响应头中的GMT时间
                    gmt_time = datetime.datetime.strptime(
                        response.headers['Date'],
                        '%a, %d %b %Y %H:%M:%S GMT'
                    )
                    # 转换为北京时间（GMT+8）
                    beijing_time = gmt_time + datetime.timedelta(hours=8)
                    
                    # 更新缓存
                    self.cached_network_time = beijing_time
                    self.cache_expiry = time.time() + self.cache_expiry
                    
                    return beijing_time
            except Exception as e:
                print(f"从{server}获取时间失败: {str(e)}")
                continue
        
        self.last_error = "无法获取网络时间，请检查网络连接"
        print(self.last_error)
        return None
    
    def generate_reg_code(self, machine_code: str, days: int) -> Tuple[str, datetime.datetime]:
        """生成带时间限制的注册码"""
        current_time = datetime.datetime.now()
        expire_date = current_time + datetime.timedelta(days=days) # 计算过期日期
        expire_timestamp = int(expire_date.timestamp())
        
        # 组合关键信息并生成SHA256哈希值
        combined = f"{machine_code}|{expire_timestamp}|{self.app_secret}|{self.salt}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        hash_b64 = base64.urlsafe_b64encode(hash_bytes).decode().rstrip('=')
        
        # 注册码格式：时间戳-Base64哈希
        reg_code = f"{expire_timestamp}-{hash_b64}"
        
        return reg_code, expire_date

    def _create_cert_file(self, machine_code: str, reg_code: str, expire_date: datetime.datetime) -> bool:
        """创建证书文件，返回是否成功"""
        try:
            # 确保目录存在
            cert_dir = os.path.dirname(self.cert_file)
            if cert_dir and not os.path.exists(cert_dir):
                os.makedirs(cert_dir, exist_ok=True)
                
            with open(self.cert_file, 'w') as f:
                f.write(reg_code)
            print(f"证书文件已保存至: {self.cert_file}")
            return True
        except Exception as e:
            self.last_error = f"创建证书文件失败: {str(e)}"
            print(self.last_error)
            return False

    def _verify_cert_file(self) -> Tuple[bool, Optional[datetime.datetime], Optional[str]]:
        """验证证书文件是否有效"""
        # 检查证书文件是否存在
        if not os.path.exists(self.cert_file):
            return False, None, "证书文件不存在"
        
        try:
            # 读取证书内容
            with open(self.cert_file, 'r') as f:
                # 只读取第一行作为注册码，忽略后续可能附加的API KEY等信息
                reg_code = f.readline().strip()
            
            # 如果文件为空，说明无效
            if not reg_code:
                return False, None, "证书文件为空"
            
            # 验证证书中的注册码是否有效
            current_machine_code = self.get_machine_code()
            verify_result, expire_date, error_msg = self.verify_reg_code(
                current_machine_code, 
                reg_code
            )
            if not verify_result:
                return False, None, f"证书中的注册码无效: {error_msg}"
            
            return True, expire_date, None
        except Exception as e:
            return False, None, f"证书验证失败: {str(e)}"

    def verify_reg_code(self, machine_code: str, reg_code: str) -> Tuple[bool, Optional[datetime.datetime], Optional[str]]:
        """验证注册码（使用网络时间）"""
        try:
            # 获取网络时间
            current_time = self.get_beijing_time()
            if not current_time:
                return False, None, self.last_error or "无法获取网络时间，无法验证注册码"
            
            # 清理注册码格式
            reg_code = reg_code.replace(" ", "").strip()
            if '-' not in reg_code:
                return False, None, "注册码格式错误（缺少分隔符）"
                
            # 分割注册码
            parts = reg_code.split('-', 1)
            if len(parts) != 2:
                return False, None, "注册码格式错误（分割后部分不正确）"
                
            timestamp_str, hash_b64 = parts
            try:
                expire_timestamp = int(timestamp_str)
            except ValueError:
                return False, None, "注册码时间戳格式错误"
                
            # 检查是否过期
            expire_date = datetime.datetime.fromtimestamp(expire_timestamp)
            if current_time > expire_date:
                return False, expire_date, f"注册码已过期（到期日：{expire_date.strftime('%Y-%m-%d')}）"
                
            # 重新计算哈希值进行验证
            combined = f"{machine_code}|{expire_timestamp}|{self.app_secret}|{self.salt}"
            expected_hash = hashlib.sha256(combined.encode()).digest()
            expected_hash_b64 = base64.urlsafe_b64encode(expected_hash).decode().rstrip('=')
            
            if hash_b64 == expected_hash_b64:
                return True, expire_date, None
            else:
                return False, None, "注册码无效或已被篡改"
                
        except Exception as e:
            return False, None, f"验证失败: {str(e)}"


class LicenseWorker(QThread):
    """工作线程，用于执行耗时的许可证操作"""
    # 信号：(成功标志, 消息, 详细信息)
    result = pyqtSignal(bool, str, str)
    
    def __init__(self, action, *args):
        super().__init__()
        self.action = action
        self.args = args
        self.license_manager = NetworkTimeLicenseManager()
        self.is_running = True
    
    def run(self):
        """线程执行函数"""
        try:
            if not self.is_running:
                return
                
            if self.action == "check_cert":
                # 检查证书文件
                cert_valid, exp_date, cert_msg = self.license_manager._verify_cert_file()
                if cert_valid and exp_date:
                    current_time = self.license_manager.get_beijing_time()
                    if current_time:
                        days_left = (exp_date - current_time).days + 1
                        self.result.emit(
                            True, 
                            f"证书验证成功！有效期至: {exp_date.strftime('%Y-%m-%d')}", 
                            f"剩余使用天数: {days_left}天"
                        )
                    else:
                        self.result.emit(
                            True, 
                            f"证书验证成功！有效期至: {exp_date.strftime('%Y-%m-%d')}", 
                            "无法获取网络时间"
                        )
                else:
                    self.result.emit(False, "证书检查失败", cert_msg or "未知错误")
            
            elif self.action == "get_machine_code":
                # 获取机器码
                machine_code = self.license_manager.get_machine_code()
                self.result.emit(True, "获取机器码成功", machine_code)
            
            elif self.action == "verify_reg_code":
                # 验证注册码
                if len(self.args) < 2:
                    self.result.emit(False, "参数错误", "缺少机器码或注册码参数")
                    return
                    
                machine_code, reg_code = self.args
                verify_result, exp_date, error_msg = self.license_manager.verify_reg_code(machine_code, reg_code)
                if verify_result and exp_date:
                    # 验证成功，创建证书文件
                    if self.license_manager._create_cert_file(machine_code, reg_code, exp_date):
                        current_time = self.license_manager.get_beijing_time()
                        if current_time:
                            days_left = (exp_date - current_time).days + 1
                            self.result.emit(
                                True, 
                                f"注册码验证成功！有效期至: {exp_date.strftime('%Y-%m-%d')}", 
                                f"剩余使用天数: {days_left}天"
                            )
                        else:
                            self.result.emit(
                                True, 
                                f"注册码验证成功！有效期至: {exp_date.strftime('%Y-%m-%d')}", 
                                ""
                            )
                    else:
                        self.result.emit(False, "创建证书失败", self.license_manager.last_error)
                else:
                    self.result.emit(False, "注册码验证失败", error_msg or "未知错误")
        except Exception as e:
            self.result.emit(False, "操作失败", str(e))
    
    def stop(self):
        """停止线程"""
        self.is_running = False
        self.wait()


class LicenseManagerUI(QMainWindow):
    """许可证管理界面"""
    # 许可证验证成功信号
    license_verified = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.license_manager = NetworkTimeLicenseManager()
        self.worker = None  # 工作线程
        self.init_ui()
        self.check_certificate()  # 启动时自动检查证书
        
        # 添加定时器，定期检查证书状态
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_certificate)
        self.timer.start(3600000)  # 每小时检查一次
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("证书校验 - 智能考务系统")
        self.setGeometry(600, 200, 600, 700)
        self.setMinimumSize(600, 600)
        self.setWindowIcon(QIcon(self.get_resource_path("ui/pic/license.svg")))
        

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15) # 设置布局中各控件之间的间距为 15 像素
        main_layout.setContentsMargins(20, 20, 20, 20) # 设置布局的四周边距为 20 像素
        
        # 标题
        title_label = QLabel("软件许可证验证")
        title_label.setFont(QFont("", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter) # 设置标题居中对齐
        main_layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine) # 设置为水平线
        line.setFrameShadow(QFrame.Sunken) # 设置为阴影效果
        main_layout.addWidget(line)
        
        # 状态显示区域
        status_group = QGroupBox("许可证状态") 
        status_layout = QVBoxLayout()
        self.status_label = QLabel("正在检查许可证状态...")
        self.status_label.setWordWrap(True) # 设置文本自动换行
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 机器码显示区域
        machine_group = QGroupBox("机器码 (请将此码提供给管理员获取注册码)")
        machine_layout = QVBoxLayout()
        # 显示机器码
        machine_code = self.license_manager.get_machine_code()
        self.machine_code_label = QLabel(machine_code)
        self.machine_code_label.setWordWrap(True)
        self.machine_code_label.setStyleSheet("padding: 5px;font-size: 14px;color:green;")
        machine_layout.addWidget(self.machine_code_label)
        
        # 复制按钮
        copy_btn = QPushButton("复制机器码")
        copy_btn.clicked.connect(self.copy_machine_code)
        machine_layout.addWidget(copy_btn)
        
        machine_group.setLayout(machine_layout)
        main_layout.addWidget(machine_group)
        
        # 注册码输入区域
        reg_group = QGroupBox("注册码验证")
        reg_layout = QVBoxLayout()
        
        reg_layout.addWidget(QLabel("请输入管理员提供的注册码:"))
        self.reg_code_input = QLineEdit()
        self.reg_code_input.setPlaceholderText("例如: 1629260800-abcdefghijklmnopqrstuvwxyz")
        reg_layout.addWidget(self.reg_code_input)
        
        # 验证按钮
        verify_btn = QPushButton("验证注册码")
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        verify_btn.clicked.connect(self.verify_reg_code)
        reg_layout.addWidget(verify_btn)
        
        reg_group.setLayout(reg_layout)
        main_layout.addWidget(reg_group)
        
        # 联系方式区域
        contact_group = QGroupBox("联系方式")
        contact_layout = QVBoxLayout()
        contact_label = QLabel("如有问题，请联系管理员：\n微信号: lhr44971")
        contact_label.setWordWrap(True)
        contact_label.setStyleSheet("padding: 5px; font-size: 14px; color: #333;")
        contact_layout.addWidget(contact_label)
        contact_group.setLayout(contact_layout)
        main_layout.addWidget(contact_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定进度模式
        main_layout.addWidget(self.progress_bar)
        
        # 底部信息
        info_label = QLabel("提示: 请确保您的电脑已连接互联网以验证许可证")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(info_label)
    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径"""
        if hasattr(sys, '_MEIPASS'):
            # 如果是打包后的exe文件
            return os.path.join(sys._MEIPASS, relative_path)
        # 如果是python脚本
        return os.path.join(os.path.abspath("."), relative_path)
    def copy_machine_code(self):
        """复制机器码到剪贴板"""
        machine_code = self.machine_code_label.text()
        clipboard = QApplication.clipboard() # 获取剪贴板对象
        clipboard.setText(machine_code) # 设置剪贴板内容
        QMessageBox.information(self, "复制成功", "机器码已复制到剪贴板")
    
    def check_certificate(self):
        """检查证书文件"""
        self._stop_worker()
        self.progress_bar.setVisible(True)
        self.worker = LicenseWorker("check_cert")
        self.worker.result.connect(self.on_check_cert_result)
        self.worker.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.worker.start()
    
    def verify_reg_code(self):
        """验证注册码"""
        reg_code = self.reg_code_input.text().strip()
        if not reg_code:
            QMessageBox.warning(self, "输入错误", "请输入注册码")
            return
        
        self._stop_worker()
        self.progress_bar.setVisible(True)
        self.worker = LicenseWorker("verify_reg_code", self.license_manager.get_machine_code(), reg_code)
        self.worker.result.connect(self.on_verify_reg_code_result)
        self.worker.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.worker.start()
    
    def _stop_worker(self):
        """停止当前工作线程"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
    
    def on_check_cert_result(self, success, message, detail):
        """证书检查结果处理"""
        if success:
            self.status_label.setText(f"<font color='green'>{message}</font><br/>{detail}")
            # 延迟发送信号，确保UI更新完成
            QTimer.singleShot(500, self.license_verified.emit)
        else:
            self.status_label.setText(f"<font color='red'>{message}: {detail}</font>")
    
    def on_verify_reg_code_result(self, success, message, detail):
        """注册码验证结果处理"""
        if success:
            self.status_label.setText(f"<font color='green'>{message}</font><br/>{detail}")
            QMessageBox.information(self, "验证成功", f"{message}\n{detail}")
            # 延迟发送信号，确保UI更新完成
            QTimer.singleShot(500, self.license_verified.emit)
        else:
            self.status_label.setText(f"<font color='red'>{message}: {detail}</font>")
            QMessageBox.critical(self, "验证失败", f"{message}: {detail}")
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self._stop_worker()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LicenseManagerUI()
    window.show()
    sys.exit(app.exec_())