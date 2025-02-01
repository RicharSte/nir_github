import os
import re
import pandas as pd
from logging_config import logging
from get_directory_contents import get_directory_contents
from cluster_analysis import analyze_code, save_reference_clusters
from language_detection import should_process_file

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 1024 * 1024  # 1MB limit


def preprocess_code(code: str) -> str:
    """Удаляем комментарии и лишние пробелы"""
    code = re.sub(r'#.*', '', code)  # Удаляем однострочные комментарии
    code = re.sub(r'\n\s*\n', '\n', code)  # Удаляем пустые строки
    return code.strip()


def process_file(file_data, save_dir: str) -> pd.DataFrame:
    """Process single file with retries"""
    if len(file_data.file_content) < 10:
        logger.warning(f'Слишком короткий файл: {file_data.file_name}')
        return pd.DataFrame()

    if len(file_data.file_content) > MAX_FILE_SIZE:
        logger.warning(f'Слишком большой файл: {file_data.file_name}')
        return pd.DataFrame()

    try:
        return analyze_code(
            file_data.file_content,
            save_clusters=True,
            clusters_filename=(
                f'{save_dir}/{file_data.owner}_{file_data.repo_name}'
                f'/{file_data.file_name.replace("/", "_")}.csv',
            ),
        )
    except Exception as e:
        logger.error(f'Error processing {file_data.file_name}: {e}')
        return pd.DataFrame()


def collect_reference_clusters(repositories: list[tuple[str, str, str]]):
    """Collect clusters from repositories with improved error handling"""
    all_code = []
    save_dir = 'cluster_results'
    os.makedirs(save_dir, exist_ok=True)

    # Сбор всего кода из репозиториев
    for owner, repo_name, path in repositories:
        try:
            logger.info(f'Processing repository: {owner}/{repo_name}')
            contents = get_directory_contents(owner, repo_name, path)

            # Фильтрация и объединение кода
            filtered = [
                file_data.file_content
                for file_data in contents
                if should_process_file(file_data.file_name, file_data.file_content)
            ]
            all_code.extend(filtered)

        except Exception as e:
            logger.error(f'Error processing {owner}/{repo_name}: {str(e)}')
            continue

    # Объединяем весь код в одну строку
    full_code = preprocess_code('\n'.join(all_code))

    # Анализ всего кода
    try:
        df = analyze_code(
            full_code,
            num_clusters=10,  # Увеличиваем количество кластеров для больших данных
            save_clusters=True,
            clusters_filename=f'{save_dir}/{owner}_{repo_name}.csv',
        )
        save_reference_clusters(df, 'reference_clusters.pkl')
        logger.info('Reference clusters saved successfully')
    except Exception as e:
        logger.error(f'Clustering failed: {str(e)}')


if __name__ == '__main__':
    repositories = [
        ('vxunderground', 'MalwareSourceCode', 'Python'),
    ]
    collect_reference_clusters(repositories)
