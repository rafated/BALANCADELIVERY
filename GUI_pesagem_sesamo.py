import PySimpleGUI as sg
import sqlite3
import config
import threading
import json
import cv2
import datetime
import time
import numpy as np
import serial
import requests
import subprocess
import os
from urllib3.exceptions import InsecureRequestWarning

# Suprimir o aviso de request inseguro
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Cores para mostrar as mensagens na consola
RED = "\033[1;31m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
CYAN = "\033[1;36m"

# Global variables
row_counter = 0
row_number_view = 1
weighing_attempts = {}  # Dicionário para rastrear tentativas de pesagem por pedido
last_order_number = 1
verped_running = False
funcpri = None
verped_lock = threading.Lock()  # Adiciona um lock para controle de execução

def teste_api_connection():
    print(GREEN + "Testando conexão à API" + RESET)
    try:
        # Adicionando um timeout de 3 segundos
        response = requests.get(config.api_url, verify=False, timeout=3)
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
        return con, cur
    # Caso haja algum erro durante a abertura da base de dados, imprime uma mensagem de erro e retorna None
    except sqlite3.Error as e:
        return None, None


def update_existing_order_button(window, nr_pedido):
    for key in list(window.AllKeysDict):
        if isinstance(key, tuple) and key[0] == '-ROW-':
            if key[1] == nr_pedido:
                print(f"{GREEN}Atualizando botão para o pedido {nr_pedido}.{RESET}")
                # Aqui você pode atualizar qualquer informação necessária
                # Exemplo: window[('-DESC-', nr_pedido)].update(text=nova_informacao)
                window[key].update(visible=True)  # Torna o botão visível, se foi ocultado

def fetch_last_order():
    api_connection = teste_api_connection()
    if(api_connection == 1):
        url = f"{config.api_url}/pedidos/ultimo"
        params = {'rest_code': config.rest_code}
        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return None
    else:
        config.api_offline = True
        con, cur = open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute(" SELECT * FROM pick_list WHERE state = 0 AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"rest_code": config.rest_code})
            response = cur.fetchall()
            return response
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None

def update_order_state(order_number):
    if(config.api_offline == False):
        url = f"{config.api_url}/pedido/confirmar_estado"
        params = {'pedido': order_number, "rest_code": config.rest_code}
        try:
            response = requests.post(url, params=params, verify=False)
            response.raise_for_status()
            print("Pedido confirmado com sucesso.")
        except requests.exceptions.RequestException as e:
            print(f"Erro ao confirmar o estado do pedido: {e}")
    else:
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute(" UPDATE pick_list SET state = 1 WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code", {"order_number": order_number ,"rest_code": config.rest_code})
            response = cur.fetchall()
            return response
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None
    

def confirm_order_api(order_number):
    if(config.api_offline == False):
        url = f"{config.api_url}/pedido/confirmar"
        params = {'pedido': order_number, 'rest_code': config.rest_code}
        try:
            response = requests.post(url, params=params, verify=False)
            response.raise_for_status()
            print(f"{GREEN}Pedido {order_number} confirmado com sucesso.{RESET}")
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao confirmar o pedido: {e}{RESET}")
    else:
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute(" UPDATE pick_list SET confirmado = 1 WHERE id = (SELECT id FROM pick_list WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"order_number": order_number ,"rest_code": config.rest_code})
            response = cur.fetchall()
            return response
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None

def fetch_order_state(order_number):
    if(config.api_offline == False):
        url = f"{config.api_url}/pedido/estado"
        params = {'pedido': order_number, 'rest_code': config.rest_code}
        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao buscuro estado do pedido: {e}{RESET}")
            return None
    else:
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute(" SELECT state, confirmado FROM pick_list WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"order_number": order_number ,"rest_code": config.rest_code})
            response = cur.fetchall()
            return response
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None


def fetch_order_details(order_number):
    if(config.api_offline == False):
        url = f"{config.api_url}/pedidos/detalhes"
        params = {'pedido': order_number, 'rest_code': config.rest_code}
        print(f"{GREEN}Fetching order details{RESET}")
        print(order_number)
        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            print(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao buscurdetalhes do pedido: {e}{RESET}")
            return None
    else:
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute(" SELECT * FROM pick_list WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"order_number": order_number ,"rest_code": config.rest_code})
            response = cur.fetchall()
            return response
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None

    
def send_weight_data_to_api(pick_list_id, peso_estimado, peso_real, photo):
    if(config.api_offline == False):
        url = f"{config.api_url}/pesagem"  # Endpoint da API para inserir dados na tabela pesagem
        payload = {
            "pick_list_id": pick_list_id,
            "peso_estimado": peso_estimado,
            "peso_real": peso_real,
            "photo": photo
        }
        try:
            response = requests.post(url, json=payload, verify=False)  # Enviando o payload como JSON
            response.raise_for_status()  # Levanta um erro se o status code não for 200
            print(f"{GREEN}Dados de pesagem enviados com sucesso: {response.json()}{RESET}")
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao enviar dados de pesagem para a API: {e}{RESET}")
    else:
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute("INSERT INTO pesagem (pick_list_id, peso_estimado, peso_real) VALUES (:pick_list_id, :peso_estimado, :peso_real)", {"pick_list_id": pick_list_id ,"peso_estimado": peso_estimado, "peso_real": peso_real})
            con.commit()
            print(GREEN + "Dados de pesagem adicionados ao banco de dados." + RESET)
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)

def clear_database_orders():
    print("Clearing orders in the database via API")
    if(config.api_offline == False):
        url = f"{config.api_url}/pedidos/limpar"
        try:
            response = requests.post(url, verify=False)
            response.raise_for_status()
            print(f"{GREEN}Pedidos limpos com sucesso na API.{RESET}")
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao limpar pedidos na API: {e}{RED}")
    else:
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute("UPDATE pick_list SET confirmado = 1, state = 1 WHERE (confirmado = 0 OR state = 0) AND codigo_restaurante = :rest_code", {"rest_code": config.rest_code})
            con.commit()
            print(GREEN + "Dados de pesagem adicionados ao banco de dados." + RESET)
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)


# GUI Layout Functions
def create_button(nr_pedido, row_counter, row_number_view):
    global last_order_number
    #TESTE_________________________________________-
    if(last_order_number  == nr_pedido):
        print(f"{RED}Botão duplicado detectado{RESET}")
        row = [sg.pin(
        sg.Col([[
            sg.Button("X", border_width=0, visible=False, key=('-DEL-', 0)),
            sg.Button(nr_pedido, size=(18, 2), font=("Arial Bold", 18), key=('-DESC-', 0), visible= False),
            sg.Text(f'{row_number_view}', key=('-STATUS-', row_counter), visible= False)
        ]], key=('-ROW-', 0)
        ))]
        row_number_view -= 1
    else:
        print(f"{CYAN}Creating button for pedido: {nr_pedido}, row_counter: {row_counter}, row_number_view: {row_number_view}{RESET}")
        row = [sg.pin(
            sg.Col([[
                sg.Button("X", border_width=0, visible=True, key=('-DEL-', nr_pedido), button_color=("white", "red")),
                sg.Button(nr_pedido, size=(18, 2), font=("Arial Bold", 18), key=('-DESC-', nr_pedido)),
                sg.Text(f'{row_number_view}', key=('-STATUS-', row_counter))
            ]], key=('-ROW-', nr_pedido)
        ))]
    last_order_number = nr_pedido
    return row

def restart_gui(window, serial_scale, camera):
    """
    Função para reiniciar a GUI sem a necessidade de um script bat.
    """
    global funcpri  # Acessa a variável global funcpri

    print(f"{CYAN}Reiniciando a GUI...{RESET}")
    
    # Cancela o intervalo anterior para interromper verped
    if funcpri is not None:
        funcpri.cancel()
        funcpri = None  # Limpa a variável global

    # Fecha a janela existente
    window.close()

    # Reconstrói o layout e a janela
    layout = build_layout()
    window = sg.Window('Balanca_McDelivery', layout, finalize=True, resizable=True, location=(0, 0), size=(1680, 1050), keep_on_top=True)
    window.Maximize()

    # Reinicializa a verificação de pedidos pendentes
    funcpri = SetInterval(3, lambda: verped(window, serial_scale, camera))

    print(f"{CYAN}GUI reiniciada com sucesso.{RESET}")
    return window  # Retorna a nova janela criada

def build_layout():
    print("Building layout")
    top_row = [[sg.Text('', size=(2, 1)), sg.Text('Pedido', size=(8, 1), font=("Arial Bold", 22)),
               sg.Text(key='-Pedido-', text='', size=(8, 1), font=("Arial CE", 22), text_color='Orange'),
               sg.Text(key='-Confirmar-', text='', size=(35, 4), font=("Arial Bold", 22), text_color='White', justification='c'),
               sg.Text('', size=(3, 1)),
               sg.Text('Desvio', size=(6, 1), font=("Arial Bold", 22)),
               sg.Text(key='-Peso_d-', text='', size=(6, 1), font=("Arial Bold", 22), justification='c'),
               sg.Text('Peso Estimado', size=(12, 1), font=("Arial CE", 22), text_color='Black'),
               sg.Text(key='-Peso_t-', text='', size=(6, 1), font=("Arial CE", 22), text_color='Black'),
               sg.Text('Peso Real', size=(9, 1), font=("Arial CE", 22), text_color='Black'),
               sg.Text(key='-Peso_r-', text='', size=(6, 1), font=("Arial CE", 22), text_color='Black')]]

    order_col = [[sg.Text('', size=(22, 1))],
                 [sg.Column([create_button(0, 0, 1)], key='-ROW_PANEL-')]]

    left_col = [[sg.Text('Molhos', font=("Arial Bold", 18))],
                [sg.MLine(key='-ML1-' + sg.WRITE_ONLY_KEY, size=(26, 11), font=("Arial CE ", 16), text_color="black", background_color="lightgrey", no_scrollbar=True)],
                [sg.Text('Addons', font=("Arial bold", 18))],
                [sg.MLine(key='-ML5-' + sg.WRITE_ONLY_KEY, size=(26, 12), font=("Arial CE ", 16), background_color="lightgrey", text_color="black", no_scrollbar=True)]]

    midle_col = [[sg.Text('Sanduiches', font=("Arial Bold", 18))],
                 [sg.MLine(key='-ML2-' + sg.WRITE_ONLY_KEY, size=(26, 25), font=("Arial CE", 16), background_color="lightgrey", text_color="black", no_scrollbar=True)],
                 [sg.Text('', size=(1, 5))],
                 [sg.Button('Reset pedidos', key='rs-ML', font=("Arial", 10), size=(15, 2), button_color='orange')]]

    right_col = [[sg.Text('Acompanhamentos', font=("Arial bold", 18))],
                 [sg.MLine(key='-ML3-' + sg.WRITE_ONLY_KEY, size=(26, 11), font=("Arial CE", 16), background_color="lightgrey", text_color="black", no_scrollbar=True)],
                 [sg.Text('Bebidas | Sobremesas', font=("Arial bold", 18))],
                 [sg.MLine(key='-ML4-' + sg.WRITE_ONLY_KEY, size=(26, 12), font=("Arial CE", 16), background_color="lightgrey", text_color="black", no_scrollbar=True)],
                 [sg.Text('', size=(1, 5))],
                 [sg.Button('Reiniciar GUI', key='restart-gui', font=("Arial", 10), size=(15, 2), button_color='orange')]]  # Novo botão adicionado

    molhos_col = [[sg.Text(key='-molho-', text='', size=(22, 7), font=("Arial Bold", 22), text_color='Red', justification='c')],
                  [sg.Text(key='-tarte-', text='', size=(22, 7), font=("Arial Bold", 22), text_color='Red', justification='c')],
                  [sg.Text("Camera", size=(10, 1))],
                  [sg.Image(filename="", key="cam")]]

    layout = [top_row,
              [sg.Column(molhos_col, element_justification='c', vertical_alignment='t'),
               sg.Column(left_col, element_justification='c', vertical_alignment='t'), sg.VSeperator(),
               sg.Column(midle_col, element_justification='c', vertical_alignment='t'), sg.VSeperator(),
               sg.Column(right_col, element_justification='c', vertical_alignment='t'),
               sg.Column(order_col, element_justification='c', vertical_alignment='t')]]

    print("Layout built")
    return layout

# Helper Classes
class SetInterval:
    def __init__(self, interval, action):
        print(f"{CYAN}Setting up interval with {interval} seconds{RESET}")
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__set_interval)
        thread.start()

    def __set_interval(self):
        next_time = time.time() + self.interval
        while not self.stopEvent.wait(next_time - time.time()):
            next_time += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()

# Main Logic Functions
def process_order(window, order, serial_scale, camera):
    global row_counter, row_number_view
    print(f"{CYAN}Processing order: {order}{RESET}")

    window['-Pedido-'].update(order['delivery_name'])
    order_json = json.loads(order['list'])
    peso, variancia = calculate_order_weight(window, order_json)

    # Atualiza a interface com o peso estimado calculado
    window['-Peso_t-'].update(f'{peso}')

    if peso > 1300:
        peso += 14

    capture_image(camera, order['delivery_name'], window)

    process_weighing(window, serial_scale, peso, order['delivery_name'], camera)

def calculate_order_weight(window, order_json):
    print(f"{CYAN}Calculating weight for order items{RESET}")
    peso = 0
    variancia = 0
    found_molho = False
    found_tarte = False
    found_bag = False
    found_ketchup = False
    found_both = False

    for item in order_json:
        if item["tipo"] == "Molho":
            if 'molho' in item["name"].lower():
                found_molho = True  # Marcurque um molho foi encontrado
            if 'ketchup' in item["name"].lower():
                found_ketchup = True
            display_order_item(window, '-ML1-', item, 'orange')
        elif item["tipo"] == "Addon":
            #Exclui a sopa no cálculo do peso do pedido.
            if 'sopa' in item["name"].lower():
                peso += 0
            else:
                peso += int(item["quantidade"]) * item["peso_produto"]
            display_order_item(window, '-ML5-', item)
        elif item["tipo"] == "Sanduiche":
            if 'tarte de maca' in item["name"].lower():
                found_tarte = True  # Marcurque uma tarte de maçã foi encontrada
            existe_campo_natura = any('natura' in item for item in order_json)
            # Imprime o resultado da verificação
            if existe_campo_natura:
                print("Existe um objeto com o campo 'natura' presente.")
                peso += int(item["quantidade"]) * item["peso_natura"]
            else:
                print("Não existe nenhum objeto com o campo 'natura'.")
                peso += int(item["quantidade"]) * item["peso_produto"]
            # Verifica se existe algum objeto na lista `order_json` que tenha o campo 'natura'
                peso += int(item["quantidade"]) * item["peso_produto"]
            variancia += int(item["quantidade"]) * item["variancia"]
            display_order_item(window, '-ML2-', item)
        elif item["tipo"] == "Batata":
            peso += int(item["quantidade"]) * item["peso_produto"]
            display_order_item(window, '-ML3-', item)
        elif item["tipo"] in ["Bebida", "Sobremesa", "Gelado"]:
            if 'saco de transporte' in item["name"].lower():
                peso += 14
                found_bag = True  # Marcurque uma saco foi encontrado
            display_order_item(window, '-ML4-', item)
       # Emitir alerta para molho
#-----------------ALTERAR INEFICIENTE------------------------------------
    if (found_molho == True):
        if(found_ketchup == True):
            found_both = True
    if (found_ketchup == True):
        if(found_molho == True):
            found_both = True
    
    if(found_both == True):
        window['-molho-'].update('\n\n Atenção! \n O Pedido leva molho e ketchup!', background_color='#E78200', text_color='white')
        found_molho = False
        found_ketchup = False
    if(found_molho == True):
        window['-molho-'].update('\n\n Atenção! \n O Pedido leva molho!', background_color='orange', text_color='white')
    if(found_ketchup == True):
        window['-molho-'].update('\n\n Atenção! \n O Pedido leva ketchup!', background_color='red', text_color='white')
    
    if(found_tarte):
        #Muda a cor do campo das sobremesas alertando que há uma tarte no pedido
        window['-tarte-'].update('\n\n Atenção! \n O pedido leva tarte de maça!', background_color='blue', text_color='white')
    # Mudar fundo do campo de sobremesas para azul se uma tarte de maçã for encontrada

    print(f"{CYAN}Calculated weight: {peso}, variancia: {variancia}{RESET}")
    return peso, variancia

def display_order_item(window, key, item, background_color=None):
    s = f"{item['quantidade']} {item['name']}"
    print(f"{CYAN}Displaying order item: {s}{RESET}")
    if background_color:
        window[key + sg.WRITE_ONLY_KEY].print(s, background_color=background_color, text_color='black')
    else:
        window[key + sg.WRITE_ONLY_KEY].print("  " + s)
    for extra in item.get("extra", []):
        window[key + sg.WRITE_ONLY_KEY].print(f"      {extra}", text_color='black')

def capture_image(camera, order_number, window):
    print(f"{CYAN}Capturing image for order number: {order_number}{RESET}")
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss')
    frameSize = (320, 240)

    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Abre o objeto da câmera
        
        ret, frame = cap.read()  # Captura um frame da câmera

        if ret:  # Verifica se a captura foi bem-sucedida
            # Construção do nome do arquivo para salvar a imagem
            filename = f"{config.img_path}/{timestamp}_{order_number}.png"
            
            # Salvamento da imagem no diretório especificado
            cv2.imwrite(filename, frame)
            print(f"{CYAN}Image captured and saved as: {filename}{RESET}")
            
            # Redimensiona a imagem para exibição na interface
            frame2 = cv2.resize(frame, frameSize)
            imgbytes = cv2.imencode(".png", frame2)[1].tobytes()
            window["cam"].update(data=imgbytes)  # Atualiza a imagem no campo "cam"
            
            cap.release()  # Libera o objeto da câmera após a captura
            return filename  # Retorna o caminho do arquivo salvo

        else:
            print(f'{RED}Frame not opened{RESET}')
            cap.release()
            return None  # Retorna None se a captura falhar

    except Exception as e:
        print(f'{RED}Erro ao acessar a webcam{RESET}')
        cap.release()
        # Log do erro
        logf = open("Erro_Log.log", "a")
        t = datetime.datetime.now()
        s = t.strftime('%Y%m%d_%Hh%Mm%Ss')
        logf.write(f"{s}; {str(e)}\n")
        logf.close()
        print(e)
        return None  # Retorna None em caso de exceção


def process_weighing(window, serial_scale, estimated_weight, order_number, camera):
    global weighing_attempts
    print(f"{CYAN}Processing weighing, estimated weight: {estimated_weight}{RESET}")
    weights = []
    image_file = None  # Variável para armazenar o caminho da imagem
    # Tentar ler os dados da balança por até 10 vezes
    for _ in range(10):
        time.sleep(0.2)
        serial_scale.flushInput()
        scale_data = serial_scale.readline().decode('utf-8').strip()
        print(f"{CYAN}Raw scale data: {scale_data}{RESET}")  # Imprimir os dados brutos

        try:
            # Verifica se o dado é do formato esperado e extrai o valor em kg
            if scale_data.startswith('ST'):
                # Extrai a parte do peso em kg (posição 7 até 14)
                weight_kg = float(scale_data[7:14])
                weight_grams = int(weight_kg * 1000)  # Converte para gramas
                print(f"{CYAN}Processed weight: {weight_grams}{RESET}")  # Verificuro peso processado
                if weight_grams > 0:
                    weights.append(weight_grams)
        except ValueError as ve:
            print(f"{RED}ValueError: {ve}{RESET}")  # Mostrar o erro específico
            print(f"{RED}Invalid data received from scale.{RESET}")
        
        if len(weights) >= 3:
            break

    if weights:
        actual_weight = weights[-1]  # Pega o último valor válido de peso
        image_file = capture_image(camera, order_number, window)
        deviation = actual_weight - estimated_weight
        print(f"Actual weight: {actual_weight}, Deviation: {deviation}")
        window['-Peso_r-'].update(str(actual_weight))
        
        # Se o desvio estiver dentro da faixa aceitável, o pedido deve ser confirmado
        if -60 <= deviation <= 100:
            print(f"{CYAN}Peso dentro da faixa aceitável. Confirmando pedido {order_number}.{RESET}")
            update_confirmation_status(window, deviation)
            confirm_order_api(order_number)  # Confirmar o pedido na API
            
            # Enviar os dados de pesagem para a API
            send_weight_data_to_api(
                pick_list_id=order_number,  # Supondo que `order_number` é o `pick_list_id`
                peso_estimado=estimated_weight,
                peso_real=actual_weight,
                photo=image_file
            )
            
            window[('-ROW-', order_number)].update(visible=False)  # Remove o pedido da tela
        else:
            print(f"{CYAN}Peso fora da faixa aceitável.{RESET}")
            update_confirmation_status(window, deviation)
            # Incrementar o contador de tentativas para o pedido
            if order_number in weighing_attempts:
                weighing_attempts[order_number] += 1
            else:
                weighing_attempts[order_number] = 1

            # Verificurse o limite de tentativas foi atingido
            if weighing_attempts[order_number] >= 2:
                print(f"{CYAN}Pedido {order_number} removido após 4 tentativas falhadas.{RESET}")
                window[('-ROW-', order_number)].update(visible=False)
                del weighing_attempts[order_number]  # Remover o pedido das tentativas
    else:
        print(f"{CYAN}Peso instável ou 0{RESET}")
        window['-Peso_r-'].update("Instável")
        window['-Confirmar-'].update('\n Pedido instável ou a 0', background_color="gray60")

def save_image(image_file, order_number):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%Hh%Mm%Ss')
    saved_filename = f"{config.img_path}{timestamp}_{order_number}_confirmed.png"
    cv2.imwrite(saved_filename, cv2.imread(image_file))
    print(f"{CYAN}Image saved as: {saved_filename}{RESET}")

def update_confirmation_status(window, deviation):
    print(f"{CYAN}Updating confirmation status, deviation: {deviation}{CYAN}")
    if deviation > 100 or deviation < -60:
        window['-Confirmar-'].update('\n Atenção, verificar novamente \n o pedido!', background_color='red', text_color = 'white')
        window['-Peso_d-'].update(str(deviation), background_color='red', text_color='black')
    else:
        window['-Confirmar-'].update('\n Pedido correcto. Pronto para entrega!', background_color='green', text_color = 'white')
        window['-Peso_d-'].update(str(deviation))

def is_order_confirmed(order_number):
    print(f"{CYAN}Checking if order is confirmed: {order_number}{RESET}")
    order_state = fetch_order_state(order_number)

    if not order_state:
        print(f"{RED}Order state could not be fetched for: {order_number}{RESET}")
        return False

    confirmed = order_state.get('state') == 1 and order_state.get('confirmado') == 1
    print(f"{CYAN}Order confirmed: {confirmed}{RESET}")
    return confirmed

def verped(window, serial_scale, camera):
    global row_counter, row_number_view, verped_running  # Acessando a flag global
    print(f"{CYAN}Checking for pending orders{RESET}")

    # Use um lock para garantir que `verped` não seja chamado simultaneamente
    with verped_lock:
        if verped_running:
            print(f"{CYAN}verped already running, skipping call{RESET}")
            return

        # Defina a flag como True no início da função
        verped_running = True

    try:
        time.sleep(3)  # Simula o tempo de espera de um pedido
        order = fetch_last_order()
        if order:
            nr_pedido = order['delivery_name']
            print(f"{CYAN}New order found: {nr_pedido}{RESET}")
            
            # Verificurse o pedido já existe na interface
            existing_order_keys = [key for key in window.AllKeysDict if isinstance(key, tuple) and key[0] == '-ROW-' and key[1] == nr_pedido]
            
            if existing_order_keys:
                print(f"{CYAN}Pedido {nr_pedido} já existe. Atualizando informações.{RESET}")
                # Atualiza o pedido existente na interface
                update_existing_order_button(window, nr_pedido)
                update_order_state(nr_pedido)
            else:    
                row_counter += 1
                row_number_view += 1
                window.extend_layout(window['-ROW_PANEL-'], [create_button(nr_pedido, row_counter, row_number_view)])
                update_order_state(nr_pedido)

    finally:
        # Defina a flag como False após a execução ser concluída
        with verped_lock:
            verped_running = False

def reset_orders(window):
    global row_counter, row_number_view, funcpri  # Declarar funcpri como variável global

    print(f"{CYAN}Resetting orders in the database and UI{RESET}")

    window['-Confirmar-'].update('\n Por favor aguarde! \n Apagando os pedidos...', background_color="orange", text_color="white")
    window.refresh()  # Atualiza a interface imediatament

    # Cancelar o intervalo anterior
    if funcpri is not None:
        funcpri.cancel()
        funcpri = None  # Certifique-se de limpar a variável

    # Itera sobre os elementos no dicionário de chaves
    for key in list(window.AllKeysDict):
        if isinstance(key, tuple) and key[0] == '-ROW-':
            try:
                window[key].update(visible=False)
            except KeyError:
                pass
    
    clear_display(window)
    clear_database_orders()
    
    row_counter = 0
    row_number_view = 1
    
    # Criar uma nova instância de SetInterval após cancelar a anterior
    funcpri = SetInterval(3, lambda: verped(window, None, None))
    
    print("Checking for pending orders")
    time.sleep(3)
    order = fetch_last_order()

    if order:
        nr_pedido = order['delivery_name']

        print(f"{CYAN}New order found: {nr_pedido}{RESET}")
        
        # Verificarse o pedido já existe na interface
        existing_order_keys = [key for key in window.AllKeysDict if isinstance(key, tuple) and key[0] == '-ROW-' and key[1] == nr_pedido]
        
        if existing_order_keys:
            print(f"{CYAN}Pedido {nr_pedido} já existe. Atualizando informações.{RESET}")
            # Atualiza o pedido existente na interface
            update_existing_order_button(window, nr_pedido)
            update_order_state(nr_pedido)
        else:    
            row_counter += 1
            row_number_view += 1
            window.extend_layout(window['-ROW_PANEL-'], [create_button(nr_pedido, row_counter, row_number_view)])
            update_order_state(nr_pedido)

def handle_order(window, order_number, serial_scale, camera):
    global funcpri  # Declarar funcpri como variável global
    print(f"{CYAN}Handling order: {order_number}{RESET}")
    window['-Confirmar-'].update('\n Por favor, aguarde! \n Pesagem em andamento...', background_color="orange", text_color="white")
    window.refresh()  # Atualiza a interface imediatament
    if funcpri is not None:
        funcpri.cancel()
    clear_display(window)
    order = fetch_order_details(order_number)
    if order:
        process_order(window, order, serial_scale, camera)
        if is_order_confirmed(order_number):
            global row_number_view
            row_number_view -= 1
            window[('-ROW-', order_number)].update(visible=False)
    funcpri = SetInterval(3, lambda: verped(window, serial_scale, camera))

def clear_display(window):
    print(f"{CYAN}Clearing the display{RESET}")
    window['-ML1-' + sg.WRITE_ONLY_KEY].update('')
    window['-ML2-' + sg.WRITE_ONLY_KEY].update('')
    window['-ML3-' + sg.WRITE_ONLY_KEY].update('')
    window['-ML4-' + sg.WRITE_ONLY_KEY].update('')
    window['-ML5-' + sg.WRITE_ONLY_KEY].update('')
    window['-Peso_d-'].update('', background_color="gray25", text_color='white')
    window['-Peso_t-'].update('', background_color="gray25", text_color='black')
    window['-Peso_r-'].update('', background_color="gray25", text_color='black')
    window['-Confirmar-'].update('\nBem-vindo! Selecione um pedido para pesagem', background_color="green", text_color="white")
    window['-molho-'].update('', background_color="gray25", text_color='white')
    window['-tarte-'].update('', background_color="gray25", text_color='white')

def log_error(e):
    print(f"{RED}Logging error: {e}{RESET}")
    with open("Erro_Log.log", "a") as logf:
        t = datetime.datetime.now()
        s = t.strftime('%Y%m%d_%Hh%Mm%Ss')
        logf.write(f"{RED}{s};Erro no GUI ;{str(e)}{RESET}\n")
    print(e)

def main():
    global funcpri  # Declarar funcpri como variável global
    print(f"{CYAN}Starting application{RESET}")
    sg.theme('Dark')
    layout = build_layout()
    window = sg.Window('Balanca_McDelivery', layout, finalize=True, resizable=True, location=(0, 0), size=(1680, 1050), keep_on_top=True)
    window.Maximize()

    print(f"{CYAN}Initializing camera and serial scale{RESET}")
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    serial_scale = serial.Serial(port=config.port_com_balanca, baudrate=9600, timeout=.1)

    # Certifique-se de que apenas uma instância de SetInterval seja criada
    funcpri = SetInterval(3, lambda: verped(window, serial_scale, camera))

    while True:
        event, values = window.read()
        print(f"Event: {event}, Values: {values}")

        if event in (sg.WIN_CLOSED, 'Exit'):
            print(f"{CYAN}Exiting application{RESET}")
            break  # Adicione um break para sair do loop

        if isinstance(event, tuple) and event[0] == '-DEL-':
            print(f"{CYAN}Deleting row for order: {event[1]}{RESET}")
            window[('-ROW-', event[1])].update(visible=False)

        if event == 'rs-ML':
            print(f"{CYAN}Resetting orders{RESET}")
            reset_orders(window)

        if isinstance(event, tuple) and event[0] == '-DESC-':
            print(f"{CYAN}Handling order selection: {event[1]}{RESET}")
            handle_order(window, event[1], serial_scale, camera)
        
        if event == 'restart-gui':
            print(f"{CYAN}Reiniciando a GUI...{RESET}")
            window = restart_gui(window, serial_scale, camera)  # Reinicia a GUI e atualiza a referência da janela
            continue  # Continua o loop com a nova janela

    # Fechar a janela ao sair do loop
    window.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(e)
