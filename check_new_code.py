import os
from get_directory_contents import get_directory_contents
from cluster_analysis import (
    analyze_code,
    load_reference_clusters,
    compare_clusters,
)
from logging_config import logging
from language_detection import should_process_file

logger = logging.getLogger(__name__)

TERMINAL_WIDTH = os.get_terminal_size().columns


def check_new_code(threshold_value: float = 0.5):
    logger.info('Загружаем эталонные кластеры...')
    reference_clusters_file = 'reference_clusters.pkl'
    reference_df = load_reference_clusters(reference_clusters_file)

    logger.info('Загружаем файлы для анализа...')
    new_code_contents = get_directory_contents(
        'vxunderground', 'MalwareSourceCode', 'Python'
    )

    repo_results = []
    # Анализируем каждый новый файл отдельно и сравниваем с эталонными кластерами
    for file_data in new_code_contents:
        if not should_process_file(file_data.file_name, file_data.file_content):
            continue
        logger.info(
            f'Analyzing code file: {file_data.file_name} from {file_data.owner}/{file_data.repo_name}'
        )
        new_df = analyze_code(file_data.file_content, visualize=False)
        if not new_df.empty:
            similarity_score, common_clusters = compare_clusters(new_df, reference_df)

            repo_results.append(
                {
                    'file_name': file_data.file_name,
                    'similarity_score': similarity_score,
                    'common_clusters': common_clusters,
                    'is_malicious': similarity_score > threshold_value,
                }
            )

            if similarity_score > threshold_value:  # Пороговое значение
                print(f'{" Similarity Analysis RESULT ":*^{TERMINAL_WIDTH}}')
                print(f'Similarity score: {similarity_score:.2f}')
                print(
                    f'⚠️ File "{file_data.file_name}" is potentially malicious.\n'
                    f'🔍 Common clusters detected: {", ".join(map(str, common_clusters))}'
                )
                print(f'{" ALERT ":*^{TERMINAL_WIDTH}}')
            else:
                print(f'{" Similarity Analysis RESULT ":*^{TERMINAL_WIDTH}}')
                print(f'Similarity score: {similarity_score:.2f}')
                print(
                    f'✅ File "{file_data.file_name}" is not malicious based on the current analysis.'
                )
                print(f'{" SAFE ":*^{TERMINAL_WIDTH}}')

    # Финальный отчет для всего репозитория
    print(f'{" Repository Analysis Summary ":*^{TERMINAL_WIDTH}}')

    total_files = len(repo_results)
    malicious_files = sum(1 for result in repo_results if result['is_malicious'])
    safe_files = total_files - malicious_files

    print(f'Total files analyzed: {total_files}')
    print(f'Malicious files detected: {malicious_files}')
    print(f'Safe files: {safe_files}')

    if malicious_files > 0:
        print('\nDetails of potentially malicious files:')
        for result in repo_results:
            if result['is_malicious']:
                print(
                    f'⚠️ File: {result["file_name"]}, '
                    f'Similarity Score: {result["similarity_score"]:.2f}, '
                    f'Common Clusters: {", ".join(map(str, result["common_clusters"]))}'
                )


if __name__ == '__main__':
    check_new_code()
