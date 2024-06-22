import os
from get_directory_contents import get_directory_contents
from cluster_analysis import (
    analyze_code_clusters,
    load_reference_clusters,
    compare_clusters,
)


def check_new_code():
    # Загружаем эталонные кластеры
    reference_clusters_file = "reference_clusters.pkl"
    reference_df = load_reference_clusters(reference_clusters_file)

    # Загружаем новые коды для проверки на вредоносность
    new_code_contents = get_directory_contents(
        'vxunderground', 'MalwareSourceCode'
    )

    # Анализируем каждый новый файл отдельно и сравниваем с эталонными кластерами
    for file_data in new_code_contents:
        print(
            f"Analyzing new code file: {file_data.file_name} from {file_data.owner}/{file_data.repo_name}"
        )
        new_df = analyze_code_clusters(file_data.file_content, visualize=False)
        if not new_df.empty:
            similarity_score, common_clusters = compare_clusters(
                new_df, reference_df
            )
            print(f"Similarity score: {similarity_score}")
            if similarity_score > 0.5:  # Пороговое значение, можно настроить
                print(
                    f"File {file_data.file_name} is potentially malicious. Common clusters: {common_clusters}"
                )


if __name__ == '__main__':
    check_new_code()
