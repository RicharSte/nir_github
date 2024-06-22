import os
from get_directory_contents import get_directory_contents
from cluster_analysis import analyze_code_clusters, save_reference_clusters
import pandas as pd


def collect_reference_clusters(repositories):
    all_df = []

    for owner, repo_name in repositories:
        contents = get_directory_contents(owner, repo_name)

        # Создаем директорию для сохранения результатов, если она не существует
        save_dir = "cluster_results"
        os.makedirs(save_dir, exist_ok=True)

        # Анализируем каждый известный вредоносный файл отдельно и сохраняем результаты
        for file_data in contents:
            print(
                f"Analyzing known malware file: {file_data.file_name} from {file_data.owner}/{file_data.repo_name}"
            )
            df = analyze_code_clusters(
                file_data.file_content,
                visualize=False,
                save_results=True,
                filename=f'{save_dir}/{file_data.repo_name}_{file_data.file_name.replace("/", "_")}.csv',
            )
            if not df.empty:
                all_df.append(df)

    if all_df:
        # Объединяем все данные в один DataFrame
        combined_df = pd.concat(all_df, ignore_index=True)

        # Сохраняем результаты кластеризации известных вредоносных кодов как эталонные
        reference_clusters_file = "reference_clusters.pkl"
        save_reference_clusters(combined_df, reference_clusters_file)
        print(f"Reference clusters saved to {reference_clusters_file}")
    else:
        print("No valid data to save.")


if __name__ == '__main__':
    repositories = [
        ('vxunderground', 'MalwareSourceCode'),
        # ('cryptwareapps', 'Malware-Database'),
        # ('ytisf', 'theZoo'),
    ]
    collect_reference_clusters(repositories)
