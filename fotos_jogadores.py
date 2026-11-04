"""Fotos locais verificadas e avatar para jogadores sem retrato disponível."""

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
import unicodedata

from PIL import Image


PASTA_FOTOS = Path(__file__).resolve().parent / "assets" / "jogadores"


@dataclass(frozen=True)
class Retrato:
    imagem: bytes | None
    fonte: str | None
    iniciais: str
    credito: str = "FotMob"
    licenca: str | None = None
    url_licenca: str | None = None
    mime: str = "image/png"


def normalizar_nome(nome):
    texto = unicodedata.normalize("NFKD", nome.strip().casefold())
    return " ".join("".join(letra for letra in texto if not unicodedata.combining(letra)).split())


def obter_retrato(nome, pasta_fotos=PASTA_FOTOS):
    palavras = nome.strip().split()
    iniciais = (palavras[0][0] + (palavras[-1][0] if len(palavras) > 1 else "")).upper() if palavras else "?"
    alternativa = Retrato(None, None, iniciais)
    pasta = Path(pasta_fotos)
    try:
        catalogo = json.loads((pasta / "catalogo.json").read_text(encoding="utf-8"))
        registro = next((item for item in catalogo if normalizar_nome(item["nome"]) == normalizar_nome(nome)), None)
        if registro is None:
            return alternativa
        arquivo = pasta / registro["arquivo"]
        dados = arquivo.read_bytes()
        # Evita que um arquivo ausente ou corrompido quebre a pesquisa.
        with Image.open(BytesIO(dados)) as imagem:
            mime = Image.MIME.get(imagem.format, "image/png")
            imagem.verify()
        return Retrato(
            dados, registro["fonte"], iniciais,
            registro.get("credito", "FotMob"), registro.get("licenca"),
            registro.get("url_licenca"), mime,
        )
    except (OSError, ValueError, KeyError, TypeError):
        return alternativa
