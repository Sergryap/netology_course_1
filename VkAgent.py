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

    def __init__(self, folder_name, owner_id=Token.token_vk[0][0], token=Token.token_vk[0][1]):
        self.params = {'access_token': token, 'v': '5.131', 'owner_id': owner_id}
        self.owner_id = owner_id
        self.folder_name = folder_name
        self.path_ads = self._folder_creation((self._folder_creation(os.getcwd(), 'VK_ads')), folder_name)
        self.path_analise = self._folder_creation(self.path_ads, 'users_groups')
        self.path_relevant = self._folder_creation(self.path_ads, 'groups_relevant')
        self.path_bot = self._folder_creation(self.path_ads, 'users_bot')
        self.path_users = self._folder_creation(self.path_ads, 'users')
        self.token = Token.token_vk
        self.author = 0

    def __set_params(self, i=True):
        self.author = rnd.randint(0, len(self.token) - 1) if i else self.author + 1
        self.params = {'access_token': self.token[self.author][1], 'v': '5.131',
                       'owner_id': self.token[self.author][0]}
        self.owner_id = self.token[self.author][0]

    def __change_token(self, *args, **kwargs):
        print('Замена токена!')
        for key, value in kwargs.items():
            if key == 'func':
                func = value
            if key == 'var':
                var = value
        if self.author < len(self.token) - 1:
            self.__set_params(i=False)
            print(f'1_token={self.author}')
            return func(*args)
        elif var:
            if self.author == len(self.token) - 1:
                self.__set_params()
                print(f'2_token={self.author}')
            return -1, -1
        elif self.author == len(self.token) - 1:
            self.__set_params()
            print(f'3_token={self.author}')
            return func(*args)

    @staticmethod
    def verify_group(value: dict):
        """
        Условие включения группы в отбор
        """
        return ('обучение' not in value['name'].lower()
                and 'материалы' not in value['name'].lower()
                and 'материалов' not in value['name'].lower()
                and 'всё для' not in value['name'].lower()
                and 'все для' not in value['name'].lower()
                and 'бесплатно' not in value['name'].lower()
                and 'ресниц' in value['name'].lower()
                )

    def group_search(self, q: str, suffix='groups', verify=True, relevant=False):
        """
        Поиск групп по ключевой фразе
        :param q: ключевая фраза для поиска
        :param suffix: суффикс для создаваемого итогового файла
        :param verify: указывает на необходимость проверки по условию verify_group
        :param relevant: указывается True при поиске релевантных групп
        :return: словарь с ключами по id групп, значения словарь с названиями группы и числом участников
        """
        group_search = {}
        group_url = self.url + 'groups.search'
        for soc in ['group', 'page', 'event']:
            for offset in range(100):
                params_delta = {'q': q.lower(), 'type': soc, 'country_id': 1, 'city_id': 110, 'sort': 6,
                                'offset': offset}
                response = requests.get(group_url, params={**self.params, **params_delta}).json()
                if 'response' in response:
                    for item in response['response']['items']:
                        print(item['id'])
                        if verify and self.verify_group(item):
                            group_search[item['id']] = {'screen_name': item['screen_name'], 'name': item['name']}
                        elif not verify:
                            group_search[item['id']] = {'screen_name': item['screen_name'], 'name': item['name']}
                else:
                    return self.__change_token(q, suffix, verify, relevant, func=self.group_search, var=False)
        # Добавляем количество участников по ключу count
        for group in group_search:
            print(f'+count: id{group}')
            group_search[group]['count'] = self.__get_offset(group)[1]
        path_result = self.path_relevant if relevant else self.path_ads
        group_result_json = os.path.join(path_result, f"{os.path.split(self.path_ads)[1]}_{suffix}.json")
        with open(group_result_json, 'w', encoding="utf-8") as f:
            json.dump(group_search, f, indent=2, ensure_ascii=False)
        return group_search

    def __get_offset(self, group_id):
        """
        Определение количества шагов для анализа группы и числа участников
        :param group_id: идентификатор группы
        :return: количество шагов (offset), количество участников в группе
        """
        offset_url = self.url + 'groups.getMembers'
        params_delta = {'group_id': group_id, 'sort': 'id_desc', 'offset': 0, 'fields': 'last_seen'}
        response = requests.get(offset_url, params={**self.params, **params_delta}).json()
        if 'response' in response:  # проверка доступности
            count = response['response']['count']
        else:
            return self.__change_token(group_id, func=self.__get_offset, var=True)
        return count // 1000, count

    def __get_users(self, group_id, month, sex, city):
        """
        Создание списка из id подписчиков группы
        :param group_id: id группы, у которой отбираем подписчиков
        :param month: количество месяцев с последнего посещения участника группы
        :param sex: пол участника группы для отбора в список
        return: список участников группы
        """
        offset = 0
        good_id_list = []
        max_offset = self.__get_offset(group_id)[0]
        print(f'max_offset={max_offset}')
        get_users_url = self.url + 'groups.getMembers'
        while offset <= max_offset:
            print(f'offset={offset}')
            params_delta = {'group_id': group_id, 'sort': 'id_desc', 'offset': offset, 'fields': 'last_seen,sex,city'}
            response = requests.get(get_users_url, params={**self.params, **params_delta}).json()
            if 'response' in response:
                offset += 1
                for item in response['response']['items']:
                    time_start = round(time.time()) - round(month * 30.42 * 86400)
                    if 'last_seen' in item and item['last_seen']['time'] >= time_start and item['sex'] == sex:
                        if 'city' in item and item['city']['id'] == city:
                            good_id_list.append(item['id'])
            else:
                return self.__change_token(group_id, month, sex, city, func=self.__get_users, var=False)

        return good_id_list

    def get_users(self, count=2, month=4, sex=1, city=110):
        """
        Создание списка из id подписчиков групп из файла с id групп
        Подписчики состоят не менее чем в количестве count группах
        :param count: минимальное количество групп в которых состоит подписчик
        :param month: активностm пользователя не менее месяцев назад
        :param sex: пол подписчика (по умолчанию жен)
        :param city: идентификатор города пользователя
        Результат записывается в файл, готовый к импорту в РК VK
        """
        group_search_json = os.path.join(self.path_ads, f"{os.path.split(self.path_ads)[1]}_groups.json")
        with open(group_search_json, encoding="utf-8") as f:
            group_list = json.load(f)

        # формируем общий список пользователей, входящих в группы group_list
        all_users = []
        len_group = len(group_list)
        count_i = 1
        for group in group_list:
            print(f'id{group}_{count_i}/{len_group}')
            users = self.__get_users(group, month=month, sex=sex, city=city)
            all_users.extend(users)
            count_i += 1

        # считаем количество подписок каждого пользователя на группы из group_lilst
        count_groups = {}
        for user in all_users:
            count_groups[user] = count_groups.get(user, 0) + 1
        all_users = []
        for user, value in count_groups.items():
            if value >= count:
                all_users.append(user)
        # записываем полученные данные в файл
        male = 'female' if sex == 1 else 'male'
        users_file = os.path.join(self.path_users,
                                  f"{os.path.split(self.path_ads)[1]}_users_{count}_groups_{month}_month_{male}_sex_{city}_city.txt")
        with open(users_file, 'w', encoding="utf-8") as f:
            for item in all_users:
                f.write(f'{item}\n')

    def get_user_groups(self, user_id):
        """
        Создает кортеж из списка групп пользователя и количество групп
        :param user_id: id пользователя, для которого создается кортеж
        :return: обозначенный кортеж из списка и количества групп
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
                user_groups = list(set(user_groups))
            return user_groups, len(user_groups)
        return self.__change_token(user_id, func=self.get_user_groups, var=True)

    def get_users_groups(self, file_user_list: str):
        """
        Создает словарь :
        {'user_id':
        {'groups': [список из id групп, в которые входит пользователь]
         'count': количество групп пользователя}
        ...
        }
        Записывает в файлы по 1000 'user_id' в каждом
        :param file_user_list: файл со списком id пользователей в дирректрии self.path_ads
        """
        users_groups = {}
        with open(os.path.join(self.path_users, file_user_list), encoding="utf-8") as f:
            users_list = f.readlines()
        print('Получаем данные:')
        # time.sleep(0.1)
        count_end = len(users_list)
        for count, user in enumerate(users_list, start=1):
            print(f'{count}/{count_end}: id{user.strip()}')
            user_groups_info = self.get_user_groups(user.strip())
            # pprint(user_groups_info)
            users_groups[user.strip()] = {'count': user_groups_info[1],
                                          'groups': user_groups_info[0]
                                          }
            if users_groups[user.strip()]['count'] == -1:
                del users_groups[user.strip()]

            if count % 1000 == 0 or count == count_end:
                users_groups_json = os.path.join(self.path_analise,
                                                 f"{file_user_list.split('.')[0]}_{count}_groups.json")
                with open(users_groups_json, 'w', encoding="utf-8") as f:
                    json.dump(users_groups, f, indent=4, ensure_ascii=False)
                users_groups = {}
        return self.__union_users_files()

    def __union_users_files(self):
        gen_file = (os.path.join(self.path_analise, f) for f in os.listdir(self.path_analise))
        users_groups = {}
        for file in gen_file:
            with open(file, encoding="utf-8") as f:
                group_list = json.load(f)
                users_groups.update(group_list)
        users_groups_file = os.path.join(self.path_ads, f'{os.path.split(self.path_ads)[1]}_users_groups.json')
        with open(users_groups_file, 'w', encoding="utf-8") as f:
            json.dump(users_groups, f, indent=4, ensure_ascii=False)
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

    # company1 = VkAgent(folder_name='ads_4')
    # company1.group_search('наращивание ресниц')
    # company1.get_users(count=3, month=3)
    # company1.get_users_groups('ads_4_users_3_groups_3_month.txt')
    # company1.groups_relevant()
    # print(company1.get_user_groups('140052354'))

    company2 = VkAgent(folder_name='ads_6')
    # company2.group_search('наращивание ресниц')
    # company2.get_users(count=2, month=8)
    company2.get_users_groups('ads_6_users_2_groups_8_month_female_sex_110_city.txt')
