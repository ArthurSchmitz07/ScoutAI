from pathlib import Path

import pandas as pd


# 1. Carregamento dos dados
pasta_projeto = Path(__file__).resolve().parent
caminho = pasta_projeto / "data" / "raw" / "players_data-2025_2026.csv"

df = pd.read_csv(caminho)


# 2. Seleção exata dos jogadores e das colunas necessárias
jogadores = [
    "Lamine Yamal",
    "Kylian Mbappé",
    "Erling Haaland",
    "Harry Kane",
    "Michael Olise",
    "Vinicius Júnior",
    "Raphinha",
    "Ousmane Dembélé",
    "Mohamed Salah",
    "Bukayo Saka",
    "Robert Lewandowski",
    "Cole Palmer",
    "Lautaro Martínez",
    "Julián Álvarez",
    "Khvicha Kvaratskhelia",
    "Luis Díaz"
]

colunas = [
    "Player",
    "Squad",
    "Comp",
    "Min",
    "Gls",
    "G-PK",
    "Ast",
    "Sh",
    "SoT",
]

craques = df.loc[df["Player"].isin(jogadores), colunas].copy()

# Confere se todos os jogadores foram encontrados
nao_encontrados = set(jogadores) - set(craques["Player"])

if nao_encontrados:
    print("\nNomes que precisam ser conferidos:")

    for nome in sorted(nao_encontrados):
        print(f"- {nome}")

    raise ValueError("Ajuste os nomes da lista conforme o CSV.")


# Evita comparar registros repetidos sem investigar sua origem
if craques["Player"].duplicated().any():
    raise ValueError("Há jogadores com mais de um registro na seleção.")

# Confere as informações necessárias para os cálculos
colunas_numericas = ["Min", "Gls", "G-PK", "Ast", "Sh", "SoT"]

craques[colunas_numericas] = craques[colunas_numericas].apply(
    pd.to_numeric,
    errors="raise",
)

if craques[colunas_numericas].isna().any().any():
    raise ValueError("Existem dados ausentes nas métricas selecionadas.")

if (craques["Min"] <= 0).any():
    raise ValueError("Existem jogadores sem minutos válidos.")


# 3. Cálculo das métricas por 90 minutos
metricas = {
    "Gls": "Gols/90",
    "G-PK": "Gols sem pênalti/90",
    "Ast": "Assistências/90",
    "Sh": "Finalizações/90",
    "SoT": "No alvo/90",
}

for coluna_original, coluna_nova in metricas.items():
    craques[coluna_nova] = (
        craques[coluna_original] / craques["Min"] * 90
    )

craques["G+A/90"] = (
    (craques["Gls"] + craques["Ast"]) / craques["Min"] * 90
)


# 4. Organização da tabela comparativa
colunas_comparacao = [
    "Player",
    "Squad",
    "Min",
    "Gols/90",
    "Gols sem pênalti/90",
    "Assistências/90",
    "Finalizações/90",
    "No alvo/90",
    "G+A/90",
]

comparacao = (
    craques[colunas_comparacao]
    .sort_values("Gols sem pênalti/90", ascending=False)
    .reset_index(drop=True)
)

print("\nSCOUTAI — COMPARAÇÃO DOS CRAQUES\n")
print(
    comparacao.to_string(
        index=False,
        float_format=lambda valor: f"{valor:.2f}",
    )
)


# 5. Exportação dos resultados
pasta_saida = pasta_projeto / "data" / "processed"
pasta_saida.mkdir(parents=True, exist_ok=True)

arquivo_saida = pasta_saida / "comparacao_craques.csv"

comparacao.to_csv(
    arquivo_saida,
    index=False,
    encoding="utf-8-sig",
)

print(f"\nTabela salva em: {arquivo_saida}")