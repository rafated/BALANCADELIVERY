#Código atualizado -- 07 Outubro de 2024 -- 2h47
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
import usb.core
import usb.util
from pydub import AudioSegment
from pydub.playback import play

# Suprimir o aviso de request inseguro
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Cores para mostrar as mensagens na consola
RED = "\033[1;31m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
CYAN = "\033[1;36m"

    
#definicao caminho som tarte
tarte = AudioSegment.from_wav(config.sound_tarte)
verificar = AudioSegment.from_wav(config.sound_verificar)

normal_size = b'\x1b\x21\x00'    # Normal size
double_height = b'\x1b\x21\x10'  # Double height
double_width = b'\x1b\x21\x20'   # Double width
double_height_width = b'\x1b\x21\x30'  # Double height and width
bold_on = b'\x1b\x45\x01'        # Bold on
bold_off = b'\x1b\x45\x00'       # Bold off
underline_on = b'\x1b\x2d\x01'   # Underline on
underline_off = b'\x1b\x2d\x00'  # Underline off
align_center = b'\x1b\x61\x01'   # Center align
align_left = b'\x1b\x61\x00'     # Left align
align_right = b'\x1b\x61\x02'    # Right align

barra_preta = b'\x1b\x21\x30\x1dB\x01\x1bE\x01 Duplo Controle \n\n\n\n'
fim_barra_preta = b'\x1d!\x00\x1bE\x00\x1d!\x00\x1dB\x00\n'

# Define paper cut commands
full_cut = b'\x1d\x56\x00'   # Full cut
partial_cut = b'\x1d\x56\x01'  # Partial cut

# Global variables
row_counter = 0
row_number_view = 1
weighing_attempts = {}  # Dicionário para rastrear tentativas de pesagem por pedido
last_order_number = 1
verped_running = False
funcpri = None
verped_lock = threading.Lock()  # Adiciona um lock para controle de execução

def play_tarte():
    try:
        play(tarte)
    except:
        print("Som tarte não encontrado")
    

def teste_api_connection():
    print(GREEN + "Testando conexão à API" + RESET)
    try:
        # Adicionando um timeout de 3 segundos
        response = requests.get(config.api_url, verify=False, timeout=3)
        if response.status_code == 200:
            print(GREEN + "Conexão à API bem-sucedida" + RESET)
            config.set_api_online()
            return True
        else:
            print(RED + f"Falha na conexão à API: Status Code {response.status_code}" + RESET)
            config.set_api_offline()
            return False
    except requests.exceptions.RequestException as e:
        print(RED + "Falha na conexão à API: " + str(e) + RESET)
        config.set_api_offline()
        return False

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
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    if teste_api_connection():  # Verifica se a API está online
        url = f"{config.api_url}/pedidos/ultimo"
        params = {'rest_code': config.rest_code}
        try:
            response = requests.get(url, params=params, headers=headers,verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            #print(f"{RED}Erro ao buscar último pedido da API: {e}{RESET}")
            return None

    # Fallback para o banco de dados local
    print(GREEN + "Usando o banco de dados local para buscar o último pedido." + RESET)
    con, cur = open_database_connection()
    if con is not None:
        cur.execute("SELECT * FROM pick_list WHERE state = 0 AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"rest_code": config.rest_code})
        response = cur.fetchall()
        if response:  # Verifica se há resultados na consulta
            order_json = []
            for r in response:
                order_json.append({
                    "id": r[0],
                    "delivery_name": r[1],
                    "list": r[2],
                    "peso_produto": r[3],
                    "peso": r[4],
                    "peso_natura": r[5],
                    "variancia": r[6]
                })
            return order_json
        else:
            print(RED + "Nenhum pedido encontrado no banco de dados local." + RESET)
            return None
    else:
        print(RED + "Erro ao abrir a base de dados" + RESET)
        return None


def update_order_state(order_number):
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    if teste_api_connection():  # Verifica se a API está online
        url = f"{config.api_url}/pedido/confirmar_estado"
        params = {'pedido': order_number, "rest_code": config.rest_code}
        try:
            response = requests.post(url, params=params, headers=headers ,verify=False)
            response.raise_for_status()
            print(f"{GREEN}Pedido {order_number} confirmado com sucesso na API.{RESET}")
            return True  # Retorna True para indicar sucesso
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao confirmar o estado do pedido na API: {e}{RESET}")
            return False  # Retorna False para indicar falha
    else:
        # Fallback para o banco de dados local
        con, cur = open_database_connection()
        if con is not None:
            try:
                print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
                cur.execute(
                    "UPDATE pick_list SET state = 1 WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code",
                    {"order_number": order_number, "rest_code": config.rest_code}
                )
                con.commit()
                print(GREEN + f"Estado do pedido {order_number} atualizado no banco de dados local." + RESET)
                return True  # Retorna True para indicar sucesso
            except sqlite3.Error as e:
                print(RED + f"Erro ao atualizar o estado do pedido no banco de dados: {e}{RESET}")
                return False  # Retorna False para indicar falha
            finally:
                con.close()  # Certifique-se de fechar a conexão ao banco de dados
        else:
            print(RED + "Erro ao abrir a base de dados local" + RESET)
            return False  # Retorna False para indicar falha


def confirm_order_api(order_number):
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    if teste_api_connection():
        url = f"{config.api_url}/pedido/confirmar"
        params = {'pedido': order_number, 'rest_code': config.rest_code}
        try:
            response = requests.post(url, params=params, headers=headers, verify=False)
            response.raise_for_status()
            print(f"{GREEN}Pedido {order_number} confirmado com sucesso.{RESET}")
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao confirmar o pedido: {e}{RESET}")
    else:
        con, cur = open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute("UPDATE pick_list SET confirmado = 1 WHERE id = (SELECT id FROM pick_list WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1)", {"order_number": order_number, "rest_code": config.rest_code})
            con.commit()
            print(GREEN + "Pedido confirmado no banco de dados local." + RESET)
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)

def fetch_order_state(order_number):
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    if teste_api_connection():
        url = f"{config.api_url}/pedido/estado"
        params = {'pedido': order_number, 'rest_code': config.rest_code}
        try:
            response = requests.get(url, params=params, headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            
            # Verifica se a resposta da API está no formato esperado
            if isinstance(data, dict) and 'state' in data and 'confirmado' in data:
                print(f"{GREEN}Order state fetched successfully from API: {data}{RESET}")
                return data
            else:
                print(f"{RED}Formato inesperado de resposta da API para estado do pedido: {data}{RESET}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao buscar estado do pedido: {e}{RESET}")
            return None
    else:
        # Fallback para o banco de dados local
        con, cur = open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            try:
                cur.execute("SELECT state, confirmado FROM pick_list WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"order_number": order_number ,"rest_code": config.rest_code})
                response = cur.fetchall()
                
                # Verifica se há resultados e que os dados estão no formato esperado
                if response and isinstance(response, list) and len(response) > 0:
                    result = response[0]  # Acessa o primeiro resultado

                    # Garante que o resultado tenha ao menos 2 elementos (state e confirmado)
                    if len(result) >= 2:
                        order_state = {
                            "state": result[0],
                            "confirmado": result[1]
                        }
                        print(f"{GREEN}Order state fetched successfully from DB: {order_state}{RESET}")
                        return order_state
                    else:
                        print(f"{RED}Resultado inesperado ao buscar o estado do pedido: {response}{RESET}")
                        return None
                else:
                    print(RED + "Nenhum estado de pedido encontrado no banco de dados local." + RESET)
                    return None
            except (sqlite3.Error, IndexError) as e:
                print(RED + f"Erro ao acessar o banco de dados: {e}{RESET}")
                return None
            finally:
                con.close()
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None

def fetch_order_details(order_number):
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    if teste_api_connection():
        url = f"{config.api_url}/pedidos/detalhes"
        params = {'pedido': order_number, 'rest_code': config.rest_code}
        print(f"{GREEN}Fetching order details{RESET}")
        try:
            response = requests.get(url, params=params, headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()

            # A API já retorna os dados no formato esperado
            print(f"{GREEN}Order details fetched successfully from API: {data}{RESET}")
            return data

        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao buscar detalhes do pedido: {e}{RESET}")
            return None  # Retorna None explicitamente se houver erro
    else:
        # Fallback para banco de dados local
        con, cur = open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            try:
                cur.execute("SELECT * FROM pick_list WHERE delivery_name = :order_number AND codigo_restaurante = :rest_code ORDER BY id DESC LIMIT 1", {"order_number": order_number, "rest_code": config.rest_code})
                response = cur.fetchall()
                
                # Verifica se há resultados
                if response and isinstance(response, list) and len(response) > 0:  # Verifica se há pelo menos um resultado
                    order = response[0]
                    
                    # Verifica se o campo 'list' é uma string e faz o parsing; caso contrário, deixa como está
                    if len(order) > 2 and isinstance(order[2], str):
                        try:
                            list_data = json.loads(order[2])  # Faz o parsing de 'list' se for string JSON
                        except json.JSONDecodeError as e:
                            print(f"{RED}Erro ao analisar JSON no campo 'list': {e}{RESET}")
                            list_data = []  # Define como lista vazia em caso de erro de parsing
                    else:
                        list_data = order[2] if len(order) > 2 and isinstance(order[2], list) else []  # Mantém o valor se já for uma lista

                    # Monta um dicionário estruturado para retornar, garantindo que ele tenha o mesmo formato que o retorno da API
                    order_json = {
                        "id": order[0] if len(order) > 0 and order[0] is not None else None,
                        "delivery_name": order[1] if len(order) > 1 and order[1] is not None else '',
                        "list": list_data,  # Usa a lista processada
                        "pick_list_file": order[2] if len(order) > 7 and order[7] is not None else '',
                        "state": order[3] if len(order) > 8 and order[8] is not None else 0,
                        "confirmado": order[4] if len(order) > 9 and order[9] is not None else 0,
                        "pendente": order[5] if len(order) > 10 and order[10] is not None else 0,
                        "codigo_restaurante": order[6] if len(order) > 11 and order[11] is not None else None,
                        "time_stamp": order[7] if len(order) > 12 and order[12] is not None else ''
                    }
                    print(f"{GREEN}Order details fetched and standardized from DB: {order_json}{RESET}")
                    return order_json  # Retorna o dicionário estruturado
                else:
                    print(RED + "Nenhum detalhe de pedido encontrado no banco de dados local ou estrutura inesperada." + RESET)
                    return None
            except (sqlite3.Error, json.JSONDecodeError) as e:
                print(RED + f"Erro ao acessar o banco de dados ou ao analisar JSON: {e}{RESET}")
                return None
            finally:
                con.close()
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)
            return None

    
def send_weight_data_to_api(pick_list_id, peso_estimado, peso_real, photo, start_time_stamp, end_time_stamp, tentativas, itens):
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    if(config.api_offline == False):
        url = f"{config.api_url}/pesagem"  # Endpoint da API para inserir dados na tabela pesagem
        payload = {
            "pick_list_id": pick_list_id,
            "peso_estimado": peso_estimado,
            "peso_real": peso_real,
            "photo": photo,
            "start_time_stamp": start_time_stamp,
            "end_time_stamp": end_time_stamp,
            "tentativas": tentativas,
            "itens": itens
        }
        try:
            response = requests.post(url, json=payload, headers=headers, verify=False)  # Enviando o payload como JSON
            response.raise_for_status()  # Levanta um erro se o status code não for 200
            print(f"{GREEN}Dados de pesagem enviados com sucesso: {response.json()}{RESET}")
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao enviar dados de pesagem para a API: {e}{RESET}")
    if(config.pending_order == True):
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute("INSERT INTO pesagem (pick_list_id, peso_estimado, peso_real, photo, start_time_stamp, end_time_stamp, tentativas) VALUES (:pick_list_id, :peso_estimado, :peso_real, :photo, :start_time_stamp, :end_time_stamp, :tentativas)", {"pick_list_id": pick_list_id ,"peso_estimado": peso_estimado, "peso_real": peso_real, "photo": photo, "start_time_stamp":start_time_stamp, "end_time_stamp": end_time_stamp, "tentativas": tentativas})
            con.commit()
            print(GREEN + "Dados de pesagem adicionados ao banco de dados." + RESET)
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)

def clear_database_orders():
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    print("Clearing orders in the database via API")
    if(config.api_offline == False or config.pending_order == False):
        url = f"{config.api_url}/pedidos/limpar"
        try:
            response = requests.post(url, headers=headers, verify=False)
            response.raise_for_status()
            print(f"{GREEN}Pedidos limpos com sucesso na API.{RESET}")
        except requests.exceptions.RequestException as e:
            print(f"{RED}Erro ao limpar pedidos na API: {e}{RED}")
    if(config.pending_order == True):
        con, cur= open_database_connection()
        if con is not None:
            print(GREEN + "Conexão ao banco de dados bem-sucedida" + RESET)
            cur.execute("UPDATE pick_list SET confirmado = 1, state = 1 WHERE (confirmado = 0 OR state = 0) AND codigo_restaurante = :rest_code", {"rest_code": config.rest_code})
            con.commit()
            print(GREEN + "Dados de pesagem adicionados ao banco de dados." + RESET)
        else:
            print(RED + "Erro ao abrir a base de dados" + RESET)


# GUI Layout Functions
def create_button(nr_pedido, row_counter, row_number_view,molh):
    global last_order_number
    if(last_order_number  == nr_pedido):
        print(f"{RED}Botão duplicado detectado{RESET}")
        button_text = f"{nr_pedido} \n ------------ \n {molh}"
        row = [sg.pin(
        sg.Col([[
            sg.Button("X", border_width=0, visible=False, key=('-DEL-', 0)),
            sg.Button(button_text, size=(18, 6), font=("Arial Bold", 18), key=('-DESC-', 0), visible= False),
            sg.Text(f'{row_number_view}', key=('-STATUS-', row_counter), visible= False)
        ]], key=('-ROW-', 0)
        ))]
        row_number_view -= 1
    else:
        print(f"{CYAN}Creating button for pedido: {nr_pedido}, row_counter: {row_counter}, row_number_view: {row_number_view}{RESET}")
        button_text = f"{nr_pedido} \n ------------ \n {molh}"
        row = [sg.pin(
            sg.Col([[
                sg.Button("X", size=(2, 1),border_width=0, visible=True, key=('-DEL-', nr_pedido), button_color=("white", "red")),
                sg.Button(button_text, size=(18, 6), font=("Arial Bold", 18), key=('-DESC-', nr_pedido)),
                sg.Text(f'{row_number_view}', key=('-STATUS-', row_counter))
            ]], key=('-ROW-', nr_pedido)
        ))]
    last_order_number = nr_pedido
    return row

def restart_gui(window, serial_scale, camera):
    #Função para reiniciar a GUI sem a necessidade de um script bat.
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
                 [sg.Column([], key='-ROW_PANEL-')]]

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

    if config.lado_botao == 'esquerdo':
        layout = [top_row,
                [sg.Column(order_col, element_justification='c', vertical_alignment='t'),
                sg.Column(left_col, element_justification='c', vertical_alignment='t'), sg.VSeperator(),
                sg.Column(midle_col, element_justification='c', vertical_alignment='t'), sg.VSeperator(),
                sg.Column(right_col, element_justification='c', vertical_alignment='t'),
                sg.Column(molhos_col, element_justification='c', vertical_alignment='t')]]
    else:
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


def process_order(window, order, serial_scale, camera, id):
    global row_counter, row_number_view
    print(f"{CYAN}Processing order: {order}{RESET}")

    window['-Pedido-'].update(order['delivery_name'])

    # Verifica se 'list' já é uma lista; caso contrário, faz o parsing JSON
    if isinstance(order['list'], str):
        try:
            order_json = json.loads(order['list'])
        except json.JSONDecodeError as e:
            print(f"{RED}Erro ao analisar JSON no campo 'list': {e}{RESET}")
            log_error(f"Erro ao analisar JSON no campo 'list': {e}")
            order_json = []  # Define como lista vazia em caso de erro de parsing
    elif isinstance(order['list'], list):
        order_json = order['list']
    else:
        print(f"{RED}Formato inesperado para o campo 'list'.{RESET}")
        log_error("Formato inesperado para o campo 'list'.")
        order_json = []

    peso, variancia, itens = calculate_order_weight(window, order_json)

    # Atualiza a interface com o peso estimado calculado
    window['-Peso_t-'].update(f'{peso}')

    if peso > 1300:
        peso += 14

    capture_image(camera, order['id'], window)

    process_weighing(window, serial_scale, peso, order['delivery_name'], camera, id, itens)

def calculate_order_weight(window, order_json):
    print(f"{CYAN}Calculating weight for order items{RESET}")
    peso = 0
    variancia = 0
    found_molho = False
    found_tarte = False
    found_bag = False
    found_ketchup = False
    found_both = False
    itens_count = 0

    for item in order_json:
        if item["tipo"] == "Molho":
            if 'molho' in item["name"].lower():
                found_molho = True
            if 'ketchup' in item["name"].lower():
                found_ketchup = True
            display_order_item(window, '-ML1-', item, 'orange')
            itens_count += 1 * int(item["quantidade"])
        elif item["tipo"] == "Addon":
            if 'sopa' not in item["name"].lower():
                peso += int(item["quantidade"]) * item["peso_produto"]
                print(f"Peso atualizado (Addon): {peso}")
            display_order_item(window, '-ML5-', item)
            itens_count += 1 * int(item["quantidade"])
        elif item["tipo"] == "Sanduiche":
            # Verifica se o item possui peso negativo (Happy Meal ou similar)
            if item["peso"] < 0:
                if 'natura' in item:
                    peso += int(item["quantidade"]) * item["peso"]
                else:
                    # Aplica o peso negativo diretamente para compensar o peso de outros itens
                    peso += int(item["quantidade"]) * item["peso_produto"]
                print(f"Peso atualizado (Happy Meal/Negativo): {peso}")
            else:
                # Verifica se o próprio item possui o campo 'natura' e usa 'peso_natura' se aplicável
                if 'natura' in item:
                    peso += int(item["quantidade"]) * item["peso_natura"]
                else:
                    peso += int(item["quantidade"]) * item["peso_produto"]
                print(f"Peso atualizado (Sanduiche): {peso}")
            
            # Atualiza a variância
            variancia += int(item["quantidade"]) * item["variancia"]
            
            # Verifica se o item é uma tarte de maçã
            if 'tarte de maca' in item["name"].lower():
                found_tarte = True
                display_order_item(window, '-ML2-', item, "orange")
            else:
                display_order_item(window, '-ML2-', item)
            itens_count += 1 * int(item["quantidade"])
        elif item["tipo"] == "Batata":
            peso += int(item["quantidade"]) * item["peso_produto"]
            print(f"Peso atualizado (Batata): {peso}")
            display_order_item(window, '-ML3-', item)
            itens_count += 1 * int(item["quantidade"])
        elif item["tipo"] in ["Bebida", "Sobremesa", "Gelado", "Outros"]:
            if 'saco de transporte' in item["name"].lower():
                peso += 14
                found_bag = True
                #display_order_item(window, '-ML4-', item, "orange")
            else:
                display_order_item(window, '-ML4-', item)
            itens_count += 1 * int(item["quantidade"])

    print(itens_count)
# Simplificando a lógica de alerta de molho
    if found_molho or found_ketchup:
        if found_molho and found_ketchup:
            window['-molho-'].update('\n\n Atenção! \n O Pedido leva molho e ketchup!', background_color='#E78200', text_color='white')
        elif found_molho:
            window['-molho-'].update('\n\n Atenção! \n O Pedido leva molho!', background_color='orange', text_color='white')
        elif found_ketchup:
            window['-molho-'].update('\n\n Atenção! \n O Pedido leva ketchup!', background_color='red', text_color='white')
    if found_tarte:
        window['-tarte-'].update('\n\n Atenção! \n O pedido leva tarte de maça!', background_color='blue', text_color='white')


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
        play_tarte()
    # Mudar fundo do campo de sobremesas para azul se uma tarte de maçã for encontrada

    print(f"{CYAN}Calculated weight: {peso}, variancia: {variancia}{RESET}")
    return peso, variancia, itens_count

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
    frameSize = (400, 260)

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


def get_string_time():
    current_time = datetime.datetime.now()
    time_string = current_time.strftime('%Y%m%d_%Hh%Mm%Ss')
    return time_string

def print_confirmation(order_number):
    try:
        printer = usb.core.find(idVendor=0x04b8, idProduct=0x0202)
        if printer is None:
            raise ValueError("Impressora não encontrada.")

        # Set configuration and claim interface
        printer.set_configuration()
        usb.util.claim_interface(printer, 0)
        endpoint = 1

        message = str(order_number)
        now = datetime.datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        # Your ESC/POS setup and printing code
        printer.write(endpoint, b'\x1b\x32\x20')
        printer.write(endpoint, align_right)
        printer.write(endpoint, barra_preta)
        printer.write(endpoint, fim_barra_preta)
        printer.write(endpoint, b' Pedido pesado e confirmado\n\n\n\n')
        printer.write(endpoint, b'electronicamente por um sistema\n\n\n\n')
        printer.write(endpoint, b'de pesagem com balan\x87a e imagem.\n\n\n\n')

        printer.write(endpoint, double_height_width)
        printer.write(endpoint, bold_on)
        printer.write(endpoint, b'\x1dB\x01\x1bE\x01\n\n\n\n\n\n Pedido n\xA3mero:')
        printer.write(endpoint, message.encode('utf-8'))
        printer.write(endpoint, b'\x1d!\x00\x1bE\x00\x1d!\x00\x1dB\x00\n')
        printer.write(endpoint, normal_size)
        printer.write(endpoint, bold_off)

        printer.write(endpoint, align_left)
        printer.write(endpoint, b'\n\n\n\n\n\n\n Validado a: ')
        printer.write(endpoint, dt_string.encode('utf-8'))
        printer.write(endpoint, b'\n\n\n\n \n\n\n\n')

        printer.write(endpoint, b'\x1d\x56\x01')  # Cut paper

        print("Talao impresso pedido", order_number)

    except usb.core.USBError as e:
        print(f"Erro USB: {e}")
    except Exception as e:
        print(f"Erro geral: {e}")
    finally:
        try:
            usb.util.release_interface(printer, 0)
        except Exception:
            pass

def get_molhos_from_order(order_json):
    molhos = []
    for item in order_json:
        if item["tipo"] == "Molho":
            s2 = item["quantidade"] + " " + item["name"]
            molhos.append(s2)
    if not molhos:  # Verifica se a lista está vazia
        return "Sem molhos"
    return '\n'.join(molhos)
    

def process_weighing(window, serial_scale, estimated_weight, order_number, camera, id, itens):
    global weighing_attempts
    
    # Fetch order details
    order = fetch_order_details(order_number)
    
    # Extract id and time_stamp from the fetched order details
    order_id = order['id']  # Captura o id do pedido
    start_time_stamp = order['time_stamp']  # Captura o time_stamp do pedido
    end_time_stamp = get_string_time()
    
    print(order_id)  # Imprime o id
    print(start_time_stamp)  # Imprime o time_stamp
    print(end_time_stamp)

    print(f"{CYAN}Processing weighing, estimated weight: {estimated_weight}{RESET}")
    weights = []
    image_file = None  # Variável para armazenar o caminho da imagem
    lista_pesos_save=[]

    # Tentar ler os dados da balança por até 10 vezes
    serial_scale.reset_input_buffer()
    for _ in range(2):
        time.sleep(0.1)
        scale_data = serial_scale.readline().decode('utf-8').strip()
        print(f"{CYAN}Raw scale data: {scale_data}{RESET}")  # Imprimir os dados brutos

        try:
            # Verifica se o dado é do formato esperado e extrai o valor em kg
            #if scale_data.startswith('ST'):---------------------------------- eliminado para testar rapidez
                # Extrai a parte do peso em kg (posição 7 até 14)
            weight_kg = float(scale_data[7:14])
            weight_grams = int(weight_kg * 1000)  # Converte para gramas
            print(f"{CYAN}Processed weight: {weight_grams}{RESET}")  # Verifica o peso processado
            if weight_grams > 0:
                weights.append(weight_grams)
        except ValueError as ve:
            print(f"{RED}ValueError: {ve}{RESET}")  # Mostrar o erro específico
            print(f"{RED}Invalid data received from scale.{RESET}")
        
        if len(weights) >= 3:
            break

        lista_pesos_save.append(scale_data)  # guarda todos dados da balança num array  
        
    weighing_try = 0
    if weights:
        actual_weight = weights[-1]  # Pega o último valor válido de peso
        image_file = capture_image(camera, order_id, window)
        deviation = actual_weight - estimated_weight
        print(f"Actual weight: {actual_weight}, Deviation: {deviation}")
        window['-Peso_r-'].update(str(actual_weight))
        
        
        # Se o desvio estiver dentro da faixa aceitável, o pedido deve ser confirmado
        if -60 <= deviation <= 80:
            if estimated_weight <= 10:
                window['-Peso_r-'].update("n/a")
                window['-Confirmar-'].update('\n Pedido não aplicável à balança', background_color="gray60")
                window[('-ROW-', order_number)].update(visible=False)
            else:
                weighing_try += 1
                print(f"{CYAN}Peso dentro da faixa aceitável. Confirmando pedido {order_number}.{RESET}")
                update_confirmation_status(window, deviation)
                confirm_order_api(order_number)  # Confirmar o pedido na API
                print_confirmation(order_number) #imprime ticket na impressora com dados
                
                # Enviar os dados de pesagem para a API
                send_weight_data_to_api(
                    pick_list_id=order_id,  # Utiliza o id do pedido
                    peso_estimado=estimated_weight,
                    peso_real=actual_weight,
                    photo=image_file,
                    start_time_stamp=start_time_stamp,
                    end_time_stamp=end_time_stamp,
                    tentativas=weighing_try,
                    itens=itens
                )
            
            window[('-ROW-', order_number)].update(visible=False)  # Remove o pedido da tela
        else:
            if estimated_weight <= 10:
                window['-Peso_r-'].update("n/a")
                window['-Confirmar-'].update('\n Pedido não aplicável à balança', background_color="gray60")
                window[('-ROW-', order_number)].update(visible=False)

            else:
                weighing_try += 1
                print(f"{CYAN}Peso fora da faixa aceitável.{RESET}")
                update_confirmation_status(window, deviation)
                # Incrementar o contador de tentativas para o pedido
                if order_number in weighing_attempts:
                    weighing_attempts[order_number] += 1
                else:
                    weighing_attempts[order_number] = 1

                # Verificarse o limite de tentativas foi atingido
                if weighing_attempts[order_number] >= 2:
                    print(f"{CYAN}Pedido {order_number} removido após 2 tentativas falhadas.{RESET}")
                    window[('-ROW-', order_number)].update(visible=False)
                    del weighing_attempts[order_number]  # Remover o pedido das tentativas
                    send_weight_data_to_api(
                        pick_list_id=order_id,  # Utiliza o id do pedido
                        peso_estimado=estimated_weight,
                        peso_real=actual_weight,
                        photo=image_file,
                        start_time_stamp=start_time_stamp,
                        end_time_stamp=end_time_stamp,
                        tentativas=2,
                        itens=itens
                    )
    else:
        if estimated_weight <= 10:
            window['-Peso_r-'].update("n/a")
            window['-Confirmar-'].update('\n Pedido não aplicável à balança', background_color="gray60")
            window[('-ROW-', order_number)].update(visible=False)
        else:
            print(f"{CYAN}Peso instável ou 0{RESET}")
            window['-Peso_r-'].update("Instável")
            window['-Confirmar-'].update('\n Pedido instável ou a 0', background_color="gray60")

    t = datetime.datetime.now()
    s=t.strftime('%Y/%m/%d %H:%M:%S')

    file_object = open(config.file_pesagem, 'a')
    file_object.write('\n'+s+'; '+str(order_number)+'; '+str(estimated_weight)+'; '+str(weights))  # guarda a data num ficheiro txt

    for peso_arr in lista_pesos_save:
        file_object.write('; '+str(peso_arr))
        
    file_object.close() 
        
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

    # Verifica se 'order_state' é um dicionário e contém as chaves esperadas
    if isinstance(order_state, dict):
        state = order_state.get('state')
        confirmado = order_state.get('confirmado')

        # Garante que 'state' e 'confirmado' sejam do tipo certo para comparação
        if isinstance(state, (int, str)) and isinstance(confirmado, (int, str)):
            # Converte para inteiros se forem strings para evitar comparações incorretas
            confirmed = int(state) == 1 and int(confirmado) == 1
            print(f"{CYAN}Order confirmed: {confirmed}{RESET}")
            return confirmed
        else:
            print(f"{RED}Formato inesperado para 'state' ou 'confirmado': {order_state}{RESET}")
            log_error(f"Formato inesperado para 'state' ou 'confirmado': {order_state}")
            return False
    else:
        print(f"{RED}Formato de dados inesperado ao verificar o estado do pedido: {order_state}{RESET}")
        log_error(f"Formato de dados inesperado ao verificar o estado do pedido: {order_state}")
        return False

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
        if order:  # Verifique se order não é None e tem o formato esperado
            molhos=[]
            s2=0
        
            if isinstance(order, list) and len(order) > 0 and isinstance(order[0], dict):  # Para o caso de DB local
                nr_pedido = order[0]['delivery_name']
                lista=json.loads(order[0]['list'])
                print(type(lista))
                for item in lista:
                    if item.get("tipo")=="Molho":
                        s2=item["quantidade"]+" "+item["name"]
                        molhos.append(s2)
                        print("molho1")
            elif isinstance(order, dict) and 'delivery_name' in order:  # Para o caso de API
                nr_pedido = order['delivery_name']
                lista=json.loads(order['list'])
                for item in lista:
                    if item.get("tipo")=="Molho":
                        s2=item["quantidade"]+" "+item["name"]
                        molhos.append(s2)
                        print("molho2")
            else:
                print(f"{RED}Formato inesperado de pedido: {order}{RESET}")
                return  # Não continue se o formato estiver errado

            print(f"{CYAN}New order found: {nr_pedido}{RESET}")

            order_json = json.loads(order['list'])
            molhos_text = get_molhos_from_order(order_json)
           
            
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
                window.extend_layout(window['-ROW_PANEL-'], [create_button(nr_pedido, row_counter, row_number_view,molhos_text)])
                update_order_state(nr_pedido)
        else:
            print(f"{CYAN}Nenhum pedido pendente encontrado.{RESET}")

    finally:
        # Defina a flag como False após a execução ser concluída
        with verped_lock:
            verped_running = False

def reset_orders(window, serial_scale, camera):
    global row_counter, row_number_view, funcpri  # Declarar funcpri como variável global

    print(f"{CYAN}Resetting orders in the database and UI{RESET}")

    window['-Confirmar-'].update('\n Por favor aguarde! \n Apagando os pedidos...', background_color="orange", text_color="white")
    window.refresh()  # Atualiza a interface imediatamente

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
    funcpri = SetInterval(3, lambda: verped(window, serial_scale, camera))
    
    print("Checking for pending orders")
    order = fetch_last_order()

    if order:
        nr_pedido = order['delivery_name']

        print(f"{CYAN}New order found: {nr_pedido}{RESET}")



        order_json2 = json.loads(order['list'])
        molhos_text = get_molhos_from_order(order_json2)
        
        # Verificar se o pedido já existe na interface
        existing_order_keys = [key for key in window.AllKeysDict if isinstance(key, tuple) and key[0] == '-ROW-' and key[1] == nr_pedido]
        
        if existing_order_keys:
            print(f"{CYAN}Pedido {nr_pedido} já existe. Atualizando informações.{RESET}")
            # Atualiza o pedido existente na interface
            update_existing_order_button(window, nr_pedido)
            update_order_state(nr_pedido)
        else:    
            row_counter += 1
            row_number_view += 1
            #window.extend_layout(window['-ROW_PANEL-'], [create_button(nr_pedido, row_counter, row_number_view,molhos2)])
            window.extend_layout(window['-ROW_PANEL-'], [create_button(nr_pedido, row_counter, row_number_view,molhos_text)])
            update_order_state(nr_pedido)

def handle_order(window, order_number, serial_scale, camera):
    global funcpri  # Declarar funcpri como variável global
    print(f"{CYAN}Handling order: {order_number}{RESET}")
    window['-Confirmar-'].update('\n Por favor, aguarde! \n Pesagem em andamento...', background_color="orange", text_color="white")
    window.refresh()  # Atualiza a interface imediatamente
    if funcpri is not None:
        funcpri.cancel()
    clear_display(window)
    
    order = fetch_order_details(order_number)
    if order is None:
        print(f"{RED}Erro: Detalhes do pedido não encontrados para o pedido {order_number}.{RESET}")
        log_error(f"Detalhes do pedido não encontrados para o pedido {order_number}.")
        return  # Adicione um retorno para parar o processamento

    # Verificar se o retorno é um dicionário e contém as chaves necessárias
    if isinstance(order, dict):
        if config.api_offline or config.pending_order:
            if 'id' in order:
                id = order["id"]
            else:
                print(f"{RED}Erro: 'id' não encontrado nos detalhes do pedido {order_number}.{RESET}")
                log_error(f"'id' não encontrado nos detalhes do pedido {order_number}.")
                return  # Adicione um retorno para parar o processamento
        else:
            if 'id' in order and 'delivery_name' in order:
                id = order['id']
            else:
                print(f"{RED}Formato de dados de pedido inesperado: {order}{RESET}")
                log_error(f"Formato de dados de pedido inesperado: {order}")
                return  # Adicione um retorno para parar o processamento
    else:
        print(f"{RED}Formato de dados inesperado para o pedido {order_number}: {order}{RESET}")
        log_error(f"Formato de dados inesperado para o pedido {order_number}: {order}")
        return  # Adicione um retorno para parar o processamento

    process_order(window, order, serial_scale, camera, id)
    
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
            reset_orders(window, serial_scale, camera)

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




