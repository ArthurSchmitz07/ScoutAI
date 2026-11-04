from pathlib import Path
import math

import numpy as np
import pandas as pd


METRICAS_RANKING = {
    "Gols sem pênalti/90": "Nota gols",
    "Assistências/90": "Nota assistências",
}


def calcular_ranking(df, peso_gols=0.5, minimo_minutos=900):
    """Normaliza as duas métricas e combina notas com pesos complementares."""
    if not math.isfinite(peso_gols) or not 0 <= peso_gols <= 1:
        raise ValueError("O peso dos gols deve estar entre 0 e 1.")

    ranking = df.copy()
    numericas = ["Min"] + list(METRICAS_RANKING)
    ranking[numericas] = ranking[numericas].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(ranking[numericas].to_numpy()).all():
        raise ValueError("Existem minutos ou métricas ausentes ou infinitos no ranking.")
    if (ranking[numericas] < 0).any().any():
        raise ValueError("Minutos e métricas do ranking não podem ser negativos.")

    ranking = ranking.loc[ranking["Min"] >= minimo_minutos].copy()
    if ranking.empty:
        raise ValueError("Nenhum craque atingiu o mínimo de minutos para o ranking.")

    for metrica, nota in METRICAS_RANKING.items():
        minimo = ranking[metrica].min()
        maximo = ranking[metrica].max()
        # Uma métrica em que todos empatam não diferencia os jogadores.
        ranking[nota] = 50.0 if maximo == minimo else (
            (ranking[metrica] - minimo) / (maximo - minimo) * 100
        )

    ranking["Pontuação"] = (
        ranking["Nota gols"] * peso_gols
        + ranking["Nota assistências"] * (1 - peso_gols)
    )
    ranking = ranking.sort_values(
        ["Pontuação", "Player"], ascending=[False, True],
    ).reset_index(drop=True)
    ranking["Posição"] = ranking["Pontuação"].rank(method="min", ascending=False).astype(int)
    return ranking


def main():
    pasta_dados = Path(__file__).resolve().parent / "data" / "processed"
    df = pd.read_csv(pasta_dados / "comparacao_craques.csv")
    cenarios = {
        "Prioridade em gols": 0.70,
        "Pesos iguais": 0.50,
        "Prioridade em assistências": 0.30,
    }
    colunas = [
        "Posição", "Player", "Min", "Gols sem pênalti/90",
        "Assistências/90", "Pontuação",
    ]
    resultados = []

    for nome, peso in cenarios.items():
        ranking = calcular_ranking(df, peso_gols=peso)
        ranking["Cenário"] = nome
        print(f"\nSCOUTAI — {nome.upper()}\n")
        print(ranking[colunas].to_string(index=False, float_format=lambda valor: f"{valor:.2f}"))
        resultados.append(ranking[["Cenário"] + colunas])

    destino = pasta_dados / "rankings_craques.csv"
    pd.concat(resultados, ignore_index=True).to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"\nRankings salvos em: {destino}")


if __name__ == "__main__":
    main()
