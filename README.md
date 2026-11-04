# ScoutAI ⚽

Aplicação em Python para explorar diferenças entre grandes jogadores de futebol
por meio de comparação de estatísticas, rankings com pesos ajustáveis e perfis
ofensivos com Machine Learning.

O objetivo é entender como cada jogador se destaca nas métricas disponíveis.
As pontuações e os agrupamentos não representam uma medida de qualidade geral.

## Funcionalidades

- **Comparador:** escolha de dois a quatro jogadores entre os 16 craques europeus
  e as três referências externas. Cartões com fotos, tabela e seis gráficos de
  métricas por 90 minutos.
- **Rankings:** ajuste do peso dos gols sem pênalti e das assistências. Modo
  europeu como padrão e modo exploratório com referências externas. Exportação
  CSV com os pesos, o grupo escolhido e as temporadas.
- **Perfis e semelhantes:** busca por proximidade estatística, comparação
  individual, grupos KMeans, mapa PCA e filtro dos integrantes de cada grupo.
- **Fotos:** catálogo local com 33 jogadores fotografados. Jogadores sem foto
  cadastrada, ou com arquivo indisponível, recebem um avatar com iniciais.

Na base preparada atual, a busca tem **387 registros de 386 nomes distintos**:
384 registros europeus (383 nomes) e três referências externas. Um jogador
europeu aparece em mais de um clube. O Comparador permanece restrito aos
19 craques, mesmo que outros jogadores da busca tenham fotos.

## Repositório

[ArthurSchmitz07/ScoutAI](https://github.com/ArthurSchmitz07/ScoutAI)

O repositório foi preparado inicialmente como privado. Para cloná-lo, utilize
uma conta com acesso ao projeto:

```powershell
git clone https://github.com/ArthurSchmitz07/ScoutAI.git
cd ScoutAI
```

## Executar no Windows

Ambiente de desenvolvimento validado com **Python 3.14.10**. As versões diretas
das bibliotecas estão fixadas em `requirements.txt`; as dependências transitivas
são resolvidas pelo pip. Não é necessário ativar o ambiente virtual nos comandos
abaixo.

Abra o PowerShell na pasta do ScoutAI e execute:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run painel.py
```

Abra o endereço informado no terminal, normalmente **http://localhost:8501**.
Esse endereço funciona no próprio computador; um link público exige hospedagem.

**O ponto de entrada da interface é `painel.py`.** O arquivo `app.py` prepara
a tabela dos craques e não inicia o site.

Para Linux ou macOS, usando Python 3.14:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run painel.py
```

Os comandos de Linux e macOS são equivalentes aos do Windows; o ambiente de
validação deste projeto é Windows. Execute os comandos a partir da pasta do
projeto para também utilizar os exemplos de testes abaixo.

## Dados necessários

Para abrir o painel com os resultados atuais, mantenha:

- `data/processed/comparacao_craques.csv`;
- `data/processed/jogadores_com_grupos.csv`;
- `data/raw/referencias_externas.csv`, para consultar os três jogadores externos;
- a pasta `assets/`, que contém o estilo dos cartões, o catálogo e as fotos.

Os CSVs e os assets não são excluídos pelo `.gitignore`, pois fazem parte da
execução da demonstração. O ambiente virtual e as configurações pessoais do
VS Code são excluídos. Não copie a `.venv` de outro computador: crie uma nova.

### Reconstruir os resultados a partir dos dados brutos

O arquivo de entrada europeu deve estar em:

```text
data/raw/players_data-2025_2026.csv
```

Execute nesta ordem, na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe app.py
.\.venv\Scripts\python.exe rankings.py
.\.venv\Scripts\python.exe preparar_perfis.py
.\.venv\Scripts\python.exe modelo_perfis.py
```

Esses comandos sobrescrevem os resultados correspondentes em `data/processed/`.

1. `app.py` seleciona os 16 craques e calcula a comparação por 90 minutos.
2. `rankings.py` gera os cenários de pesos 70/30, 50/50 e 30/70.
3. `preparar_perfis.py` seleciona posições que contêm `FW`, acrescenta os craques
   da lista mesmo quando classificados como meio-campistas e aplica o mínimo
   de 900 minutos. Remove registros incompletos nas métricas exigidas.
4. `modelo_perfis.py` padroniza as quatro métricas, avalia KMeans de dois a seis
   grupos e exporta a avaliação, os jogadores com grupos e as médias dos grupos.

O PCA é calculado pela interface a partir da base europeia preparada. As
referências externas são carregadas de seu próprio CSV, sem alterar os grupos.

### Outros scripts

```powershell
# Busca no terminal, sem salvar um novo CSV
.\.venv\Scripts\python.exe jogadores_semelhantes.py "Lamine Yamal" --sem-salvar

# Gera o gráfico dos perfis sem abrir uma janela
.\.venv\Scripts\python.exe graficos_perfis.py --sem-abrir
```

`graficos.py` gera comparações visuais e `analise_rankings.py` analisa os três
cenários de pesos. Esses dois scripts também abrem uma janela do Matplotlib.
Gráficos e exportações gerados em `outputs/` ficam fora do versionamento.

## Metodologia

### Métricas por 90 minutos

O cálculo utiliza `total / minutos × 90`. O Comparador mostra gols, gols sem
pênalti, assistências, finalizações, finalizações no alvo e gols + assistências.
Uma estatística ausente não é substituída por zero. Quando faltar, o Comparador
mostra **Não disponível**, explica o motivo e não desenha uma barra de valor zero.

### Rankings

Apenas jogadores com pelo menos 900 minutos são elegíveis. Para cada métrica,
a normalização min–max transforma o menor valor do grupo em 0 e o maior em 100:

```text
Nota = (valor − mínimo) / (máximo − mínimo) × 100
Pontuação = Nota gols × peso gols + Nota assistências × peso assistências
```

Se todos tiverem o mesmo valor, a nota dessa métrica é 50. Os pesos somam 100%.
Empates na pontuação recebem a mesma posição; nomes empatados são organizados
alfabeticamente. A pontuação usa os valores completos, antes do arredondamento
para exibição.

A normalização é recalculada no grupo elegível do modo escolhido. Assim,
incluir jogadores pode mudar as notas dos demais. Não há ajuste por liga ou equipe.

### Grupos, PCA e semelhança

- Quatro métricas: gols sem pênalti, assistências, finalizações e cruzamentos/90.
- `StandardScaler` ajustado somente na população europeia.
- KMeans com `random_state=42`, `n_init=20` e seleção provisória pela maior
  silhueta entre os cenários avaliados.
- No resultado atual, três grupos e silhueta aproximada de **0,280**. Os grupos
  são exploratórios e não formam um ranking de qualidade.
- PCA em dois eixos, preservando aproximadamente **79,8% da variância** das
  quatro métricas padronizadas. O desenho é uma aproximação das distâncias.
- A busca usa distância euclidiana nas quatro métricas padronizadas, considera
  todos os grupos e exclui registros com o mesmo nome da referência. A distância
  não é uma porcentagem de semelhança.
- O filtro de grupo altera a lista de integrantes; o mapa mantém todos os grupos.

## Fontes, períodos e limitações

### Base europeia

O arquivo local está identificado como **2025/26**. O projeto ainda não registra
a URL original de obtenção nem uma verificação independente de todos os seus
números. Essa procedência deve ser completada antes da publicação dos dados.

### Referências externas

Consulta manual ao FotMob em **04/11/2026**, apenas para a liga de cada clube:

| Jogador | Competição | Temporada | Minutos no snapshot |
| --- | --- | --- | ---: |
| Cristiano Ronaldo | Liga Saudita | 2026/27 | 783 |
| Lionel Messi | MLS | 2026 | 2.574 |
| Neymar | Brasileirão | 2026 | 1.223 |

Esses calendários são diferentes do recorte europeu. Atualizar os números não
iguala os períodos, e as métricas por 90 não ajustam diferenças de liga e equipe.
Por isso, o ranking com externos é identificado como exploratório. Nesse snapshot,
Messi e Neymar são elegíveis no ranking, enquanto Cristiano está abaixo de 900
minutos e permanece disponível no Comparador e como referência de semelhança.

Não há atualização automática. A data da consulta não garante que o fornecedor
tenha incorporado todos os jogos até aquele dia. A consulta anterior foi preservada
em `data/raw/referencias_externas_2026-10-28.csv`.

O método de reconstrução dos cruzamentos, a conferência dos pênaltis de Cristiano
e as fontes de cada recorte estão em
[REFERENCIAS_EXTERNAS.md](data/raw/REFERENCIAS_EXTERNAS.md).

### Fotos

As imagens locais vêm dos perfis do FotMob, com crédito na interface e origem
registrada em [catalogo.json](assets/jogadores/catalogo.json). Consulte
[FONTES.md](assets/jogadores/FONTES.md). As fotos de perfil não representam
necessariamente o clube ou a aparência do jogador na temporada analisada.
Os dados do clube e da temporada vêm dos CSVs.

As permissões de redistribuição dos CSVs e das imagens ainda precisam ser
verificadas antes de tornar esses arquivos públicos. Este projeto não declara
uma licença para materiais de terceiros.

### Alcance da análise

O modelo de perfis não utiliza xG, xA, dribles ou progressão. Os resultados
descrevem as métricas escolhidas, e não todo o estilo de jogo ou o auge de um
jogador. Fotos e estatísticas externas permanecem em recortes diferentes da
base europeia.

## Testes

Com os CSVs preparados e as fotos locais presentes:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Os testes verificam rankings, pesos, empates, grupos, PCA, referências externas,
dados ausentes, fotos e interações do painel com `streamlit.testing.v1.AppTest`.
As verificações de navegador com Playwright foram feitas durante o desenvolvimento;
o projeto ainda não contém uma suíte Playwright executável por comando.

## Estrutura principal

```text
ScoutAI/
├── painel.py                    # Interface Streamlit
├── app.py                       # Prepara a comparação dos craques
├── rankings.py                  # Cálculo e cenários de ranking
├── preparar_perfis.py            # Filtros e métricas dos perfis
├── modelo_perfis.py              # KMeans e avaliação dos grupos
├── perfis_pca.py                 # Projeção PCA
├── jogadores_semelhantes.py      # Busca por distância estatística
├── referencias_externas.py       # Validação e cálculo dos externos
├── fotos_jogadores.py            # Fotos locais e avatar alternativo
├── graficos.py
├── graficos_perfis.py
├── analise_rankings.py
├── test_*.py                     # Testes automatizados
├── assets/                      # CSS, catálogo, fotos e créditos
├── data/
│   ├── raw/                     # Dados de entrada e documentação de fontes
│   └── processed/               # CSVs preparados para o painel
├── outputs/                     # Resultados gerados, ignorados pelo Git
├── requirements.txt
├── .gitignore
└── README.md
```

A hospedagem pública da aplicação ainda não foi configurada. O roteiro e os
parâmetros para publicar uma versão independente do computador do autor estão
em [DEPLOY.md](DEPLOY.md).
