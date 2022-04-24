from bs4 import BeautifulSoup
import requests
import sqlite3 as sq


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


def get_set_sql():
    with sq.connect("social_agent.db") as con:
        cur = con.cursor()
        cur.execute("DROP TABLE IF EXISTS groups_search")
        cur.execute("""CREATE TABLE IF NOT EXISTS groups_search (
            group_id INTEGER,
            screen_name TEXT,
            name TEXT,
            count INTEGER
            )""")


if __name__ == '__main__':
    # get_count_group('73271503')
    get_set_sql()
