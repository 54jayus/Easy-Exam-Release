from ...core.utils.data_loader import DataLoader
from ...core.validators.desk_label_validator import check_desk_data_sort


def load_excel_with_mapping(file_path, mapping_provider):
    headers = DataLoader.get_headers(file_path)
    if not headers:
        raise Exception("文件为空或无法读取表头")

    mapping = mapping_provider(headers)
    if not mapping:
        return None, None

    data_list = DataLoader.load_data(file_path, mapping)
    return mapping, data_list


def load_desk_import(file_path, mapping_provider):
    mapping, data_list = load_excel_with_mapping(file_path, mapping_provider)
    if not mapping:
        return None, None, None

    is_sorted, msg = check_desk_data_sort(data_list)
    return mapping, data_list, (is_sorted, msg)

