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

    def __init__(self, folder_name, last_seen=2, count_groups=2, tok=token[0]):
        self.params = {'access_token': tok, 'v': '5.131'}
        self.author = 0
        self.last_seen = last_seen
        self.count_groups = count_groups
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
                user_id INTEGER,
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
                    if response and response['response']['items'] and offset < 6:
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

    def __get_users(self, group_id, sex, city):
        """
        Создание списка из id подписчиков группы
        :param group_id: id группы, у которой отбираем подписчиков
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
                    time_start = round(time.time()) - round(self.last_seen * 30.42 * 86400)
                    if 'last_seen' in item and item['last_seen']['time'] >= time_start and item['sex'] == sex:
                        if 'city' in item and item['city']['id'] == city:
                            good_id_list.append(item['id'])
        return list(set(good_id_list))

    def get_users(self, sex=1, city=110):
        """
        Создание списка из id подписчиков групп из файла с id групп
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
                users = self.__get_users(group[0], sex=sex, city=city)
                for user in users:
                    cur.execute(f"INSERT INTO groups_search_users VALUES({group[0]}, {user})")
                count_i += 1

        # считаем количество подписок каждого пользователя на группы из groups_search
        # with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
        #     cur = con.cursor()
        #     cur.execute("SELECT user_id FROM groups_search_users")
        #     count_groups = {}
        #     for user in cur:
        #         count_groups[user[0]] = count_groups.get(user[0], 0) + 1

        # считаем количество подписок каждого пользователя на группы из groups_search
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute(f"""
                SELECT user_id, COUNT(user_id) AS count                
                FROM groups_search_users
                GROUP BY user_id
                ORDER BY count                
                """)
            count_groups = cur.fetchall()

        # записываем полученные данные
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            for user in count_groups:
                cur.execute(f"""INSERT INTO users_list VALUES(
                {user[0]},
                {self.last_seen}, 
                {user[1]},
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
        n = int(input('Пользователь состоит не менеее чем в n групп из поиска: ').strip())
        print('Получаем данные по группам пользователей')
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur1 = con.cursor()
            all_count = len(list(cur.execute(f"SELECT id FROM users_list WHERE count_groups >= {n}")))
            cur.execute(f"SELECT id FROM users_list WHERE count_groups >= {n}")
            for count, user in enumerate(cur, start=1):
                print(f'{count}/{all_count}_id{user[0]}')
                user_groups_info = self.get_user_groups(user[0])
                if user_groups_info[1] != -1:
                    for group in user_groups_info[0]:
                        cur1.execute(f"""INSERT INTO users_groups VALUES(
                        {user[0]},
                        {user_groups_info[1]}, 
                        {group}
                        )""")

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


def search_ads():
    def set_groups_param(c):
        words = input('Введите ключевую фразу для поиска групп: ').strip().lower()
        members = input('Введите минимальное количество членов групп, если нет, то - "N": ').strip().lower()
        if members.isdigit():
            c.group_search(members=int(members), q=words)
        else:
            c.group_search(q=words)

    folder_name = input(f'Введите название нового проекта либо существующего: ').strip()
    company = VkAgent(folder_name)
    print('Выполнить новый поиск групп или использовать ранее выполненный:')
    i = input('"Y" - новый поиcк, "любой символ" - использовать существующий: ').strip().lower()
    if i == 'y':
        set_groups_param(c=company)
    elif not os.path.isfile(os.path.join(company.path_ads, "social_agent.db")):
        print('Целевых групп не создано, сначала выполните поиск')
        set_groups_param(c=company)

    if os.listdir(company.path_users):
        print('Выполнить новый отбор аудитории или использовать ранее выполненный:')
        i = input('"Y" - новый, "любой символ" - использовать существующий: ').strip().lower()
        if i == 'y':
            company.get_users()
    else:
        company.get_users()

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
