"""Prepara três referências externas sem alterar a população europeia."""

from pathlib import Path
import math

import numpy as np
import pandas as pd


NOMES = {"Cristiano Ronaldo", "Lionel Messi", "Neymar"}


def reconstituir_cruzamentos(certos, percentual):
    """Exige um único total compatível com a taxa arredondada a uma casa.

    Não confunde cruzamentos certos com totais e não escolhe um valor
    arbitrário quando a taxa publicada permite vários denominadores.
    """
    if not math.isfinite(certos) or not math.isfinite(percentual):
        raise ValueError("Cruzamentos e percentual precisam ser finitos.")
    if certos <= 0 or certos != int(certos) or not 0 < percentual <= 100:
        raise ValueError("Não é possível reconstituir este total de cruzamentos.")
    inferior = percentual - 0.05
    superior = percentual + 0.05
    if inferior <= 0:
        raise ValueError("Taxa de cruzamentos insuficiente para obter um total único.")
    inicio = max(int(certos), math.floor(100 * certos / superior))
    fim = math.ceil(100 * certos / inferior)
    candidatos = [
        total for total in range(inicio, fim + 1)
        if inferior <= 100 * certos / total < superior
    ]
    if len(candidatos) != 1:
        raise ValueError("Taxa de cruzamentos ambígua: confirme o total na fonte.")
    return candidatos[0]


def carregar_externos(pasta_projeto=None):
    pasta = Path(pasta_projeto) if pasta_projeto else Path(__file__).resolve().parent
    caminho = pasta / "data" / "raw" / "referencias_externas.csv"
    if not caminho.exists():
        return pd.DataFrame()
    df = pd.read_csv(caminho, dtype={"Temporada": str})
    if set(df["Player"]) != NOMES or len(df) != 3:
        raise ValueError("O CSV externo deve conter uma linha para cada um dos três jogadores.")
    numericas = ["Min", "Gls", "PK", "Ast", "Sh", "Cruzamentos_certos", "Acerto_cruzamentos_pct"]
    df[numericas] = df[numericas].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(df[numericas].to_numpy()).all():
        raise ValueError("Existem dados externos ausentes ou infinitos.")
    if (df[numericas] < 0).any().any() or (df["Min"] <= 0).any():
        raise ValueError("Estatísticas externas inválidas.")
    if (df["PK"] > df["Gls"]).any():
        raise ValueError("Gols de pênalti não podem superar os gols totais.")
    # Arquivos antigos podem não ter SoT. Ausência continua sendo ausência, não zero.
    if "SoT" not in df:
        df["SoT"] = np.nan
    df["SoT"] = pd.to_numeric(df["SoT"], errors="raise")
    informados = df["SoT"].notna()
    if (
        not np.isfinite(df.loc[informados, "SoT"]).all()
        or (df.loc[informados, "SoT"] < 0).any()
        or (df.loc[informados, "SoT"] > df.loc[informados, "Sh"]).any()
        or (df.loc[informados, "SoT"] % 1 != 0).any()
    ):
        raise ValueError("Finalizações no alvo devem ser totais inteiros entre zero e as finalizações.")
    df["Crs"] = [
        reconstituir_cruzamentos(certos, percentual)
        for certos, percentual in zip(df["Cruzamentos_certos"], df["Acerto_cruzamentos_pct"])
    ]
    df["Gols sem pênalti/90"] = (df["Gls"] - df["PK"]) / df["Min"] * 90
    for coluna, metrica in [
        ("Ast", "Assistências/90"),
        ("Sh", "Finalizações/90"),
        ("SoT", "No alvo/90"),
        ("Crs", "Cruzamentos/90"),
    ]:
        df[metrica] = df[coluna] / df["Min"] * 90
    df["Externo"] = True
    # Os grupos existentes foram aprendidos apenas com a população europeia.
    df["Grupo"] = pd.NA
    return df


def montar_referencias(europa, externos):
    europeus = europa.copy()
    europeus["Externo"] = False
    if "Temporada" not in europeus:
        europeus["Temporada"] = "2025/26"
    if externos.empty:
        return europeus.reset_index(drop=True)
    return pd.concat([europeus, externos], ignore_index=True)
