from pathlib import Path
import argparse

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler


def main():
    parser = argparse.ArgumentParser(description="Visualiza os perfis do SCOUTAI.")
    parser.add_argument("--sem-abrir", action="store_true")
    args = parser.parse_args()

    pasta = Path(__file__).resolve().parent
    df = pd.read_csv(pasta / "data" / "processed" / "jogadores_com_grupos.csv")
    metricas = [
        "Gols sem pênalti/90", "Assistências/90",
        "Finalizações/90", "Cruzamentos/90",
    ]

    # A mesma padronização usada no modelo permite comparar escalas diferentes.
    padronizados = pd.DataFrame(
        StandardScaler().fit_transform(df[metricas]),
        columns=metricas,
        index=df.index,
    )
    padronizados["Grupo"] = df["Grupo"]
    medias = padronizados.groupby("Grupo")[metricas].mean()

    fig, (ax_perfis, ax_jogadores) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("ScoutAI | Perfis ofensivos", fontsize=21, fontweight="bold")
    cores = plt.get_cmap("tab10")

    for indice, grupo in enumerate(medias.index):
        cor = cores(indice % 10)
        jogadores = df.loc[df["Grupo"].eq(grupo)]
        legenda = f"Grupo {grupo} ({len(jogadores)} registros)"

        ax_perfis.plot(
            range(len(metricas)), medias.loc[grupo],
            marker="o", linewidth=2, color=cor, label=legenda,
        )
        ax_jogadores.scatter(
            jogadores["Cruzamentos/90"], jogadores["Gols sem pênalti/90"],
            color=cor, alpha=0.5, s=28, label=legenda,
        )

    ax_perfis.axhline(0, color="#64748b", linestyle="--", linewidth=1)
    ax_perfis.set_xticks(range(len(metricas)))
    ax_perfis.set_xticklabels([
        "Gols sem\npênalti", "Assistências", "Finalizações", "Cruzamentos",
    ])
    ax_perfis.set_ylabel("Média do grupo em desvios padrão da base")
    ax_perfis.set_title("Perfis nas quatro métricas por 90 minutos")
    ax_perfis.legend(fontsize=9)

    destaques = df.loc[df["Destaque"].eq(True)]
    ax_jogadores.scatter(
        destaques["Cruzamentos/90"], destaques["Gols sem pênalti/90"],
        s=80, facecolors="none", edgecolors="#0f172a", linewidths=1.2,
        label="16 craques (contorno)",
    )
    ax_jogadores.set_xlabel("Cruzamentos por 90 minutos")
    ax_jogadores.set_ylabel("Gols sem pênalti por 90 minutos")
    ax_jogadores.set_title("Jogadores em duas das quatro métricas")
    ax_jogadores.legend(fontsize=9)

    for eixo in (ax_perfis, ax_jogadores):
        eixo.grid(alpha=0.2)
        eixo.set_axisbelow(True)
        eixo.spines[["top", "right"]].set_visible(False)

    fig.text(
        0.5, 0.025,
        "Esquerda: 0 representa a média da base; +1 representa um desvio padrão acima.\n"
        "Direita: cada ponto é um registro. O modelo usa quatro métricas; "
        "este painel mostra apenas duas. Sem ajuste por liga ou equipe.",
        ha="center", fontsize=9, color="#475569",
    )
    fig.tight_layout(rect=(0, 0.09, 1, 0.93))
    saida = pasta / "outputs" / "perfis_ofensivos.png"
    saida.parent.mkdir(exist_ok=True)
    fig.savefig(saida, dpi=180, bbox_inches="tight")
    print(f"Gráfico salvo em: {saida}")
    if not args.sem_abrir:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
