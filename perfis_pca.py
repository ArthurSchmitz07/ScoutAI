"""Projeta a base europeia em dois eixos, preservando os grupos existentes."""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from jogadores_semelhantes import METRICAS


def calcular_mapa_perfis(df):
    if len(df) < 2:
        raise ValueError("O mapa precisa de pelo menos dois registros.")
    if "Externo" in df and df["Externo"].any():
        raise ValueError("O PCA deve ser ajustado somente na base europeia.")

    valores = df[METRICAS].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(valores.to_numpy()).all():
        raise ValueError("Há métricas ausentes ou infinitas na base do PCA.")
    padronizados = StandardScaler().fit_transform(valores)
    if not np.any(padronizados):
        raise ValueError("As métricas não variam entre os registros; não há um mapa PCA interpretável.")

    pca = PCA(n_components=2, svd_solver="full")
    coordenadas = pca.fit_transform(padronizados)
    mapa = df[["Player", "Squad", "Comp", "Min", "Grupo", "Destaque"]].reset_index(drop=True).copy()
    mapa["Eixo 1"] = coordenadas[:, 0]
    mapa["Eixo 2"] = coordenadas[:, 1]
    resumo = df.groupby("Grupo")[METRICAS].mean()
    resumo.insert(0, "Registros", df.groupby("Grupo").size())
    return mapa, pca.explained_variance_ratio_.copy(), resumo.reset_index()
