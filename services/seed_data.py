from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database.models import Lead, AuditoriaTransacao, Aplicativo, LogAcesso, RegistroErro



SAMPLE_LEADS = [
    {
        "codigo": "MC-2026-0001",
        "razao_social": "Activia Logística e Distribuição S/A",
        "nome_fantasia": "Activia Logística",
        "documento": "12.345.678/0001-90",
        "contato_nome": "Diretoria de Operações",
        "contato_cargo": "Gerente Geral de Logística",
        "email": "operacoes@activialog.com.br",
        "telefone": "(11) 98000-1001",
        "origem": "MalhaX Rollout",
        "plano": "MalhaX Enterprise Fleet",
        "valor_mensal": 5000.00,
        "status_pagamento": "PENDENTE",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-25",
        "data_pagamento": None,
        "dias_atraso": 0,
        "nfe_emitida": False,
        "observacoes": "Cliente piloto da plataforma central MalhaX. Rollout operacional em implantação.",
    },
    {
        "codigo": "MC-2026-0002",
        "razao_social": "Clínica Psicanálise Dra. Shirlei Elisabete",
        "nome_fantasia": "Dra. Shirlei Elisabete",
        "documento": "98.765.432/0001-10",
        "contato_nome": "Dra. Shirlei Elisabete",
        "contato_cargo": "Psicanalista Titular",
        "email": "psicanaliseshirlei@gmail.com",
        "telefone": "(11) 99000-2002",
        "origem": "01.Clínicas (PythonAnywhere)",
        "plano": "Portal Clínico & Pacientes",
        "valor_mensal": 1200.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-10",
        "data_pagamento": "2026-10-10 10:00",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Sistema clínico em produção e ativo no PythonAnywhere.",
    },
    {
        "codigo": "MC-2026-0003",
        "razao_social": "Açaiteria Maranata Operações & Varejo Ltda",
        "nome_fantasia": "Açaiteria Maranata",
        "documento": "45.678.901/0001-23",
        "contato_nome": "Gerência Maranata",
        "contato_cargo": "Responsável de Loja",
        "email": "contato@maranataacai.com.br",
        "telefone": "(11) 97000-3003",
        "origem": "05.Açaiteria",
        "plano": "Totem Autoatendimento & Insumos",
        "valor_mensal": 1800.00,
        "status_pagamento": "PENDENTE",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-20",
        "data_pagamento": None,
        "dias_atraso": 0,
        "nfe_emitida": False,
        "observacoes": "Módulo de autoatendimento e comanda rápida.",
    },
    {
        "codigo": "MC-2026-0004",
        "razao_social": "Clínica de Psicologia Dra. Raquel",
        "nome_fantasia": "Dra. Raquel Psicologia",
        "documento": "34.567.890/0001-45",
        "contato_nome": "Dra. Raquel",
        "contato_cargo": "Psicóloga Responsável",
        "email": "contato@psiraquel.com.br",
        "telefone": "(11) 96000-4004",
        "origem": "01.Clínicas",
        "plano": "Portal de Pacientes & Sessões",
        "valor_mensal": 1200.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-05",
        "data_pagamento": "2026-10-05 14:30",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Gestão de consultas e histórico de prontuários.",
    },
    {
        "codigo": "MC-2026-0005",
        "razao_social": "AdegaOS Distribuidora de Bebidas Ltda",
        "nome_fantasia": "AdegaOS Distribuidora",
        "documento": "56.789.012/0001-67",
        "contato_nome": "Coordenação de Estoque",
        "contato_cargo": "Gestor WMS",
        "email": "contato@adegaos.com.br",
        "telefone": "(11) 95000-5005",
        "origem": "03.Adegas",
        "plano": "WMS & Gestão de Adegas",
        "valor_mensal": 2500.00,
        "status_pagamento": "PENDENTE",
        "metodo_pagamento": "BOLETO",
        "vencimento": "2026-10-18",
        "data_pagamento": None,
        "dias_atraso": 0,
        "nfe_emitida": False,
        "observacoes": "Backend FastAPI para controle de estoque, compras e vendas.",
    }
]


SAMPLE_APPS = [
    {
        "slug": "04-logistica",
        "nome": "04.Logística Enterprise",
        "categoria": "Logística & Frotas",
        "ambiente": "producao",
        "api_key": "mc_live_logistica_77ab12",
        "status": "CRITICO",
        "descricao": "Roteirização e rastreamento de cargas de frota interestadual."
    },
    {
        "slug": "01-clinicas",
        "nome": "01.Clínicas — Dra. Shirlei Elisabete",
        "categoria": "Saúde & Psicanálise",
        "ambiente": "producao",
        "api_key": "mc_live_clinicas_shirlei_99cc44",
        "status": "OPERACIONAL",
        "descricao": "Sistema de Controle Clínico & Portal de Pacientes (Psicanálise).",
        "url_acesso": "https://tiago.pythonanywhere.com/admin/login"
    },
    {
        "slug": "03-adegas",
        "nome": "03.Adegas WineCore",
        "categoria": "Varejo & Estoque",
        "ambiente": "producao",
        "api_key": "mc_live_adegas_33ee55",
        "status": "OPERACIONAL",
        "descricao": "Controle de safra, estoque de vinhos finos e PDV."
    },
    {
        "slug": "05-acaiteria",
        "nome": "05.Açaiteria FastCore",
        "categoria": "Food Service",
        "ambiente": "producao",
        "api_key": "mc_live_acaiteria_88dd11",
        "status": "OPERACIONAL",
        "descricao": "Totem de autoatendimento e comanda rápida."
    },
    {
        "slug": "06-malhacore",
        "nome": "06.MalhaCore Central",
        "categoria": "Núcleo de Comando",
        "ambiente": "producao",
        "api_key": "mc_live_core_master_001",
        "status": "OPERACIONAL",
        "descricao": "Painel de controle financeiro, auditoria e telemetria preditiva."
    }
]

SAMPLE_ERROS = [
    {
        "app_slug": "04-logistica",
        "app_nome": "04.Logística Enterprise",
        "nivel": "CRITICAL",
        "tipo_erro": "DatabaseConnectionTimeout",
        "mensagem": "Timeout de 5000ms atingido ao conectar no pool de dados de telemetria de frota.",
        "traceback": "Traceback (most recent call last):\n  File 'services/roteirizacao.py', line 88, in calcular_rota\n    db_conn = pool.acquire(timeout=5.0)\n  File 'db/pool.py', line 142, in acquire\nTimeoutError: Timeout de 5000ms atingido ao conectar no pool",
        "rota_ou_funcao": "/api/rotas/otimizar",
        "cliente_afetado": "TransLogística Brasil S/A",
        "usuario_afetado": "carlos.silveira@translogbrasil.com.br",
        "ambiente": "producao",
        "status": "NOVO",
        "recorrencias": 8
    },
    {
        "app_slug": "01-clinicas",
        "app_nome": "01.Clínicas MedCore",
        "nivel": "ERROR",
        "tipo_erro": "KeyError: 'cpf_titular'",
        "mensagem": "Chave obrigatória 'cpf_titular' ausente no payload de agendamento de convênio.",
        "traceback": "Traceback (most recent call last):\n  File 'routes/agendamento.py', line 45, in criar_consulta\n    cpf = payload['convenio']['cpf_titular']\nKeyError: 'cpf_titular'",
        "rota_ou_funcao": "/api/consultas/agendar",
        "cliente_afetado": "Clínica Santa Maria Ltda",
        "usuario_afetado": "recepcao@santamaria.med.br",
        "ambiente": "producao",
        "status": "EM_ANALISE",
        "recorrencias": 3
    },
    {
        "app_slug": "04-logistica",
        "app_nome": "04.Logística Enterprise",
        "nivel": "ERROR",
        "tipo_erro": "HTTP 502 Bad Gateway",
        "mensagem": "Falha na comunicação com a API externa da SEFAZ para emissão de MDF-e.",
        "traceback": "Traceback (most recent call last):\n  File 'services/sefaz.py', line 112, in emitir_mdfe\n    resp = requests.post(sefaz_url, data=xml)\nrequests.exceptions.HTTPError: 502 Server Error: Bad Gateway",
        "rota_ou_funcao": "/api/fiscal/mdfe/emitir",
        "cliente_afetado": "Atlas Distribuição e Cargas Ltda",
        "usuario_afetado": "operador.fiscal@atlascargas.com.br",
        "ambiente": "producao",
        "status": "NOVO",
        "recorrencias": 5
    },
    {
        "app_slug": "03-adegas",
        "nome": "03.Adegas WineCore",
        "nivel": "WARNING",
        "tipo_erro": "AlertaEstoqueMinimo",
        "mensagem": "Lote Cabernet Sauvignon Gran Reserva atingiu limite de segurança (3 garrafas restantes).",
        "traceback": None,
        "rota_ou_funcao": "rotina_auditoria_estoque",
        "cliente_afetado": "Adega Gran Reserva",
        "usuario_afetado": "sommelier@adegagran.com.br",
        "ambiente": "producao",
        "status": "RESOLVIDO",
        "recorrencias": 1
    }
]

SAMPLE_ACESSOS = [
    {
        "app_slug": "04-logistica",
        "app_nome": "04.Logística Enterprise",
        "usuario": "carlos.silveira@translogbrasil.com.br",
        "cliente_identificador": "TransLogística Brasil S/A",
        "rota": "/api/rotas/otimizar",
        "metodo": "POST",
        "status_code": 500,
        "tempo_resposta_ms": 5012.4,
        "ip_origem": "177.132.40.11",
        "detalhes": "Falha no pool de banco de dados"
    },
    {
        "app_slug": "04-logistica",
        "app_nome": "04.Logística Enterprise",
        "usuario": "guilherme@deltafreight.com.br",
        "cliente_identificador": "Delta Freight",
        "rota": "/painel/motoristas/rastreio",
        "metodo": "GET",
        "status_code": 200,
        "tempo_resposta_ms": 32.8,
        "ip_origem": "189.44.12.89",
        "detalhes": "Consulta de telemetria GPS"
    },
    {
        "app_slug": "01-clinicas",
        "app_nome": "01.Clínicas MedCore",
        "usuario": "dr.roberto@medcore.com.br",
        "cliente_identificador": "Clínica Santa Maria Ltda",
        "rota": "/prontuario/paciente/8812",
        "metodo": "GET",
        "status_code": 200,
        "tempo_resposta_ms": 48.1,
        "ip_origem": "201.88.92.10",
        "detalhes": "Prontuário eletrônico aberto"
    },
    {
        "app_slug": "03-adegas",
        "app_nome": "03.Adegas WineCore",
        "usuario": "caixa01@adegagran.com.br",
        "cliente_identificador": "Adega Gran Reserva",
        "rota": "/pdv/checkout/venda",
        "metodo": "POST",
        "status_code": 201,
        "tempo_resposta_ms": 84.5,
        "ip_origem": "192.168.1.104",
        "detalhes": "Venda PDV aprovada via PIX"
    },
    {
        "app_slug": "05-acaiteria",
        "app_nome": "05.Açaiteria FastCore",
        "usuario": "totem_entrada_02",
        "cliente_identificador": "Açaí Tropical Ltda",
        "rota": "/totem/pedido/novo",
        "metodo": "POST",
        "status_code": 201,
        "tempo_resposta_ms": 22.0,
        "ip_origem": "10.0.0.50",
        "detalhes": "Comanda de açaí 500ml gerada"
    },
    {
        "app_slug": "06-malhacore",
        "app_nome": "06.MalhaCore Central",
        "usuario": "controladoria@malhacore.com",
        "cliente_identificador": "Controladoria Interna",
        "rota": "/api/financeiro/resumo",
        "metodo": "GET",
        "status_code": 200,
        "tempo_resposta_ms": 14.2,
        "ip_origem": "127.0.0.1",
        "detalhes": "Leitura de KPIs financeiros"
    }
]


def seed_database(db: Session):
    from services import auth_service
    auth_service.obter_ou_criar_usuario_admin(db, email="tiagoaraujoxsl@gmail.com", senha_pura="Neyva@10")

    existing_count = db.query(Lead).count()
    if existing_count == 0:
        for item in SAMPLE_LEADS:
            lead = Lead(**item)
            db.add(lead)
            db.flush()

            auditoria = AuditoriaTransacao(
                lead_id=lead.id,
                codigo_lead=lead.codigo,
                tipo_evento="CARGA_INICIAL" if lead.status_pagamento == "PENDENTE" else "LIQUIDACAO_CONFIRMADA",
                status_anterior=None,
                status_novo=lead.status_pagamento,
                valor=lead.valor_mensal,
                responsavel="Sistema MalhaCore",
                detalhes=f"Registro inicial de contrato - Status: {lead.status_pagamento}"
            )
            db.add(auditoria)
        db.commit()

    # Carga de Apps e Telemetria
    apps_count = db.query(Aplicativo).count()
    if apps_count == 0:
        agora = datetime.now(timezone.utc)
        for app_data in SAMPLE_APPS:
            app = Aplicativo(
                slug=app_data["slug"],
                nome=app_data["nome"],
                categoria=app_data["categoria"],
                ambiente=app_data["ambiente"],
                api_key=app_data["api_key"],
                status=app_data["status"],
                descricao=app_data["descricao"],
                url_acesso=app_data.get("url_acesso"),
                ultimo_ping=agora
            )
            db.add(app)
        db.flush()

        for err_data in SAMPLE_ERROS:
            err = RegistroErro(
                app_slug=err_data["app_slug"],
                app_nome=err_data.get("app_nome") or err_data.get("nome"),
                nivel=err_data["nivel"],
                tipo_erro=err_data["tipo_erro"],
                mensagem=err_data["mensagem"],
                traceback=err_data["traceback"],
                rota_ou_funcao=err_data["rota_ou_funcao"],
                cliente_afetado=err_data["cliente_afetado"],
                usuario_afetado=err_data["usuario_afetado"],
                ambiente=err_data["ambiente"],
                status=err_data["status"],
                recorrencias=err_data["recorrencias"],
                criado_em=agora - timedelta(minutes=45),
                atualizado_em=agora - timedelta(minutes=10)
            )
            db.add(err)

        for acc_data in SAMPLE_ACESSOS:
            acc = LogAcesso(
                app_slug=acc_data["app_slug"],
                app_nome=acc_data["app_nome"],
                usuario=acc_data["usuario"],
                cliente_identificador=acc_data["cliente_identificador"],
                rota=acc_data["rota"],
                metodo=acc_data["metodo"],
                status_code=acc_data["status_code"],
                tempo_resposta_ms=acc_data["tempo_resposta_ms"],
                ip_origem=acc_data["ip_origem"],
                detalhes=acc_data["detalhes"],
                criado_em=agora - timedelta(minutes=15)
            )
            db.add(acc)

        db.commit()

