import os
import re
import json
import urllib.request
import urllib.error
import sys
import logging
from urllib.parse import urljoin

from backend.licensing import LicenseCert
from backend.licensing.cert_store import get_app_base_dir, get_default_cert_path

logger = logging.getLogger(__name__)

class ZhipuApiError(RuntimeError):
    pass


def _get_base_path():
    return str(get_app_base_dir())


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

    cert = LicenseCert.load(get_default_cert_path())
    if cert.api_key:
        return cert.api_key

    # 如果 license.cert 中没有，检查传统的 apikey.txt
    base = _get_base_path()
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
    
    # Check if raw key is just the content
    for p in candidates:
        raw = _try_read_text(p).strip()
        if raw and "." in raw and len(raw) > 20 and not " " in raw:
            return raw

    return ""

def save_api_key(api_key: str):
    base = _get_base_path()
    # Save to root apikey.txt
    path = os.path.join(base, "apikey.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"API_KEY = {api_key.strip()}")


class ZhipuChatClient:
    def __init__(self, api_key=None, base_url="https://open.bigmodel.cn/api/paas/v4/"):
        self._manual_api_key = api_key
        self.base_url = base_url

    @property
    def api_key(self):
        if self._manual_api_key:
            return self._manual_api_key
        return load_api_key()

    def create_chat_completion(self, payload, timeout=60):
        if not self.api_key:
            raise ZhipuApiError("未检测到 API Key，请配置环境变量 ZAI_API_KEY 或 apikey.txt。")

        import time
        url = urljoin(self.base_url, "chat/completions")
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=body, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("Authorization", f"Bearer {self.api_key}")

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")

                return json.loads(raw)

            except urllib.error.HTTPError as e:
                http_code = getattr(e, 'code', 0)
                try:
                    raw_err = e.read().decode("utf-8", errors="replace")
                except Exception:
                    raw_err = ""
                # 429 Too Many Requests: retry with exponential backoff
                if http_code == 429 and attempt < max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning("API 限流（429），第 %s 次重试，等待 %ss", attempt + 1, wait)
                    time.sleep(wait)
                    last_error = ZhipuApiError(f"HTTP 429 限流：{raw_err[:400]}")
                    continue
                raise ZhipuApiError(f"HTTP {http_code} 请求失败：{raw_err[:4000]}") from None

            except Exception as e:
                last_error = e
                logger.warning("第 %s 次请求失败: %s", attempt + 1, e)
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue

        raise ZhipuApiError(f"请求失败（重试{max_retries}次后）：{last_error}") from None

