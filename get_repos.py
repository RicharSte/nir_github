import requests
import json
from source import TOKEN


def get_repositories():
    headers = {'Authorization': f'token {TOKEN}'}

    repositories = []
    url = 'https://api.github.com/search/repositories'
    page = 1
    page_amount = 10

    while page <= page_amount:
        params = {'q': 'language:python', 'per_page': 100, 'page': page}

        print(f'Происходит запрос к GitHub API: {page}/{page_amount}')
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            repos = data.get('items', [])
            if not repos:
                break

            repositories.extend(
                [
                    {'name': repo['name'], 'owner': repo['owner']['login']}
                    for repo in repos
                ]
            )
            page += 1
        else:
            print(
                f'Ошибка при получении списка репозиториев: {response.status_code}'
            )
            break

    with open('repositories.json', 'w') as file:
        json.dump(repositories, file)

    print(
        f'Список репозиториев сохранен в файле "repositories.json". Всего репозиториев: {len(repositories)}'
    )


if __name__ == '__main__':
    get_repositories()
