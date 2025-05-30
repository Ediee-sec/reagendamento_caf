import pandas as pd
import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import os

class Mail:
    def __init__(self, df):
        self.df = df
        self.email = os.getenv('VAR_PROJ_CAF_EMAIL_FROM')
        self.password = os.getenv('VAR_PROJ_CAF_KEY')
        self.to = os.getenv('VAR_PROJ_CAF_EMAIL_TO')
        self.server = smtplib.SMTP(os.getenv('VAR_PROJ_CAF_SMTP_SERVER'), os.getenv('VAR_PROJ_CAF_SMTP_PORT'))
        self.subject = 'Resultado do Reagendamento Automático - SGC'
        
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
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = self.to
        msg['Subject'] = self.subject
        
        msg.attach(MIMEText(self.create_template(), 'html'))
        
        try:
            self.server.starttls()
            self.server.login(self.email, self.password)
            self.server.sendmail(self.email, self.to, msg.as_string())
            self.server.quit()
            print('Email enviado com sucesso')
        except Exception as e:
            print(f'Erro ao enviar email: {e}')
