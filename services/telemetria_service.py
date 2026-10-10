from datetime import datetime, timezone, timedelta
import secrets
import urllib.request
import time
from typing import Optional, List
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from database.models import Aplicativo, LogAcesso, RegistroErro
from schemas.telemetria_schema import (
    AppCreate, LogAcessoCreate, RegistroErroCreate,
    ErroUpdateStatus, ResumoTelemetria
)


def obter_ou_criar_app(db: Session, slug: str, nome: Optional[str] = None) -> Aplicativo:
    slug_limpo = slug.strip().lower()
    app = db.query(Aplicativo).filter(Aplicativo.slug == slug_limpo).first()
    
    if not app:
        nome_final = nome or slug.replace("-", " ").replace(".", " ").title()
        api_key = f"mc_live_{secrets.token_hex(16)}"
        app = Aplicativo(
            slug=slug_limpo,
            nome=nome_final,
            categoria="Ecossistema Python",
            ambiente="producao",
            api_key=api_key,
            status="OPERACIONAL",
            descricao=f"Aplicativo integrado automaticamente via telemetria MalhaCore",
            ultimo_ping=datetime.now(timezone.utc)
        )
        db.add(app)
        db.commit()
        db.refresh(app)
    else:
        app.ultimo_ping = datetime.now(timezone.utc)
        db.commit()
        
    return app


def atualizar_saude_app(db: Session, app_slug: str):
    app = db.query(Aplicativo).filter(Aplicativo.slug == app_slug).first()
    if not app:
        return
        
    erros_criticos = db.query(RegistroErro).filter(
        RegistroErro.app_slug == app_slug,
        RegistroErro.status != "RESOLVIDO",
        RegistroErro.nivel == "CRITICAL"
    ).count()
    
    erros_ativos = db.query(RegistroErro).filter(
        RegistroErro.app_slug == app_slug,
        RegistroErro.status != "RESOLVIDO"
    ).count()
    
    if erros_criticos > 0:
        app.status = "CRITICO"
    elif erros_ativos > 0:
        app.status = "ALERTA"
    else:
        app.status = "OPERACIONAL"
        
    db.commit()


def registrar_acesso(db: Session, dados: LogAcessoCreate) -> LogAcesso:
    app = obter_ou_criar_app(db, slug=dados.app_slug, nome=dados.app_nome)
    
    log = LogAcesso(
        app_slug=app.slug,
        app_nome=dados.app_nome or app.nome,
        usuario=dados.usuario or "Operador / Anônimo",
        cliente_identificador=dados.cliente_identificador,
        rota=dados.rota,
        metodo=(dados.metodo or "GET").upper(),
        status_code=dados.status_code or 200,
        tempo_resposta_ms=round(float(dados.tempo_resposta_ms or 0.0), 2),
        ip_origem=dados.ip_origem or "127.0.0.1",
        detalhes=dados.detalhes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def registrar_erro(db: Session, dados: RegistroErroCreate) -> RegistroErro:
    app = obter_ou_criar_app(db, slug=dados.app_slug, nome=dados.app_nome)
    
    nivel_normalizado = (dados.nivel or "ERROR").upper()
    if nivel_normalizado not in ["CRITICAL", "ERROR", "WARNING"]:
        nivel_normalizado = "ERROR"
        
    # Verificar se o mesmo erro já existe não resolvido para agrupar recorrências
    erro_existente = db.query(RegistroErro).filter(
        RegistroErro.app_slug == app.slug,
        RegistroErro.tipo_erro == dados.tipo_erro,
        RegistroErro.rota_ou_funcao == dados.rota_ou_funcao,
        RegistroErro.status.in_(["NOVO", "EM_ANALISE"])
    ).first()
    
    if erro_existente:
        erro_existente.recorrencias += 1
        erro_existente.mensagem = dados.mensagem
        if dados.traceback:
            erro_existente.traceback = dados.traceback
        if dados.cliente_afetado:
            erro_existente.cliente_afetado = dados.cliente_afetado
        if dados.usuario_afetado:
            erro_existente.usuario_afetado = dados.usuario_afetado
        erro_existente.atualizado_em = datetime.now(timezone.utc)
        db.commit()
        db.refresh(erro_existente)
        atualizar_saude_app(db, app.slug)
        return erro_existente
        
    novo_erro = RegistroErro(
        app_slug=app.slug,
        app_nome=dados.app_nome or app.nome,
        nivel=nivel_normalizado,
        tipo_erro=dados.tipo_erro,
        mensagem=dados.mensagem,
        traceback=dados.traceback,
        rota_ou_funcao=dados.rota_ou_funcao,
        cliente_afetado=dados.cliente_afetado,
        usuario_afetado=dados.usuario_afetado,
        ambiente=dados.ambiente or "producao",
        status="NOVO",
        recorrencias=1
    )
    db.add(novo_erro)
    db.commit()
    db.refresh(novo_erro)
    
    atualizar_saude_app(db, app.slug)
    return novo_erro


def atualizar_status_erro(db: Session, erro_id: int, dados: ErroUpdateStatus) -> Optional[RegistroErro]:
    erro = db.query(RegistroErro).filter(RegistroErro.id == erro_id).first()
    if not erro:
        return None
        
    status_novo = dados.status.upper()
    erro.status = status_novo
    erro.solucao_nota = dados.solucao_nota
    
    if status_novo == "RESOLVIDO":
        erro.resolvido_em = datetime.now(timezone.utc)
    else:
        erro.resolvido_em = None
        
    erro.atualizado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(erro)
    
    atualizar_saude_app(db, erro.app_slug)
    return erro


def listar_apps(db: Session) -> List[dict]:
    apps = db.query(Aplicativo).order_by(Aplicativo.nome).all()
    resultado = []
    
    for a in apps:
        erros_ativos = db.query(RegistroErro).filter(
            RegistroErro.app_slug == a.slug,
            RegistroErro.status != "RESOLVIDO"
        ).count()
        
        total_acessos = db.query(LogAcesso).filter(
            LogAcesso.app_slug == a.slug
        ).count()
        
        resultado.append({
            "id": a.id,
            "slug": a.slug,
            "nome": a.nome,
            "categoria": a.categoria,
            "ambiente": a.ambiente,
            "api_key": a.api_key,
            "status": a.status,
            "estagio_deploy": getattr(a, "estagio_deploy", "DESENVOLVIMENTO") or "DESENVOLVIMENTO",
            "cliente_piloto": getattr(a, "cliente_piloto", None),
            "versao": getattr(a, "versao", "1.0.0") or "1.0.0",
            "descricao": a.descricao,
            "url_acesso": a.url_acesso,
            "ultimo_ping": a.ultimo_ping,
            "criado_em": a.criado_em,
            "total_erros_ativos": erros_ativos,
            "total_acessos": total_acessos
        })
        
    return resultado


def executar_healthcheck_url(db: Session, slug: str) -> dict:
    app = db.query(Aplicativo).filter(Aplicativo.slug == slug.strip().lower()).first()
    if not app:
        return {"status": "erro", "mensagem": "Aplicativo não encontrado."}
        
    if not app.url_acesso:
        return {"status": "aviso", "mensagem": "Nenhuma URL configurada para este aplicativo."}
        
    inicio = time.time()
    try:
        req = urllib.request.Request(
            app.url_acesso,
            headers={"User-Agent": "MalhaCore-Telemetry-Agent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            duracao_ms = round((time.time() - inicio) * 1000.0, 1)
            codigo = resp.status
            app.status = "OPERACIONAL"
            app.ultimo_ping = datetime.now(timezone.utc)
            db.commit()
            
            # Registrar log de acesso do ping
            log = LogAcesso(
                app_slug=app.slug,
                app_nome=app.nome,
                usuario="Healthcheck MalhaCore",
                cliente_identificador="Monitor Central",
                rota=app.url_acesso,
                metodo="GET",
                status_code=codigo,
                tempo_resposta_ms=duracao_ms,
                ip_origem="127.0.0.1",
                detalhes=f"Verificação ativa online (HTTP {codigo})"
            )
            db.add(log)
            db.commit()
            
            return {
                "status": "sucesso",
                "http_status": codigo,
                "latencia_ms": duracao_ms,
                "app_status": app.status,
                "mensagem": f"App online respondendo em {duracao_ms}ms (HTTP {codigo})"
            }
    except Exception as exc:
        duracao_ms = round((time.time() - inicio) * 1000.0, 1)
        app.status = "ALERTA"
        db.commit()
        return {
            "status": "falha",
            "latencia_ms": duracao_ms,
            "app_status": app.status,
            "mensagem": f"Falha na verificação da URL: {str(exc)}"
        }



def listar_erros(
    db: Session,
    app_slug: Optional[str] = None,
    status: Optional[str] = None,
    nivel: Optional[str] = None,
    busca: Optional[str] = None,
    limit: int = 100
) -> List[RegistroErro]:
    query = db.query(RegistroErro)
    
    if app_slug and app_slug.strip() and app_slug.upper() != "TODOS":
        query = query.filter(RegistroErro.app_slug == app_slug.strip().lower())
        
    if status and status.strip() and status.upper() != "TODOS":
        query = query.filter(RegistroErro.status == status.strip().upper())
        
    if nivel and nivel.strip() and nivel.upper() != "TODOS":
        query = query.filter(RegistroErro.nivel == nivel.strip().upper())
        
    if busca and busca.strip():
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                RegistroErro.tipo_erro.ilike(termo),
                RegistroErro.mensagem.ilike(termo),
                RegistroErro.rota_ou_funcao.ilike(termo),
                RegistroErro.cliente_afetado.ilike(termo),
                RegistroErro.app_nome.ilike(termo)
            )
        )
        
    return query.order_by(desc(RegistroErro.atualizado_em)).limit(limit).all()


def obter_erro_por_id(db: Session, erro_id: int) -> Optional[RegistroErro]:
    return db.query(RegistroErro).filter(RegistroErro.id == erro_id).first()


def listar_acessos(
    db: Session,
    app_slug: Optional[str] = None,
    status_code: Optional[int] = None,
    busca: Optional[str] = None,
    limit: int = 150
) -> List[LogAcesso]:
    query = db.query(LogAcesso)
    
    if app_slug and app_slug.strip() and app_slug.upper() != "TODOS":
        query = query.filter(LogAcesso.app_slug == app_slug.strip().lower())
        
    if status_code:
        query = query.filter(LogAcesso.status_code == status_code)
        
    if busca and busca.strip():
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                LogAcesso.usuario.ilike(termo),
                LogAcesso.cliente_identificador.ilike(termo),
                LogAcesso.rota.ilike(termo),
                LogAcesso.app_nome.ilike(termo),
                LogAcesso.ip_origem.ilike(termo)
            )
        )
        
    return query.order_by(desc(LogAcesso.id)).limit(limit).all()


def obter_resumo_telemetria(db: Session) -> ResumoTelemetria:
    apps = db.query(Aplicativo).all()
    total_apps = len(apps)
    
    operacionais = sum(1 for a in apps if a.status == "OPERACIONAL")
    alerta = sum(1 for a in apps if a.status == "ALERTA")
    criticos = sum(1 for a in apps if a.status == "CRITICO")
    
    erros_ativos = db.query(RegistroErro).filter(RegistroErro.status != "RESOLVIDO").count()
    erros_resolvidos = db.query(RegistroErro).filter(RegistroErro.status == "RESOLVIDO").count()
    
    total_acessos = db.query(LogAcesso).count()
    acessos_500 = db.query(LogAcesso).filter(LogAcesso.status_code >= 500).count()
    
    taxa_disp = 100.0
    if total_acessos > 0:
        taxa_disp = round(((total_acessos - acessos_500) / total_acessos) * 100, 1)
        
    # Geração de alertas preditivos automáticos
    alertas = []
    # 1. Verificar erros com alta recorrência
    erros_recorrentes = db.query(RegistroErro).filter(
        RegistroErro.status != "RESOLVIDO",
        RegistroErro.recorrencias >= 3
    ).order_by(desc(RegistroErro.recorrencias)).limit(3).all()
    
    for er in erros_recorrentes:
        alertas.append(
            f"ALERTA PREDITIVO: [{er.app_nome}] falha recorrente '{er.tipo_erro}' na rota '{er.rota_ou_funcao or 'sistema'}' ({er.recorrencias} ocorrências)."
        )
        
    # 2. Clientes afetados por anomalias
    clientes_afetados = db.query(RegistroErro.cliente_afetado, func.count(RegistroErro.id)).filter(
        RegistroErro.status != "RESOLVIDO",
        RegistroErro.cliente_afetado.isnot(None)
    ).group_by(RegistroErro.cliente_afetado).having(func.count(RegistroErro.id) >= 2).all()
    
    for cliente, qtd in clientes_afetados:
        alertas.append(
            f"IMPACTO EM CLIENTE: O cliente '{cliente}' registrou {qtd} incidentes ativos. Risco de insatisfação."
        )
        
    if not alertas and erros_ativos == 0:
        alertas.append("TODOS OS SISTEMAS EM CONDIÇÃO NOMINAL. Nenhuma anomalia preditiva detectada.")
        
    return ResumoTelemetria(
        total_apps=total_apps,
        apps_operacionais=operacionais,
        apps_alerta=alerta,
        apps_criticos=criticos,
        total_erros_ativos=erros_ativos,
        total_erros_resolvidos=erros_resolvidos,
        total_acessos=total_acessos,
        taxa_disponibilidade=taxa_disp,
        alertas_preditivos=alertas
    )

