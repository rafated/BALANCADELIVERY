import PySimpleGUI as sg
import sqlite3
import config
from threading import Thread, Timer
import threading
import json
import requests
import datetime
import serial
#import fakeSerial as serial
import statistics
import time
import numpy as np
import cv2
from pydub import AudioSegment
from pydub.playback import play

print("GUI")
#sg.theme('Dark Brown 1')
sg.theme('Dark')


 
tarte = AudioSegment.from_wav(config.sound_tarte)


def create_button(nr_pedido, row_counter, row_number_view):
    row =  [sg.pin(
        sg.Col([[
            sg.Button("X", border_width=0, visible=False, key=('-DEL-', row_counter)),
            sg.Button(nr_pedido, size=(18,2), font=("Arial Bold", 18), key=('-DESC-', nr_pedido)),
            sg.Text(f'{row_number_view}', key=('-STATUS-', row_counter))
            ]],
        key=('-ROW-', nr_pedido)
        ))]
    return row




# top row

top_row = [[sg.Text('',size=(2,1)),sg.Text('Pedido', size=(8, 1), font=("Arial Bold", 22)),
#sg.InputText(key='input_codigo', do_not_clear=False, size=(7, 1)),
#sg.Button('Go', visible=False, bind_return_key=True),
sg.Text(key='-Pedido-',text='',size=(8, 1),font=("Arial CE", 22),text_color='Orange'),
sg.Text(key='-Confirmar-',text='',size=(35, 4),font=("Arial Bold", 22), text_color='White', justification='c'),
sg.Text('',size=(3,1)),
sg.Text('Desvio', size=(6, 1),font=("Arial Bold", 22)),
sg.Text(key='-Peso_d-',text='',size=(6, 1),font=("Arial Bold", 22), justification='c'),
sg.Text('Peso Estimado', size=(12, 1),font=("Arial CE", 22),text_color='Black'),
sg.Text(key='-Peso_t-',text='',size=(6, 1),font=("Arial CE ", 22),text_color='Black'),
sg.Text('Peso Real', size=(9, 1),font=("Arial CE ", 22),text_color='Black'),
sg.Text(key='-Peso_r-',text='',size=(6, 1),font=("Arial CE ", 22),text_color='Black')
]]
# First colum vazia, para centrar as restantes colunas

order_col = [[sg.Text('',size=(22,1))],
[sg.Column([create_button(0,0,1)],key='-ROW_PANEL-')]

]

# First the window layout...3 columns

empty_col2 = [[sg.Text('',size=(5,1))]]

left_col = [[sg.Text('Molhos',font=("Arial Bold", 18))],
[sg.MLine(key='-ML1-'+sg.WRITE_ONLY_KEY, size=(26,11),font=("Arial CE ", 16),text_color="black",background_color="lightgrey",no_scrollbar = True)],
[sg.Text('Addons',font=("Arial bold", 18))],
[sg.MLine(key='-ML5-'+sg.WRITE_ONLY_KEY, size=(26,12),font=("Arial CE ", 16),background_color="lightgrey",text_color="black",no_scrollbar = True)]]

midle_col = [[sg.Text('Sanduiches',font=("Arial Bold", 18))],
[sg.MLine(key='-ML2-'+sg.WRITE_ONLY_KEY, size=(26,25),font=("Arial CE", 16),background_color="lightgrey",text_color="black",no_scrollbar = True)],
[sg.Text('',size=(1,5))]
,
[sg.Button('Reset pedidos',key='rs-ML',font=("Arial", 10),size=(15,2),button_color='orange')]
]

right_col = [[sg.Text('Acompanhamentos',font=("Arial bold",18))],
[sg.MLine(key='-ML3-'+sg.WRITE_ONLY_KEY, size=(26,11),font=("Arial CE", 16),background_color="lightgrey",text_color="black",no_scrollbar = True)],
[sg.Text('Bebidas | Sobremesas',font=("Arial bold", 18))],
[sg.MLine(key='-ML4-'+sg.WRITE_ONLY_KEY,  size=(26,12),font=("Arial CE", 16),background_color="lightgrey",text_color="black",no_scrollbar = True)]]

molhos_col = [[sg.Text(key='-molho-',text='',size=(20, 8),font=("Arial Bold", 22), text_color='Red', justification='c')],
[sg.Text(key='-tarte-',text='',size=(20, 8),font=("Arial Bold", 22), text_color='Red', justification='c')],
[sg.Text("Camara", size=(10, 1))],
[sg.Image(filename="", key="cam")]
]


# ----- Full layout -----
layout = [top_row,
[sg.Column(order_col, element_justification='c',vertical_alignment='t'),
sg.Column(empty_col2, element_justification='c',vertical_alignment='t'),
sg.Column(left_col, element_justification='c',vertical_alignment='t'), sg.VSeperator(),
sg.Column(midle_col, element_justification='c',vertical_alignment='t'), sg.VSeperator(),
sg.Column(right_col, element_justification='c',vertical_alignment='t'),
sg.Column(molhos_col, element_justification='c',vertical_alignment='t')]
]

window = sg.Window('Balanca_McDelivery', layout, finalize=True,  resizable = True, location=(0,0), size=(1920,1080),keep_on_top=True)
# no_titlebar=True colocar no programa superior



#window.force_focus() #uncoment caso não estiver a "focar" o cursor no campo "pedido"
window.Maximize()
#window.Element('input_codigo').SetFocus() #forçar o cursor a focar

counter = 0

camera_Width  = 450 #480 # 640 # 1024 # 1280
camera_Heigth = 450 # 480 # 780  # 960
frameSize = (camera_Width, camera_Heigth)


nr_pedido=0
row_counter=0
row_number_view=1


class setInterval :
    def __init__(self,interval,action) :
        self.interval=interval
        self.action=action
        self.stopEvent=threading.Event()
        thread=threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) :
        nextTime=time.time()+self.interval
        while not self.stopEvent.wait(nextTime-time.time()) :
            nextTime+=self.interval
            self.action()

    def cancel(self) :
        self.stopEvent.set()
        for x in range(0,4):
            print(x)
            time.sleep(1)


def verped():
    con = sqlite3.connect(config.db)
    cur = con.cursor()
    cur.execute("SELECT * FROM pick_list WHERE state LIKE :estado ORDER BY id DESC LIMIT 1 ",{"estado":0})
    resposta=cur.fetchall()


    if resposta:
        ped=resposta[0][1]
        print(ped)
        
        global row_counter
        global row_number_view

        if ped:
            row_counter += 1
            row_number_view += 1
            print("Actual Row Number: ", row_counter)
            print("Displayed Row Number: ", row_number_view)
            # Allows you to add items to a layout
            # These items cannot be deleted, but can be made invisible
            window.extend_layout(window['-ROW_PANEL-'], [create_button(ped,row_counter, row_number_view)])



        cur.execute("UPDATE pick_list SET state=1 WHERE delivery_name LIKE :numero",{"numero":ped})
        con.commit()
        con.close()
    



#elif event[0] == '-DEL-':
#        row_number_view -= 1
#        window[('-ROW-', event[1])].update(visible=False)

row_number_view -= 1
window[('-ROW-', 0)].update(visible=False)

try:

    # porta serial de comunicacao Balanca
    try:
      serial_scale = serial.Serial(port= config.port_com_balanca, baudrate=9600, timeout=.1)
    except :
        print ('erro load port balanca - '+config.port_com_balanca)

    # abre porta serial de comunicacao arduino/led
    try:
        arduino = serial.Serial(port=config.port_com_arduino_led, baudrate=9600, timeout=.1)
    except :
        print ('erro load port arduino - '+config.port_com_arduino_led)
        #sys.exit(1)

    


    #introduzir função que Lê os pedidos por mostrar e que cria um botão


    funcpri=setInterval(3,verped)






    while True:             # Event Loop
        #event, values = window.read(timeout=100)
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break

        if event == 'rs-ML':
            tti=threading.Timer(0.1,funcpri.cancel)
            tti.start()


            window['-ML1-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML2-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML3-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML4-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML5-'+sg.WRITE_ONLY_KEY].update('')
            window['-Peso_d-'].update('',background_color="gray25",text_color='white')
            window['-Peso_t-'].update('',background_color="gray25",text_color='black')
            window['-Peso_r-'].update('',background_color="gray25",text_color='black')
            window['-Pedido-'].update('',background_color="gray25",text_color='white')                    
            window['-Confirmar-'].update('',background_color="gray50")
            window['-molho-'].update('',background_color="gray25")
            window['-tarte-'].update('',background_color="gray25")

            time.sleep(0.15)
        

            zero=0
            #limpar base de dados
            while True:
                con = sqlite3.connect(config.db)
                cur = con.cursor()
                cur.execute("SELECT * FROM pick_list WHERE confirmado LIKE :estado ORDER BY id DESC LIMIT 1 ",{"estado":zero})
                resp=cur.fetchall()
                if resp:
                    pedi=resp[0][1]
                    cur.execute("UPDATE pick_list SET confirmado=1 WHERE delivery_name LIKE :numero",{"numero":pedi})
                    con.commit()
                    cur.execute("UPDATE pick_list SET state=1 WHERE delivery_name LIKE :numero",{"numero":pedi})
                    con.commit()
                    con.close()

                    ke=('-ROW-', pedi)
                    #element = window[ke]

                    if ke in window.AllKeysDict:
                        print(ke)
                        row_number_view -= 1
                        window[('-ROW-', pedi)].update(visible=False)
                    else:
                        print("Nao ha pedidos para apagar")

                else:
                    break
            #print("ok")
            funcpri=setInterval(3,verped)
            
            continue


        if event[0] == '-DESC-': 
        
            tti=threading.Timer(0.1,funcpri.cancel)
            tti.start()    


            startTime = time.time()
            
            # Clear all text 
            window['-ML1-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML2-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML3-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML4-'+sg.WRITE_ONLY_KEY].update('')
            window['-ML5-'+sg.WRITE_ONLY_KEY].update('')
            window['-Peso_d-'].update('',background_color="gray25",text_color='white')
            window['-Peso_t-'].update('',background_color="gray25",text_color='black')
            window['-Peso_r-'].update('',background_color="gray25",text_color='black')
            window['-Pedido-'].update('',background_color="gray25",text_color='white') 
            window['-Confirmar-'].update('\n A verificar...',background_color="orange")
            window['-molho-'].update('',background_color="gray25")
            window['-tarte-'].update('',background_color="gray25")

            codigo=event[1]
            print(codigo)

            time.sleep(0.15)
            
            # Envia o codigo do pedido para o servidor orbmcdelivery para "chamar" o estafeta
            # myobj = {'login':'1', 'user_email':config.email, 'user_password':config.password, 'submit_pedido':codigo}
            # try:
                # x = requests.post(config.url_entrega, data = myobj)
               # # print(x.text)
                

            # except Exception as e:
                # logf = open("Erro_Log.log", "a")
                # t = datetime.datetime.now()
                # s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
                # logf.write(s+";Erro envio do codigo do pedido ao servidor para chamar o estafeta ;"+str(e)+'\n')
                # print(e)
                # logf.close()
            
            


            #procura a pick list correspondete
            
            if len(codigo)>3:   #para códigos uber/glovo/Jet
                a=codigo+"%"
            else:               #para códigos internos [1:100]
                a=codigo
                
            con = sqlite3.connect(config.db)
            cur = con.cursor()
            cur.execute("SELECT * FROM pick_list WHERE delivery_name LIKE :name ORDER BY id DESC LIMIT 1 ",{"name":a})
            resposta=cur.fetchall()
            con.close()
            
            s=""
            peso=0
            var=0
            flag_molho=False
            flag_tarte=False
            pick_list_id=0 ###########
            if resposta:
                pick_list_id=resposta[0][0]
                window['-Pedido-'].update(resposta[0][1])
               # print(resposta[0])
                #print(resposta[0][2])
                json_object = json.loads(resposta[0][2])

               # print(len(json_object))


                for value in json_object:
                    if value["name"]:
                        if value["tipo"]=="Molho":
                            flag_molho=True #define a flag para acender o led no final do processo
                            s=value["quantidade"]+" "+value["name"]
                            window['-ML1-'+sg.WRITE_ONLY_KEY].print(s,background_color='orange',text_color='black')
                            if value["extra"]:
                                for v in value["extra"]:
                                    window['-ML1-'+sg.WRITE_ONLY_KEY].print("      "+str(v), text_color='black')

                        if value["tipo"]=="Tarte":
                            flag_tarte=True #define a flag para acender o led no final do processo
                            peso=peso+(int(value["quantidade"])*value["peso_produto"])
                            s=value["quantidade"]+" "+value["name"]
                            window['-ML2-'+sg.WRITE_ONLY_KEY].print(s,background_color='orange',text_color='black')
                            if value["extra"]:
                                for v in value["extra"]:
                                    window['-ML2-'+sg.WRITE_ONLY_KEY].print("      "+str(v), text_color='black')


                        if value["tipo"]=="Addon":
                            peso=peso+(int(value["quantidade"])*value["peso_produto"])
                           # var=var+(int(value["quantidade"])*value["variancia"])
                            s=value["quantidade"]+" "+value["name"]
                            window['-ML5-'+sg.WRITE_ONLY_KEY].print(s,background_color='orange',text_color='black')
                            if value["extra"]:
                                for v in value["extra"]:
                                    window['-ML5-'+sg.WRITE_ONLY_KEY].print("      "+str(v), background_color='orange',text_color='black')

                        
                        if value["tipo"]=="Sanduiche":
                            peso=peso+(int(value["quantidade"])*value["peso_produto"])
                            var=var+(int(value["quantidade"])*value["variancia"])
                            #print(var)
                            s=value["quantidade"]+" "+value["name"]
                            window['-ML2-'+sg.WRITE_ONLY_KEY].print("  "+s)
                            if value["extra"]:
                                for v in value["extra"]:
                                    window['-ML2-'+sg.WRITE_ONLY_KEY].print("      "+str(v))
                                    
                            
                        if value["tipo"]=="Batata":
                            peso=peso+(int(value["quantidade"])*value["peso_produto"])
                           # var=var+(int(value["quantidade"])*value["variancia"])
                            s=value["quantidade"]+" "+value["name"]
                            window['-ML3-'+sg.WRITE_ONLY_KEY].print(s)
                            if value["extra"]:
                                for v in value["extra"]:
                                    window['-ML3-'+sg.WRITE_ONLY_KEY].print("      "+str(v))
                                       
                        
                        if value["tipo"]=="Bebida" or value["tipo"]=="Sobremesa" or value["tipo"]=="Gelado":
                            s=value["quantidade"]+" "+value["name"]
                            window['-ML4-'+sg.WRITE_ONLY_KEY].print(s)
                            if value["extra"]:
                                for v in value["extra"]:
                                    window['-ML4-'+sg.WRITE_ONLY_KEY].print("      "+str(v))
                                    

                            
                        #s=s+value["name"]
                        #s=value["quantidade"]+" "+value["name"]
                        #window['-ML1-'+sg.WRITE_ONLY_KEY].print(s, text_color='black')

                
                

                if peso>1300:
                    peso=peso+28 # Se estimativa de peso for superior a 1kg adicionar peso de dois sacos (2x14g)
                else:
                    peso=peso+14 # Se a estimativa de peso for inferior a 1kg adicionar peso de um saco (14g)


                print("peso=",peso)
                print("variancia=",var)

           
            executionTime = (time.time() - startTime)
            #print('Execution time 1 in seconds: ' + str(executionTime))
            startTime = time.time()
            
            # Captura de fem                        
            # Cria a string com a data atual
            t = datetime.datetime.now()
            sc=t.strftime('%Y%m%d_%Hh%Mm%Ss')
            try:
                 
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW,)  #abre o objeto e fecha todas as vezes para evitar guardar frames no buffer
                #cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                #cap.set(cv2.CAP_PROP_EXPOSURE, 0.01)   
                ret, frame = cap.read() # Check o frame da webcam
                
                
                print (cap.get(cv2.CAP_PROP_BUFFERSIZE))

                if ret == True:
                    cv2.imwrite(config.img_path+sc+'_'+codigo+".png",frame) # Guarda num ficheiro a foto com a hora atual
                    frame2 = cv2.resize(frame, frameSize)
                    imgbytes = cv2.imencode(".png", frame2)[1].tobytes()
                    window["cam"].update(data=imgbytes)
                    
                    cap.release()
                    print('WebCam Frame Guardado')


                  
                else:
                    print('Frame not opened')
                    cap.release()
                    #cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    
            except Exception as e:
                print('erro acesso webcam')
                cap.release()
                #cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                logf = open("Erro_Log.log", "a")
                t = datetime.datetime.now()
                s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
                logf.write(s+"; "+str(e)+'\n')
                logf.close()
                print(e)

                
            window['-Peso_t-'].update(str(peso))
            #event, values = window.read(timeout=10)


            executionTime = (time.time() - startTime)
            print('Execution time 2 in seconds: ' + str(executionTime))
            startTime = time.time()
            
            #teste pesagem balança ------------------
            
            

            lista_pesos_save=[]
            peso_g=[]
            peso_medio=""
            desvio=100 #desvio por defaut é maior que 65g
            #peso=0
            # loop 10  times para balança estabilizar.
            serial_scale.flushInput()  # descarta todos os dados que estão no buffer da porta serial_scale
            time.sleep(0.15)

            #alterar para 10 ciclo com a balança
            for i in range(10):
                
                serial_scale.flushInput()  # descarta todos os dados que estão no buffer da porta serial_scale
                time.sleep(0.2) # Espera x segundos 
                scale_data = serial_scale.readline() # ler os dados enviados pelo arduino pela porta
                #print(scale_data[7:14])
                if len(scale_data)==18 and str(scale_data[0:2])=="b'ST'":
                    peso_kg=scale_data[7:14]
                    if int(float(peso_kg)*1000)>50: #ignora todas as medições estáveis abaixo de 50g
                        peso_g.append(int(float(peso_kg)*1000))
                    print(peso_g)
                        
                lista_pesos_save.append(scale_data)  # guarda todos dados da balança num array  

                window['-Peso_r-'].update(str(i))
                values = window.read(timeout=10)                
                if len(peso_g)==3: #para o ciclo sempre que tem duas medições estáveis
                    break    

            if peso_g:
                
                #peso_medio=123
                #desvio=peso-np.average(peso_g)

                peso_medio=peso_g[-1]
                desvio=peso_medio-peso
                
                window['-Peso_r-'].update(str(peso_medio))
              

                if desvio > 100:
                    window['-Confirmar-'].update('\n Atenção, verificar novamente o pedido!',background_color='red')
                    window['-Peso_d-'].update(str(desvio),background_color='red',text_color='black')
                    #window['-ML5-'+sg.WRITE_ONLY_KEY].update(background_color='red')
                elif desvio < -60 :
                    window['-Confirmar-'].update('\n Atenção, verificar novamente o pedido!',background_color='red')
                    window['-Peso_d-'].update(str(desvio),background_color='red',text_color='black')
                
                else:
                    window['-Confirmar-'].update('\n Pedido correcto. Pronto para entrega!',background_color='green')
                    window['-Peso_d-'].update(str(desvio))

                    con = sqlite3.connect(config.db)
                    cur = con.cursor()
                    cur.execute("UPDATE pick_list SET confirmado=1 WHERE delivery_name LIKE :numero",{"numero":codigo})
                    con.commit()
                    con.close()            


                
            else:
                ## uncoment to test 
                #desvio=peso-1000*np.random.random(1)[0]
                #peso_medio=str(-desvio-peso)

                desvio=peso

                window['-Confirmar-'].update('\n Instável',background_color="gray25")
                window['-Peso_r-'].update("Instável")


  
            
            #event, values = window.read(timeout=10) #atualiza GUI

            # Cria a string com a data atual
            t = datetime.datetime.now()
            s=t.strftime('%Y/%m/%d %H:%M:%S')

            file_object = open(config.file_pesagem, 'a')
            file_object.write('\n'+s+'; '+str(codigo)+'; '+str(peso)+'; '+str(peso_medio)+'; '+str(var))  # guarda a data num ficheiro txt

            for peso_arr in lista_pesos_save:
                file_object.write('; '+str(peso_arr))
                
            file_object.close()  #fecha ficheiro .txt


            con = sqlite3.connect(config.db)
            cur = con.cursor()
            cur.execute("INSERT INTO pesagem (pick_list_id,peso_estimado,peso_real, foto_file) VALUES (:pick_list_id,:peso,:peso_medio,:foto_file)",{"pick_list_id":pick_list_id ,"peso":peso,"peso_medio":peso_medio, "foto_file":sc+'_'+codigo+'.png'})
            con.commit()


            


            executionTime = (time.time() - startTime)
            #print('Execution time 3 in seconds: ' + str(executionTime))


            #------------------ Sinaliza molhos com o piscar da luz
            if flag_molho==True:
                # ciclo de 6 vz 700 ms cada
                valueH = '6,700\n'
                
                window['-molho-'].update('\n\n Atenção! \n\n O Pedido leva molho!',background_color='orange')
                try:
                    arduino.write(bytes(valueH, 'utf-8'))
                except:
                    print ('erro arduino - H')
                    
                
                
             #--------------------------------------

            if flag_tarte==True:
                
                window['-tarte-'].update('\n\n Atenção! \n\n O Pedido leva TARTE!',background_color='blue')
                #play(tarte)
            

            cur.execute("SELECT state,confirmado FROM pick_list WHERE delivery_name LIKE :numero_pedido ORDER BY id DESC LIMIT 1 ",{"numero_pedido":codigo})
            resp=cur.fetchall()

            
            print(event[1])
            print(event)

            if resp:
                if resp[0][0]==1:
                    if resp[0][1]==1:
                        row_number_view -= 1
                        window[('-ROW-', event[1])].update(visible=False)
                        print("pedido confirmado")



            cur.execute("UPDATE pick_list SET confirmado=1 WHERE delivery_name LIKE :numero",{"numero":codigo})
            con.commit()
            con.close()            



            funcpri=setInterval(3,verped)

            


                



                                            
except Exception as e:
#    if arduino:
#        arduino.close()
    #os.rename(config.temp_file_dir+file_name, config.file_dir_erro+file_name)
    print(e)
    logf = open("Erro_Log.log", "a")
    t = datetime.datetime.now()
    s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
    logf.write(s+";Erro no GUI ;"+str(e)+'\n')
    logf.close()
    a=input()

window.close()



    

    



