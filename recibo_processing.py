#Código atualizado --07 de Outubro de 2024-- 2h47
import requests
import time
import json
import os
from os import walk
import sqlite3
import datetime
from array import array
import config  # importa as configurações/variáveis globais para cada instalação
from urllib3.exceptions import InsecureRequestWarning
import re

# Suprimir o aviso de request inseguro
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Cores para mostrar as mensagens na consola
RED = "\033[1;31m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
CYAN = "\033[1;36m"

class pick_list:
    def __init__(self):
        self.name = ""
        self.quantidade = []
        self.extra = []

    def __repr__(self):
        return pick_list

def do_nothing():
    return

def get_string_time():
    current_time = datetime.datetime.now()
    time_string = current_time.strftime('%Y%m%d_%Hh%Mm%Ss')
    return time_string

# Guarda os produtos que não têm correspondência na BD
def save_erro(erro_file, erro_str):
    time_string = get_string_time()
    with open(erro_file, 'a') as file_obj:
        file_obj.write(time_string + '; ' + erro_str + '\n')

# Identifica todos os ficheiros na pasta dos recibos temporários
def check_temp_files():
    filenames = []
    for dirpath, dirnames, files in os.walk(config.temp_file_dir):
        filenames.extend(files)
        break  # Parar após o primeiro nível, se não desejar explorar subdiretórios.
    
    if filenames:
        print(GREEN + "Há ficheiros para processar" + RESET)
        print("Ficheiros:", filenames)
        return filenames[0]  # Retorna o primeiro arquivo encontrado
    else:
        return None  # Nenhum arquivo encontrado

def file_processing(file_name, lines):
    if not file_name:
        print(RED + "Nenhum arquivo para processar." + RESET)
        return  
    with open(os.path.join(config.temp_file_dir, file_name), "r") as file:
        for line in file: 
            line = line.upper()
            line = line.replace("\\X1BD","").replace("\\X1DVB","").replace("\\N'","").replace('\\N"',"").replace("\\X1BE","").replace("\\X00","").replace("\\X1BA","").replace("\\X1D!D","").replace("\\X1DB","").replace("\\X1DBD","")
            line = line.replace("B'","").replace('B"',"").replace('"',"").replace("\\X01","").replace("\\X11","").replace("\\R\\X1DL","").replace("\\X1DR'","").replace("\\X1D!","").replace("\\R","").replace("\\X1DR","").replace("\\X1BT","").replace("\\X10","").replace("\\X1DL","").strip()
            line = line.strip()
            lines.append(line)
            print(CYAN + line + RESET)
        return

def teste_api_connection():
    print(GREEN + "Testando conexão à API" + RESET)
    try:
        # Adicionando um timeout de 3 segundos
        headers = {
            'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
        }
        response = requests.get(config.api_url, verify=False, timeout=3, headers=headers)
        if response.status_code == 200:
            print(GREEN + "Conexão à API bem-sucedida" + RESET)
            config.set_api_online()
            return 1
        else:
            print(RED + f"Falha na conexão à API: Status Code {response.status_code}" + RESET)
            config.set_api_offline()
            return 0
    except requests.exceptions.Timeout:
        print(RED + "Falha na conexão à API: Tempo de resposta excedido (timeout)" + RESET)
        config.set_api_offline()
        return 0
    except requests.exceptions.RequestException as e:
        print(RED + "Falha na conexão à API: " + str(e) + RESET)
        config.set_api_offline()
        return 0


def open_database_connection():
    try:
        # Cria uma conexão ao banco de dados
        con = sqlite3.connect(config.data_base)
        # Cria um cursor para manipular os dados
        cur = con.cursor()
        # Inicia a variável para o estado inicial da pick list (0 = não confirmada, 1 = confirmada)
        estadoinicial = 0
        return con, cur, estadoinicial
    # Caso haja algum erro durante a abertura da base de dados, imprime uma mensagem de erro e retorna None
    except sqlite3.Error as e:
        return None, None, None


lines = []
#------------------------------------------SESSÃO FILE PROCESSING---------------------------------------------------------------------  
def main():
    print(GREEN + "Inicializando Recibo Processing" + RESET)
    while True:
        try:
            print(GREEN + "Buscando ficheiros para procesar" + RESET)
            file_name = check_temp_files()

            if file_name is None:
                time.sleep(5)
                continue   
            print(CYAN + file_name +  RESET)

            file_processing(file_name, lines)
#------------------------------------------DECLARAÇÃO DE VARIÁVIES---------------------------------------------------------------------
            # Variáveis
            array_str_pedido = []
            PickList = []
            estadoinicial = 0
            array_posicao = 0
            linha_pedido = 0
            nr_pedido = 1
            product_index = 0
            c = 0
            codigo_delivery = 0
            apenas = False
#------------------------------------------SESSÃO EXTRAIR CÓDIGO DELIVERY-------------------------------------------------------------    
            identifier = ""
            if(config.dlv == True):
                identifier = "PEDIDO"
            else:
                identifier = "DRIVE"    
            for word in lines:
                if identifier in word:
                    if(config.dlv == True):
                        codigo_delivery = lines[array_posicao + 1]
                    else:
                        codigo_delivery = lines[array_posicao + 1]
                    linha_pedido = array_posicao
                    array_str_pedido.append(array_posicao)
                    break
                array_posicao += 1
            print(codigo_delivery)
#-------------------------------------------------------------------------------------------------------------------------------------    
            for i in range(array_str_pedido[0] - 1):
                ing = []
                word = []
                word = lines[i+1].split()
                if len(word):
                    if word[0] == "TAKE":
                        for word in lines[i].split():
                            if word.isdigit():
                                nr_pedido = int(word)
                    if word[0].isdigit():
                        if " ".join(word[1:]).upper() in ["SEM SACO", "TAXA SACO"]:
                            continue  # Ignorar essas linhas
                        PickList.append(pick_list())
                        PickList[product_index].quantidade = word[0]
                        word.pop(0)
                        
                        if re.match(r'\d+P$', word[-1]):  # funciona para indetermináveis promocões
                            word.pop()
                            print("promo")

                        p = " ".join(word)
#------------------------------------------BUSCA DE DADOS -------------------------------------------------------------------------  
                        api_connection = teste_api_connection()
                        headers = {
                            'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
                        }
                        #CONEXÃO FEITA COM SUCESSO
                        if(config.api_offline == False):
                            url = config.api_url + "/produtos"
                            params = {"name": p}

                            response = requests.get(url, params=params, headers=headers, verify=False)  # Verify False for development only

                            if response.status_code == 200:
                                resposta = response.json()
                                print(resposta)
                                print(GREEN + "Operção efetuada com sucesso" + RESET)
                            else:
                                resposta = None
                                print(RED + f"Erro: {response.status_code}" + RESET)
                                continue
                        #CONEXÃO NÃO ESTABELECIDA COM SUCESSO
                        else:
                            config.set_api_offline()
                            #Chamada da função para conexão com o banco de dados
                            con, cur, estadoinicial = open_database_connection()
                            if con is not None:
                                print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
                                cur.execute("SELECT * FROM produtos INNER JOIN designacao on designacao.produto_id = produtos.produto_id WHERE designacao.nome = :name ",{"name":p})
                                resposta = cur.fetchall()
                                print(resposta)
                            else:
                                print(RED + "Erro ao abrir a base de dados" + RESET)    
#-------------------------------------------------------------------------------------------------------------------------------------  
                        if (resposta):
                            if(config.api_offline == False):
                                produto = resposta[0]
                                PickList[product_index].name = produto.get('Produto_name', 'Desconhecido')
                                PickList[product_index].peso = produto.get('Peso_total', 0)
                                PickList[product_index].variancia = produto.get('Variancia', 0)
                                PickList[product_index].peso_natura = produto.get('Peso_Natura', 0)
                                PickList[product_index].tipo = produto.get('tipo', 'Desconhecido')
                            if(config.api_offline == True):
                                PickList[product_index].name = resposta[0][1]
                                PickList[product_index].peso = resposta[0][2]
                                PickList[product_index].variancia = resposta[0][3]
                                PickList[product_index].peso_natura = resposta[0][4]
                                PickList[product_index].tipo = resposta[0][5]
                        else:
                            if ((p == r"N\X84O, OBRIGADO!") or (p == r"TAXA SERVI\X87O") or (p == r"SEM MOLHO")) != 1:
                                PickList[product_index].name = p
                                PickList[product_index].peso = 0
                                PickList[product_index].variancia = 0
                                PickList[product_index].peso_natura = 0
                                PickList[product_index].tipo = "Sanduiche"
                                print(RED + 'Erro, sem correspondência do seguinte produto no banco de dados: '+str(p) + RESET)
                                save_erro(config.unknown_products_errors, str(p))

                        product_index += 1
                        c = 0
#------------------------------------------SESSÃO PROCESSAMENTO DE EXTRAS---------------------------------------------------------------
                    else:
                        q = 1
                        peso_extra = 0
                        if word[0] in ["APENAS", "SO"]:
                                apenas = True
                        if word[0] in ["COM", "EXTRA", "SO", "SEM", "NATURA", "PLAIN", "APENAS"]:
                            if word[0] in ["EXTRA"] and word[1] in ["NATURA", "PLAIN"]:
                                PickList[product_index - 1].natura = "True"
                                peso_extra = 0
                            if word[0] in ["NATURA", "PLAIN"]:
                                PickList[product_index - 1].natura = "True"
                                peso_extra = 0
                            else:
                                ing = word[:]
                                ing.pop(0)
                                p = " ".join(ing)
                                if word[1].isdigit():
                                    q = int(word[1])
                                    ing.pop(0)
                                    p = " ".join(ing)
#------------------------------------------BUSCA DE DADOS -------------------------------------------------------------------------      
                                api_connection = teste_api_connection()
                                headers = {
                                    'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
                                }
                                #CONEXÃO FEITA COM SUCESSO
                                if(api_connection == 1 and config.api_offline == False):
                                    url = config.api_url + "/ingredientes"
                                    params = {"name": p}

                                    response = requests.get(url, params=params, headers=headers, verify=False)  # Verify False for development only

                                    if response.status_code == 200:
                                        resposta = response.json()
                                        print(resposta)
                                        print(GREEN + "Operção efetuada com sucesso" + RESET)
                                    else:
                                        resposta = None
                                        print(RED + f"Erro: {response.status_code}" + RESET)

                                    if resposta:
                                        if(word[0] in ["APENAS", "SO"]) and resposta[0]['nome'] in ["CARNE MCROYAL", "CARNE"]:
                                            print("Produto com APENAS ou SO")
                                            print("Anulando peso da carne")
                                            peso_extra = 0
                                        elif word[0] == "SEM":
                                            peso_extra_ingrediente = resposta[0]['peso']
                                            peso_extra = peso_extra_ingrediente * q * (-1)
                                        else:
                                            peso_extra_ingrediente = resposta[0]['peso']
                                            peso_extra = peso_extra_ingrediente * q
                                    else:
                                        save_erro(config.unknown_extras_errors, p)
                                        print("Erro Sessão COM/EXTRA/SO/SEM - Extra não conhecido: " + str(p))
                                        peso_extra = 0
                                #CONEXÃO NÃO ESTABELECIDA COM SUCESSO
                                else:
                                    con, cur, estadoinicial = open_database_connection()
                                    #Chamada da função para conexão com o banco de dados
                                    if con is not None:
                                        print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
                                        #Procura na base de dados uma correspondência (tabela ingredientes)
                                        cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                        resposta = cur.fetchall()
                                        print(resposta)
                                    else:
                                            print(RED + "Erro ao abrir a base de dados" + RESET) 
                                    if resposta:
                                        if word[0] == "SEM":
                                            peso_extra_ingrediente = resposta[0][2]
                                            peso_extra = peso_extra_ingrediente * q * (-1)
                                        else:
                                            peso_extra_ingrediente = resposta[0][2]
                                            peso_extra = peso_extra_ingrediente * q
                                    else:
                                        save_erro(config.unknown_extras_errors, p)
                                        print("Erro Sessão COM/EXTRA/SO/SEM - Extra não conhecido: " + str(p))
                                        peso_extra = 0
#-------------------------------------------------------------------------------------------------------------------------------------  
                            str_extra = " ".join(word)

                            if c == 0:
                                PickList[product_index - 1].extra = [str_extra]
                                PickList[product_index - 1].extra_peso = [peso_extra]
                            else:
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                
                            c += 1

                        elif word[0] in ["--------------------", "---------------------------------------", "--------------------" "TAKE", "OUT", "ORDER"]:
                            do_nothing() 
                        else:
                            p = " ".join(word)
                            save_erro(config.unknown_extras_errors, p)
                            print("Erro no processamento do EXTRA - Extra não conhecido: " + str(p))

                            peso_extra = 0
                            str_extra = p
#---------------------------------------------CÁLCULO DO PESO-----------------------------------------------------------------  
            for i in range(len(PickList)):
                peso = 0
                if PickList[i].name:
                    if hasattr(PickList[i], 'natura'):
                        peso = PickList[i].peso_natura
                    else:
                        peso = PickList[i].peso

                    if hasattr(PickList[i], 'extra_peso'):
                        if(apenas == True):
                            print("Calculando o peso APENAS")
                            #peso somente dos ingredientes
                            peso_somente_ingredientes = (PickList[i].peso - PickList[i].peso_natura)
                            #peso do ingredientes que não fazem parte do hamburguer
                            peso_ingrientes_fora = peso_somente_ingredientes - sum(PickList[i].extra_peso)
                            peso = PickList[i].peso - peso_ingrientes_fora
                        else:
                            peso = sum(PickList[i].extra_peso) + PickList[i].peso
                    PickList[i].peso_produto = peso                
                print(peso)
            print(GREEN + "Soma efetuada." +RESET)
            apenas = False
#---------------------------------------------COMMIT PARA PARA O BANCO DE DADOS-----------------------------------------------------------------  
            jsonStr = json.dumps([ob.__dict__ for ob in PickList], indent=4, sort_keys=True)
            print(jsonStr)
            time_stamp = get_string_time()
            codigo_restaurante = config.rest_code
            api_connection = teste_api_connection()
            #CONEXÃO FEITA COM SUCESSO
            headers = {
                'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
            }
            if(api_connection == 1 and config.api_offline == False):
                url = config.api_url + "/pick_list"
                data = {      
                    "numero_pedido": codigo_delivery,
                    "list": str(jsonStr),
                    "file_name": file_name,
                    "estado": estadoinicial,
                    "pendente": 0,
                    "codigo_restaurante": codigo_restaurante,
                    "time_stamp": time_stamp
                }
                response = requests.post(url, json=data, headers=headers, verify=False)  # Verify False for development only

                if response.status_code == 201:
                    print(GREEN + "Dados inseridos com sucesso" + RESET)
                else:
                    print(RED + f"Erro: {response.status_code}" + RESET)
            #CONEXÃO NÃO ESTABELECIDA COM SUCESSO
            else:
                config.set_api_offline()
                #Declara que um pedido será inderido na base de dados local, oque 
                config.set_pending_order_true()
                pendente = 1

                #Chamada da função para conexão com o banco de dados
                con, cur, estadoinicial = open_database_connection()
                if con is not None:
                    cur.execute(
                    """
                    INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado, pendente, codigo_restaurante, time_stamp)
                    VALUES (:numero_pedido, :list, :file_name, :estado, :estado, :pendente, :codigo_restaurante, :time_stamp)
                    """,
                    {
                        "numero_pedido": codigo_delivery,
                        "list": str(jsonStr),
                        "file_name": file_name,
                        "estado": estadoinicial,
                        "pendente": pendente,
                        "codigo_restaurante": config.rest_code,
                        "time_stamp": time_stamp,
                    })
                    con.commit()
                    con.close()
                    print(GREEN + "PickList gravada com sucesso no banco de dados." + RESET)
                else:
                    print(RED + "Erro ao abrir a base de dados" + RESET)

            flag_molho = 0

            os.rename(os.path.join(config.temp_file_dir, file_name), os.path.join(config.file_dir_pick_list, file_name))
            lines.clear()

            if len(array_str_pedido) > 2:
                print(GREEN + 'O pedido possui várias PickList.' +  RESET)
                with open(config.errors_log, "a") as logf:
                    time_string = get_string_time()
                    logf.write(time_string + "; Recibo_processing" + "Várias pick_list" + str(file_name) + '\n')
#---------------------------------------------LOG DE ERRO----------------------------------------------------------------- 
        except Exception as e:
            time.sleep(2)
            os.rename(os.path.join(config.temp_file_dir, file_name), os.path.join(config.file_dir_erro, file_name))
            print(RED + "Erro no processamento da PickList." + RESET)
            print(f'{e}')
            # break    
 
if __name__ == '__main__':
    main()
