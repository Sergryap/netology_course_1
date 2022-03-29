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
            photos_info[self._path_normalizer(album['title'])] = value_photos_info
        return photos_info


if __name__ == '__main__':
    FILE_DIR = "ok1"
    PATH_DIR = os.path.join(os.getcwd(), FILE_DIR)
    # ok1 = OkAgent("332021380847")
    # ok1.files_downloader(FILE_DIR)
    ok1_load = Ya.YaUploader(Token.TOKEN_YA)
    ok1_load.upload(PATH_DIR)