import fileinput
import requests
import os
import json
import Ya
import VkAgent
import time
import random as rnd
from bs4 import BeautifulSoup
from pprint import pprint
import sqlite3 as sq


class Botovod(VkAgent.VkAgent):

    def __init__(self, folder_name):
        super().__init__(folder_name)
        self.list_relevant = ['наращивание ресниц', 'брови', 'маникюр', 'макияж', 'ламинирование', 'красота', 'мода']
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute(f"""CREATE TABLE IF NOT EXISTS
                groups_search_relevant (
                id INTEGER PRIMARY KEY,
                count INTEGER,
                screen_name VARCHAR(50)                                        
                )""")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS
                users_groups_not_relevant (
                user_id INTEGER,
                count INTEGER,
                group_id INTEGER                                        
                )""")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS
                count_groups_not_relevant (
                group_id INTEGER PRIMARY KEY,
                count INTEGER                                                        
                )""")
            cur.execute(f"""CREATE TABLE IF NOT EXISTS
                bot_users (
                user_id INTEGER                                                                       
                )""")

    def groups_relevant(self, members=None):
        """
        Поиск релевантных групп по данным списка list_relevant.
        Запись в отдельные json файлы с суффиксами из элементов списка list_relevant
        """
        i = input(f"Использовать список: {', '.join(self.list_relevant)}? (Y/N):").lower().strip()
        list_relevant = self.list_relevant if i == 'y' else [q.strip().lower() for q in
                                                             input(f"Введите ваш список фраз через запятую: ").split(
                                                                 ',')]
        for word in list_relevant:
            print(f'Поиск по "{word}"')
            self.group_search(members=members, suffix=f'relevant_{word}', verify=False, relevant=True,
                              word_relevant=word)

    def get_list_relevant(self):
        """
        Создание общей таблицы релевантных групп по всем таблицам релевантных групп
        c объединением в одну таблицу
        """
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            table_name = (f"relevant_{'_'.join(rew.strip().split())}" for rew in self.list_relevant)
            for table in table_name:
                cur.execute(f"""
                    INSERT INTO groups_search_prev (id, screen_name)
                    SELECT id, screen_name                  
                    FROM {table}                
                    """)
            cur.execute(f"DELETE FROM groups_search_relevant")
            cur.execute(f"""
                INSERT INTO count_groups_not_relevant (id, screen_name)
                SELECT id, screen_name                  
                FROM groups_search_prev
                GROUP BY id, screen_name
                ORDER BY id
                """)
            cur.execute(f"""
                DELETE FROM groups_search_prev
                """)

    def exclusion_relevant_groups(self):
        """
        Исключаем из 'users_groups' релевантные группы
        из 'groups_search_relevant' по каждому пользователю
        Записываем в таблицу 'users_groups_not_relevant'
        """
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute(f"DELETE FROM users_groups_not_relevant")
            cur.execute(f"""
                INSERT INTO users_groups_not_relevant
                SELECT user_id, count, group_id                  
                FROM users_groups
                WHERE group_id NOT IN (
                SELECT id
                FROM groups_search_relevant)
                """)

    def groups_count(self, count, min_gr_count):
        """
        Подсчет количества вхождений нерелевантных групп в группы пользователей
        """
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute(f"DELETE FROM count_groups_not_relevant")
            cur.execute(f"""
            INSERT INTO count_groups_not_relevant            
            SELECT group_id, count(*) AS n
            FROM users_groups_not_relevant
            GROUP BY 1
            HAVING n >= {count}
            ORDER BY n
            """)
            gen = list(cur.execute("""SELECT group_id
                      FROM count_groups_not_relevant 
                      """))
            for group in gen:
                if self._get_offset(group[0])[1] > min_gr_count or self.get_count_group(group[0]) > min_gr_count:
                    print(f"Исключаем группу {group[0]}")
                    cur.execute(f"""
                        DELETE FROM count_groups_not_relevant
                        WHERE group_id = {group[0]}
                        """)

    def get_bot_list(self, gr=500, stop_gr=10):
        """
        Создание списка ботов
        :param stop_gr: допустимое количество вхождений нерелевантных групп из groups_count
        :param gr: допустимое количество групп у пользователя
        """
        with sq.connect(os.path.join(self.path_ads, "social_agent.db")) as con:
            cur = con.cursor()
            cur.execute(f"DELETE FROM bot_users")
            cur.execute(f"""
                INSERT INTO bot_users
                SELECT user_id
                FROM users_groups_not_relevant                
                WHERE group_id IN (
                  SELECT group_id
                  FROM count_groups_not_relevant)                                  
                GROUP BY user_id
                HAVING count(*) > {stop_gr}
                UNION
                SELECT DISTINCT user_id
                FROM users_groups_not_relevant
                WHERE count >= {gr}
                """)
            users_list = list(cur.execute("""
                                 SELECT DISTINCT user_id
                                 FROM users_groups_not_relevant
                                 WHERE user_id NOT IN (
                                 SELECT user_id
                                 FROM bot_users)  
                                 """))
            for user in users_list:
                if self.friends_info(user[0]) > 1500:
                    cur.execute(f'INSERT INTO bot_users VALUES ({user[0]})')

    def get_target_audience(self):
        """Получение списка пользователей, очищенного от нежелательных пользователей"""

        bots = os.listdir(self.path_bot)
        all_user_bots = set()
        with fileinput.FileInput([os.path.join(self.path_bot, f) for f in bots if 'all_bots' not in f],
                                 encoding='utf-8') as lines:
            for bot in lines:
                all_user_bots.add(bot)
        with open(os.path.join(self.path_bot, 'all_bots.txt'), 'w', encoding="utf-8") as f:
            for bot in all_user_bots:
                f.write(f'{bot}')

        users = os.listdir(self.path_users)
        for n, f in enumerate(users, start=1):
            file = os.path.join(self.path_users, f)
            with open(file, encoding="utf-8") as file_users:
                print(f'{n}: {f}, количество={len(file_users.readlines())}')
        i = int(input('Выберите первоначальный файл пользователей: ').strip())
        print()
        with open(os.path.join(self.path_users, users[i - 1]), encoding="utf-8") as file_users:
            all_users = set([f.strip() for f in file_users.readlines()])

        bots = sorted(os.listdir(self.path_bot))
        for n, f in enumerate(bots, start=1):
            file = os.path.join(self.path_bot, f)
            with open(file, encoding="utf-8") as file_bots:
                print(f'{n}: {f}, количество={len(file_bots.readlines())}')
        j = int(input('Выберите файл с нежелательными пользователями: ').strip())
        print()
        with open(os.path.join(self.path_bot, bots[j - 1]), encoding="utf-8") as file_bots:
            bot_users = set([f.strip() for f in file_bots.readlines()])

        file_target = os.path.join(self.path_target,
                                   f'{(users[i - 1]).split(".")[0]}_free_№_{len(os.listdir(self.path_target)) + 1}.txt')
        with open(file_target, 'w', encoding="utf-8") as f:
            for user in list(all_users - bot_users):
                f.write(f'{user}\n')
        return list(all_users - bot_users)


if __name__ == '__main__':
    b1 = Botovod(folder_name='ads_21')
    b1.get_bot_list()
    # b1.groups_count(300, 15000)
    # b1.exclusion_relevant_groups()
    # b1.groups_relevant()
    # b1.get_list_relevant()
    # b1.get_bot_list('ads_14_users_groups.json', count=500, stop_gr=10, gr=200, min_gr_count=15000)
    # b1.get_target_audience()
