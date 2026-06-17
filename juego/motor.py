"""
motor.py
--------
Motor de datos y algoritmos del juego, escrito SOLO con numpy para que la
imagen de despliegue sea ligera (sin scikit-learn / scipy / matplotlib) y no
se quede sin memoria en planes gratuitos.

Incluye:
  - dataset_ejemplo(): clientes ficticios con duplicados y outliers a proposito.
  - escalar(): StandardScaler / MinMaxScaler manuales.
  - detectar_outliers_iqr(): metodo del rango intercuartilico.
  - kmeans(): K-Means clasico (Lloyd) con varios reinicios.
  - aglomerativo(): clustering jerarquico (enlace promedio) para datasets chicos.
  - silhouette(): Silhouette Score promedio.
  - inertia(): suma de cuadrados intra-cluster (WCSS), para el metodo del codo.
"""

from __future__ import annotations

import numpy as np

# Nombres de las columnas numericas que usa el juego.
COLUMNAS = ["Edad", "IngresoAnual_k", "PuntajeGasto"]


def dataset_ejemplo() -> dict:
    """
    Devuelve un dataset pequeño de clientes como dict de listas.

    Tiene 3 "grupos naturales" + ruido, MAS:
      - 2 filas duplicadas (para el paso de duplicados),
      - 2 outliers evidentes (para el paso de outliers).
    """
    rng = np.random.default_rng(7)

    # Tres grupos naturales (centro + dispersion).
    grupos = [
        # (edad, ingreso_k, gasto, n)
        (25, 30, 80, 10),   # jovenes, ingreso bajo, gastan mucho
        (45, 90, 25, 10),   # adultos, ingreso alto, gastan poco
        (35, 60, 55, 10),   # intermedios
    ]
    filas = []
    for edad, ing, gasto, n in grupos:
        for _ in range(n):
            filas.append([
                int(np.clip(rng.normal(edad, 4), 18, 70)),
                round(float(np.clip(rng.normal(ing, 8), 10, 150)), 1),
                int(np.clip(rng.normal(gasto, 8), 1, 100)),
            ])

    # Duplicados a proposito (copiamos 2 filas existentes).
    filas.append(list(filas[0]))
    filas.append(list(filas[10]))

    # Outliers a proposito (valores extremos).
    filas.append([69, 149.0, 99])   # cliente atipico: viejo, riquisimo, gasta todo
    filas.append([19, 12.0, 2])     # cliente atipico: muy joven, pobre, casi no gasta

    arr = np.array(filas, dtype=float)
    return {COLUMNAS[i]: arr[:, i].tolist() for i in range(len(COLUMNAS))}


def a_matriz(datos: dict, columnas: list[str]) -> np.ndarray:
    """Convierte el dict de datos en una matriz numpy con las columnas dadas."""
    return np.column_stack([np.asarray(datos[c], dtype=float) for c in columnas])


def contar_duplicados(datos: dict) -> int:
    """Cuenta filas exactamente repetidas."""
    X = a_matriz(datos, COLUMNAS)
    _, idx = np.unique(X, axis=0, return_index=True)
    return len(X) - len(idx)


def quitar_duplicados(datos: dict) -> dict:
    """Devuelve los datos sin filas repetidas (conserva el orden)."""
    X = a_matriz(datos, COLUMNAS)
    vistos = set()
    keep = []
    for i, fila in enumerate(map(tuple, X)):
        if fila not in vistos:
            vistos.add(fila)
            keep.append(i)
    return {c: [datos[c][i] for i in keep] for c in COLUMNAS}


def detectar_outliers_iqr(datos: dict, columnas: list[str], factor: float = 1.5):
    """
    Marca como outlier cualquier fila con algun valor fuera de
    [Q1 - factor*IQR, Q3 + factor*IQR] en alguna de las columnas dadas.

    Devuelve un array booleano (True = es outlier).
    """
    X = a_matriz(datos, columnas)
    mask = np.zeros(len(X), dtype=bool)
    for j in range(X.shape[1]):
        col = X[:, j]
        q1, q3 = np.percentile(col, 25), np.percentile(col, 75)
        iqr = q3 - q1
        li, ls = q1 - factor * iqr, q3 + factor * iqr
        mask |= (col < li) | (col > ls)
    return mask


def quitar_filas(datos: dict, mask_quitar: np.ndarray) -> dict:
    """Elimina las filas marcadas como True en mask_quitar."""
    keep = [i for i in range(len(mask_quitar)) if not mask_quitar[i]]
    return {c: [datos[c][i] for i in keep] for c in COLUMNAS}


def escalar(X: np.ndarray, metodo: str) -> np.ndarray:
    """Escala una matriz. metodo: 'standard', 'minmax' o 'ninguno'."""
    X = np.asarray(X, dtype=float)
    if metodo == "standard":
        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        sd[sd == 0] = 1.0
        return (X - mu) / sd
    if metodo == "minmax":
        mn = X.min(axis=0)
        mx = X.max(axis=0)
        rango = mx - mn
        rango[rango == 0] = 1.0
        return (X - mn) / rango
    return X  # 'ninguno'


def kmeans(X: np.ndarray, k: int, n_init: int = 6, max_iter: int = 100, seed: int = 42):
    """
    K-Means clasico (algoritmo de Lloyd) con varios reinicios.
    Devuelve (labels, centros, inertia) de la mejor corrida.
    """
    X = np.asarray(X, dtype=float)
    rng = np.random.default_rng(seed)
    mejor = None
    for _ in range(n_init):
        centros = X[rng.choice(len(X), k, replace=False)].copy()
        labels = np.zeros(len(X), dtype=int)
        for _ in range(max_iter):
            d = ((X[:, None, :] - centros[None, :, :]) ** 2).sum(axis=2)
            nuevos = d.argmin(axis=1)
            centros_n = np.array([
                X[nuevos == j].mean(axis=0) if np.any(nuevos == j) else centros[j]
                for j in range(k)
            ])
            if np.array_equal(nuevos, labels) and np.allclose(centros_n, centros):
                centros = centros_n
                labels = nuevos
                break
            centros, labels = centros_n, nuevos
        wcss = float(((X - centros[labels]) ** 2).sum())
        if mejor is None or wcss < mejor[2]:
            mejor = (labels, centros, wcss)
    return mejor


def aglomerativo(X: np.ndarray, k: int) -> np.ndarray:
    """
    Clustering jerarquico aglomerativo con enlace promedio (average linkage).
    Pensado para datasets chicos (el del juego). Devuelve labels.
    """
    X = np.asarray(X, dtype=float)
    n = len(X)
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))
    clusters = [[i] for i in range(n)]
    while len(clusters) > k:
        mejor = None
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                dist = D[np.ix_(clusters[a], clusters[b])].mean()
                if mejor is None or dist < mejor[0]:
                    mejor = (dist, a, b)
        _, a, b = mejor
        clusters[a] = clusters[a] + clusters[b]
        del clusters[b]
    labels = np.zeros(n, dtype=int)
    for ci, grupo in enumerate(clusters):
        for i in grupo:
            labels[i] = ci
    return labels


def silhouette(X: np.ndarray, labels: np.ndarray) -> float:
    """Silhouette Score promedio (rango -1 a 1; mas alto = mejor)."""
    X = np.asarray(X, dtype=float)
    labels = np.asarray(labels)
    grupos = np.unique(labels)
    if len(grupos) < 2:
        return 0.0
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=2))
    s = np.zeros(len(X))
    for i in range(len(X)):
        mismos = labels == labels[i]
        mismos[i] = False
        a = D[i, mismos].mean() if mismos.any() else 0.0
        b = np.inf
        for c in grupos:
            if c == labels[i]:
                continue
            m = labels == c
            if m.any():
                b = min(b, D[i, m].mean())
        s[i] = 0.0 if max(a, b) == 0 else (b - a) / max(a, b)
    return float(s.mean())


def inertia(X: np.ndarray, labels: np.ndarray) -> float:
    """Suma de cuadrados intra-cluster (WCSS). Mas bajo = mas compacto."""
    X = np.asarray(X, dtype=float)
    total = 0.0
    for c in np.unique(labels):
        pts = X[labels == c]
        if len(pts):
            total += float(((pts - pts.mean(axis=0)) ** 2).sum())
    return total


def curva_codo(X: np.ndarray, ks: list[int]):
    """Calcula inertia y silhouette para cada K (para el metodo del codo)."""
    inercias, sils = [], []
    for k in ks:
        labels, _, wcss = kmeans(X, k)
        inercias.append(wcss)
        sils.append(silhouette(X, labels))
    return inercias, sils


def k_optimo_silhouette(X: np.ndarray, ks: list[int]) -> int:
    """Devuelve el K con mayor Silhouette (la 'respuesta correcta' del juego)."""
    _, sils = curva_codo(X, ks)
    return ks[int(np.argmax(sils))]
