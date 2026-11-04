"""Busca perfis próximos usando as quatro métricas do agrupamento."""

import argparse
from difflib import get_close_matches
from pathlib import Path
import re
import sys
import unicodedata

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from referencias_externas import carregar_externos, montar_referencias


METRICAS = [
    "Gols sem pênalti/90",
    "Assistências/90",
    "Finalizações/90",
    "Cruzamentos/90",
]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.strip().casefold())
    return "".join(letra for letra in texto if not unicodedata.combining(letra))


def buscar_semelhantes(df, jogador, quantidade=10, clube=None, externos=None):
    if quantidade < 1:
        raise ValueError("A quantidade precisa ser maior que zero.")

    # Reinicia o índice para manter as linhas alinhadas com a matriz numérica.
    df = df.reset_index(drop=True).copy()
    nomes = df["Player"].map(normalizar)
    externos = pd.DataFrame() if externos is None else externos
    opcoes = montar_referencias(df, externos)
    selecionado = opcoes["Player"].map(normalizar).eq(normalizar(jogador))
    if clube:
        selecionado &= opcoes["Squad"].map(normalizar).eq(normalizar(clube))
    referencias = opcoes.loc[selecionado]

    if referencias.empty:
        sugestoes = get_close_matches(jogador, opcoes["Player"].unique(), n=5, cutoff=0.3)
        raise ValueError(
            f"Jogador/clube não encontrado: {jogador}. "
            f"Confira o nome e o clube. Nomes próximos: {', '.join(sugestoes)}"
        )
    if len(referencias) > 1:
        clubes = ", ".join(referencias["Squad"].unique())
        raise ValueError(
            f"Há vários registros para {jogador}: {clubes}. "
            "Informe --clube para escolher um registro."
        )

    valores = df[METRICAS].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(valores.to_numpy()).all():
        raise ValueError("Existem métricas ausentes ou infinitas na base.")

    # Ajuste SOMENTE na Europa; os externos não mudam a escala nem os grupos.
    padronizador = StandardScaler()
    matriz = padronizador.fit_transform(valores)
    referencia = referencias.iloc[0]
    valores_referencia = referencia[METRICAS].to_frame().T.apply(pd.to_numeric, errors="raise")
    if not np.isfinite(valores_referencia.to_numpy(dtype=float)).all():
        raise ValueError("Existem métricas inválidas no jogador de referência.")
    vetor_referencia = padronizador.transform(valores_referencia)[0]

    # Distância euclidiana: raiz da soma dos quadrados das diferenças.
    diferencas = matriz - vetor_referencia
    df["Distância"] = np.sqrt((diferencas ** 2).sum(axis=1))

    # Remove também eventuais registros do mesmo nome em outros clubes.
    candidatos = df.loc[~nomes.eq(normalizar(referencia["Player"]))]
    resultado = (
        candidatos.sort_values(["Distância", "Player", "Squad", "Comp"])
        .head(quantidade)
        .copy()
    )
    resultado.insert(0, "Posição", range(1, len(resultado) + 1))
    colunas = ["Posição", "Player", "Squad", "Comp", "Min", "Grupo", "Distância"]
    return referencia, resultado[colunas + METRICAS]


def main():
    # Preserva os acentos dos nomes também no terminal do Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jogador", nargs="?", default="Lamine Yamal")
    parser.add_argument("--quantidade", type=int, default=10)
    parser.add_argument("--clube", help="Clube do jogador quando houver vários registros.")
    parser.add_argument("--sem-salvar", action="store_true")
    args = parser.parse_args()

    pasta = Path(__file__).resolve().parent
    arquivo = pasta / "data" / "processed" / "jogadores_com_grupos.csv"
    if not arquivo.exists():
        parser.error("Execute modelo_perfis.py primeiro para gerar a base com grupos.")
    df = pd.read_csv(arquivo)
    try:
        externos = carregar_externos(pasta)
        referencia, resultado = buscar_semelhantes(
            df, args.jogador, args.quantidade, args.clube, externos=externos,
        )
    except ValueError as erro:
        parser.error(str(erro))

    print("\nSCOUTAI — JOGADORES SEMELHANTES\n")
    print(f"Referência: {referencia['Player']} | {referencia['Squad']}")
    grupo = "Referência externa" if referencia["Externo"] else referencia["Grupo"]
    print(f"Minutos: {referencia['Min']} | Grupo: {grupo}")
    print(f"Temporada: {referencia['Temporada']} | Base europeia: 2025/26")
    if referencia["Externo"]:
        print(f"Fonte: {referencia['Fonte']} | Consulta: {referencia['Data_consulta']}")
        print("Cruzamentos totais reconstituídos dos certos e da taxa de acerto publicada.")
        if referencia["Min"] < 900:
            print("Atenção: referência externa com menos de 900 minutos na amostra.")
    print("\nMétricas da referência (por 90 minutos):")
    print(referencia[METRICAS].to_string(float_format=lambda valor: f"{valor:.3f}"))
    print("\nQuanto menor a distância, mais próximo o perfil nas quatro métricas.\n")
    print(resultado.to_string(index=False, float_format=lambda valor: f"{valor:.3f}"))
    print("\nBusca em todos os grupos. Distância não é porcentagem de semelhança.")
    print("Sem ajuste por liga ou equipe; proximidade estatística não garante qualidade ou função tática.")

    if not args.sem_salvar:
        nome = normalizar(f"{referencia['Player']} {referencia['Squad']}")
        nome = re.sub(r"[^a-z0-9]+", "_", nome).strip("_")
        destino = pasta / "outputs" / f"semelhantes_{nome}.csv"
        destino.parent.mkdir(exist_ok=True)
        exportacao = resultado.copy()
        exportacao.insert(0, "Referência", referencia["Player"])
        exportacao.insert(1, "Clube referência", referencia["Squad"])
        exportacao.insert(2, "Temporada referência", referencia["Temporada"])
        exportacao.insert(3, "Temporada Europa", "2025/26")
        if referencia["Externo"]:
            exportacao["Fonte referência"] = referencia["Fonte"]
            exportacao["Consulta referência"] = referencia["Data_consulta"]
            exportacao["Método cruzamentos referência"] = "Reconstituídos dos certos e da taxa de acerto a uma casa decimal"
        exportacao.to_csv(destino, index=False, encoding="utf-8-sig")
        print(f"\nTabela salva em: {destino}")


if __name__ == "__main__":
    main()
