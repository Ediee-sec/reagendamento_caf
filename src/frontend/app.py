from flask import Flask, render_template, jsonify, request
import pandas as pd
import threading
import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar a classe de scraping do backend
sys.path.append(os.path.join(str(Path(__file__).resolve().parents[2]))) 
from src.backend.ws_extract_file import WSExtractFile

app = Flask(__name__, template_folder='templates', static_folder='static')

# Estado global da aplicação
class ScrapingState:
    def __init__(self):
        self.thread = None
        self.is_running = False
        self.cancel_requested = False
        self.progress = 0
        self.status = "idle"  # idle, running, completed, error, cancelled
        self.start_time = None
        self.end_time = None
        self.result_df = pd.DataFrame()
        self.error_message = ""
        self.current_step = ""
        self.activity_log = [] # Adicionado para logs de atividade
        self.log_lock = threading.Lock() # Lock para thread safety
        self.pending_today_count = 0
        self.pending_accumulated_count = 0
        self.total_pending_count = 0
        
    def reset(self):
        with self.log_lock: # Usar lock ao modificar a lista
            self.activity_log.clear()
        self.is_running = False
        self.cancel_requested = False
        self.progress = 0
        self.status = "idle"
        self.start_time = None
        self.end_time = None
        self.result_df = pd.DataFrame()
        self.error_message = ""
        self.current_step = ""
        self.pending_today_count = 0
        self.pending_accumulated_count = 0
        self.total_pending_count = 0

scraping_state = ScrapingState()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_scraping():
    global scraping_state
    
    # Obter dados da requisição (email, senha e filtro de data)
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data or 'date_filter' not in data:
        return jsonify({
            "success": False,
            "error": "E-mail, senha e filtro de data são obrigatórios."
        }), 400
        
    # Validar filtro de data específica se necessário
    if data.get('date_filter') == 'specific' and 'specific_date' not in data:
        return jsonify({
            "success": False,
            "error": "Data específica é obrigatória quando o filtro 'Pendente Dia Específico' é selecionado."
        }), 400

    # Verificar se já está rodando
    if scraping_state.is_running:
        return jsonify({
            "success": False, 
            "error": "Scraping já está em execução."
        })
    
    # Resetar estado
    scraping_state.reset()
    scraping_state.is_running = True
    scraping_state.status = "running"
    scraping_state.start_time = datetime.now()

    def run_scraper():
        try:
            logger.info("Iniciando processo de scraping...")
            email = data.get('email')
            password = data.get('password')
            date_filter = data.get('date_filter')
            specific_date = data.get('specific_date')
            
            logger.info(f"Recebido e-mail: {email}") # Log para confirmação
            logger.info(f"Filtro de data: {date_filter}{' - ' + specific_date if specific_date else ''}")
            
            scraping_state.current_step = "Inicializando..."
            scraping_state.progress = 10
            
            # Definir a função de callback para logs
            def add_log_entry(message_or_data):
                with scraping_state.log_lock:
                    # Verificar se é uma mensagem de texto ou um objeto de dados
                    if isinstance(message_or_data, dict):
                        # Se for um objeto de dados com contagens de pendentes
                        if message_or_data.get('type') == 'pending_counts':
                            counts = message_or_data.get('counts', {})
                            scraping_state.pending_today_count = counts.get('pending_today', 0)
                            scraping_state.pending_accumulated_count = counts.get('pending_accumulated', 0)
                            scraping_state.total_pending_count = counts.get('total_pending', 0)
                            
                        # Se for uma atualização de contagens durante o processo
                        elif message_or_data.get('type') == 'pending_counts_update':
                            counts = message_or_data.get('counts', {})
                            scraping_state.pending_today_count = counts.get('pending_today', 0)
                            scraping_state.pending_accumulated_count = counts.get('pending_accumulated', 0)
                            scraping_state.total_pending_count = counts.get('total_pending', 0)
                    else:
                        # Se for uma mensagem de texto normal
                        scraping_state.activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message_or_data}")
            
            if scraping_state.cancel_requested:
                return
                
            job = WSExtractFile(log_callback=add_log_entry, date_filter=date_filter, specific_date=specific_date) # Passar o callback e filtros
            
            scraping_state.current_step = "Fazendo login..."
            scraping_state.progress = 20
            job.login(email, password)
            
            if scraping_state.cancel_requested:
                return
                
            scraping_state.current_step = "Navegando..."
            scraping_state.progress = 40
            job.navegation()
            
            if scraping_state.cancel_requested:
                return
                
            scraping_state.current_step = "Aplicando filtros..."
            scraping_state.progress = 60
            job.filter()
            
            if scraping_state.cancel_requested:
                return
                
            scraping_state.current_step = "Reagendando..."
            scraping_state.progress = 80
            job.reschedule()
            
            if scraping_state.cancel_requested:
                return
                
            scraping_state.current_step = "Processando resultados..."
            scraping_state.progress = 90
            
            # Carregar resultados
            csv_path = os.path.join(
                str(Path(__file__).resolve().parents[2]), 
                'data', 'csv', 'results', 'reagendados.csv'
            )
            
            if os.path.exists(csv_path):
                scraping_state.result_df = pd.read_csv(csv_path)
            else:
                scraping_state.result_df = pd.DataFrame()
                
            scraping_state.progress = 100
            scraping_state.status = "completed"
            scraping_state.end_time = datetime.now()
            scraping_state.current_step = "Concluído!"
            
            logger.info(f"Scraping concluído. {len(scraping_state.result_df)} registros processados.")
            
        except Exception as e:
            logger.error(f"Erro durante scraping: {str(e)}")
            scraping_state.status = "error"
            scraping_state.error_message = str(e)
            scraping_state.end_time = datetime.now()
        finally:
            scraping_state.is_running = False

    # Iniciar thread
    scraping_state.thread = threading.Thread(target=run_scraper)
    scraping_state.thread.daemon = True
    scraping_state.thread.start()
    
    return jsonify({
        "success": True, 
        "message": "Scraping iniciado com sucesso."
    })

@app.route('/cancel', methods=['POST'])
def cancel_scraping():
    global scraping_state
    
    if not scraping_state.is_running:
        return jsonify({
            "success": False,
            "message": "Nenhum processo em execução para cancelar."
        })
    
    scraping_state.cancel_requested = True
    scraping_state.status = "cancelled"
    scraping_state.end_time = datetime.now()
    scraping_state.current_step = "Cancelado pelo usuário"
    
    logger.info("Cancelamento solicitado pelo usuário.")
    
    return jsonify({
        "success": True,
        "message": "Solicitação de cancelamento enviada."
    })

@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint para obter status atual do scraping"""
    duration = None
    if scraping_state.start_time:
        end_time = scraping_state.end_time or datetime.now()
        duration = (end_time - scraping_state.start_time).total_seconds()
    
    response_data = {
        "is_running": scraping_state.is_running,
        "status": scraping_state.status,
        "progress": scraping_state.progress,
        "current_step": scraping_state.current_step,
        "duration": duration,
        "records_count": len(scraping_state.result_df) if not scraping_state.result_df.empty else 0,
        "activity_log": scraping_state.activity_log[:],  # Retorna uma cópia da lista
        "pending_counts": {
            "today": scraping_state.pending_today_count,
            "accumulated": scraping_state.pending_accumulated_count,
            "total": scraping_state.total_pending_count
        }
    }
    
    if scraping_state.status == "error":
        response_data["error"] = scraping_state.error_message
    
    if scraping_state.status == "completed" and not scraping_state.result_df.empty:
        response_data["data"] = scraping_state.result_df.to_dict(orient='records')
    
    return jsonify(response_data)

@app.route('/results', methods=['GET'])
def get_results():
    """Endpoint separado para obter apenas os resultados"""
    if scraping_state.result_df.empty:
        return jsonify({"success": False, "message": "Nenhum resultado disponível."})
    
    return jsonify({
        "success": True,
        "data": scraping_state.result_df.to_dict(orient='records'),
        "count": len(scraping_state.result_df)
    })

@app.route('/download', methods=['GET'])
def download_results():
    """Endpoint para download dos resultados em CSV"""
    if scraping_state.result_df.empty:
        return jsonify({"success": False, "message": "Nenhum resultado para download."})
    
    try:
        # Salvar em arquivo temporário
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraping_results_{timestamp}.csv"
        temp_path = os.path.join("temp", filename)
        
        # Criar diretório temp se não existir
        os.makedirs("temp", exist_ok=True)
        
        scraping_state.result_df.to_csv(temp_path, index=False)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": f"/temp/{filename}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/temp/<filename>')
def serve_temp_file(filename):
    """Servir arquivos temporários"""
    return app.send_static_file(f"../temp/{filename}")

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {str(error)}")
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    # Criar diretórios necessários
    os.makedirs("temp", exist_ok=True)
    
    # Rodar aplicação
    app.run(host='0.0.0.0', port=5000, debug=True, use_debugger=True, use_reloader=False)