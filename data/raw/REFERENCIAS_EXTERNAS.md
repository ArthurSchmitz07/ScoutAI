# Referências externas

Consulta manual em 04/11/2026 às páginas do FotMob indicadas no CSV.
Somente Cristiano Ronaldo, Lionel Messi e Neymar; apenas a liga de cada clube,
sem seleção, copas ou competições continentais. Não há atualização automática.
Ao renovar os números, atualizar a linha inteira com o mesmo recorte.
O arquivo referencias_externas_2026-10-28.csv preserva a consulta anterior.

| Jogador | Liga | Temporada | Minutos | Gols | Pênaltis | Assistências | Finalizações | No alvo | Último jogo de liga listado |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Cristiano Ronaldo | Saudi Pro League | 2026/27 | 783 | 7 | 0 | 0 | 37 | 17 | 29/10/2026 |
| Lionel Messi | Major League Soccer | 2026 | 2574 | 26 | 1 | 13 | 179 | 73 | 02/11/2026 |
| Neymar | Série A Brasil | 2026 | 1223 | 8 | 4 | 3 | 51 | 22 | 25/10/2026 |

A data da consulta não garante que o fornecedor já tenha incorporado todos os
jogos até aquele dia. Os calendários não coincidem com o CSV europeu 2025/26.
Atualizar a consulta não torna esses períodos iguais.

## Finalizações no alvo

SoT é o total de finalizações no alvo publicado na seção de desempenho da
temporada. O carregador calcula No alvo/90 = SoT / Min * 90.
Os três valores agora foram conferidos na fonte. Antes, faltavam no nosso
arquivo local; isso não significava que o fornecedor não possuísse os dados.
Arquivos sem SoT ou células vazias continuam produzindo valor ausente, com
"Não disponível" e motivo no Comparador. Totais negativos, fracionários,
infinitos ou maiores que as finalizações são rejeitados.

## Cruzamentos reconstituídos

As páginas publicam cruzamentos certos e percentual de acerto a uma casa
decimal, não o total tentado. Admitindo taxa = certos/total, há um único
denominador inteiro compatível com o arredondamento em cada caso:

- Cristiano: 1 certo, 33,3% => 3 totais.
- Messi: 23 certos, 28,4% => 81 totais.
- Neymar: 13 certos, 19,7% => 66 totais.

São totais derivados, não contagens totais publicadas diretamente. A interface
explica o método. O carregador rejeita taxas que permitem vários denominadores
e não preenche ausências com zero. Definições de cruzamento podem diferir entre
o fornecedor externo e o CSV europeu.

## Conferência dos pênaltis de Cristiano

O perfil não publica um campo explícito de gols de pênalti. A tabela de
artilheiros indicada em Fonte_penaltis ainda exibia 4 gols e zero pênaltis
na consulta: ela corresponde ao recorte anterior e não foi tratada como uma
atualização direta para os 7 gols.

Reconciliamos esse recorte com o único jogo de liga posterior listado no perfil:
Al Nassr x Al Kholood, 29/10/2026. A ficha registra 90 minutos e três gols de
Cristiano, aos 66, 72 e 81 minutos, todos com assistências e sem indicação de
pênalti. Assim, 693 + 90 = 783 minutos e 4 + 3 = 7 gols; os gols de pênalti
permanecem em zero. A ficha está em Fonte_atualizacao.
Não inferimos zero apenas da ausência do campo no perfil.

Messi e Neymar publicam seus totais de gols de pênalti diretamente no perfil.

## Uso no projeto

- Comparador: os três estão disponíveis; os períodos e a data da consulta
  aparecem na interface. Não há ajuste por liga ou equipe.
- Rankings: modo europeu como padrão; modo externo explicitamente exploratório.
  O mínimo de 900 minutos vale nos dois. Neste snapshot, Messi e Neymar são
  elegíveis, Cristiano não. A normalização usa somente o grupo elegível do modo.
- Semelhança: padronização ajustada somente em jogadores_com_grupos.csv, Europa
  2025/26. Os externos usam transform, não alteram médias, desvios ou grupos,
  não recebem grupo e não entram na lista de candidatos. Cristiano permanece
  disponível como referência abaixo de 900 minutos, com aviso.
- Todas as métricas por 90 usam os totais sem arredondamento prévio.

Fontes:
- https://www.fotmob.com/players/30893/cristiano-ronaldo
- https://www.fotmob.com/en-GB/leagues/536/stats/season/1000000494/players/goals/team/101918/al-nassr-fc-loan-players
- https://www.fotmob.com/matches/al-nassr-fc-vs-al-kholood/gv0d6tk6
- https://www.fotmob.com/players/30981/lionel-messi
- https://www.fotmob.com/players/19533/neymar
