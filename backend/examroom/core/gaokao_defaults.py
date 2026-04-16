"""高考模式默认配置。"""

from __future__ import annotations

from copy import deepcopy
from datetime import date


GAOKAO_SUBJECT_ORDER = ["语文", "数学", "物理历史", "英语", "化学", "地理", "政治", "生物"]
GAOKAO_ELECTIVE_SUBJECTS = ["化学", "地理", "政治", "生物"]

_GAOKAO_TIME_RANGES = {
    "语文": ("09:00", "11:30"),
    "数学": ("15:00", "17:00"),
    "物理历史": ("09:00", "10:15"),
    "英语": ("15:00", "17:00"),
    "化学": ("08:30", "09:45"),
    "地理": ("11:00", "12:15"),
    "政治": ("14:30", "15:45"),
    "生物": ("17:00", "18:15"),
}


def build_gaokao_time_defaults(today: str | None = None) -> dict:
    default_date = str(today or date.today().isoformat())
    exam_times = {
        subject: {
            "subjectName": subject,
            "date": default_date,
            "startTime": start_time,
            "endTime": end_time,
        }
        for subject, (start_time, end_time) in _GAOKAO_TIME_RANGES.items()
    }
    self_study_times = {
        subject: {
            "date": exam_times[subject]["date"],
            "startTime": exam_times[subject]["startTime"],
            "endTime": exam_times[subject]["endTime"],
        }
        for subject in GAOKAO_ELECTIVE_SUBJECTS
    }
    return {"examTimes": exam_times, "selfStudyTimes": self_study_times}


def normalize_gaokao_time_settings(settings: object) -> dict:
    defaults = build_gaokao_time_defaults()
    if not isinstance(settings, dict):
        return defaults

    raw_exam_times = settings.get("examTimes")
    raw_self_study_times = settings.get("selfStudyTimes")
    exam_times: dict[str, dict[str, str]] = {}
    self_study_times: dict[str, dict[str, str]] = {}

    raw_exam_times = raw_exam_times if isinstance(raw_exam_times, dict) else {}
    raw_self_study_times = raw_self_study_times if isinstance(raw_self_study_times, dict) else {}

    for subject in GAOKAO_SUBJECT_ORDER:
        raw_item = raw_exam_times.get(subject)
        default_item = defaults["examTimes"][subject]
        raw_item = raw_item if isinstance(raw_item, dict) else {}
        subject_name = (
            str(raw_item["subjectName"]).strip()
            if "subjectName" in raw_item
            else default_item["subjectName"]
        ) or default_item["subjectName"]
        exam_times[subject] = {
            "subjectName": subject_name,
            "date": str(raw_item["date"]).strip() if "date" in raw_item else default_item["date"],
            "startTime": str(raw_item["startTime"]).strip() if "startTime" in raw_item else default_item["startTime"],
            "endTime": str(raw_item["endTime"]).strip() if "endTime" in raw_item else default_item["endTime"],
        }

    for subject in GAOKAO_ELECTIVE_SUBJECTS:
        raw_item = raw_self_study_times.get(subject)
        default_item = defaults["selfStudyTimes"][subject]
        raw_item = raw_item if isinstance(raw_item, dict) else {}
        self_study_times[subject] = {
            "date": str(raw_item["date"]).strip() if "date" in raw_item else default_item["date"],
            "startTime": str(raw_item["startTime"]).strip() if "startTime" in raw_item else default_item["startTime"],
            "endTime": str(raw_item["endTime"]).strip() if "endTime" in raw_item else default_item["endTime"],
        }

    return {"examTimes": exam_times, "selfStudyTimes": self_study_times}


def copy_gaokao_time_defaults() -> dict:
    return deepcopy(build_gaokao_time_defaults())


GAOKAO_TIME_DEFAULTS = build_gaokao_time_defaults()
