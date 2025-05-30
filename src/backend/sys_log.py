import logging
from datetime import datetime
import traceback
import os
from pathlib import Path


class SysLog:
    def __init__(self):
        self.base_path = str(Path(__file__).resolve().parents[2])
        self.path = os.path.join(self.base_path, 'logs', 'log_backend')
        self.now = datetime.now()
        self.log_file = self.now.strftime(f"application_%Y_%m_%d.log")


    def config_log(self):   
        file_path = os.path.join(self.path, self.log_file)
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s', 
                            handlers=[
                                logging.FileHandler(file_path, mode='a', encoding='utf-8'),
                                logging.StreamHandler(),
                                
                            ])
            
            
    def det_error(self, e) -> str:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        tb_str = ''.join(tb_str)
        
        return tb_str
        
        
    def log_message(self, level: str, message: str, exception: Exception = None) -> None:
        """
        Registra mensagens com diferentes níveis de severidade e detalhes de exceção opcionais.
        
        Args:
            level (str): Nível de log ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
            message (str): Mensagem de log
            exception (Exception, opcional): Objeto de exceção para log de erro detalhado
        """
        # Dicionário mapeando níveis de log para funções de logging
        log_levels = {
            "INFO": logging.info,
            "WARNING": logging.warning,
            "ERROR": logging.error,
            "CRITICAL": logging.critical
        }
        
        try:
            level_upper = level.upper()
            
            if level_upper not in log_levels:
                logging.warning(f"Nível de log desconhecido: {level}. Usando WARNING como padrão.")
                log_func = logging.warning
            else:
                log_func = log_levels[level_upper]
            
            if exception and level_upper in ["ERROR", "CRITICAL"]:
                full_message = f"{message}\nDetalhes do Erro:\n{self.det_error(exception)}"
                log_func(full_message)
            else:
                log_func(message)
        
        except Exception as log_error:
            # Registro de fallback em caso de falha no logging
            logging.critical(f"Falha ao registrar mensagem: {log_error}")
            logging.critical(f"Mensagem original: {message}")
            
            
# job = SysLog()
# job.log_message('INFO', 'teste')