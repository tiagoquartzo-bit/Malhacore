from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.telemetria_schema import (
    AppCreate, AppResponse, LogAcessoCreate, LogAcessoResponse,
    RegistroErroCreate, RegistroErroResponse, ErroUpdateStatus, ResumoTelemetria
)
from services import telemetria_service

router = APIRouter(prefix="/api/telemetria", tags=["Telemetria & Observabilidade"])


@router.get("/resumo", response_model=ResumoTelemetria)
def obter_resumo(db: Session = Depends(get_db)):
    return telemetria_service.obter_resumo_telemetria(db)


@router.get("/apps", response_model=List[AppResponse])
def listar_aplicativos(db: Session = Depends(get_db)):
    return telemetria_service.listar_apps(db)


@router.post("/apps", response_model=AppResponse, status_code=201)
def cadastrar_aplicativo(dados: AppCreate, db: Session = Depends(get_db)):
    app = telemetria_service.obter_ou_criar_app(db, slug=dados.slug, nome=dados.nome)
    app.categoria = dados.categoria or app.categoria
    app.ambiente = dados.ambiente or app.ambiente
    app.descricao = dados.descricao or app.descricao
    db.commit()
    db.refresh(app)
    return app


@router.post("/acesso", response_model=LogAcessoResponse, status_code=201)
def registrar_log_acesso(dados: LogAcessoCreate, db: Session = Depends(get_db)):
    """Endpoint simplificado para qualquer aplicativo reportar um acesso/requisição."""
    return telemetria_service.registrar_acesso(db, dados)


@router.post("/erro", response_model=RegistroErroResponse, status_code=201)
def reportar_erro_ou_bug(dados: RegistroErroCreate, db: Session = Depends(get_db)):
    """Endpoint simplificado para qualquer aplicativo reportar exceções, bugs ou anomalias."""
    return telemetria_service.registrar_erro(db, dados)


@router.post("/ping/{app_slug}")
def heartbeat_app(app_slug: str, db: Session = Depends(get_db)):
    """Ping simples de liveness para indicar que o app está ativo."""
    app = telemetria_service.obter_ou_criar_app(db, slug=app_slug)
    return {"status": "ok", "app": app.nome, "ultimo_ping": app.ultimo_ping}


@router.post("/apps/{app_slug}/healthcheck")
def checar_saude_online(app_slug: str, db: Session = Depends(get_db)):
    """Verifica ativamente se a URL pública do app está online."""
    return telemetria_service.executar_healthcheck_url(db, slug=app_slug)


@router.get("/erros", response_model=List[RegistroErroResponse])
def listar_todos_erros(
    app_slug: Optional[str] = Query(None, description="Filtrar por app"),
    status: Optional[str] = Query(None, description="Filtrar por status: NOVO, EM_ANALISE, RESOLVIDO"),
    nivel: Optional[str] = Query(None, description="Filtrar por nível: CRITICAL, ERROR, WARNING"),
    busca: Optional[str] = Query(None, description="Busca textual livre"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return telemetria_service.listar_erros(
        db, app_slug=app_slug, status=status, nivel=nivel, busca=busca, limit=limit
    )


@router.get("/erros/{erro_id}", response_model=RegistroErroResponse)
def obter_detalhes_erro(erro_id: int, db: Session = Depends(get_db)):
    erro = telemetria_service.obter_erro_por_id(db, erro_id)
    if not erro:
        raise HTTPException(status_code=404, detail="Registro de erro não encontrado.")
    return erro


@router.patch("/erros/{erro_id}/status", response_model=RegistroErroResponse)
def alterar_status_erro(erro_id: int, dados: ErroUpdateStatus, db: Session = Depends(get_db)):
    erro = telemetria_service.atualizar_status_erro(db, erro_id, dados)
    if not erro:
        raise HTTPException(status_code=404, detail="Registro de erro não encontrado.")
    return erro


@router.get("/acessos", response_model=List[LogAcessoResponse])
def listar_historico_acessos(
    app_slug: Optional[str] = Query(None, description="Filtrar por app"),
    status_code: Optional[int] = Query(None, description="Filtrar por código HTTP (ex: 500, 404, 200)"),
    busca: Optional[str] = Query(None, description="Busca textual (usuário, rota, IP)"),
    limit: int = Query(150, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return telemetria_service.listar_acessos(
        db, app_slug=app_slug, status_code=status_code, busca=busca, limit=limit
    )

