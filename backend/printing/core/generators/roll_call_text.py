def format_class_name(value) -> str:
    class_name = str(value or "").strip()
    return f"班级：{class_name}" if class_name else ""
