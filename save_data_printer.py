import time
import datetime
import serial
import sys
import config


arduino = ''
count=1

print("Save_data_printer.py")

try:# para fazer registo em log dos possíveis erros

    # abre porta serial de comunicacao arduino
    try:
        arduino = serial.Serial(port=config.port_com_arduino, baudrate=9600, timeout=.1)
    except :
        print ('erro load port arduino - '+config.port_com_arduino)
        #sys.exit(1)
    

    # teste string data e hora
    t = datetime.datetime.now()
    s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
    print(s)
    
    
    recibo=["A"]
   
     
    while(True):
        
        #try caso o usb arduino seja desconectado não encera o programa
        try:
            while arduino.in_waiting:  # Or: while ser.inWaiting():

                data = arduino.readline()# ler os dados enviados pelo arduino pela porta
                recibo.append(str(data))
                                
                data1=str(data).replace('\\x00','')
                print(str(data).rstrip())
                #if "\\x1dVB" in str(data1):
                #if "\\x1bd" in str(data1):
                if "\\x1bd\\x1dVB\\r" in str(data1):    
                    print('ok')
                    t = datetime.datetime.now()
                    s=t.strftime('%Y%m%d_%Hh%Mm_')
                    
                    with open(config.temp_file_dir+"\\"+s+str(count)+".txt", "a") as file_object:
                        for line in recibo:
                            file_object.write(line+'\n')  # guarda a data num ficheiro
                    
                    #recibo=[]
                    recibo=[line]
                    count=count+1
                elif "\\x1bd" in str(data1):    
                    print('ok')
                    t = datetime.datetime.now()
                    s=t.strftime('%Y%m%d_%Hh%Mm_')
                    
                    with open(config.temp_file_dir+"\\"+s+str(count)+".txt", "a") as file_object:
                        for line in recibo:
                            file_object.write(line+'\n')  # guarda a data num ficheiro
                    
                    #recibo=[]
                    recibo=[]
                    count=count+1
                            
        except Exception as e:
            print(e)
            print ('erro ler arduino')
            time.sleep(5) # Espera 5 segundos para que a coneçºao ao arduino seja realizada
            try:
                arduino.close()  #fecha ligacao serial com arduino
                arduino = serial.Serial(port=config.port_com_arduino, baudrate=9600, timeout=.1)
            except:
                print ('erro load port arduino - '+config.port_com_arduino)
            
    
    x = input() # para não fechar automaticamente

except Exception as e:     # most generic exception you can catch
    print(e)
    logf = open("Erro_Log.log", "a")
    t = datetime.datetime.now()
    s=t.strftime('%Y%m%d_%Hh%Mm%Ss')
    logf.write(s+"; "+str(e)+'\n')
    logf.close()
