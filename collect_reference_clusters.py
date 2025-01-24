import os
from get_directory_contents import get_directory_contents
from cluster_analysis import analyze_code_clusters, save_reference_clusters
import pandas as pd
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_reference_clusters(repositories):
    all_df = []

    for owner, repo_name in repositories:
        try:
            logger.info(f'Processing repository: {owner}/{repo_name}')
            contents = get_directory_contents(owner, repo_name)

            save_dir = 'cluster_results'
            os.makedirs(save_dir, exist_ok=True)

            for file_data in contents:
                logger.info(
                    f'Analyzing file: {file_data.file_name} from {file_data.owner}/{file_data.repo_name}'
                )
                df = analyze_code_clusters(
                    file_data.file_content,
                    visualize=False,
                    save_results=True,
                    filename=f'{save_dir}/{file_data.repo_name}_{file_data.file_name.replace("/", "_")}.csv',
                )
                if not df.empty:
                    all_df.append(df)
        except Exception as e:
            logger.error(f'Error processing {owner}/{repo_name}: {str(e)}')

    # Объединяем все результаты
    if all_df:
        final_df = pd.concat(all_df, ignore_index=True)
        save_reference_clusters(final_df, 'reference_clusters.pkl')
        logger.info('Reference clusters saved successfully')
    else:
        logger.warning('No data collected')


if __name__ == '__main__':
    print('Collecting reference clusters...')
    # Список репозиториев для анализа
repositories = [
    # ('haku4130', 'Binary-vector'),
    ('cryptwareapps', 'Malware-Database'),
]

collect_reference_clusters(repositories)
