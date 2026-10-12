from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.settings import settings
from database.connection import engine, Base, SessionLocal
from services.seed_data import seed_database
from routes import api_router, telemetria_router, views_router, ia_router

# Inicializar tabelas do banco SQLite
Base.metadata.create_all(bind=engine)

# Inserir carga inicial corporativa se banco estiver novo
with SessionLocal() as db_session:
    seed_database(db_session)

# Aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Núcleo de Comando, Auditoria Financeira e Observabilidade Multi-App MalhaCore",
    version="1.1.0"
)

# Montar arquivos estáticos
static_dir = settings.BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Incluir rotas
app.include_router(views_router)
app.include_router(api_router)
app.include_router(telemetria_router)
app.include_router(ia_router)

