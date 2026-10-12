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
        "slug": "malhax",
        "nome": "MalhaX — Plataforma Central de Operações & Logística",
        "categoria": "Logística Integrada & Frotas",
        "ambiente": "piloto",
        "api_key": "mc_live_malhax_activia_01",
        "status": "OPERACIONAL",
        "estagio_deploy": "ROLLOUT",
        "cliente_piloto": "Activia Logística",
        "versao": "1.0.0-rc1",
        "descricao": "App responsável por tudo. Consultoria operacional, inteligência de rotas, estoque e gestão de ativos. Piloto em implantação na Activia.",
        "url_acesso": None
    },
    {
        "slug": "01-clinicas",
        "nome": "01.Clínicas — Dra. Shirlei Elisabete",
        "categoria": "Saúde & Psicanálise",
        "ambiente": "producao",
        "api_key": "mc_live_clinicas_shirlei_99cc44",
        "status": "OPERACIONAL",
        "estagio_deploy": "PUBLICADO",
        "cliente_piloto": "Dra. Shirlei Elisabete",
        "versao": "1.0.0",
        "descricao": "Sistema de Controle Clínico & Portal de Pacientes (Psicanálise). No ar no PythonAnywhere.",
        "url_acesso": "https://tiago.pythonanywhere.com"
    },
    {
        "slug": "05-acaiteria",
        "nome": "05.Açaiteria — Maranata",
        "categoria": "Food Service & Operações",
        "ambiente": "desenvolvimento",
        "api_key": "mc_live_acaiteria_88dd11",
        "status": "OPERACIONAL",
        "estagio_deploy": "DESENVOLVIMENTO",
        "cliente_piloto": "Açaiteria Maranata",
        "versao": "0.1.0",
        "descricao": "Totem de autoatendimento, comanda rápida e gestão de insumos. Em fase de programação.",
        "url_acesso": None
    },
    {
        "slug": "03-adegas",
        "nome": "03.Adegas — AdegaOS",
        "categoria": "WMS & Distribuidoras",
        "ambiente": "desenvolvimento",
        "api_key": "mc_live_adegas_33ee55",
        "status": "OPERACIONAL",
        "estagio_deploy": "DESENVOLVIMENTO",
        "cliente_piloto": "AdegaOS Distribuidora",
        "versao": "0.1.0",
        "descricao": "Plataforma SaaS de gestão inteligente para Adegas, Distribuidoras e Empórios. Backend FastAPI.",
        "url_acesso": None
    },
    {
        "slug": "06-malhacore",
        "nome": "06.MalhaCore Central",
        "categoria": "Núcleo de Comando & Auditoria",
        "ambiente": "producao",
        "api_key": "mc_live_core_master_001",
        "status": "OPERACIONAL",
        "estagio_deploy": "PUBLICADO",
        "cliente_piloto": "MalhaCore Master",
        "versao": "1.1.0",
        "descricao": "Central executiva de auditoria financeira, telemetria de rede e observabilidade preditiva.",
        "url_acesso": "https://malhacore.onrender.com"
    }
]

SAMPLE_ERROS = []
SAMPLE_ACESSOS = []


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
                estagio_deploy=app_data.get("estagio_deploy", "DESENVOLVIMENTO"),
                cliente_piloto=app_data.get("cliente_piloto"),
                versao=app_data.get("versao", "1.0.0"),
                descricao=app_data["descricao"],
                url_acesso=app_data.get("url_acesso"),
                ultimo_ping=agora
            )
            db.add(app)
        db.commit()

