import requests
import os
import json
import time
import random as rnd
import Token


class Social:
    url = 'https://api.vk.com/method/'

    def __set_params(self, i=True):
        self.author = rnd.randint(0, len(self.token) - 1) if i else self.author + 1
        self.params = {'access_token': self.token[self.author][1], 'v': '5.131'}

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

    def res_stability(self, method: str, params_delta: dict, var=False):
        method_url = self.url + method
        response = requests.get(method_url, params={**self.params, **params_delta}).json()
        if 'response' in response:
            return response
        return self.__change_token(method, params_delta, func=self.res_stability, var=var)

    @staticmethod
    def _folder_creation(base_path, path):
        """
        Создание вложенной папки для директории base_path
        """
        file_path = os.path.join(base_path, path)
        if not os.path.isdir(file_path):
            os.mkdir(file_path)
        return file_path

    @staticmethod
    def _path_normalizer(name_path):
        """Удаление и замена запрещенных символов в имени папки"""
        symbol_no = rf"""*:'"%!@?$/\\|&<>+.)("""
        name = '_'.join(name_path.split()).strip(symbol_no)
        for s in symbol_no:
            if s in name:
                name = name.replace(s, '_')
        return name

    def files_downloader(self, owner_id, file_dir: str):
        """
        Загрузка фотографий на локальный диск ПК
        file_dir - директория для загрузки файлов в текущей директории
        Вложенные папки создаются по именам альбомов из self_photos.info()
        """
        file_path_start = self._folder_creation(os.getcwd(), file_dir)
        dict_foto_info = {}
        for title, value in self.photos_info(owner_id).items():
            file_path = self._folder_creation(file_path_start, title)
            print(f"Загружаем файлы в директорию >>> {file_path}:")
            time.sleep(rnd.randint(1, 5))
            list_value = []

            for info in value:
                file_name = os.path.join(file_path, info['file_name'])
                response = requests.get(info['url'])
                print(f"'{info['file_name']}' ")
                with open(file_name, 'wb') as f:
                    f.write(response.content)

                list_value.append({
                    'file_name': info['file_name'],
                    'size': info['size']
                })

            dict_foto_info[title] = list_value

        # Создание и загрузка итогового json-файла в директорию file_dir
        file_name_json = os.path.join(file_path_start, f"{file_dir}.json")
        print(f"Загружаем файл '{file_dir}.json' в >>> {file_path_start}")
        with open(file_name_json, 'w', encoding="utf-8") as f:
            json.dump(dict_foto_info, f, indent=2, ensure_ascii=False)
        print("=" * 50)
