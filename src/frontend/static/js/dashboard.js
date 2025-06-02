class ScrapingDashboard {
  constructor() {
    this.segundos = 0;
    this.intervalId = null;
    this.statusIntervalId = null;
    this.isRunning = false;
    
    // Elementos DOM
    this.elements = {
      tempo: document.getElementById("tempo"),
      statusIndicator: document.getElementById("statusIndicator"),
      statusText: document.getElementById("statusText"),
      currentStep: document.getElementById("currentStep"),
      progressFill: document.getElementById("progressFill"),
      progressText: document.getElementById("progressText"),
      startBtn: document.getElementById("startBtn"),
      cancelBtn: document.getElementById("cancelBtn"),
      resultsCard: document.getElementById("resultsCard"),
      recordsCount: document.getElementById("recordsCount"),
      downloadBtn: document.getElementById("downloadBtn"),
      tableContainer: document.getElementById("tableContainer"),
      emailInput: document.getElementById("emailInput"),
      passwordInput: document.getElementById("passwordInput"),
      logsContainer: document.getElementById("logsContainer"),
      // Elementos para contadores de pendentes
      pendingTodayCount: document.getElementById("pendingTodayCount"),
      pendingAccumulatedCount: document.getElementById("pendingAccumulatedCount"),
      totalPendingCount: document.getElementById("totalPendingCount")
    };
    
    this.initializeUI();
  }
  
  initializeUI() {
    this.addLog("Sistema iniciado e pronto para uso", "info");
    this.updateStatusIndicator("idle", "Aguardando");
    this.updateProgress(0);
  }
  
  atualizarCronometro() {
    this.segundos++;
    const horas = Math.floor(this.segundos / 3600);
    const minutos = Math.floor((this.segundos % 3600) / 60);
    const segs = this.segundos % 60;
    
    this.elements.tempo.textContent = 
      `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
  }
  
  updateStatusIndicator(status, text) {
    const statusDot = this.elements.statusIndicator.querySelector('.status-dot');
    statusDot.className = `status-dot ${status}`;
    this.elements.statusText.textContent = text;
  }
  
  updateProgress(percentage) {
    this.elements.progressFill.style.width = `${percentage}%`;
    this.elements.progressText.textContent = `${percentage}%`;
  }
  
  updateCurrentStep(step) {
    this.elements.currentStep.textContent = step;
  }
  
  // Método para atualizar os contadores de pendentes
  updateCurrentStep(step) {
    this.elements.currentStep.textContent = step;
  }
  
  // Método para atualizar os contadores de pendentes
  updatePendingCounts(counts) {
    if (!counts) return;
    
    // Atualizar os elementos na interface
    if (this.elements.pendingTodayCount) {
      this.elements.pendingTodayCount.textContent = counts.today || 0;
      this.elements.pendingTodayCount.classList.add('updated');
      setTimeout(() => {
        this.elements.pendingTodayCount.classList.remove('updated');
      }, 1000);
    }
    
    if (this.elements.pendingAccumulatedCount) {
      this.elements.pendingAccumulatedCount.textContent = counts.accumulated || 0;
      this.elements.pendingAccumulatedCount.classList.add('updated');
      setTimeout(() => {
        this.elements.pendingAccumulatedCount.classList.remove('updated');
      }, 1000);
    }
    
    if (this.elements.totalPendingCount) {
      this.elements.totalPendingCount.textContent = counts.total || 0;
      this.elements.totalPendingCount.classList.add('updated');
      setTimeout(() => {
        this.elements.totalPendingCount.classList.remove('updated');
      }, 1000);
    }
  }
  
  addLog(message, type = "info") {
    const logEntry = document.createElement("div");
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
      <span class="timestamp">${new Date().toLocaleTimeString()}</span>
      <span class="message">${message}</span>
    `;
    
    this.elements.logsContainer.appendChild(logEntry);
    this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
    
    // Manter apenas os últimos 50 logs
    const logs = this.elements.logsContainer.children;
    if (logs.length > 50) {
      this.elements.logsContainer.removeChild(logs[0]);
    }
  }
  
  async iniciar() {
    console.log('Método iniciar() executado');
    
    if (this.isRunning) {
      console.log('Processo já está em execução');
      this.addLog("Processo já está em execução", "warning");
      return;
    }
    
    try {
      console.log('Iniciando processo de scraping...');
      this.addLog("Iniciando processo de scraping...", "info");
      this.isRunning = true;
      this.segundos = 0;
      
      // Atualizar UI
      this.elements.startBtn.disabled = true;
      this.elements.cancelBtn.disabled = false;
      this.updateStatusIndicator("running", "Executando");
      this.updateCurrentStep("Iniciando...");
      this.updateProgress(0);
      this.elements.resultsCard.style.display = "none";
      
      console.log('UI atualizada, iniciando cronômetro...');
      
      // Iniciar cronômetro
      this.intervalId = setInterval(() => this.atualizarCronometro(), 1000);
      
      // Iniciar monitoramento de status
      this.statusIntervalId = setInterval(() => this.checkStatus(), 1000);
      
      // Obter email e senha
      const email = this.elements.emailInput.value;
      const password = this.elements.passwordInput.value;

      // Obter filtro de data selecionado do select
      const dateFilterSelect = document.getElementById('dateFilterSelect');
      const selectedFilter = dateFilterSelect.value;

      // Obter data específica se necessário
      let specificDate = null;
      if (selectedFilter === 'specific') {
        specificDate = document.getElementById('specificDate').value;
        if (!specificDate) {
          this.addLog("Por favor, selecione uma data específica.", "warning");
          this.finalizarProcesso("idle", "Aguardando");
          this.elements.startBtn.disabled = false;
          this.elements.cancelBtn.disabled = true;
          this.isRunning = false;
          return;
        }
      }
      
      // Validar se os campos foram preenchidos
      if (!email || !password) {
        this.addLog("Por favor, preencha o e-mail e a senha.", "warning");
        this.finalizarProcesso("idle", "Aguardando");
        return;
      }
      
      console.log('Fazendo requisição para /start...');
      
      // Chamar endpoint de início, enviando email, senha e filtro de data
      const requestData = { 
        email: email, 
        password: password,
        date_filter: selectedFilter
      };

      // Adicionar data específica se necessário
      if (selectedFilter === 'specific') {
        requestData.specific_date = specificDate;
      }

      this.addLog(`Iniciando com filtro: ${selectedFilter}${specificDate ? ' - ' + specificDate : ''}`, "info");

      const response = await fetch('/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      console.log('Resposta recebida:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Dados da resposta:', data);
      
      if (!data.success) {
        throw new Error(data.error || 'Erro desconhecido');
      }
      
      this.addLog("Processo iniciado com sucesso", "success");
      
    } catch (error) {
      console.error("Erro ao iniciar scraping:", error);
      this.addLog(`Erro ao iniciar: ${error.message}`, "error");
      this.finalizarProcesso("error", "Erro");
    }
  }
  
  async cancelar() {
    if (!this.isRunning) {
      this.addLog("Nenhum processo em execução para cancelar", "warning");
      return;
    }
    
    try {
      this.elements.cancelBtn.disabled = true;
      this.addLog("Solicitando cancelamento...", "warning");
      
      const response = await fetch('/cancel', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.addLog("Cancelamento solicitado com sucesso", "warning");
      } else {
        this.addLog(data.message || "Erro ao cancelar", "error");
      }
      
    } catch (error) {
      console.error("Erro ao cancelar:", error);
      this.addLog(`Erro ao cancelar: ${error.message}`, "error");
    }
  }
  
  async checkStatus() {
    if (!this.isRunning) return;
    
    try {
      const response = await fetch('/status');
      const data = await response.json();
      
      // Atualizar progresso
      if (data.progress !== undefined) {
        this.updateProgress(data.progress);
      }
      
      // Atualizar step atual
      if (data.pending_counts) {
        this.updatePendingCounts(data.pending_counts);
      }
      
      // Atualizar contadores de pendentes
      if (data.pending_counts) {
        this.updatePendingCounts(data.pending_counts);
      }
      
      // Atualizar logs de atividade
      if (data.activity_log && Array.isArray(data.activity_log)) {
        // Limpar logs antigos
        this.elements.logsContainer.innerHTML = '';
        
        // Adicionar logs do backend
        data.activity_log.forEach(logMsg => {
          const logEntry = document.createElement("div");
          logEntry.className = "log-entry info";
          
          // Extrair timestamp e mensagem se o formato for consistente
          const match = logMsg.match(/^\s*\[(.*?)\]\s*(.*)$/);
          if (match) {
            logEntry.innerHTML = `
              <span class="timestamp">${match[1]}</span>
              <span class="message">${match[2]}</span>
            `;
          } else {
            logEntry.innerHTML = `
              <span class="timestamp">${new Date().toLocaleTimeString()}</span>
              <span class="message">${logMsg}</span>
            `;
          }
          
          this.elements.logsContainer.appendChild(logEntry);
        });
        
        // Rolar para o final
        this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
      }
      
      // Verificar se processo terminou
      if (data.status === 'completed') {
        this.finalizarProcesso("completed", "Concluído");
        this.addLog(`Processo concluído! ${data.records_count} registros processados`, "success");
        
        if (data.data && data.data.length > 0) {
          this.showResults(data.data);
        }
        
      } else if (data.status === 'error') {
        this.finalizarProcesso("error", "Erro");
        this.addLog(`Erro: ${data.error || 'Erro desconhecido'}`, "error");
        
      } else if (data.status === 'cancelled') {
        this.finalizarProcesso("cancelled", "Cancelado");
        this.addLog("Processo cancelado pelo usuário", "warning");
      }
      
    } catch (error) {
      console.error("Erro ao verificar status:", error);
    }
  }
  
  finalizarProcesso(status, statusText) {
    this.isRunning = false;
    
    // Parar cronômetro e monitoramento
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    if (this.statusIntervalId) {
      clearInterval(this.statusIntervalId);
      this.statusIntervalId = null;
    }
    
    // Atualizar UI
    this.updateStatusIndicator(status, statusText);
    this.elements.startBtn.disabled = false;
    this.elements.cancelBtn.disabled = true;
    
    if (status === "completed") {
      this.updateProgress(100);
    }
  }
  
  showResults(data) {
    if (!data || data.length === 0) {
      this.elements.recordsCount.textContent = "Nenhum registro encontrado";
      this.elements.downloadBtn.disabled = true;
      return;
    }
    
    // Mostrar card de resultados
    this.elements.resultsCard.style.display = "block";
    this.elements.recordsCount.textContent = `${data.length} registros encontrados`;
    this.elements.downloadBtn.disabled = false;
    
    // Criar tabela
    this.createResultsTable(data);
  }
  
  createResultsTable(data) {
    if (!data || data.length === 0) return;
    
    const table = document.createElement('table');
    table.className = 'results-table';
    
    // Cabeçalho
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    const columns = Object.keys(data[0]);
    columns.forEach(column => {
      const th = document.createElement('th');
      th.textContent = column;
      headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Corpo da tabela
    const tbody = document.createElement('tbody');
    
    // Mostrar apenas os primeiros 100 registros para performance
    const displayData = data.slice(0, 100);
    
    displayData.forEach(row => {
      const tr = document.createElement('tr');
      
      columns.forEach(column => {
        const td = document.createElement('td');
        td.textContent = row[column] || '';
        tr.appendChild(td);
      });
      
      tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    
    // Limpar container e adicionar tabela
    this.elements.tableContainer.innerHTML = '';
    this.elements.tableContainer.appendChild(table);
    
    // Adicionar aviso se há mais registros
    if (data.length > 100) {
      const notice = document.createElement('div');
      notice.style.padding = '10px';
      notice.style.textAlign = 'center';
      notice.style.color = '#666';
      notice.style.fontStyle = 'italic';
      notice.textContent = `Mostrando 100 de ${data.length} registros. Faça o download para ver todos.`;
      this.elements.tableContainer.appendChild(notice);
    }
  }
  
  async downloadResults() {
    try {
      this.elements.downloadBtn.disabled = true;
      this.addLog("Preparando download...", "info");
      
      const response = await fetch('/download');
      const data = await response.json();
      
      if (data.success) {
        // Criar link temporário para download
        const link = document.createElement('a');
        link.href = data.download_url;
        link.download = data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.addLog(`Download iniciado: ${data.filename}`, "success");
      } else {
        throw new Error(data.error || 'Erro no download');
      }
      
    } catch (error) {
      console.error("Erro no download:", error);
      this.addLog(`Erro no download: ${error.message}`, "error");
    } finally {
      this.elements.downloadBtn.disabled = false;
    }
  }
}

// Aguardar DOM carregar antes de inicializar
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM carregado, inicializando dashboard...');
  
  // Verificar se todos os elementos existem
  const requiredElements = [
    'tempo', 'statusIndicator', 'statusText', 'currentStep', 
    'progressFill', 'progressText', 'startBtn', 'cancelBtn',
    'resultsCard', 'recordsCount', 'downloadBtn', 'tableContainer', 'logsContainer'
  ];
  
  const missingElements = requiredElements.filter(id => !document.getElementById(id));
  
  if (missingElements.length > 0) {
    console.error('Elementos HTML faltando:', missingElements);
    alert('Erro: Alguns elementos da interface não foram encontrados. Verifique o HTML.');
    return;
  }
  
  // Instância global do dashboard
  window.dashboard = new ScrapingDashboard();
  console.log('Dashboard inicializado com sucesso');
});

// Funções globais para compatibilidade
function iniciar() {
  console.log('Função iniciar() chamada');
  if (window.dashboard) {
    window.dashboard.iniciar();
  } else {
    console.error('Dashboard não foi inicializado');
    alert('Erro: Sistema não foi inicializado corretamente. Recarregue a página.');
  }
}

function cancelar() {
  console.log('Função cancelar() chamada');
  if (window.dashboard) {
    window.dashboard.cancelar();
  } else {
    console.error('Dashboard não foi inicializado');
  }
}

function downloadResults() {
  console.log('Função downloadResults() chamada');
  if (window.dashboard) {
    window.dashboard.downloadResults();
  } else {
    console.error('Dashboard não foi inicializado');
  }
}

// Cleanup quando a página é fechada
window.addEventListener('beforeunload', () => {
  if (window.dashboard && window.dashboard.isRunning) {
    // Tentar cancelar processo se ainda estiver rodando
    fetch('/cancel', { method: 'POST' }).catch(() => {});
  }
});
