from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd
from PIL import Image

from fotos_jogadores import PASTA_FOTOS, obter_retrato
from referencias_externas import NOMES


PASTA = Path(__file__).resolve().parent


class FotosJogadoresTest(unittest.TestCase):
    def test_catalogo_cobre_craques_e_lote_adicional_com_imagem_valida(self):
        craques = pd.read_csv(PASTA / "data/processed/comparacao_craques.csv")
        novos = {
            "Endrick", "Antoine Griezmann", "Antony", "Marcus Rashford",
            "Viktor Gyökeres", "Paulo Dybala", "Richarlison", "Gabriel Martinelli",
            "João Pedro", "Lucas Paquetá", "Ferrán Torres", "Jeremy Doku",
            "Cody Gakpo", "Désiré Doué",
        }
        nomes = set(craques["Player"]) | NOMES | novos
        catalogo = json.loads((PASTA_FOTOS / "catalogo.json").read_text(encoding="utf-8"))
        self.assertEqual({item["nome"] for item in catalogo}, nomes)
        self.assertEqual(len(catalogo), 33)
        self.assertEqual(len({item["arquivo"] for item in catalogo}), 33)
        for nome in nomes:
            with self.subTest(jogador=nome):
                retrato = obter_retrato(nome)
                self.assertIsNotNone(retrato.imagem)
                if nome == "Lamine Yamal":
                    self.assertTrue(retrato.fonte.startswith("https://commons.wikimedia.org/wiki/File:"))
                    self.assertEqual(retrato.credito, "Biso / Wikimedia Commons")
                    self.assertEqual(retrato.licenca, "CC BY 4.0")
                    self.assertEqual(retrato.url_licenca, "https://creativecommons.org/licenses/by/4.0/")
                    self.assertEqual(retrato.mime, "image/jpeg")
                else:
                    self.assertTrue(retrato.fonte.startswith("https://www.fotmob.com/players/"))
                with Image.open(BytesIO(retrato.imagem)) as imagem:
                    self.assertEqual(imagem.format, "JPEG" if nome == "Lamine Yamal" else "PNG")
                    self.assertGreaterEqual(min(imagem.size), 100)
                    imagem.verify()

    def test_busca_normaliza_acentos_sem_usar_fotos_de_outro_jogador(self):
        correto = obter_retrato("Vinicius Júnior")
        self.assertEqual(obter_retrato("  VINÍCIUS JÚNIOR  ").imagem, correto.imagem)
        desconhecido = obter_retrato("Abde Ezzalzouli")
        self.assertIsNone(desconhecido.imagem)
        self.assertIsNone(desconhecido.fonte)
        self.assertEqual(desconhecido.iniciais, "AE")

    def test_arquivo_ausente_ou_corrompido_usa_iniciais(self):
        with TemporaryDirectory() as temporaria:
            pasta = Path(temporaria)
            catalogo = [{"nome": "Lamine Yamal", "arquivo": "foto.png", "fonte": "https://www.fotmob.com/players/1467236"}]
            (pasta / "catalogo.json").write_text(json.dumps(catalogo), encoding="utf-8")
            for dados in [None, b"imagem corrompida"]:
                if dados is not None:
                    (pasta / "foto.png").write_bytes(dados)
                retrato = obter_retrato("Lamine Yamal", pasta)
                self.assertIsNone(retrato.imagem)
                self.assertEqual(retrato.iniciais, "LY")


if __name__ == "__main__":
    unittest.main()
