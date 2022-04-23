from bs4 import BeautifulSoup
import requests
from pprint import pprint


def get_count_group(group_id):
    url = f"https://vk.com/public{group_id}"
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
        }
    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    count = int(soup.find("span", class_="group_friends_count").text)
    print(count)

if __name__ == '__main__':
    get_count_group('73271503')


