from pathlib import Path
from html import escape
from base64 import b64encode

import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import pandas as pd
import streamlit as st

from jogadores_semelhantes import METRICAS, buscar_semelhantes
from referencias_externas import carregar_externos, montar_referencias
from rankings import calcular_ranking
from perfis_pca import calcular_mapa_perfis
from fotos_jogadores import obter_retrato


# 1. Configuração da página
st.set_page_config(
    page_title="SCOUTAI",
    page_icon="⚽",
    layout="wide",
)

st.title("SCOUTAI")
st.write("Compare craques, explore rankings e descubra perfis ofensivos.")

estilo_cartoes = (Path(__file__).resolve().parent / "assets" / "cartao_jogador.css").read_text(encoding="utf-8")
st.html(f"<style>{estilo_cartoes}</style>")


def exibir_cartoes_comparador(comparacao, cores):
    """Apresenta os jogadores com as mesmas cores usadas nos gráficos."""
    cartoes = []
    for _, jogador in comparacao.iterrows():
        nome = escape(jogador["Jogador"])
        retrato = obter_retrato(jogador["Jogador"])
        if retrato.imagem is not None:
            imagem = b64encode(retrato.imagem).decode("ascii")
            foto = f'<img src="data:image/png;base64,{imagem}" alt="Foto de {nome}">'
            credito = f'<a href="{escape(retrato.fonte, quote=True)}" target="_blank" rel="noopener noreferrer">Foto: FotMob ↗</a>'
        else:
            foto = (
                f'<div class="scout-comparador-iniciais" role="img" aria-label="Avatar de {nome}">'
                f'{escape(retrato.iniciais)}</div>'
            )
            credito = '<span>Foto não cadastrada ou indisponível.</span>'

        cartoes.append(
            f'<article class="scout-comparador-card" aria-label="Cartão de {nome}" '
            f'style="--cor-jogador:{to_hex(cores[jogador["Jogador"]])}">'
            f'<div class="scout-comparador-retrato">{foto}</div>'
            f'<h4>{nome}</h4>'
            f'<p class="scout-comparador-clube">{escape(jogador["Clube"])}</p>'
            '<div class="scout-comparador-dados">'
            f'<span>Temporada {escape(str(jogador["Temporada"]))}</span>'
            f'<span>{int(jogador["Minutos"])} min na amostra</span></div>'
            '<p class="scout-comparador-cor"><span aria-hidden="true"></span>Cor nos gráficos</p>'
            f'<div class="scout-comparador-fonte">{credito}</div></article>'
        )

    st.html('<div class="scout-comparador-grid">' + "".join(cartoes) + '</div>')


def exibir_comparador():
    """Mostra os dados dos dois a quatro craques escolhidos."""
    st.subheader("Comparador de craques")
    st.write("Escolha de dois a quatro craques para comparar seus números.")

    arquivo = (
        Path(__file__).resolve().parent
        / "data"
        / "processed"
        / "comparacao_craques.csv"
    )

    if not arquivo.exists():
        st.error("Tabela dos craques não encontrada. Execute app.py primeiro.")
        return

    craques = pd.read_csv(arquivo)
    metricas_comparacao = [coluna for coluna in craques.columns if coluna.endswith("/90")]

    try:
        externos = carregar_externos(arquivo.parents[2])
    except (ValueError, KeyError) as erro:
        st.warning(f"Referências externas indisponíveis: {erro}")
        externos = pd.DataFrame()

    if not externos.empty:
        externos = externos.copy()
        externos["Gols/90"] = externos["Gls"] / externos["Min"] * 90
        externos["G+A/90"] = (externos["Gls"] + externos["Ast"]) / externos["Min"] * 90

    craques = montar_referencias(craques, externos)
    opcoes = sorted(craques["Player"].unique().tolist())
    padrao = [nome for nome in ["Lamine Yamal", "Erling Haaland"] if nome in opcoes]

    selecionados = st.multiselect(
        "Craques para comparar",
        options=opcoes,
        default=padrao,
        max_selections=4,
        placeholder="Escolha de dois a quatro jogadores",
    )

    if len(selecionados) < 2:
        st.info("Selecione pelo menos dois jogadores para visualizar a comparação.")
        return

    # Mantém a mesma ordem em que os jogadores foram selecionados.
    escolhidos = craques.set_index("Player").loc[selecionados].reset_index()
    colunas = ["Player", "Squad", "Temporada", "Min"] + metricas_comparacao
    comparacao = escolhidos[colunas].rename(
        columns={"Player": "Jogador", "Squad": "Clube", "Min": "Minutos"}
    )

    paleta = plt.get_cmap("tab20")
    cores = {nome: paleta(indice) for indice, nome in enumerate(opcoes)}
    exibir_cartoes_comparador(comparacao, cores)

    st.caption(
        "A temporada de cada jogador está identificada na tabela. "
        "As métricas /90 representam a produção a cada 90 minutos jogados. "
        "G+A/90 é a soma de gols e assistências por 90 minutos."
    )
    # Formata apenas a apresentação; os dados numéricos continuam em comparacao.
    exibicao = comparacao.copy()
    for metrica in metricas_comparacao:
        exibicao[metrica] = comparacao[metrica].map(
            lambda valor: f"{valor:.2f}" if pd.notna(valor) else "Não disponível"
        )

    st.dataframe(exibicao, hide_index=True, width="stretch")

    st.subheader("Comparação em gráficos")
    st.caption(
        "Cada gráfico tem sua própria escala vertical. "
        "As cores identificam os jogadores e os valores são por 90 minutos. "
        "Dados indisponíveis não são representados como zero."
    )
    for inicio in range(0, len(metricas_comparacao), 2):
        paineis = st.columns(2)
        for painel, metrica in zip(paineis, metricas_comparacao[inicio:inicio + 2]):
            with painel:
                st.write(f"**{metrica}**")
                fig, eixo = plt.subplots(figsize=(6.5, 4.2))
                valores_validos = comparacao[metrica].dropna()
                limite = max(float(valores_validos.max()) * 1.25, 0.1) if not valores_validos.empty else 1
                eixo.set_ylim(0, limite)
                eixo.set_xlim(-0.6, len(comparacao) - 0.4)

                for posicao, (_, jogador) in enumerate(comparacao.iterrows()):
                    valor = jogador[metrica]
                    if pd.isna(valor):
                        eixo.text(
                            posicao, 0.1, "Não\ndisponível",
                            transform=eixo.get_xaxis_transform(),
                            ha="center", va="bottom", fontsize=9, color="#475569",
                        )
                    else:
                        barras = eixo.bar(
                            posicao, float(valor), width=0.6,
                            color=cores[jogador["Jogador"]],
                        )
                        eixo.bar_label(barras, fmt="%.2f", padding=3)

                eixo.set_xticks(range(len(comparacao)))
                eixo.set_xticklabels(
                    comparacao["Jogador"], rotation=20, ha="right", fontsize=9,
                )
                eixo.set_ylabel("Por 90 minutos")
                eixo.grid(axis="y", alpha=0.2)
                eixo.set_axisbelow(True)
                eixo.spines[["top", "right"]].set_visible(False)
                if valores_validos.empty:
                    eixo.set_yticks([])
                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                sem_dados = comparacao.loc[comparacao[metrica].isna(), "Jogador"]
                if not sem_dados.empty:
                    st.caption(f"Não disponível em {metrica}: {', '.join(sem_dados)}.")

    ausencias = []
    for _, jogador in escolhidos.iterrows():
        for metrica in metricas_comparacao:
            if pd.isna(jogador[metrica]):
                if jogador["Externo"] and metrica == "No alvo/90":
                    motivo = (
                        "O arquivo de referências externas não contém o total de "
                        "finalizações no alvo desse jogador. Sem esse total, "
                        "não é possível calcular o valor por 90 minutos."
                    )
                else:
                    motivo = "O CSV utilizado não informa o valor necessário para esta métrica."
                ausencias.append({
                    "Jogador": jogador["Player"],
                    "Métrica": metrica,
                    "Valor": "Não disponível",
                    "Motivo": motivo,
                })

    if ausencias:
        st.write("**Por que alguns dados estão indisponíveis?**")
        for ausencia in ausencias:
            st.write(
                f"**{ausencia['Jogador']} — {ausencia['Métrica']}: "
                f"{ausencia['Valor']}.** {ausencia['Motivo']}"
            )

    externos_escolhidos = escolhidos.loc[escolhidos["Externo"]]
    if not externos_escolhidos.empty:
        st.info(
            "As referências externas têm ligas e períodos diferentes do CSV europeu "
            "2025/26. A comparação não ajusta essas diferenças e representa os "
            "períodos registrados, não o auge de cada jogador."
        )
        for _, jogador in externos_escolhidos.iterrows():
            st.caption(
                f"{jogador['Player']}: {jogador['Comp']} — {jogador['Temporada']}. "
                f"Dados consultados em {jogador['Data_consulta']}; "
                f"último jogo de liga listado: {jogador['Ultimo_jogo_liga']}. "
                "Recorte apenas da liga."
            )
            st.markdown(f"[Fonte dos dados de {jogador['Player']}]({jogador['Fonte']})")
            if jogador["Min"] < 900:
                st.warning(
                    f"{jogador['Player']} tem {int(jogador['Min'])} minutos na amostra, "
                    "abaixo do mínimo de 900 minutos usado na base de perfis europeus."
                )


def exibir_rankings():
    """Atualiza o ranking conforme o grupo elegível e os pesos escolhidos."""
    st.subheader("Rankings dos craques")
    st.write("Ajuste a importância dos gols sem pênalti e das assistências.")
    modo = st.radio(
        "Grupo do ranking",
        ["Europeu (padrão)", "Com referências externas"],
        horizontal=True,
    )
    st.caption(
        "O modo europeu usa os 16 craques do CSV 2025/26. O modo com referências "
        "externas também considera Messi, Neymar e Cristiano Ronaldo. "
        "Nos dois modos, só entram jogadores com pelo menos 900 minutos."
    )
    percentual_gols = st.slider(
        "Peso dos gols sem pênalti (%)", min_value=0, max_value=100, value=50,
        step=1, help="O peso das assistências é ajustado para a soma permanecer em 100%.",
    )
    st.write(f"**Pesos atuais: {percentual_gols}% gols e {100 - percentual_gols}% assistências.**")

    arquivo = Path(__file__).resolve().parent / "data" / "processed" / "comparacao_craques.csv"
    if not arquivo.exists():
        st.error("Tabela dos craques não encontrada. Execute app.py primeiro.")
        return

    try:
        externos = carregar_externos(arquivo.parents[2]) if modo == "Com referências externas" else pd.DataFrame()
        if modo == "Com referências externas" and externos.empty:
            st.error("Arquivo de referências externas não encontrado. Escolha o modo europeu ou restaure o arquivo.")
            return
        base = montar_referencias(pd.read_csv(arquivo), externos)
        ranking = calcular_ranking(base, peso_gols=percentual_gols / 100)
    except (ValueError, KeyError) as erro:
        st.error(f"Não foi possível calcular o ranking: {erro}")
        return

    st.caption(
        f"{len(ranking)} jogadores elegíveis. As notas de 0 a 100 são recalculadas "
        "dentro do grupo escolhido; mudar o grupo pode mudar a pontuação dos demais jogadores."
    )
    for _, jogador in base.loc[base["Min"] < 900].iterrows():
        st.info(
            f"{jogador['Player']} — não elegível neste ranking: "
            f"{int(jogador['Min'])} minutos na amostra, abaixo do mínimo de 900. "
            "Continua disponível no Comparador e na busca de semelhantes."
        )

    if not externos.empty:
        st.info(
            "Modo exploratório: os dados externos vêm de ligas e temporadas diferentes "
            "do CSV europeu. Os valores por 90 minutos ajustam o tempo jogado, "
            "mas não a dificuldade da liga, a equipe ou o período analisado."
        )
        for _, jogador in externos.iterrows():
            st.caption(
                f"{jogador['Player']}: {jogador['Comp']} — {jogador['Temporada']}. "
                f"Dados consultados em {jogador['Data_consulta']}; "
                f"último jogo de liga listado: {jogador['Ultimo_jogo_liga']}."
            )
            st.markdown(f"[Fonte do ranking: {jogador['Player']}]({jogador['Fonte']})")

    with st.expander("Como a pontuação é calculada"):
        st.write(
            "Usamos gols sem pênalti e assistências por 90 minutos. Para cada métrica, "
            "o menor valor do grupo recebe nota 0 e o maior recebe 100. "
            "Os demais ficam proporcionalmente entre esses extremos."
        )
        st.code("Nota = (valor - mínimo do grupo) / (máximo do grupo - mínimo do grupo) × 100")
        st.write(
            "Se todos tiverem o mesmo valor, todos recebem nota 50 nessa métrica. "
            "Uma nota 0 significa o menor valor deste grupo, não ausência de habilidade."
        )
        st.code(
            f"Pontuação = Nota gols × {percentual_gols / 100:.2f} "
            f"+ Nota assistências × {(100 - percentual_gols) / 100:.2f}"
        )
        st.write(
            "Pontuações iguais recebem a mesma posição. A ordem alfabética apenas "
            "organiza os nomes empatados. A normalização usa sempre o grupo elegível inteiro."
        )

    colunas = [
        "Posição", "Player", "Squad", "Temporada", "Min", "Gols sem pênalti/90", "Assistências/90",
        "Nota gols", "Nota assistências", "Pontuação",
    ]
    tabela = ranking[colunas].rename(columns={"Player": "Jogador", "Squad": "Clube", "Min": "Minutos"})
    st.dataframe(
        tabela, hide_index=True, width="stretch",
        column_config={
            coluna: st.column_config.NumberColumn(format="%.2f")
            for coluna in ["Gols sem pênalti/90", "Assistências/90", "Nota gols", "Nota assistências", "Pontuação"]
        },
    )
    exportacao = tabela.copy()
    exportacao["Modo"] = modo
    exportacao["Mínimo de minutos"] = 900
    exportacao["Peso gols (%)"] = percentual_gols
    exportacao["Peso assistências (%)"] = 100 - percentual_gols
    st.download_button(
        "Baixar ranking em CSV",
        data=exportacao.to_csv(index=False).encode("utf-8-sig"),
        file_name="ranking_craques.csv", mime="text/csv",
    )
    st.info(
        "Esta pontuação combina somente duas métricas ofensivas e depende dos pesos "
        "e dos jogadores incluídos. Não representa qualidade geral nem ajusta diferenças entre ligas e equipes. "
        "As posições usam os valores completos; notas arredondadas na tela podem parecer empatadas."
    )


def exibir_mapa_perfis(df, referencia):
    """Mostra os grupos existentes e a projeção das quatro métricas em dois eixos."""
    st.subheader("Grupos ofensivos e mapa PCA")
    try:
        mapa, variancia, resumo = calcular_mapa_perfis(df)
    except (ValueError, KeyError) as erro:
        st.error(f"Não foi possível montar o mapa dos perfis: {erro}")
        return

    st.write(
        f"A base europeia contém {len(mapa)} registros em {len(resumo)} grupos. "
        "A tabela mostra as médias originais por 90 minutos de cada grupo. "
        "Os números dos grupos são identificadores, não posições em um ranking."
    )
    st.write("**O que caracteriza cada grupo?**")
    st.caption(
        "As descrições comparam as médias dos grupos nas quatro métricas por 90 minutos. "
        "Elas não são rótulos definitivos de função tática ou qualidade."
    )
    nomes_metricas = {
        "Gols sem pênalti/90": "gols sem pênalti",
        "Assistências/90": "assistências",
        "Finalizações/90": "finalizações",
        "Cruzamentos/90": "cruzamentos",
    }
    paineis_grupos = st.columns(len(resumo))
    for painel, (_, grupo) in zip(paineis_grupos, resumo.iterrows()):
        # Os extremos são calculados das médias atuais, sem fixar rótulos nos IDs.
        maiores = [
            nomes_metricas[metrica] for metrica in METRICAS
            if resumo[metrica].nunique() > 1 and grupo[metrica] == resumo[metrica].max()
        ]
        menores = [
            nomes_metricas[metrica] for metrica in METRICAS
            if resumo[metrica].nunique() > 1 and grupo[metrica] == resumo[metrica].min()
        ]
        with painel, st.container(border=True):
            st.write(f"**Grupo {int(grupo['Grupo'])} · {int(grupo['Registros'])} registros**")
            if maiores:
                st.write("**Entre as maiores médias:** " + ", ".join(maiores) + ".")
            if menores:
                st.write("**Entre as menores médias:** " + ", ".join(menores) + ".")
            if not maiores and not menores:
                st.write("As médias deste grupo não se destacam nos extremos das métricas.")
            st.caption("São médias do grupo; cada jogador pode ter características diferentes.")

    st.dataframe(
        resumo, hide_index=True, width="stretch",
        column_config={metrica: st.column_config.NumberColumn(format="%.2f") for metrica in METRICAS},
    )
    st.caption(
        f"Os dois eixos do PCA preservam {variancia.sum() * 100:.1f}% da variância "
        "das quatro métricas padronizadas. O mapa é uma aproximação: a busca de "
        "semelhança continua usando todas as quatro métricas."
    )

    fig, eixo = plt.subplots(figsize=(11, 7))
    cores = plt.get_cmap("tab10")
    for indice, (grupo, jogadores) in enumerate(mapa.groupby("Grupo")):
        eixo.scatter(
            jogadores["Eixo 1"], jogadores["Eixo 2"],
            s=30, alpha=0.55, color=cores(indice),
            label=f"Grupo {grupo} ({len(jogadores)} registros)",
        )

    destaques = mapa.loc[mapa["Destaque"].eq(True)]
    eixo.scatter(
        destaques["Eixo 1"], destaques["Eixo 2"],
        s=100, facecolors="none", edgecolors="#0f172a", linewidths=1.2,
        label="Craques selecionados (contorno)",
    )
    if not referencia["Externo"]:
        selecionado = mapa.loc[
            mapa["Player"].eq(referencia["Player"]) & mapa["Squad"].eq(referencia["Squad"])
        ]
        eixo.scatter(
            selecionado["Eixo 1"], selecionado["Eixo 2"],
            marker="*", s=240, color="#facc15", edgecolors="#0f172a",
            linewidths=1, label="Referência selecionada", zorder=5,
        )
        for _, jogador in selecionado.iterrows():
            eixo.annotate(
                jogador["Player"], (jogador["Eixo 1"], jogador["Eixo 2"]),
                xytext=(8, 8), textcoords="offset points", fontsize=9,
            )

    eixo.set_xlabel(f"Eixo 1 — {variancia[0] * 100:.1f}% da variância")
    eixo.set_ylabel(f"Eixo 2 — {variancia[1] * 100:.1f}% da variância")
    eixo.set_title("Perfis ofensivos | Base europeia 2025/26")
    eixo.axhline(0, color="#94a3b8", linewidth=0.7, linestyle="--")
    eixo.axvline(0, color="#94a3b8", linewidth=0.7, linestyle="--")
    eixo.grid(alpha=0.15)
    eixo.set_axisbelow(True)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.legend(fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    if referencia["Externo"]:
        st.caption(
            f"{referencia['Player']} é uma referência externa e não está neste mapa. "
            "Os externos não participam do ajuste do PCA nem recebem grupo."
        )
    with st.expander("Como ler os grupos e o mapa"):
        st.write(
            "Cada ponto representa um registro de jogador, clube e competição. "
            "As cores são os grupos já calculados pelo KMeans com gols sem pênalti, "
            "assistências, finalizações e cruzamentos por 90 minutos."
        )
        st.write(
            "Antes do PCA, as métricas são padronizadas para que suas escalas possam "
            "ser comparadas. Cada eixo combina as quatro métricas; ele não representa "
            "uma nota de qualidade. Pontos próximos no desenho podem ter diferenças "
            "que ficaram fora dos dois eixos."
        )
        st.write(
            "Os grupos são exploratórios. Não há ajuste por liga ou equipe, e as "
            "quatro métricas não descrevem todo o estilo de um jogador."
        )

    st.write("**Grupos dos 16 craques**")
    st.dataframe(
        destaques[["Player", "Squad", "Grupo"]].sort_values(["Grupo", "Player"]).rename(
            columns={"Player": "Jogador", "Squad": "Clube"}
        ),
        hide_index=True, width="stretch",
    )

    st.subheader("Explore os jogadores de um grupo")
    grupo_escolhido = st.selectbox(
        "Grupo para explorar",
        options=sorted(df["Grupo"].unique().tolist()),
        format_func=lambda grupo: f"Grupo {grupo}",
        key="grupo_perfis",
    )
    integrantes = df.loc[df["Grupo"].eq(grupo_escolhido)].sort_values(
        ["Destaque", "Player", "Squad"], ascending=[False, True, True],
    )
    craques_grupo = integrantes.loc[integrantes["Destaque"].eq(True), "Player"].drop_duplicates()
    st.caption(
        f"Grupo {grupo_escolhido}: {len(integrantes)} registros, "
        f"{integrantes['Player'].nunique()} jogadores distintos e {len(craques_grupo)} craques selecionados. "
        "O filtro muda esta lista; o mapa continua mostrando todos os grupos."
    )
    if not craques_grupo.empty:
        st.write("**Craques neste grupo:** " + ", ".join(craques_grupo) + ".")
    else:
        st.write("Este grupo não contém nenhum dos 16 craques selecionados.")
    st.dataframe(
        integrantes[["Player", "Squad", "Comp", "Grupo", "Min", "Destaque"] + METRICAS].rename(
            columns={
                "Player": "Jogador", "Squad": "Clube", "Comp": "Competição",
                "Min": "Minutos", "Destaque": "Entre os 16 craques",
            }
        ),
        hide_index=True, width="stretch",
        column_config={metrica: st.column_config.NumberColumn(format="%.2f") for metrica in METRICAS},
    )


def exibir_perfis():
    """Exibe a busca e encerra apenas esta seção em caso de erro."""
    # 2. Carregamento da base
    pasta_projeto = Path(__file__).resolve().parent

    arquivo = (
        pasta_projeto
        / "data"
        / "processed"
        / "jogadores_com_grupos.csv"
    )

    if not arquivo.exists():
        st.error(
            "Base não encontrada. Execute modelo_perfis.py primeiro."
        )
        return

    df = pd.read_csv(arquivo)

    if len(df) < 2:
        st.error("Precisamos de pelo menos dois registros para comparar.")
        return

    try:
        externos = carregar_externos(pasta_projeto)
    except (ValueError, KeyError) as erro:
        st.error(f"Confira o CSV de referências externas: {erro}")
        return

    referencias = montar_referencias(df, externos)


    # 3. Escolha do jogador
    st.sidebar.header("Configurar busca")

    indices = referencias.sort_values(
        ["Player", "Squad", "Comp"]
    ).index.tolist()

    indice_padrao = next(
        (
            posicao
            for posicao, indice in enumerate(indices)
            if referencias.loc[indice, "Player"] == "Lamine Yamal"
        ),
        0,
    )


    def rotulo_jogador(indice):
        linha = referencias.loc[indice]

        return (
            f"{linha['Player']} | "
            f"{linha['Squad']} | "
            f"{linha['Comp']} | {linha['Temporada']}"
            + (" | Referência externa" if linha["Externo"] else "")
        )


    indice_escolhido = st.sidebar.selectbox(
        "Jogador de referência",
        options=indices,
        index=indice_padrao,
        format_func=rotulo_jogador,
    )

    escolhido = referencias.loc[indice_escolhido]

    quantidade = int(
        st.sidebar.number_input(
            "Quantidade de semelhantes",
            min_value=1,
            max_value=min(30, len(df) - 1),
            value=min(10, len(df) - 1),
            step=1,
        )
    )


    # 4. Busca usando a função que já criamos
    try:
        referencia, resultado = buscar_semelhantes(
            df=df,
            jogador=escolhido["Player"],
            quantidade=quantidade,
            clube=escolhido["Squad"],
            externos=externos,
        )
    except ValueError as erro:
        st.error(str(erro))
        return


    # 5. Informações do jogador de referência
    retrato = obter_retrato(referencia["Player"])
    with st.container(key="cartao_jogador"):
        identidade, fotografia = st.columns([3, 1.2], vertical_alignment="center")
        with identidade:
            st.html('<div class="scout-perfil-kicker">SCOUTAI / JOGADOR EM FOCO</div>')
            st.subheader(f"{referencia['Player']} — {referencia['Squad']}")
            st.caption(f"{referencia['Comp']} · Temporada {referencia['Temporada']}")
            coluna_minutos, coluna_grupo = st.columns(2)
            coluna_minutos.metric("Minutos na amostra", int(referencia["Min"]))
            coluna_grupo.metric(
                "Grupo",
                "Referência externa" if referencia["Externo"] else int(referencia["Grupo"]),
            )
        with fotografia:
            if retrato.imagem is not None:
                st.image(retrato.imagem, caption=f"Foto de {referencia['Player']}", width=210)
            else:
                st.html(
                    f'<div class="scout-avatar-iniciais" role="img" '
                    f'aria-label="Avatar de {escape(referencia["Player"], quote=True)}">'
                    f'{escape(retrato.iniciais)}</div>'
                )
                st.caption("Foto não cadastrada ou indisponível.")

    if retrato.fonte:
        st.caption(f"Foto de perfil: [FotMob]({retrato.fonte}). O clube e os números acima são do recorte analisado.")
    st.caption("Candidatos europeus: CSV identificado como 2025/26.")

    if referencia["Externo"]:
        st.caption(
            f"Dados consultados em {referencia['Data_consulta']}; "
            f"último jogo de liga listado: {referencia['Ultimo_jogo_liga']}. "
            "Recorte apenas da liga, sem seleção ou copas."
        )
        st.markdown(f"[Consultar fonte das estatísticas]({referencia['Fonte']})")
        if referencia["Min"] < 900:
            st.warning(
                "Esta referência tem menos de 900 minutos. "
                "A amostra é menor que o mínimo usado para selecionar os candidatos europeus."
            )
        with st.expander("Como os cruzamentos foram calculados"):
            st.write(
                f"A fonte informa {int(referencia['Cruzamentos_certos'])} cruzamentos certos "
                f"e {referencia['Acerto_cruzamentos_pct']:.1f}% de acerto. "
                f"O único total inteiro compatível com essa taxa arredondada "
                f"a uma casa decimal é {int(referencia['Crs'])}. "
                "Esse total foi reconstituído; não foi publicado diretamente como total na página."
            )
        st.caption(
            "Os três são referências para a busca; os grupos e a escala "
            "continuam calculados somente com a base europeia."
        )

    st.write("**Métricas da referência por 90 minutos**")

    tabela_referencia = referencia[METRICAS].to_frame(
        name="Valor"
    ).astype(float)

    st.dataframe(
        tabela_referencia.round(3),
        width="stretch",
    )


    # 6. Tabela dos semelhantes
    st.subheader("Jogadores mais próximos")

    st.caption(
        "Quanto menor a distância, mais próximo o perfil "
        "nas quatro métricas. A busca considera todos os grupos."
    )

    exportacao = resultado.copy()
    exportacao.insert(0, "Referência", referencia["Player"])
    exportacao.insert(1, "Clube referência", referencia["Squad"])
    exportacao.insert(2, "Temporada referência", referencia["Temporada"])
    exportacao.insert(3, "Temporada Europa", "2025/26")
    if referencia["Externo"]:
        exportacao["Fonte referência"] = referencia["Fonte"]
        exportacao["Consulta referência"] = referencia["Data_consulta"]
        exportacao["Método cruzamentos referência"] = "Reconstituídos dos certos e da taxa de acerto a uma casa decimal"

    st.dataframe(
        resultado.round(3),
        hide_index=True,
        width="stretch",
    )

    st.download_button(
        label="Baixar resultado em CSV",
        data=exportacao.to_csv(
            index=False,
        ).encode("utf-8-sig"),
        file_name="jogadores_semelhantes.csv",
        mime="text/csv",
    )


    # 7. Escolha de um resultado para comparação
    st.subheader("Comparação individual")

    if resultado.empty:
        st.info("Nenhum outro jogador disponível para comparar.")
        return

    indices_resultado = resultado.index.tolist()


    def rotulo_resultado(indice):
        linha = resultado.loc[indice]

        return f"{linha['Player']} | {linha['Squad']}"


    indice_comparacao = st.selectbox(
        "Compare a referência com:",
        options=indices_resultado,
        format_func=rotulo_resultado,
    )

    comparado = resultado.loc[indice_comparacao]


    # 8. Gráfico com um painel para cada métrica
    fig, eixos = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=(12, 8),
    )

    nomes = [
        referencia["Player"],
        comparado["Player"],
    ]

    for eixo, metrica in zip(eixos.flat, METRICAS):
        valores = [
            float(referencia[metrica]),
            float(comparado[metrica]),
        ]

        barras = eixo.bar(
            nomes,
            valores,
            color=["#2563eb", "#f59e0b"],
        )

        eixo.bar_label(
            barras,
            fmt="%.2f",
            padding=3,
        )

        eixo.set_title(metrica)
        eixo.set_ylim(0, max(max(valores) * 1.25, 0.1))
        eixo.grid(axis="y", alpha=0.2)
        eixo.set_axisbelow(True)

        eixo.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "Cada painel tem sua própria escala vertical. "
        "Os valores exibidos são as métricas originais por 90 minutos."
    )

    st.info(
        "A comparação usa gols sem pênalti, assistências, "
        "finalizações e cruzamentos. Não há ajuste por liga ou equipe. "
        "Os períodos e fornecedores dos dados podem diferir entre as referências externas "
        "e o CSV europeu. Proximidade estatística não garante a mesma qualidade "
        "ou função tática."
    )

    exibir_mapa_perfis(df, referencia)


# 9. Navegação entre as áreas do ScoutAI
aba_comparador, aba_rankings, aba_perfis = st.tabs(
    ["Comparador", "Rankings", "Perfis e semelhantes"]
)

with aba_comparador:
    exibir_comparador()

with aba_rankings:
    exibir_rankings()

with aba_perfis:
    exibir_perfis()
