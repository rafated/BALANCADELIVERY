import time
import datetime
import serial
import sys
import config

count = 1

# abre porta serial de comunicacao arduino
def open_serial_connection():
    arduino = None
    try:
        arduino = serial.Serial(port=config.port_com_arduino, baudrate=9600, timeout=.1)
    except Exception as e:
        print(f'Erro ao carregar porta Arduino - {config.port_com_arduino}: {e}')
    return arduino


def get_string_time():
    current_time = datetime.datetime.now()
    time_string = current_time.strftime('%Y%m%d_%Hh%Mm%Ss')
    return time_string

def process_data(data, recibo, count, config):
    # Remover os caracteres '\x00' da string e rstrip para remover espaços à direita
    data1 = str(data).replace('\\x00', '')
    print(str(data).rstrip())
    
    # Checar pelo primeiro padrão
    if "\\x1bd\\x1dVB\\r" in data1:    
        print('Padrão encontrado')
        time_string = get_string_time()

        # Escrever no arquivo
        with open(config.temp_file_dir + "\\" + time_string + str(count) + ".txt", "a") as file_object:
            for line in recibo:
                file_object.write(line + '\n')  # Salva os dados em um arquivo
        recibo = [line]
        count += 1
    
    # Checar pelo segundo padrão
    elif "\\x1bd" in data1:    
        print('Padrão encontrado')
        time_string = get_string_time()

        # Escrever no arquivo
        with open(config.temp_file_dir + "\\" + time_string + str(count) + ".txt", "a") as file_object:
            for line in recibo:
                file_object.write(line + '\n')  # Salva os dados em um arquivo
        recibo = []
        count += 1
    
    return recibo, count

def main():
    try:# para fazer registo em log dos possíveis erros
        arduino = open_serial_connection()

        time_string = get_string_time()
        print(time_string)
        
        recibo=["A"]
    
        while(True):
            #try caso o usb arduino seja desconectado não encera o programa
            try:
                while arduino.in_waiting:  # Or: while ser.inWaiting():
                    
                    recibo, count = process_data(data, recibo, count, config)                            
            
            except Exception as e:
                print(e)
                print ('Erro ao ler o Arduino')
                time.sleep(5) # Espera 5 segundos para que a coneçºao ao arduino seja realizada
                try:
                    arduino.close()  #fecha ligacao serial com arduino
                    arduino = serial.Serial(port=config.port_com_arduino, baudrate=9600, timeout=.1)
                except:
                    print ('erro load port arduino - '+config.port_com_arduino)
                
        
        x = input() # para não fechar automaticamente

    except Exception as e:
        print(e)
        logf = open("Erro_Log.log", "a")
        string_time = get_string_time()
        logf.write(string_time + "; " + str(e) + '\n')
        logf.close()

if __name__ == "__main__":
    main()
