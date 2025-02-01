import requests
from collections import namedtuple
import zipfile
import tarfile
import py7zr
import io
import os
import logging

from collections import defaultdict

from source import TOKEN

logger = logging.getLogger(__name__)


FileData = namedtuple('FileData', ['owner', 'repo_name', 'file_name', 'file_content'])


def get_extension(filename: str) -> str:
    """Извлекает расширение из имени файла."""
    basename = os.path.basename(filename)
    parts = basename.split('.')
    return parts[-1].lower() if len(parts) > 1 else 'no_extension'


def count_extensions(results: list[FileData]) -> dict[str, int]:
    """Подсчитывает количество файлов по расширениям."""
    counts = defaultdict(int)
    for file_data in results:
        ext = get_extension(file_data.file_name)
        counts[ext] += 1
    return dict(counts)


def get_directory_contents(owner: str, repo_name: str, directory_path='', results=None):
    if results is None:
        results = []

    headers = {'Authorization': f'Bearer {TOKEN}'}

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
                    file_content = file_response.content
                    if file_name.endswith('.zip'):
                        try:
                            extract_zip(file_content, owner, repo_name, results)
                        except zipfile.BadZipFile:
                            logger.error(
                                f'Файл {file_name} не является корректным zip-архивом'
                            )
                        except RuntimeError as e:
                            logger.error(
                                f'Ошибка при обработке zip-архива {file_name}: {e}'
                            )
                    elif file_name.endswith('.tar.gz') or file_name.endswith('.tgz'):
                        try:
                            extract_tar(file_content, owner, repo_name, results)
                        except tarfile.ReadError:
                            logger.error(
                                f'Файл {file_name} не является корректным tar-архивом'
                            )
                    elif file_name.endswith('.7z'):
                        try:
                            extract_7z(file_content, owner, repo_name, results)
                        except py7zr.PasswordRequired:
                            logger.error(
                                f'Файл {file_name} требует пароль для распаковки'
                            )
                        except py7zr.Bad7zFile:
                            logger.error(
                                f'Файл {file_name} не является корректным 7z-архивом'
                            )
                        except py7zr.UnsupportedCompressionMethodError:
                            logger.error(
                                f'Файл {file_name} использует неподдерживаемый метод сжатия'
                            )
                    else:
                        try:
                            file_data = FileData(
                                owner, repo_name, file_name, file_response.text
                            )
                            results.append(file_data)
                        except UnicodeDecodeError:
                            logger.error(f'Ошибка при декодировании файла {file_name}')
                        except Exception as e:
                            logger.error(f'Ошибка при обработке файла {file_name}: {e}')
                else:
                    logger.error(
                        f'Ошибка при получении файла {file_name}: {file_response.status_code}'
                    )

            elif content_item['type'] == 'dir':
                dir_name = content_item['name']
                get_directory_contents(
                    owner, repo_name, f'{directory_path}/{dir_name}', results
                )
    else:
        logger.error(
            f'Ошибка при получении содержимого репозитория {owner}/{repo_name}: {response.status_code}'
        )

    logger.debug(count_extensions(results))
    return results


def extract_zip(file_content, owner, repo_name, results):
    with zipfile.ZipFile(io.BytesIO(file_content)) as zip_ref:
        for zip_info in zip_ref.infolist():
            if not zip_info.is_dir():
                try:
                    with zip_ref.open(zip_info) as file:
                        try:
                            file_data = FileData(
                                owner,
                                repo_name,
                                zip_info.filename,
                                file.read().decode('utf-8'),
                            )
                            results.append(file_data)
                        except UnicodeDecodeError:
                            logger.warning(
                                f'Ошибка при декодировании файла {zip_info.filename}'
                            )
                        except Exception as e:
                            logger.error(
                                f'Ошибка при обработке файла {zip_info.filename}: {e}'
                            )
                except RuntimeError as e:
                    logger.error(f'Ошибка при обработке файла {zip_info.filename}: {e}')


def extract_tar(file_content, owner, repo_name, results):
    with tarfile.open(fileobj=io.BytesIO(file_content), mode='r:gz') as tar_ref:
        for tar_info in tar_ref.getmembers():
            if tar_info.isfile():
                try:
                    file = tar_ref.extractfile(tar_info)
                    if file:
                        try:
                            file_data = FileData(
                                owner,
                                repo_name,
                                tar_info.name,
                                file.read().decode('utf-8'),
                            )
                            results.append(file_data)
                        except UnicodeDecodeError:
                            logger.warning(
                                f'Ошибка при декодировании файла {tar_info.name}'
                            )
                        except Exception as e:
                            logger.error(
                                f'Ошибка при обработке файла {tar_info.name}: {e}'
                            )
                except Exception as e:
                    logger.error(f'Ошибка при распаковке файла {tar_info.name}: {e}')


def extract_7z(file_content, owner, repo_name, results):
    try:
        with py7zr.SevenZipFile(io.BytesIO(file_content), mode='r') as archive:
            for name, bio in archive.readall().items():
                try:
                    file_data = FileData(
                        owner, repo_name, name, bio.read().decode('utf-8')
                    )
                    results.append(file_data)
                except UnicodeDecodeError:
                    logger.warning(f'Ошибка при декодировании файла {name}')
                except Exception as e:
                    logger.error(f'Ошибка при обработке файла {name}: {e}')
    except py7zr.exceptions.UnsupportedCompressionMethodError:
        logger.error('Файл использует неподдерживаемый метод сжатия')
    except Exception as e:
        logger.error(f'Ошибка при обработке 7z-архива: {e}')
