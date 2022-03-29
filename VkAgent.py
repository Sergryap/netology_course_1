import requests
import os
import json
import Token
import Ya
import Agent


class VkAgent(Agent.Social):
    url = 'https://api.vk.com/method/'

    def __init__(self, token, owner_id):
        self.params = {'access_token': token, 'v': '5.131', 'owner_id': owner_id}

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
                'title': self._path_normalizer(item['title']),
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


if __name__ == '__main__':
    FILE_DIR1 = "Michel"
    PATH_DIR1 = os.path.join(os.getcwd(), FILE_DIR1)
    # michel = VkAgent(Token.TOKEN_VK, "552934290")
    # michel.files_downloader(FILE_DIR1)
    michel_load = Ya.YaUploader(Token.TOKEN_YA)
    michel_load.upload(PATH_DIR1)

    # FILE_DIR3 = "Oksana_Magura"
    # PATH_DIR3 = os.path.join(os.getcwd(), FILE_DIR3)
    # magur = VkAgent(Token.TOKEN_VK, '9681859')
    # magur.files_downloader(FILE_DIR3)
    # magur_load = Ya.YaUploader(Token.TOKEN_YA)
    # magur_load.upload(PATH_DIR3)

    # FILE_DIR5 = "Lyudmila"
    # PATH_DIR5 = os.path.join(os.getcwd(), FILE_DIR5)
    # lyud = VkAgent(Token.TOKEN_VK, '208193971')
    # lyud.files_downloader(FILE_DIR5)
    # lupload = Ya.YaUploader(Token.TOKEN_YA)
    # lupload.upload(PATH_DIR5)

    # path_ok = os.path.join(os.getcwd(), 'Test01')
    # ok1 = Ya.YaUploader(Token.TOKEN_YA)
    # ok1.upload_recursive(path_ok)