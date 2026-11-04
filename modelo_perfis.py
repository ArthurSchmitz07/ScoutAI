from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# 1. Carregamento das características dos jogadores
pasta_projeto = Path(__file__).resolve().parent
pasta_dados = pasta_projeto / "data" / "processed"

df = pd.read_csv(pasta_dados / "perfis_ofensivos.csv")

metricas = [
    "Gols sem pênalti/90",
    "Assistências/90",
    "Finalizações/90",
    "Cruzamentos/90",
]

X = df[metricas]


# 2. Padronização das métricas
padronizador = StandardScaler()
X_padronizado = padronizador.fit_transform(X)


# 3. Experimentos com diferentes quantidades de grupos
avaliacoes = []
modelos = {}

for quantidade_grupos in range(2, 7):
    modelo = KMeans(
        n_clusters=quantidade_grupos,
        random_state=42,
        n_init=20,
    )

    grupos = modelo.fit_predict(X_padronizado)

    silhueta = silhouette_score(
        X_padronizado,
        grupos,
    )

    tamanhos = pd.Series(grupos).value_counts()

    avaliacoes.append({
        "Grupos": quantidade_grupos,
        "Silhueta": silhueta,
        "Menor grupo": tamanhos.min(),
        "Maior grupo": tamanhos.max(),
    })

    modelos[quantidade_grupos] = modelo

avaliacao = (
    pd.DataFrame(avaliacoes)
    .sort_values("Silhueta", ascending=False)
    .reset_index(drop=True)
)

print("\nSCOUTAI — AVALIAÇÃO DOS AGRUPAMENTOS\n")
print(
    avaliacao.to_string(
        index=False,
        float_format=lambda valor: f"{valor:.3f}",
    )
)


# 4. Seleção provisória pela maior silhueta
melhor_k = int(avaliacao.loc[0, "Grupos"])
modelo_escolhido = modelos[melhor_k]

# Somamos 1 apenas para exibir grupos começando em 1
df["Grupo"] = modelo_escolhido.labels_ + 1

print(f"\nQuantidade provisória de grupos: {melhor_k}")


# 5. Interpretação pelas médias nas unidades originais
medias = df.groupby("Grupo")[metricas].mean()
quantidades = df.groupby("Grupo").size().rename("Registros")

resumo = medias.join(quantidades)

print("\nMÉDIAS POR GRUPO\n")
print(
    resumo.to_string(
        float_format=lambda valor: f"{valor:.2f}",
    )
)


# 6. Localização dos nossos craques nos grupos
destaques = (
    df.loc[
        df["Destaque"].eq(True),
        ["Player", "Squad", "Min", "Grupo"] + metricas,
    ]
    .sort_values(["Grupo", "Player"])
)

print("\nGRUPOS DOS CRAQUES\n")
print(
    destaques.to_string(
        index=False,
        float_format=lambda valor: f"{valor:.2f}",
    )
)


# 7. Exportação dos resultados
arquivos = {
    "avaliacao_grupos.csv": avaliacao,
    "jogadores_com_grupos.csv": df,
    "resumo_grupos.csv": resumo.reset_index(),
}

for nome, tabela in arquivos.items():
    destino = pasta_dados / nome

    tabela.to_csv(
        destino,
        index=False,
        encoding="utf-8-sig",
    )

print("\nAvaliação, jogadores e resumo dos grupos foram salvos.")