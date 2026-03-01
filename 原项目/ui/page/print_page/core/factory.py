from enum import Enum, auto
from .config import BaseConfig, CornerPaperConfig, DeskLabelConfig, AdmissionTicketConfig, StudentInfoTableConfig
from .generators.excel.corner_paper import CornerPaperGenerator
from .generators.excel.desk_label import DeskLabelGenerator
from .generators.excel.admission_ticket import AdmissionTicketGenerator
from .generators.excel.student_info_table import StudentInfoTableGenerator
from .generators.pdf.desk_label_pdf import DeskLabelPDFGenerator
from .generators.pdf.pdf_generators import CornerPaperPDFGenerator, AdmissionTicketPDFGenerator
from .generators.pdf.student_info_pdf import StudentInfoTablePDFGenerator

class GeneratorType(Enum):
    CORNER_PAPER = auto()
    DESK_LABEL = auto()
    ADMISSION_TICKET = auto()

class GeneratorFactory:
    """生成器工厂类"""
    
    @staticmethod
    def create_generator(config: BaseConfig):
        """
        根据配置类型创建对应的生成器实例
        """
        export_pdf = bool(getattr(config, "export_pdf", False))
        export_xlsx = bool(getattr(config, "export_xlsx", True))
        if isinstance(config, CornerPaperConfig):
            if export_pdf and not export_xlsx:
                return CornerPaperPDFGenerator(config)
            return CornerPaperGenerator(config)
        elif isinstance(config, DeskLabelConfig):
            if export_pdf and not export_xlsx:
                return DeskLabelPDFGenerator(config)
            return DeskLabelGenerator(config)
        elif isinstance(config, AdmissionTicketConfig):
            if export_pdf and not export_xlsx:
                return AdmissionTicketPDFGenerator(config)
            return AdmissionTicketGenerator(config)
        elif isinstance(config, StudentInfoTableConfig):
            if export_pdf and not export_xlsx:
                return StudentInfoTablePDFGenerator(config)
            return StudentInfoTableGenerator(config)
        else:
            raise ValueError(f"Unsupported config type: {type(config)}")
