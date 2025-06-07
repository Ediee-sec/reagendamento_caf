import unittest
import json
import os
import sys
from pathlib import Path
import pandas as pd
import shutil

# Adicionar o diretório src ao PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[1] / 'src' / 'frontend'))

from app import app, scraping_state # Importar scraping_state

class DownloadTestCase(unittest.TestCase):

    def setUp(self):
        # Configurar o cliente de teste do Flask
        self.app = app.test_client()
        self.app.testing = True
        # Criar diretório temp se não existir
        os.makedirs('temp', exist_ok=True)
        # Resetar o estado do scraping antes de cada teste
        scraping_state.reset() # Acessar diretamente a variável global

    def tearDown(self):
        # Limpar o diretório temp após cada teste
        temp_dir = Path('temp')
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Erro ao limpar diretório temp: {e}")
                
    def test_download_results_success(self):
        """Testa o download quando há resultados"""
        # Popular o result_df com dados de teste
        test_data = {
            'col1': [1, 2],
            'col2': ['a', 'b']
        }
        scraping_state.result_df = pd.DataFrame(test_data) # Acessar diretamente
        scraping_state.status = "completed" # Simular estado completo

        # Chamar o endpoint de download
        response = self.app.get('/download')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))

        # Verificar a resposta JSON
        self.assertTrue(data['success'])
        self.assertIn('filename', data)
        self.assertIn('download_url', data)
        self.assertTrue(data['filename'].endswith('.csv'))
        self.assertTrue(data['download_url'].startswith('/temp/'))

        # Verificar se o arquivo temporário foi criado
        temp_filepath = Path('temp') / data['filename']
        self.assertTrue(temp_filepath.exists())
        
        # Opcional: Verificar o conteúdo do arquivo CSV
        read_df = pd.read_csv(temp_filepath)
        pd.testing.assert_frame_equal(read_df, scraping_state.result_df) # Acessar diretamente

    def test_download_results_no_data(self):
        """Testa o download quando não há resultados"""
        # Garantir que result_df esteja vazio
        scraping_state.result_df = pd.DataFrame() # Acessar diretamente
        scraping_state.status = "completed" # Simular estado completo

        # Chamar o endpoint de download
        response = self.app.get('/download')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))

        # Verificar a resposta JSON
        self.assertFalse(data['success'])
        self.assertIn('Nenhum resultado para download.', data['message'])
        
        # Verificar que nenhum arquivo foi criado na pasta temp
        temp_dir = Path('temp')
        self.assertEqual(len(list(temp_dir.iterdir())), 0, "Arquivos foram criados na pasta temp quando não deveriam")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False) 