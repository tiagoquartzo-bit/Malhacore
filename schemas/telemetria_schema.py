from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AppCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64)
    nome: str = Field(..., min_length=2, max_length=128)
    categoria: Optional[str] = "Corporativo"
    ambiente: Optional[str] = "producao"
    estagio_deploy: Optional[str] = "DESENVOLVIMENTO"  # PUBLICADO, ROLLOUT, DESENVOLVIMENTO
    cliente_piloto: Optional[str] = None
    versao: Optional[str] = "1.0.0"
    descricao: Optional[str] = None
    url_acesso: Optional[str] = None


class AppResponse(BaseModel):
    id: int
    slug: str
    nome: str
    categoria: str
    ambiente: str
    api_key: Optional[str] = None
    status: str
    estagio_deploy: str = "DESENVOLVIMENTO"
    cliente_piloto: Optional[str] = None
    versao: str = "1.0.0"
    descricao: Optional[str] = None
    url_acesso: Optional[str] = None
    ultimo_ping: Optional[datetime] = None
    criado_em: Optional[datetime] = None
    total_erros_ativos: int = 0
    total_acessos: int = 0

    class Config:
        from_attributes = True



class LogAcessoCreate(BaseModel):
    app_slug: str
    app_nome: Optional[str] = None
    usuario: Optional[str] = "anonimo"
    cliente_identificador: Optional[str] = None
    rota: str
    metodo: Optional[str] = "GET"
    status_code: Optional[int] = 200
    tempo_resposta_ms: Optional[float] = 0.0
    ip_origem: Optional[str] = None
    detalhes: Optional[str] = None


class LogAcessoResponse(BaseModel):
    id: int
    app_slug: str
    app_nome: Optional[str] = None
    usuario: Optional[str] = None
    cliente_identificador: Optional[str] = None
    rota: str
    metodo: str
    status_code: int
    tempo_resposta_ms: float
    ip_origem: Optional[str] = None
    detalhes: Optional[str] = None
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class RegistroErroCreate(BaseModel):
    app_slug: str
    app_nome: Optional[str] = None
    nivel: Optional[str] = "ERROR"  # CRITICAL, ERROR, WARNING
    tipo_erro: str
    mensagem: str
    traceback: Optional[str] = None
    rota_ou_funcao: Optional[str] = None
    cliente_afetado: Optional[str] = None
    usuario_afetado: Optional[str] = None
    ambiente: Optional[str] = "producao"


class ErroUpdateStatus(BaseModel):
    status: str  # NOVO, EM_ANALISE, RESOLVIDO
    solucao_nota: Optional[str] = None


class RegistroErroResponse(BaseModel):
    id: int
    app_slug: str
    app_nome: Optional[str] = None
    nivel: str
    tipo_erro: str
    mensagem: str
    traceback: Optional[str] = None
    rota_ou_funcao: Optional[str] = None
    cliente_afetado: Optional[str] = None
    usuario_afetado: Optional[str] = None
    ambiente: str
    status: str
    recorrencias: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    resolvido_em: Optional[datetime] = None
    solucao_nota: Optional[str] = None

    class Config:
        from_attributes = True


class ResumoTelemetria(BaseModel):
    total_apps: int
    apps_operacionais: int
    apps_alerta: int
    apps_criticos: int
    total_erros_ativos: int
    total_erros_resolvidos: int
    total_acessos: int
    taxa_disponibilidade: float
    alertas_preditivos: List[str] = []

