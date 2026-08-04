"""Deterministic PCA and clustering functions shared by generated and live views."""

from __future__ import annotations

import numpy as np


def standardize(matrix: np.ndarray) -> tuple[np.ndarray, list[float], list[float]]:
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds = np.where(stds == 0, 1.0, stds)
    return (matrix - means) / stds, means.tolist(), stds.tolist()


def pca_2d(matrix: np.ndarray) -> np.ndarray:
    centered = matrix - matrix.mean(axis=0)
    if centered.shape[1] == 1:
        return np.column_stack([centered[:, 0], np.zeros(len(centered))])
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[:2].T
    coords = centered @ components
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(len(coords))])
    return coords[:, :2]


def squared_distances(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)


def kmeans(matrix: np.ndarray, k: int, seed: int, iterations: int = 80) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed + k)
    if k >= len(matrix):
        labels = np.arange(len(matrix), dtype=int)
        return labels, matrix.copy()
    centers = matrix[rng.choice(len(matrix), size=k, replace=False)].copy()
    labels = np.zeros(len(matrix), dtype=int)
    for _ in range(iterations):
        distances = squared_distances(matrix, centers)
        new_labels = distances.argmin(axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for cluster in range(k):
            members = matrix[labels == cluster]
            if len(members):
                centers[cluster] = members.mean(axis=0)
            else:
                centers[cluster] = matrix[rng.integers(0, len(matrix))]
    return labels, centers


def silhouette_proxy(matrix: np.ndarray, labels: np.ndarray, centers: np.ndarray) -> float:
    own = np.linalg.norm(matrix - centers[labels], axis=1)
    distances = np.linalg.norm(matrix[:, None, :] - centers[None, :, :], axis=2)
    if centers.shape[0] > 1:
        distances[np.arange(len(matrix)), labels] = np.inf
        nearest_other = distances.min(axis=1)
    else:
        nearest_other = np.zeros(len(matrix))
    denom = np.maximum(own, nearest_other)
    scores = np.where(denom > 0, (nearest_other - own) / denom, 0.0)
    return float(scores.mean())


def pairwise_distances(matrix: np.ndarray) -> np.ndarray:
    norms = (matrix**2).sum(axis=1)
    squared = norms[:, None] + norms[None, :] - 2 * matrix @ matrix.T
    return np.sqrt(np.maximum(squared, 0.0))


def hierarchical_single_linkage_labels(matrix: np.ndarray, k_values: tuple[int, ...]) -> dict[int, np.ndarray]:
    distances = pairwise_distances(matrix)
    edges: list[tuple[float, int, int]] = []
    for left in range(len(matrix)):
        for right, distance in enumerate(distances[left, left + 1 :], start=left + 1):
            edges.append((float(distance), left, right))
    edges.sort(key=lambda item: item[0])
    parent = list(range(len(matrix)))
    sizes = [1] * len(matrix)

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    mst_edges: list[tuple[float, int, int]] = []
    for distance, left, right in edges:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            continue
        if sizes[root_left] < sizes[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        sizes[root_left] += sizes[root_right]
        mst_edges.append((distance, left, right))
        if len(mst_edges) == len(matrix) - 1:
            break
    return {k: labels_from_mst(len(matrix), mst_edges, k) for k in k_values}


def labels_from_mst(node_count: int, mst_edges: list[tuple[float, int, int]], k: int) -> np.ndarray:
    kept_edges = sorted(mst_edges, key=lambda item: item[0])[: max(0, node_count - k)]
    parent = list(range(node_count))
    sizes = [1] * node_count

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for _, left, right in kept_edges:
        root_left, root_right = find(left), find(right)
        if root_left == root_right:
            continue
        if sizes[root_left] < sizes[root_right]:
            root_left, root_right = root_right, root_left
        parent[root_right] = root_left
        sizes[root_left] += sizes[root_right]

    cluster_index: dict[int, int] = {}
    labels = np.zeros(node_count, dtype=int)
    for item in range(node_count):
        root = find(item)
        cluster_index.setdefault(root, len(cluster_index))
        labels[item] = cluster_index[root]
    return labels
