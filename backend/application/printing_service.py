from __future__ import annotations

import base64
import os
import tempfile
from dataclasses import replace
from typing import Any

from backend.domain.state import AppState
from backend.domain.models import PrintingConfig
from backend.repository.interfaces import IStateRepository
from backend.printing.core.utils.data_loader import DataLoader
from backend.printing.core.factory import GeneratorFactory
from backend.printing.core.config import (
    CornerPaperConfig,
    DeskLabelConfig,
    AdmissionTicketConfig,
    StudentInfoTableConfig,
    ExamBagLabelConfig,
)
from backend.printing.core.adapters.examroom_adapter import (
    load_examroom_data_for_corner,
    load_examroom_data_for_student_info,
    load_examroom_data_for_ticket,
    load_examroom_data_for_exam_bag,
)
from backend.printing.core.validators import check_desk_data_sort


def _normalize_output_path(path: str, ext: str) -> str:
    ext = (ext or "").lower()
    if not ext.startswith("."):
        ext = "." + ext
    lower = (path or "").lower()
    if lower.endswith(".xlsx") and ext == ".pdf":
        return path[:-5] + ".pdf"
    if lower.endswith(".pdf") and ext == ".xlsx":
        return path[:-4] + ".xlsx"
    if lower.endswith(ext):
        return path
    if lower.endswith(".xlsx") or lower.endswith(".pdf"):
        return path[:-5] + ext if lower.endswith(".xlsx") else path[:-4] + ext
    return path + ext


class PrintingService:
    def __init__(self, state: AppState, repo: IStateRepository):
        self._state = state
        self._repo = repo

    def _get_exam_arrangement(self):
        """Return exam_arrangement if available (lazy reconstruct via rooms service)."""
        return self._state.exam_arrangement

    def get_state(self, _params: dict) -> Any:
        return {
            "sourceType": self._state.printing.source_type,
            "dataPath": self._state.printing.data_path,
            "headers": self._state.printing.headers,
            "mapping": self._state.printing.mapping,
            "data": self._state.printing.data,
            "total": self._state.printing.total,
            "config": self._state.printing.config,
            "commonConfig": self._state.printing.common_config,
        }

    def save_config(self, params: dict) -> Any:
        if "config" in params:
            self._state.printing.config = params["config"]
        if "commonConfig" in params:
            self._state.printing.common_config = params["commonConfig"]
        if "totalCount" in params:
            self._state.printing.total = params["totalCount"]
        if "sourceType" in params:
            self._state.printing.source_type = params["sourceType"]
        self._repo.save(self._state)
        return {}

    def reset_state(self, _params: dict) -> Any:
        self._state.printing = PrintingConfig()
        self._repo.save(self._state)
        return {}

    def read_headers(self, params: dict) -> Any:
        path = params["path"]
        try:
            headers = DataLoader.get_headers(path)
            self._state.printing.source_type = "file"
            self._state.printing.data_path = path
            self._state.printing.headers = headers
            self._state.printing.data = []
            self._state.printing.total = 0
            self._repo.save(self._state)
            return {"headers": headers}
        except Exception as e:
            return {"error": str(e)}

    def preview_data(self, params: dict) -> Any:
        path = params["path"]
        mapping = params.get("mapping", {})
        type_ = params.get("type")
        try:
            if type_ == "exam_bag_label":
                data = DataLoader.load_exam_bag_data(path)
            elif type_ == "table":
                data = DataLoader.load_student_info_data(path, mapping)
            else:
                data = DataLoader.load_data(path, mapping)

            self._state.printing.source_type = "file"
            self._state.printing.data_path = path
            if mapping:
                self._state.printing.mapping = mapping
            self._state.printing.data = data
            self._state.printing.total = len(data)
            self._repo.save(self._state)

            if type_ == "table":
                return {"data": data, "total": len(data)}
            return {"data": data[:50], "total": len(data)}
        except Exception as e:
            return {"error": str(e)}

    def load_from_schedule(self, params: dict) -> Any:
        try:
            ea = self._get_exam_arrangement()
            if not ea or ea.arranged_students is None:
                return {"error": '暂无考场编排数据，请先在"考场编排"页面完成编排'}

            # 获取打印类型，根据类型选择正确的数据加载函数
            type_ = params.get("type", "table")

            if type_ == "corner":
                # 台角纸：传递 ea 对象，适配器会自动检测高考模式
                data = load_examroom_data_for_corner(ea) or []
            elif type_ == "ticket":
                # 准考证：传递 ea 对象，适配器会自动检测高考模式
                data = load_examroom_data_for_ticket(ea) or []
            else:
                # 考生信息表等其他类型：使用原有逻辑
                df = ea.arranged_students.fillna("")
                data = load_examroom_data_for_student_info(df, include_subject_fields=True) or []

            return {"data": data, "total": len(data)}
        except Exception as e:
            return {"error": str(e)}

    def preview_pdf(self, params: dict) -> Any:
        type_ = params.get("type")
        source_type = params.get("sourceType", "file")
        data_path = params.get("dataPath")
        mapping = params.get("mapping")
        config_data = params.get("config", {}) or {}

        if type_ not in ("corner", "ticket"):
            return {"error": "暂不支持该类型的打印预览"}

        subjects = config_data.get("subjects") or []
        subject_times = config_data.get("subjectTimes") or []
        title = str(config_data.get("title") or "")

        def templates_per_col_page(subject_count: int) -> int:
            if subject_count <= 3: return 5
            if 4 <= subject_count <= 5: return 4
            if 6 <= subject_count <= 9: return 3
            return 2

        capacity = 3 * templates_per_col_page(len(subjects))

        try:
            if source_type == "file":
                if not data_path:
                    return {"error": "未选择导入文件"}
                data_list = DataLoader.load_data(data_path, mapping)
            elif source_type == "schedule":
                ea = self._get_exam_arrangement()
                if not ea or ea.arranged_students is None:
                    return {"error": '暂无考场编排数据，请先在"考场编排"页面完成编排'}
                # 直接传递 ea 对象，适配器会自动检测模式
                data_list = load_examroom_data_for_corner(ea) if type_ == "corner" else load_examroom_data_for_ticket(ea)
                data_list = data_list or []
            elif source_type == "empty":
                data_list = []
            else:
                return {"error": "不支持的数据来源"}
        except Exception as e:
            return {"error": f"读取数据失败: {str(e)}"}

        if data_list:
            group_key = "考场" if type_ == "corner" else "班级"
            first_group = data_list[0].get(group_key, "")
            data_list = [d for d in data_list if d.get(group_key, "") == first_group][:capacity]

        tmp_dir = os.path.join(tempfile.gettempdir(), "examdesk_print_preview")
        os.makedirs(tmp_dir, exist_ok=True)
        out_path = os.path.join(tmp_dir, f"preview_{type_}.pdf")
        num_templates = capacity if source_type == "empty" else len(data_list)

        if type_ == "corner":
            cfg = CornerPaperConfig(output_path=out_path, export_xlsx=False, export_pdf=True, subjects=subjects, title=title, num_templates=num_templates, student_data_list=data_list)
        else:
            cfg = AdmissionTicketConfig(output_path=out_path, export_xlsx=False, export_pdf=True, subjects=subjects, subject_times=subject_times, title=title, num_templates=num_templates, student_data_list=data_list)

        try:
            generator = GeneratorFactory.create_generator(cfg)
            pdf_path = generator.generate()
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            b64_data = base64.b64encode(pdf_bytes).decode("utf-8")
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            return {"data": b64_data}
        except Exception as e:
            return {"error": str(e)}

    def generate(self, params: dict) -> Any:
        type_ = params["type"]
        config_data = params.get("config", {})
        source_type = params.get("sourceType", "file")
        data_path = params.get("dataPath")
        mapping = params.get("mapping")
        output_path = params.get("outputPath")
        confirm_flags = params.get("confirmFlags") or {}

        export_xlsx = bool(config_data.get("exportXlsx", True))
        export_pdf = bool(config_data.get("exportPdf", False))
        if not export_xlsx and not export_pdf:
            return {"error": "请至少选择一种输出格式（xlsx 或 pdf）"}
        if not output_path:
            return {"error": "请选择保存路径"}

        data_list = []
        try:
            if source_type == "file":
                if type_ == "exam_bag_label":
                    data_list = DataLoader.load_exam_bag_data(data_path)
                elif type_ == "table":
                    data_list = DataLoader.load_student_info_data(data_path, mapping)
                else:
                    data_list = DataLoader.load_data(data_path, mapping)
            elif source_type == "schedule":
                ea = self._get_exam_arrangement()
                if not ea or ea.arranged_students is None:
                    return {"error": '暂无考场编排数据，请先在"考场编排"页面完成编排'}
                # 直接传递 ea 对象，适配器会自动检测模式
                if type_ == "corner":
                    data_list = load_examroom_data_for_corner(ea) or []
                elif type_ == "ticket":
                    data_list = load_examroom_data_for_ticket(ea) or []
                elif type_ == "table":
                    df = ea.arranged_students.fillna("")
                    data_list = load_examroom_data_for_student_info(df, include_subject_fields=config_data.get("includeSubjectFields", False)) or []
                elif type_ == "desk":
                    data_list = load_examroom_data_for_corner(ea) or []
                elif type_ == "exam_bag_label":
                    data_list = load_examroom_data_for_exam_bag(ea) or []
                else:
                    data_list = load_examroom_data_for_ticket(ea) or []
            elif source_type == "empty":
                data_list = []
        except Exception as e:
            return {"error": f"读取数据失败: {str(e)}"}

        try:
            config_obj = None
            if type_ == "corner":
                config_obj = CornerPaperConfig(output_path=output_path, export_xlsx=export_xlsx, export_pdf=export_pdf, subjects=config_data.get("subjects", []), title=config_data.get("title", ""), num_templates=config_data.get("numTemplates", 0), student_data_list=data_list)
            elif type_ == "desk":
                if source_type != "empty":
                    ok, msg = check_desk_data_sort(data_list)
                    if not ok and not bool(confirm_flags.get("deskSort")):
                        return {"confirm": {"code": "deskSort", "level": "warning", "title": "排序警告", "message": f"数据存在乱序：{msg}\n是否继续生成？"}}
                    layout_rows = int(config_data.get("layoutRows", 7) or 7)
                    layout_cols = int(config_data.get("layoutCols", 6) or 6)
                    capacity = max(1, layout_rows * layout_cols)
                    room_counts: dict[str, int] = {}
                    for item in data_list:
                        room = str(item.get("考场号", "Unknown"))
                        room_counts[room] = room_counts.get(room, 0) + 1
                    overflow_rooms = [f"考场号 {k}: {c}人 (上限{capacity})" for k, c in room_counts.items() if c > capacity]
                    if overflow_rooms and not bool(confirm_flags.get("deskOverflow")):
                        msg_lines = overflow_rooms[:10]
                        msg_suffix = "\n..." if len(overflow_rooms) > 10 else ""
                        return {"confirm": {"code": "deskOverflow", "level": "question", "title": "人数超限提示", "message": "以下考场人数超过当前布局容量，将自动分两页打印：\n\n" + "\n".join(msg_lines) + msg_suffix + "\n\n是否继续生成？"}}
                config_obj = DeskLabelConfig(output_path=output_path, export_xlsx=export_xlsx, export_pdf=export_pdf, total_count=config_data.get("totalCount", 0) if source_type == "empty" else len(data_list), layout_rows=config_data.get("layoutRows", 7), layout_cols=config_data.get("layoutCols", 6), layout_name=config_data.get("layoutName", ""), layout_pattern=config_data.get("layoutPattern", "S型横排"), start_pos=config_data.get("startPos", "left"), custom_col_counts=config_data.get("customColCounts"), student_data_list=data_list)
            elif type_ == "ticket":
                config_obj = AdmissionTicketConfig(output_path=output_path, export_xlsx=export_xlsx, export_pdf=export_pdf, subjects=config_data.get("subjects", []), subject_times=config_data.get("subjectTimes", []), title=config_data.get("title", ""), num_templates=config_data.get("numTemplates", 0), student_data_list=data_list)
            elif type_ == "table":
                config_obj = StudentInfoTableConfig(output_path=output_path, export_xlsx=export_xlsx, export_pdf=export_pdf, title=config_data.get("title", ""), student_data_list=data_list, template_path=config_data.get("templatePath"), include_subject_fields=config_data.get("includeSubjectFields", False), group_mode=config_data.get("groupMode", "class"))
            elif type_ == "exam_bag_label":
                school_name = str(config_data.get("schoolName") or config_data.get("school_name") or "").strip() or "xxx学校"
                config_obj = ExamBagLabelConfig(output_path=output_path, student_data_list=data_list, school_name=school_name, layout_rows=int(config_data.get("layoutRows", 3) or 3), layout_cols=int(config_data.get("layoutCols", 3) or 3))
            else:
                return {"error": "未知的打印类型"}

            formats = []
            if export_xlsx:
                formats.append("xlsx")
            if export_pdf:
                formats.append("pdf")

            result_paths: list[str] = []
            for fmt in formats:
                if fmt == "xlsx":
                    step_output_path = _normalize_output_path(output_path, ".xlsx")
                    step_config = replace(config_obj, output_path=step_output_path, export_xlsx=True, export_pdf=False)
                else:
                    step_output_path = _normalize_output_path(output_path, ".pdf")
                    step_config = replace(config_obj, output_path=step_output_path, export_xlsx=False, export_pdf=True)
                generator = GeneratorFactory.create_generator(step_config)
                generated_path = generator.generate()
                try:
                    with open(generated_path, "rb") as f:
                        head = f.read(5)
                    if fmt == "pdf" and head != b"%PDF-":
                        raise Exception("输出文件不是有效的 PDF（可能生成过程被中断或被错误覆盖）")
                    if fmt == "xlsx" and head[:2] != b"PK":
                        raise Exception("输出文件不是有效的 Excel（可能生成过程被中断或被错误覆盖）")
                except Exception as e:
                    raise Exception(f"{fmt.upper()} 文件校验失败: {str(e)}")
                result_paths.append(generated_path)

            return {"paths": result_paths}
        except Exception as e:
            return {"error": f"生成失败: {str(e)}"}
