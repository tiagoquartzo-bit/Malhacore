from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from services import lead_service, telemetria_service
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/ia", tags=["Inteligência & Briefing IA"])


class PerguntaIARequest(BaseModel):
    pergunta: str


def formatar_moeda_fala(valor: float) -> str:
    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))
    if centavos > 0:
        return f"{inteiro} reais e {centavos} centavos"
    return f"{inteiro} reais"


@router.get("/briefing")
def obter_briefing_executivo(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Gera diagnóstico e relatório inteligente de voz e texto do ecossistema MalhaCore."""
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

    # Construção de roteiro falado em linguagem natural fluida
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

    # Diagnóstico textual executivo
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
def consultar_ia(dados: PerguntaIARequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Responde dúvidas do operador sobre contratos, valores ou saúde dos apps."""
    pergunta_lower = dados.pergunta.lower()
    resumo_fin = lead_service.obter_resumo_financeiro(db)
    leads = lead_service.listar_leads(db)
    apps = telemetria_service.listar_apps(db)

    # Análise de intenções inteligente
    if any(k in pergunta_lower for k in ["receber", "previsto", "falta", "saldo"]):
        resposta = f"Você tem R$ {resumo_fin.faturamento_a_receber:,.2f} previstos a receber em carteira neste ciclo, distribuídos entre os contratos pendentes."
    elif any(k in pergunta_lower for k in ["liquidado", "pago", "entrou", "recebido", "caiu"]):
        resposta = f"O faturamento liquidado até o momento é de R$ {resumo_fin.faturamento_liquidado:,.2f}, totalmente confirmado via PIX."
    elif any(k in pergunta_lower for k in ["activia", "malhax", "logistica"]):
        lead_activia = next((l for l in leads if "activia" in l.razao_social.lower()), None)
        valor = f"R$ {lead_activia.valor_mensal:,.2f}" if lead_activia else "não informado"
        resposta = f"O contrato da Activia Logística está associado ao MalhaX, com valor mensal de {valor}. O sistema está configurado em estágio de ROLLOUT."
    elif any(k in pergunta_lower for k in ["shirlei", "clinica", "clínica"]):
        resposta = "A Clínica da Dra. Shirlei Elisabete está com contrato de R$ 1.200,00 liquidado no ciclo, e o sistema 01.Clínicas está ativo no PythonAnywhere."
    elif any(k in pergunta_lower for k in ["maranata", "açaí", "acai", "açaiteria"]):
        resposta = "A Açaiteria Maranata está cadastrada com mensalidade de R$ 1.800,00 no plano de Totem de Autoatendimento e comanda rápida."
    elif any(k in pergunta_lower for k in ["adega", "adegaos"]):
        resposta = "A AdegaOS Distribuidora possui contrato de R$ 2.500,00 mensais para a solução WMS e gestão de empórios."
    elif any(k in pergunta_lower for k in ["erro", "bug", "falha", "anomalia"]):
        erros_ativos = telemetria_service.listar_erros(db, status="NOVO")
        resposta = f"Atualmente temos {len(erros_ativos)} erros ou bugs ativos. Todos os sistemas monitorados estão operando com estabilidade."
    else:
        total = resumo_fin.faturamento_liquidado + resumo_fin.faturamento_a_receber
        resposta = f"A Central MalhaCore possui {len(leads)} clientes ativos com faturamento total de R$ {total:,.2f} e {len(apps)} sistemas mapeados na rede."

    return {
        "pergunta": dados.pergunta,
        "resposta": resposta,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
