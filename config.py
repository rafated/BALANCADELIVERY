#-------------Comum------------
prog_dir='C:\\Users\\BALAL\\Documents\\Pesagem2\\'

#portas Serial
port_com_balanca = 'COM9' #porta balança
port_com_arduino = 'COM7' #porta impressora


#db='example.db'
db='db_picklist.db'


#pasta temporária para recibos
temp_file_dir = prog_dir+'temp_faturas'

#-------------recibo processing----------
url = 'http://orbmcdelivery.com/pedidos/add_picklist_pedido'
email = 'Restaurante_alges@orbmcdelivery.com'
#email = 'Restaurante_Demo@orbmcdelivery.com'
password = 'test'


file_produto_desconhecido=prog_dir+'erro_produtos.txt'
file_extra_desconhecido=prog_dir+'erro_extras.txt'
file_desconhecido_filtrado=prog_dir+'erro_produtos_filtrado.txt'
sound_tarte=prog_dir+'tartes.wav'


file_dir_pick_list=prog_dir+'pick_list'

file_dir_fatura=prog_dir+'faturas'

file_dir_erro=prog_dir+'erros'


#------------------Save data printer--------------

#------------------GUI---------------------------
url_entrega = 'http://orbmcdelivery.com/pedidos/move_entrega_byscanner'



#--------------leitura_balanca--------------

port_com_arduino_led = 'COM10'

img_path =prog_dir+'fotos\\'

file_pesagem=prog_dir+'pesagem.txt'
