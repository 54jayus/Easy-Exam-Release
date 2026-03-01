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


@dataclass
class StudentInfoTableConfig(BaseConfig):
    """考生信息表生成配置"""
    title: str = "座位安排-班级"
    student_data_list: Optional[List[dict]] = None
    template_path: Optional[str] = None
    include_subject_fields: bool = False
    group_mode: str = "class"
