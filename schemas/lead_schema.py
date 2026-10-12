from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LeadCreate(BaseModel):
    razao_social: str = Field(..., min_length=2, max_length=255)
    nome_fantasia: Optional[str] = None
    documento: str = Field(..., min_length=5, max_length=32)
    contato_nome: str = Field(..., min_length=2, max_length=128)
    contato_cargo: Optional[str] = "Diretoria / Operações"
    email: str = Field(..., min_length=5, max_length=128)
    telefone: str = Field(..., min_length=8, max_length=32)
    origem: Optional[str] = "App MalhaCore"
    plano: Optional[str] = "Malha Enterprise"
    valor_mensal: float = Field(..., ge=0)
    status_pagamento: Optional[str] = "PENDENTE"
    metodo_pagamento: Optional[str] = "PIX"
    vencimento: Optional[str] = None
    observacoes: Optional[str] = None
    vincular_app: Optional[bool] = False
    app_vinculado_slug: Optional[str] = None
    app_estagio_deploy: Optional[str] = "ROLLOUT"


class LeadUpdateStatus(BaseModel):
    status_pagamento: str  # PAGO, PENDENTE, INADIMPLENTE, CANCELADO
    metodo_pagamento: Optional[str] = None
    motivo_baixa: Optional[str] = None


class LeadUpdate(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    documento: Optional[str] = None
    contato_nome: Optional[str] = None
    contato_cargo: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    origem: Optional[str] = None
    plano: Optional[str] = None
    valor_mensal: Optional[float] = None
    status_pagamento: Optional[str] = None
    metodo_pagamento: Optional[str] = None
    vencimento: Optional[str] = None
    observacoes: Optional[str] = None
    motivo_alteracao: Optional[str] = "Atualização cadastral via painel"


class AuditoriaResponse(BaseModel):
    id: int
    lead_id: int
    codigo_lead: str
    tipo_evento: str
    status_anterior: Optional[str] = None
    status_novo: str
    valor: float
    responsavel: str
    detalhes: Optional[str] = None
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: int
    codigo: str
    razao_social: str
    nome_fantasia: Optional[str]
    documento: str
    contato_nome: str
    contato_cargo: Optional[str]
    email: str
    telefone: str
    origem: str
    plano: str
    valor_mensal: float
    status_pagamento: str
    metodo_pagamento: str
    vencimento: Optional[str]
    data_pagamento: Optional[str]
    dias_atraso: int
    nfe_emitida: bool
    observacoes: Optional[str]
    criado_em: Optional[datetime]

    class Config:
        from_attributes = True


class ResumoFinanceiro(BaseModel):
    total_leads: int
    total_pagos: int
    total_pendentes: int
    total_inadimplentes: int
    faturamento_liquidado: float
    faturamento_a_receber: float
    faturamento_em_atraso: float
    taxa_adimplencia: float
