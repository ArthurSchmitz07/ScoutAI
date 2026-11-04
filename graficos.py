from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# 1. Carregamento e ordenação
pasta_projeto = Path(__file__).resolve().parent
arquivo = pasta_projeto / "data" / "processed" / "comparacao_craques.csv"

df = pd.read_csv(arquivo)
df = df.sort_values(
    "Gols sem pênalti/90",
    ascending=False,
).reset_index(drop=True)

metricas = [
    "Gols sem pênalti/90",
    "Assistências/90",
    "Finalizações/90",
    "No alvo/90",
]


# 2. Preparação do mapa de calor
valores = df.set_index("Player")[metricas]

# Cada coluna recebe sua própria escala de cores entre 0 e 1.
# Os números exibidos nas células continuam sendo os valores reais.
minimos = valores.min()
amplitudes = valores.max() - minimos

normalizados = (
    (valores - minimos)
    / amplitudes.replace(0, float("nan"))
).fillna(0)


# 3. Figura com dois painéis
fig, (ax_barras, ax_mapa) = plt.subplots(
    nrows=1,
    ncols=2,
    figsize=(19, 11),
    gridspec_kw={"width_ratios": [1, 1.25]},
)

fig.suptitle(
    "ScoutAI | Comparação de 16 craques",
    fontsize=22,
    fontweight="bold",
)


# 4. Barras horizontais
posicoes = list(range(len(df)))
altura = 0.36

barras_gols = ax_barras.barh(
    [posicao - altura / 2 for posicao in posicoes],
    df["Gols sem pênalti/90"],
    height=altura,
    color="#2563eb",
    label="Gols sem pênalti/90",
)

barras_assistencias = ax_barras.barh(
    [posicao + altura / 2 for posicao in posicoes],
    df["Assistências/90"],
    height=altura,
    color="#f59e0b",
    label="Assistências/90",
)

ax_barras.bar_label(barras_gols, fmt="%.2f", padding=3, fontsize=8)
ax_barras.bar_label(
    barras_assistencias,
    fmt="%.2f",
    padding=3,
    fontsize=8,
)

ax_barras.set_yticks(posicoes)
ax_barras.set_yticklabels(df["Player"])
ax_barras.invert_yaxis()
ax_barras.set_xlim(
    0,
    df[metricas[:2]].max().max() * 1.25,
)

ax_barras.set_title("Gols sem pênalti e assistências", pad=15)
ax_barras.set_xlabel("Média por 90 minutos")
ax_barras.legend(loc="lower right")
ax_barras.grid(axis="x", alpha=0.2)
ax_barras.set_axisbelow(True)

for lado in ["top", "right", "left"]:
    ax_barras.spines[lado].set_visible(False)


# 5. Mapa de calor
imagem = ax_mapa.imshow(
    normalizados.to_numpy(),
    cmap="Blues",
    aspect="auto",
    vmin=0,
    vmax=1,
)

ax_mapa.set_yticks(posicoes)
ax_mapa.set_yticklabels(df["Player"])

ax_mapa.set_xticks(range(len(metricas)))
ax_mapa.set_xticklabels(
    [
        "Gols sem\npênalti/90",
        "Assistências/90",
        "Finalizações/90",
        "No alvo/90",
    ]
)

ax_mapa.set_title("Perfil estatístico dos jogadores", pad=15)
ax_mapa.tick_params(axis="both", length=0)

# Escreve o valor real em cada célula
for linha in range(len(valores)):
    for coluna in range(len(metricas)):
        valor = valores.iloc[linha, coluna]
        intensidade = normalizados.iloc[linha, coluna]

        ax_mapa.text(
            coluna,
            linha,
            f"{valor:.2f}",
            ha="center",
            va="center",
            color="white" if intensidade > 0.6 else "#172554",
            fontsize=10,
        )

barra_cores = fig.colorbar(
    imagem,
    ax=ax_mapa,
    fraction=0.035,
    pad=0.03,
)

barra_cores.set_label(
    "Escala por coluna: 0 = menor valor; 1 = maior valor entre os 16"
)


# 6. Exportação
fig.text(
    0.5,
    0.025,
    "Fonte: CSV do projeto, identificado como 2025/26. "
    "Valores por 90 minutos, sem ajuste por liga ou equipe.\n"
    f"Minutos na amostra: de {df['Min'].min():,.0f} "
    f"a {df['Min'].max():,.0f}.",
    ha="center",
    fontsize=10,
    color="#555555",
)

fig.tight_layout(rect=(0, 0.07, 1, 0.94))

pasta_saida = pasta_projeto / "outputs"
pasta_saida.mkdir(exist_ok=True)

destino = pasta_saida / "comparacao_16_craques.png"
fig.savefig(destino, dpi=200, bbox_inches="tight")

print(f"Gráfico salvo em: {destino}")

plt.show()