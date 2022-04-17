import os
import json


# К КУРСОВОЙ РАБОТЕ НЕ ОТНОСИТСЯ. ПРОСТО УВЛЕКСЯ.


# def structure_decor(func):
#     def wraper(path):
#         d = func(path)
#         return {os.path.split(path)[1]: d}#
#     return wraper


def get_structure(path_start):
    """
    Создание файла json со структурой каталогов и файлов
    """

    try:
        gen_path = (os.path.join(path_start, folder) for folder in os.listdir(path_start) if
                    os.path.isdir(os.path.join(path_start, folder)))
        file_name = (file for file in os.listdir(path_start) if os.path.isfile(os.path.join(path_start, file)))
    except PermissionError:
        gen_path = []
        file_name = []

    struct = {}
    for path in gen_path:
        folder = os.path.split(path)[1]
        struct[folder] = get_structure(path)
        print(f'{path} >>>')
    struct['*files'] = tuple(file_name)

    return struct


def structure(path):
    folder = os.path.split(path)[1]
    d = get_structure(path)
    return {folder: d}


def load_json(data_dict):
    file_name = os.path.join(os.getcwd(), f"{[d for d in data][0]}.json")
    with open(file_name, 'w', encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    data = structure("VK_ads")
    # data = structure("C:\\")
    load_json(data)
