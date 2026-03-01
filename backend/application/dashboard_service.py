from __future__ import annotations

from typing import Any

from backend.domain.state import AppState


class DashboardService:
    def __init__(self, state: AppState):
        self._state = state

    def get_stats(self, _params: dict) -> Any:
        subject_count = len(self._state.subjects)
        teacher_count = len(self._state.proctoring.teachers)

        room_count = len(self._state.rooms.settings_data)
        ea = self._state.exam_arrangement
        if room_count == 0 and ea:
            room_count = ea.total_rooms

        student_count = 0
        if self._state.rooms.results:
            student_count = len(self._state.rooms.results)
        elif ea and ea.arranged_students is not None:
            student_count = len(ea.arranged_students)

        has_subjects = subject_count > 0
        has_teachers = teacher_count > 0
        has_rooms = room_count > 0
        has_students = student_count > 0
        has_schedule = self._state.proctoring.schedule is not None

        shortage_str = "未检测"
        if not has_teachers:
            shortage_str = "未导入"
        elif not has_schedule:
            shortage_str = "未编排"
        else:
            is_complete = True
            mode = self._state.proctoring.config.get("mode", "single")
            if self._state.proctoring.schedule:
                for subj in self._state.proctoring.schedule:
                    for room in subj.get("rooms", []):
                        teachers = room.get("teachers", [])
                        valid_count = sum(1 for t in teachers if t is not None)
                        if mode == "double" and valid_count < 2:
                            is_complete = False
                            break
                        elif mode != "double" and valid_count < 1:
                            is_complete = False
                            break
                    if not is_complete:
                        break
            else:
                is_complete = False
            shortage_str = "充足" if is_complete else "不足"

        wf_subjects = "completed" if has_subjects else "current"
        wf_proctoring = "pending"
        if has_subjects:
            wf_proctoring = "current"
        if has_teachers and has_schedule:
            wf_proctoring = "completed"
        wf_rooms = "pending"
        if has_subjects:
            wf_rooms = "current"
        if ea and ea.arranged_students is not None:
            wf_rooms = "completed"
        wf_printing = "pending"
        if wf_proctoring == "completed" and wf_rooms == "completed":
            wf_printing = "current"

        c_success = "bg-emerald-50 text-emerald-600"
        c_neutral = "bg-slate-100 text-slate-500"
        c_danger = "bg-rose-50 text-rose-600"
        c_warning = "bg-amber-50 text-amber-600"

        t1_trend = "已就绪" if has_subjects else "未设置"
        t1_class = c_success if has_subjects else c_neutral
        t2_trend = shortage_str
        t2_class = c_success if shortage_str == "充足" else (c_danger if shortage_str == "不足" else c_neutral)
        if has_students:
            t3_trend, t3_class = "已编排", c_success
        elif has_rooms:
            t3_trend, t3_class = "已设置", c_warning
        else:
            t3_trend, t3_class = "未设置", c_neutral
        if wf_printing == "current":
            t4_trend, t4_class = "准备就绪", c_success
        else:
            t4_trend, t4_class = "--", c_neutral

        return {
            "stats": [
                {"label": "考试科目", "value": str(subject_count), "icon": "Notebook", "bgClass": "bg-sky-50", "textClass": "text-sky-600", "trend": t1_trend, "trendClass": t1_class},
                {"label": "监考教师", "value": str(teacher_count), "icon": "User", "bgClass": "bg-emerald-50", "textClass": "text-emerald-600", "trend": t2_trend, "trendClass": t2_class},
                {"label": "考场编排", "value": str(student_count), "icon": "School", "bgClass": "bg-indigo-50", "textClass": "text-indigo-600", "trend": t3_trend, "trendClass": t3_class},
                {"label": "资料打印", "value": "进行中" if wf_printing == "current" else "未开始", "icon": "Printer", "bgClass": "bg-rose-50", "textClass": "text-rose-600", "trend": t4_trend, "trendClass": t4_class},
            ],
            "workflow": [
                {"title": "科目设置", "desc": "导入考试科目、时间及时长，自动检测冲突。", "status": wf_subjects, "path": "/subjects"},
                {"title": "监考编排", "desc": "分配监考教师，支持多轮自动均衡算法。", "status": wf_proctoring, "path": "/proctoring"},
                {"title": "考场编排", "desc": "可视化分配考场座位，支持随机打乱。", "status": wf_rooms, "path": "/rooms"},
                {"title": "资料打印", "desc": "一键生成准考证、台角纸及考场门贴。", "status": wf_printing, "path": "/printing"},
            ],
        }
