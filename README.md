## Melhorias em Andamento

Esse projeto tem como core a reestruturação de uma solução já existente, focando na centralização do banco de dados e adição de novas features.
No que dita a centralização será usada uma API em nodejs que recebe as requisições do cliente (python), através de métodos HTTP. Receberemos essas requisões no servidor conectada pela API em nodejs. Fazendo então a busca baseada na requisição do cliente no banco de dados.

## Solução **(Balança)**

## 1.1 Introdução:
A solução foi criada com o obejetivo de verificar a exatidão na montagem de pedidos DLV e DT utilizando como base de cálculo o pedido recebido e o peso de cada item para verificação

## 1.2 Estrutura e Linguagens: 

### O projeto está estruturado em três processos:

#### 1.2.1 Save_data_printer: 
Esse processo abre uma porta Serial para interceptar o sinal enviado do OT para a impressora. Recebido esse sinal o mesmo é filtrado excluindo espaços nulos e buscando uma sequência de caracteres específica, presente no conjunto de dados que é preciso durante o workflow. Cada conjunto de dados é guardado em uma pasta de ficheiros temporários sendo o seu nome a concatenação do counter e uma string com o datetime atual da criação do arquivo.

#### 1.2.2 Recibo_processing: 
Nesta etapa é buscado todos os ficheiros temporários gerados pelo processo anterior, identificando o seu tipo, tal como no save_data_priter seleciona somente oque será útil. Nessa altura já temos a pick_list pura, restando então somente a identificação de cada item da mesma e sua respectiva associação aos produtos presentes no Banco de dados. 
Nesse processo também é feito o commit para a tabela pick_list de todos os dados relevantes, tais como:

- delivery_name
- list
- pick_list_file
- state 
- confirmado

#### 1.2.3 GUI_pesagem:
Nesse processo é criada toda a interface de usuário usando o PySimpleGUI,  efetuamos o a pesagem do pedido buscando pelo delivery_name todas as informações necessárias para a realização da mesma. O pedido sendo pesado e o sistema confirmando que o peso corresponde com o valor esperado é então tirada uma foto do pedido. Por fim fazemos o storage de cada pesagem na DB para futuras buscas feitas pelo GUI_histórico.




