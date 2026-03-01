def check_desk_data_sort(data_list):
    """校验数据是否按考场号、座位号排序"""
    if not data_list:
        return True, "无数据"

    last_room = -1
    last_seat = -1

    for i, item in enumerate(data_list):
        try:
            room_str = item.get("考场号", "0")
            seat_str = item.get("座位号", "0")

            room = int(room_str) if str(room_str).isdigit() else room_str
            seat = int(seat_str) if str(seat_str).isdigit() else seat_str
        except (ValueError, TypeError, AttributeError):
            continue

        if isinstance(room, int) and isinstance(last_room, int):
            if room < last_room:
                return False, f"第 {i+1} 行考场号乱序 ({room} < {last_room})"
        elif str(room) < str(last_room):
            pass

        if room == last_room:
            if isinstance(seat, int) and isinstance(last_seat, int):
                if seat < last_seat:
                    return False, f"第 {i+1} 行座位号乱序 (考场 {room}: {seat} < {last_seat})"

        last_room = room
        last_seat = seat

    return True, "数据顺序校验通过"

