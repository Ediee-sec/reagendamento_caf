import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import sys

class ReadFile:
    def __init__(self):
        self.file = os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'downloads', 'Relatório Geral.xlsx')
        
    def read(self):
        self.df = pd.read_excel(self.file)
        
        return self.df
    
    def data_cleansing(self):
        self.df.dropna(how='all', inplace=True)
        self.df.dropna(axis=1, how='all', inplace=True)
        self.df.drop_duplicates(inplace=True)
        
        return self.df
    
    def only_desired_columns(self):
        self.df = self.df[['NOME', 'CURSO', 'FONE', 'DATA_AGENDAMENTO', 'TOTAL_AGENDAMENTOS', 'STATUS_PENDENCIA']]
        
        return self.df
    
    def filter_for_date(self):
        
        self.df['DATA_AGENDAMENTO'] = pd.to_datetime(self.df['DATA_AGENDAMENTO'], errors='coerce')
        now = pd.to_datetime(datetime.now().date())
        self.df = self.df[self.df['DATA_AGENDAMENTO'] <= now]
        
    def filter_for_status(self):
        self.df = self.df[self.df['STATUS_PENDENCIA'] != 'Finalizado' or self.df['STATUS_PENDENCIA'] != 'FinalizadoM']
        
        return self.df
        
    def data(self):
        self.read()
        self.data_cleansing()
        self.only_desired_columns()
        self.filter_for_date()
        
        os.remove(self.file)
        
        return self.df