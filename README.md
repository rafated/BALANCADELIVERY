# Documentação do Processo GUI

## Visão Geral
Este projeto implementa um sistema de pesagem automatizado para pedidos McDelivery. Ele utiliza uma combinação de uma balança eletrônica, uma câmera e uma API para gerenciar e confirmar pedidos de maneira automatizada. Além disso, há fallback para banco de dados local em caso de falha de conexão com a API.

### Principais Tecnologias Utilizadas:
- **Python**: Linguagem de programação principal.
- **PySimpleGUI**: Biblioteca para criação da interface gráfica do usuário (GUI).
- **SQLite3**: Banco de dados local para persistência de pedidos.
- **Requests**: Para integração com a API remota.
- **Threading**: Para execução de tarefas assíncronas.
- **OpenCV**: Para captura de imagem da câmera.
- **Serial**: Comunicação com a balança eletrônica.
- **USB**: Comunicação com impressora.

---

## Instalação

### Dependências
Este projeto utiliza várias bibliotecas Python e interfaces externas. Abaixo está uma lista de dependências e como instalá-las.

### Pacotes Python Necessários
Instale os pacotes listados abaixo usando `pip`:

```bash
pip install PySimpleGUI
pip install sqlite3
pip install requests
pip install opencv-python
pip install pyserial
pip install pyusb
Hardware Suportado:
Balança com interface serial (comunicação via porta COM).
Impressora de etiquetas compatível com comandos ESC/POS.
Câmera para captura de imagem dos pedidos.
Configuração
Os parâmetros de configuração, como a URL da API, o código do restaurante e a porta COM da balança, são armazenados no arquivo config.py. Exemplo de configuração:

python
Copy code
api_url = 'https://sua-api.com'
rest_code = 'MCDELIVERY001'
data_base = 'local_database.db'
img_path = './images'
port_com_balanca = 'COM3'
api_offline = False
pending_order = True

Funcionalidades

1. Teste de Conexão com a API
A função teste_api_connection() verifica a conectividade com a API remota. Se a API estiver online, ela retorna True e define o sistema como online, caso contrário, retorna False e define o sistema como offline.

2. Conexão com o Banco de Dados
Função open_database_connection() abre a conexão com o banco de dados local SQLite. Em caso de erro, a função retorna None.

3. Buscar Último Pedido
A função fetch_last_order() busca o último pedido disponível, primeiro tentando pela API e, caso a API esteja offline, acessa o banco de dados local.

4. Atualização do Estado do Pedido
Função update_order_state(order_number) é responsável por marcar o pedido como confirmado, seja pela API ou banco de dados local.

5. Processamento do Pedido
A função process_order() processa os pedidos de acordo com a lista de itens, calculando o peso estimado e verificando os detalhes do pedido, como a presença de molhos ou sobremesas específicas.

6. Pesagem e Validação
O sistema coleta os dados da balança por meio da interface serial, compara o peso real com o peso estimado e decide se o pedido deve ser confirmado ou não. Em caso de sucesso, o pedido é marcado como concluído.

7. Captura de Imagem
A função capture_image() tira uma foto do pedido usando a câmera conectada, salva a imagem e a exibe na interface gráfica.

8. Intervalo para Verificação de Pedidos
Utilizando a classe SetInterval, o sistema verifica periodicamente por novos pedidos usando a função verped(), que busca e processa pedidos pendentes.

9. Resetar Pedidos
A função reset_orders() limpa os pedidos pendentes e reinicia a interface do sistema.

10. Impressão de Confirmação
A função print_confirmation() utiliza comandos ESC/POS para imprimir uma confirmação do pedido processado.

Interface Gráfica (GUI)
A interface gráfica foi construída utilizando PySimpleGUI. As principais áreas da interface incluem:

Seção de Pedidos: Lista os pedidos pendentes.
Seção de Pesagem: Exibe o peso estimado e real do pedido.
Câmera: Mostra a imagem do pedido.
Botões de Ação:
"Reiniciar GUI": Reinicia a interface do sistema.
"Resetar Pedidos": Limpa a lista de pedidos pendentes.
Layout
python
Copy code
layout = build_layout() # Função que constrói o layout da GUI
window = sg.Window('Balanca_McDelivery', layout, finalize=True, resizable=True, ...)
Fluxo de Execução
Inicialização do Sistema: A interface gráfica é carregada e a conexão com a balança e câmera é iniciada.
Verificação de Pedidos: A cada 3 segundos, o sistema verifica por novos pedidos usando a API ou banco de dados local.
Processamento de Pedido: Ao selecionar um pedido, o sistema calcula o peso estimado e verifica a conformidade do pedido.
Captura de Imagem: Uma imagem do pedido é capturada e exibida na interface.
Confirmação do Pedido: Se o peso estiver dentro dos limites aceitáveis, o pedido é confirmado e removido da lista.
Impressão: Caso haja uma impressora conectada, o sistema imprime um ticket de confirmação.
Tratamento de Erros
Erros e exceções são logados em um arquivo chamado Erro_Log.log. A função log_error() captura o erro e o salva no arquivo de log com um timestamp.

python
Copy code
def log_error(e):
    with open("Erro_Log.log", "a") as logf:
        t = datetime.datetime.now()
        logf.write(f"{t.strftime('%Y%m%d_%Hh%Mm%Ss')}; Erro: {str(e)}\n")
Principais Funções
Função	Descrição
teste_api_connection()	Testa a conexão com a API remota.
open_database_connection()	Abre conexão com o banco de dados SQLite.
fetch_last_order()	Busca o último pedido disponível via API ou banco de dados local.
update_order_state()	Atualiza o estado do pedido como confirmado.
process_order()	Processa o pedido, exibindo detalhes e calculando o peso estimado.
capture_image()	Captura uma imagem do pedido via câmera.
send_weight_data_to_api()	Envia os dados de pesagem para a API.
SetInterval()	Executa uma ação periodicamente em segundo plano (threading).
reset_orders()	Limpa os pedidos pendentes e reinicia a GUI.
print_confirmation()	Imprime um ticket de confirmação utilizando uma impressora ESC/POS.
verped()	Verifica periodicamente por novos pedidos e os processa.
main()	Função principal que inicializa a GUI e executa o sistema.
Conclusão
Este sistema automatizado foi projetado para facilitar o processo de pesagem e confirmação de pedidos McDelivery, garantindo maior precisão e automação. Ele integra diversos dispositivos de hardware e serviços em nuvem (API) para fornecer uma solução robusta e eficiente para operações de entrega.
```
# Documentação do Sistema de Processamento de Recibos McDelivery

## Visão Geral
Este projeto implementa um sistema para processar arquivos de recibo temporários e convertê-los em uma lista de produtos (PickList), que inclui informações sobre o pedido, como quantidades, produtos e ingredientes extras. Ele também integra a comunicação com uma API ou um banco de dados local para verificar os dados de cada item.

### Principais Tecnologias Utilizadas:
- **Python**: Linguagem de programação principal.
- **SQLite3**: Banco de dados local para persistência de pedidos.
- **Requests**: Para integração com a API remota.
- **Threading**: Para execução de tarefas assíncronas.
- **Regex**: Para validação de padrões e extração de dados.

---

## Instalação

### Dependências
Este projeto utiliza várias bibliotecas Python e interfaces externas. Abaixo está uma lista de dependências e como instalá-las.

### Pacotes Python Necessários
Instale os pacotes listados abaixo usando `pip`:

```bash
pip install requests
pip install sqlite3
Hardware Suportado:
Integração com sistemas de pedidos (via arquivos temporários).
Conexão com banco de dados SQLite e APIs para verificação de produtos.
Configuração
Os parâmetros de configuração, como a URL da API e a localização dos diretórios de arquivos, são armazenados no arquivo config.py. Exemplo de configuração:

python
Copy code
api_url = 'https://sua-api.com'
rest_code = 'MCDELIVERY001'
data_base = 'local_database.db'
temp_file_dir = './temp'
file_dir_pick_list = './processed'
file_dir_erro = './errors'
unknown_products_errors = './unknown_products_errors.log'
unknown_extras_errors = './unknown_extras_errors.log'
dlv = True
Funcionalidades
1. Teste de Conexão com a API
A função teste_api_connection() verifica a conectividade com a API remota. Se a API estiver online, define o sistema como online, caso contrário, o define como offline.

2. Processamento de Arquivos Temporários
A função check_temp_files() verifica se há arquivos temporários de recibos para processar na pasta especificada. Se houver arquivos, retorna o primeiro arquivo encontrado.

3. Processamento de Linhas de Arquivos
A função file_processing() limpa e formata as linhas de um arquivo de recibo para serem analisadas posteriormente. Ela remove caracteres especiais e imprime as linhas processadas.

4. Extração de Informações de Pedidos
O sistema analisa cada linha processada para extrair informações de produtos e ingredientes. Ele utiliza o identificador "PEDIDO" ou "DRIVE" para localizar o código de pedido (dependendo do modo dlv).

5. Busca de Dados em API ou Banco de Dados Local
A função teste_api_connection() tenta buscar os dados dos produtos e ingredientes via API. Se a API estiver offline, o sistema utiliza o banco de dados SQLite local para buscar as informações.

6. Salvamento de Produtos Desconhecidos
Caso o sistema não encontre um produto ou ingrediente, ele salva o item no arquivo de log de produtos desconhecidos usando a função save_erro().

7. Cálculo de Peso
A função realiza o cálculo do peso total de cada item no pedido, incluindo o peso dos ingredientes extras e a variação devido a ingredientes removidos ou adicionados.

8. Envio de Dados para a API
Após processar o recibo, o sistema envia as informações para a API via requisição POST. Caso a conexão com a API falhe, os dados são armazenados no banco de dados local e marcados como pendentes.

9. Log de Erros
Todos os erros durante o processamento são logados no arquivo de erros. Os arquivos que não puderam ser processados são movidos para uma pasta de erros.

Fluxo de Execução
Inicialização do Sistema: O sistema verifica constantemente se há arquivos de recibos temporários para processar.
Processamento de Linhas: Ao encontrar um arquivo, ele formata e processa cada linha do recibo.
Extração de Dados: As informações do pedido, como produtos e ingredientes extras, são extraídas das linhas do recibo.
Verificação de Dados: O sistema tenta buscar informações dos produtos na API ou no banco de dados local.
Cálculo do Peso: O peso de cada item do pedido é calculado, levando em consideração os ingredientes extras ou removidos.
Envio de Dados: Os dados do pedido são enviados para a API ou salvos no banco de dados local, dependendo da conectividade.
Conclusão do Processo: O arquivo é movido para a pasta de processados ou erros, dependendo do resultado do processamento.
Tratamento de Erros
Erros e exceções são logados em arquivos dedicados. A função save_erro() captura e salva erros relacionados a produtos e ingredientes desconhecidos. A função log_error() pode ser usada para registrar outros erros críticos durante o processo.

Principais Funções
Função	Descrição
teste_api_connection()	Testa a conexão com a API remota.
check_temp_files()	Verifica a existência de arquivos temporários de recibo para processar.
file_processing()	Processa as linhas do arquivo de recibo, removendo caracteres indesejados.
save_erro()	Salva produtos ou ingredientes desconhecidos em arquivos de log de erro.
open_database_connection()	Abre conexão com o banco de dados SQLite.
main()	Função principal que verifica e processa arquivos de recibo continuamente.
file_processing()	Formata as linhas do arquivo temporário para análise e extração de dados.
save_erro()	Loga e armazena produtos ou ingredientes que não possuem correspondência no banco de dados.
json.dumps()	Converte a lista de objetos PickList em uma string JSON estruturada para envio ou armazenamento.
Conclusão
Este sistema foi projetado para automatizar o processamento de pedidos a partir de recibos temporários, integrando o uso de uma API e um banco de dados local para garantir que todos os dados dos produtos sejam corretamente processados e armazenados. O sistema também gerencia erros de forma eficiente, movendo arquivos malformados para pastas de erro e gerando logs detalhados para referência futura.
