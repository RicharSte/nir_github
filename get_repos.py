import requests
import json
from source import TOKEN


def main():
    headers = {
        'Authorization': f'token {TOKEN}'
    }

    params = {
        'q': 'language:python',
        'per_page': 100,
    }

    url = 'https://api.github.com/search/repositories'
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        repositories = [{'name': repo['name'], 'owner': repo['owner']['login']} for repo in data.get('items', [])]

        with open('repositories.json', 'w') as file:
            json.dump(repositories, file)

        print('Список репозиториев сохранен в файле "repositories.json".')
    else:
        print(f'Ошибка при получении списка репозиториев: {response.status_code}')


if __name__ == '__main__':
    main()
