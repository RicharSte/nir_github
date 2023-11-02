import requests
import json
from source import TOKEN

headers = {
    'Authorization': f'token {TOKEN}'
}

with open('repositories.json', 'r') as file:
    repositories = json.load(file)


def get_directory_contents(owner, repo_name, directory_path):
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
                    file_content = file_response.text
                    print(f'Содержимое файла {file_name}:\n{file_content}\n')
                else:
                    print(f'Ошибка при получении файла {file_name}: {file_response.status_code}')

            elif content_item['type'] == 'dir':
                dir_name = content_item['name']
                get_directory_contents(owner, repo_name, f'{directory_path}/{dir_name}')

    else:
        print(f'Ошибка при получении содержимого репозитория {owner}/{repo_name}: {response.status_code}')


for repo in repositories:
    owner = repo['owner']
    repo_name = repo['name']
    directory_path = ''
    print(f'Обработка репозитория {owner}/{repo_name}...\n')
    get_directory_contents(owner, repo_name, directory_path)
