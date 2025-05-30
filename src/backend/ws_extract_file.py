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

sys.path.append(os.path.join(str(Path(__file__).resolve().parents[2])))
from src.backend.treatment import ReadFile 
from src.backend.send_email import Mail
from src.backend.sys_log import SysLog

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
    def __init__(self):
        super().__init__()
        SysLog().log_message('INFO', 'Iniciando Web Scraping para extração de arquivos')
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
        except Exception as e:
            raise Exception(f"Erro ao fazer login: {e}")
        
        
    def navegation(self):
        SysLog().log_message('INFO', 'Iniciando navegação no sistema')
        SafeActions(self.driver, '/html/body/div/div/div/section/div[3]/div[2]/div[2]/div/div/div[2]/div/a', 'click').execute()
        self.open_new_window(1)
        time.sleep(15)
        SafeActions(self.driver, '//*[@id="side-menu-btn"]/i', 'click').execute()
        SafeActions(self.driver, '//*[@id="accordion"]/li[3]', 'click').execute()
        SafeActions(self.driver, '//*[@id="collapse-report"]/a[3]', 'click').execute()
        self.open_new_window(2)
        SafeActions(self.driver, '/html/body/div[3]/section/div[2]/div[1]/div/div/div[2]/button[1]', 'click').execute()
        
    def filter(self):
        SysLog().log_message('INFO', 'Iniciando filtro de dados')
        time.sleep(5)  # Espera o elemento ser carregado
        SafeActions(self.driver, "//button[normalize-space()='Filtrar']", 'click').execute()
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
        
    
    def reschedule(self):
        SysLog().log_message('INFO', 'Iniciando reagendamento de dados')
        df = ReadFile().data()
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
            df.to_csv(os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'results', 'reagendados.csv'), index=False)
            Mail(df).send_mail()
        except Exception as e:
            df.to_csv(os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'results', 'reagendados.csv'), index=False)
            Mail(df).send_mail()
            SysLog().log_message('ERROR', f'Erro ao reagendar o telefone: {row["FONE"]}', e)
        finally: 
            SysLog().log_message('INFO', 'Fechando o navegador')
            self.driver.quit()
            SysLog().log_message('INFO', 'Processo de reagendamento concluído com sucesso')        

        
# job = WSExtractFile()
# job.login()
# job.navegation()
# job.filter()
# job.reschedule()
        


       

