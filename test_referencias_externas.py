"""Verifica referências externas e garante que a escala continue europeia."""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from jogadores_semelhantes import METRICAS, buscar_semelhantes
from referencias_externas import carregar_externos, montar_referencias, reconstituir_cruzamentos


PASTA = Path(__file__).resolve().parent


class ReferenciasExternasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.europa = pd.read_csv(PASTA / "data/processed/jogadores_com_grupos.csv")
        cls.externos = carregar_externos(PASTA)

    def test_totais_e_metricas_reconstituidos(self):
        por_nome = self.externos.set_index("Player")
        self.assertEqual(por_nome["Crs"].to_dict(), {
            "Cristiano Ronaldo": 3, "Lionel Messi": 81, "Neymar": 66,
        })
        self.assertAlmostEqual(por_nome.loc["Neymar", METRICAS[0]], 4 / 1223 * 90)
        self.assertAlmostEqual(por_nome.loc["Lionel Messi", METRICAS[0]], 25 / 2574 * 90)
        self.assertAlmostEqual(por_nome.loc["Cristiano Ronaldo", METRICAS[0]], 7 / 783 * 90)
        for nome, total in [("Cristiano Ronaldo", 17), ("Lionel Messi", 73), ("Neymar", 22)]:
            self.assertAlmostEqual(por_nome.loc[nome, "No alvo/90"], total / por_nome.loc[nome, "Min"] * 90)
        self.assertTrue(self.externos["Grupo"].isna().all())

    def test_taxas_ambiguas_ou_invalidas_sao_rejeitadas(self):
        for certos, taxa in [(1, 0), (1, 101), (1.5, 50), (100, 10), (1, float("nan"))]:
            with self.subTest(certos=certos, taxa=taxa):
                with self.assertRaises(ValueError):
                    reconstituir_cruzamentos(certos, taxa)

    def test_externos_usam_escala_e_candidatos_apenas_europeus(self):
        original = self.europa.copy(deep=True)
        valores = self.europa[METRICAS].to_numpy()
        media = valores.mean(axis=0)
        desvio = valores.std(axis=0)
        for nome in self.externos["Player"]:
            with self.subTest(jogador=nome):
                ref, resultado = buscar_semelhantes(
                    self.europa, nome, externos=self.externos,
                )
                vetor = ref[METRICAS].to_numpy(dtype=float)
                distancias = np.linalg.norm((valores - vetor) / desvio, axis=1)
                esperados = self.europa.assign(distancia=distancias).sort_values(
                    ["distancia", "Player", "Squad", "Comp"]
                ).head(10)
                self.assertEqual(resultado["Player"].tolist(), esperados["Player"].tolist())
                np.testing.assert_allclose(resultado["Distância"], esperados["distancia"])
                self.assertFalse(resultado["Player"].isin(self.externos["Player"]).any())
                self.assertTrue(ref["Externo"])
                # O vetor usa a média europeia, sem incluir os externos no ajuste.
                np.testing.assert_allclose(
                    ((valores - media) / desvio) - ((vetor - media) / desvio),
                    (valores - vetor) / desvio,
                    atol=1e-12,
                )
        pd.testing.assert_frame_equal(self.europa, original)

    def test_busca_europeia_permanece_igual(self):
        for nome in ["Lamine Yamal", "Harry Kane"]:
            _, antes = buscar_semelhantes(self.europa, nome)
            ref, depois = buscar_semelhantes(self.europa, nome, externos=self.externos)
            pd.testing.assert_frame_equal(antes, depois)
            self.assertFalse(ref["Externo"])

    def test_referencia_externa_invalida_nao_gera_ranking(self):
        externos = self.externos.copy()
        externos.loc[externos["Player"].eq("Neymar"), METRICAS[0]] = np.nan
        with self.assertRaises(ValueError):
            buscar_semelhantes(self.europa, "Neymar", externos=externos)

    def test_comparador_externos_e_motivos_dos_dados_ausentes(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.multiselect[0].options), 19)
        nomes = ["Cristiano Ronaldo", "Lionel Messi", "Neymar", "Harry Kane"]
        app.multiselect[0].set_value(nomes).run()
        self.assertFalse(app.exception)
        aba = app.tabs[0]
        tabela = aba.dataframe[0].value.set_index("Jogador")
        motivos = [item.value for item in aba.markdown if " — No alvo/90:" in item.value]
        self.assertEqual(tabela.index.tolist(), nomes)
        self.assertEqual(motivos, [])
        for _, jogador in self.externos.iterrows():
            with self.subTest(jogador=jogador["Player"]):
                linha = tabela.loc[jogador["Player"]]
                self.assertEqual(linha["No alvo/90"], f"{jogador['SoT'] / jogador['Min'] * 90:.2f}")
                self.assertEqual(linha["Gols/90"], f"{jogador['Gls'] / jogador['Min'] * 90:.2f}")
                self.assertEqual(linha["G+A/90"], f"{(jogador['Gls'] + jogador['Ast']) / jogador['Min'] * 90:.2f}")
                self.assertEqual(linha["Temporada"], jogador["Temporada"])
        self.assertEqual(tabela.loc["Cristiano Ronaldo", "Assistências/90"], "0.00")
        fonte = pd.read_csv(PASTA / "data/processed/comparacao_craques.csv").set_index("Player")
        self.assertEqual(tabela.loc["Harry Kane", "No alvo/90"], f"{fonte.loc['Harry Kane', 'No alvo/90']:.2f}")
        self.assertTrue(any("783 minutos" in item.value for item in aba.warning))
        app.multiselect[0].set_value(["Harry Kane", "Lamine Yamal"]).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs[0].dataframe), 1)
        self.assertFalse(app.tabs[0].warning)

    def test_graficos_distinguem_ausencia_de_zero_e_preservam_cores(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest

        graficos = []

        def registrar(fig):
            eixo = fig.axes[0]
            graficos.append({
                "barras": [(barra.get_height(), barra.get_facecolor()) for barra in eixo.patches],
                "textos": [texto.get_text() for texto in eixo.texts],
            })

        # Simula uma consulta sem SoT para preservar o comportamento de ausência.
        sem_alvo = self.externos.copy()
        sem_alvo["No alvo/90"] = np.nan
        with patch("referencias_externas.carregar_externos", return_value=sem_alvo), patch("streamlit.pyplot", side_effect=registrar):
            app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
            self.assertFalse(app.exception)
            graficos.clear()
            app.multiselect[0].set_value(["Lamine Yamal", "Cristiano Ronaldo"]).run()
            self.assertFalse(app.exception)
            # As seis métricas antecedem a comparação individual e o mapa PCA.
            self.assertEqual(len(graficos), 8)
            self.assertEqual(len(graficos[4]["barras"]), 1)
            self.assertIn("Não\ndisponível", graficos[4]["textos"])
            self.assertEqual(graficos[2]["barras"][1][0], 0)
            self.assertIn("0.00", graficos[2]["textos"])
            cor_yamal = graficos[0]["barras"][0][1]
            fonte = pd.read_csv(PASTA / "data/processed/comparacao_craques.csv").set_index("Player")
            self.assertAlmostEqual(graficos[0]["barras"][0][0], fonte.loc["Lamine Yamal", "Gols/90"])

            graficos.clear()
            app.multiselect[0].set_value(["Neymar", "Lamine Yamal", "Lionel Messi", "Cristiano Ronaldo"]).run()
            self.assertFalse(app.exception)
            self.assertEqual(graficos[0]["barras"][1][1], cor_yamal)
            self.assertEqual(len(graficos[4]["barras"]), 1)
            self.assertEqual(graficos[4]["textos"].count("Não\ndisponível"), 3)

            graficos.clear()
            app.multiselect[0].set_value(["Neymar", "Lionel Messi", "Cristiano Ronaldo"]).run()
            self.assertFalse(app.exception)
            self.assertEqual(graficos[4]["barras"], [])
            self.assertEqual(graficos[4]["textos"].count("Não\ndisponível"), 3)

    def test_sot_opcional_e_totais_invalidos(self):
        from tempfile import TemporaryDirectory

        fonte = pd.read_csv(PASTA / "data/raw/referencias_externas.csv", dtype={"Temporada": str})
        with TemporaryDirectory() as temporaria:
            pasta = Path(temporaria)
            destino = pasta / "data/raw/referencias_externas.csv"
            destino.parent.mkdir(parents=True)
            fonte.drop(columns="SoT").to_csv(destino, index=False)
            self.assertTrue(carregar_externos(pasta)["No alvo/90"].isna().all())
            for valor in [-1, 0.5, float("inf"), 1000]:
                with self.subTest(valor=valor):
                    invalida = fonte.copy()
                    invalida["SoT"] = invalida["SoT"].astype(float)
                    invalida.loc[0, "SoT"] = valor
                    invalida.to_csv(destino, index=False)
                    with self.assertRaises(ValueError):
                        carregar_externos(pasta)

    def test_comparador_explica_ausencia_quando_sot_realmente_falta(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest

        externos = self.externos.copy()
        externos.loc[externos["Player"].eq("Neymar"), "No alvo/90"] = np.nan
        with patch("referencias_externas.carregar_externos", return_value=externos):
            app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
            app.multiselect[0].set_value(["Neymar", "Lionel Messi"]).run()
            self.assertFalse(app.exception)
            tabela = app.tabs[0].dataframe[0].value.set_index("Jogador")
            self.assertEqual(tabela.loc["Neymar", "No alvo/90"], "Não disponível")
            self.assertNotEqual(tabela.loc["Lionel Messi", "No alvo/90"], "Não disponível")
            motivos = [item.value for item in app.tabs[0].markdown if " — No alvo/90:" in item.value]
            self.assertEqual(len(motivos), 1)
            self.assertIn("Neymar", motivos[0])
            self.assertIn("não contém o total", motivos[0])

    def test_painel_selecao_grafico_e_quantidade(self):
        from streamlit.testing.v1 import AppTest

        referencias = montar_referencias(self.europa, self.externos)
        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        for nome in ["Cristiano Ronaldo", "Lionel Messi", "Neymar"]:
            with self.subTest(jogador=nome):
                indice = int(referencias.index[referencias["Player"].eq(nome)][0])
                app.sidebar.selectbox[0].select(indice).run()
                self.assertFalse(app.exception, [e.message for e in app.exception])
                tabela = app.tabs[2].dataframe[1].value
                self.assertEqual(len(tabela), 10)
                self.assertFalse(tabela["Player"].isin(self.externos["Player"]).any())
                self.assertEqual(app.metric[1].value, "Referência externa")
                self.assertEqual(bool(app.warning), nome == "Cristiano Ronaldo")
                comparacao = next(s for s in app.selectbox if s.label == "Compare a referência com:")
                comparacao.select(int(tabela.index[-1])).run()
                self.assertFalse(app.exception)
        app.sidebar.number_input[0].set_value(5).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs[2].dataframe[1].value), 5)


if __name__ == "__main__":
    unittest.main()
