import requests
import time
import json
import os
from os import walk
import sqlite3
import datetime
import config #importa as configurações/variáveis globais para cada instalação


class pick_list:
    def __init__(self):
            self.name = ""
            self.quantidade = []
            self.extra =[]

    def __repr__(self):
        return pick_list

def save_erro(erro_file,erro_str): #guarda os produtos que não têm correspondencia na BD
    
    # Cria a string com a data atual
    t = datetime.datetime.now()
    s=t.strftime('%Y/%m/%d %H:%M:%S')

    file_obj = open(erro_file, 'a')
    file_obj.write(s+'; '+erro_str+'\n')# guarda a data num ficheiro txt
    file_obj.close()
		


#abre db
con = sqlite3.connect(config.db)
cur = con.cursor()

estadoinicial=0

print("recibo_processing")
t=1
while (True):

    try:
        #a=input()
        #print(a)
        time.sleep(5)   # A cada 5 seg procura novos recibos

        f=[]
        #identifica todos os ficheiros na pasta dos recibos temporários (config.temp_file_dir)
        for (dirpath, dirnames, filenames) in walk(config.temp_file_dir):
            f.extend(filenames)
            #print(filenames)
            break

        #caso existam ficheiros para processar:
        if len(filenames)!=0:
            file_name=filenames[0]

            lines = []
            nr_pedido =[]

            #abre o ficheiro e processa linha a linha
            with open(config.temp_file_dir+'\\'+file_name, "r") as file:
                for line in file: 
                    line = line.upper()
                    #print(line)8
                    line = line.replace("\\X1BD","").replace("\\X1DVB","").replace("\\N'","").replace('\\N"',"").replace("\\X1BE","").replace("\\X00","").replace("\\X1BA","").replace("\\X1D!D","").replace("\\X1DB","").replace("\\X1DBD","")
                    #print(line)
                    line = line.replace("B'","").replace('B"',"").replace('"',"").replace("\\X01","").replace("\\X11","").replace("\\R\\X1DL","").replace("\\X1DR'","").replace("\\X1D!","").replace("\\R","").replace("\\X1DR","").replace("\\X1BT","").replace("\\X10","").replace("\\X1DL","").strip()
                    #print (line)
                    line = line.strip()
                    lines.append(line) #storing everything in memory!
                    print(line)

            # Extrai o numero interno do pedido (apresentado na primeira linha da picklist
            
            # for word in lines[2].split():
            #     if word.isdigit():
            #         nr_pedido=int(word)
                    
            nr_pedido=1        
            #alterar nr pedido para 2 digitos apenas

            #print("Pedido nr: "+str(nr_pedido))

            #caso na primeira linha exista um número, entºao estamos perante uma pick list, caso
            #caso contrário estamos perante uma fatura.
            if isinstance(nr_pedido,int):

                array_posicao=0
                linha_pedido=0
                array_str_pedido=[]
                #procura a ultima posição da palavra IVA no recibo (cada pick list apresenta duas vezes a palavra IVA
                #print(".")

                for word in lines:
                    if "PEDIDO" in word:
                        codigo_delivery=lines[array_posicao+2]
                        linha_pedido=array_posicao
                        array_str_pedido.append(array_posicao)
                        print("OKpedido")
                    array_posicao=array_posicao+1
                
                print(array_str_pedido)
                print(codigo_delivery)
                #del array_str_pedido[2]
                #del array_str_pedido[2]                
                #print(array_str_pedido)

                PickList = []
                #print (linha_pedido)
                b=0 #flag contador de produtos numa pick list
                c=0 #flag contador de extras de cada produto
                
                
               
                #caso exista mais que uma pick_list no mesmo recibo, ignora todas exceto a primeira
                for i in range (array_str_pedido[0]-1):
                    ing=[]
                    word=[]
                    word = lines[i+1].split()  # Separa a linha em palavras
                    #print(word)
                    if len(word):
                        if word[0]=="TAKE":
                            for word in lines[i].split():
                                if word.isdigit():
                                    nr_pedido=int(word)
                                    print("Pedido nr", nr_pedido)
                        elif word[0].isdigit():   #caso a primeira "palavra" seja um número, então estamos perante um produto
                            PickList.append(pick_list())    #adiciona ao array um novo objeto
                            
                            PickList[b].quantidade=word[0]  #define a quantidade
                            #print(word[0])
                            word.pop(0)     #apaga a quantidade da linha
                            p=" ".join(word)    #junta todas as palavras da linha
                            #print(word)

                            # procura na base de dados uma correspondência (tabela designação)
                            cur.execute("SELECT * FROM produtos INNER JOIN designacao on designacao.produto_id = produtos.produto_id WHERE designacao.nome = :name ",{"name":p})
                            resposta=cur.fetchall()
                            #print(resposta)
                            if resposta:    #Caso haja correspondência 
                                #print(resposta)
                                PickList[b].name=resposta[0][1]
                                PickList[b].peso=resposta[0][2]
                                PickList[b].variancia=resposta[0][3]
                                PickList[b].peso_natura=resposta[0][4]
                                PickList[b].tipo=resposta[0][5]
                            else:
                                if ((p=="N\X84O, OBRIGADO!") or (p=="TAXA SERVI\X87O") or (p=="SEM MOLHO"))!=1:
                                    #caso não seja nenhuma das apresentadas acima
                                    PickList[b].name=p
                                    PickList[b].peso=0
                                    PickList[b].variancia=0
                                    PickList[b].peso_natura=0
                                    PickList[b].tipo="Sanduiche"
                                    
                                    print('erros: '+str(p))    #mostrar quando não há correspondência
                                    save_erro(config.file_produto_desconhecido,str(p)) #Guarda o artigo no seguinte ficheiro

                            b=b+1
                            c=0  # faz reset ao contador de extras

                        else: #caso a primeira palavra não seja um número
                            q=1 # flag quantidade
                            if word[0]=="-":
#                               print(word[0])
                                asv=0 # ignorar
                            elif word[0]=="SEM":
#                                print(word)
                                ing=word[:] #copia o array word
                                ing.pop(0) #apaga a primeira palavra
                                p=" ".join(ing)    #junta todas as palavras da linha
                                if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q=int(word[1]) #guarda a quantidade de extras
                                    ing.pop(0)
                                    p=" ".join(ing)
#                                    print(p+" teste")
                                
                                # procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta=cur.fetchall()
#                                print(resposta)
                                if resposta:
                                    peso_extra=resposta[0][2]*q*(-1) #peso vezes a quantidade (default q =1)
#                                    print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: "+str(p))
                                    peso_extra=0 #define variavel peso extra

                                str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
                                                                
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[b-1].extra= [str_extra]
                                    PickList[b-1].extra_peso= [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[b-1].extra=PickList[b-1].extra+[str_extra]
                                    PickList[b-1].extra_peso=PickList[b-1].extra_peso+[peso_extra]
                                    
                                c=c+1 #flag contador de extras de cada pedido
                            elif word[0]=="COM":
#                                print(word)
                                ing=word[:] #copia o array word
                                ing.pop(0)#apaga a primeira palavra
                                p=" ".join(ing)    #junta todas as palavras da linha
                                if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q=int(word[1]) #guarda a quantidade de extras
                                    ing.pop(0)
                                    p=" ".join(ing)
#                                    print(p+" teste")
                                
                                # procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta=cur.fetchall()
#                                print(resposta)
                                if resposta:
                                    peso_extra=resposta[0][2]*q #peso vezes a quantidade (default q =1)
 #                                   print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: "+str(p))
                                    peso_extra=0 #define variavel peso extra

                                str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
 #                               print(c)
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[b-1].extra= [str_extra]
                                    PickList[b-1].extra_peso= [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[b-1].extra=PickList[b-1].extra+[str_extra]
                                    PickList[b-1].extra_peso=PickList[b-1].extra_peso+[peso_extra]
                                    
                                
                                c=c+1 #flag contador de extras de cada pedido                                
                    
                            elif word[0]=="EXTRA":
#                                print(word)
                                ing=word[:] #copia o array word
                                ing.pop(0)#apaga a primeira palavra
                                p=" ".join(ing)    #junta todas as palavras da linha
                                if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q=int(word[1]) #guarda a quantidade de extras
                                    ing.pop(0)
                                    p=" ".join(ing)
#                                    print(p+" teste")
                                
                                # procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta=cur.fetchall()
#                                print(resposta)
                                if resposta:
                                    peso_extra=resposta[0][2]*q #peso vezes a quantidade (default q =1)
  #                                  print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: "+str(p))
                                    peso_extra=0 #define variavel peso extra

                                str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
#                                print(c)
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[b-1].extra= [str_extra]
                                    PickList[b-1].extra_peso= [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[b-1].extra=PickList[b-1].extra+[str_extra]
                                    PickList[b-1].extra_peso=PickList[b-1].extra_peso+[peso_extra]
                                    
                                
                                c=c+1 #flag contador de extras de cada pedido
                            elif word[0]=="SO":
                                PickList[b-1].natura="True"
#                                print(word)
                                ing=word[:] #copia o array word
                                ing.pop(0)#apaga a primeira palavra
                                p=" ".join(ing)    #junta todas as palavras da linha
                                if word[1].isdigit():   #caso os extras tenham quantidades (ex. Extra 2 queijo)
                                    q=int(word[1]) #guarda a quantidade de extras
                                    ing.pop(0)
                                    p=" ".join(ing)
#                                    print(p+" teste")
                                
                                # procura na base de dados uma correspondência (tabela ingredientes)
                                cur.execute("SELECT * FROM ingredientes WHERE nome = :name ",{"name":p})
                                resposta=cur.fetchall()
#                                print(resposta)
                                if resposta:
                                    peso_extra=resposta[0][2]*q #peso vezes a quantidade (default q =1)
#                                    print(peso_extra)
                                else:
                                    #todos os extras "não conhecidos"
                                    save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                    print("Erro - extra não conhecido: "+str(p))
                                    peso_extra=0 #define variavel peso extra

                                str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
 #                               print(c)
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[b-1].extra= [str_extra]
                                    PickList[b-1].extra_peso= [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[b-1].extra=PickList[b-1].extra+[str_extra]
                                    PickList[b-1].extra_peso=PickList[b-1].extra_peso+[peso_extra]
                                    
                                
                                c=c+1 #flag contador de extras de cada pedido

                            elif word[0]=="NATURA" or word[0]=="PLAIN":
                                PickList[b-1].natura="True"
                                
                                peso_extra=0 #peso extra é 0
#                                    print(peso_extra)
                                
                                str_extra=" ".join(word) #Define o texto dos extras para guardar na pick list
 #                              print(c)
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[b-1].extra= [str_extra]
                                    PickList[b-1].extra_peso= [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[b-1].extra=PickList[b-1].extra+[str_extra]
                                    PickList[b-1].extra_peso=PickList[b-1].extra_peso+[peso_extra]
                                    
                                
                                c=c+1 #flag contador de extras de cada pedido
                            elif word[0][0]=="-":
                                #do nada
                                asd=0
                            else:
                                #todos os tipos de extras "não conhecidos"
                                p=" ".join(word)
                                
                                save_erro(config.file_extra_desconhecido,p) #Guarda o extra no seguinte ficheiro)
                                print("Erro - extra não conhecido: "+str(p))

                                peso_extra=0 #peso extra é 0
#                               print(peso_extra)
                                
                                str_extra=p #Define o texto dos extras para guardar na pick list
 #                              print(c)
                                if c==0:    #se for o primeiro extra do produto
                                    PickList[b-1].extra= [str_extra]
                                    PickList[b-1].extra_peso= [peso_extra]
                                else:       #para os restantes extras do produtos
                                    PickList[b-1].extra=PickList[b-1].extra+[str_extra]
                                    PickList[b-1].extra_peso=PickList[b-1].extra_peso+[peso_extra]
                                    
                                
                                c=c+1 #flag contador de extras de cada pedido
                             
                #print ("pesos guardados")

       
                #calcular peso total de cada produto
                for i in range(len(PickList)):
                    peso=0
                    if PickList[i].name:
                        if hasattr(PickList[i],'natura'): #verifica se o objeto tem o atributo natura
                            peso=PickList[i].peso_natura
                        else:
                            peso=PickList[i].peso

                        if hasattr(PickList[i],'extra_peso'):
                            peso=peso+sum(PickList[i].extra_peso)
                        PickList[i].peso_produto=peso
                    print(peso)
                    
                print("soma efetuada")

                #convert to JSON string-
                jsonStr = json.dumps([ob.__dict__ for ob in PickList],indent=4, sort_keys=True)


                cur.execute("INSERT INTO pick_list (delivery_name, list, pick_list_file, state, confirmado) VALUES (:numero_pedido, :list, :file_name, :estado, :estado)",{"numero_pedido":codigo_delivery, "list":str(jsonStr), "file_name":file_name, "estado":estadoinicial})
                con.commit()
                #print(".")
                #print json string
                #                print(jsonStr)
                
                
                flag_molho=0



                # Guarda o ficheiro na pasta das pick list's
                os.rename(config.temp_file_dir+'\\'+file_name, config.file_dir_pick_list+'\\'+file_name)
                #caso tenha várias pick list no mesmo "recibo"
                if len(array_str_pedido)>2:
                    print('várias pick_list')
                    logf = open("Erro_Log.log", "a")
                    t = datetime.datetime.now()
                    s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
                    logf.write(s+"; recibo processing "+"Várias pick_list"+str(file_name)+'\n')
                    logf.close()
            else:
                print('Fatura')
                os.rename(config.temp_file_dir+'\\'+file_name, config.file_dir_fatura+'\\'+file_name)
        else:
            t=0
        
        #break
    except Exception as e:
        time.sleep(2) #"teste" dar tempo para fechar o ficehiro?
        os.rename(config.temp_file_dir+'\\'+file_name, config.file_dir_erro+'\\'+file_name)
        print(e)
        #break
       
con.close()        
