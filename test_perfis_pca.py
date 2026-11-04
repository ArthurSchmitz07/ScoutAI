from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from jogadores_semelhantes import METRICAS
from perfis_pca import calcular_mapa_perfis


PASTA = Path(__file__).resolve().parent


class PerfisPCATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = pd.read_csv(PASTA / "data/processed/jogadores_com_grupos.csv")

    def test_projecao_e_variancia_conferidas_por_svd(self):
        original = self.base.copy(deep=True)
        mapa, variancia, resumo = calcular_mapa_perfis(self.base)
        valores = self.base[METRICAS].to_numpy()
        padronizados = (valores - valores.mean(axis=0)) / valores.std(axis=0)
        u, s, _ = np.linalg.svd(padronizados, full_matrices=False)
        np.testing.assert_allclose(variancia, s[:2] ** 2 / (s ** 2).sum())
        esperado = u[:, :2] * s[:2]
        projetado = mapa[["Eixo 1", "Eixo 2"]].to_numpy()
        # Distâncias independem de uma eventual inversão do sinal dos eixos.
        np.testing.assert_allclose(
            np.linalg.norm(projetado - projetado[0], axis=1),
            np.linalg.norm(esperado - esperado[0], axis=1), atol=1e-10,
        )
        self.assertEqual(len(mapa), 384)
        self.assertEqual(int(mapa["Destaque"].sum()), 16)
        self.assertEqual(resumo["Registros"].sum(), len(self.base))
        self.assertEqual(resumo["Grupo"].tolist(), [1, 2, 3])
        pd.testing.assert_series_equal(mapa["Grupo"], self.base["Grupo"])
        pd.testing.assert_frame_equal(self.base, original)

    def test_externos_ausencias_e_base_sem_variacao_sao_rejeitados(self):
        externa = self.base.copy()
        externa["Externo"] = False
        externa.loc[0, "Externo"] = True
        invalida = self.base.copy()
        invalida.loc[0, METRICAS[0]] = np.nan
        constante = self.base.copy()
        constante[METRICAS] = 1.0
        for caso in [externa, invalida, constante, self.base.head(1)]:
            with self.assertRaises(ValueError):
                calcular_mapa_perfis(caso)

    def test_filtro_mostra_integrantes_e_craques_do_grupo_correto(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        mapa_original = app.tabs[2].dataframe[2].value.copy()
        for grupo in [1, 2, 3]:
            with self.subTest(grupo=grupo):
                app.selectbox(key="grupo_perfis").select(grupo).run()
                self.assertFalse(app.exception)
                tabela = app.tabs[2].dataframe[4].value
                fonte = self.base.loc[self.base["Grupo"].eq(grupo)].sort_values(
                    ["Destaque", "Player", "Squad"], ascending=[False, True, True],
                )
                self.assertEqual(len(tabela), len(fonte))
                self.assertTrue(tabela["Grupo"].eq(grupo).all())
                self.assertEqual(tabela["Jogador"].tolist(), fonte["Player"].tolist())
                self.assertEqual(tabela["Entre os 16 craques"].tolist(), fonte["Destaque"].tolist())
                np.testing.assert_allclose(tabela[METRICAS], fonte[METRICAS])
                craques = fonte.loc[fonte["Destaque"].eq(True), "Player"].drop_duplicates()
                textos = [item.value for item in app.tabs[2].markdown]
                if not craques.empty:
                    lista = next(texto for texto in textos if texto.startswith("**Craques neste grupo:**"))
                    self.assertTrue(all(nome in lista for nome in craques))
                pd.testing.assert_frame_equal(app.tabs[2].dataframe[2].value, mapa_original)

    def test_descricoes_distinguem_as_caracteristicas_dos_grupos(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        textos = [item.value for item in app.tabs[2].markdown]
        indice = textos.index("**Grupo 1 · 181 registros**")
        self.assertEqual(textos[indice + 1], "**Entre as menores médias:** assistências, finalizações.")
        indice = textos.index("**Grupo 2 · 100 registros**")
        self.assertEqual(textos[indice + 1], "**Entre as maiores médias:** gols sem pênalti, finalizações.")
        indice = textos.index("**Grupo 3 · 103 registros**")
        self.assertEqual(textos[indice + 1], "**Entre as maiores médias:** assistências, cruzamentos.")

    def test_painel_mostra_grupos_craques_e_contexto_externo(self):
        from streamlit.testing.v1 import AppTest
        from referencias_externas import carregar_externos, montar_referencias

        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        resumo = app.tabs[2].dataframe[2].value
        craques = app.tabs[2].dataframe[3].value
        self.assertEqual(resumo["Registros"].sum(), 384)
        self.assertEqual(len(craques), 16)
        self.assertTrue(any("variância" in item.value for item in app.tabs[2].caption))
        referencias = montar_referencias(self.base, carregar_externos(PASTA))
        indice = int(referencias.index[referencias["Player"].eq("Neymar")][0])
        app.sidebar.selectbox[0].select(indice).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Neymar é uma referência externa" in item.value for item in app.tabs[2].caption))
        pd.testing.assert_frame_equal(app.tabs[2].dataframe[2].value, resumo)
        pd.testing.assert_frame_equal(app.tabs[2].dataframe[3].value, craques)


if __name__ == "__main__":
    unittest.main()
