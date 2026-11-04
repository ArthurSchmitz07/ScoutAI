from pathlib import Path

import pandas as pd


# 1. Carregamento das bases
pasta_projeto = Path(__file__).resolve().parent
pasta_dados = pasta_projeto / "data"

df = pd.read_csv(
    pasta_dados / "raw" / "players_data-2025_2026.csv"
)

craques = pd.read_csv(
    pasta_dados / "processed" / "comparacao_craques.csv"
)

nomes_destaque = craques["Player"].tolist()


# 2. Seleção da população
eh_atacante = df["Pos"].str.contains(
    "FW",
    case=False,
    na=False,
    regex=False,
)

eh_destaque = df["Player"].isin(nomes_destaque)

colunas = [
    "Player",
    "Squad",
    "Comp",
    "Pos",
    "Min",
    "G-PK",
    "Ast",
    "Sh",
    "Crs",
]

base = df.loc[eh_atacante | eh_destaque, colunas].copy()

print(f"Registros no recorte inicial: {len(base)}")


# 3. Conferência dos números e filtro de minutos
numericas = ["Min", "G-PK", "Ast", "Sh", "Crs"]

base[numericas] = base[numericas].apply(
    pd.to_numeric,
    errors="raise",
)

# Não substituímos dados ausentes por zero
incompletos = base[numericas].isna().any(axis=1)

print(f"Registros removidos por dados ausentes: {incompletos.sum()}")

base = base.loc[~incompletos].copy()
base = base.loc[base["Min"] >= 900].copy()

if base.empty:
    raise ValueError("Nenhum jogador passou pelos filtros.")

if (base[numericas] < 0).any().any():
    raise ValueError("Há valores negativos nas estatísticas selecionadas.")

chave = ["Player", "Squad", "Comp"]

if base.duplicated(subset=chave).any():
    raise ValueError("Há registros repetidos de jogador, clube e competição.")


# 4. Métricas por 90 minutos
metricas = {
    "G-PK": "Gols sem pênalti/90",
    "Ast": "Assistências/90",
    "Sh": "Finalizações/90",
    "Crs": "Cruzamentos/90",
}

for origem, destino in metricas.items():
    base[destino] = base[origem] / base["Min"] * 90

base["Destaque"] = base["Player"].isin(nomes_destaque)

colunas_saida = [
    "Player",
    "Squad",
    "Comp",
    "Pos",
    "Min",
    "Destaque",
] + list(metricas.values())

perfis = (
    base[colunas_saida]
    .sort_values(["Player", "Squad", "Comp"])
    .reset_index(drop=True)
)


# 5. Resumo e exportação
print(f"\nRegistros elegíveis: {len(perfis)}")
print(f"Craques presentes: {perfis['Player'].isin(nomes_destaque).groupby(perfis['Player']).any().sum()}")

print("\nDistribuição por competição:")
print(perfis["Comp"].value_counts().to_string())

print("\nResumo das métricas:")
print(
    perfis[list(metricas.values())]
    .describe()
    .round(2)
    .to_string()
)

ausentes = set(nomes_destaque) - set(perfis["Player"])

if ausentes:
    print(f"\nCraques que não passaram pelos filtros: {sorted(ausentes)}")

pasta_saida = pasta_dados / "processed"
pasta_saida.mkdir(parents=True, exist_ok=True)

arquivo_saida = pasta_saida / "perfis_ofensivos.csv"

perfis.to_csv(
    arquivo_saida,
    index=False,
    encoding="utf-8-sig",
)

print(f"\nBase salva em: {arquivo_saida}")