import requests
import os
import json
import Token
import Ya
import VkAgent
import time
import random as rnd
from pprint import pprint


class Botovod(VkAgent.VkAgent):

    def __init__(self, folder_name, owner_id='7352307', token=Token.TOKEN_VK):
        super().__init__(folder_name, owner_id=owner_id, token=token)
        self.list_relevant = ['брови', 'ламинирование', 'мода', 'красота']
        self.path_users_analise = self._folder_creation(self.path_ads, 'users_analise')

    def groups_relevant(self):
        """
        Поиск релевантных групп по данным списка list_relevant.
        Запись в отдельные json файлы с суффиксами из элементов списка list_relevant
        """
        for q in self.list_relevant:
            print(f'Поиск по "{q}"')
            self.group_search(q=q, suffix=f'relevant_{q}', verify=False)

    def get_list_relevant(self):
        """
        Создание списка релевантных групп по всем элементам self.list_relevant
        c объединением в один файл txt
        :return: group_list
        """
        gen_file = (os.path.join(self.path_ads, file) for file in os.listdir(self.path_ads) if
                    os.path.isfile(os.path.join(self.path_ads, file)) and 'relevant' in file)
        groups_list = []
        for file in gen_file:
            with open(file, encoding="utf-8") as f:
                groups_list.extend(json.load(f).keys())

        file_list_relevant = os.path.join(self.path_users_analise,
                                          f"{os.path.split(self.path_ads)[1]}_relevant.txt")
        with open(file_list_relevant, 'w', encoding="utf-8") as f:
            for group in groups_list:
                f.write(f'{group}\n')
        return groups_list

    def exclusion_relevant_groups(self, file_users_groups: str):
        """
        Исключаем из словаря со значениями из групп пользователя
        релевантные группы, созданные в get_list_relevant
        :param file_users_groups: json файл со словарем:
        ключи - id пользователя, значения - списки групп пользователя
        :return: словарь, в котором ключи - id пользователя,
        значения - списки нерелевантных групп
        """
        new_users_groups = {}
        file = os.path.join(self.path_users_analise, file_users_groups)
        with open(file, encoding="utf-8") as f:
            all_users_group = json.load(f)
        delta_groups = set(self.get_list_relevant())

        # Приводим к строковому типу значения all_users_group
        for user, groups in all_users_group.items():
            all_users_group[user] = [str(group) for group in groups]

        for key, value in all_users_group.items():
            # print(key)
            new_value = list(set(value) - delta_groups)
            new_users_groups[key] = new_value

        file_no_relevant = os.path.join(self.path_users_analise, f"{os.path.split(self.path_ads)[1]}_not_relevant.json")
        with open(file_no_relevant, 'w', encoding="utf-8") as f:
            json.dump(new_users_groups, f, indent=2, ensure_ascii=False)
        return new_users_groups

    def groups_count(self, file_users_groups, count=100):
        """
        Подсчет количества вхождений не релевантных групп в группы пользователей
        :param file_users_groups: json файл со словарем: ключи - id пользователя,
        значения - списки групп пользователя
        :param count: минимальное учитываемое количество вхождений группы
        :return: словарь ключи - id групп
        значения - количество вхождений в группы пользователей
        """
        groups_count = {}
        not_relevant_groups = self.exclusion_relevant_groups(file_users_groups)
        for groups in not_relevant_groups.values():
            for group in groups:
                groups_count[group] = groups_count.get(group, 0) + 1
        for group, i in groups_count.copy().items():
            if i > count or i < 10:
                del groups_count[group]
            # else:
            #     groups_count[group] = {'entry': i, 'count': self._get_offset(group)[1]}

        file_groups_count = os.path.join(self.path_users_analise,
                                         f"{os.path.split(self.path_ads)[1]}_groups_count.json")
        with open(file_groups_count, 'w', encoding="utf-8") as f:
            json.dump(groups_count, f, indent=2, ensure_ascii=False)
        return groups_count

    def get_bot_list(self, count_entry=6):
        """
        Создание списка ботов
        :param count_entry: количество вхождений нерелевантных групп из groups_count
        в группы пользователей, при котором пользователь относится к боту
        """
        bot_users = []
        file_users = os.path.join(self.path_users_analise, f"{os.path.split(self.path_ads)[1]}_not_relevant.json")
        with open(file_users, encoding="utf-8") as f:
            all_users = json.load(f)
        file_count = os.path.join(self.path_users_analise, f"{os.path.split(self.path_ads)[1]}_groups_count.json")
        with open(file_count, encoding="utf-8") as f:
            count_groups = json.load(f)

        for user, groups in all_users.items():
            count = 0
            for group in groups:
                if group in count_groups:
                    count += 1
            if count >= count_entry:
                print(count, len(groups), user)
                bot_users.append(user)

        file_bot = os.path.join(self.path_users_analise,
                                f"{os.path.split(self.path_ads)[1]}_bot_users.txt")
        with open(file_bot, 'w', encoding="utf-8") as f:
            for user in bot_users:
                f.write(f'{user}\n')


if __name__ == '__main__':
    b1 = Botovod(folder_name='ads_4')
    # b1.get_list_relevant()
    # b1.exclusion_relevant_groups('ads_4_users_3_groups_4_month.json')
    # b1.groups_count('ads_4_users_3_groups_4_month.json', count=100)
    b1.get_bot_list(count_entry=200)
