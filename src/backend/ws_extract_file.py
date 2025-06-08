import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
import time
import traceback
from pathlib import Path
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.join(str(Path(__file__).resolve().parents[2])))
from src.backend.treatment import ReadFile 
from src.backend.send_email import Mail
from src.backend.sys_log import SysLog
from src.backend.models.load_data import LoadData
SysLog().config_log()



class Envoriment:
    def __init__(self):
        SysLog().log_message('INFO', 'Iniciando configuração do ambiente')
        self.url = os.environ.get('VAR_PROJ_CAF_SITE')
        # self.username = os.environ.get('VAR_PROJ_CAF_USERNAME')
        # self.password = os.environ.get('VAR_PROJ_CAF_PASSWORD')
        
        
class ConfigReschedule():
    def __init__(self):
        SysLog().log_message('INFO', 'Iniciando configuração de reagendamento')
        
    def days_to_reschedule(self, qtd):
        SysLog().log_message('INFO', f'Calculando dias para reagendamento com base na quantidade: {qtd}')
        if qtd <= 5:
            return 3
        elif qtd >= 6 and qtd <= 10:
            return 5
        elif qtd >= 11 and qtd <= 15:
            return 10
        elif qtd >= 16 and qtd <= 20:
            return 20
        elif qtd >= 21 and qtd <= 25:
            return 30
        else:
            return 40
        
class SafeActions:
    """
    Executa uma ação segura em um elemento Selenium com espera e retry.
    
    Parâmetros:
        driver: instância do Selenium WebDriver
        xpath: localizador do elemento (XPATH)
        action: 'click', 'send_keys', 'get_text'
        value: texto a ser enviado (usado com send_keys)
        max_retries: número máximo de tentativas
        interval: tempo entre as tentativas (em segundos)
        timeout: tempo máximo de espera para o elemento estar disponível
    """
    def __init__(self, driver, xpath, action, value=None, max_retries=5, interval=30, timeout=60):
        SysLog().log_message('INFO', f'Iniciando SafeActions com xpath: {xpath}, ação: {action}, valor: {value}, tentativas máximas: {max_retries}, intervalo: {interval}, timeout: {timeout}')
        self.driver = driver
        self.xpath = xpath
        self.action = action
        self.value = value
        self.max_retries = max_retries
        self.interval = interval
        self.timeout = timeout
        
    def execute(self):
        attempts = 0
        while attempts < self.max_retries:
            try:
                SysLog().log_message('INFO', f'Tentativa {attempts + 1} de {self.max_retries} para executar ação: {self.action} no elemento: {self.xpath}')
                if self.action == 'click':
                    element = WebDriverWait(self.driver, self.timeout).until(
                        EC.element_to_be_clickable((By.XPATH, self.xpath))
                    )
                    element.click()

                elif self.action == 'send_keys':
                    element = WebDriverWait(self.driver, self.timeout).until(
                        EC.visibility_of_element_located((By.XPATH, self.xpath))
                    )
                    element.clear()
                    element.send_keys(self.value)

                elif self.action == 'get_text':
                    element = WebDriverWait(self.driver, self.timeout).until(
                        EC.visibility_of_element_located((By.XPATH, self.xpath))
                    )
                    return element.text

                else:
                    raise ValueError(f"Ação '{self.action}' não suportada.")
                SysLog().log_message('INFO', f'Ação {self.action} executada com sucesso no elemento: {self.xpath}')
                return True

            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException) as e:
                SysLog().log_message('ERROR', f"Erro ao executar ação '{self.action}' no elemento {self.xpath}: {e}", e)
                print(f"[Tentativa {attempts + 1}] Falha ao executar '{self.action}' no elemento {self.xpath}: {e}")
                attempts += 1
                time.sleep(self.interval)

        SysLog().log_message('CRITICAL', f"Não foi possível executar a ação '{self.action}' após {self.max_retries} tentativas.") 
        raise Exception(f"Não foi possível executar a ação '{self.action}' após {self.max_retries} tentativas.")


class WSExtractFile(Envoriment, ConfigReschedule):
    def __init__(self, log_callback=None, date_filter='accumulated', specific_date=None): # Adicionado log_callback e parâmetros de filtro
        super().__init__()
        self.log_callback = log_callback # Armazena o callback
        self.date_filter = date_filter # Tipo de filtro: accumulated, today, specific
        self.specific_date = specific_date # Data específica para filtro (se aplicável)
        self.cancel_requested = False
        SysLog().log_message('INFO', f'Iniciando Web Scraping com filtro: {date_filter}{" - " + specific_date if specific_date else ""}')
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'downloads'),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        self.chrome_options.add_argument("--headless")  
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        self.chrome_options.add_argument("--disable-browser-side-navigation")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.get(self.url)
        self.driver.maximize_window()
        self.today = datetime.today().strftime('%m/%d/%Y')
        self.timeout = 300  # 5 minutos
        self.start_time = time.time()
  
    def open_new_window(self, position):
        SysLog().log_message('INFO', f'Abrindo nova janela na posição {position}')
        self.driver.switch_to.window(self.driver.window_handles[position])
        
    def dedup_elements_by_select(self, elements, value):
        SysLog().log_message('INFO', f'Deduplicando elementos por select com valor: {value}')
        time.sleep(5)  # Espera o elemento ser carregado
        all_status_elements = WebDriverWait(self.driver, 30).until(
        EC.presence_of_all_elements_located((By.XPATH, f'{elements}')))
        
        real_select = all_status_elements[1]
        select = Select(real_select)

        select.select_by_visible_text(value)
        

    def login(self, username, password):
        SysLog().log_message('INFO', 'Iniciando login no sistema')
        try:
            SafeActions(self.driver, '//*[@id="login-box-inner"]/form/div[1]/input', 'send_keys', username).execute()
            SafeActions(self.driver, '//*[@id="login-box-inner"]/form/div[2]/input', 'send_keys', password).execute()
            SafeActions(self.driver, '//*[@id="login-box-inner"]/form/div[6]/div/button', 'click').execute() 
            SysLog().log_message('INFO', f'Login realizado com sucesso para {username}')
            self.log_callback(f"Login realizado com sucesso para {username}") if self.log_callback else None
        except Exception as e:
            raise Exception(f"Erro ao fazer login: {e}")
        
        
    def navegation(self):
        SysLog().log_message('INFO', 'Iniciando navegação no sistema')
        try:
            SafeActions(self.driver, '/html/body/div/div/div/section/div[3]/div[2]/div[2]/div/div/div[2]/div/a', 'click').execute()
            self.open_new_window(1)
            time.sleep(5)
            SafeActions(self.driver, '//*[@id="side-menu-btn"]/i', 'click').execute()
            SafeActions(self.driver, '//*[@id="accordion"]/li[3]', 'click').execute()
            SafeActions(self.driver, '//*[@id="collapse-report"]/a[3]', 'click').execute()
            self.open_new_window(2)
            
            # Enviar log para o frontend
            if self.log_callback:
                self.log_callback("Navegação no sistema concluída com sucesso")
                
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Erro durante navegação: {str(e)}")
            raise
        
    def filter(self):
        SysLog().log_message('INFO', 'Iniciando filtro de dados')
        try:
            time.sleep(5)  # Espera o elemento ser carregado
            #SafeActions(self.driver, "(//button[normalize-space()='Filtrar'])[1]", 'click').execute()
            SafeActions(self.driver, '/html/body/div[3]/section/div[2]/div[1]/div/div/div[2]/button[1]', 'click').execute()
            time.sleep(2)  # Espera o modal de filtro abrir
            SafeActions(self.driver, '//*[@id="filterStatus"]/option[3]', 'click').execute()
            SafeActions(self.driver, '//*[@id="filterUsuario"]/option[2]', 'click').execute()
            SafeActions(self.driver, '//*[@id="filterStatusAgendamento"]/option[2]', 'click').execute()
            SafeActions(self.driver, '//*[@id="filterDataInicial"]', 'send_keys', '01/01/2020').execute()
            SafeActions(self.driver, '//*[@id="filterDataFinal"]', 'send_keys', self.today).execute()
            SafeActions(self.driver, '//*[@id="filterModal"]/div/div/div[3]/button[2]', 'click').execute()
            time.sleep(3)
            SafeActions(self.driver, '/html/body/div[3]/section/div[2]/div[1]/div/div/div[2]/button[2]', 'click').execute()  # Exportar CSV
            time.sleep(10)  # Espera o download do CSV ser concluído
            
            # Enviar log para o frontend
            if self.log_callback:
                self.log_callback("Filtros aplicados e dados exportados com sucesso")
                
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Erro ao aplicar filtros: {str(e)}")
            raise
        
    
    def reschedule(self):
        SysLog().log_message('INFO', 'Iniciando reagendamento de dados')
        # Passar os parâmetros de filtro para o ReadFile
        data = ReadFile(date_filter=self.date_filter, specific_date=self.specific_date).data()
        df = data['dataframe']
    
        # Enviar contagens para o callback, se disponível
        if self.log_callback:
            self.log_callback({
                'type': 'pending_counts',
                'counts': data
            })
            self.log_callback(f"Total de pendentes: {data['total_pending']} (Hoje: {data['pending_today']}, Acumulados: {data['pending_accumulated']})")
            
        # Armazenar contagens para uso durante o reagendamento
        self.pending_today_count = data['pending_today']
        self.pending_accumulated_count = data['pending_accumulated']
        
        try:
            for index, row in df.iterrows():
                SysLog().log_message('INFO', f'Reagendando o telefone: {row["FONE"]}')
                SafeActions(self.driver, '//*[@id="form-search"]/div/input', 'send_keys', row['FONE']).execute()
                SafeActions(self.driver, '//*[@id="button-addon2"]', 'click').execute()
                time.sleep(2)
                SafeActions(self.driver, '//*[@id="tableData"]/tr/td[12]/a/button', 'click').execute()
                SafeActions(self.driver, '//*[@id="openModalLinkAgendamento"]/button', 'click').execute()
                self.dedup_elements_by_select('//select[@id="status"]', 'Agendado')
                SafeActions(self.driver, '//*[@id="motivo"]/option[10]', 'click').execute()
                SafeActions(self.driver, '//*[@id="obs"]', 'send_keys', 'Mandei campanha vigente - Daiane').execute()
                SafeActions(self.driver, '//*[@id="tipo_agendamento"]/option[2]', 'click').execute()
                SafeActions(self.driver, '//*[@id="tipo_cadastro"]/option[3]', 'click').execute()
                
                today = datetime.now() + timedelta(days=self.days_to_reschedule(row['TOTAL_AGENDAMENTOS']))
                today = today.strftime('%m/%d/%Y')
                
                SafeActions(self.driver, '//*[@id="data_agendamento"]', 'send_keys', today).execute()
                SafeActions(self.driver, "//div[@id='editModalCadastrarAgendamento']//input[@id='submit_toggle_registration']", 'click').execute()
                time.sleep(6)
                SysLog().log_message('INFO', f'Reagendamento concluído para o telefone: {row["FONE"]}')
                
                # Enviar log para o frontend após o reagendamento
                if self.log_callback:
                    # Determinar se o registro é de hoje ou acumulado
                    data_agendamento = row.get('DATA_AGENDAMENTO')
                    now = pd.to_datetime(datetime.now().date())
                    
                    # Decrementar contadores apropriados
                    if data_agendamento == now:
                        self.pending_today_count -= 1
                    elif data_agendamento < now:
                        self.pending_accumulated_count -= 1
                    
                    # Enviar contagens atualizadas
                    self.log_callback({
                        'type': 'pending_counts_update',
                        'counts': {
                            'pending_today': self.pending_today_count,
                            'pending_accumulated': self.pending_accumulated_count,
                            'total_pending': self.pending_today_count + self.pending_accumulated_count
                        }
                    })
                                
                # Chamar o callback com a mensagem formatada
                if self.log_callback:
                    log_message = f"Reagendamento realizado com sucesso para: {row.get('NOME', 'N/A')} - {row['FONE']}"
                    self.log_callback(log_message)
            df.to_csv(os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'results', 'reagendados.csv'), index=False)
            LoadData(df).insert()
            Mail(df).send_mail()
        except Exception as e:
            df.to_csv(os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'results', 'reagendados.csv'), index=False)
            LoadData(df).insert()
            Mail(df).send_mail()
            SysLog().log_message('ERROR', f'Erro ao reagendar o telefone: {row["FONE"]}', e)
        finally: 
            SysLog().log_message('INFO', 'Fechando o navegador')
            self.driver.quit()
            SysLog().log_message('INFO', 'Processo de reagendamento concluído com sucesso')        

    def check_timeout(self):
        if time.time() - self.start_time > self.timeout:
            raise TimeoutError("Operação excedeu o tempo limite")
        
    def cancel(self):
        """Método para cancelar a execução do scraping"""
        self.cancel_requested = True
        SysLog().log_message('INFO', 'Cancelamento solicitado')
        if self.log_callback:
            self.log_callback("Cancelamento solicitado pelo usuário")
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            SysLog().log_message('ERROR', f'Erro ao fechar o driver: {str(e)}', e)
        
# job = WSExtractFile()
# job.login()
# job.navegation()
# job.filter()
# job.reschedule()
        


       

