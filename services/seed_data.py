from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database.models import Lead, AuditoriaTransacao, Aplicativo, LogAcesso, RegistroErro



SAMPLE_LEADS = [
    {
        "codigo": "MC-2026-0101",
        "razao_social": "TransLogística Brasil S/A",
        "nome_fantasia": "TransLog Brasil",
        "documento": "14.289.412/0001-89",
        "contato_nome": "Carlos Eduardo Silveira",
        "contato_cargo": "Diretor de Operações",
        "email": "carlos.silveira@translogbrasil.com.br",
        "telefone": "(11) 98712-4091",
        "origem": "App MalhaCore",
        "plano": "Malha Enterprise Fleet",
        "valor_mensal": 7900.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-05",
        "data_pagamento": "2026-10-05 11:24",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Contrato anual faturado. PIX com liquidação instantânea.",
    },
    {
        "codigo": "MC-2026-0102",
        "razao_social": "Atlas Distribuição e Cargas Ltda",
        "nome_fantasia": "Atlas Cargas",
        "documento": "08.761.942/0001-30",
        "contato_nome": "Renata Vasconcellos",
        "contato_cargo": "Gerente de Controladoria",
        "email": "renata.v@atlascargas.com.br",
        "telefone": "(19) 99182-3341",
        "origem": "Inbound Enterprise",
        "plano": "Malha Enterprise Fleet",
        "valor_mensal": 6100.00,
        "status_pagamento": "PENDENTE",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-14",
        "data_pagamento": None,
        "dias_atraso": 0,
        "nfe_emitida": False,
        "observacoes": "Fatura enviada para o departamento financeiro. Aguardando compensação.",
    },
    {
        "codigo": "MC-2026-0103",
        "razao_social": "NorteLog Operadora Multimodal S.A.",
        "nome_fantasia": "NorteLog",
        "documento": "23.419.002/0001-55",
        "contato_nome": "Fernando Bastos",
        "contato_cargo": "Head de Suprimentos",
        "email": "fbastos@nortelog.com.br",
        "telefone": "(91) 98451-2290",
        "origem": "App MalhaCore",
        "plano": "Core Pro Hub",
        "valor_mensal": 5400.00,
        "status_pagamento": "INADIMPLENTE",
        "metodo_pagamento": "BOLETO",
        "vencimento": "2026-10-02",
        "data_pagamento": None,
        "dias_atraso": 8,
        "nfe_emitida": True,
        "observacoes": "Atraso de 8 dias. Primeiro contato de cobrança realizado via WhatsApp.",
    },
    {
        "codigo": "MC-2026-0104",
        "razao_social": "Delta Cargas & Fretes Inteligentes Ltda",
        "nome_fantasia": "Delta Freight",
        "documento": "31.902.584/0001-12",
        "contato_nome": "Guilherme Sampaio",
        "contato_cargo": "Chief Logistics Officer",
        "email": "guilherme@deltafreight.com.br",
        "telefone": "(41) 99760-1123",
        "origem": "Checkout Direto",
        "plano": "Malha Enterprise Ultra",
        "valor_mensal": 9800.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "TED",
        "vencimento": "2026-10-08",
        "data_pagamento": "2026-10-08 09:12",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Comprovante TED conciliado pelo banco.",
    },
    {
        "codigo": "MC-2026-0105",
        "razao_social": "Expresso Rápido Paulista Eireli",
        "nome_fantasia": "Expresso Paulista",
        "documento": "04.551.290/0001-77",
        "contato_nome": "Mariana Toledo",
        "contato_cargo": "Supervisora Financeira",
        "email": "mariana.toledo@expaulista.com.br",
        "telefone": "(11) 97109-8832",
        "origem": "App MalhaCore",
        "plano": "Core Standard Fleet",
        "valor_mensal": 4250.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "BOLETO",
        "vencimento": "2026-10-07",
        "data_pagamento": "2026-10-07 14:48",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Boleto liquidado na data do vencimento.",
    },
    {
        "codigo": "MC-2026-0106",
        "razao_social": "Minas RodoTransportes Ltda",
        "nome_fantasia": "RodoMinas",
        "documento": "19.332.810/0001-99",
        "contato_nome": "Alexandre Morais",
        "contato_cargo": "Diretor Financeiro",
        "email": "alexandre@rodominas.com.br",
        "telefone": "(31) 98845-6671",
        "origem": "Indicação Comercial",
        "plano": "Core Starter",
        "valor_mensal": 2950.00,
        "status_pagamento": "INADIMPLENTE",
        "metodo_pagamento": "BOLETO",
        "vencimento": "2026-09-26",
        "data_pagamento": None,
        "dias_atraso": 14,
        "nfe_emitida": True,
        "observacoes": "Promessa de regularização feita pelo financeiro para próxima sexta-feira.",
    },
    {
        "codigo": "MC-2026-0107",
        "razao_social": "Centro-Oeste Grãos & Transportes S.A.",
        "nome_fantasia": "COG Transportes",
        "documento": "10.890.311/0001-44",
        "contato_nome": "Luciano Valente",
        "contato_cargo": "VP de Operações Rodoviárias",
        "email": "lvalente@cogtransportes.com.br",
        "telefone": "(65) 99612-9900",
        "origem": "Inbound Enterprise",
        "plano": "Malha Enterprise Ultra",
        "valor_mensal": 12500.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "TED",
        "vencimento": "2026-10-01",
        "data_pagamento": "2026-10-01 16:03",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Cliente corporativo enterprise com integração de API ativa.",
    },
    {
        "codigo": "MC-2026-0108",
        "razao_social": "Rodoviário Porto Seguro Cargo Ltda",
        "nome_fantasia": "Porto Cargo",
        "documento": "18.112.980/0001-63",
        "contato_nome": "Camila Figueira",
        "contato_cargo": "Gerente de Frota",
        "email": "camila.f@portocargo.com.br",
        "telefone": "(13) 99120-7711",
        "origem": "App MalhaCore",
        "plano": "Malha Enterprise Fleet",
        "valor_mensal": 8200.00,
        "status_pagamento": "PENDENTE",
        "metodo_pagamento": "PIX",
        "vencimento": "2026-10-12",
        "data_pagamento": None,
        "dias_atraso": 0,
        "nfe_emitida": False,
        "observacoes": "Chave PIX enviada para conferência interna.",
    },
    {
        "codigo": "MC-2026-0109",
        "razao_social": "EcoFrotas Logística Urbana Sustentável",
        "nome_fantasia": "EcoFrotas",
        "documento": "28.771.602/0001-08",
        "contato_nome": "Felipe Aragão",
        "contato_cargo": "Fundador & COO",
        "email": "aragao@ecofrotas.log.br",
        "telefone": "(21) 98114-5502",
        "origem": "App MalhaCore",
        "plano": "Core Standard Fleet",
        "valor_mensal": 3500.00,
        "status_pagamento": "PAGO",
        "metodo_pagamento": "CARTAO",
        "vencimento": "2026-10-04",
        "data_pagamento": "2026-10-04 03:10",
        "dias_atraso": 0,
        "nfe_emitida": True,
        "observacoes": "Cobrança recorrente em cartão de crédito corporativo.",
    },
    {
        "codigo": "MC-2026-0110",
        "razao_social": "Amazonas Cabotagem e Logística Integrada",
        "nome_fantasia": "Amazonas Log",
        "documento": "07.210.490/0001-21",
        "contato_nome": "Larissa Medeiros",
        "contato_cargo": "Controladora Regional",
        "email": "larissa.m@amazonaslog.com.br",
        "telefone": "(92) 99318-4421",
        "origem": "Checkout Direto",
        "plano": "Core Pro Hub",
        "valor_mensal": 4600.00,
        "status_pagamento": "PENDENTE",
        "metodo_pagamento": "BOLETO",
        "vencimento": "2026-10-15",
        "data_pagamento": None,
        "dias_atraso": 0,
        "nfe_emitida": False,
        "observacoes": "Boleto registrado no DDA bancário.",
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

