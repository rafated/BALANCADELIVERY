import sqlite3
import requests
import pandas as pd
import config
import logging

# Configurando o logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Função para pegar os dados da API
def fetch_data_from_api(api_url):
    headers = {
        'x-api-key': config.api_key  # Adicionando o cabeçalho da API Key
    }
    try:
        logging.info(f"Fazendo requisição para {api_url}")
        response = requests.get(api_url, headers=headers, verify=False)
        if response.status_code == 200:
            logging.info(f"Requisição para {api_url} bem-sucedida. Dados recebidos.")
            data = response.json()
            logging.debug(f"Dados recebidos da API ({api_url}): {data}")  # Exibe os dados recebidos em modo debug
            return data
        else:
            logging.error(f"Erro ao acessar {api_url}. Status Code: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Erro na requisição para {api_url}: {e}")
        return None

# Função para sincronizar os dados da API com a base de dados local
def sync_table_data_from_api(table_name, api_url):
    # Pegar os dados da API
    logging.info(f"Iniciando sincronização da tabela '{table_name}' com dados de {api_url}")
    data = fetch_data_from_api(api_url)
    if data is None:
        logging.error(f"Erro: Nenhum dado retornado da API para a tabela '{table_name}'")
        return

    # Conectar ao banco de dados local
    logging.info(f"Conectando ao banco de dados: {config.data_base}")
    conn = sqlite3.connect(config.data_base)
    cursor = conn.cursor()

    try:
        # Apagar os dados existentes na tabela local
        delete_query = f"DELETE FROM {table_name}"
        cursor.execute(delete_query)
        conn.commit()
        logging.info(f"Dados antigos da tabela '{table_name}' apagados com sucesso.")

        # Inserir os dados da API na tabela local
        df = pd.DataFrame(data)
        if not df.empty:
            df.to_sql(table_name, conn, if_exists='append', index=False)
            logging.info(f"Dados da tabela '{table_name}' sincronizados com sucesso.")
        else:
            logging.warning(f"Atenção: Nenhum dado encontrado para inserir na tabela '{table_name}'.")

    except Exception as e:
        logging.error(f"Erro ao sincronizar a tabela '{table_name}': {e}")
    finally:
        # Fechar a conexão com o banco de dados
        conn.close()
        logging.info(f"Conexão com o banco de dados fechada para a tabela '{table_name}'.")

# Função principal para sincronizar todas as tabelas
def sync_all_tables():
    # Define as URLs específicas para cada tabela
    tables = {
        "designacao": f"{config.api_url}/designacao_todos",
        "produtos": f"{config.api_url}/produtos_todos",
        "ingredientes": f"{config.api_url}/ingredientes_todos"
    }

    # Loop para sincronizar cada tabela individualmente
    logging.info("Iniciando a sincronização de todas as tabelas.")
    for table_name, api_url in tables.items():
        logging.info(f"Iniciando sincronização da tabela '{table_name}'")
        sync_table_data_from_api(table_name, api_url)
    logging.info("Sincronização de todas as tabelas finalizada.")

if __name__ == "__main__":
    # Sincronizar dados de todas as tabelas
    logging.info("Iniciando o processo de sincronização de tabelas.")
    sync_all_tables()
    logging.info("Processo de sincronização finalizado.")
