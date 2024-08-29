#-------------Comum------------
prog_dir='C:/Users/rafae/OneDrive/Desktop/Balv1'
#portas Serial
port_com_balanca = 'COM3' #porta balança
port_com_arduino = 'COM4' #porta impressora

rest_code = 51
api_offline = False
dlv = False

#db='example.db'
data_base = prog_dir + '/Instance/db_picklist.db'


#pasta temporária para recibos
temp_file_dir = prog_dir + '/Orders_Resources/temp_files'

#-------------Recibo processing------------
unknown_products_errors = prog_dir + '/Logs_and_errors/unknown_products_errors.txt'
unknown_extras_errors = prog_dir + '/Logs_and_errors/extras_errors.txt'
filtered_unknown_products_errors = prog_dir + '/Logs_and_errors/filtered_unknown_products_errors.txt'
sound_tarte = prog_dir + '/Services/Main_Services/tartes.wav'
errors_log = prog_dir + '/Logs_and_errors/error_log.log'

file_dir_pick_list = prog_dir +'/Orders_Resources/pick_list'

file_dir_fatura = prog_dir + '/Orders_Resources/invoices'

file_dir_erro = prog_dir + '/Logs_and_errors/errors'

api_url='https://85.246.46.140:3000/api'

#--------------leitura_balanca--------------

port_com_arduino_led = 'COM10'

img_path = prog_dir + "/Orders_Resources/fotos"

file_pesagem = prog_dir + '/Orders_Resources/pesagem.txt'

def set_api_offline():
    global api_offline
    api_offline = True
def set_api_online():
    global api_offline
    api_offline = False  
