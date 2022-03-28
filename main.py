import requests
import os
import json
import Token


class VkAgent:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, owner_id):
        self.params = {'access_token': token, 'v': '5.131', 'owner_id': owner_id}

    @staticmethod
    def __folder_creation(base_path, path):
        """
        Создание вложенной папки для директории base_path
        """
        file_path = os.path.join(base_path, path)
        if not os.path.isdir(file_path):
            os.mkdir(file_path)
        return file_path

    @staticmethod
    def __path_normalizer(name_path):
        """Удаление и замена запрещенных символов в имени папки"""
        symbol_no = rf"""*:'"%!@?$/\\|&<>+"""
        name = '_'.join(name_path.split()).strip(symbol_no)
        for s in symbol_no:
            if s in name:
                name = name.replace(s, '_')
        return name

    def files_downloader(self, file_dir: str):
        """
        Загрузка фотографий на локальный диск ПК
        file_dir - директория для загрузки файлов в текущей директории
        Вложенные папки создаются по именам альбомов
        """
        file_path_start = self.__folder_creation(os.getcwd(), file_dir)
        dict_foto_info = {}
        for title, value in self.photos_info.items():
            title = self.__path_normalizer(title)
            file_path = self.__folder_creation(file_path_start, title)
            print(f"Загружаем файлы в директорию >>> {file_path}:")
            list_value = []

            for info in value:
                file_name = os.path.join(file_path, info['file_name'])
                response = requests.get(info['url'])
                print(f"'{info['file_name']}' ")
                with open(file_name, 'wb') as f:
                    f.write(response.content)

                list_value.append({
                    'file_name': info['file_name'],
                    'size': info['size']
                })

            dict_foto_info[title] = list_value

        # Создание и загрузка итогового json-файла в директорию file_dir
        file_name_json = os.path.join(file_path_start, f"{file_dir}.json")
        print(f"Загружаем файл '{file_dir}.json' в >>> {file_path_start}")
        with open(file_name_json, 'w', encoding="utf-8") as f:
            json.dump(dict_foto_info, f, indent=2, ensure_ascii=False)
        print("=" * 50)

    @property
    def albums_id(self):
        """
        возвращает список словарей, содержащих название и id
        альбомы пользователя
        """
        albums_id = []
        photos_getalbums_url = self.url + 'photos.getAlbums'
        photos_getalbums_params = {'need_system': '1'}
        response = requests.get(photos_getalbums_url, params={**self.params, **photos_getalbums_params}).json()

        for item in response['response']['items']:
            albums_id.append({
                'title': item['title'],
                'id': item['id']
            })

        return albums_id

    @property
    def photos_info(self):
        """
        Создает список словарей self.photos_info с информацией для загружаемых файлов фотографий
        для альбомов из self.albums_id
        Метод ВК: photos.get:

        """
        total_photos_info = {}
        photos_get_url = self.url + 'photos.get'
        for album_id in self.albums_id:
            photos_info = []
            file_names_count = {}
            photos_get_params = {'album_id': album_id['id'], 'extended': 1}
            response = requests.get(photos_get_url, params={**self.params, **photos_get_params}).json()
            if 'response' in response:  # исключаем не доступные альбомы
                for item in response['response']['items']:
                    area = 0
                    for size in item['sizes']:
                        if size['height'] * size['width'] > area:
                            area = size['height'] * size['width']
                            image_resolution = f"{size['height']} * {size['width']}"
                            photo_url = size['url']

                    likes = item['likes']['count']
                    file_name = str(likes)

                    # Создаем словарь типа {количество лайков: количество одинаковых количеств лайков}
                    file_names_count[file_name] = file_names_count.get(file_name, 0) + 1

                    # Добавляем словарь в список photos_info
                    photos_info.append({
                        'file_name': file_name,
                        'date': item['date'],
                        'url': photo_url,
                        'size': image_resolution
                    })

                # Преобразовываем полученный ранее список photos_info:
                # добавляем расширение и при необходимости дату к имени файла
                # на основании данных словаря file_names_count
                # удаляем дату из словарей
                for photo in photos_info:
                    if file_names_count[photo['file_name']] > 1:
                        photo['file_name'] += f"_{photo['date']}.jpg"
                    else:
                        photo['file_name'] += ".jpg"
                    del photo['date']

                # создаем глобальный словарь с добавлением ключа по названию альбома
                total_photos_info[album_id['title']] = photos_info

        return total_photos_info


class YaUploader:
    URL = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self, token):
        self.token = token
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                        'Authorization': f'OAuth {token}'}

    def __create_folder(self, path):
        """Создание папки на диске."""
        requests.put(f'{YaUploader.URL}?path={path}', headers=self.headers)

    def __create_folder_path(self, path):
        """Создание вложенных папок для заданного пути path"""
        print('Cоздана папка на яндекс-диске: ', end='')
        for i, folder in enumerate(path.split('/')):
            if i == 0:
                directory = folder
            else:
                directory = f"{directory}/{folder}"
            self.__create_folder(directory)
            print(f'{folder}/', end='')
        print()

    def upload(self, file_dir):
        """
        Метод загружает папки с файлами из папки file_dir в яндекс диск
        Путь для копирования создается по типу file_dir/имя вложенной папки
        """

        base_path = os.getcwd()
        file_path_dir = os.path.join(base_path, file_dir)
        gen_directory = (d for d in os.listdir(file_path_dir) if '.json' not in d)
        for directory in gen_directory:
            ya_dir = f"{file_dir}/{directory}"
            self.__create_folder_path(ya_dir)
            file_path = os.path.join(base_path, file_dir, directory)
            file_list = os.listdir(file_path)
            print('Загрузка файлов в папку: ')
            for file in file_list:
                file_list_path = os.path.join(file_path, file)
                print(f"'{file}'")
                res = requests.get(f"{YaUploader.URL}/upload?path={ya_dir}/{file}&overwrite=true",
                                   headers=self.headers)
                link = res.json()['href']
                with open(file_list_path, 'rb') as f:
                    requests.put(link, files={'file': f})
            print()


if __name__ == '__main__':
    # FILE_DIR2 = "Sergryap"

    # FILE_DIR1 = "Michel"
    # michel = VkAgent(Token.TOKEN_VK, "552934290")
    # michel.files_downloader(FILE_DIR1)

    # FILE_DIR3 = "Oksana_Magura"
    # magur = VkAgent(Token.TOKEN_VK, '9681859')
    # magur.files_downloader(FILE_DIR3)
    # magur_load = YaUploader(Token.TOKEN_YA)
    # magur_load.upload(FILE_DIR3)

    FILE_DIR5 = "Lyudmila"
    # lyud = VkAgent(Token.TOKEN_VK, '208193971')
    # lyud.files_downloader(FILE_DIR5)
    lupload = YaUploader(Token.TOKEN_YA)
    lupload.upload(FILE_DIR5)
