# MALHACORE — NÚCLEO DE COMANDO & AUDITORIA FINANCEIRA

Sistema gerencial corporativo de alta densidade para localização de leads, auditoria de contratos e telemetria de liquidação (pagos vs inadimplentes) do ecossistema **MalhaCore**.

---

## 1. DIRETRIZES DE DESIGN & ARQUITETURA
* **Zero Custo de Hospedagem:** Arquitetura orientada a SQLite local e FastAPI de alta performance, sem dependência de serviços externos pagos.
* **Sobriedade Operacional (Zero Ícones):** Layout institucional sem iconografia decorativa. Uso estrito de tipografia corporativa (`Plus Jakarta Sans` e `JetBrains Mono`), micro-rotulagem técnica e badges de status de alta densidade.
* **Segurança e Persistência:** Dados salvos em `data/malhacore.db` com histórico de auditoria por transação e backup automático integrado ao Google Drive.

---

## 2. ESTRUTURA DE DIRETÓRIOS NO VS CODE

```
06.MalhaCore/
├── .vscode/                   # Configurações do VS Code (Launch F5 e Settings)
│   ├── launch.json
│   └── settings.json
├── config/                    # Configurações e variáveis de ambiente
│   ├── __init__.py
│   └── settings.py
├── database/                  # Camada de banco de dados e ORM
│   ├── __init__.py
│   ├── connection.py          # Conexão SQLite
│   └── models.py              # Modelos Lead e AuditoriaTransacao
├── schemas/                   # Validação de dados (Pydantic v2)
│   ├── __init__.py
│   └── lead_schema.py
├── services/                  # Regras de negócio e telemetria
│   ├── __init__.py
│   ├── lead_service.py        # Busca, filtros, liquidação e CSV
│   └── seed_data.py           # Carga corporativa inicial
├── routes/                    # Rotas da aplicação
│   ├── __init__.py
│   ├── api_leads.py           # Endpoints REST (/api/leads)
│   └── views.py               # Renderização do painel
├── static/                    # Ativos do frontend corporativo
│   ├── css/
│   │   └── malhacore.css      # Design System sóbrio (sem ícones)
│   └── js/
│       └── app.js             # Busca em tempo real e filtros instantâneos
├── templates/                 # Telas em HTML / Jinja2
│   ├── base.html              # Shell do sistema
│   └── dashboard.html         # Painel Gerencial & Tabela de Auditoria
├── data/                      # Banco de dados persistente
│   └── malhacore.db
├── .env                       # Configuração de portas e ambiente
├── requirements.txt           # Dependências Python
├── run.py                     # Inicializador do servidor
└── README.md
```

---

## 3. COMO EXECUTAR NO VS CODE

1. Abra a pasta `G:\Meu Drive\App's\Python\06.MalhaCore` no **VS Code**.
2. Pressione **`F5`** (ou selecione *"MalhaCore: Iniciar Servidor (FastAPI)"* na aba Executar).
3. Ou no terminal integrado, execute:
   ```bash
   python run.py
   ```
4. Acesse no navegador:
   ```
   http://127.0.0.1:8000
   ```

---

## 4. FUNCIONALIDADES DO PAINEL GERENCIAL

* **Localizador Universal:** Busca instantânea por Razão Social, Nome Fantasia, CNPJ/CPF, Telefone, Contato ou Código de Contrato (`MC-2026-XXXX`).
* **Telemetria de Pagamentos & Atraso Automático:**
  * `[ PAGO ]` — Contratos liquidados com registro de data/hora.
  * `[ PENDENTE ]` — Contratos faturados aguardando compensação (PIX / Boleto / TED / Cartão).
  * `[ INADIMPLENTE ]` — Alertas de atraso com cálculo automático de dias corridos após o vencimento (`+8d`, `+14d`).
  * `[ CANCELADO ]` — Contratos descontinuados.
* **Ações Diretas em Cada Registro:**
  * Botão `[ DETALHES ]`: Abre modal executivo com Ficha Cadastral, Edição de Dados, Alteração de Status e Trilha Completa de Auditoria (`AuditoriaTransacao`).
  * Botão `[ BAIXA ]`: Liquidação instantânea de recebíveis com carimbo de data/hora.
  * Botão `[ COBRAR ]`: Abertura imediata de mensagem corporativa padronizada no WhatsApp do responsável financeiro.
  * Botão `[ EXPORTAR LEDGER CSV ]`: Download instantâneo da base de dados delimitada por ponto e vírgula para conciliação contábil em Excel.

---

## 5. ENDPOINTS REST DA API

### A. Módulo Financeiro & Leads
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Painel Web Executivo Unificado (Financeiro + Central de Apps + Erros + Acessos) |
| `GET` | `/api/leads` | Listagem de leads com filtros (`?busca=`, `?status=`, `?origem=`) |
| `GET` | `/api/leads/{id}` | Ficha detalhada do contrato/lead por ID |
| `POST` | `/api/leads` | Cadastro de novo contrato/lead com geração de código `MC-2026-XXXX` |
| `PUT` | `/api/leads/{id}` | Edição completa cadastral com registro em auditoria |
| `PATCH` | `/api/leads/{id}/status` | Alteração de status (Baixa, Pendência, Inadimplência, Cancelamento) |
| `DELETE` | `/api/leads/{id}` | Exclusão do lead com registro do evento em auditoria |
| `GET` | `/api/leads/{id}/auditoria` | Histórico cronológico de alterações e eventos daquele lead |
| `GET` | `/api/financeiro/resumo` | Métricas agregadas (Total, Pagos, Pendentes, Inadimplentes, R$) |
| `GET` | `/api/leads/exportar/csv` | Download do arquivo CSV formatado |

### B. Módulo Multi-App, Telemetria & Monitor de Erros
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/telemetria/resumo` | Resumo global de saúde, disponibilidade (%) e alertas preditivos |
| `GET` | `/api/telemetria/apps` | Catálogo de todos os aplicativos conectados com status de saúde |
| `POST` | `/api/telemetria/apps` | Cadastro/configuração manual de aplicativo |
| `POST` | `/api/telemetria/acesso` | Ingestão simplificada de log de acesso (usuário, rota, latência, HTTP code) |
| `POST` | `/api/telemetria/erro` | Ingestão simplificada de erro/bug com traceback completo e cliente afetado |
| `POST` | `/api/telemetria/ping/{slug}` | Batimento cardíaco (heartbeat) do aplicativo |
| `GET` | `/api/telemetria/erros` | Listagem de incidentes com filtros (`?app_slug=`, `?nivel=`, `?status=`) |
| `GET` | `/api/telemetria/erros/{id}` | Inspeção detalhada de um bug específico com stack trace |
| `PATCH` | `/api/telemetria/erros/{id}/status` | Resolução do bug (`EM_ANALISE`, `RESOLVIDO` + nota técnica) |
| `GET` | `/api/telemetria/acessos` | Trilha cronológica de acessos em todos os sistemas |

---

## 6. COMO CONECTAR OUTROS APPS VIA SDK (4 LINHAS)

O arquivo `sdk/malhacore_client.py` não possui nenhuma dependência externa (funciona em qualquer Python com `urllib` nativo).

```python
from malhacore_client import MalhaCoreMonitor

# 1. Inicializar apontando para a central
monitor = MalhaCoreMonitor(app_slug="04-logistica", app_nome="04.Logística Enterprise")

# 2. Registrar acesso do cliente
monitor.registrar_acesso(rota="/painel", usuario="operador@cliente.com", cliente="TransLog Brasil")

# 3. Capturar qualquer erro / exceção com Traceback completo
try:
    calcular_rota()
except Exception as e:
    monitor.capturar_excecao(e, cliente="TransLog Brasil", rota="/rotas/calcular")
```

---

## 7. SUÍTE DE TESTES AUTOMATIZADOS

Para rodar todos os testes de integração e validação do sistema:
```bash
python test_core.py
```
Testa renderização do dashboard, cálculo de métricas, filtros em memória, cadastro, baixa, edição, exclusão, exportação CSV e telemetria multi-app com 100% de cobertura operacional.


