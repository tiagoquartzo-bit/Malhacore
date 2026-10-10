from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from database.connection import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(32), unique=True, index=True, nullable=False)
    
    # Dados Corporativos
    razao_social = Column(String(255), nullable=False, index=True)
    nome_fantasia = Column(String(255), nullable=True)
    documento = Column(String(32), index=True, nullable=False)  # CNPJ ou CPF
    
    # Contato Principal
    contato_nome = Column(String(128), nullable=False)
    contato_cargo = Column(String(128), default="Operações / Finanças")
    email = Column(String(128), index=True, nullable=False)
    telefone = Column(String(32), nullable=False)
    
    # Origem & Contrato
    origem = Column(String(64), default="App MalhaCore")
    plano = Column(String(64), default="Malha Enterprise")
    valor_mensal = Column(Float, nullable=False, default=0.0)
    
    # Status Financeiro e Liquidação
    # Status: PAGO, PENDENTE, INADIMPLENTE, CANCELADO
    status_pagamento = Column(String(32), default="PENDENTE", index=True)
    metodo_pagamento = Column(String(32), default="PIX")  # PIX, BOLETO, CARTAO, TED
    vencimento = Column(String(32), nullable=True)  # YYYY-MM-DD
    data_pagamento = Column(String(32), nullable=True)  # YYYY-MM-DD HH:MM
    dias_atraso = Column(Integer, default=0)
    nfe_emitida = Column(Boolean, default=False)
    
    # Auditoria & Notas Internas
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AuditoriaTransacao(Base):
    __tablename__ = "auditorias_transacoes"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, index=True, nullable=False)
    codigo_lead = Column(String(32), nullable=False)
    tipo_evento = Column(String(64), nullable=False)  # BAIXA_MANUAL, COBRANCA_GERADA, PIX_LIQUIDADO, CONTRATO_ATIVADO
    status_anterior = Column(String(32), nullable=True)
    status_novo = Column(String(32), nullable=False)
    valor = Column(Float, default=0.0)
    responsavel = Column(String(64), default="Controladoria MalhaCore")
    detalhes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Aplicativo(Base):
    __tablename__ = "aplicativos"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True, nullable=False)
    nome = Column(String(128), nullable=False)
    categoria = Column(String(64), default="Corporativo")
    ambiente = Column(String(32), default="producao")
    api_key = Column(String(64), nullable=True)
    status = Column(String(32), default="OPERACIONAL", index=True)  # OPERACIONAL, ALERTA, CRITICO, INATIVO
    estagio_deploy = Column(String(32), default="DESENVOLVIMENTO", index=True)  # PUBLICADO, ROLLOUT, DESENVOLVIMENTO
    cliente_piloto = Column(String(128), nullable=True)  # Ex: Activia, Dra. Shirlei
    versao = Column(String(32), default="1.0.0")
    descricao = Column(String(255), nullable=True)
    url_acesso = Column(String(255), nullable=True)
    ultimo_ping = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))



class LogAcesso(Base):
    __tablename__ = "logs_acessos"

    id = Column(Integer, primary_key=True, index=True)
    app_slug = Column(String(64), index=True, nullable=False)
    app_nome = Column(String(128), nullable=True)
    usuario = Column(String(128), nullable=True, index=True)
    cliente_identificador = Column(String(128), nullable=True, index=True)  # Razão Social ou CNPJ
    rota = Column(String(255), nullable=False)
    metodo = Column(String(16), default="GET")
    status_code = Column(Integer, default=200, index=True)
    tempo_resposta_ms = Column(Float, default=0.0)
    ip_origem = Column(String(64), nullable=True)
    detalhes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class RegistroErro(Base):
    __tablename__ = "registros_erros"

    id = Column(Integer, primary_key=True, index=True)
    app_slug = Column(String(64), index=True, nullable=False)
    app_nome = Column(String(128), nullable=True)
    nivel = Column(String(32), default="ERROR", index=True)  # CRITICAL, ERROR, WARNING
    tipo_erro = Column(String(128), nullable=False, index=True)  # Ex: ZeroDivisionError, ConnectionTimeout
    mensagem = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    rota_ou_funcao = Column(String(255), nullable=True)
    cliente_afetado = Column(String(128), nullable=True, index=True)
    usuario_afetado = Column(String(128), nullable=True)
    ambiente = Column(String(32), default="producao")
    status = Column(String(32), default="NOVO", index=True)  # NOVO, EM_ANALISE, RESOLVIDO
    recorrencias = Column(Integer, default=1)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    atualizado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolvido_em = Column(DateTime, nullable=True)
    solucao_nota = Column(Text, nullable=True)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(128), unique=True, index=True, nullable=False)
    nome = Column(String(128), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    cargo = Column(String(64), default="Administrador Master")
    ativo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))


