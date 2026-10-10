from datetime import datetime, timezone
import io
import csv
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from database.models import Lead, AuditoriaTransacao
from schemas.lead_schema import LeadCreate, LeadUpdateStatus, LeadUpdate, ResumoFinanceiro


def recalcular_atrasos(db: Session):
    hoje = datetime.now().date()
    leads = db.query(Lead).filter(Lead.status_pagamento != "PAGO").all()
    alterados = False
    for lead in leads:
        if lead.vencimento:
            try:
                data_venc = datetime.strptime(lead.vencimento, "%Y-%m-%d").date()
                if hoje > data_venc:
                    dias = (hoje - data_venc).days
                    if lead.dias_atraso != dias:
                        lead.dias_atraso = dias
                        alterados = True
                    if lead.status_pagamento == "PENDENTE":
                        lead.status_pagamento = "INADIMPLENTE"
                        alterados = True
                        auditoria = AuditoriaTransacao(
                            lead_id=lead.id,
                            codigo_lead=lead.codigo,
                            tipo_evento="INADIMPLENCIA_DETECTADA",
                            status_anterior="PENDENTE",
                            status_novo="INADIMPLENTE",
                            valor=lead.valor_mensal,
                            responsavel="Telemetria Automática",
                            detalhes=f"Vencimento expirado em {lead.vencimento} (+{dias}d de atraso)"
                        )
                        db.add(auditoria)
                else:
                    if lead.dias_atraso != 0:
                        lead.dias_atraso = 0
                        alterados = True
            except ValueError:
                pass
    if alterados:
        db.commit()


def gerar_novo_codigo(db: Session) -> str:
    ultimo = db.query(Lead).order_by(desc(Lead.id)).first()
    proximo_num = (ultimo.id + 101) if ultimo else 101
    ano_atual = datetime.now().year
    return f"MC-{ano_atual}-{proximo_num:04d}"


def obter_resumo_financeiro(db: Session) -> ResumoFinanceiro:
    recalcular_atrasos(db)
    leads = db.query(Lead).all()
    
    total = len(leads)
    pagos = [l for l in leads if l.status_pagamento == "PAGO"]
    pendentes = [l for l in leads if l.status_pagamento == "PENDENTE"]
    inadimplentes = [l for l in leads if l.status_pagamento == "INADIMPLENTE"]
    
    valor_liquidado = sum(l.valor_mensal for l in pagos)
    valor_pendente = sum(l.valor_mensal for l in pendentes)
    valor_inadimplente = sum(l.valor_mensal for l in inadimplentes)
    
    taxa_adimplencia = (len(pagos) / total * 100) if total > 0 else 0.0
    
    return ResumoFinanceiro(
        total_leads=total,
        total_pagos=len(pagos),
        total_pendentes=len(pendentes),
        total_inadimplentes=len(inadimplentes),
        faturamento_liquidado=round(valor_liquidado, 2),
        faturamento_a_receber=round(valor_pendente, 2),
        faturamento_em_atraso=round(valor_inadimplente, 2),
        taxa_adimplencia=round(taxa_adimplencia, 1)
    )


def listar_leads(
    db: Session,
    busca: Optional[str] = None,
    status: Optional[str] = None,
    origem: Optional[str] = None
) -> List[Lead]:
    recalcular_atrasos(db)
    query = db.query(Lead)
    
    if status and status.upper() != "TODOS":
        query = query.filter(Lead.status_pagamento == status.upper())
        
    if origem and origem.strip():
        query = query.filter(Lead.origem == origem)
        
    if busca and busca.strip():
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Lead.razao_social.ilike(termo),
                Lead.nome_fantasia.ilike(termo),
                Lead.documento.ilike(termo),
                Lead.codigo.ilike(termo),
                Lead.contato_nome.ilike(termo),
                Lead.email.ilike(termo),
                Lead.telefone.ilike(termo)
            )
        )
        
    return query.order_by(desc(Lead.id)).all()


def obter_lead_por_id(db: Session, lead_id: int) -> Optional[Lead]:
    return db.query(Lead).filter(Lead.id == lead_id).first()


def criar_novo_lead(db: Session, dados: LeadCreate) -> Lead:
    codigo = gerar_novo_codigo(db)
    
    data_pagamento = None
    if dados.status_pagamento == "PAGO":
        data_pagamento = datetime.now().strftime("%Y-%m-%d %H:%M")
        
    lead = Lead(
        codigo=codigo,
        razao_social=dados.razao_social,
        nome_fantasia=dados.nome_fantasia or dados.razao_social,
        documento=dados.documento,
        contato_nome=dados.contato_nome,
        contato_cargo=dados.contato_cargo or "Diretoria / Operações",
        email=dados.email,
        telefone=dados.telefone,
        origem=dados.origem or "App MalhaCore",
        plano=dados.plano or "Malha Enterprise",
        valor_mensal=dados.valor_mensal,
        status_pagamento=dados.status_pagamento or "PENDENTE",
        metodo_pagamento=dados.metodo_pagamento or "PIX",
        vencimento=dados.vencimento,
        data_pagamento=data_pagamento,
        dias_atraso=0,
        nfe_emitida=False,
        observacoes=dados.observacoes
    )
    
    db.add(lead)
    db.flush()
    
    auditoria = AuditoriaTransacao(
        lead_id=lead.id,
        codigo_lead=lead.codigo,
        tipo_evento="CADASTRO_LEAD",
        status_anterior=None,
        status_novo=lead.status_pagamento,
        valor=lead.valor_mensal,
        responsavel="Controladoria MalhaCore",
        detalhes=f"Novo lead registrado no sistema via {lead.origem}"
    )
    db.add(auditoria)
    db.commit()
    db.refresh(lead)
    return lead


def atualizar_status_lead(
    db: Session,
    lead_id: int,
    dados: LeadUpdateStatus
) -> Optional[Lead]:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None
        
    status_antigo = lead.status_pagamento
    novo_status = dados.status_pagamento.upper()
    
    lead.status_pagamento = novo_status
    if dados.metodo_pagamento:
        lead.metodo_pagamento = dados.metodo_pagamento.upper()
        
    if novo_status == "PAGO":
        lead.data_pagamento = datetime.now().strftime("%Y-%m-%d %H:%M")
        lead.dias_atraso = 0
    elif novo_status in ["PENDENTE", "INADIMPLENTE"]:
        lead.data_pagamento = None
        
    auditoria = AuditoriaTransacao(
        lead_id=lead.id,
        codigo_lead=lead.codigo,
        tipo_evento="ALTERACAO_STATUS_FINANCEIRO",
        status_anterior=status_antigo,
        status_novo=novo_status,
        valor=lead.valor_mensal,
        responsavel="Painel Gerencial",
        detalhes=dados.motivo_baixa or f"Status atualizado de {status_antigo} para {novo_status}"
    )
    db.add(auditoria)
    db.commit()
    db.refresh(lead)
    return lead


def gerar_csv_exportacao(db: Session) -> str:
    leads = db.query(Lead).order_by(desc(Lead.id)).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    
    writer.writerow([
        "CODIGO",
        "RAZAO_SOCIAL",
        "CNPJ_CPF",
        "CONTATO",
        "TELEFONE",
        "EMAIL",
        "ORIGEM",
        "PLANO",
        "VALOR_MENSAL_BRL",
        "STATUS_PAGAMENTO",
        "METODO",
        "VENCIMENTO",
        "DATA_PAGAMENTO",
        "DIAS_ATRASO"
    ])
    
    for l in leads:
        writer.writerow([
            l.codigo,
            l.razao_social,
            l.documento,
            l.contato_nome,
            l.telefone,
            l.email,
            l.origem,
            l.plano,
            f"{l.valor_mensal:.2f}",
            l.status_pagamento,
            l.metodo_pagamento,
            l.vencimento or "-",
            l.data_pagamento or "-",
            l.dias_atraso
        ])
        
    return output.getvalue()


def obter_auditoria_lead(db: Session, lead_id: int) -> List[AuditoriaTransacao]:
    return db.query(AuditoriaTransacao).filter(
        AuditoriaTransacao.lead_id == lead_id
    ).order_by(desc(AuditoriaTransacao.id)).all()


def atualizar_dados_lead(
    db: Session,
    lead_id: int,
    dados: LeadUpdate
) -> Optional[Lead]:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return None
        
    status_antigo = lead.status_pagamento
    mudancas = []
    
    campos = [
        "razao_social", "nome_fantasia", "documento",
        "contato_nome", "contato_cargo", "email", "telefone",
        "origem", "plano", "valor_mensal", "metodo_pagamento",
        "vencimento", "observacoes"
    ]
    
    for campo in campos:
        novo_val = getattr(dados, campo, None)
        if novo_val is not None:
            velho_val = getattr(lead, campo)
            if velho_val != novo_val:
                mudancas.append(f"{campo}: '{velho_val}' -> '{novo_val}'")
                setattr(lead, campo, novo_val)
                
    if dados.status_pagamento and dados.status_pagamento.upper() != status_antigo:
        novo_st = dados.status_pagamento.upper()
        mudancas.append(f"status: '{status_antigo}' -> '{novo_st}'")
        lead.status_pagamento = novo_st
        if novo_st == "PAGO":
            lead.data_pagamento = datetime.now().strftime("%Y-%m-%d %H:%M")
            lead.dias_atraso = 0
        elif novo_st in ["PENDENTE", "INADIMPLENTE"]:
            lead.data_pagamento = None
            
    if mudancas:
        auditoria = AuditoriaTransacao(
            lead_id=lead.id,
            codigo_lead=lead.codigo,
            tipo_evento="EDICAO_CADASTRO",
            status_anterior=status_antigo,
            status_novo=lead.status_pagamento,
            valor=lead.valor_mensal,
            responsavel="Painel Gerencial",
            detalhes=(dados.motivo_alteracao or "Edição cadastral") + " | " + "; ".join(mudancas[:5])
        )
        db.add(auditoria)
        db.commit()
        db.refresh(lead)
        
    return lead


def excluir_lead(db: Session, lead_id: int) -> bool:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return False
        
    auditoria = AuditoriaTransacao(
        lead_id=lead.id,
        codigo_lead=lead.codigo,
        tipo_evento="EXCLUSAO_LEAD",
        status_anterior=lead.status_pagamento,
        status_novo="EXCLUIDO",
        valor=lead.valor_mensal,
        responsavel="Painel Gerencial",
        detalhes=f"Lead {lead.razao_social} ({lead.codigo}) removido do sistema."
    )
    db.add(auditoria)
    db.delete(lead)
    db.commit()
    return True

