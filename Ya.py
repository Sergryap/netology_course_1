import os
import requests
import Token


class YaUploader:
    """
    Создает объекты-загрузчики содержимого папок с дублированием структуры
    методом self.upload_recursive(path_start) на яндекс-диск.
    Использован метод рекурсивного обхода папок
    """
    URL = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self, token):
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                        'Authorization': f'OAuth {token}'}

    def __create_folder(self, folder):
        """Создание папки на диске"""
        requests.put(f"{YaUploader.URL}?path={folder}", headers=self.headers)

    def __create_folder_recursive(self, folder):
        """
        Создание структуры вложенных папок на яндекс-диске
        аналогичной ПК от начальной папки в текущей директории до folder
        """
        base_path = os.getcwd()
        base_path_name = os.path.split(base_path)[1]
        path_ya = os.path.split(folder)
        ya_dir = path_ya[1]

        while base_path_name != os.path.split(path_ya[0])[1]:
            ya_dir = f"{os.path.split(path_ya[0])[1]}/{ya_dir}"
            path_ya = os.path.split(path_ya[0])
        self.__create_folder(ya_dir)
        return ya_dir

    def __upload(self, folder, ya_dir, file):
        """Загрузка файла file из folder в ya_dir на яндекс диске"""
        file_path_name = os.path.join(folder, file)
        res = requests.get(f"{YaUploader.URL}/upload?path={ya_dir}/{file}&overwrite=true", headers=self.headers)
        link = res.json()['href']
        with open(file_path_name, 'rb') as f:
            requests.put(link, files={'file': f})

    def upload(self, path_start):

        """
        Метод загружает папки с файлами из папки path_start в яндекс диск,
        воссоздавая структуру папок на яндекс диске аналогичную относительному пути на ПК,
        начиная с папки path_start
        path_start - абсолютный путь к папке на ПК для загрузки на я-диск
        """
        # Создаем генератор абсолютных путей папок:
        gen_path = (os.path.join(path_start, folder) for folder in os.listdir(path_start) if
                    os.path.isdir(os.path.join(path_start, folder)))
        # Создаем генератор имен файлов без путей:
        gen_file_name = (file for file in os.listdir(path_start) if os.path.isfile(os.path.join(path_start, file)))
        ya_dir = self.__create_folder_recursive(path_start)
        print(f'Загрузка файлов в папку "{ya_dir}":')
        for file in gen_file_name:
            print(file)
            self.__upload(path_start, ya_dir, file)

        for folder in gen_path:
            # Рекурсивный вызов функции для вложенных папок
            self.upload(folder)


if __name__ == '__main__':
    path = os.path.join(os.getcwd(), 'Test01')
    Ya1 = YaUploader(Token.TOKEN_YA)
    Ya1.upload(path)
