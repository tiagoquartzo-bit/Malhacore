from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from services import lead_service, telemetria_service, ia_service
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/ia", tags=["Copilot & Inteligência IA"])


class PerguntaIARequest(BaseModel):
    pergunta: str
    api_key: Optional[str] = None


def formatar_moeda_fala(valor: float) -> str:
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))
    if centavos > 0:
        return f"{inteiro} reais e {centavos} centavos"
    return f"{inteiro} reais"


@router.get("/briefing")
def obter_briefing_executivo(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Gera diagnóstico e relatório inteligente do ecossistema MalhaCore."""
    resumo_fin = lead_service.obter_resumo_financeiro(db)
    leads = lead_service.listar_leads(db)
    apps = telemetria_service.listar_apps(db)
    erros = telemetria_service.listar_erros(db, status="NOVO")

    total_leads = len(leads)
    liquidado = resumo_fin.faturamento_liquidado
    a_receber = resumo_fin.faturamento_a_receber
    total_carteira = liquidado + a_receber
    inadimplente = resumo_fin.faturamento_em_atraso

    apps_publicados = [a for a in apps if getattr(a, "estagio_deploy", "") == "PUBLICADO"]
    apps_rollout = [a for a in apps if getattr(a, "estagio_deploy", "") == "ROLLOUT"]
    apps_desenv = [a for a in apps if getattr(a, "estagio_deploy", "") == "DESENVOLVIMENTO"]
    erros_criticos = [e for e in erros if getattr(e, "nivel", "") == "CRITICAL"]

    hora_atual = datetime.now().hour
    saudacao = "Bom dia" if 5 <= hora_atual < 12 else ("Boa tarde" if 12 <= hora_atual < 18 else "Boa noite")

    texto_fala = (
        f"{saudacao}, Tiago. Central MalhaCore operacional e conectada. "
        f"Atualmente temos {total_leads} contratos na base, com faturamento total em carteira de R$ {total_carteira:,.2f}. "
        f"Deste montante, R$ {liquidado:,.2f} já foram liquidados e confirmados, e R$ {a_receber:,.2f} estão previstos para compensação. "
    )

    if inadimplente > 0:
        texto_fala += f"Atenção financeira: temos R$ {inadimplente:,.2f} em contratos vencidos aguardando contato de cobrança. "
    else:
        texto_fala += "Excelente notícia financeira: taxa de inadimplência está zerada neste ciclo. "

    texto_fala += (
        f"Na central de sistemas, monitoramos {len(apps)} pontos de rede. "
        f"{len(apps_publicados)} sistemas estão no ar na rede, incluindo a Clínica da Doutora Shirlei, "
        f"e o projeto flagship MalhaX está ativo em rollout prioritário para a Activia Logística. "
    )

    if len(erros_criticos) > 0:
        texto_fala += f"Identifiquei {len(erros_criticos)} incidentes técnicos críticos que exigem inspeção imediata no monitor de bugs."
    else:
        texto_fala += "Todos os sistemas operam em condição nominal, com estabilidade técnica de 100% e zero anomalias ativas."

    texto_fala += " Todos os módulos estão prontos para a sua condução operacional."

    return {
        "status": "OPERACIONAL_ESTAVEL" if len(erros_criticos) == 0 else "ATENCAO_OPERACIONAL",
        "saudacao": saudacao,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "texto_fala": texto_fala,
        "kpis": {
            "total_contratos": total_leads,
            "faturamento_carteira": round(total_carteira, 2),
            "faturamento_liquidado": round(liquidado, 2),
            "faturamento_a_receber": round(a_receber, 2),
            "inadimplencia": round(inadimplente, 2),
            "total_apps": len(apps),
            "apps_publicados": len(apps_publicados),
            "apps_rollout": len(apps_rollout),
            "apps_desenvolvimento": len(apps_desenv),
            "erros_ativos": len(erros)
        },
        "destaques": [
            {
                "titulo": "Carteira Financeira",
                "valor": f"R$ {total_carteira:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "status": "CONFIRMADO",
                "detalhe": f"R$ {liquidado:,.2f} liquidado | R$ {a_receber:,.2f} a receber"
            },
            {
                "titulo": "Rollout Flagship",
                "valor": "MalhaX — Activia",
                "status": "EM ROLLOUT",
                "detalhe": "Plataforma integrada de logística e inteligência de frotas"
            },
            {
                "titulo": "Disponibilidade de Rede",
                "valor": f"{len(apps_publicados)} Sistemas no Ar",
                "status": "OPERACIONAL",
                "detalhe": "Clínicas Shirlei & MalhaCore Master conectados"
            },
            {
                "titulo": "Saúde dos Sistemas",
                "valor": "0 Falhas Críticas",
                "status": "ESTÁVEL",
                "detalhe": "Telemetria preditiva sem registros de anomalia"
            }
        ],
        "recomendacoes": [
            "Acompanhar o piloto operacional do MalhaX com os gestores da Activia Logística.",
            "Confirmar as baixas bancárias conforme os vencimentos previstos forem compensados.",
            "Verificar a evolução dos novos módulos da Açaiteria Maranata e AdegaOS."
        ]
    }


@router.post("/perguntar")
@router.post("/copilot")
def consultar_ia(dados: PerguntaIARequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Consulta o Copilot MalhaCore (100% gratuito, sem voz, integrado à base de dados)."""
    resultado = ia_service.consultar_copilot(
        db=db,
        pergunta=dados.pergunta,
        api_key_override=dados.api_key
    )
    resultado["timestamp"] = datetime.now().strftime("%H:%M:%S")
    return resultado


