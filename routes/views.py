import urllib.parse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.connection import get_db
from config.settings import settings
from services import lead_service, telemetria_service, auth_service

templates = Jinja2Templates(directory=str(settings.BASE_DIR / "templates"))
router = APIRouter(tags=["Visões do Painel"])

COOKIE_NAME = "malhacore_session"


@router.get("/login")
def pagina_login(request: Request):
    """Página de autenticação do operador MalhaCore."""
    token = request.cookies.get(COOKIE_NAME)
    if token and auth_service.verificar_token_sessao(token):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"email": "tiagoaraujoxsl@gmail.com", "erro": None}
    )


@router.post("/login")
async def processar_login(request: Request, db: Session = Depends(get_db)):
    """Valida credenciais e gera cookie de sessão seguro."""
    body_bytes = await request.body()
    form_data = urllib.parse.parse_qs(body_bytes.decode("utf-8"))

    email = form_data.get("email", [""])[0].strip()
    senha = form_data.get("senha", [""])[0].strip()

    # Garantir que o admin existe e senha está sincronizada
    auth_service.obter_ou_criar_usuario_admin(db, email="tiagoaraujoxsl@gmail.com", senha_pura="Neyva@10")

    usuario = auth_service.autenticar_usuario(db, email=email, senha=senha)
    if not usuario:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "email": email,
                "erro": "Credenciais inválidas. Verifique o e-mail ou a chave de acesso."
            },
            status_code=401
        )

    token = auth_service.gerar_token_sessao(usuario.id, usuario.email, usuario.nome)
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=7 * 24 * 3600,
        httponly=True,
        samesite="lax"
    )
    return resp


@router.get("/logout")
def processar_logout():
    """Encerra a sessão do operador e retorna ao login."""
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(key=COOKIE_NAME)
    return resp


@router.get("/")
def painel_principal(request: Request, db: Session = Depends(get_db)):
    """Painel principal unificado (protegido por sessão de autenticação)."""
    token = request.cookies.get(COOKIE_NAME)
    dados_sessao = auth_service.verificar_token_sessao(token) if token else None

    if not dados_sessao:
        return RedirectResponse(url="/login", status_code=302)

    resumo_fin = lead_service.obter_resumo_financeiro(db)
    leads = lead_service.listar_leads(db)
    resumo_tele = telemetria_service.obter_resumo_telemetria(db)
    apps = telemetria_service.listar_apps(db)
    erros = telemetria_service.listar_erros(db, limit=100)
    acessos = telemetria_service.listar_acessos(db, limit=150)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "resumo": resumo_fin,
            "leads": leads,
            "telemetria": resumo_tele,
            "apps": apps,
            "erros": erros,
            "acessos": acessos,
            "app_name": settings.APP_NAME,
            "usuario_logado": dados_sessao,
        }
    )


