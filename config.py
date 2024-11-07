#-------------Comum------------
prog_dir ='Digite aqui o diretório onde está o progama'


#portas Serial
port_com_balanca = 'Colocar aqui a porta COM que da balaça' #porta balança
port_com_arduino = 'Colocar aqui a porta COM da impressora' #porta impressora

rest_code = 'Digite aqui o código do restaurante'
api_offline = False
dlv = False
pending_order = False

data_base = prog_dir + '/Instance/db_picklist.db'

#pasta temporária para recibos
temp_file_dir = prog_dir + '/Orders_Resources/temp_files'

#-------------Recibo processing------------
unknown_products_errors = prog_dir + '/Logs_and_errors/unknown_products_errors.txt'
unknown_extras_errors = prog_dir + '/Logs_and_errors/extras_errors.txt'
filtered_unknown_products_errors = prog_dir + '/Logs_and_errors/filtered_unknown_products_errors.txt'
sound_tarte = prog_dir + '/Orders_Resources/tartes.wav'
errors_log = prog_dir + '/Logs_and_errors/error_log.log'
file_dir_pick_list = prog_dir +'/Orders_Resources/pick_list'
file_dir_fatura = prog_dir + '/Orders_Resources/invoices'
file_dir_erro = prog_dir + '/Logs_and_errors/errors'
api_url='https://85.246.46.140:3000/api'
img_path = prog_dir + '/Orders_Resources/fotos'
file_pesagem = prog_dir + '/Orders_Resources/pesagem.txt'

def set_api_offline():
    global api_offline
    api_offline = True
def set_api_online():
    global api_offline
    api_offline = False

def set_pending_order_true():
    global pending_order
    pending_order = True
def set_pending_order_true():
    global pending_order
    pending_order = False      
