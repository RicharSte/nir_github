import json
import os

from get_repos import get_repositories
from get_directory_contents import get_directory_contents
from search_hash import get_file_hash, search_hash_in_dataset, load_csv_to_dataframe


def main():
    if not os.path.exists('repositories.json') or os.path.getsize('repositories.json') == 0:
        print('Файл со списком репозиториев не существует или пустой. Получение списка репозиториев...')
        get_repositories()
    else:
        print('Файл со списком репозиториев уже существует. Загрузка данных из файла...')

    with open('repositories.json') as file:
        repositories = json.load(file)

    malware_dataset = load_csv_to_dataframe('full.csv')

    if malware_dataset is None:
        print('Не удалось открыть базу данных вирусов, завершение работы программы')
        return

    for repo in repositories:
        print(f'Обработка репозитория {repo["owner"]}/{repo["name"]}...\n')
        file_data_list = get_directory_contents(repo["owner"], repo["name"])
        for file_data in file_data_list:
            for hash_type in 'sha256', 'md5', 'sha1':
                file_hash = get_file_hash(file_data.file_content, hash_type)
                search_result = search_hash_in_dataset(malware_dataset, file_hash, hash_type + '_hash')
                if search_result is not None and not search_result.empty:
                    print(
                        f'Найдено совпадение хеша {hash_type} '
                        f'для файла {file_data.file_name} в репозитории {repo["name"]}')
                else:
                    print(f'Хеш {hash_type} для файла {file_data.file_name} не найден в базе данных')


if __name__ == '__main__':
    main()
