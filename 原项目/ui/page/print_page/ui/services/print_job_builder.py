import os

from ...core.adapters.examroom_adapter import (
    check_examroom_data,
    load_examroom_data_for_corner,
    load_examroom_data_for_ticket,
    load_examroom_data_for_student_info,
)
from ...core.config import AdmissionTicketConfig, CornerPaperConfig, DeskLabelConfig, StudentInfoTableConfig
from ...core.utils.data_loader import DataLoader
from ...core.validators.desk_label_validator import check_desk_data_sort


class BuildError(Exception):
    def __init__(self, title, message, level="warning"):
        super().__init__(message)
        self.title = title
        self.message = message
        self.level = level


class BuildCancelled(Exception):
    pass


def build_config_for_current_tab(window, mapping_provider=None, confirm=None, log=None):
    idx = window.tabs.currentIndex()
    if idx == 0:
        return _build_desk_config(window, confirm, log)
    if idx == 1:
        return _build_corner_config(window, mapping_provider, log)
    if idx == 2:
        return _build_ticket_config(window, mapping_provider, log)
    if idx == 3:
        return _build_student_info_config(window, mapping_provider, log)
    return None


def _build_corner_config(window, mapping_provider, log):
    path = window.pathEdit.text()
    if not path:
        raise BuildError("错误", "请选择保存路径", level="warning")

    export_xlsx = bool(getattr(window, "checkExportXLSX", None) and window.checkExportXLSX.isChecked())
    export_pdf = bool(window.checkExportPDF.isChecked())
    if not export_xlsx and not export_pdf:
        raise BuildError("错误", "请至少选择一种输出格式（xlsx 或 pdf）", level="warning")

    subjects = window.subjects
    count = 0
    data_list = None

    if window.radioEmpty.isChecked():
        count = window.spinCount1.value()
    elif window.radioImport.isChecked():
        import_path = window.importFileEdit.text()
        if not import_path or not os.path.exists(import_path):
            raise BuildError("错误", "请选择有效的数据源文件", level="warning")

        headers = DataLoader.get_headers(import_path)
        if not headers:
            if log:
                log("导入失败: 文件为空或无法读取表头")
            raise BuildError("导入失败", "文件为空或无法读取表头", level="critical")

        if not mapping_provider:
            raise BuildError("导入失败", "缺少列映射提供器", level="critical")

        mapping = mapping_provider(headers)
        if not mapping:
            raise BuildCancelled()

        try:
            if log:
                log("正在读取并校验数据...")
            data_list = DataLoader.load_data(import_path, mapping)
            if log:
                log(f"成功读取 {len(data_list)} 条数据")
            count = len(data_list)
        except Exception as e:
            if log:
                log(f"导入失败: {str(e)}")
            raise BuildError("导入失败", str(e), level="critical")

    elif window.radioExamroom.isChecked():
        df = check_examroom_data(window.examroom_page)
        data_list = load_examroom_data_for_corner(df)
        if not data_list:
            raise BuildError("错误", "未检测到有效的考场编排数据，请先在“考场编排”中完成编排。", level="warning")
        count = len(data_list)
        if log:
            log(f"成功从考场编排加载 {count} 条数据")

    return CornerPaperConfig(
        output_path=path,
        subjects=subjects,
        num_templates=count,
        student_data_list=data_list,
        title=window.titleEdit.text(),
        export_xlsx=export_xlsx,
        export_pdf=export_pdf,
    )


def _build_desk_config(window, confirm, log):
    path = window.deskPathEdit.text()
    if not path:
        raise BuildError("错误", "请选择保存路径", level="warning")

    export_xlsx = bool(getattr(window, "deskCheckExportXLSX", None) and window.deskCheckExportXLSX.isChecked())
    export_pdf = bool(window.deskCheckExportPDF.isChecked())
    if not export_xlsx and not export_pdf:
        raise BuildError("错误", "请至少选择一种输出格式（xlsx 或 pdf）", level="warning")

    count = 0
    data_list = None

    if window.deskRadioEmpty.isChecked():
        count = window.deskSpinCount.value()
    elif window.deskRadioImport.isChecked():
        import_path = window.deskImportFileEdit.text()
        if not import_path or not os.path.exists(import_path):
            raise BuildError("错误", "请选择有效的数据源文件", level="warning")

        try:
            if log:
                log("正在读取数据...")

            if hasattr(window, "desk_mapping") and window.desk_mapping:
                mapping = window.desk_mapping
            else:
                headers = DataLoader.get_headers(import_path)
                if not headers:
                    raise Exception("文件为空或无法读取表头")
                mapping = {h: h for h in headers}

            data_list = DataLoader.load_data(import_path, mapping)

            is_sorted, msg = check_desk_data_sort(data_list)
            if not is_sorted:
                if not confirm:
                    raise BuildCancelled()
                ok = confirm("warning", "排序警告", f"数据存在乱序：{msg}\n是否继续？")
                if not ok:
                    raise BuildCancelled()

            count = len(data_list)
        except BuildCancelled:
            raise
        except Exception as e:
            raise BuildError("导入失败", str(e), level="critical")

    elif window.deskRadioExamroom.isChecked():
        df = check_examroom_data(window.examroom_page)
        data_list = load_examroom_data_for_corner(df)
        if not data_list:
            raise BuildError("错误", "未检测到有效的考场编排数据", level="warning")
        count = len(data_list)

    if data_list:
        capacity = window.desk_layout_capacity
        room_counts = {}
        for item in data_list:
            room = item.get("考场号", "Unknown")
            room_counts[room] = room_counts.get(room, 0) + 1

        overflow_rooms = []
        for room, c in room_counts.items():
            if c > capacity:
                overflow_rooms.append(f"考场号 {room}: {c}人 (上限{capacity})")

        if overflow_rooms:
            msg = "以下考场人数超过当前布局容量，将自动分两页打印：\n\n" + "\n".join(overflow_rooms[:10])
            if len(overflow_rooms) > 10:
                msg += "\n..."
            msg += "\n\n是否继续生成？"

            if not confirm:
                raise BuildCancelled()
            ok = confirm("question", "人数超限提示", msg)
            if not ok:
                raise BuildCancelled()

    return DeskLabelConfig(
        output_path=path,
        total_count=count,
        layout_rows=window.desk_layout_rows,
        layout_cols=window.desk_layout_cols,
        layout_name=window.desk_layout_name,
        layout_pattern=getattr(window, "desk_layout_pattern", "S型横排"),
        start_pos=getattr(window, "desk_layout_start_pos", "left"),
        custom_col_counts=getattr(window, "desk_layout_custom_counts", None),
        student_data_list=data_list,
        export_xlsx=export_xlsx,
        export_pdf=export_pdf,
    )


def _build_ticket_config(window, mapping_provider, log):
    path = window.ticketPathEdit.text()
    if not path:
        raise BuildError("错误", "请选择保存路径", level="warning")

    export_xlsx = bool(getattr(window, "ticketCheckExportXLSX", None) and window.ticketCheckExportXLSX.isChecked())
    export_pdf = bool(window.ticketCheckExportPDF.isChecked())
    if not export_xlsx and not export_pdf:
        raise BuildError("错误", "请至少选择一种输出格式（xlsx 或 pdf）", level="warning")

    subjects = window.subjects
    count = 0
    data_list = None

    if window.ticketRadioEmpty.isChecked():
        count = window.ticketSpinCount.value()
    elif window.ticketRadioImport.isChecked():
        import_path = window.ticketImportFileEdit.text()
        if not import_path or not os.path.exists(import_path):
            raise BuildError("错误", "请选择有效的数据源文件", level="warning")

        try:
            headers = DataLoader.get_headers(import_path)
            if not headers:
                raise Exception("文件为空或无法读取表头")

            if not mapping_provider:
                raise Exception("缺少列映射提供器")

            mapping = mapping_provider(headers)
            if not mapping:
                raise BuildCancelled()

            if log:
                log("正在读取并校验数据...")
            data_list = DataLoader.load_data(import_path, mapping)
            if log:
                log(f"成功读取 {len(data_list)} 条数据")
            count = len(data_list)

        except BuildCancelled:
            raise
        except Exception as e:
            if log:
                log(f"导入失败: {str(e)}")
            raise BuildError("导入失败", str(e), level="critical")

    elif window.ticketRadioExamroom.isChecked():
        df = check_examroom_data(window.examroom_page)
        data_list = load_examroom_data_for_ticket(df)
        if not data_list:
            raise BuildError("错误", "未检测到有效的考场编排数据，请先在“考场编排”中完成编排。", level="warning")
        count = len(data_list)
        if log:
            log(f"成功从考场编排加载 {count} 条数据")

    return AdmissionTicketConfig(
        output_path=path,
        subjects=subjects,
        subject_times=window.subject_times,
        num_templates=count,
        student_data_list=data_list,
        title=window.ticketTitleEdit.text(),
        export_xlsx=export_xlsx,
        export_pdf=export_pdf,
    )


def _build_student_info_config(window, mapping_provider, log):
    path = window.studentInfoPathEdit.text()
    if not path:
        raise BuildError("错误", "请选择保存路径", level="warning")

    export_xlsx = bool(getattr(window, "studentInfoCheckExportXLSX", None) and window.studentInfoCheckExportXLSX.isChecked())
    export_pdf = bool(getattr(window, "studentInfoCheckExportPDF", None) and window.studentInfoCheckExportPDF.isChecked())
    if not export_xlsx and not export_pdf:
        raise BuildError("错误", "请至少勾选一种输出格式（xlsx 或 pdf）", level="warning")

    data_list = None
    include_subject_fields = False

    if window.studentInfoRadioEmpty.isChecked():
        data_list = []
    elif window.studentInfoRadioImport.isChecked():
        import_path = window.studentInfoImportFileEdit.text()
        if not import_path or not os.path.exists(import_path):
            raise BuildError("错误", "请选择有效的数据源文件", level="warning")

        cached_data = getattr(window, "studentInfo_cached_data", None)
        cached_include = bool(getattr(window, "studentInfo_include_subject_fields", False))
        if cached_data is not None:
            data_list = cached_data
            include_subject_fields = cached_include
        else:
            raise BuildError("错误", "请先选择导入文件并完成列映射", level="warning")

    elif window.studentInfoRadioExamroom.isChecked():
        df = check_examroom_data(window.examroom_page)
        include_subject_fields = False
        if df is not None and hasattr(window.examroom_page, "mode_combo"):
            include_subject_fields = window.examroom_page.mode_combo.currentData() == "subject_mode"
            include_subject_fields = include_subject_fields and all(c in df.columns for c in ["首选", "选科1", "选科2"])
        data_list = load_examroom_data_for_student_info(df, include_subject_fields=include_subject_fields)
        if not data_list:
            raise BuildError("错误", "未检测到有效的考场编排数据，请先在“考场编排”中完成编排。", level="warning")
        if log:
            log(f"成功从考场编排加载 {len(data_list)} 条数据")

    template_path = os.path.join(os.path.abspath("."), "ui", "page", "print_page", "assets", "templates", "考生信息表（班级）.xlsx")
    group_mode = "class"
    if hasattr(window, "studentInfoPreviewTabs") and window.studentInfoPreviewTabs.currentIndex() == 1:
        group_mode = "examroom"

    title = window.studentInfoTitleEdit.text()
    titles = getattr(window, "_student_info_titles", None)
    if isinstance(titles, dict):
        titles[group_mode] = title

    return StudentInfoTableConfig(
        output_path=path,
        title=title,
        student_data_list=data_list,
        export_xlsx=export_xlsx,
        export_pdf=export_pdf,
        template_path=template_path,
        include_subject_fields=include_subject_fields,
        group_mode=group_mode,
    )
