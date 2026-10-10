from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar .env se existir
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "MalhaCore Ledger & Command")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = BASE_DIR / "data" / "malhacore.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")


settings = Settings()
