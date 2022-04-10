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

    def __init__(self, folder_name, owner_id='7352307', token=Token.TOKEN_VK):
        self.params = {'access_token': token, 'v': '5.131', 'owner_id': owner_id}
        self.owner_id = owner_id
        self.folder_name = folder_name
        self.path_ads = self._folder_creation((self._folder_creation(os.getcwd(), 'VK_ads')), folder_name)

    @staticmethod
    def verify_group(value: dict):
        """
        Условие включения группы в базу
        """
        return ('обучение' not in value['name'].lower()
                and 'материалы' not in value['name'].lower()
                and 'материалов' not in value['name'].lower()
                and 'всё для' not in value['name'].lower()
                and 'все для' not in value['name'].lower()
                and 'бесплатно' not in value['name'].lower()
                and 'ресниц' in value['name'].lower()
                )

    def group_search(self, q: str, suffix='groups', verify=True):
        """
        Поиск групп по ключевой фразе
        :param q: ключевая фраза для поиска
        :param suffix: суффикс для создаваемого итогового файла
        :param verify: указывает на необходимость проверки по verify_group
        :return: словарь с ключами по id групп, значения словарь с названиями группы и числом участников
        """
        group_search = {}
        group_url = self.url + 'groups.search'
        for soc in ['group', 'page', 'event']:
            for offset in range(100):
                params_delta = {'q': q.lower(), 'type': soc, 'country_id': 1, 'city_id': 110, 'sort': 6,
                                'offset': offset}
                response = requests.get(group_url, params={**self.params, **params_delta}).json()
                for item in response['response']['items']:
                    print(item['id'])
                    if verify and self.verify_group(item):
                        group_search[item['id']] = {'screen_name': item['screen_name'], 'name': item['name']}
                    elif not verify:
                        group_search[item['id']] = {'screen_name': item['screen_name'], 'name': item['name']}
        # Добавляем количество участников по ключу count
        for group in group_search:
            print(f'+count: id{group}')
            group_search[group]['count'] = self.__get_offset(group)[1]

        group_result_json = os.path.join(self.path_ads, f"{os.path.split(self.path_ads)[1]}_{suffix}.json")
        with open(group_result_json, 'w', encoding="utf-8") as f:
            json.dump(group_search, f, indent=2, ensure_ascii=False)
        return group_search

    def __get_offset(self, group_id):
        """
        Определение количества шагов для анализа группы, числа участников
        :param group_id: идентификатор группы
        :return: количество шагов, количество участников
        """
        offset_url = self.url + 'groups.getMembers'
        params_delta = {'group_id': group_id, 'sort': 'id_desc', 'offset': 0, 'fields': 'last_seen'}
        response = requests.get(offset_url, params={**self.params, **params_delta}).json()
        if 'response' in response:  # проверка доступности
            count = response['response']['count']
        else:
            count = -1
        return count // 1000, count

    def __get_users(self, group_id, month):
        """
        Отбор id подписчиков группы в список
        :param group_id: id группы
        :param month: количество месяцев с последнего посещения
        return: список участников группы
        """
        offset = 0
        good_id_list = []
        max_offset = self.__get_offset(group_id)[0]
        print(f'max_offset={max_offset}')
        get_users_url = self.url + 'groups.getMembers'
        while offset <= max_offset:
            print(f'offset={offset}')
            params_delta = {'group_id': group_id, 'sort': 'id_desc', 'offset': offset, 'fields': 'last_seen'}
            response = requests.get(get_users_url, params={**self.params, **params_delta}).json()
            offset += 1
            for item in response['response']['items']:
                try:
                    if item['last_seen']['time'] >= round(time.time()) - round(month * 30.42 * 86400):
                        good_id_list.append(item['id'])
                except KeyError:
                    continue
        return good_id_list

    def get_users(self, count=3, month=6):
        """
        Создание списка id подписчиков групп из файла с id групп
        Подписчики состоят не менее чем в количестве count группах
        :param count: минимальное количество групп в которых состоит подписчик
        :param month: количество месяцев последней активности пользователя
        Результат записывается в файл, готовый к импорту в РК VK
        """
        group_search_json = os.path.join(self.path_ads, f"{os.path.split(self.path_ads)[1]}_groups.json")
        with open(group_search_json, encoding="utf-8") as f:
            group_list = json.load(f).keys()
        all_users = []
        for group in group_list:
            print(group)
            users = self.__get_users(group, month)
            all_users.extend(users)

        count_group = {}
        for user in all_users:
            count_group[user] = count_group.get(user, 0) + 1
        all_users = []
        for user, value in count_group.items():
            if value >= count:
                all_users.append(user)
        users_file = os.path.join(self.path_ads,
                                  f"{os.path.split(self.path_ads)[1]}_users_{count}_groups_{month}_month.txt")
        with open(users_file, 'w', encoding="utf-8") as f:
            for item in all_users:
                f.write(f'{item}\n')

    def get_user_groups(self, user_id):
        """
        Создает списк групп, в которые входит пользователь user_id
        :return: обозначенный список
        """
        user_groups_url = self.url + 'groups.get'
        params_delta = {'user_id': user_id, 'offset': 0}
        print(f'offset=0')
        response = requests.get(user_groups_url, params={**self.params, **params_delta}).json()
        if 'response' in response:
            offset = 1
            max_offset = response['response']['count'] // 1000
            user_groups = []
            user_groups.extend(response['response']['items'])
            while offset <= max_offset:
                print(f'offset={offset}')
                params_delta = {'user_id': user_id, 'offset': offset}
                response = requests.get(user_groups_url, params={**self.params, **params_delta}).json()
                user_groups.extend(response['response']['items'])
                offset += 1
            return user_groups

    def get_users_groups(self, file_user_list: str):
        """
        Создает словарь: {ключ - id пользователя,
        значение - список из групп, в которые входит пользователь
        :param file_user_list: файл со списком id пользователей в дирректрии self.path_ads
        :return: обозначенный выше словарь
        """
        users_groups = {}
        with open(os.path.join(self.path_ads, file_user_list), encoding="utf-8") as f:
            users_list = f.readlines()
        print('Получаем данные:')
        # time.sleep(0.1)
        count = 1
        count_end = len(users_list)
        for user in users_list:
            print(f'{count}/{count_end}: id{user.strip()}')
            users_groups[user.strip()] = self.get_user_groups(user.strip())
            if not users_groups[user.strip()]:
                del users_groups[user.strip()]
            count += 1

        path_users_analise = self._folder_creation(self.path_ads, 'users_analise')
        users_groups_json = os.path.join(path_users_analise,
                                         f"{file_user_list.split('.')[0]}.json")
        with open(users_groups_json, 'w', encoding="utf-8") as f:
            json.dump(users_groups, f, indent=2, ensure_ascii=False)
        return users_groups

    def friends_info(self):
        """Метод friends.get VK"""
        friends_info = {}
        friends_url = self.url + 'friends.get'
        friends_params = {'user_id': self.owner_id,
                          'fields': 'nickname,domain,sex,bdate,city,country,timezone,photo_200_orig'
                          }
        response = requests.get(friends_url, params={**self.params, **friends_params}).json()
        for item in response['response']['items']:
            city = country = 'Нет данных'
            if 'country' in item:
                country = item['country']['title']
            if 'city' in item:
                city = item['city']['title']
            friends_info[f"id{item['id']}"] = {
                'first_name': item['first_name'],
                'last_name': item['last_name'],
                'avatar_url': item['photo_200_orig'],
                'country': country,
                'city': city
            }

        return friends_info
        # return response

    def __albums_id(self):
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
        for album_id in self.__albums_id():
            print(f"Получаем данные из альбома: {album_id['title']}")
            time.sleep(rnd.randint(1, 5))
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
    # FILE_DIR1 = "Oksana_Magura"
    # magur = VkAgent(Token.TOKEN_VK, '9681859')
    # magur.files_downloader(FILE_DIR1)
    # # PATH_DIR1 = os.path.join(os.getcwd(), FILE_DIR1)
    # magur_load = Ya.YaUploader(Token.TOKEN_YA)
    # magur_load.upload(PATH_DIR1)
    # pprint(magur.photos_info())

    # FILE_DIR2 = "Oksa_Studio"
    # oksa_studio = VkAgent(Token.TOKEN_VK, '-142029999')
    # # pprint(oksa_studio.photos_info())
    # oksa_studio.files_downloader(FILE_DIR2)

    # FILE_DIR3 = "Netology"
    # netology = VkAgent(Token.TOKEN_VK, '-30159897')
    # # pprint(oksa_studio.photos_info())
    # netology.files_downloader(FILE_DIR3)

    # oksana = VkAgent(Token.TOKEN_VK, 448564047)
    # # pprint(oksana.friends_info())
    # # pprint(oksana.group_search('наращивание ресниц'))
    # oksana.get_users(3)

    company1 = VkAgent(folder_name='ads_4')
    # company1.group_search('наращивание ресниц')
    # company1.get_users(count=3, month=3)
    # company1.get_users_groups('ads_4_users_3_groups_4_month.txt')
    company1.groups_relevant()
    # print(company1.get_user_groups('140052354'))
