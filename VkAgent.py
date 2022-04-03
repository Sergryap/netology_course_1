import requests
import os
import json
import Token
import Ya
import Agent
import time
import random as rnd
from pprint import pprint


class VkAgent(Agent.Social):
    url = 'https://api.vk.com/method/'

    def __init__(self, token, owner_id):
        self.params = {'access_token': token, 'v': '5.131', 'owner_id': owner_id}

    def albums_id(self):
        """
        Cоздает список словарей, содержащих название и id
        альбомы пользователя
        """
        albums_id = []
        photos_getalbums_url = self.url + 'photos.getAlbums'
        photos_getalbums_params = {'need_system': '1'}
        response = requests.get(photos_getalbums_url, params={**self.params, **photos_getalbums_params}).json()

        for item in response['response']['items']:
            albums_id.append({
                'title': self._path_normalizer(item['title']),
                'id': item['id']
            })

        return albums_id

    @staticmethod
    def __get_items(item: dict):
        """
        Находим фото с наибольшим разрешением.
        Если данных по размерам нет, то принимаем по size['type']
        """
        area = 0
        for size in item['sizes']:
            if size['height'] and size['width'] and size['height'] > 0 and size['width'] > 0:
                if size['height'] * size['width'] > area:
                    area = size['height'] * size['width']
                    image_res = f"{size['height']} * {size['width']}"
                    photo_url = size['url']
            else:
                flag = False
                for i in 'wzyx':
                    for size1 in item['sizes']:
                        if size1['type'] == i:
                            image_res = "нет данных"
                            photo_url = size1['url']
                            flag = True
                            break
                    if flag:
                        break
                break
        return image_res, photo_url

    def photos_info(self):
        """
        Создает словарь типа:
        {'название альбома':
        [{'file_name': file_name, 'url': photo_url, 'size': image_resolution}...]
        Метод ВК: photos.get:

        """
        total_photos_info = {}
        photos_get_url = self.url + 'photos.get'
        for album_id in self.albums_id():
            print(f"Получаем данные из альбома: {album_id['title']}")
            time.sleep(rnd.randint(1, 3))
            photos_info = []
            file_names_count = {}
            photos_get_params = {'album_id': album_id['id'], 'extended': 1}
            response = requests.get(photos_get_url, params={**self.params, **photos_get_params}).json()
            if 'response' in response:  # исключаем не доступные альбомы
                for item in response['response']['items']:
                    image_resolution = self.__get_items(item)[0]
                    photo_url = self.__get_items(item)[1]
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


if __name__ == '__main__':
    # FILE_DIR1 = "Michel"
    # PATH_DIR1 = os.path.join(os.getcwd(), FILE_DIR1)
    # michel = VkAgent(Token.TOKEN_VK, "552934290")
    # pprint(michel.photos_info())
    # michel.files_downloader(FILE_DIR1)
    # michel_load = Ya.YaUploader(Token.TOKEN_YA)
    # michel_load.upload(PATH_DIR1)

    # FILE_DIR3 = "Oksana_Magura"
    # PATH_DIR3 = os.path.join(os.getcwd(), FILE_DIR3)
    # magur = VkAgent(Token.TOKEN_VK, '9681859')
    # pprint(magur.photos_info())
    # magur.files_downloader(FILE_DIR3)
    # magur_load = Ya.YaUploader(Token.TOKEN_YA)
    # magur_load.upload(PATH_DIR3)

    FILE_DIR5 = "Lyudmila"
    PATH_DIR5 = os.path.join(os.getcwd(), FILE_DIR5)
    lyud = VkAgent(Token.TOKEN_VK, '208193971')
    # pprint(lyud.photos_info())
    # lyud.files_downloader(FILE_DIR5)
    # lupload = Ya.YaUploader(Token.TOKEN_YA)
    # lupload.upload(PATH_DIR5)

    # FILE_DIR6 = "Nataly_Ryapina"
    # PATH_DIR6 = os.path.join(os.getcwd(), FILE_DIR6)
    # nataly = VkAgent(Token.TOKEN_VK, "3627604")
    # pprint(nataly.photos_info())
    # nataly.files_downloader(FILE_DIR6)
    # michel_load = Ya.YaUploader(Token.TOKEN_YA)
    # michel_load.upload(PATH_DIR1)

    # path_ok = os.path.join(os.getcwd(), 'Test01')
    # ok1 = Ya.YaUploader(Token.TOKEN_YA)
    # ok1.upload_recursive(path_ok)
