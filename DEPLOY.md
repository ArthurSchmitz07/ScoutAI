# Publicar o ScoutAI com um endereço permanente

Destino: **Streamlit Community Cloud**, na modalidade gratuita.
O aplicativo será executado nos servidores da hospedagem e não dependerá
do computador de desenvolvimento ligado. O endereço será do tipo
`https://<nome-disponível>.streamlit.app`.

## Configuração da publicação

| Campo | Valor |
| --- | --- |
| Conta GitHub | `ArthurSchmitz07` |
| Repositório | `ArthurSchmitz07/ScoutAI` |
| Branch | `main` |
| Arquivo principal | `painel.py` |
| Versão do Python, em Advanced settings | `3.14` |
| Dependências | `requirements.txt`, na raiz do repositório |
| Segredos do aplicativo | Nenhum é necessário no estado atual |

O ambiente foi validado localmente com Python 3.14.10. A versão padrão da
hospedagem pode ser diferente: selecione Python 3.14 antes de iniciar o deploy.
Não use `app.py` como arquivo principal; ele prepara dados e não abre a interface.

## Publicação inicial

1. Entre em https://share.streamlit.io com sua conta GitHub.
2. Conecte a conta `ArthurSchmitz07` e permita o acesso ao repositório privado
   `ScoutAI`, quando solicitado pelo serviço.
3. Na área de trabalho correspondente ao proprietário do repositório, escolha
   **Create app** e a opção de publicar um aplicativo existente.
4. Informe repositório, branch e arquivo conforme a tabela.
5. Escolha um subdomínio disponível, por exemplo `scoutai-arthur`.
   O nome só estará confirmado quando aceito pela hospedagem.
6. Em **Advanced settings**, selecione Python 3.14 e salve.
7. Inicie a publicação e acompanhe os logs da instalação.
8. Nas configurações de compartilhamento, permita o acesso público ao aplicativo.
   Aplicativos derivados de repositórios privados começam privados por padrão.
   O repositório pode continuar privado mesmo com o aplicativo público.

Esse processo requer login e autorização da conta do proprietário. Uma credencial
local do Git, usada para enviar commits, não substitui a entrada na hospedagem.
Não é necessário colocar tokens do GitHub no código ou nos segredos do ScoutAI.

## Conferência antes de compartilhar no LinkedIn

- Abra o endereço publicado numa janela sem sessão de login para conferir o acesso público.
- Compare dois e quatro craques e confira as fotos e os seis gráficos.
- Altere os pesos dos Rankings e baixe o CSV.
- Pesquise Yamal e uma referência externa na aba Perfis e semelhantes.
- Confira o mapa PCA, as descrições dos grupos e o filtro de integrantes.
- Abra o link no celular.
- Registre o endereço confirmado no README e na descrição do repositório.

Os CSVs e as imagens necessários já estão no repositório. Suas fontes e limitações
estão documentadas no README e nas pastas de dados e assets. Os períodos das
referências externas continuam diferentes do recorte europeu.

## Endereço permanente e hibernação

O serviço gratuito mantém o endereço da aplicação, mas pode hibernar após
12 horas sem tráfego. Nesse caso, um visitante pode encontrar a tela de
reativação antes de abrir o ScoutAI. Isso não depende do computador do autor.
Esse plano não garante execução contínua 24 horas por dia.

Atualizações enviadas para `main` são detectadas pela hospedagem. Mudanças nas
dependências podem provocar uma reinstalação e levar mais tempo para aparecer.

## Documentação da hospedagem

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
