from pathlib import Path
import unittest

import pandas as pd

from rankings import calcular_ranking


PASTA = Path(__file__).resolve().parent


class RankingsTest(unittest.TestCase):
    def test_extremos_empates_e_entrada_preservada(self):
        base = pd.DataFrame({
            "Player": ["C", "A", "B", "Fora"],
            "Min": [900, 1000, 950, 899],
            "Gols sem pênalti/90": [2, 0, 1, 100],
            "Assistências/90": [0, 2, 1, 100],
        })
        original = base.copy(deep=True)
        gols = calcular_ranking(base, 1)
        assistencias = calcular_ranking(base, 0)
        self.assertEqual(gols["Player"].tolist(), ["C", "B", "A"])
        self.assertEqual(assistencias["Player"].tolist(), ["A", "B", "C"])
        self.assertEqual(gols["Pontuação"].tolist(), [100, 50, 0])
        iguais = calcular_ranking(base, 0.5)
        self.assertEqual(iguais["Player"].tolist(), ["A", "B", "C"])
        self.assertEqual(iguais["Posição"].tolist(), [1, 1, 1])
        self.assertEqual(iguais["Pontuação"].tolist(), [50, 50, 50])
        pd.testing.assert_frame_equal(base, original)

    def test_metrica_constante_e_pesos_invalidos(self):
        base = pd.DataFrame({
            "Player": ["A", "B"], "Min": [900, 900],
            "Gols sem pênalti/90": [1, 1], "Assistências/90": [0, 1],
        })
        ranking = calcular_ranking(base, 1)
        self.assertEqual(ranking["Nota gols"].tolist(), [50, 50])
        self.assertEqual(ranking["Posição"].tolist(), [1, 1])
        for peso in [-0.1, 1.1, float("nan"), float("inf")]:
            with self.subTest(peso=peso), self.assertRaises(ValueError):
                calcular_ranking(base, peso)

    def test_cenarios_continuam_iguais_ao_csv_existente(self):
        base = pd.read_csv(PASTA / "data/processed/comparacao_craques.csv")
        anteriores = pd.read_csv(PASTA / "data/processed/rankings_craques.csv")
        for nome, peso in [("Prioridade em gols", 0.7), ("Pesos iguais", 0.5), ("Prioridade em assistências", 0.3)]:
            with self.subTest(cenario=nome):
                atual = calcular_ranking(base, peso)
                esperado = anteriores.loc[anteriores["Cenário"].eq(nome)].reset_index(drop=True)
                pd.testing.assert_frame_equal(atual[esperado.columns.drop("Cenário")], esperado.drop(columns="Cenário"))

    def test_modo_externo_inclui_elegiveis_e_preserva_temporadas(self):
        from streamlit.testing.v1 import AppTest
        from referencias_externas import carregar_externos, montar_referencias

        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        europeu = app.tabs[1].dataframe[0].value.copy()
        self.assertEqual(app.radio[0].value, "Europeu (padrão)")
        app.radio[0].set_value("Com referências externas").run()
        self.assertFalse(app.exception)
        tabela = app.tabs[1].dataframe[0].value
        self.assertEqual(len(tabela), 18)
        self.assertIn("Lionel Messi", tabela["Jogador"].tolist())
        self.assertIn("Neymar", tabela["Jogador"].tolist())
        self.assertNotIn("Cristiano Ronaldo", tabela["Jogador"].tolist())
        self.assertTrue(any(
            "Cristiano Ronaldo" in item.value and "783 minutos" in item.value and "não elegível" in item.value
            for item in app.tabs[1].info
        ))
        por_nome = tabela.set_index("Jogador")
        self.assertEqual(por_nome.loc["Lionel Messi", "Temporada"], "2026")
        self.assertEqual(por_nome.loc["Neymar", "Temporada"], "2026")
        self.assertEqual(por_nome.loc["Harry Kane", "Temporada"], "2025/26")
        self.assertTrue(tabela["Minutos"].ge(900).all())

        base = montar_referencias(
            pd.read_csv(PASTA / "data/processed/comparacao_craques.csv"),
            carregar_externos(PASTA),
        )
        elegiveis = base.loc[base["Min"].ge(900)].set_index("Player")
        gols = elegiveis["Gols sem pênalti/90"]
        assistencias = elegiveis["Assistências/90"]
        esperado = (
            (gols - gols.min()) / (gols.max() - gols.min()) * 50
            + (assistencias - assistencias.min()) / (assistencias.max() - assistencias.min()) * 50
        )
        for nome, linha in por_nome.iterrows():
            self.assertAlmostEqual(linha["Pontuação"], esperado.loc[nome])

        app.radio[0].set_value("Europeu (padrão)").run()
        self.assertFalse(app.exception)
        pd.testing.assert_frame_equal(app.tabs[1].dataframe[0].value, europeu)

    def test_painel_atualiza_ranking_e_pesos(self):
        from streamlit.testing.v1 import AppTest

        base = pd.read_csv(PASTA / "data/processed/comparacao_craques.csv")
        app = AppTest.from_file(str(PASTA / "painel.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        for percentual in [50, 100, 0, 70]:
            with self.subTest(peso_gols=percentual):
                app.slider[0].set_value(percentual).run()
                self.assertFalse(app.exception)
                tabela = app.tabs[1].dataframe[0].value
                self.assertEqual(len(tabela), 16)
                # Cálculo independente para validar os valores exibidos.
                gols = base["Gols sem pênalti/90"]
                assistencias = base["Assistências/90"]
                notas = (
                    (gols - gols.min()) / (gols.max() - gols.min()) * percentual
                    + (assistencias - assistencias.min()) / (assistencias.max() - assistencias.min()) * (100 - percentual)
                )
                esperado = base.assign(pontos=notas).sort_values(["pontos", "Player"], ascending=[False, True])
                self.assertEqual(tabela["Jogador"].tolist(), esperado["Player"].tolist())
                for atual, correto in zip(tabela["Pontuação"], esperado["pontos"]):
                    self.assertAlmostEqual(atual, correto)
                self.assertTrue(any(
                    f"{percentual}% gols e {100 - percentual}% assistências" in item.value
                    for item in app.tabs[1].markdown
                ))


if __name__ == "__main__":
    unittest.main()
