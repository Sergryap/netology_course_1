import requests
import os
import json
import Token
import Ya
import Agent
import hashlib


# Данные для авторизации из файла Token.py в текущей директории:
# token_ok = "..."
# application_id = "..."
# application_key = "..."
# application_secret_key = "..."
# session_secret_key = "..."

class OkAgent(Agent.Social):
    url = "https://api.ok.ru/fb.do"

    def __init__(self, fid):
        self.fid = fid
        self.params = {
            "application_key": Token.application_key,
            "fid": fid,
            "format": "json",
            "access_token": Token.token_ok
        }

    def __photos_get_albums(self):
        method = "photos.getAlbums"
        row = f"application_key={Token.application_key}fid={self.fid}format=jsonmethod={method}{Token.session_secret_key}"
        sig = hashlib.md5(row.encode('utf-8')).hexdigest()
        params_delta = {"method": method, "sig": sig}
        return requests.get(OkAgent.url, params={**self.params, **params_delta}).json()

    def __get_aid(self):
        """Возвращает список aid альбомов пользователя"""
        aids = []
        for value in self.__photos_get_albums()['albums']:
            aids.append({'aid': value['aid'], 'title': value['title']})
        return aids

    def __photos_get_photos(self, aid=None):
        method = "photos.getPhotos"
        if aid:
            row = f"aid={aid}application_key={Token.application_key}fid={self.fid}format=jsonmethod={method}{Token.session_secret_key}"
        else:
            row = f"application_key={Token.application_key}fid={self.fid}format=jsonmethod={method}{Token.session_secret_key}"
        sig = hashlib.md5(row.encode('utf-8')).hexdigest()
        params_delta = {"method": method, "sig": sig, "aid": aid}
        return requests.get(OkAgent.url, params={**self.params, **params_delta}).json()

    @staticmethod
    def __info_photos(info_foto):
        value_photos_info = []
        for photo in info_foto['photos']:
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
        return value_photos_info

    def photos_info(self):
        photos_info = {}
        for album in self.__get_aid():
            info = self.__photos_get_photos(aid=album['aid'])
            value_photos_info = self.__info_photos(info)
            photos_info[self._path_normalizer(album['title'])] = value_photos_info
        info = self.__photos_get_photos()
        value_photos_info = self.__info_photos(info)
        photos_info['Личные_фотографии'] = value_photos_info
        return photos_info


if __name__ == '__main__':
    FILE_DIR = "Алексей"
    ok1 = OkAgent("332021380847")
    ok1.files_downloader(FILE_DIR)
    # PATH_DIR = os.path.join(os.getcwd(), FILE_DIR)
    # ok1_load = Ya.YaUploader(Token.TOKEN_YA)
    # ok1_load.upload(PATH_DIR)

    # FILE_DIR1 = "Владимир"
    # ok1 = OkAgent("553931153141")
    # ok1.files_downloader(FILE_DIR1)
    # PATH_DIR1 = os.path.join(os.getcwd(), FILE_DIR1)
    # ok1_load = Ya.YaUploader(Token.TOKEN_YA)
    # ok1_load.upload(PATH_DIR1)
