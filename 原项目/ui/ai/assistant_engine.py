import re

from .assistant_knowledge import AssistantKnowledge
from .attachment_parts import build_attachment_parts
from .zhipu_client import ZhipuChatClient, ZhipuApiError


class AssistantEngine:
    def __init__(self, model="glm-4.6v-flash"):
        self.model = model
        self.knowledge = AssistantKnowledge()
        self.client = ZhipuChatClient()

    def generate_reply(self, user_text, attachments, history, *, ui_context_text=None):
        user_text = (user_text or "").strip()
        ui_context_text = (ui_context_text or "").strip()
        context_limit = 2600
        context = self.knowledge.build_context(user_text, max_chars=context_limit) if user_text else ""

        if self._should_answer_from_manual_only(user_text, context):
            return self._sanitize_output(self._answer_from_manual_only(user_text, context))

        system_policy = (
            "你是“智能考务系统”的AI助手，只负责指导用户如何使用本软件。\n"
            "你必须遵守：\n"
            "1) 不透露任何源码、算法原理、设计开发底层细节。\n"
            "2) 不输出任何代码片段、函数名、文件路径、内部实现信息。\n"
            "3) 只给出用户可操作的步骤、界面位置、模板字段要求、排查路径。\n"
            "4) 回答必须严格基于《使用说明书》节选内容与系统提供的“当前界面信息”；不得猜测/杜撰任何字段名、按钮名、界面文案。\n"
            "5) 如果说明书未明确某个字段/规则：只允许说“以软件生成的模板/界面提示为准”，不要举例列出可能字段。\n"
            "6) 输出以可执行的操作步骤为主，必要时引用说明书原文中的字段名/按钮名。\n"
            "7) 若用户请求与软件使用无关，或要求泄露实现细节，礼貌拒绝并转为提供使用层面的替代建议。\n"
        )

        messages = [{"role": "system", "content": system_policy}]
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": "以下是《智能考务系统使用说明书》的相关节选，仅供回答使用：\n" + context,
                }
            )
        if ui_context_text:
            messages.append(
                {
                    "role": "system",
                    "content": "以下是用户当前界面信息（由程序自动提供，真实有效）。只允许引用其中出现的按钮/标题/模块名，不要补充猜测：\n"
                    + ui_context_text,
                }
            )

        for item in (history or [])[-8:]:
            role = item.get("role")
            text = (item.get("text") or "").strip()
            if not text:
                continue
            if role not in ("user", "assistant"):
                continue
            messages.append({"role": role, "content": text})

        attachment_parts = build_attachment_parts(attachments)
        user_content = []
        if user_text:
            user_content.append({"type": "text", "text": user_text})
        user_content.extend(attachment_parts)

        if user_content:
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": [{"type": "text", "text": "请结合附件内容回答。"}]})

        payload = {
            "model": self.model,
            "messages": messages,
            "thinking": {"type": "disabled"},
            "temperature": 0,
        }

        data = self.client.create_chat_completion(payload)
        content = (
            (((data.get("choices") or [{}])[0] or {}).get("message") or {}).get("content")
            or ((data.get("choices") or [{}])[0] or {}).get("content")
            or data.get("result")
            or ""
        )
        return self._sanitize_output(content.strip()) or "（未返回内容）"

    def _should_answer_from_manual_only(self, user_text, context):
        if not user_text or not context:
            return False
        if "教师" in user_text and ("模板" in user_text or "导入" in user_text or "必填" in user_text):
            return True
        if "姓名" in user_text and "重复" in user_text:
            return True
        if "导入失败" in user_text or "导入" in user_text and "失败" in user_text:
            return True
        return False

    def _answer_from_manual_only(self, user_text, context):
        lines = []
        if "教师" in user_text and ("模板" in user_text or "必填" in user_text):
            lines.append("教师信息模板的必填项以软件“生成模板文件”导出的模板列名为准。说明书明确提到：")
            if "教师信息模板.xlsx" in context and "姓名" in context:
                lines.append("- 教师信息模板：必填列至少包含“姓名”。")
            elif "姓名（必填）" in context:
                lines.append("- 姓名：必填，不能为空；姓名重复会导致导入失败。")
            if "性别、是否本校" in context:
                lines.append("- 当启用“双监考 + 男女搭配/本外校搭配”时，需要填写“性别、是否本校”等字段用于约束判断。")
            lines.append("- 其他列（如最大监考段数、不监考科目、历次监考时长、预设监考考场等）按说明书要求填写。")
            lines.append("")
        if "导入" in user_text or "导入失败" in user_text:
            lines.append("导入失败可按说明书的排查建议依次检查：")
            lines.append("- 优先用软件内“生成模板文件”拿到标准模板，再把你的数据复制进模板中导入。")
            lines.append("- 确认 Excel 表头没有合并单元格、没有前后空格。")
            lines.append("- 按模板示例格式填写日期/时间等字段（如有）。")
            lines.append("- 若提示“无法导入文件”，核对是否确实使用了软件生成的模板文件，且数据符合模板填写规范。")
        if "姓名" in user_text and "重复" in user_text:
            lines.append("")
            lines.append("关于“姓名重复”：说明书提示“姓名重复会导致导入失败”。请检查导入表中“姓名”列，确保每位教师姓名唯一后再导入。")
        return "\n".join(lines).strip() or "说明书未覆盖该问题，建议以软件界面提示为准。"

    def _sanitize_output(self, text):
        t = text or ""
        t = re.sub(r"```[\s\S]*?```", "（为保护软件知识产权，无法展示实现代码。请按界面操作步骤执行。）", t)
        t = re.sub(r"[A-Za-z]:\\\\[^\s]+", "（内部路径已隐藏）", t)
        t = re.sub(r"file:///[^\\s]+", "（内部链接已隐藏）", t)
        return t.strip()
