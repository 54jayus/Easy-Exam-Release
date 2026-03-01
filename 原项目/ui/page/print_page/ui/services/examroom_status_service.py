from ...core.adapters.examroom_adapter import check_examroom_data


def get_examroom_status(examroom_page):
    data = check_examroom_data(examroom_page)
    count = len(data) if data is not None else 0

    if data is not None:
        return f"已就绪，共 {count} 条数据", "green"

    return "未检测到编排数据，请先进行考场编排", "red"

