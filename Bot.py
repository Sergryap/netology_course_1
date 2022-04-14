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

    def __init__(self, folder_name, token=Token.token_vk[0][1]):
        super().__init__(folder_name, token=token)
        self.list_relevant = ['наращивание ресниц', 'брови', 'ламинирование', 'красота', 'мода']

    def __groups_relevant(self):
        """
        Поиск релевантных групп по данным списка list_relevant.
        Запись в отдельные json файлы с суффиксами из элементов списка list_relevant
        """
        for q in self.list_relevant:
            print(f'Поиск по "{q}"')
            self.group_search(q=q, suffix=f'relevant_{q}', verify=False, relevant=True)

    def get_list_relevant(self):
        """
        Создание списка релевантных групп по всем элементам self.list_relevant
        c объединением в один файл txt
        :return: group_list
        """
        self.__groups_relevant()
        gen_file = (os.path.join(self.path_relevant, file) for file in os.listdir(self.path_relevant) if
                    os.path.isfile(os.path.join(self.path_relevant, file)) and 'relevant' in file)
        groups_list = []
        for file in gen_file:
            with open(file, encoding="utf-8") as f:
                try:
                    groups_list.extend(json.load(f).keys())
                except json.decoder.JSONDecodeError:
                    continue
        groups_list = list(set(groups_list))
        file_list_relevant = os.path.join(self.path_relevant,
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
        ключи - id пользователя,
        значения - {'groups': список групп пользователя, "count': количество участников}
        :return: словарь, в котором ключи - id пользователя,
        значения - списки нерелевантных групп
        """
        new_users_groups = {}
        file = os.path.join(self.path_ads, file_users_groups)
        with open(file, encoding="utf-8") as f:
            all_users_group = json.load(f)

        file_list_relevant = os.path.join(self.path_relevant, f"{os.path.split(self.path_ads)[1]}_relevant.txt")
        with open(file_list_relevant, encoding="utf-8") as f:
            delta_groups = f.readlines()
        delta_groups = set([f.strip() for f in delta_groups])

        # Приводим к строковому типу значения id групп в all_users_group
        for user, groups in all_users_group.items():
            all_users_group[user] = {'count': groups['count'],
                                     'groups': [str(group) for group in groups['groups']]}

        for key, value in all_users_group.items():
            print(key)
            new_value = {'count': value['count'],
                         'groups': list(set(value['groups']) - delta_groups)}
            new_users_groups[key] = new_value

        file_no_relevant = os.path.join(self.path_ads, f"{os.path.split(self.path_ads)[1]}_not_relevant.json")
        with open(file_no_relevant, 'w', encoding="utf-8") as f:
            json.dump(new_users_groups, f, indent=3, ensure_ascii=False)
        return new_users_groups

    def groups_count(self, file_users_groups, count):
        """
        Подсчет количества вхождений нерелевантных групп в группы пользователей
        :param file_users_groups: json файл со словарем:
        ключи - id пользователя,
        значения - {'groups': список групп пользователя, "count': количество участников}
        :param count: минимальное учитываемое количество вхождений группы
        :return: словарь ключи - id групп
        значения - количество вхождений в группы пользователей
        """
        groups_count = {}
        not_relevant_groups = self.exclusion_relevant_groups(file_users_groups)
        for groups in not_relevant_groups.values():
            for group in groups['groups']:
                groups_count[group] = groups_count.get(group, 0) + 1
        for group, i in groups_count.copy().items():
            if i < count:
                del groups_count[group]

        file_groups_count = os.path.join(self.path_ads,
                                         f"{os.path.split(self.path_ads)[1]}_not_relevant_groups_count.json")
        with open(file_groups_count, 'w', encoding="utf-8") as f:
            json.dump(groups_count, f, indent=2, ensure_ascii=False)
        return groups_count

    def get_bot_list(self, file, count=500, stop_gr=30, gr=500):
        """
        Создание списка ботов
        :param stop_gr: количество вхождений нерелевантных групп из groups_count
        :param gr: допустимое количество групп у пользователя
        :param file: файл для groups_count
        :param count: count для groups_count
        в группы пользователей, при котором пользователь относится к боту
        """
        self.groups_count(file_users_groups=file, count=count)
        bot_users = []
        file_users = os.path.join(self.path_ads, f"{os.path.split(self.path_ads)[1]}_not_relevant.json")
        with open(file_users, encoding="utf-8") as f:
            all_users = json.load(f)
        file_count = os.path.join(self.path_ads, f"{os.path.split(self.path_ads)[1]}_not_relevant_groups_count.json")
        with open(file_count, encoding="utf-8") as f:
            count_groups = json.load(f)

        for user, groups in all_users.items():
            i = 0
            for group in groups['groups']:
                if group in count_groups:
                    i += 1
            if i >= stop_gr or groups['count'] >= gr:
                print(i, len(groups), user)
                bot_users.append(user)

        file_bot = os.path.join(self.path_bot,
                                f"{os.path.split(self.path_ads)[1]}_bot_users_count_{count}_stop_gr_{stop_gr}_gr_{gr}.txt")
        with open(file_bot, 'w', encoding="utf-8") as f:
            for user in bot_users:
                f.write(f'{user}\n')


if __name__ == '__main__':
    b1 = Botovod(folder_name='ads_6')
    # b1.get_list_relevant()
    b1.get_bot_list('ads_6_users_groups.json', count=500, stop_gr=50, gr=500)
