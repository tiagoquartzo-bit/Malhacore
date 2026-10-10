from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.lead_schema import (
    LeadCreate, LeadUpdateStatus, LeadUpdate, LeadResponse,
    AuditoriaResponse, ResumoFinanceiro
)
from services import lead_service

router = APIRouter(prefix="/api", tags=["Leads & Financeiro"])


@router.get("/leads", response_model=List[LeadResponse])
def listar_todos_leads(
    busca: Optional[str] = Query(None, description="Busca por termo (Razão, CNPJ, Contato, etc)"),
    status: Optional[str] = Query(None, description="Filtro de status (PAGO, PENDENTE, INADIMPLENTE)"),
    origem: Optional[str] = Query(None, description="Filtro de origem"),
    db: Session = Depends(get_db)
):
    return lead_service.listar_leads(db=db, busca=busca, status=status, origem=origem)


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def obter_detalhes_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = lead_service.obter_lead_por_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não localizado no sistema.")
    return lead


@router.post("/leads", response_model=LeadResponse, status_code=201)
def cadastrar_lead(dados: LeadCreate, db: Session = Depends(get_db)):
    return lead_service.criar_novo_lead(db=db, dados=dados)


@router.patch("/leads/{lead_id}/status", response_model=LeadResponse)
def alterar_status_pagamento(
    lead_id: int,
    dados: LeadUpdateStatus,
    db: Session = Depends(get_db)
):
    lead = lead_service.atualizar_status_lead(db=db, lead_id=lead_id, dados=dados)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não localizado.")
    return lead


@router.get("/financeiro/resumo", response_model=ResumoFinanceiro)
def obter_metricas_financeiras(db: Session = Depends(get_db)):
    return lead_service.obter_resumo_financeiro(db=db)


@router.get("/leads/{lead_id}/auditoria", response_model=List[AuditoriaResponse])
def obter_historico_auditoria(lead_id: int, db: Session = Depends(get_db)):
    lead = lead_service.obter_lead_por_id(db=db, lead_id=lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não localizado.")
    return lead_service.obter_auditoria_lead(db=db, lead_id=lead_id)


@router.put("/leads/{lead_id}", response_model=LeadResponse)
def atualizar_lead_completo(lead_id: int, dados: LeadUpdate, db: Session = Depends(get_db)):
    lead = lead_service.atualizar_dados_lead(db=db, lead_id=lead_id, dados=dados)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não localizado.")
    return lead


@router.delete("/leads/{lead_id}")
def remover_lead(lead_id: int, db: Session = Depends(get_db)):
    sucesso = lead_service.excluir_lead(db=db, lead_id=lead_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Lead não localizado para exclusão.")
    return {"status": "sucesso", "mensagem": "Lead removido com registro em auditoria."}


@router.get("/leads/exportar/csv")
def exportar_csv(db: Session = Depends(get_db)):
    conteudo_csv = lead_service.gerar_csv_exportacao(db=db)
    return Response(
        content=conteudo_csv,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=malhacore_leads_ledger.csv"}
    )
