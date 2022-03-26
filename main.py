import requests
import os
import json


class VkGet:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, owner_id):
        self.token = token
        self.params = {'access_token': token, 'v': '5.131'}
        self.id = owner_id

    @staticmethod
    def __file_path(directory):
        """
        Создание пути для сохранения файлов на ПК
        """
        base_path = os.getcwd()
        file_path = os.path.join(base_path, directory)
        if not os.path.isdir(file_path):
            os.mkdir(file_path)
        return file_path

    def files_downloader(self, file_dir: str):
        """
        Загрузка файлов на локальный диск ПК
        file_dir - директория для загрузки файлов в текущей директории
        """
        file_path = self.__file_path(file_dir)

        # Загрузка фотографий
        print(f"Загружаем файлы в директорию {file_path}:")
        for info in self.photos_info:
            file_name = os.path.join(file_path, info['file_name'])
            response = requests.get(info['url'])
            print(f"'{info['file_name']}' ", end='')
            with open(file_name, 'wb') as f:
                f.write(response.content)

        # Создание и загрузка json-файла в директорию file_dir
        file_name_json = os.path.join(file_path, f"{file_dir}.json")
        print(f"'{file_dir}.json' ", end='')
        with open(file_name_json, 'w', encoding="utf-8") as f:
            json.dump([{
                'file_name': data['file_name'],
                'size': data['size']
            } for data in self.photos_info], f, indent=3)
        print()

    @property
    def photos_info(self):
        """
        Создает список словарей self.photos_info с информацией для загружаемых файлов фотографий:

        """
        photos_info = []
        file_names_count = {}
        photos_get_url = self.url + 'photos.get'
        photos_get_params = {'owner_id': self.id, 'album_id': 'profile', 'extended': 1}
        response = requests.get(photos_get_url, params={**self.params, **photos_get_params}).json()

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

            photos_info.append({
                'file_name': file_name,
                'date': item['date'],
                'url': photo_url,
                'size': image_resolution
            })

        # Преобразовываем полученный ранее список photos_info:
        # добавляем расширение и при необходимости дату к имени файла
        # удаляем дату из словарей
        for photo in photos_info:
            if file_names_count[photo['file_name']] > 1:
                photo['file_name'] += f"_{photo['date']}.jpg"
            else:
                photo['file_name'] += ".jpg"
            del photo['date']

        return photos_info


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
        print('Cоздана папка на ya-диске: ', end='')
        for i, folder in enumerate(path.split('/')):
            if i == 0:
                directory = folder
            else:
                directory = f"{directory}/{folder}"
            self.__create_folder(directory)
            print(f'{folder}/', end='')
        print()

    def upload(self, file_dir, ya_dir):
        """Метод загружает файлы из папки file_path в папку ya_dir на яндекс дискe"""
        self.__create_folder_path(ya_dir)
        base_path = os.getcwd()
        file_path = os.path.join(base_path, file_dir)
        file_list = os.listdir(file_path)
        print('Загрузка файлов на ya-диск: ')
        for file in file_list:
            file_list_path = os.path.join(file_path, file)
            print(f"'{file}' ", end='')
            res = requests.get(f"{YaUploader.URL}/upload?path={ya_dir}/{file}&overwrite=true",
                               headers=self.headers)
            link = res.json()['href']
            with open(file_list_path, 'rb') as f:
                requests.put(link, files={'file': f})
        print()


if __name__ == '__main__':
    TOKEN_VK = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
    TOKEN_YA = ""

    FILE_DIR1 = "loaded_files1"
    FILE_DIR2 = "sergryap"
    FILE_DIR3 = "oksana_magura"

    YA_DIR1 = 'Michail/test2/test3'  # Дирректория для загрузки на я-диск
    YA_DIR2 = 'Serg/test2/test3'
    YA_DIR3 = 'Serg/Magura'

    album1 = VkGet(TOKEN_VK, '552934290')
    album2 = VkGet(TOKEN_VK, '7352307')
    album3 = VkGet(TOKEN_VK, '9681859')
    album1.files_downloader(FILE_DIR1)
    album2.files_downloader(FILE_DIR2)
    album3.files_downloader(FILE_DIR3)

    uploader = YaUploader(TOKEN_YA)
    uploader.upload(FILE_DIR1, YA_DIR1)
    uploader.upload(FILE_DIR2, YA_DIR2)
    uploader.upload(FILE_DIR3, YA_DIR3)
