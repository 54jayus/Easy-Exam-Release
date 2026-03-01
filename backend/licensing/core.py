from __future__ import annotations

import base64
import datetime as dt
import hashlib
import os
import platform
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Optional, Tuple

import urllib.request

from .cert_store import LicenseCert, get_default_cert_path


@dataclass
class LicenseStatus:
    valid: bool
    expire_date: dt.datetime | None = None
    message: str = ""
    days_left: int | None = None


class LicenseManager:
    def __init__(
        self,
        *,
        app_secret: str | None = None,
        salt: str | None = None,
        cert_path: str | os.PathLike[str] | None = None,
    ):
        # Keys can be overridden via environment variables for production deployments.
        # Defaults are kept for backward compatibility with existing deployments.
        if app_secret is None:
            app_secret = os.environ.get("EXAMFLOW_APP_SECRET", "54lanyue")
        if salt is None:
            salt = os.environ.get("EXAMFLOW_SALT", "paijiankao2025")
        self.app_secret = app_secret
        self.salt = salt
        self.time_servers = [
            "https://www.baidu.com",
            "https://www.taobao.com",
            "https://time1.aliyun.com",
            "https://www.163.com",
        ]
        self.timeout_seconds = 3
        self._cached_network_time: dt.datetime | None = None
        self._cache_expire_at: float = 0.0
        self.cert_path = str(cert_path) if cert_path is not None else str(get_default_cert_path())

    def get_machine_code(self) -> str:
        try:
            system_info = platform.system()
            node_info = platform.node()
            processor_info = platform.processor()
            disk_serial = ""

            if system_info == "Windows":
                disk_serial = self._get_windows_volume_serial() or ""
            elif system_info == "Linux":
                p = "/etc/machine-id"
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        disk_serial = f.read().strip()
            elif system_info == "Darwin":
                try:
                    result = subprocess.run(
                        ["ioreg", "-l", "-d", "2", "-w", "0", "-c", "IOPlatformExpertDevice"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                    for line in result.stdout.splitlines():
                        if "IOPlatformUUID" in line:
                            disk_serial = line.split("=")[1].strip().strip('"')
                            break
                except Exception:
                    disk_serial = ""
            else:
                disk_serial = str(uuid.getnode())

            hardware_info = f"{system_info}-{node_info}-{processor_info}-{disk_serial}"
            return hashlib.md5(hardware_info.encode()).hexdigest()[:16].upper()
        except Exception:
            return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16].upper()

    def _get_windows_volume_serial(self) -> str:
        try:
            import wmi  # type: ignore

            c = wmi.WMI()
            for disk in c.Win32_LogicalDisk(DeviceID="C:"):
                serial = (disk.VolumeSerialNumber or "").strip()
                if serial:
                    return serial
        except Exception:
            pass

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_LogicalDisk -Filter \"DeviceID='C:'\").VolumeSerialNumber",
                ],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
            serial = (result.stdout or "").strip()
            if serial:
                return serial
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["cmd", "/c", "vol", "C:"],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
            text_out = (result.stdout or "") + "\n" + (result.stderr or "")
            m = re.search(r"([0-9A-Fa-f]{4}-[0-9A-Fa-f]{4})", text_out)
            if m:
                return m.group(1).replace("-", "").upper()
        except Exception:
            pass

        return ""

    def get_beijing_time(self) -> dt.datetime | None:
        now = time.time()
        if self._cached_network_time is not None and now < self._cache_expire_at:
            return self._cached_network_time

        for server in self.time_servers:
            try:
                req = urllib.request.Request(server, method="HEAD")
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    date_header = resp.headers.get("Date") or ""
                if not date_header:
                    continue
                gmt_time = dt.datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S GMT")
                beijing_time = gmt_time + dt.timedelta(hours=8)
                self._cached_network_time = beijing_time
                self._cache_expire_at = now + 3600
                return beijing_time
            except Exception:
                continue
        return None

    def generate_reg_code(self, machine_code: str, days: int) -> tuple[str, dt.datetime]:
        current_time = dt.datetime.now()
        expire_date = current_time + dt.timedelta(days=days)
        expire_timestamp = int(expire_date.timestamp())
        combined = f"{machine_code}|{expire_timestamp}|{self.app_secret}|{self.salt}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        hash_b64 = base64.urlsafe_b64encode(hash_bytes).decode().rstrip("=")
        return f"{expire_timestamp}-{hash_b64}", expire_date

    def verify_reg_code(self, machine_code: str, reg_code: str) -> LicenseStatus:
        current_time = self.get_beijing_time()
        if current_time is None:
            return LicenseStatus(valid=False, message="无法获取网络时间，请检查网络连接")

        reg_code = (reg_code or "").replace(" ", "").strip()
        if "-" not in reg_code:
            return LicenseStatus(valid=False, message="注册码格式错误（缺少分隔符）")

        timestamp_str, hash_b64 = reg_code.split("-", 1)
        try:
            expire_timestamp = int(timestamp_str)
        except ValueError:
            return LicenseStatus(valid=False, message="注册码时间戳格式错误")

        expire_date = dt.datetime.fromtimestamp(expire_timestamp)
        if current_time > expire_date:
            return LicenseStatus(
                valid=False,
                expire_date=expire_date,
                message=f"注册码已过期\n到期日：{expire_date.strftime('%Y-%m-%d')}",
                days_left=0,
            )

        combined = f"{machine_code}|{expire_timestamp}|{self.app_secret}|{self.salt}"
        expected_hash = hashlib.sha256(combined.encode()).digest()
        expected_hash_b64 = base64.urlsafe_b64encode(expected_hash).decode().rstrip("=")
        if hash_b64 != expected_hash_b64:
            return LicenseStatus(valid=False, message="注册码无效或已被篡改")

        days_left = (expire_date - current_time).days + 1
        return LicenseStatus(valid=True, expire_date=expire_date, days_left=days_left, message="OK")

    def load_cert(self) -> LicenseCert:
        return LicenseCert.load(self.cert_path)

    def save_cert(self, cert: LicenseCert) -> None:
        cert.save(self.cert_path)

    def verify_cert(self) -> LicenseStatus:
        cert = self.load_cert()
        if not cert.license_code:
            return LicenseStatus(valid=False, message="证书文件不存在或为空")
        machine_code = self.get_machine_code()
        return self.verify_reg_code(machine_code, cert.license_code)
