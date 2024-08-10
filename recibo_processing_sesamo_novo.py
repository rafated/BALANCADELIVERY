import requests
import time
import json
import os
from os import walk
import sqlite3
import datetime
from array import array
import re
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

 #identifica todos os ficheiros na pasta dos recibos temporários (config.temp_file_dir)
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
        #print(RED + "Não há ficheiros para processar" + RESET)
        return None  #Nenhum arquivo encontrado

def file_processing(file_name, lines):
    file_path = os.path.join(config.temp_file_dir, file_name)
    if file_name is None:
        print(RED + "Nenhum arquivo para processar." + RESET)
        return
    
    # Abre o arquivo e processa linha a linha
    with open(file_path, "r") as file:
        for line in file: 
            line = line.upper()
            line = line.replace(r"\\X1BD","").replace(r"\\X1DVB","").replace(r"\\N'","").replace(r'\\N"',"").replace(r"\\X1BE","").replace(r"\\X00","").replace(r"\\X1BA","").replace(r"\\X1D!D","").replace(r"\\X1DB","").replace(r"\\X1DBD","").replace(r"\\X1D!","")
            line = line.replace("B'","").replace('B"',"").replace('"',"").replace(r"\\X01","").replace(r"\\X11","").replace(r"\\R\\X1DL","").strip()
            lines.append(line) # Armazena tudo em memória
            print(line)
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
        print("Erro ao abrir a base de dados: {e}")
        return None, None, None

def extract_order_numbers(lines):
    # Converte o conteúdo do arquivo de uma lista de strings para uma única string
    conteudo = ''.join(lines)
    
    # Expressão regular para encontrar padrões GLV ou UE seguidos por caracteres e números
    padrao = r'\b(GLV|UE)\s*([A-Z0-9]+)\b'
    
    # Encontrar todas as ocorrências que correspondem ao padrão
    correspondencias = re.findall(padrao, conteudo)
    
    # Extrair apenas os valores numéricos das correspondências
    numeros_extraidos = [codigo for prefixo, codigo in correspondencias]
    return numeros_extraidos
 		
con, cur, estadoinicial = open_database_connection()
if con is not None:
    print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)

print(GREEN + "Inicializando Recibo Processing" + RESET)
#Variavel para armazenar o tempo

def main():
    t = 1 
    while (True):
        try:
            print(GREEN + "Buscando ficheiros para procesar" + RESET)
            file_name = check_temp_files()

            if(file_name == None):
                time.sleep(5)
                continue   
            print(file_name)

            lines = []

            file_processing(file_name, lines)

            # Extrai os números de pedido GLV ou UE
            nr_pedido = extract_order_numbers(lines)

            print(CYAN + str(nr_pedido) + RESET)

            #----------------------------------------------------------------------------
                                            #OBSERVAÇÃO
            #Caso na primeira linha exista um número, então estamos perante uma pick list, 
            #Caso contrário estamos perante uma fatura.
            #----------------------------------------------------------------------------

            #Caso seja uma pick list
            if nr_pedido != 'LDA':
                array_posicao = 0
                linha_pedido = 0
                array_str_pedido = []
                
                #----------------------------------------------------------------------------
                                                #OBSERVAÇÃO
                #Toda informção que precisamos para fazer o cálculo da pesagem se encontra
                #entre as palvras IVA presente na fatura (Verficiar na pasta temp_faturas)
                #----------------------------------------------------------------------------

                #Procura a ultima posição da palavra IVA na farura 
                for word in lines:
                    if "IVA" in word:
                        linha_pedido = array_posicao
                        array_str_pedido.append(array_posicao)
                    array_posicao = array_posicao + 1
                
                print(array_str_pedido)                
                del array_str_pedido[2]

                PickList = []
                product_index = 0 #flag contador de produtos numa pick list
                c = 0 #flag contador de extras de cada produto
                
                #Para todas as linhas da pick list compreendidas entre os nomes IvA
                #Caso exista mais que uma pick_list no mesmo recibo, ignora todas exceto a primeira
                for i in range (array_str_pedido[0],array_str_pedido[1] - 2,1): #pica linha a linha os produtos
                    ing = []
                    word = []
                    word = lines[i+1].split()  # Separa a linha em palavras
                    
                    if len(word):
                        if word[0].isdigit():   #caso a primeira "palavra" seja um número, então estamos perante um produto
                            PickList.append(pick_list())    #adiciona ao array um novo objeto
                            
                            PickList[product_index].quantidade = word[0]  #define a quantidade
                            word.pop(0)     #apaga a quantidade da linha

                            f = 0

                            ppp=[]
                            
                            for w in word:
                                try:
                                    float(w)
                                except Exception as e:
                                    if not w[:1].isdigit():
                                        ppp.append(w)
                                        print(ppp)
                            p = " ".join(ppp)

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
                                if ((p==r"N\X84O, OBRIGADO!") or (p==r"TAXA SERVI\X87O") or (p==r"SEM MOLHO") or (p==r"SACO DE TRANSPOR") or (p==r"TAXA SACO"))!= 1:
                                    #Caso não seja nenhuma das apresentadas acima
                                    PickList[product_index].name = p
                                    PickList[product_index].peso = 0
                                    PickList[product_index].variancia = 0
                                    PickList[product_index].peso_natura = 0
                                    PickList[product_index].tipo = "Sanduiche"
                                    
                                    
                                    print(RED + 'ERROS: '+str(p) + RESET)    #mostrar quando não há correspondência
                                    save_erro(config.file_produto_desconhecido,str(p)) #Guarda o artigo no seguinte ficheiro
                            print ("Check Duplicado")

                            if product_index >= 2:
                                if PickList[product_index - 2].name:
                                    if PickList[product_index].name:
                                        if PickList[product_index - 2].name == PickList[product_index].name:
                                            print("Apagado produto", PickList[product_index - 2].name)
                                            PickList.pop(product_index - 2)
                                            product_index = product_index - 1

                            print ("Duplicado checked")
                            product_index = product_index + 1
                            c = 0  # faz reset ao contador de extras

                        else: #caso a primeira palavra não seja um número
                            q = 1 # flag quantidade
                            if word[0]=="-":
                            #print(word[0])
                                asv=0 # ignorar
                            elif word[0]=="SEM":
                                #print(word[:2])
                                cop=word #copia o array word
                                cop.pop(0) #apaga a primeira palavra
                                #print(cop)

                                for w2 in cop:
                                    try:
                                        float(w2)
                                    except Exception as e:
                                        if not w2[:1].isdigit():
                                            ing.append(w2)
                                            #print(ing)


                                p=" ".join(ing)    #junta todas as palavras da linha
                                #print(p)
                                str_extra="SEM "+p
                                #print(str_extra)

                                if cop[0].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q=int(cop[0]) #guarda a quantidade de extras
                                    p=" ".join(ing)
                                    #print(p+" teste")
                                # #print(p+" teste")
                                
                                # procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta=cur.fetchall()
                                #           print(resposta)
                                if resposta:
                                    peso_extra=resposta[0][2]*q*(-1) #peso vezes a quantidade (default q =1)
                                    #print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: " + str(p))
                                    peso_extra=0 #define variavel peso extra



                                if c==0:    #se for o primeiro extra do produto
                                    PickList[product_index - 1].extra = [str_extra]
                                    PickList[product_index - 1].extra_peso = [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                    PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                    
                                c = c + 1 #flag contador de extras de cada pedido
                            elif word[0]=="COM":
                                #print(word)
                                cop = word #copia o array word
                                cop.pop(0) #apaga a primeira palavra
                                

                                for w2 in cop:
                                    try:
                                        float(w2)
                                    except Exception as e:
                                        if not w2[:1].isdigit():
                                            ing.append(w2)
                                            print(ing)


                                p = " ".join(ing)    #junta todas as palavras da linha

                                if cop[0].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q = int(cop[0]) #guarda a quantidade de extras
                                    p = " ".join(ing)
                                    print(p + "teste")
                                
                                #Procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta = cur.fetchall()
                                #print(resposta)
                                if resposta:
                                    peso_extra = resposta[0][2]*q #peso vezes a quantidade (default q =1)
                                #print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: " + str(p))
                                    peso_extra = 0 #define variavel peso extra

                                str_extra = "COM" + p#Define o texto dos extras para guardar na pick list
                                if c == 0:    #se for o primeiro extra do produto
                                    PickList[product_index - 1].extra = [str_extra]
                                    PickList[product_index - 1].extra_peso = [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                    PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                    
                                c = c + 1 #flag contador de extras de cada pedido                                
                    
                            elif word[0] == "EXTRA":
                                cop = word #copia o array word
                                cop.pop(0) #apaga a primeira palavra
                                
                                #print(cop)
                                for w2 in cop:
                                    try:
                                        float(w2)
                                    except Exception as e:
                                        if not w2[:1].isdigit():
                                            ing.append(w2)
                                            print(ing)


                                p=" ".join(ing)    #junta todas as palavras da linha
                                #print(p)

                                if cop[0].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q = int(cop[0]) #guarda a quantidade de extras
                                    p = " ".join(ing) 
                                    print(p + "teste")
                                                        
                                #Procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta=cur.fetchall()

                                if resposta:
                                    peso_extra = resposta[0][2] * q #peso vezes a quantidade (default q =1)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print(RED + "Erro - Extra não reconhecido: " + str(p) + RESET)
                                    peso_extra = 0 #define variavel peso extra

                                str_extra = "EXTRA "+ p #Define o texto dos extras para guardar na pick list
                                    #                                print(c)
                                if c == 0:    #se for o primeiro extra do produto
                                    PickList[product_index - 1].extra = [str_extra]
                                    PickList[product_index - 1].extra_peso = [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                    PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                    
                                
                                c=c+1 #flag contador de extras de cada pedido
                            elif word[0] == "SO" or word[0] == "APENAS":
                                PickList[product_index - 1].natura = "True"
                                cop = ord #copia o array word
                                cop.pop(0) #apaga a primeira palavra
                                
                                for w2 in cop:
                                    try:
                                        float(w2)
                                    except Exception as e:
                                        if not w2[:1].isdigit():
                                            ing.append(w2)
                                            print(ing)

                                p=" ".join(ing)    #junta todas as palavras da linha

                                if cop[0].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q  =int(cop[0]) #guarda a quantidade de extras
                                    p = " ".join(ing)
                                    print(p + "teste")
                                # #print(p+" teste")
                                # procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta = cur.fetchall()
                                #                                print(resposta)
                                if resposta:
                                    peso_extra = resposta[0][2] * q #peso vezes a quantidade (default q =1)
                                #                                    print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: " + str(p))
                                    peso_extra = 0 #define variavel peso extra

                                str_extra = "APENAS" + p #Define o texto dos extras para guardar na pick list
                                #                               print(c)
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[product_index-1].extra = [str_extra]
                                    PickList[product_index-1].extra_peso = [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                    PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                            
                                c = c + 1 #flag contador de extras de cada pedido

                            elif word[0] == "NATURA" or word[0] == "PLAIN":
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
                            else:
                                #todos os tipos de extras "não conhecidos"
                                p = " ".join(word)
                                
                                save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                print("Erro - Extra não conhecido: " + str(p))

                                peso_extra = 0 #peso extra é 0
                                
                                str_extra = p #Define o texto dos extras para guardar na pick list
                                if c == 0:    #se for o primeiro extra do produto
                                    PickList[product_index - 1].extra = [str_extra]
                                    PickList[product_index - 1].extra_peso = [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[product_index - 1].extra = PickList[product_index - 1].extra + [str_extra]
                                    PickList[product_index - 1].extra_peso = PickList[product_index - 1].extra_peso + [peso_extra]
                                    
                                c = c + 1 #flag contador de extras de cada pedido

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
                print("Soma efetuada: " + str(peso))

                # Convert to JSON string
                jsonStr = json.dumps([ob.__dict__ for ob in PickList], indent=4, sort_keys=True)

                print(nr_pedido)

                #Garantir que a variavel nr_pedido é de um tipo suportado pelo SQLite
                if isinstance(nr_pedido, list):
                    nr_pedido = json.dumps(nr_pedido)
                    print ("OK")
                
                print(RED + jsonStr + RESET)  
                #Insert into database
                #Filtrar pick lists vazias.
                
                if PickList:  # Verifica se PickList não está vazio
                    cur.execute(
                        "INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado) VALUES (?, ?, ?, ?, ?)",
                        (nr_pedido, jsonStr, file_name, estadoinicial, estadoinicial)
                    )
                    con.commit()
                    flag_molho = 0
                else:
                    print(RED + "PickList está vazio. Nenhum dado foi inserido no banco de dados" + RESET)

                # Guarda o ficheiro na pasta das pick list's
                os.rename(config.temp_file_dir+'//'+file_name, config.file_dir_pick_list+'//'+file_name)
                #caso tenha várias pick list no mesmo "recibo"
                if len(array_str_pedido) > 2:
                    print('várias pick_list')
                    logf = open("Erro_Log.log", "a")
                    t = datetime.datetime.now()
                    s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
                    logf.write(s+"; recibo processing "+"Várias pick_list"+str(file_name)+'\n')
                    logf.close()
            else:
                print('Fatura')
                os.rename(config.temp_file_dir+'//'+file_name, config.file_dir_fatura+'//'+file_name)

        except Exception as e:
            time.sleep(2) #"teste" dar tempo para fechar o ficehiro?
            os.rename(config.temp_file_dir+'//'+file_name, config.file_dir_erro+'//'+file_name)
            print(e)
            #break
        
    con.close()        

if __name__ == '__main__':
    main()
