import sys
import os
from pathlib import Path

# Adicionar o diretório src ao PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src'))

import pandas as pd
from backend.send_email import Mail

def test_email_sending():
    # Criar um DataFrame de teste
    test_data = {
        'Protocolo': ['123456', '789012'],
        'Status': ['Sucesso', 'Falha'],
        'Mensagem': ['Reagendado com sucesso', 'Erro ao reagendar']
    }
    df = pd.DataFrame(test_data)
    
    try:
        # Instanciar a classe Mail com o DataFrame de teste
        mail = Mail(df)
        # Tentar enviar o email
        mail.send_mail()
        print("✅ Teste de envio de email concluído com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {str(e)}")

if __name__ == "__main__":
    test_email_sending() 