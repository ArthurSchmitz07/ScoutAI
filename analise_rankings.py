from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# 1. Leitura dos três rankings
pasta_projeto = Path(__file__).resolve().parent
pasta_dados = pasta_projeto / "data" / "processed"

df = pd.read_csv(pasta_dados / "rankings_craques.csv")

cenarios = [
    "Prioridade em gols",
    "Pesos iguais",
    "Prioridade em assistências",
]


# 2. Uma linha por jogador e uma coluna por cenário
posicoes = df.pivot(
    index="Player",
    columns="Cenário",
    values="Posição",
)

posicoes = posicoes[cenarios]


# 3. Quanto cada jogador varia entre os cenários
resumo = posicoes.copy()

resumo["Melhor posição"] = posicoes.min(axis=1)
resumo["Pior posição"] = posicoes.max(axis=1)

resumo["Variação"] = (
    resumo["Pior posição"] - resumo["Melhor posição"]
)

resumo = resumo.sort_values(
    ["Variação", "Melhor posição"],
    ascending=[False, True],
)

print("\nSCOUTAI — VARIAÇÃO ENTRE OS CENÁRIOS\n")
print(resumo.to_string())

destino_tabela = pasta_dados / "sensibilidade_rankings.csv"

resumo.to_csv(
    destino_tabela,
    encoding="utf-8-sig",
)


# 4. Gráfico: todos os jogadores como contexto, cinco em destaque
destaques = {
    "Harry Kane": "#2563eb",
    "Kylian Mbappé": "#dc2626",
    "Erling Haaland": "#16a34a",
    "Lamine Yamal": "#ea580c",
    "Michael Olise": "#9333ea",
}

fig, ax = plt.subplots(figsize=(12, 8))
eixo_x = list(range(len(cenarios)))

for jogador, linha in posicoes.iterrows():
    if jogador not in destaques:
        ax.plot(
            eixo_x,
            linha.to_numpy(),
            color="#d1d5db",
            linewidth=1,
            alpha=0.6,
            zorder=1,
        )

for jogador, cor in destaques.items():
    linha = posicoes.loc[jogador]

    ax.plot(
        eixo_x,
        linha.to_numpy(),
        marker="o",
        linewidth=2.5,
        color=cor,
        label=jogador,
        zorder=2,
    )

    for x, posicao in zip(eixo_x, linha):
        ax.annotate(
            str(int(posicao)),
            (x, posicao),
            xytext=(7, 5),
            textcoords="offset points",
            color=cor,
            fontweight="bold",
        )


# 5. Acabamento e exportação
ax.set_xticks(eixo_x)
ax.set_xticklabels(
    [
        "70% gols\n30% assistências",
        "50% gols\n50% assistências",
        "30% gols\n70% assistências",
    ]
)

ax.set_yticks(range(1, len(posicoes) + 1))
ax.set_ylim(len(posicoes) + 0.5, 0.5)

ax.set_title(
    "ScoutAI | Como os pesos mudam o ranking",
    fontsize=17,
    fontweight="bold",
    pad=20,
)

ax.set_ylabel("Posição entre os 16 selecionados")
ax.grid(axis="y", alpha=0.2)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.legend(
    title="Jogadores destacados",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
)

fig.text(
    0.5,
    0.02,
    "Gols sem pênalti e assistências por 90 minutos. "
    "Linhas cinza representam os demais jogadores.",
    ha="center",
    fontsize=9,
)

fig.tight_layout(rect=(0, 0.06, 1, 1))

pasta_saida = pasta_projeto / "outputs"
pasta_saida.mkdir(exist_ok=True)

destino_grafico = pasta_saida / "sensibilidade_rankings.png"

fig.savefig(destino_grafico, dpi=200, bbox_inches="tight")

print(f"\nTabela salva em: {destino_tabela}")
print(f"Gráfico salvo em: {destino_grafico}")

plt.show()