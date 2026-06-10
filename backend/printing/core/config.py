from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BaseConfig:
    """基础配置类"""
    output_path: str
    export_xlsx: bool = True
    export_pdf: bool = False

@dataclass
class CornerPaperConfig(BaseConfig):
    """台角纸生成配置"""
    subjects: List[str] = field(default_factory=lambda: [''] * 8)
    title: str = "高二期中考试台角纸"
    num_templates: int = 0
    student_data_list: Optional[List[dict]] = None

@dataclass
class AdmissionTicketConfig(BaseConfig):
    """准考证生成配置"""
    subjects: List[str] = field(default_factory=lambda: [''] * 8)
    subject_times: List[str] = field(default_factory=lambda: [''] * 8)
    title: str = "高三市调研测试准考证"
    num_templates: int = 0
    student_data_list: Optional[List[dict]] = None

@dataclass
class DeskLabelConfig(BaseConfig):
    """桌角纸生成配置"""
    total_count: int = 0
    layout_rows: int = 7
    layout_cols: int = 6
    layout_name: str = "6行*7列 (42人)"
    layout_pattern: str = "S型横排"
    start_pos: str = "left" # "left" or "right"
    custom_col_counts: Optional[List[int]] = None
    student_data_list: Optional[List[dict]] = None
    seat_layout: Optional[dict] = None


@dataclass
class RollCallConfig(BaseConfig):
    """考场点名表生成配置"""
    exam_name: str = "xxx考试点名表"
    school_name: str = "xxx学校"
    template_mode: str = "full"
    orientation: str = "auto"
    mirror_view: bool = False
    show_exam_no: bool = True
    show_class: bool = False
    show_checkbox: bool = True
    notes_title: str = "备注栏："
    instructions: str = "1.学生缺考时，请在对应方框内打勾。\n2.学生出现异常行为，请在备注栏记录相关情况。\n3.请将本表张贴于答卷袋正面。"
    groups: Optional[List[dict]] = None


@dataclass
class StudentInfoTableConfig(BaseConfig):
    """考生信息表生成配置"""
    title: str = "座位安排-班级"
    student_data_list: Optional[List[dict]] = None
    template_path: Optional[str] = None
    include_subject_fields: bool = False
    group_mode: str = "class"

@dataclass
class ExamBagLabelConfig(BaseConfig):
    """试卷袋标签生成配置"""
    student_data_list: Optional[List[dict]] = None
    school_name: str = "xxx学校"
    layout_rows: int = 3
    layout_cols: int = 3
