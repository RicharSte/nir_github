import requests
from collections import namedtuple

from source import TOKEN

FileData = namedtuple('FileData', ['owner', 'repo_name', 'file_name', 'file_content'])


def get_directory_contents(owner, repo_name, directory_path='', results=None):
    if results is None:
        results = []

    headers = {
        'Authorization': f'token {TOKEN}'
    }

    url = f'https://api.github.com/repos/{owner}/{repo_name}/contents/{directory_path}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content_data = response.json()

        for content_item in content_data:
            if content_item['type'] == 'file':
                file_name = content_item['name']
                file_content_url = content_item['download_url']
                file_response = requests.get(file_content_url)

                if file_response.status_code == 200:
                    file_data = FileData(owner, repo_name, file_name, file_response.text)
                    results.append(file_data)
                else:
                    print(f'Ошибка при получении файла {file_name}: {file_response.status_code}')

            elif content_item['type'] == 'dir':
                dir_name = content_item['name']
                get_directory_contents(owner, repo_name, f'{directory_path}/{dir_name}', results)

    else:
        print(f'Ошибка при получении содержимого репозитория {owner}/{repo_name}: {response.status_code}')

    return results
