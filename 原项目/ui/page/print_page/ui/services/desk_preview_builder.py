from ...core.adapters.examroom_adapter import check_examroom_data, load_examroom_data_for_corner


def build_desk_preview_payload(mode, desk_cached_data, examroom_page):
    data_list = []
    if mode == 1:
        if desk_cached_data:
            data_list = desk_cached_data
    elif mode == 2:
        df = check_examroom_data(examroom_page)
        data_list = load_examroom_data_for_corner(df) or []

    room_data_list = []
    student_info_map = {}

    if data_list:
        first_room = _find_first_room(data_list)
        if first_room:
            room_data_list = [d for d in data_list if str(d.get("考场号", "")).strip() == first_room]
            student_info_map = _build_student_info_map(room_data_list)

    return room_data_list, student_info_map


def _find_first_room(data_list):
    for d in data_list:
        r = d.get("考场号")
        if r is not None and str(r).strip() != "":
            return str(r).strip()
    return None


def _build_student_info_map(room_data_list):
    student_info_map = {}
    for d in room_data_list:
        try:
            seat_val = d.get("座位号")
            if seat_val is None:
                continue
            seat = int(float(str(seat_val)))
            name = str(d.get("考生姓名", ""))
            no = str(d.get("考生考号", ""))
            student_info_map[seat] = f"{name}\n{no}"
        except:
            pass
    return student_info_map

