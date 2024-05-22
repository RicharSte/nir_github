import pandas as pd
import hashlib


def get_file_hash(file_content, hash_type='sha256'):
    """
    Генерирует хеш для содержимого файла.

    :param file_content: Содержимое файла.
    :param hash_type: Тип хеша ('sha256', 'md5', 'sha1').
    :return: Строка с хешем файла.
    """
    if hash_type == 'sha256':
        hasher = hashlib.sha256()
    elif hash_type == 'md5':
        hasher = hashlib.md5()
    elif hash_type == 'sha1':
        hasher = hashlib.sha1()
    else:
        raise ValueError('Неизвестный тип хеша')

    hasher.update(file_content.encode('utf-8'))
    return hasher.hexdigest()


def load_csv_to_dataframe(file_path):
    """
    Загружает CSV файл в DataFrame.

    :param file_path: Путь к CSV файлу.
    :return: DataFrame с данными из файла.
    """
    try:
        print('Загружаю данные о вредоносном ПО из базы...')
        df = pd.read_csv(file_path, quotechar='"', on_bad_lines='warn', engine='python')
        print(df.head())
        return df
    except Exception as e:
        print(f"Ошибка при загрузке файла {file_path}: {e}")
        return None


def search_hash_in_dataset(df, hash_value, hash_type='sha256_hash'):
    """
    Ищет хеш в заданном столбце DataFrame.

    :param df: DataFrame для поиска.
    :param hash_value: Хеш значение, которое нужно найти.
    :param hash_type: Тип хеша (столбец), по умолчанию 'sha256_hash'.
    :return: Строки DataFrame, где найден хеш.
    """
    if df is not None and hash_type in df.columns:
        return df[df[hash_type] == hash_value]
    else:
        print("DataFrame пустой или не содержит указанного столбца хеша.")
        return None
