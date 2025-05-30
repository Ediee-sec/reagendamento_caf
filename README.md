# Reagendamento CAF

Este projeto é uma aplicação Python para gerenciar o reagendamento de compromissos no sistema CAF. Ele é dividido em módulos backend e frontend, com suporte a logging, extração de arquivos e configuração de ambiente.

---

## Módulos

### Backend

#### 1. **`main.py`**
   - Ponto de entrada principal do backend.
   - Responsável por inicializar a aplicação e gerenciar as rotas.

#### 2. **`sys_log.py`**
   - Gerencia o sistema de logging.
   - Classe principal: `SysLog`
     - Método: `log_message(level: str, message: str, exception: Exception = None)`
       - Registra mensagens de log com diferentes níveis de severidade (`INFO`, `WARNING`, `ERROR`, `CRITICAL`).
       - Suporte a detalhes de exceção.

#### 3. **`send_email.py`**
   - Gerencia o envio de e-mails.
   - Utilizado para notificações e alertas.

#### 4. **`ws_extract_file.py`**
   - Classe principal: `Envoriment`
     - Configura o ambiente utilizando variáveis de ambiente.
     - Valida a presença das variáveis `VAR_PROJ_CAF_SITE`, `VAR_PROJ_CAF_USERNAME` e `VAR_PROJ_CAF_PASSWORD`.
     - Registra mensagens de log relacionadas à configuração do ambiente.

---

### Frontend

- **Descrição**: O módulo frontend é responsável pela interface do usuário. Ele ainda não possui detalhes específicos documentados.

---

## Logs

Os logs são armazenados na pasta `logs/` e estão divididos em:
- **`log_backend/`**: Logs relacionados ao backend.
- **`log_frontend/`**: Logs relacionados ao frontend.

---



## Dependências

As dependências do projeto estão listadas no arquivo [requirements.txt](requirements.txt). Para instalá-las, execute:

```bash
pip install -r [requirements.txt](http://_vscodecontentref_/1)
```
