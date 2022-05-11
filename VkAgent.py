import requests
import os
import json
import Ya
import Agent
import time
import random as rnd
from bs4 import BeautifulSoup
from pprint import pprint
import sqlite3 as sq


class VkAgent(Agent.Social):
    url = 'https://api.vk.com/method/'
    with open(os.path.join(os.getcwd(), "Token.txt"), encoding='utf-8') as file:
        token = [t.strip() for t in file.readlines()]

    def __init__(self, folder_name=None, tok=token[0]):
        self.params = {'access_token': tok, 'v': '5.131'}
        self.author = 0
        if folder_name:
            self.folder_name = folder_name
            self.path_ads = self._folder_creation((self._folder_creation(os.getcwd(), 'VK_ads')), folder_name)
            self.path_analise = self._folder_creation(self.path_ads, 'users_groups')
            self.path_relevant = self._folder_creation(self.path_ads, 'groups_relevant')
            self.path_bot = self._folder_creation(self.path_ads, 'users_bot')
            self.path_users = self._folder_creation(self.path_ads, 'users')
            self.path_target = self._folder_creation(self.path_ads, 'target_audience')

    def db_create(self, suffix, relevant):
        table_name = suffix if relevant else 'groups_search'
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute("PRAGMA FOREIGN_KEYS=ON")
            cur.execute(f"DROP TABLE IF EXISTS groups_search_users")
            cur.execute(f"DROP TABLE IF EXISTS users_groups")
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            cur.execute(f"DROP TABLE IF EXISTS users_list")

            cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                count INTEGER,
                screen_name TEXT                                        
                )""")

            cur.execute(f"""CREATE TABLE IF NOT EXISTS users_list (
                id INTEGER PRIMARY KEY,
                last_seen_month INTEGER,
                count_groups INTEGER,
                city_id INTEGER,
                sex TEXT,
                stop_list INTEGER
                )""")

            cur.execute(f"""CREATE TABLE IF NOT EXISTS users_groups (
                user_id INTEGER PRIMARY KEY,
                count INTEGER,
                group_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users_list(id)
                )""")

            cur.execute(f"""CREATE TABLE IF NOT EXISTS groups_search_users (
                group_search_id INTEGER,
                user_id INTEGER,
                FOREIGN KEY (group_search_id) REFERENCES groups_search(id),
                FOREIGN KEY (user_id) REFERENCES users_list(id)
                )""")

    def __set_params(self, zero=True):
        self.author = 0 if zero else self.author + 1
        print(f'Токен заменен на >>> {self.author}!')
        # time.sleep(0.5)
        self.params = {'access_token': self.token[self.author], 'v': '5.131'}

    def res_stability(self, method, params_delta, i=0):
        print(f'Глубина рекурсии: {i}/токен: {self.author}')
        method_url = self.url + method
        response = requests.get(method_url, params={**self.params, **params_delta}).json()
        if 'response' in response:
            return response
        elif i == len(self.token) - 1:
            return False
        elif self.author < len(self.token) - 1:
            self.__set_params(zero=False)
        elif self.author == len(self.token) - 1:
            self.__set_params()
        count = i + 1
        return self.res_stability(method, params_delta, i=count)

    @staticmethod
    def verify_group(value: dict):
        """
        Условие включения группы в отбор
        """
        with open(os.path.join(os.getcwd(), 'words.txt'), encoding="utf-8") as file:
            words = [rew.strip().lower() for rew in file.readlines()]
        for rew in words:
            if rew == 'stop':
                flag = False
                continue
            elif rew == 'require':
                flag = True
                count = 0
                continue
            if rew in value['name'].lower():
                if not flag:
                    return False
                elif flag:
                    return True
            if flag:
                count += 1
                print(count)
        if count == 0:
            return True
        return False

    @staticmethod
    def get_count_group(group_id):
        """Определение количества подписчиков, в том числе, если они скрыты"""
        print(f'Beautifulsoup for {group_id}')
        url_vk = f"https://vk.com/public{group_id}"
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
        }
        response = requests.get(url=url_vk, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")
        count = soup.find("span", class_="group_friends_count")
        if count:
            return int(count.text)
        count = soup.find("span", class_="header_count")
        if count:
            return int(''.join(count.text.split()))
        return -1

    def group_search(self, q: str, members=None, suffix='groups', verify=True, relevant=False):
        """
        Поиск групп по ключевой фразе
        :param q: ключевая фраза для поиска
        :param suffix: суффикс для создаваемого итогового файла
        :param verify: указывает на необходимость проверки по условию verify_group
        :param relevant: указывается True при поиске релевантных групп
        :param members: минимальное количество участников группы
        """
        self.db_create(suffix, relevant)
        table_name = suffix if relevant else 'groups_search'
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            for soc in ['group', 'page']:
                offset = 0
                while True:
                    params_delta = {'q': q.lower(), 'type': soc, 'country_id': 1, 'city_id': 110, 'sort': 6,
                                    'offset': offset}
                    response = self.res_stability('groups.search', params_delta)
                    offset += 1
                    if response and response['response']['items'] and offset < 10:
                        for item in response['response']['items']:
                            print(f"offset={offset}/id{item['id']}")
                            if (item['id'],) not in cur.execute(f"SELECT id FROM {table_name}").fetchall():
                                if verify and self.verify_group(item):
                                    cur.execute(
                                        f"INSERT INTO {table_name} (id, screen_name) VALUES({item['id']}, '{item['screen_name']}')")
                                elif not verify:
                                    cur.execute(
                                        f"INSERT INTO {table_name} (id, screen_name) VALUES({item['id']}, '{item['screen_name']}')")
                    else:
                        break

            if members:
                groups = cur.execute(f"SELECT id FROM {table_name}").fetchall()
                for group in groups:
                    print(f'+count: id{group[0]}')
                    count = self._get_offset(group)[1]
                    count = count if count != -1 else self.get_count_group(group[0])
                    cur.execute(f"UPDATE {table_name} SET count = {count} WHERE id = {group[0]}")

    def _get_offset(self, group_id):
        """
        Определение количества шагов для анализа группы и числа участников
        :param group_id: идентификатор группы
        :return: количество шагов (offset), количество участников в группе
        """
        params_delta = {'group_id': group_id, 'sort': 'id_desc', 'offset': 0, 'fields': 'last_seen'}
        response = self.res_stability('groups.getMembers', params_delta)
        if response:
            count = response['response']['count']
            return count // 1000, count
        return -1, -1

    def _users_lock(self, user_id):
        """
        Получение информации о том закрытый или нет профиль пользователя
        :return: bool
        """
        params_delta = {'user_ids': user_id}
        response = self.res_stability('users.get', params_delta)
        if response and 'is_closed' in response['response'][0]:
            return response['response'][0]['is_closed']
        return -1, -1

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
        max_offset = self._get_offset(group_id)[0]
        print(f'max_offset={max_offset}')
        while offset <= max_offset:
            print(f'offset={offset}')
            params_delta = {'group_id': group_id, 'sort': 'id_desc', 'offset': offset, 'fields': 'last_seen,sex,city'}
            response = self.res_stability('groups.getMembers', params_delta)
            if response:
                offset += 1
                for item in response['response']['items']:
                    time_start = round(time.time()) - round(month * 30.42 * 86400)
                    if 'last_seen' in item and item['last_seen']['time'] >= time_start and item['sex'] == sex:
                        if 'city' in item and item['city']['id'] == city:
                            good_id_list.append(item['id'])
        return list(set(good_id_list))

    def get_users(self, month=4, sex=1, city=110):
        """
        Создание списка из id подписчиков групп из файла с id групп
        Подписчики состоят не менее чем в количестве count группах
        :param month: активностm пользователя не менее месяцев назад
        :param sex: пол подписчика (по умолчанию жен)
        :param city: идентификатор города пользователя
        Результат записывается в файл, готовый к импорту в РК VK
        """
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM groups_search")
            len_group = len(list(cur))
            groups = cur.execute("SELECT id FROM groups_search").fetchall()
            count_i = 1
            for group in groups:
                print(f'id{group[0]}_{count_i}/{len_group}')
                users = self.__get_users(group[0], month=month, sex=sex, city=city)
                for user in users:
                    cur.execute(f"INSERT INTO groups_search_users VALUES({group[0]}, {user})")
                count_i += 1

        # считаем количество подписок каждого пользователя на группы из groups_search
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute("SELECT user_id FROM groups_search_users")
            count_groups = {}
            for user in cur:
                count_groups[user[0]] = count_groups.get(user[0], 0) + 1

        # записываем полученные данные
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            for user, value in count_groups.items():
                cur.execute(f"""INSERT INTO users_list VALUES(
                {user},
                {month}, 
                {value},
                {city},
                '{'female' if sex == 1 else 'male'}',
                0)""")

    def get_user_groups(self, user_id):
        """
        Создает кортеж из списка групп пользователя и количество групп
        :param user_id: id пользователя, для которого создается кортеж
        :return: обозначенный кортеж из списка и количества групп
        """
        if self._users_lock(user_id):
            return -1, -1
        params_delta = {'user_id': user_id, 'offset': 0}
        print(f'offset=0')
        response = self.res_stability('groups.get', params_delta)
        if response:
            offset = 1
            max_offset = response['response']['count'] // 1000
            user_groups = []
            user_groups.extend(response['response']['items'])
            while offset <= max_offset:
                print(f'offset={offset}')
                params_delta = {'user_id': user_id, 'offset': offset}
                response = self.res_stability('groups.get', params_delta)
                user_groups.extend(response['response']['items'])
                offset += 1
                user_groups = list(set(user_groups))
            return user_groups, len(user_groups)
        return -1, -1

    def get_users_groups(self):
        """
        Создает словарь :
        {'user_id':
        {'groups': [список из id групп, в которые входит пользователь]
         'count': количество групп пользователя}
        ...
        }
        Записывает в файлы по 1000 'user_id' в каждом
        """
        users_groups = {}
        user_files = os.listdir(self.path_users)
        if len(user_files) == 1:
            n = 1
        else:
            for i, user_file in enumerate(user_files, start=1):
                print(f'{i}: "{user_file}"')
            n = int(input('Введите номер файл для анализа: ').strip())
        file_user_list = user_files[n - 1]
        print('Получаем данные по группам пользователей из файла:')
        print(file_user_list)
        # time.sleep(3)
        with open(os.path.join(self.path_users, file_user_list), encoding="utf-8") as f:
            users_list = f.readlines()
        print('Получаем данные:')
        count_end = len(users_list)
        for count, user in enumerate(users_list, start=1):
            print(f'{count}/{count_end}: id{user.strip()}')
            user_groups_info = self.get_user_groups(user.strip())

            if user_groups_info[1] != -1:
                with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
                    cur = con.cursor()
                    cur.execute(f"""CREATE TABLE IF NOT EXISTS users_groups (
                        user_id INTEGER,
                        count INTEGER,
                        group_id INTEGER
                        )""")
                    for group in user_groups_info[0]:
                        cur.execute(f"""INSERT INTO users_groups VALUES(
                        {user},
                        {user_groups_info[1]}, 
                        {group}
                        )""")

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
        """Объединяет файлы с группами пользоватлей в один"""
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

    def friends_info(self, user_id, count_only=True):
        """Метод friends.get VK"""
        if count_only:
            params_delta = {'user_id': user_id}
            response = self.res_stability('friends.get', params_delta)
            if response:
                return response['response']['count']
        else:
            friends_info = {}
            params_delta = {'user_id': user_id,
                            'fields': 'nickname,domain,sex,bdate,city,country,timezone,photo_200_orig'
                            }
            response = self.res_stability('friends.get', params_delta)
            if response:
                friends_info['count'] = response['response']['count']
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
                        'city': city}
                return friends_info
        return -1

    def __albums_id(self, owner_id):
        """
        Cоздает список словарей, содержащих название и id
        альбомы пользователя
        """
        params_delta = {'owner_id': owner_id, 'need_system': '1'}
        response = self.res_stability('photos.getAlbums', params_delta)
        if response:
            albums_id = []
            for item in response['response']['items']:
                albums_id.append({
                    'title': self._path_normalizer(item['title']),
                    'id': item['id']
                })
            return albums_id
        return -1, -1

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

    def __photos_get(self, owner_id, album_id):
        """Создает список для метода photos_info"""
        params_delta = {'owner_id': owner_id, 'album_id': album_id, 'extended': 1}
        response = self.res_stability('photos.get', params_delta)
        if response:
            photos_info = []
            file_names_count = {}
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
            return photos_info
        return -1, -1

    def photos_info(self, owner_id):
        """
        Создает словарь типа:
        {'название альбома':
        [{'file_name': file_name, 'url': photo_url, 'size': image_resolution}...]
        Метод ВК: photos.get:
        """
        total_photos_info = {}
        for album_id in self.__albums_id(owner_id):
            print(f"Получаем данные из альбома: {album_id['title']}")
            # time.sleep(rnd.randint(1, 5))
            total_photos_info[album_id['title']] = self.__photos_get(owner_id, album_id['id'])
        return total_photos_info


def search_ads():
    def set_groups_param(c):
        words = input('Введите ключевую фразу для поиска групп: ').strip().lower()
        members = input('Введите минимальное количество членов групп, если нет, то - "N": ').strip().lower()
        if members.isdigit():
            c.group_search(members=int(members), q=words)
        else:
            c.group_search(q=words)

    def set_users_param(c):
        print('Введите данные для отбора целевой аудитории:')
        month = int(input('Последняя активность не менее N месяцев назад: ').strip())
        c.get_users(month=month)

    folder_name = input(f'Введите название нового проекта либо существующего: ').strip()
    company = VkAgent(folder_name)
    print('Выполнить новый поиск групп или использовать ранее выполненный:')
    i = input('"Y" - новый поиcк, "любой символ" - использовать существующий: ').strip().lower()
    if i == 'y':
        set_groups_param(c=company)
    elif not os.path.isfile(os.path.join(company.path_ads, f"{os.path.split(company.path_ads)[1]}_groups.json")):
        print('Целевых групп не создано, сначала выполните поиск')
        set_groups_param(c=company)
    if os.listdir(company.path_users):
        print('Выполнить новый отбор аудитории или использовать ранее выполненный:')
        i = input('"Y" - новый, "любой символ" - использовать существующий: ').strip().lower()
        if i == 'y':
            set_users_param(company)
    else:
        set_users_param(company)

    q = input('Выполнить поиск групп пользователей по всем отобранным пользователям ("Y"/"N"): ').strip().lower()
    if q == "y":
        company.get_users_groups()


if __name__ == '__main__':
    search_ads()
    # vk1 = VkAgent('ads_15')
    # vk1.get_users()
    # vk1.get_users_groups()
    # pprint(vk1.friends_info("6055736"))

    # FILE_DIR2 = "Oksa_Studio"
    # oksa_studio = VkAgent()
    # oksa_studio.files_downloader('-142029999', FILE_DIR2)
