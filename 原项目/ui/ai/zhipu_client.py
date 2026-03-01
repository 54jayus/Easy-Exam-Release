import os
import re
import json
import urllib.request
import urllib.error
import sys
from urllib.parse import urljoin


class ZhipuApiError(RuntimeError):
    pass


def _get_base_path():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _try_read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_api_key():
    env_key = os.getenv("ZAI_API_KEY") or os.getenv("ZHIPUAI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    base = _get_base_path()
    
    # 优先检查 license.cert
    # 增加对 PyInstaller 打包后的路径支持（优先检查可执行文件同级目录）
    cert_paths = []
    
    if getattr(sys, "frozen", False):
        # 打包环境下，优先检查 exe 同级目录
        cert_paths.append(os.path.join(os.path.dirname(sys.executable), "license.cert"))
    
    # 检查 base 目录（开发环境为项目根目录，打包环境为临时目录）
    cert_paths.append(os.path.join(base, "license.cert"))
    
    # 检查当前工作目录
    cert_paths.append(os.path.join(os.getcwd(), "license.cert"))

    # 去重并检查
    checked_paths = set()
    for license_cert_path in cert_paths:
        abs_path = os.path.abspath(license_cert_path)
        if abs_path in checked_paths:
            continue
        checked_paths.add(abs_path)
        
        if os.path.exists(license_cert_path):
            try:
                with open(license_cert_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # license.cert 格式：
                    # 第一行：License Code
                    # 第二行：API_KEY:xxxxx (可选)
                    if len(lines) >= 2:
                        second_line = lines[1].strip()
                        if second_line.startswith("API_KEY:"):
                            key_part = second_line.split("API_KEY:", 1)[1].strip()
                            if key_part:
                                return key_part
            except Exception:
                pass

    # 如果 license.cert 中没有，检查传统的 apikey.txt
    candidates = [
        os.path.join(base, "智谱清言api文档", "apikey.txt"),
        os.path.join(base, "api文档", "apikey.txt"),
        os.path.join(base, "apikey.txt"),
    ]
    for p in candidates:
        raw = _try_read_text(p)
        if not raw.strip():
            continue
        m = re.search(r"API\s*key\s*:\s*([A-Za-z0-9_\-\.]+)", raw, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"API_KEY\s*=\s*([A-Za-z0-9_\-\.]+)", raw, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return ""


class ZhipuChatClient:
    def __init__(self, api_key=None, base_url="https://open.bigmodel.cn/api/paas/v4/"):
        self.api_key = api_key if api_key is not None else load_api_key()
        self.base_url = base_url

    def create_chat_completion(self, payload, timeout=60):
        if not self.api_key:
            raise ZhipuApiError("未检测到 API Key，请配置环境变量 ZAI_API_KEY 或 apikey.txt。")

        url = urljoin(self.base_url, "chat/completions")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
        # Simple retry logic
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("Authorization", f"Bearer {self.api_key}")
                
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                    
                data = json.loads(raw)
                return data
                
            except urllib.error.HTTPError as e:
                # 4xx errors usually shouldn't be retried (except maybe 429)
                try:
                    raw_err = e.read().decode("utf-8", errors="replace")
                except Exception:
                    raw_err = ""
                raise ZhipuApiError(f"HTTP {getattr(e, 'code', '')} 请求失败：{raw_err[:4000]}") from None
                
            except Exception as e:
                last_error = e
                print(f"[ZhipuClient] Attempt {attempt+1} failed: {e}")
                import time
                if attempt < max_retries:
                    time.sleep(1)
                    continue
        
        raise ZhipuApiError(f"请求失败（重试{max_retries}次后）：{last_error}") from None
