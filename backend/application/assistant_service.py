from __future__ import annotations

from typing import Any

from backend.assistant import AssistantEngine


class AssistantService:
    def __init__(self, engine: AssistantEngine):
        self._engine = engine

    def generate_reply(self, params: dict) -> Any:
        user_text = params.get("userText") or ""
        attachments = params.get("attachments") or []
        history = params.get("history") or []
        ui_context_text = params.get("uiContextText") or ""
        reply = self._engine.generate_reply(
            user_text, attachments, history, ui_context_text=ui_context_text
        )
        return {"reply": reply}

    def check_config(self, _params: dict) -> Any:
        has_key = bool(self._engine.client.api_key)
        return {"configured": has_key}

    def configure(self, params: dict) -> Any:
        from backend.assistant.core.zhipu_client import save_api_key
        api_key = str(params.get("apiKey") or "").strip()
        if not api_key:
            return {"success": False, "error": "API Key 不能为空"}
        try:
            save_api_key(api_key)
        except Exception as e:
            return {"success": False, "error": f"保存 API Key 失败: {e}"}
        try:
            test_payload = {
                "model": "glm-4.6v-flash",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.1,
                "max_tokens": 10,
            }
            self._engine.client.create_chat_completion(test_payload, timeout=10)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": f"API Key 测试失败: {e}"}
