import pandas as pd
import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import os
import sys

sys.path.append(os.path.join(str(Path(__file__).resolve().parents[2])))
from src.backend.sys_log import SysLog

class Mail:
    def __init__(self, df):
        self.df = df
        self.validate_env_vars()
        self.setup_smtp()
        self.subject = 'Resultado do Reagendamento Automático - SGC'
        
    def validate_env_vars(self):
        required_vars = [
            'VAR_PROJ_CAF_EMAIL_FROM',
            'VAR_PROJ_CAF_KEY',
            'VAR_PROJ_CAF_EMAIL_TO',
            'VAR_PROJ_CAF_SERVER',
            'VAR_PROJ_CAF_PORT'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
            
        self.email = os.getenv('VAR_PROJ_CAF_EMAIL_FROM')
        self.password = os.getenv('VAR_PROJ_CAF_KEY')
        self.to = os.getenv('VAR_PROJ_CAF_EMAIL_TO')
        
    def setup_smtp(self):
        try:
            self.server = smtplib.SMTP(
                os.getenv('VAR_PROJ_CAF_SMTP_SERVER'),
                int(os.getenv('VAR_PROJ_CAF_SMTP_PORT'))
            )
            self.server.starttls()
            self.server.login(self.email, self.password)
        except Exception as e:
            raise Exception(f"Erro ao configurar SMTP: {str(e)}")
            
    def create_template(self):
        def style():
            with open(os.path.join(Path(__file__).resolve().parents[0], 'static', 'style.css'), 'r') as f:
                return f.read()         
    
        df_html = self.df.to_html(
            index=False,
            classes='data-table',
            escape=False
        )
        df_html = df_html.replace('<tr style="text-align: right;">', '<tr>')
        df_html = df_html.replace('border="1"', '')
        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        {style()}
        </style>
        </head>
        <body>
        {df_html}
        </body>
        </html>
        """
        
        return template
    
    def send_mail(self):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.to
            msg['Subject'] = self.subject
            
            msg.attach(MIMEText(self.create_template(), 'html'))
            
            self.server.sendmail(self.email, self.to, msg.as_string())
            self.server.quit()
            SysLog().log_message('INFO', 'Email enviado com sucesso')
        except Exception as e:
            SysLog().log_message('ERROR', f'Erro ao enviar email: {str(e)}', e)
            raise
