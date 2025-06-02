import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import sys

class ReadFile:
    def __init__(self, date_filter='accumulated' or None, specific_date=None):
        self.file = os.path.join(str(Path(__file__).resolve().parents[2]), 'data', 'csv', 'downloads', 'Relatório Geral.xlsx')
        self.date_filter = date_filter  # accumulated, today, specific
        self.specific_date = specific_date  # Usado quando date_filter é 'specific'
        self.pending_today_count = 0
        self.pending_accumulated_count = 0
        
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
        # Converter a coluna de data para datetime
        self.df['DATA_AGENDAMENTO'] = pd.to_datetime(self.df['DATA_AGENDAMENTO'], errors='coerce')
        now = pd.to_datetime(datetime.now().date())
        
        if self.date_filter == 'accumulated':
            # Pendente acumulado: registros com data menor que hoje
            self.df = self.df[self.df['DATA_AGENDAMENTO'] < now]
            
            
        elif self.date_filter == 'today':
            # Pendente hoje: registros com data igual a hoje
            self.df = self.df[self.df['DATA_AGENDAMENTO'] == now]
            self.pending_today_count = len(self.df)
            
        elif self.date_filter == 'accumulated_today':
            # Pendente acumulado + hoje: registros com data menor ou igual a hoje
            self.df = self.df[self.df['DATA_AGENDAMENTO'] <= now]
            
            
        elif self.date_filter == 'specific' and self.specific_date:
            # Pendente dia específico: registros com data igual à data específica
            specific_date = pd.to_datetime(self.specific_date)
            self.df = self.df[self.df['DATA_AGENDAMENTO'] == specific_date]
            
        else:
            # Fallback para o comportamento original (menor ou igual a hoje)
            self.df = self.df[self.df['DATA_AGENDAMENTO'] <= now]
            
        
        
    def filter_for_status(self):
        self.df = self.df[self.df['STATUS_PENDENCIA'] != 'Finalizado' or self.df['STATUS_PENDENCIA'] != 'FinalizadoM']
        
        return self.df
    
    def get_pending_counts(self):
        """Retorna as contagens de pendentes calculadas durante o filtro"""
        now = pd.to_datetime(datetime.now().date())
        self.pending_accumulated_count = len(self.df[self.df['DATA_AGENDAMENTO'] < now])
        self.pending_today_count = len(self.df[self.df['DATA_AGENDAMENTO'] == now])
        
        return {
            'dataframe': self.df,
            'pending_today': self.pending_today_count,
            'pending_accumulated': self.pending_accumulated_count,
            'total_pending': self.pending_today_count + self.pending_accumulated_count
        }
        
    def data(self):
        self.read()
        self.data_cleansing()
        self.only_desired_columns()
        self.filter_for_date()
        self.get_pending_counts()
        
        os.remove(self.file)  # Remove o arquivo após o processamento
        
        return self.get_pending_counts()