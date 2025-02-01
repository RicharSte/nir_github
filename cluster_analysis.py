import logging
from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np
from tqdm import tqdm

logger = logging.getLogger(__name__)

model_name = 'Salesforce/codegen-2B-mono'
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token
model = AutoModel.from_pretrained(model_name)


def _get_embeddings(code: str):
    # Токенизация кода с использованием токенизатора модели
    inputs = tokenizer(
        code, return_tensors='pt', truncation=True, padding=True, max_length=2048
    )

    # Получение эмбеддингов
    with torch.no_grad():
        outputs = model(**inputs)

    # Эмбеддинги из последнего слоя модели
    embeddings = outputs.last_hidden_state.mean(dim=1)

    return embeddings.squeeze().cpu().numpy()


def _determine_optimal_clusters(data, max_k=10):
    if len(data) < 2:
        return 1  # Минимум 1 кластер

    max_k = min(max_k, len(data))
    sse = []
    for k in range(1, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=0)
        kmeans.fit(data)
        sse.append(kmeans.inertia_)

    plt.figure()
    plt.plot(range(1, 11), sse)
    plt.xlabel('Number of Clusters')
    plt.ylabel('SSE')
    plt.title('Elbow Method For Optimal k')
    plt.savefig('elbow_method.png')
    plt.close()

    optimal_k = 3
    for i in range(1, len(sse) - 1):
        if sse[i] - sse[i + 1] < sse[i - 1] - sse[i]:
            optimal_k = i + 1
            break

    return optimal_k


def get_code_embeddings(code: str, max_tokens: int = 2048) -> np.ndarray:
    """Возвращает эмбеддинги для кода."""
    # Токенизация и разбиение на чанки
    code_chunks = [code[i : i + max_tokens] for i in range(0, len(code), max_tokens)]

    all_embeddings = []
    for code_chunk in tqdm(code_chunks, desc='Processing Chunks'):
        try:
            embedding = _get_embeddings(code_chunk)
            all_embeddings.append(embedding)
        except Exception as e:
            logger.warning(f'Ошибка при обработке чанка: {e}')

    return np.vstack(all_embeddings) if all_embeddings else np.array([])


def cluster_embeddings(
    embeddings: np.ndarray,
    num_clusters: int = 5,
    visualize: bool = True,
    save_results: bool = False,
    filename: str = 'clusters.csv',
) -> pd.DataFrame:
    """Кластеризует эмбеддинги и возвращает результаты."""
    if embeddings.size == 0:
        logger.warning('Нет данных для кластеризации.')
        return pd.DataFrame()

    # Автоматическая коррекция числа кластеров
    num_clusters = min(num_clusters, len(embeddings))
    if num_clusters < 1:
        logger.warning('Невозможно выполнить кластеризацию.')
        return pd.DataFrame()

    # Кластеризация
    kmeans = KMeans(n_clusters=num_clusters)
    clusters = kmeans.fit_predict(embeddings)

    # Визуализация
    if visualize and len(embeddings) >= 2:
        pca = PCA(n_components=2)
        reduced_embeddings = pca.fit_transform(embeddings)
        plt.scatter(
            reduced_embeddings[:, 0],
            reduced_embeddings[:, 1],
            c=clusters,
            cmap='viridis',
        )
        plt.title('Code Clusters')
        plt.savefig('clusters.png')
        plt.close()

    # Сохранение результатов
    df = pd.DataFrame({'cluster': clusters})
    if save_results:
        df.to_csv(filename, index=False)

    return df


def analyze_code(
    code: str,
    num_clusters: int = 5,
    visualize: bool = True,
    save_embeddings: bool = False,
    save_clusters: bool = False,
    embeddings_filename: str = 'embeddings.npy',
    clusters_filename: str = 'clusters.csv',
) -> pd.DataFrame:
    """
    Главная функция для анализа кода:
    1. Получает эмбеддинги для переданного кода.
    2. Кластеризует эмбеддинги.
    3. Возвращает результаты кластеризации.
    """
    # Шаг 1: Получение эмбеддингов
    logger.info('Получение эмбеддингов для кода...')
    embeddings = get_code_embeddings(code)

    if embeddings.size == 0:
        logger.error('Не удалось получить эмбеддинги.')
        return pd.DataFrame()

    # Сохранение эмбеддингов (опционально)
    if save_embeddings:
        logger.info(f'Сохранение эмбеддингов в {embeddings_filename}...')
        # save_embeddings(embeddings, embeddings_filename)

    # Шаг 2: Кластеризация
    logger.info('Кластеризация эмбеддингов...')
    df = cluster_embeddings(
        embeddings,
        num_clusters=num_clusters,
        visualize=visualize,
        save_results=save_clusters,
        filename=clusters_filename,
    )

    if df.empty:
        logger.error('Кластеризация не удалась.')
    else:
        logger.info('Кластеризация завершена успешно.')

    return df


def save_reference_clusters(df: pd.DataFrame, filename: str):
    df.to_pickle(filename)


def load_reference_clusters(filename: str) -> pd.DataFrame:
    return pd.read_pickle(filename)


def compare_clusters(new_df: pd.DataFrame, reference_df: pd.DataFrame) -> float:
    if 'cluster' not in new_df.columns or 'cluster' not in reference_df.columns:
        logger.error("Столбец 'cluster' отсутствует в DataFrame.")
        return 0.0, set()

    common_clusters = set(new_df['cluster']).intersection(set(reference_df['cluster']))
    similarity_score = len(common_clusters) / len(set(reference_df['cluster']))
    return similarity_score, common_clusters
