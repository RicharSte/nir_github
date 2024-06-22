import json
import os

from get_repos import get_repositories
from get_directory_contents import get_directory_contents
from search_hash import (
    get_file_hash,
    search_hash_in_dataset,
    load_csv_to_dataframe,
)
from cluster_analysis import analyze_code_clusters


def load_repos():
    if (
        not os.path.exists('repositories.json')
        or os.path.getsize('repositories.json') == 0
    ):
        print(
            'Файл со списком репозиториев не существует или пустой. Получение списка репозиториев...'
        )
        get_repositories()
    else:
        print(
            'Файл со списком репозиториев уже существует. Загрузка данных из файла...'
        )

    with open('repositories.json') as file:
        repositories = json.load(file)

    return repositories


def analyze_with_dataset():

    repositories = load_repos()

    malware_dataset = load_csv_to_dataframe('full.csv')

    if malware_dataset is None:
        print(
            'Не удалось открыть базу данных вирусов, завершение работы программы'
        )
        return

    for repo in repositories:
        print(f'Обработка репозитория {repo["owner"]}/{repo["name"]}...\n')
        file_data_list = get_directory_contents(repo["owner"], repo["name"])
        for file_data in file_data_list:
            for hash_type in 'sha256', 'md5', 'sha1':
                file_hash = get_file_hash(file_data.file_content, hash_type)
                search_result = search_hash_in_dataset(
                    malware_dataset, file_hash, hash_type + '_hash'
                )
                if search_result is not None and not search_result.empty:
                    print(
                        f'Найдено совпадение хеша {hash_type} '
                        f'для файла {file_data.file_name} в репозитории {repo["name"]}'
                    )
                else:
                    print(
                        f'Хеш {hash_type} для файла {file_data.file_name} не найден в базе данных'
                    )


def main():
    # Получаем содержимое репозиториев
    contents1 = get_directory_contents('haku4130', 'Binary-vector')
    # contents2 = get_directory_contents('cryptwareapps', 'Malware-Database')

    # Объединяем результаты
    all_contents = contents1  # + contents2

    # Создаем директорию для сохранения результатов, если она не существует
    save_dir = "cluster_results"
    os.makedirs(save_dir, exist_ok=True)

    # Анализируем каждый файл отдельно и сохраняем результаты
    for file_data in all_contents:
        print(
            f"Analyzing file: {file_data.file_name} from {file_data.owner}/{file_data.repo_name}"
        )
        df = analyze_code_clusters(file_data.file_content, visualize=False)
        df.to_csv(
            f'{save_dir}/{file_data.repo_name}_{file_data.file_name.replace("/", "_")}.csv',
            index=False,
        )


if __name__ == '__main__':
    main()
