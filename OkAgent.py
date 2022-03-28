import requests
import json
from pprint import pprint
import hashlib
import os
import Token
import main

#Данные для авторизации импортируются из файла Token.py в текущей директории:
# token_ok = "..."
# application_id = "..."
# application_key = "..."
# application_secret_key = "..."
# session_secret_key = "..."

class OkAgent:
    url = "https://api.ok.ru/fb.do"

    def __init__(self, fid):
        self.fid = fid
        self.params = {
            "application_key": Token.application_key,
            "fid": fid,
            "format": "json",
            "access_token": Token.token_ok
        }

    @property
    def photos_get_albums(self):
        method = "photos.getAlbums"
        row = f"application_key={Token.application_key}fid={self.fid}format=jsonmethod={method}{Token.session_secret_key}"
        sig = hashlib.md5(row.encode('utf-8')).hexdigest()
        params_delta = {"method": method, "sig": sig}
        return requests.get(OkAgent.url, params={**self.params, **params_delta}).json()

    @property
    def get_aid(self):
        """Возвращает список aid альбомов пользователя"""
        aids = []
        for value in self.photos_get_albums['albums']:
            aids.append({'aid': value['aid'], 'title': value['title']})
        return aids

    def photos_get_photos(self, aid=None):
        method = "photos.getPhotos"
        if aid:
            row = f"aid={aid}application_key={Token.application_key}fid={self.fid}format=jsonmethod={method}{Token.session_secret_key}"
        else:
            row = f"application_key={Token.application_key}fid={self.fid}format=jsonmethod={method}{Token.session_secret_key}"
        sig = hashlib.md5(row.encode('utf-8')).hexdigest()
        params_delta = {"method": method, "sig": sig, "aid": aid}
        return requests.get(OkAgent.url, params={**self.params, **params_delta}).json()

    @staticmethod
    def __path_normalizer(name_path):
        """Удаление и замена запрещенных символов в имени папки"""
        symbol_no = rf"""*:'"%!@?$/\\|&<>+.)("""
        name = '_'.join(name_path.split()).strip(symbol_no)
        for s in symbol_no:
            if s in name:
                name = name.replace(s, '_')
        return name

    @property
    def photos_info(self):
        photos_info = {}
        for album in self.get_aid:
            value_photos_info = []
            info = self.photos_get_photos(aid=album['aid'])
            for photo in info['photos']:
                area = 0
                for key in photo:
                    if 'pic' in key:
                        pic = key.strip('pic').split('x')
                        area_new = int(pic[0]) * int(pic[1])
                        if area_new > area:
                            area = area_new
                            photo_url = photo[key]
                            size = f'{pic[0]} * {pic[1]}'
                value_photos_info.append({
                    'file_name': f"id{photo['id']}.jpg",
                    'url': photo_url,
                    'size': size
                })
            photos_info[self.__path_normalizer(album['title'])] = value_photos_info
        return photos_info


    @staticmethod
    def __folder_creation(base_path, path):
        """
        Создание вложенной папки для директории base_path
        """
        file_path = os.path.join(base_path, path)
        if not os.path.isdir(file_path):
            os.mkdir(file_path)
        return file_path

    def files_downloader(self, file_dir: str):
        """
        Загрузка фотографий на локальный диск ПК
        file_dir - директория для загрузки файлов в текущей директории
        Вложенные папки создаются по именам альбомов
        """
        file_path_start = self.__folder_creation(os.getcwd(), file_dir)
        dict_foto_info = {}
        for title, value in self.photos_info.items():
            file_path = self.__folder_creation(file_path_start, title)
            print(f"Загружаем файлы в директорию >>> {file_path}:")
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




if __name__ == '__main__':
    ok1 = OkAgent("332021380847")
    # pprint(ok1.photos_get_albums)
    # print("=" * 100)
    # pprint(ok1.get_aid)
    # print("=" * 100)
    # pprint(ok1.photos_get_photos(aid="432076964335"))
    # pprint(ok1.photos_info)
    ok1.files_downloader('ok1')

