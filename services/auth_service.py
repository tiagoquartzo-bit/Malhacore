import hmac
import hashlib
import secrets
import json
import base64
import time
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from database.models import Usuario
from config.settings import settings

SECRET_KEY = getattr(settings, "SECRET_KEY", "malhacore-secret-master-key-2026-auth")
SESSION_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 dias de persistência


def gerar_hash_senha(senha: str) -> str:
    """Gera hash PBKDF2-HMAC-SHA256 com salt aleatório de 16 bytes (100.000 iterações)."""
    salt = secrets.token_hex(16)
    chave = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{chave.hex()}"


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash armazenado."""
    try:
        salt, chave_hex = hash_armazenado.split(":")
        chave_calc = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(chave_calc.hex(), chave_hex)
    except Exception:
        return False


def gerar_token_sessao(usuario_id: int, email: str, nome: str) -> str:
    """Gera um token de sessão assinado com HMAC-SHA256 e timestamp de expiração."""
    payload = {
        "uid": usuario_id,
        "email": email,
        "nome": nome,
        "exp": int(time.time()) + SESSION_MAX_AGE_SECONDS
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    
    assinatura = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{assinatura}"


def verificar_token_sessao(token: str) -> Optional[dict]:
    """Valida a assinatura do token e verifica se não está expirado."""
    if not token or "." not in token:
        return None
    try:
        payload_b64, assinatura = token.split(".", 1)
        
        # Verificar assinatura HMAC
        assinatura_esperada = hmac.new(
            SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(assinatura, assinatura_esperada):
            return None
            
        # Decodificar payload
        padding = "=" * (4 - len(payload_b64) % 4) if len(payload_b64) % 4 != 0 else ""
        payload_json = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8")).decode("utf-8")
        dados = json.loads(payload_json)
        
        # Verificar expiração
        if dados.get("exp", 0) < int(time.time()):
            return None
            
        return dados
    except Exception:
        return None


def obter_ou_criar_usuario_admin(db: Session, email: str = "tiagoaraujoxsl@gmail.com", senha_pura: str = "Neyva@10") -> Usuario:
    """Garante a existência do usuário administrador padrão com a senha solicitada."""
    usuario = db.query(Usuario).filter(Usuario.email == email.strip().lower()).first()
    if not usuario:
        hash_senha = gerar_hash_senha(senha_pura)
        usuario = Usuario(
            email=email.strip().lower(),
            nome="Tiago Araujo",
            senha_hash=hash_senha,
            cargo="Administrador Geral & Fundador",
            ativo=True,
            criado_em=datetime.now(timezone.utc)
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    else:
        # Se já existir, garante que a senha está atualizada com a chave requisitada
        if not verificar_senha(senha_pura, usuario.senha_hash):
            usuario.senha_hash = gerar_hash_senha(senha_pura)
            usuario.ativo = True
            db.commit()
            db.refresh(usuario)
    return usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> Optional[Usuario]:
    """Autentica usuário e atualiza timestamp de último login."""
    usuario = db.query(Usuario).filter(Usuario.email == email.strip().lower(), Usuario.ativo == True).first()
    if not usuario:
        return None
    if not verificar_senha(senha, usuario.senha_hash):
        return None
        
    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(usuario)
    return usuario

