import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from services import lead_service, telemetria_service


def formatar_moeda_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def consultar_copilot(
    db: Session,
    pergunta: str,
    api_key_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Motor do Copilot MalhaCore.
    Utiliza motor semântico nativo integrado diretamente ao SQLite local,
    com suporte transparente ao Google Gemini (gratuito) caso haja API key configurada.
    """
    pergunta_clean = pergunta.strip()
    pergunta_lower = pergunta_clean.lower()

    # Coletar dados ao vivo do banco de dados
    resumo_fin = lead_service.obter_resumo_financeiro(db)
    leads = lead_service.listar_leads(db)
    apps = telemetria_service.listar_apps(db)
    erros = telemetria_service.listar_erros(db, status="NOVO")

    total_leads = len(leads)
    liquidado = resumo_fin.faturamento_liquidado
    a_receber = resumo_fin.faturamento_a_receber
    total_carteira = liquidado + a_receber
    inadimplente = resumo_fin.faturamento_em_atraso

    # 1. Tentar chamada ao Google Gemini se houver chave (gratuita)
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
                "motor": "Google Gemini 1.5 Flash (Gratuito)",
                "sugestoes": [
                    "Qual o faturamento previsto a receber?",
                    "Quais clientes estão pendentes?",
                    "Como está o status dos apps?",
                    "Detalhes da Activia Logística"
                ]
            }

    # 2. Motor Nativo Copilot MalhaCore (100% gratuito, offline, sem chave necessária)
    resposta_nativa = _processar_pergunta_nativa(
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
        "motor": "Copilot MalhaCore Local (Zero Custo)",
        "sugestoes": [
            "Resumo financeiro da carteira",
            "Quais contratos estão pendentes?",
            "Quem são todos os meus clientes?",
            "Status da Central de Apps",
            "Consultar cliente Activia",
            "Verificar erros e bugs"
        ]
    }


def _processar_pergunta_nativa(
    pergunta_lower: str,
    resumo_fin: Any,
    leads: List[Any],
    apps: List[Any],
    erros: List[Any],
    total_carteira: float
) -> str:
    """Processa intenções e formata resposta executiva em Markdown profissional."""

    # 1. BUSCA ESPECÍFICA DE CLIENTE PELO NOME OU CNPJ (Prioridade Alta)
    for lead in leads:
        nome_completo = (lead.razao_social or "").lower()
        fantasia = (lead.nome_fantasia or "").lower()
        doc = (lead.documento or "").lower()
        codigo = (lead.codigo or "").lower()

        palavras_empresa = [p for p in nome_completo.split() if len(p) > 3] + [p for p in fantasia.split() if len(p) > 3]

        if any(p in pergunta_lower for p in palavras_empresa) or doc in pergunta_lower or codigo in pergunta_lower:
            linhas = [
                f"### 🏢 Ficha do Contrato: {lead.razao_social}",
                f"- **Código:** `{lead.codigo}`",
                f"- **Nome Fantasia:** {lead.nome_fantasia or 'N/A'}",
                f"- **CNPJ/CPF:** `{lead.documento}`",
                f"- **Mensalidade:** **{formatar_moeda_brl(lead.valor_mensal)}**",
                f"- **Status Financeiro:** **{lead.status_pagamento}**",
                f"- **Método de Pagamento:** {lead.metodo_pagamento}",
                f"- **Data de Vencimento:** {lead.vencimento or 'A definir'}",
                f"- **Contato:** {lead.contato_nome} ({lead.telefone} | {lead.email})",
                f"- **Origem / Plano:** {lead.origem} | {lead.plano}",
                f"- **Observações:** {lead.observacoes or 'Sem observações'}"
            ]
            return "\n".join(linhas)

    # 2. RESUMO GERAL / STATUS / COMO ESTÁ TUDO
    if any(k in pergunta_lower for k in ["resumo", "status geral", "visao geral", "visão geral", "como esta tudo", "como está tudo", "painel", "saude", "saúde"]):
        linhas = [
            "### 📊 Resumo Executivo MalhaCore",
            f"- **Base de Clientes:** {len(leads)} contratos ativos",
            f"- **Faturamento Total em Carteira:** **{formatar_moeda_brl(total_carteira)}**",
            f"- **Liquidado / Confirmado:** **{formatar_moeda_brl(resumo_fin.faturamento_liquidado)}** ({resumo_fin.total_pagos} contratos)",
            f"- **A Receber (Previsto):** **{formatar_moeda_brl(resumo_fin.faturamento_a_receber)}** ({resumo_fin.total_pendentes} contratos)",
            f"- **Inadimplência:** **{formatar_moeda_brl(resumo_fin.faturamento_em_atraso)}** ({resumo_fin.total_inadimplentes} contratos)",
            f"- **Sistemas Monitorados:** {len(apps)} aplicativos na rede",
            f"- **Erros Técnicos Ativos:** {len(erros)} anomalias pendentes"
        ]
        if resumo_fin.faturamento_em_atraso == 0:
            linhas.append("\n✅ *A carteira está com adimplência perfeita (100% em dia).*")
        return "\n".join(linhas)

    # 3. PENDENTES / A RECEBER
    if any(k in pergunta_lower for k in ["receber", "previsto", "pendente", "pendentes", "falta", "aguardando", "aberto"]):
        pendentes = [l for l in leads if l.status_pagamento == "PENDENTE"]
        total_p = sum(l.valor_mensal for l in pendentes)
        linhas = [
            f"### ⏳ Contratos Pendentes a Receber (Total: {formatar_moeda_brl(total_p)})",
            f"Temos **{len(pendentes)}** clientes aguardando liquidação neste ciclo:\n"
        ]
        for p in pendentes:
            venc = p.vencimento or "A definir"
            linhas.append(f"- **{p.razao_social}** — **{formatar_moeda_brl(p.valor_mensal)}** (Vencimento: `{venc}` | Contato: {p.telefone})")
        linhas.append(f"\n💡 *Você pode dar baixa manual no painel assim que os comprovantes forem confirmados.*")
        return "\n".join(linhas)

    # 3. LIQUIDADOS / PAGOS
    if any(k in pergunta_lower for k in ["pago", "pagos", "liquidado", "liquidados", "entrou", "recebido", "caiu"]):
        pagos = [l for l in leads if l.status_pagamento == "PAGO"]
        total_p = sum(l.valor_mensal for l in pagos)
        linhas = [
            f"### ✅ Contratos Liquidados & Confirmados (Total: {formatar_moeda_brl(total_p)})",
            f"Temos **{len(pagos)}** contratos baixados com sucesso:\n"
        ]
        for p in pagos:
            linhas.append(f"- **{p.razao_social}** — **{formatar_moeda_brl(p.valor_mensal)}** via {p.metodo_pagamento}")
        return "\n".join(linhas)

    # 4. INADIMPLÊNCIA / ATRASOS
    if any(k in pergunta_lower for k in ["inadimplente", "inadimplentes", "atraso", "atrasado", "vencido", "cobrar", "divida", "dívida", "deve"]):
        inadimplentes = [l for l in leads if l.status_pagamento == "INADIMPLENTE"]
        if not inadimplentes:
            return "### 🟢 Inadimplência Zerada\nNenhum contrato possui pendência de pagamento vencida no momento. Todos os clientes estão em dia ou com vencimentos futuros."
        linhas = [
            f"### ⚠️ Contratos em Atraso ({len(inadimplentes)} clientes)",
            f"Total em cobrança: **{formatar_moeda_brl(resumo_fin.faturamento_em_atraso)}**:\n"
        ]
        for ina in inadimplentes:
            dias = ina.dias_atraso or 0
            linhas.append(f"- **{ina.razao_social}** — **{formatar_moeda_brl(ina.valor_mensal)}** (+{dias} dias de atraso | Telefone: {ina.telefone})")
        linhas.append("\n👉 *Utilize o botão 'COBRAR' na tabela para enviar mensagem direta via WhatsApp corporativo.*")
        return "\n".join(linhas)

    # 5. LISTAR TODOS OS CLIENTES / LEADS
    if any(k in pergunta_lower for k in ["clientes", "listar clientes", "todos clientes", "quais clientes", "lista", "empresas", "base"]):
        linhas = [
            f"### 📋 Base Cadastral de Clientes ({len(leads)} contratos)",
            "| Código | Empresa | Mensalidade | Status | Método |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for l in leads:
            status_badge = f"**{l.status_pagamento}**"
            linhas.append(f"| `{l.codigo}` | {l.razao_social} | {formatar_moeda_brl(l.valor_mensal)} | {status_badge} | {l.metodo_pagamento} |")
        linhas.append(f"\n**Total da Carteira:** {formatar_moeda_brl(total_carteira)}")
        return "\n".join(linhas)

    # 6. CENTRAL DE APPS / SISTEMAS
    if any(k in pergunta_lower for k in ["app", "apps", "sistema", "sistemas", "central de apps", "rede", "rollout", "no ar"]):
        publicados = [a for a in apps if getattr(a, "estagio_deploy", "") == "PUBLICADO"]
        rollouts = [a for a in apps if getattr(a, "estagio_deploy", "") == "ROLLOUT"]
        linhas = [
            f"### 🌐 Central de Apps ({len(apps)} sistemas mapeados)",
            f"- **No Ar na Rede:** {len(publicados)} sistemas ativos",
            f"- **Em Rollout / Piloto:** {len(rollouts)} sistemas em implantação\n",
            "**Sistemas do Ecossistema:**"
        ]
        for a in apps:
            estagio = getattr(a, "estagio_deploy", "OPERACIONAL")
            url_info = f"({a.url_publica})" if getattr(a, "url_publica", None) else f"(Porta: {a.porta})"
            linhas.append(f"- `[{a.slug}]` **{a.nome}** — Estágio: `{estagio}` {url_info}")
        return "\n".join(linhas)

    # 7. ERROS / BUGS / ESTABILIDADE
    if any(k in pergunta_lower for k in ["erro", "erros", "bug", "bugs", "falha", "falhas", "anomalia"]):
        if not erros:
            return "### 🛡️ Estabilidade 100% Nominal\nNenhum erro ou bug ativo registrado na telemetria. Todos os aplicativos estão operando sem falhas."
        linhas = [
            f"### ⚠️ Incidentes Técnicos Ativos ({len(erros)} registros):",
        ]
        for err in erros:
            linhas.append(f"- `[{err.nivel}]` **{err.tipo_erro}** no app `{err.app_slug}`: {err.mensagem}")
        return "\n".join(linhas)

    # 8. BUSCA ESPECÍFICA DE CLIENTE PELO NOME OU CNPJ
    for lead in leads:
        nome_completo = (lead.razao_social or "").lower()
        fantasia = (lead.nome_fantasia or "").lower()
        doc = (lead.documento or "").lower()
        codigo = (lead.codigo or "").lower()

        palavras_empresa = [p for p in nome_completo.split() if len(p) > 3] + [p for p in fantasia.split() if len(p) > 3]

        if any(p in pergunta_lower for p in palavras_empresa) or doc in pergunta_lower or codigo in pergunta_lower:
            linhas = [
                f"### 🏢 Ficha de Cliente: {lead.razao_social}",
                f"- **Código:** `{lead.codigo}`",
                f"- **Nome Fantasia:** {lead.nome_fantasia or 'N/A'}",
                f"- **CNPJ/CPF:** `{lead.documento}`",
                f"- **Mensalidade:** **{formatar_moeda_brl(lead.valor_mensal)}**",
                f"- **Status:** **{lead.status_pagamento}**",
                f"- **Método:** {lead.metodo_pagamento}",
                f"- **Vencimento:** {lead.vencimento or 'A definir'}",
                f"- **Contato:** {lead.contato_nome} ({lead.telefone} | {lead.email})",
                f"- **Origem / Plano:** {lead.origem} | {lead.plano}",
                f"- **Observações:** {lead.observacoes or 'Sem observações'}"
            ]
            return "\n".join(linhas)

    # 9. RESPOSTA PADRÃO CONTEXTUALIZADA
    return (
        f"### 🤖 Copilot MalhaCore\n"
        f"Estou conectado diretamente à sua base de dados central. Atualmente temos **{len(leads)} clientes** cadastrados "
        f"e faturamento em carteira de **{formatar_moeda_brl(total_carteira)}** "
        f"({formatar_moeda_brl(resumo_fin.faturamento_liquidado)} liquidados e {formatar_moeda_brl(resumo_fin.faturamento_a_receber)} a receber).\n\n"
        f"**Consultas rápidas que posso responder:**\n"
        f"- *'Quais clientes estão pendentes?'*\n"
        f"- *'Quanto temos a receber?'*\n"
        f"- *'Como está a Activia Logística ou a Dra. Shirlei?'*\n"
        f"- *'Como estão os apps da Central?'*\n"
        f"- *'Tem algum erro no sistema?'*"
    )


def _consultar_gemini(
    pergunta: str,
    gemini_key: str,
    resumo_fin: Any,
    leads: List[Any],
    apps: List[Any],
    erros: List[Any]
) -> Optional[str]:
    """Chama a API do Google Gemini com todo o contexto do banco de dados injetado."""
    try:
        dados_leads = [
            {
                "codigo": l.codigo,
                "razao_social": l.razao_social,
                "valor_mensal": l.valor_mensal,
                "status": l.status_pagamento,
                "vencimento": l.vencimento,
                "contato": l.contato_nome,
                "telefone": l.telefone
            }
            for l in leads
        ]

        dados_apps = [
            {"slug": a.slug, "nome": a.nome, "estagio": getattr(a, "estagio_deploy", "OPERACIONAL")}
            for a in apps
        ]

        prompt_sistema = (
            "Você é o Copilot Executivo da plataforma MalhaCore, assistente do Tiago. "
            "Responda sempre em português do Brasil com clareza, objetividade e formatação em Markdown limpo (bullets e tabelas quando aplicável). "
            "DADOS AO VIVO DO SISTEMA:\n"
            f"- Faturamento Liquidado: R$ {resumo_fin.faturamento_liquidado:.2f}\n"
            f"- Faturamento a Receber: R$ {resumo_fin.faturamento_a_receber:.2f}\n"
            f"- Inadimplência: R$ {resumo_fin.faturamento_em_atraso:.2f}\n"
            f"- Total de Clientes: {len(leads)}\n"
            f"- Clientes:\n{json.dumps(dados_leads, ensure_ascii=False, indent=2)}\n"
            f"- Aplicativos no Ecossistema:\n{json.dumps(dados_apps, ensure_ascii=False, indent=2)}\n"
            f"- Erros Técnicos Ativos: {len(erros)}\n\n"
            f"Pergunta do Tiago: {pergunta}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        body = {
            "contents": [{
                "parts": [{"text": prompt_sistema}]
            }]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            texto = data["candidates"][0]["content"]["parts"][0]["text"]
            return texto.strip()
    except Exception as e:
        # Se a chave for inválida ou timeout, o motor nativo assume com perfeição
        return None
