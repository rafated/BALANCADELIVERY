import requests
import time
import json
import os
from os import walk
import sqlite3
import datetime
from array import array
import config #importa as configurações/variáveis globais para cada instalação

# Cores para mostrar as mensagens na consola
RED = "\033[1;31m"  
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
CYAN  = "\033[1;36m"

class pick_list:
    def __init__(self):
            self.name = ""
            self.quantidade = []
            self.extra =[]

    def __repr__(self):
        return pick_list

 #guarda os produtos que não têm correspondencia na BD
def save_erro(erro_file,erro_str):
    # Cria a string com a data atual
    t = datetime.datetime.now()
    s=t.strftime('%Y/%m/%d %H:%M:%S')

    file_obj = open(erro_file, 'a')
    file_obj.write(s+'; '+erro_str+'\n')# guarda a data num ficheiro txt
    file_obj.close()

 #identifica todos os ficheiros na pasta dos recibos temporários (config.file_dir_pick_list)
def check_temp_files():
    filenames = []
    for dirpath, dirnames, files in os.walk(config.file_dir_pick_list):
        filenames.extend(files)
        break  # Parar após o primeiro nível, se não desejar explorar subdiretórios.
    
    if filenames:
        print(GREEN + "Há ficheiros para processar" + RESET)
        print("Ficheiros:", filenames)
        return filenames[0]  # Retorna o primeiro arquivo encontrado
    else:
        return None  #Nenhum arquivo encontrado

def file_processing(file_name, lines):
    file_path = os.path.join(config.file_dir_pick_list, file_name)
    if not file_name:
        print(RED + "Nenhum arquivo para processar." + RESET)
        return  
    with open(config.file_dir_pick_list+'//'+file_name, "r") as file:
        for line in file: 
            line = line.upper()
            #print(line)8
            line = line.replace("\\X1BD","").replace("\\X1DVB","").replace("\\N'","").replace('\\N"',"").replace("\\X1BE","").replace("\\X00","").replace("\\X1BA","").replace("\\X1D!D","").replace("\\X1DB","").replace("\\X1DBD","")
            #print(line)
            line = line.replace("B'","").replace('B"',"").replace('"',"").replace("\\X01","").replace("\\X11","").replace("\\R\\X1DL","").replace("\\X1DR'","").replace("\\X1D!","").replace("\\R","").replace("\\X1DR","").replace("\\X1BT","").replace("\\X10","").replace("\\X1DL","").strip()
            #print (line)
            line = line.strip()
            lines.append(line) #storing everything in memory!
            print(CYAN + line + RESET)
        return

def open_database_connection():
    try:
        # Cria uma conexão ao banco de dados
        con = sqlite3.connect(config.db)
        # Cria um cursor para manipular os dados
        cur = con.cursor()
        # Inicia a variável para o estado inicial da pick list (0 = não confirmada, 1 = confirmada)
        estadoinicial = 0
        return con, cur, estadoinicial
    # Caso haja algum erro durante a abertura da base de dados, imprime uma mensagem de erro e retorna None
    except sqlite3.Error as e:
        print(RED + "Erro ao abrir a base de dados: {e}" +  RESET)
        return None, None, None

def get_string_time():
    current_time = datetime.datetime.now()
    time_string = current_time.strftime('%Y%m%d_%Hh%Mm%Ss')
    return time_string

lines = []

def main():
    #Chamada da função para conexão com o banco de dados
    con, cur, estadoinicial = open_database_connection()
    if con is not None:
        print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)

    print(GREEN + "Inicializando Recibo Processing" + RESET)
    t = 1 
    while (True):
        try:
            print(GREEN + "Buscando ficheiros para procesar" + RESET)
            file_name = check_temp_files()

            if(file_name == None):
                #Espera mais cinco segundos antes de prcurar outro arquivo
                time.sleep(5)
                continue   
            print(CYAN + file_name +  RESET)

            file_processing(file_name, lines)

            array_posicao = 0
            linha_pedido = 0
            array_str_pedido = []
            nr_pedido = 1
            
            #----------------------------------------------------------------------------
                                            #OBSERVAÇÃO
            #Toda informção que precisamos para fazer o cálculo da pesagem se encontra
            #entre as palvras IVA presente na fatura (Verficiar na pasta temp_faturas)
            #----------------------------------------------------------------------------
        
            for word in lines:
                if "PEDIDO" in word:
                    codigo_delivery=lines[array_posicao + 1]
                    linha_pedido=array_posicao
                    array_str_pedido.append(array_posicao)
                array_posicao=array_posicao+1
            
            print(codigo_delivery)
            PickList = []
            product_index = 0 #flag contador de produtos numa pick list
            c = 0 #flag contador de extras de cada produto
            
            #Caso exista mais que uma pick_list no mesmo recibo, ignora todas exceto a primeira
            for i in range (array_str_pedido[0] - 1): #Pica linha a linha os produtos
                ing = []
                word = []
                word = lines[i+1].split()  # Separa a linha em palavras
                if len(word):
                    if word[0]=="TAKE":
                        for word in lines[i].split():
                            if word.isdigit():
                                nr_pedido=int(word)
                    if word[0].isdigit():   #caso a primeira "palavra" seja um número, então estamos perante um produto
                        PickList.append(pick_list())    #adiciona ao array um novo objeto
                        
                        PickList[product_index].quantidade=word[0]  #define a quantidade
                        #print(word[0])
                        word.pop(0)     #apaga a quantidade da linha
                        p=" ".join(word)    #junta todas as palavras da linha

                        #Procura na base de dados uma correspondência (tabela designação)
                        cur.execute("SELECT * FROM produtos INNER JOIN designacao on designacao.produto_id = produtos.produto_id WHERE designacao.nome = :name ",{"name":p})
                        resposta = cur.fetchall()
                        #print(resposta)

                        if resposta:#Caso haja correspondência 
                            print(resposta)
                            PickList[product_index].name = resposta[0][1]
                            PickList[product_index].peso = resposta[0][2]
                            PickList[product_index].variancia = resposta[0][3]
                            PickList[product_index].peso_natura = resposta[0][4]
                            PickList[product_index].tipo = resposta[0][5]
                        else:
                            if ((p==r"N\X84O, OBRIGADO!") or (p==r"TAXA SERVI\X87O") or (p==r"SEM MOLHO"))!= 1:
                                #Caso não seja nenhuma das apresentadas acima
                                PickList[product_index].name = p
                                PickList[product_index].peso = 0
                                PickList[product_index].variancia = 0
                                PickList[product_index].peso_natura = 0
                                PickList[product_index].tipo = "Sanduiche"
                                
                                
                                print(RED + 'ERROS: '+str(p) + RESET)    #mostrar quando não há correspondência
                                save_erro(config.file_produto_desconhecido,str(p)) #Guarda o artigo no seguinte ficheiro
                        
                        product_index += 1
                        c = 0  # faz reset ao contador de extras
#------------------------------------------SESSÃO 1---------------------------------------------------------------
                    else: #caso a primeira palavra não seja um número
                        q = 1 # flag quantidade
                        
                        #Ignora o o caractere na hora do processamento (Esse caracrtere separa cada classe de produto dentro da Picklist)
                        if word[0]=="-":
                            asv=0    
                        elif word[0]=="SEM":
                            print(word)
                            ing=word[:]#Copia o array word
                            ing.pop(0) #Apaga a primeira palavra
                            p=" ".join(ing)#Junta todas as palavras da linha
                            if word[1].isdigit():#Caso os extras tenham quantidades (ex. Extra 2 queijo)
                                q=int(word[1])#Guarda a quantidade de extras
                                ing.pop(0)
                                p=" ".join(ing)
                            
                            #Procura na base de dados uma correspondência (tabela ingredientes)
                            cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                            resposta=cur.fetchall()

                            if resposta:
                                peso_extra=resposta[0][2] * q *(-1)#Peso vezes a quantidade (default q = 1)
                            else:
                                #Todos os extras "não conhecidos"
                                save_erro(config.file_extra_desconhecido,p)#Guarda o extra no seguinte ficheiro
                                print("Erro Sessão 1 - Extra não conhecido: " + str(p))
                                peso_extra=0#Define variavel peso extra

                            str_extra=" ".join(word)#Define o texto dos extras para guardar na pick list

                            if c == 0:#se for o primeiro extra do produto
                                PickList[product_index - 1].extra = [str_extra]
                                PickList[product_index - 1].extra_peso = [peso_extra]
                            else:       #para os restantes extras do produtos
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]                                
                            c = c + 1 #flag contador de extras de cada pedido
#------------------------------------------SESSÃO 2---------------------------------------------------------------                            
                        elif word[0]=="COM":
                            print(word)
                            ing=word[:] #copia o array word
                            ing.pop(0)#apaga a primeira palavra
                            p=" ".join(ing)    #junta todas as palavras da linha
                            if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                q=int(word[1]) #guarda a quantidade de extras
                                ing.pop(0)
                                p=" ".join(ing)

                            #Procura na base de dados uma correspondência (tabela ingredientes)
                            cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                            resposta = cur.fetchall()

                            if resposta:
                                peso_extra = resposta[0][2] * q #peso vezes a quantidade (default q =1)
                            else:
                                #todos os extras "não conhecidos"
                                save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                print("Erro Sessão 2 - Extra não conhecido: " + str(p))
                                peso_extra = 0 #define variavel peso extra

                            str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list

                            if c == 0:    #se for o primeiro extra do produto
                                PickList[product_index - 1].extra = [str_extra]
                                PickList[product_index - 1].extra_peso = [peso_extra]
                            else:       #para os restantes extras do produtos
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                
                            c = c + 1 #flag contador de extras de cada pedido                                
#------------------------------------------SESSÃO 3---------------------------------------------------------------                  
                        elif word[0] == "EXTRA":
                            print(word)
                            ing=word[:] #copia o array word
                            ing.pop(0)#apaga a primeira palavra
                            p=" ".join(ing)    #junta todas as palavras da linha
                            if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                q=int(word[1]) #guarda a quantidade de extras
                                ing.pop(0)
                                p=" ".join(ing)
                      
                            #Procura na base de dados uma correspondência (tabela ingredientes)
                            cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                            resposta=cur.fetchall()

                            if resposta:
                                peso_extra = resposta[0][2] * q #peso vezes a quantidade (default q =1)
                            else:
                                #todos os extras "não conhecidos"
                                save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                print("Erro Sessão 3 - Extra não conhecido: " + str(p))
                                peso_extra = 0 #define variavel peso extra

                            str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
                            
                            if c == 0:    #se for o primeiro extra do produto
                                PickList[product_index - 1].extra = [str_extra]
                                PickList[product_index - 1].extra_peso = [peso_extra]
                            else:       #para os restantes extras do produtos
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                            
                            c = c + 1 #flag contador de extras de cada pedido
#------------------------------------------SESSÃO 4---------------------------------------------------------------  
                        elif word[0]=="SO":
                            print(word)
                            PickList[product_index - 1].natura="True"
                            ing=word[:] #copia o array word
                            ing.pop(0)#apaga a primeira palavra
                            p=" ".join(ing)    #junta todas as palavras da linha
                            if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                q=int(word[1]) #guarda a quantidade de extras
                                ing.pop(0)
                                p=" ".join(ing)
                            
                            # procura na base de dados uma correspondência (tabela ingredientes)
                            cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                            resposta = cur.fetchall()
                    
                            if resposta:
                                peso_extra = resposta[0][2] * q #peso vezes a quantidade (default q =1)
                            else:
                                #todos os extras "não conhecidos"
                                save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                print("Erro Sessão 4 - Extra não conhecido: " + str(p))
                                peso_extra = 0 #define variavel peso extra

                            str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list

                            if c == 0:    #se for o primeiro extra do produto
                                PickList[product_index-1].extra = [str_extra]
                                PickList[product_index-1].extra_peso = [peso_extra]
                            else:       #para os restantes extras do produtos
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                        
                            c = c + 1 #flag contador de extras de cada pedido
#------------------------------------------SESSÃO 5---------------------------------------------------------------  
                        elif word[0] == "NATURA" or word[0] == "PLAIN":
                            print(word)
                            PickList[product_index - 1].natura = "True"
                            peso_extra = 0 #peso extra é 0
                            
                            str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
                            if c == 0:    #se for o primeiro extra do produto
                                PickList[product_index - 1].extra = [str_extra]
                                PickList[product_index - 1].extra_peso = [peso_extra]
                            else:       #para os restantes extras do produtos
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                            
                            c = c + 1 #flag contador de extras de cada pedido
                        elif word[0][0] == "-":
                                #do nada
                                asd=0
                        elif word[0] == "TAKE" or word[0] == "OUT" or word[0] == "ORDER":
                            #do nada
                            asd=0 
                        else:
                            #todos os tipos de extras "não conhecidos"
                            p = " ".join(word)
                            
                            save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                            print("Erro Sessão 5 - Extra não conhecido: " + str(p))

                            peso_extra = 0 #peso extra é 0
                            
                            str_extra = p #Define o texto dos extras para guardar na pick list
                            if c == 0:    #se for o primeiro extra do produto
                                PickList[product_index - 1].extra = [str_extra]
                                PickList[product_index - 1].extra_peso = [peso_extra]
                            else:       #para os restantes extras do produtos
                                PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                
                            c = c + 1 #flag contador de extras de cada pedido
#---------------------------------------------CÁLCULO DO PESO-----------------------------------------------------------------  
            #calcular peso total de cada produto
            for i in range(len(PickList)):
                peso = 0
                if PickList[i].name:
                    if hasattr(PickList[i],'natura'): #verifica se o objeto tem o atributo natura
                        peso = PickList[i].peso_natura
                    else:
                        peso = PickList[i].peso

                    if hasattr(PickList[i],'extra_peso'):
                        peso = sum(PickList[i].extra_peso)
                    PickList[i].peso_produto=peso                
                print(peso)
            print(GREEN + "Soma efetuada." +RESET)
#---------------------------------------------COMMIT PARA A BD-----------------------------------------------------------------  
            # Convert to JSON string
            jsonStr = json.dumps([ob.__dict__ for ob in PickList], indent=4, sort_keys=True)
            print(jsonStr)
            #Insert into database
            if con is not None:
                cur.execute("INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado) VALUES (:numero_pedido, :list, :file_name, :estado, :estado)",
                    {"numero_pedido": codigo_delivery,
                    "list": str(jsonStr), 
                    "file_name": file_name, 
                    "estado":estadoinicial})
                con.commit()
                print(GREEN + "PickList gravada com sucesso no banco de dados." + RESET)
            
            flag_molho = 0

            os.rename(config.file_dir_pick_list+'//'+file_name, config.temp_file_dir+'//'+file_name)
            lines.clear()  

            #caso tenha várias pick list no mesmo "recibo"
            if len(array_str_pedido) > 2:
                print(GREEN + 'O pedido possui várias PickList.' +  RESET)
                logf = open("Erro_Log.log", "a")
                time_string = get_string_time()
                logf.write(time_string + "; Recibo_processing" + "Várias pick_list" + str(file_name) + '\n')
                logf.close()
#---------------------------------------------LOG DE ERRO-----------------------------------------------------------------  
        except Exception as e:
            time.sleep(2)
            os.rename(config.file_dir_pick_list+'//'+file_name, config.file_dir_erro+'//'+file_name)
            print(RED + "Erro no processamento da PickList." + RESET)
            print(e)
            #break
    con.close()        

if __name__ == '__main__':
    main()
