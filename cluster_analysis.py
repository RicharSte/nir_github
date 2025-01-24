from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np

# Загрузка модели и токенизатора
model_name = 'Salesforce/codegen-2B-mono'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)


def analyze_code_clusters(
    code: str,
    num_clusters: int = 5,
    visualize: bool = True,
    save_results: bool = False,
    filename: str = 'clusters.csv',
):
    max_length = 2048  # Максимальная длина последовательности, поддерживаемая моделью
    tokens = tokenizer.tokenize(code)

    if len(tokens) < 2:  # Минимум 2 токена для кластеризации
        print(f'Недостаточно токенов для кластеризации. Токенов: {len(tokens)}')
        return pd.DataFrame()  # Возвращаем пустой DataFrame

    chunks = [tokens[i : i + max_length] for i in range(0, len(tokens), max_length)]
    all_embeddings = []

    for chunk in chunks:
        if len(chunk) < 2:  # Пропускать куски с недостаточным количеством токенов
            continue
        inputs = tokenizer.convert_tokens_to_ids(chunk)
        inputs = tokenizer.prepare_for_model(inputs, return_tensors='pt')

        # Получение эмбеддингов токенов
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            last_hidden_states = outputs.hidden_states[-1]

        all_embeddings.append(last_hidden_states[0].cpu().numpy())

    if not all_embeddings:  # Проверка наличия эмбеддингов
        print('Не удалось получить эмбеддинги.')
        return pd.DataFrame()  # Возвращаем пустой DataFrame

    token_embeddings = np.vstack(all_embeddings)

    if len(token_embeddings) < 2:  # Минимум 2 эмбеддинга для кластеризации
        print(
            f'Недостаточно эмбеддингов для кластеризации. Эмбеддингов: {len(token_embeddings)}'
        )
        return pd.DataFrame()  # Возвращаем пустой DataFrame

    # Определение оптимального количества кластеров с помощью метода локтя
    def determine_optimal_clusters(data):
        sse = []
        for k in range(1, 11):
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

        optimal_k = 3  # Default значение
        for i in range(1, len(sse) - 1):
            if sse[i] - sse[i + 1] < sse[i - 1] - sse[i]:
                optimal_k = i + 1
                break

        return optimal_k

    # Определение оптимального количества кластеров
    optimal_clusters = determine_optimal_clusters(token_embeddings)
    print(f'Оптимальное количество кластеров: {optimal_clusters}')

    # Кластеризация токенов с помощью KMeans
    kmeans = KMeans(n_clusters=optimal_clusters, random_state=0)
    clusters = kmeans.fit_predict(token_embeddings)

    # Визуализация кластеров с помощью PCA
    if visualize:
        pca = PCA(n_components=2)
        reduced_embeddings = pca.fit_transform(token_embeddings)

        plt.figure(figsize=(10, 10))
        for i in range(optimal_clusters):
            cluster_points = reduced_embeddings[clusters == i]
            plt.scatter(
                cluster_points[:, 0],
                cluster_points[:, 1],
                label=f'Cluster {i}',
            )

        plt.legend()
        plt.title('Token Clusters')
        plt.xlabel('PCA Component 1')
        plt.ylabel('PCA Component 2')
        plt.savefig('token_clusters.png')
        plt.close()

    # Печать токенов с их кластерами
    all_tokens = sum(chunks, [])  # Список всех токенов
    token_cluster_pairs = [
        (token, cluster) for token, cluster in zip(all_tokens, clusters)
    ]

    df = pd.DataFrame(token_cluster_pairs, columns=['Token', 'Cluster'])

    if save_results:
        df.to_csv(filename, index=False)
        print(f'Results saved to {filename}')

    return df


def save_reference_clusters(df: pd.DataFrame, filename: str):
    df.to_pickle(filename)


def load_reference_clusters(filename: str) -> pd.DataFrame:
    return pd.read_pickle(filename)


def compare_clusters(new_df: pd.DataFrame, reference_df: pd.DataFrame) -> float:
    common_clusters = set(new_df['Cluster']).intersection(set(reference_df['Cluster']))
    similarity_score = len(common_clusters) / len(set(reference_df['Cluster']))
    return similarity_score, common_clusters
