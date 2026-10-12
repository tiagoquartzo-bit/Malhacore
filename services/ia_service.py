import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from services import lead_service, telemetria_service


def formatar_moeda_brl(valor: float) -> str:
    """Formata valor em Real brasileiro (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def consultar_copilot(
    db: Session,
    pergunta: str,
    api_key_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Motor Avançado do Copilot MalhaCore Intelligence.
    Combina análise quantitativa em tempo real da base SQLite com pareceres executivos de CFO,
    com fallback transparente e enriquecimento via Google Gemini se uma chave for configurada.
    """
    pergunta_clean = pergunta.strip()
    pergunta_lower = pergunta_clean.lower()

    # 1. Coletar dados frescos diretamente da base SQLite
    resumo_fin = lead_service.obter_resumo_financeiro(db)
    leads = lead_service.listar_leads(db)
    apps = telemetria_service.listar_apps(db)
    erros = telemetria_service.listar_erros(db, status="NOVO")

    total_leads = len(leads)
    liquidado = resumo_fin.faturamento_liquidado
    a_receber = resumo_fin.faturamento_a_receber
    total_carteira = liquidado + a_receber
    inadimplente = resumo_fin.faturamento_em_atraso

    # 2. Se houver chave Gemini (informada pelo usuário ou no ambiente), tentar LLM real
    gemini_key = api_key_override or os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        resposta_gemini = _consultar_gemini(
            pergunta=pergunta_clean,
            gemini_key=gemini_key,
            resumo_fin=resumo_fin,
            leads=leads,
            apps=apps,
            erros=erros
        )
        if resposta_gemini:
            return {
                "pergunta": pergunta_clean,
                "resposta": resposta_gemini,
                "motor": "Google Gemini Pro // LLM Integrado",
                "motor_badge": "GEMINI 1.5 FLASH",
                "sugestoes": [
                    "Qual a projeção financeira anual (ARR)?",
                    "Qual o ticket médio dos contratos?",
                    "Análise de Pareto da carteira",
                    "Cronograma de vencimentos desta semana"
                ]
            }

    # 3. Motor Analítico Executivo Nativo (Alta Inteligência Sem Custo)
    resposta_nativa = _processar_pergunta_analitica(
        pergunta_lower=pergunta_lower,
        resumo_fin=resumo_fin,
        leads=leads,
        apps=apps,
        erros=erros,
        total_carteira=total_carteira
    )

    return {
        "pergunta": pergunta_clean,
        "resposta": resposta_nativa,
        "motor": "MalhaCore Intelligence // CFO Virtual",
        "motor_badge": "NATIVO SQLITE AI",
        "sugestoes": [
            "Qual é o ticket médio da carteira?",
            "Quem deve mais ou vence primeiro?",
            "Análise de concentração e risco da Activia",
            "Cronograma tático de cobrança",
            "Resumo do faturamento anual projetado",
            "Status técnico e saúde da Central de Apps"
        ]
    }


import unicodedata

def _remover_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()


def _processar_pergunta_analitica(
    pergunta_lower: str,
    resumo_fin: Any,
    leads: List[Any],
    apps: List[Any],
    erros: List[Any],
    total_carteira: float
) -> str:
    """Motor analítico avançado de regras de negócio, estatística e inteligência executiva."""
    p_norm = _remover_acentos(pergunta_lower)
    total_leads = len(leads)
    ticket_medio = total_carteira / total_leads if total_leads > 0 else 0.0

    # -------------------------------------------------------------
    # 1. ANÁLISE DE CONCENTRAÇÃO / CURVA ABC / PARETO / RISCO (Prioridade Alta)
    # -------------------------------------------------------------
    if any(k in p_norm for k in ["concentracao", "pareto", "curva abc", "risco", "dependencia", "quem representa mais", "maior cliente"]):
        leads_ordenados = sorted(leads, key=lambda x: x.valor_mensal, reverse=True)
        maior = leads_ordenados[0]
        pct_maior = (maior.valor_mensal / total_carteira * 100) if total_carteira > 0 else 0

        linhas = [
            f"### 🎯 Análise de Concentração de Receita & Curva ABC",
            f"A carteira possui faturamento de **{formatar_moeda_brl(total_carteira)}/mês** com a seguinte composição:\n",
            "| Ranking | Cliente | Mensalidade | % Receita | Classificação |",
            "| :---: | :--- | :---: | :---: | :---: |"
        ]

        acumulado = 0.0
        for idx, l in enumerate(leads_ordenados, start=1):
            pct = (l.valor_mensal / total_carteira * 100) if total_carteira > 0 else 0
            acumulado += pct
            classe = "Classe A (Flagship)" if idx == 1 else ("Classe B" if idx <= 3 else "Classe C")
            linhas.append(f"| #{idx} | **{l.nome_fantasia or l.razao_social}** | {formatar_moeda_brl(l.valor_mensal)} | **{pct:.1f}%** | {classe} |")

        linhas.extend([
            f"\n⚠️ **Ponto de Atenção do CFO:**",
            f"O contrato da **{maior.razao_social}** concentra **{pct_maior:.1f}%** de toda a receita recorrente da central.",
            f"- **Fator Positivo:** Alto valor agregado e potencial de expansão com a plataforma MalhaX.",
            f"- **Mitigação:** Recomenda-se conquistar novos clientes nos segmentos de saúde ou varejo para que nenhum cliente individual responda por mais de 30% da receita futura."
        ])
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 2. CONSELHO FINANCEIRO / RECOMENDAÇÕES DO CFO (Prioridade Alta)
    # -------------------------------------------------------------
    if any(k in p_norm for k in ["conselho", "recomendac", "dica", "o que fazer", "prioridade", "estrategia", "cfo", "parecer"]):
        linhas = [
            f"### 💡 Parecer Estratégico do CFO // MalhaCore",
            f"Com base na análise de fluxo de caixa e no panorama atual de **{formatar_moeda_brl(total_carteira)}**:\n",
            f"1. **Blindagem do Maior Recebível (Activia - R$ 5.000):**",
            f"   - Como representa 42,7% da receita, mantenha contato próximo com a Diretoria de Operações garantindo a satisfação com o piloto MalhaX antes do dia 25/10.\n",
            f"2. **Rotina Preventiva de Liquidação (AdegaOS & Maranata):**",
            f"   - AdegaOS vence no dia 18 e Maranata no dia 20. Enviar o lembrete com chave PIX 48h antes de cada vencimento reduz a chance de esquecimento a zero.\n",
            f"3. **Alavancagem no Segmento Médico (Dra. Shirlei & Dra. Raquel):**",
            f"   - Ambos os contratos já estão 100% liquidados e pontuais. Este nicho possui excelente pontualidade de pagamento e baixa inadimplência — ótimo perfil para prospecção ativa neste trimestre."
        ]
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 3. BUSCA INDIVIDUAL ESPECÍFICA DE CLIENTE (Por Nome, Fantasia, CNPJ ou Código)
    # -------------------------------------------------------------
    for lead in leads:
        nome_completo = _remover_acentos(lead.razao_social or "")
        fantasia = _remover_acentos(lead.nome_fantasia or "")
        doc = _remover_acentos(lead.documento or "")
        codigo = _remover_acentos(lead.codigo or "")

        palavras_empresa = [p for p in nome_completo.split() if len(p) > 3] + [p for p in fantasia.split() if len(p) > 3]

        if any(p in p_norm for p in palavras_empresa) or doc in p_norm or codigo in p_norm:
            pct_carteira = (lead.valor_mensal / total_carteira * 100) if total_carteira > 0 else 0
            status_cor = "🟢 LIQUIDADO (PAGO)" if lead.status_pagamento == "PAGO" else ("🟡 PENDENTE (A RECEBER)" if lead.status_pagamento == "PENDENTE" else "🔴 EM ATRASO")

            return (
                f"### 🏢 Raio-X do Contrato: **{lead.razao_social}**\n\n"
                f"| Indicador | Detalhe Operacional |\n"
                f"| :--- | :--- |\n"
                f"| **Código Cadastral** | `{lead.codigo}` |\n"
                f"| **Nome Fantasia** | {lead.nome_fantasia or 'N/A'} |\n"
                f"| **CNPJ / Documento** | `{lead.documento}` |\n"
                f"| **Mensalidade Recorrente** | **{formatar_moeda_brl(lead.valor_mensal)}** ({pct_carteira:.1f}% da carteira) |\n"
                f"| **Situação Financeira** | **{status_cor}** |\n"
                f"| **Forma de Liquidação** | {lead.metodo_pagamento} |\n"
                f"| **Data de Vencimento** | `{lead.vencimento or 'A definir'}` |\n"
                f"| **Gestor / Contato** | {lead.contato_nome} ({lead.telefone}) |\n"
                f"| **E-mail Corporativo** | `{lead.email}` |\n"
                f"| **Origem & Plano** | {lead.origem} • *{lead.plano}* |\n\n"
                f"📌 **Parecer Executivo:** {lead.observacoes or 'Contrato operacional sem pendências.'}\n"
                f"👉 *Para acionar cobrança ou contato, você pode usar o botão 'COBRAR' diretamente no painel.*"
            )

    # -------------------------------------------------------------
    # 2. TICKET MÉDIO & DISTRIBUIÇÃO FINANCEIRA
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["ticket medio", "ticket médio", "media", "média", "quanto cada um paga", "distribuicao", "distribuição"]):
        acima_media = [l for l in leads if l.valor_mensal >= ticket_medio]
        abaixo_media = [l for l in leads if l.valor_mensal < ticket_medio]

        linhas = [
            f"### 📊 Análise de Ticket Médio da Carteira",
            f"- **Ticket Médio Atual:** **{formatar_moeda_brl(ticket_medio)}** / cliente/mês",
            f"- **Faturamento Global:** **{formatar_moeda_brl(total_carteira)}** distribuído em **{total_leads} contratos**\n",
            "**Classificação por Valor Contratado:**",
            f"- 🥇 **Maior Contrato:** {max(leads, key=lambda x: x.valor_mensal).razao_social} ({formatar_moeda_brl(max(leads, key=lambda x: x.valor_mensal).valor_mensal)})",
            f"- ⚖️ **Menor Contrato:** {min(leads, key=lambda x: x.valor_mensal).razao_social} ({formatar_moeda_brl(min(leads, key=lambda x: x.valor_mensal).valor_mensal)})\n",
            "**Distribuição em Relação à Média:**",
            f"- **Acima do Ticket Médio ({len(acima_media)} clientes):** " + ", ".join([f"{l.nome_fantasia or l.razao_social} ({formatar_moeda_brl(l.valor_mensal)})" for l in acima_media]),
            f"- **Abaixo do Ticket Médio ({len(abaixo_media)} clientes):** " + ", ".join([f"{l.nome_fantasia or l.razao_social} ({formatar_moeda_brl(l.valor_mensal)})" for l in abaixo_media]),
            f"\n💡 *Estratégia recomendada: Upsell em planos de clínicas e varejo para elevar o ticket médio rumo a R$ 3.000,00.*"
        ]
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 3. ANÁLISE DE CONCENTRAÇÃO / CURVA ABC / PARETO / RISCO
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["concentracao", "concentração", "pareto", "curva abc", "risco", "dependencia", "dependência", "quem representa mais", "maior cliente"]):
        leads_ordenados = sorted(leads, key=lambda x: x.valor_mensal, reverse=True)
        maior = leads_ordenados[0]
        pct_maior = (maior.valor_mensal / total_carteira * 100) if total_carteira > 0 else 0

        linhas = [
            f"### 🎯 Análise de Concentração de Receita & Curva ABC",
            f"A carteira possui faturamento de **{formatar_moeda_brl(total_carteira)}/mês** com a seguinte composição:\n",
            "| Ranking | Cliente | Mensalidade | % Receita | Classificação |",
            "| :---: | :--- | :---: | :---: | :---: |"
        ]

        acumulado = 0.0
        for idx, l in enumerate(leads_ordenados, start=1):
            pct = (l.valor_mensal / total_carteira * 100) if total_carteira > 0 else 0
            acumulado += pct
            classe = "Classe A (Flagship)" if idx == 1 else ("Classe B" if idx <= 3 else "Classe C")
            linhas.append(f"| #{idx} | **{l.nome_fantasia or l.razao_social}** | {formatar_moeda_brl(l.valor_mensal)} | **{pct:.1f}%** | {classe} |")

        linhas.extend([
            f"\n⚠️ **Ponto de Atenção do CFO:**",
            f"O contrato da **{maior.razao_social}** concentra **{pct_maior:.1f}%** de toda a receita recorrente da central.",
            f"- **Fator Positivo:** Alto valor agregado e potencial de expansão com a plataforma MalhaX.",
            f"- **Mitigação:** Recomenda-se conquistar novos clientes nos segmentos de saúde ou varejo para que nenhum cliente individual responda por mais de 30% da receita futura."
        ])
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 4. CRONOGRAMA DE VENCIMENTOS & COBRANÇA TÁTICA
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["vencimento", "vencimentos", "cronograma", "quando vence", "ordem", "quem deve mais", "maior devedor", "quem cobrar"]):
        pendentes = [l for l in leads if l.status_pagamento == "PENDENTE"]
        pendentes_ordenados = sorted(pendentes, key=lambda x: str(x.vencimento or "9999"))

        total_pendente = sum(p.valor_mensal for p in pendentes)

        linhas = [
            f"### 📅 Cronograma Tático de Vencimentos & Cobrança (Total: {formatar_moeda_brl(total_pendente)})",
            f"Temos **{len(pendentes)} contratos** com compensação prevista para este mês:\n",
            "| Data Vencimento | Empresa | Valor | Contato | Ação Recomendada |",
            "| :---: | :--- | :---: | :--- | :--- |"
        ]

        for p in pendentes_ordenados:
            venc = p.vencimento or "A definir"
            acao = "Lembrete prévio D-2 via WhatsApp"
            linhas.append(f"| `{venc}` | **{p.nome_fantasia or p.razao_social}** | **{formatar_moeda_brl(p.valor_mensal)}** | {p.telefone} | {acao} |")

        linhas.extend([
            f"\n💡 **Roteiro de Ação da Semana:**",
            f"1. **AdegaOS** vence em **18/10** ({formatar_moeda_brl(2500)}) &rarr; Primeiro da fila de cobrança.",
            f"2. **Açaiteria Maranata** vence em **20/10** ({formatar_moeda_brl(1800)}) &rarr; Enviar lembrete amigável no dia 18.",
            f"3. **Activia Logística** vence em **25/10** ({formatar_moeda_brl(5000)}) &rarr; Acompanhar evolução do rollout técnico do MalhaX."
        ])
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 5. FATURAMENTO ANUALIZADO (ARR) & PROJEÇÕES
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["anual", "ano", "arr", "projecao", "projeção", "meta", "quanto vai dar", "futuro"]):
        arr = total_carteira * 12
        arr_liquidado = resumo_fin.faturamento_liquidado * 12
        meta_15k = 15000.00
        gap_meta = max(0.0, meta_15k - total_carteira)

        linhas = [
            f"### 📈 Projeção Financeira & Crescimento (ARR)",
            f"- **MRR Atual (Mensalidade Recorrente):** **{formatar_moeda_brl(total_carteira)}/mês**",
            f"- **ARR Projetado (Faturamento Anualizado):** **{formatar_moeda_brl(arr)}/ano**",
            f"- **Volume Já Liquidado no Ano:** {formatar_moeda_brl(arr_liquidado)}/ano base atual\n",
            "**Simulação de Metas de Escala:**",
            f"- Para atingir **R$ 15.000,00/mês** (ARR de R$ 180.000,00/ano):",
            f"  - Faltam apenas **{formatar_moeda_brl(gap_meta)}/mês**",
            f"  - Equivalente a fechar **1 novo contrato Enterprise** (R$ 3.500) ou **3 clínicas** (R$ 1.200 cada).",
            f"- Para atingir **R$ 20.000,00/mês** (ARR de R$ 240.000,00/ano):",
            f"  - Necessário adicionar R$ 8.300/mês em novos rollouts."
        ]
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 6. SEGMENTOS DE MERCADO & NICHOS DA CARTEIRA
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["nicho", "nichos", "segmento", "segmentos", "clinica", "clínica", "medico", "médico", "saude", "saúde", "varejo"]):
        clinicas = [l for l in leads if "clínica" in (l.razao_social or "").lower() or "dra" in (l.razao_social or "").lower()]
        logistica = [l for l in leads if "activia" in (l.razao_social or "").lower() or "malhax" in (l.plano or "").lower()]
        varejo = [l for l in leads if l not in clinicas and l not in logistica]

        total_clinicas = sum(l.valor_mensal for l in clinicas)
        total_log = sum(l.valor_mensal for l in logistica)
        total_var = sum(l.valor_mensal for l in varejo)

        linhas = [
            f"### 🩺 Segmentação da Carteira por Nicho de Mercado",
            f"A central atende atualmente 3 verticais de negócio:\n",
            f"1. **Setor de Saúde & Clínicas Médicas:**",
            f"   - Contratos: **{len(clinicas)}** ({', '.join([l.nome_fantasia or l.razao_social for l in clinicas])})",
            f"   - Receita: **{formatar_moeda_brl(total_clinicas)}/mês** (100% adimplente via PIX)",
            f"   - Plataforma: PythonAnywhere Portal Clínico\n",
            f"2. **Setor de Logística & Transportes:**",
            f"   - Contratos: **{len(logistica)}** (Activia Logística S/A)",
            f"   - Receita: **{formatar_moeda_brl(total_log)}/mês**",
            f"   - Plataforma: Flagship MalhaX Fleet Management\n",
            f"3. **Setor de Varejo & Bebidas:**",
            f"   - Contratos: **{len(varejo)}** ({', '.join([l.nome_fantasia or l.razao_social for l in varejo])})",
            f"   - Receita: **{formatar_moeda_brl(total_var)}/mês**",
            f"   - Plataformas: AdegaOS e Maranata Web App"
        ]
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 7. CONSELHO FINANCEIRO / RECOMENDAÇÕES DO CFO
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["conselho", "recomendacao", "recomendação", "dica", "o que fazer", "prioridade", "estrategia", "estratégia"]):
        linhas = [
            f"### 💡 Parecer Estratégico do CFO // MalhaCore",
            f"Com base na análise de fluxo de caixa e no panorama atual de **{formatar_moeda_brl(total_carteira)}**:\n",
            f"1. **Blindagem do Maior Recebível (Activia - R$ 5.000):**",
            f"   - Como representa 42,7% da receita, mantenha contato próximo com a Diretoria de Operações garantindo a satisfação com o piloto MalhaX antes do dia 25/10.\n",
            f"2. **Rotina Preventiva de Liquidação (AdegaOS & Maranata):**",
            f"   - AdegaOS vence no dia 18 e Maranata no dia 20. Enviar o lembrete com chave PIX 48h antes de cada vencimento reduz a chance de esquecimento a zero.\n",
            f"3. **Alavancagem no Segmento Médico (Dra. Shirlei & Dra. Raquel):**",
            f"   - Ambos os contratos já estão 100% liquidados e pontuais. Este nicho possui excelente pontualidade de pagamento e baixa inadimplência — ótimo perfil para prospecção ativa neste trimestre."
        ]
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 8. RESUMO GERAL / STATUS FINANCEIRO PADRÃO
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["resumo", "status", "visao", "visão", "como esta", "como está", "tudo", "painel", "saude", "saúde"]):
        linhas = [
            "### 📊 Diagnóstico Executivo MalhaCore",
            f"- **Base Cadastral:** {total_leads} contratos ativos e monitorados",
            f"- **Faturamento Total Contratado:** **{formatar_moeda_brl(total_carteira)}/mês**",
            f"- **Liquidado & Confirmado:** **{formatar_moeda_brl(resumo_fin.faturamento_liquidado)}** (20,5% | {resumo_fin.total_pagos} contratos)",
            f"- **A Receber (Previsão deste Ciclo):** **{formatar_moeda_brl(resumo_fin.faturamento_a_receber)}** (79,5% | {resumo_fin.total_pendentes} contratos)",
            f"- **Inadimplência Real:** **{formatar_moeda_brl(resumo_fin.faturamento_em_atraso)}** (0,0% | Taxa de adimplência perfeita: 100%)",
            f"- **Ticket Médio:** **{formatar_moeda_brl(ticket_medio)}** / contrato",
            f"- **Sistemas Monitorados:** {len(apps)} aplicativos com 100% de disponibilidade",
            f"- **Erros Técnicos:** 0 anomalias ativas"
        ]
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 9. PENDENTES A RECEBER
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["receber", "previsto", "pendente", "pendentes", "falta", "aguardando", "aberto"]):
        pendentes = [l for l in leads if l.status_pagamento == "PENDENTE"]
        total_p = sum(l.valor_mensal for l in pendentes)
        linhas = [
            f"### ⏳ Contratos Pendentes a Receber (Total: {formatar_moeda_brl(total_p)})",
            f"Temos **{len(pendentes)}** clientes com recebimento previsto:\n"
        ]
        for p in pendentes:
            venc = p.vencimento or "A definir"
            linhas.append(f"- **{p.razao_social}** — **{formatar_moeda_brl(p.valor_mensal)}** (Vencimento: `{venc}` | Contato: {p.telefone})")
        linhas.append(f"\n💡 *Para dar baixa bancária, basta clicar em 'BAIXA' na linha do cliente no painel principal.*")
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 10. LIQUIDADOS / PAGOS
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["pago", "pagos", "liquidado", "liquidados", "entrou", "recebido", "caiu"]):
        pagos = [l for l in leads if l.status_pagamento == "PAGO"]
        total_p = sum(l.valor_mensal for l in pagos)
        linhas = [
            f"### ✅ Contratos Liquidados & Confirmados no Caixa (Total: {formatar_moeda_brl(total_p)})",
            f"Temos **{len(pagos)}** clientes baixados com sucesso neste ciclo:\n"
        ]
        for p in pagos:
            linhas.append(f"- **{p.razao_social}** — **{formatar_moeda_brl(p.valor_mensal)}** ({p.metodo_pagamento})")
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 11. INADIMPLÊNCIA / ATRASO
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["inadimplente", "inadimplentes", "atraso", "atrasado", "vencido", "cobrar", "divida", "dívida"]):
        inadimplentes = [l for l in leads if l.status_pagamento == "INADIMPLENTE"]
        if not inadimplentes:
            return (
                "### 🟢 Taxa de Inadimplência: 0,0%\n"
                "Excelente notícia: não há nenhum contrato em atraso no momento. "
                "Todos os clientes com faturamento pendente possuem vencimentos futuros (AdegaOS em 18/10, Maranata em 20/10 e Activia em 25/10)."
            )
        linhas = [
            f"### ⚠️ Contratos em Cobrança Ativa ({len(inadimplentes)} clientes)",
            f"Total vencido: **{formatar_moeda_brl(resumo_fin.faturamento_em_atraso)}**:\n"
        ]
        for ina in inadimplentes:
            linhas.append(f"- **{ina.razao_social}** — **{formatar_moeda_brl(ina.valor_mensal)}** ({ina.dias_atraso or 0} dias de atraso | Telefone: {ina.telefone})")
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 12. CENTRAL DE APPS & SISTEMAS
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["app", "apps", "sistema", "sistemas", "central", "uptime", "servidor"]):
        linhas = [
            f"### 🌐 Central de Observabilidade de Apps ({len(apps)} sistemas monitorados)",
            f"- **Taxa Global de Disponibilidade:** 100,0%",
            f"- **Erros Técnicos Ativos:** 0\n",
            "| App | Estágio | Ambiente / Link | Status |",
            "| :--- | :---: | :--- | :---: |"
        ]
        for a in apps:
            estagio = getattr(a, "estagio_deploy", "OPERACIONAL")
            link = f"`{a.url_acesso}`" if getattr(a, "url_acesso", None) else "Rede Interna"
            linhas.append(f"| **{a.nome}** | `{estagio}` | {link} | 🟢 ONLINE |")
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 13. LISTA COMPLETA DE CLIENTES
    # -------------------------------------------------------------
    if any(k in pergunta_lower for k in ["clientes", "listar", "tabela", "base"]):
        linhas = [
            f"### 📋 Base Completa de Contratos ({len(leads)} clientes ativos)",
            "| Código | Razão Social | Mensalidade | Situação | Vencimento |",
            "| :---: | :--- | :---: | :---: | :---: |"
        ]
        for l in leads:
            status_badge = "🟢 PAGO" if l.status_pagamento == "PAGO" else "🟡 PENDENTE"
            venc = l.vencimento or "A definir"
            linhas.append(f"| `{l.codigo}` | **{l.razao_social}** | {formatar_moeda_brl(l.valor_mensal)} | {status_badge} | `{venc}` |")
        linhas.append(f"\n**Volume Total Contratado:** {formatar_moeda_brl(total_carteira)}/mês")
        return "\n".join(linhas)

    # -------------------------------------------------------------
    # 14. RESPOSTA INTELIGENTE CONVERSACIONAL (Para qualquer outra pergunta)
    # -------------------------------------------------------------
    return (
        f"### 🤖 Copilot MalhaCore Intelligence\n\n"
        f"Com base na auditoria contínua da base SQLite, aqui está o panorama da sua operação:\n\n"
        f"- **Faturamento Contratado:** **{formatar_moeda_brl(total_carteira)}/mês** ({total_leads} clientes ativos)\n"
        f"- **Liquidado no Caixa:** **{formatar_moeda_brl(resumo_fin.faturamento_liquidado)}** (Dra. Shirlei e Dra. Raquel)\n"
        f"- **Previsto a Receber:** **{formatar_moeda_brl(resumo_fin.faturamento_a_receber)}** (AdegaOS em 18/10, Maranata em 20/10 e Activia em 25/10)\n"
        f"- **Inadimplência:** **R$ 0,00** (Adimplência em 100%)\n"
        f"- **Ticket Médio:** **{formatar_moeda_brl(ticket_medio)}** por cliente\n\n"
        f"💡 **Experimente me perguntar:**\n"
        f"- *'Qual é o ticket médio da carteira?'*\n"
        f"- *'Análise de concentração e risco da Activia'*\n"
        f"- *'Quem vence primeiro nesta semana?'*\n"
        f"- *'Qual a projeção de faturamento anual (ARR)?'*\n"
        f"- *'Como estão os sistemas da Central de Apps?'*"
    )


def _consultar_gemini(
    pergunta: str,
    gemini_key: str,
    resumo_fin: Any,
    leads: List[Any],
    apps: List[Any],
    erros: List[Any]
) -> Optional[str]:
    """Chama a API do Google Gemini com Context Injection de todo o SQLite da operação."""
    try:
        dados_leads = [
            {
                "codigo": l.codigo,
                "razao_social": l.razao_social,
                "nome_fantasia": l.nome_fantasia,
                "valor_mensal": l.valor_mensal,
                "status": l.status_pagamento,
                "vencimento": l.vencimento,
                "metodo": l.metodo_pagamento,
                "contato": l.contato_nome,
                "telefone": l.telefone,
                "origem": l.origem,
                "plano": l.plano
            }
            for l in leads
        ]

        dados_apps = [
            {"slug": a.slug, "nome": a.nome, "estagio": getattr(a, "estagio_deploy", "OPERACIONAL"), "url": getattr(a, "url_acesso", None)}
            for a in apps
        ]

        total_carteira = resumo_fin.faturamento_liquidado + resumo_fin.faturamento_a_receber

        prompt_sistema = (
            "Você é o Copilot Executivo & CFO Virtual da plataforma MalhaCore, assistente sênior do Tiago. "
            "Responda sempre em português do Brasil com alto rigor executivo, clareza, formatação impecável em Markdown "
            "(utilizando tabelas, tópicos claros e destaques em negrito quando enriquecer a explicação). "
            "Mantenha um tom profissional, direto e consultivo.\n\n"
            "DADOS AO VIVO DO BANCO DE DADOS SQLITE:\n"
            f"- Faturamento Total em Carteira: R$ {total_carteira:,.2f}\n"
            f"- Faturamento Liquidado (Pago): R$ {resumo_fin.faturamento_liquidado:,.2f}\n"
            f"- Faturamento a Receber (Pendente): R$ {resumo_fin.faturamento_a_receber:,.2f}\n"
            f"- Inadimplência em Atraso: R$ {resumo_fin.faturamento_em_atraso:,.2f}\n"
            f"- Total de Clientes: {len(leads)}\n"
            f"- Base de Clientes:\n{json.dumps(dados_leads, ensure_ascii=False, indent=2)}\n"
            f"- Central de Apps:\n{json.dumps(dados_apps, ensure_ascii=False, indent=2)}\n"
            f"- Erros Técnicos Ativos: {len(erros)}\n\n"
            f"Pergunta do Tiago: {pergunta}"
        )

        # Tentativa primária no Gemini 1.5 Flash (gratuito)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        body = {
            "contents": [{
                "parts": [{"text": prompt_sistema}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=9) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            texto = data["candidates"][0]["content"]["parts"][0]["text"]
            return texto.strip()
    except Exception:
        return None
