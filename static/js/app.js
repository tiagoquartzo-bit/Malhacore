// MALHACORE - CONTROLADOR DE CLIENTE (SEM ÍCONES, ALTA PRECISÃO)

let statusAtivo = 'TODOS';
let buscaTermo = '';

document.addEventListener('DOMContentLoaded', () => {
    configurarFiltros();
    configurarBusca();
    configurarFormularioNovoLead();
    configurarFormularioEditarLead();
    configurarFormularioAlterarStatus();
    configurarFiltrosApps();
    configurarBuscaApps();
    configurarFiltrosErros();
    configurarBuscaErros();
    configurarFiltrosAcessos();
    configurarBuscaAcessos();
    verificarConexaoCentralApps(false);
});

function showToast(msg) {
    const toast = document.getElementById('toastMsg');
    if (!toast) return;
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3500);
}

function formatarMoeda(val) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
}

function configurarFiltros() {
    const pills = document.querySelectorAll('.filter-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            statusAtivo = pill.getAttribute('data-status');
            aplicarFiltrosNaTabela();
        });
    });
}

function configurarBusca() {
    const input = document.getElementById('inputBusca');
    if (!input) return;
    input.addEventListener('input', (e) => {
        buscaTermo = e.target.value.toLowerCase().trim();
        aplicarFiltrosNaTabela();
    });
}

function aplicarFiltrosNaTabela() {
    const rows = document.querySelectorAll('#tabelaLeads tbody tr.lead-row');
    let visiveis = 0;

    rows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        const rowBusca = row.getAttribute('data-search').toLowerCase();

        const matchStatus = (statusAtivo === 'TODOS') || (rowStatus === statusAtivo);
        const matchBusca = !buscaTermo || rowBusca.includes(buscaTermo);

        if (matchStatus && matchBusca) {
            row.style.display = '';
            visiveis++;
        } else {
            row.style.display = 'none';
        }
    });

    const contador = document.getElementById('contadorRegistros');
    if (contador) {
        contador.textContent = `${visiveis} REGISTROS ENCONTRADOS`;
    }
}

// Modal Novo Lead
function abrirModalNovoLead() {
    document.getElementById('modalNovoLead').classList.add('open');
}

function fecharModalNovoLead() {
    document.getElementById('modalNovoLead').classList.remove('open');
}

function configurarFormularioNovoLead() {
    const form = document.getElementById('formNovoLead');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);

        const payload = {
            razao_social: formData.get('razao_social'),
            nome_fantasia: formData.get('nome_fantasia') || null,
            documento: formData.get('documento'),
            contato_nome: formData.get('contato_nome'),
            contato_cargo: formData.get('contato_cargo') || 'Operações',
            email: formData.get('email'),
            telefone: formData.get('telefone'),
            origem: formData.get('origem') || 'App MalhaCore',
            plano: formData.get('plano') || 'Malha Enterprise',
            valor_mensal: parseFloat(formData.get('valor_mensal')) || 0,
            status_pagamento: formData.get('status_pagamento') || 'PENDENTE',
            metodo_pagamento: formData.get('metodo_pagamento') || 'PIX',
            vencimento: formData.get('vencimento') || null,
            vincular_app: formData.get('vincular_app') === 'true' || formData.get('vincular_app') === 'on',
            app_vinculado_slug: formData.get('app_vinculado_slug') || null,
            app_estagio_deploy: formData.get('app_estagio_deploy') || 'ROLLOUT',
            observacoes: formData.get('observacoes') || null
        };

        try {
            const resp = await fetch('/api/leads', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const err = await resp.json();
                alert(`Erro ao cadastrar: ${err.detail || 'Falha na validação'}`);
                return;
            }

            fecharModalNovoLead();
            showToast('CONTRATO / LEAD REGISTRADO NO LEDGER');
            setTimeout(() => window.location.reload(), 1200);
        } catch (error) {
            console.error(error);
            alert('Erro de conexão ao salvar lead.');
        }
    });
}

// Alteração de Status (Baixa / Regularização)
async function registrarBaixaPagamento(leadId, codigo) {
    const confirmacao = confirm(`CONFIRMAR BAIXA MANUAL DE PAGAMENTO:\n\nLead: ${codigo}\nStatus atual passará para: [ PAGO ]`);
    if (!confirmacao) return;

    try {
        const resp = await fetch(`/api/leads/${leadId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status_pagamento: 'PAGO',
                motivo_baixa: 'Baixa manual confirmada pela controladoria'
            })
        });

        if (!resp.ok) {
            alert('Falha ao registrar baixa.');
            return;
        }

        showToast(`LIQUIDAÇÃO REGISTRADA COM SUCESSO: ${codigo}`);
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        console.error(err);
        alert('Erro ao processar comunicação com o servidor.');
    }
}

// Cobrança WhatsApp (Texto sério, corporativo, sem emojis ou ícones)
function enviarCobrancaWhatsApp(telefone, razaoSocial, valor, codigo) {
    const numLimpo = telefone.replace(/\D/g, '');
    const msg = encodeURIComponent(
        `Prezados da ${razaoSocial},\n\n` +
        `Notificação de faturamento MalhaCore [Ref: ${codigo}].\n` +
        `Identificamos fatura em aberto no valor de ${formatarMoeda(valor)}.\n` +
        `Solicitamos envio do comprovante para conciliação contábil.\n\n` +
        `Controladoria MalhaCore.`
    );
    window.open(`https://wa.me/55${numLimpo}?text=${msg}`, '_blank');
}

// ==========================================
// DETALHES, AUDITORIA & EDIÇÃO DO LEAD
// ==========================================
let leadAtualId = null;
let leadAtualCodigo = '';
let leadAtualRazao = '';

function trocarAbaDetalhes(abaId) {
    const tabs = ['abaFicha', 'abaStatus', 'abaAuditoria'];
    const btns = {
        'abaFicha': 'tabBtnFicha',
        'abaStatus': 'tabBtnStatus',
        'abaAuditoria': 'tabBtnAuditoria'
    };

    tabs.forEach(tab => {
        const el = document.getElementById(tab);
        if (el) el.classList.remove('active');
        const btn = document.getElementById(btns[tab]);
        if (btn) btn.classList.remove('active');
    });

    const activeEl = document.getElementById(abaId);
    if (activeEl) activeEl.classList.add('active');
    const activeBtn = document.getElementById(btns[abaId]);
    if (activeBtn) activeBtn.classList.add('active');
}

async function abrirModalDetalhes(leadId) {
    leadAtualId = leadId;
    trocarAbaDetalhes('abaFicha');

    try {
        const resp = await fetch(`/api/leads/${leadId}`);
        if (!resp.ok) {
            alert('Não foi possível carregar os dados do lead.');
            return;
        }

        const lead = await resp.json();
        leadAtualCodigo = lead.codigo;
        leadAtualRazao = lead.razao_social;

        // Cabeçalho do modal
        document.getElementById('detalhesCodigoBadge').textContent = lead.codigo;
        document.getElementById('detalhesRazaoTitulo').textContent = lead.razao_social;

        // Ficha Cadastral (Inputs)
        document.getElementById('editLeadId').value = lead.id;
        document.getElementById('editRazaoSocial').value = lead.razao_social || '';
        document.getElementById('editNomeFantasia').value = lead.nome_fantasia || '';
        document.getElementById('editDocumento').value = lead.documento || '';
        document.getElementById('editContatoNome').value = lead.contato_nome || '';
        document.getElementById('editContatoCargo').value = lead.contato_cargo || '';
        document.getElementById('editEmail').value = lead.email || '';
        document.getElementById('editTelefone').value = lead.telefone || '';
        document.getElementById('editOrigem').value = lead.origem || '';
        document.getElementById('editPlano').value = lead.plano || '';
        document.getElementById('editValorMensal').value = lead.valor_mensal || 0;
        document.getElementById('editVencimento').value = lead.vencimento || '';
        document.getElementById('editObservacoes').value = lead.observacoes || '';

        // Aba Status
        const statusBadge = document.getElementById('detalhesStatusBadge');
        statusBadge.textContent = lead.status_pagamento;
        statusBadge.className = `badge-status ${lead.status_pagamento.toLowerCase()}`;

        document.getElementById('detalhesDataPagamento').textContent = lead.data_pagamento || 'NÃO LIQUIDADO';
        document.getElementById('detalhesDiasAtraso').textContent = lead.dias_atraso > 0 ? `+${lead.dias_atraso} DIAS DE ATRASO` : 'EM DIA';

        document.getElementById('novoStatusSelect').value = lead.status_pagamento;
        document.getElementById('novoMetodoSelect').value = lead.metodo_pagamento || 'PIX';
        document.getElementById('novoMotivoStatus').value = '';

        // Carregar Histórico de Auditoria
        await carregarAuditoriaLead(leadId);

        document.getElementById('modalDetalhesLead').classList.add('open');
    } catch (err) {
        console.error(err);
        alert('Erro ao carregar dados do lead.');
    }
}

function fecharModalDetalhes() {
    document.getElementById('modalDetalhesLead').classList.remove('open');
    leadAtualId = null;
}

async function carregarAuditoriaLead(leadId) {
    const tbody = document.getElementById('listaAuditoriaLead');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-tertiary);">Carregando trilha de auditoria...</td></tr>';

    try {
        const resp = await fetch(`/api/leads/${leadId}/auditoria`);
        if (!resp.ok) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-tertiary);">Sem histórico disponível.</td></tr>';
            return;
        }

        const logs = await resp.json();
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-tertiary);">Nenhum registro de auditoria.</td></tr>';
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const dataFmt = log.criado_em ? log.criado_em.replace('T', ' ').substring(0, 16) : '-';
            const dePara = log.status_anterior ? `${log.status_anterior} &rarr; ${log.status_novo}` : log.status_novo;
            return `
                <tr>
                    <td class="mono" style="font-size: 10px;">${dataFmt}</td>
                    <td class="mono" style="font-weight: 700; color: #FFFFFF;">${log.tipo_evento}</td>
                    <td><span class="badge-status ${log.status_novo.toLowerCase()}" style="font-size: 9px; padding: 1px 5px;">${dePara}</span></td>
                    <td class="mono">R$ ${Number(log.valor || 0).toFixed(2)}</td>
                    <td style="color: var(--text-tertiary); font-size: 10px;">${log.responsavel}</td>
                    <td style="color: var(--text-primary); font-size: 11px;">${log.detalhes || '-'}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error(err);
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-tertiary);">Erro ao carregar auditoria.</td></tr>';
    }
}

function configurarFormularioEditarLead() {
    const form = document.getElementById('formEditarLead');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!leadAtualId) return;

        const formData = new FormData(form);
        const payload = {
            razao_social: formData.get('razao_social'),
            nome_fantasia: formData.get('nome_fantasia') || null,
            documento: formData.get('documento'),
            contato_nome: formData.get('contato_nome'),
            contato_cargo: formData.get('contato_cargo') || null,
            email: formData.get('email'),
            telefone: formData.get('telefone'),
            origem: formData.get('origem') || null,
            plano: formData.get('plano') || null,
            valor_mensal: parseFloat(formData.get('valor_mensal')) || 0,
            vencimento: formData.get('vencimento') || null,
            observacoes: formData.get('observacoes') || null,
            motivo_alteracao: 'Atualização cadastral realizada via painel'
        };

        try {
            const resp = await fetch(`/api/leads/${leadAtualId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) {
                const err = await resp.json();
                alert(`Erro ao atualizar: ${err.detail || 'Falha na requisição'}`);
                return;
            }

            fecharModalDetalhes();
            showToast(`DADOS ATUALIZADOS COM SUCESSO: ${leadAtualCodigo}`);
            setTimeout(() => window.location.reload(), 1200);
        } catch (error) {
            console.error(error);
            alert('Erro de conexão ao salvar alterações.');
        }
    });
}

function configurarFormularioAlterarStatus() {
    const form = document.getElementById('formAlterarStatus');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!leadAtualId) return;

        const formData = new FormData(form);
        const novoStatus = formData.get('status_pagamento');
        const novoMetodo = formData.get('metodo_pagamento');
        const motivo = formData.get('motivo_baixa');

        try {
            const resp = await fetch(`/api/leads/${leadAtualId}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    status_pagamento: novoStatus,
                    metodo_pagamento: novoMetodo,
                    motivo_baixa: motivo
                })
            });

            if (!resp.ok) {
                const err = await resp.json();
                alert(`Erro ao alterar status: ${err.detail || 'Falha na requisição'}`);
                return;
            }

            fecharModalDetalhes();
            showToast(`STATUS ATUALIZADO PARA [ ${novoStatus} ]: ${leadAtualCodigo}`);
            setTimeout(() => window.location.reload(), 1200);
        } catch (error) {
            console.error(error);
            alert('Erro ao alterar status financeiro.');
        }
    });
}

async function excluirLeadAtual() {
    if (!leadAtualId) return;

    const confirmacao = confirm(
        `ATENÇÃO: EXCLUSÃO DE CONTRATO\n\n` +
        `Lead: ${leadAtualCodigo} - ${leadAtualRazao}\n\n` +
        `Esta operação removerá o lead da listagem ativa e registrará o evento na auditoria.\n\n` +
        `Deseja prosseguir?`
    );

    if (!confirmacao) return;

    try {
        const resp = await fetch(`/api/leads/${leadAtualId}`, {
            method: 'DELETE'
        });

        if (!resp.ok) {
            alert('Não foi possível excluir o lead.');
            return;
        }

        fecharModalDetalhes();
        showToast(`LEAD EXCLUÍDO DO SISTEMA: ${leadAtualCodigo}`);
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        console.error(err);
        alert('Erro ao comunicar com o servidor.');
    }
}

// =========================================================================
// CONTROLE DE VISÕES PRINCIPAIS (COMANDO CENTRAL MULTI-APP)
// =========================================================================
function mudarVisaoPrincipal(visaoId) {
    const visoes = ['visaoFinanceiro', 'visaoApps', 'visaoErros', 'visaoAcessos', 'visaoCopilot'];
    const btns = {
        'visaoFinanceiro': 'btnVisaoFinanceiro',
        'visaoApps': 'btnVisaoApps',
        'visaoErros': 'btnVisaoErros',
        'visaoAcessos': 'btnVisaoAcessos',
        'visaoCopilot': 'btnVisaoCopilot'
    };

    visoes.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
        const btn = document.getElementById(btns[id]);
        if (btn) btn.classList.remove('active');
    });

    const activeEl = document.getElementById(visaoId);
    if (activeEl) activeEl.style.display = 'block';

    const activeBtn = document.getElementById(btns[visaoId]);
    if (activeBtn) activeBtn.classList.add('active');

    if (visaoId === 'visaoApps') {
        verificarConexaoCentralApps(false);
    }
}

// =========================================================================
// FILTROS E BUSCA DO MONITOR DE ERROS
// =========================================================================
let filtroErroAtivo = 'TODOS';
let buscaErroTermo = '';
let appErroFiltro = null;

function configurarFiltrosErros() {
    const container = document.getElementById('filtroPillsErros');
    if (!container) return;

    const pills = container.querySelectorAll('.filter-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            filtroErroAtivo = pill.getAttribute('data-erro-filtro');
            aplicarFiltrosErros();
        });
    });
}

function configurarBuscaErros() {
    const input = document.getElementById('inputBuscaErros');
    if (!input) return;

    input.addEventListener('input', (e) => {
        buscaErroTermo = e.target.value.toLowerCase().trim();
        aplicarFiltrosErros();
    });
}

function filtrarErrosPorApp(appSlug) {
    appErroFiltro = appSlug;
    mudarVisaoPrincipal('visaoErros');
    const input = document.getElementById('inputBuscaErros');
    if (input) input.value = appSlug;
    buscaErroTermo = appSlug.toLowerCase();
    aplicarFiltrosErros();
}

function aplicarFiltrosErros() {
    const rows = document.querySelectorAll('#tabelaErros tbody tr.erro-row');
    let visiveis = 0;

    rows.forEach(row => {
        const rowNivel = row.getAttribute('data-nivel');
        const rowStatus = row.getAttribute('data-status');
        const rowSearch = row.getAttribute('data-search').toLowerCase();

        let matchFiltro = false;
        if (filtroErroAtivo === 'TODOS') matchFiltro = true;
        else if (filtroErroAtivo === 'CRITICAL' || filtroErroAtivo === 'ERROR' || filtroErroAtivo === 'WARNING') {
            matchFiltro = (rowNivel === filtroErroAtivo);
        } else if (filtroErroAtivo === 'NOVO' || filtroErroAtivo === 'RESOLVIDO') {
            matchFiltro = (rowStatus === filtroErroAtivo);
        }

        const matchBusca = !buscaErroTermo || rowSearch.includes(buscaErroTermo);

        if (matchFiltro && matchBusca) {
            row.style.display = '';
            visiveis++;
        } else {
            row.style.display = 'none';
        }
    });

    const contador = document.getElementById('contadorErros');
    if (contador) contador.textContent = `${visiveis} REGISTROS COLETADOS`;
}

// =========================================================================
// FILTROS E BUSCA DA AUDITORIA DE ACESSOS
// =========================================================================
let filtroAcessoAtivo = 'TODOS';
let buscaAcessoTermo = '';

function configurarFiltrosAcessos() {
    const container = document.getElementById('filtroPillsAcessos');
    if (!container) return;

    const pills = container.querySelectorAll('.filter-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            filtroAcessoAtivo = pill.getAttribute('data-acesso-filtro');
            aplicarFiltrosAcessos();
        });
    });
}

function configurarBuscaAcessos() {
    const input = document.getElementById('inputBuscaAcessos');
    if (!input) return;

    input.addEventListener('input', (e) => {
        buscaAcessoTermo = e.target.value.toLowerCase().trim();
        aplicarFiltrosAcessos();
    });
}

function aplicarFiltrosAcessos() {
    const rows = document.querySelectorAll('#tabelaAcessos tbody tr.acesso-row');
    let visiveis = 0;

    rows.forEach(row => {
        const statusCode = parseInt(row.getAttribute('data-status') || '200');
        const rowSearch = row.getAttribute('data-search').toLowerCase();

        let matchFiltro = false;
        if (filtroAcessoAtivo === 'TODOS') matchFiltro = true;
        else if (filtroAcessoAtivo === 'SUCESSO') matchFiltro = (statusCode < 400);
        else if (filtroAcessoAtivo === 'ERRO') matchFiltro = (statusCode >= 400);

        const matchBusca = !buscaAcessoTermo || rowSearch.includes(buscaAcessoTermo);

        if (matchFiltro && matchBusca) {
            row.style.display = '';
            visiveis++;
        } else {
            row.style.display = 'none';
        }
    });

    const contador = document.getElementById('contadorAcessos');
    if (contador) contador.textContent = `${visiveis} ACESSOS AUDITADOS`;
}

// =========================================================================
// INSPEÇÃO DE ERRO & BUG (MODAL COM TRACEBACK E RESOLUÇÃO)
// =========================================================================
let erroInspecionadoId = null;

async function abrirModalInspecionarErro(erroId) {
    erroInspecionadoId = erroId;

    try {
        const resp = await fetch(`/api/telemetria/erros/${erroId}`);
        if (!resp.ok) {
            alert('Não foi possível carregar os detalhes do erro.');
            return;
        }

        const erro = await resp.json();

        document.getElementById('inspErroId').textContent = erro.id;
        document.getElementById('inspAppNomeTitulo').textContent = `[ ${erro.app_slug} ] - ${erro.app_nome || ''}`;
        document.getElementById('inspTipoErro').textContent = erro.tipo_erro;

        const nivelBadge = document.getElementById('inspNivelBadge');
        nivelBadge.textContent = erro.nivel;
        nivelBadge.className = `badge-nivel ${erro.nivel.toLowerCase()}`;

        const statusBadge = document.getElementById('inspStatusBadge');
        statusBadge.textContent = erro.status;
        statusBadge.className = `badge-status ${erro.status === 'RESOLVIDO' ? 'pago' : 'inadimplente'}`;

        document.getElementById('inspRota').textContent = erro.rota_ou_funcao || 'Rotina Interna';
        document.getElementById('inspCliente').textContent = erro.cliente_afetado || 'Não especificado';
        document.getElementById('inspUsuario').textContent = erro.usuario_afetado || 'Não especificado';
        document.getElementById('inspRecorrencias').textContent = `${erro.recorrencias} Ocorrência(s)`;

        document.getElementById('inspMensagem').textContent = erro.mensagem;
        document.getElementById('inspTraceback').textContent = erro.traceback || 'Sem traceback registrado para esta exceção.';
        document.getElementById('inspSolucaoNota').value = erro.solucao_nota || '';

        document.getElementById('modalInspecionarErro').classList.add('open');
    } catch (err) {
        console.error(err);
        alert('Erro ao carregar detalhes do bug.');
    }
}

function fecharModalInspecionarErro() {
    document.getElementById('modalInspecionarErro').classList.remove('open');
    erroInspecionadoId = null;
}

async function atualizarStatusErroAtual(novoStatus) {
    if (!erroInspecionadoId) return;

    const nota = document.getElementById('inspSolucaoNota').value.trim();

    try {
        const resp = await fetch(`/api/telemetria/erros/${erroInspecionadoId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                status: novoStatus,
                solucao_nota: nota || `Status atualizado para ${novoStatus} via central MalhaCore`
            })
        });

        if (!resp.ok) {
            alert('Falha ao atualizar status do erro.');
            return;
        }

        fecharModalInspecionarErro();
        showToast(`BUG #${erroInspecionadoId} ATUALIZADO PARA: [ ${novoStatus} ]`);
        setTimeout(() => window.location.reload(), 1200);
    } catch (err) {
        console.error(err);
        alert('Erro de conexão ao atualizar status do bug.');
    }
}

// Modal Conectar App SDK
function abrirModalConectarApp() {
    document.getElementById('modalConectarApp').classList.add('open');
}

function fecharModalConectarApp() {
    document.getElementById('modalConectarApp').classList.remove('open');
}

// Verificação Ativa de Saúde Online (Ping HTTP)
async function checarHealthcheckOnline(slug) {
    showToast(`VERIFICANDO STATUS ONLINE DE [${slug.toUpperCase()}]...`);
    try {
        const resp = await fetch(`/api/telemetria/apps/${slug}/healthcheck`, {
            method: 'POST'
        });
        const data = await resp.json();
        if (data.status === 'sucesso') {
            showToast(`[${slug.toUpperCase()}] OPERACIONAL: ${data.latencia_ms}ms (HTTP ${data.http_status})`);
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showToast(`[${slug.toUpperCase()}] FALHA: ${data.mensagem}`);
            setTimeout(() => window.location.reload(), 2200);
        }
    } catch (err) {
        console.error(err);
        showToast(`ERRO AO CONECTAR COM A CENTRAL MALHACORE`);
    }
}

// =========================================================================
// FILTROS E BUSCA DO CATÁLOGO DE APLICATIVOS (CICLO DE VIDA & CLIENTES)
// =========================================================================
let filtroAppAtivo = 'TODOS';
let buscaAppTermo = '';

function configurarFiltrosApps() {
    const container = document.getElementById('filtroPillsApps');
    if (!container) return;

    const pills = container.querySelectorAll('.filter-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            filtroAppAtivo = pill.getAttribute('data-app-filtro');
            aplicarFiltrosApps();
        });
    });
}

function configurarBuscaApps() {
    const input = document.getElementById('inputBuscaApps');
    if (!input) return;

    input.addEventListener('input', (e) => {
        buscaAppTermo = e.target.value.toLowerCase().trim();
        aplicarFiltrosApps();
    });
}

function aplicarFiltrosApps() {
    const cards = document.querySelectorAll('#gridApps .app-card');
    let visiveis = 0;

    cards.forEach(card => {
        const estagio = card.getAttribute('data-estagio') || 'DESENVOLVIMENTO';
        const search = (card.getAttribute('data-search') || '').toLowerCase();

        let matchFiltro = (filtroAppAtivo === 'TODOS') || (estagio === filtroAppAtivo);
        let matchBusca = !buscaAppTermo || search.includes(buscaAppTermo);

        if (matchFiltro && matchBusca) {
            card.style.display = '';
            visiveis++;
        } else {
            card.style.display = 'none';
        }
    });

    const contador = document.getElementById('contadorApps');
    if (contador) {
        contador.textContent = `${visiveis} SISTEMAS CATALOGADOS`;
    }
}

// =========================================================================
// CONEXÃO AUTOMÁTICA DA CENTRAL DE APPS
// =========================================================================
async function verificarConexaoCentralApps(notificar = false) {
    try {
        const resp = await fetch('/api/telemetria/resumo');
        if (resp.ok) {
            const data = await resp.json();
            const statusEl = document.getElementById('statusConexaoApps');
            if (statusEl) {
                statusEl.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="live-indicator" style="background: var(--status-pago-text); box-shadow: 0 0 8px var(--status-pago-text);"></span>
                        <span style="font-weight: 700; color: #FFFFFF;">CENTRAL DE APPS CONECTADA (${data.total_apps} SISTEMAS)</span>
                        <span style="color: var(--text-secondary);">— DISPONIBILIDADE: ${data.taxa_disponibilidade}% | RESPOSTA NOMINAL</span>
                    </div>
                    <button class="btn btn-sm btn-outline-cyan" onclick="verificarConexaoCentralApps(true)" style="font-size: 10px; padding: 3px 8px;">REVERIFICAR CONEXÃO</button>
                `;
            }
            if (notificar) {
                showToast(`CENTRAL CONECTADA: ${data.total_apps} SISTEMAS SINCRONIZADOS (${data.taxa_disponibilidade}% ATIVO)`);
            }
        }
    } catch (err) {
        console.error('Falha ao verificar conexão com Central de Apps:', err);
        const statusEl = document.getElementById('statusConexaoApps');
        if (statusEl) {
            statusEl.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: var(--status-inadimplente-text); font-weight: 700;">[FALHA DE REDE] CENTRAL DE APPS DESCONECTADA</span>
                </div>
                <button class="btn btn-sm" onclick="verificarConexaoCentralApps(true)" style="font-size: 10px; padding: 3px 8px;">TENTAR NOVAMENTE</button>
            `;
        }
    }
}

// =========================================================================
// BRIEFING EXECUTIVO COM INTELIGÊNCIA ARTIFICIAL & SÍNTESE DE VOZ (PT-BR)
// =========================================================================
let synth = ('speechSynthesis' in window) ? window.speechSynthesis : null;
let currentUtterance = null;
let briefingDataCache = null;
let ptVoiceSelected = null;

function carregarVozes() {
    if (!synth) return;
    const voices = synth.getVoices();
    ptVoiceSelected = voices.find(v => v.lang === 'pt-BR' && (v.name.includes('Luciana') || v.name.includes('Maria') || v.name.includes('Google') || v.name.includes('Natural'))) ||
                      voices.find(v => v.lang === 'pt-BR') ||
                      voices.find(v => v.lang.startsWith('pt')) ||
                      null;
}

if (synth) {
    carregarVozes();
    if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = carregarVozes;
    }
}

async function abrirModalIABriefing() {
    const modal = document.getElementById('modalIABriefing');
    if (!modal) return;
    modal.classList.add('open');

    const speechBox = document.getElementById('iaSpeechBox');
    const kpiRow = document.getElementById('iaKpiRow');

    if (speechBox) {
        speechBox.innerHTML = '<div style="color: var(--text-tertiary); font-style: italic;">Carregando telemetria e sintetizando relatório executivo...</div>';
    }

    try {
        const resp = await fetch('/api/ia/briefing');
        if (!resp.ok) throw new Error('Falha na resposta da API de inteligência');
        const data = await resp.json();
        briefingDataCache = data;

        if (speechBox) {
            speechBox.innerHTML = `
                <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px; font-size: 11px; letter-spacing: 0.05em;">
                    DIAGNÓSTICO EXECUTIVO — ${data.timestamp} [${data.status}]
                </div>
                <div>${data.texto_fala}</div>
            `;
        }

        if (kpiRow && data.kpis) {
            kpiRow.innerHTML = `
                <div class="ia-kpi-chip">
                    <div class="label">Total Contratos</div>
                    <div class="val mono">${data.kpis.total_contratos}</div>
                </div>
                <div class="ia-kpi-chip">
                    <div class="label">Faturamento Carteira</div>
                    <div class="val mono" style="color: var(--accent-cyan); font-size: 13px;">${formatarMoeda(data.kpis.faturamento_carteira)}</div>
                </div>
                <div class="ia-kpi-chip">
                    <div class="label">Liquidado</div>
                    <div class="val mono" style="color: var(--status-pago-text); font-size: 13px;">${formatarMoeda(data.kpis.faturamento_liquidado)}</div>
                </div>
                <div class="ia-kpi-chip">
                    <div class="label">A Receber</div>
                    <div class="val mono" style="color: var(--status-pendente-text); font-size: 13px;">${formatarMoeda(data.kpis.faturamento_a_receber)}</div>
                </div>
                <div class="ia-kpi-chip">
                    <div class="label">Apps na Rede</div>
                    <div class="val mono">${data.kpis.apps_publicados} / ${data.kpis.total_apps}</div>
                </div>
                <div class="ia-kpi-chip">
                    <div class="label">Falhas / Erros</div>
                    <div class="val mono" style="color: ${data.kpis.erros_ativos > 0 ? 'var(--status-inadimplente-text)' : 'var(--status-pago-text)'};">${data.kpis.erros_ativos}</div>
                </div>
            `;
        }

        // Iniciar fala sintetizada automaticamente
        tocarAudioBriefing();
    } catch (err) {
        console.error('Erro ao abrir briefing IA:', err);
        if (speechBox) {
            speechBox.innerHTML = '<div style="color: var(--status-inadimplente-text);">Falha de comunicação com o motor de inteligência artificial MalhaCore.</div>';
        }
    }
}

function fecharModalIABriefing() {
    pararAudioBriefing();
    const modal = document.getElementById('modalIABriefing');
    if (modal) modal.classList.remove('open');
}

function tocarAudioBriefing(textoCustom = null) {
    if (!synth) {
        alert('Seu navegador não possui suporte à síntese de voz (Web Speech API).');
        return;
    }

    if (synth.paused && !textoCustom) {
        synth.resume();
        const visualizer = document.getElementById('iaAudioVisualizer');
        if (visualizer) visualizer.classList.add('speaking');
        atualizarBotoesAudio(true);
        return;
    }

    synth.cancel();

    const textoParaFalar = textoCustom || (briefingDataCache ? briefingDataCache.texto_fala : null);
    if (!textoParaFalar) return;

    if (!ptVoiceSelected) carregarVozes();

    currentUtterance = new SpeechSynthesisUtterance(textoParaFalar);
    currentUtterance.lang = 'pt-BR';
    if (ptVoiceSelected) {
        currentUtterance.voice = ptVoiceSelected;
    }
    currentUtterance.rate = 1.05;
    currentUtterance.pitch = 1.0;

    const visualizer = document.getElementById('iaAudioVisualizer');

    currentUtterance.onstart = () => {
        if (visualizer) visualizer.classList.add('speaking');
        atualizarBotoesAudio(true);
    };

    currentUtterance.onend = () => {
        if (visualizer) visualizer.classList.remove('speaking');
        atualizarBotoesAudio(false);
    };

    currentUtterance.onerror = (e) => {
        console.warn('Speech synthesis event:', e);
        if (visualizer) visualizer.classList.remove('speaking');
        atualizarBotoesAudio(false);
    };

    synth.speak(currentUtterance);
}

function pausarAudioBriefing() {
    if (!synth) return;
    if (synth.speaking) {
        synth.pause();
        const visualizer = document.getElementById('iaAudioVisualizer');
        if (visualizer) visualizer.classList.remove('speaking');
        const btnOuvir = document.getElementById('btnIaOuvir');
        if (btnOuvir) btnOuvir.textContent = '▶ RETOMAR';
    }
}

function reiniciarAudioBriefing() {
    if (!synth) return;
    synth.cancel();
    tocarAudioBriefing();
}

function pararAudioBriefing() {
    if (!synth) return;
    synth.cancel();
    const visualizer = document.getElementById('iaAudioVisualizer');
    if (visualizer) visualizer.classList.remove('speaking');
    atualizarBotoesAudio(false);
}

function atualizarBotoesAudio(falando) {
    const btnOuvir = document.getElementById('btnIaOuvir');
    if (btnOuvir) {
        btnOuvir.textContent = falando ? '▶ REPRODUZINDO...' : '▶ OUVIR';
    }
}

async function perguntarIA(event) {
    event.preventDefault();
    const input = document.getElementById('inputPerguntaIA');
    if (!input || !input.value.trim()) return;

    const pergunta = input.value.trim();
    input.value = '';

    const speechBox = document.getElementById('iaSpeechBox');
    if (speechBox) {
        speechBox.innerHTML = `
            <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px;">
                PERGUNTA: "${pergunta}"
            </div>
            <div style="color: var(--text-tertiary); font-style: italic;">Processando resposta executiva...</div>
        `;
    }

    try {
        const resp = await fetch('/api/ia/perguntar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pergunta: pergunta })
        });

        if (!resp.ok) throw new Error('Erro ao consultar IA');
        const data = await resp.json();

        if (speechBox) {
            speechBox.innerHTML = `
                <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px; font-size: 11px;">
                    RESPOSTA MALHACORE IA [${data.timestamp}]
                </div>
                <div style="color: #FFFFFF; font-size: 14px; line-height: 1.6;">${data.resposta}</div>
            `;
        }

        // Falar a resposta
        tocarAudioBriefing(data.resposta);
    } catch (err) {
        console.error(err);
        if (speechBox) {
            speechBox.innerHTML = '<div style="color: var(--status-inadimplente-text);">Não foi possível obter resposta no momento.</div>';
        }
    }
}

// Fechar com tecla ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modalCopilot = document.getElementById('modalCopilot');
        if (modalCopilot && modalCopilot.classList.contains('open')) {
            fecharModalCopilot();
        }
    }
});

// =========================================================================
// COPILOT MALHACORE - CONSULTAS À BASE DE DADOS (100% GRATUITO, SEM ÁUDIO)
// =========================================================================

function renderizarMarkdown(texto) {
    if (!texto) return '';
    let html = texto;

    // Escapar caracteres básicos
    html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Headers: ### Title
    html = html.replace(/^### (.*$)/gim, '<h3 style="color: var(--accent-cyan); margin: 8px 0 6px 0; font-size: 13.5px;">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h3 style="color: var(--accent-cyan); margin: 10px 0 6px 0; font-size: 14px;">$1</h3>');

    // Negrito: **text**
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong style="color: #FFFFFF;">$1</strong>');

    // Itálico: *text*
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Código inline: `code`
    html = html.replace(/`([^`]+)`/gim, '<code class="mono" style="background: rgba(0,210,211,0.1); color: var(--accent-cyan); padding: 2px 6px; border-radius: 3px; font-size: 11px;">$1</code>');

    // Listas: - item
    html = html.replace(/^\- (.*$)/gim, '<li style="margin-left: 18px; margin-bottom: 4px;">$1</li>');

    // Quebras de linha
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');

    return html;
}

async function processarConsultaCopilot(pergunta, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Bolha do usuário
    const bubbleUser = document.createElement('div');
    bubbleUser.className = 'copilot-bubble user';
    bubbleUser.innerHTML = `<div style="font-size: 11px; color: var(--accent-cyan); margin-bottom: 4px; font-weight: 700;">VOCÊ</div><div>${pergunta}</div>`;
    container.appendChild(bubbleUser);

    // Bolha temporária do assistente
    const bubbleAssist = document.createElement('div');
    bubbleAssist.className = 'copilot-bubble assistant';
    bubbleAssist.innerHTML = `<div style="font-size: 11px; color: var(--accent-cyan); margin-bottom: 4px; font-weight: 700;">COPILOT MALHACORE</div><div style="color: var(--text-tertiary); font-style: italic;">Consultando base de dados em tempo real...</div>`;
    container.appendChild(bubbleAssist);
    container.scrollTop = container.scrollHeight;

    try {
        const resp = await fetch('/api/ia/copilot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pergunta: pergunta })
        });

        if (!resp.ok) throw new Error('Falha ao processar consulta');
        const data = await resp.json();

        bubbleAssist.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 11px; color: var(--accent-cyan); font-weight: 700;">COPILOT MALHACORE [${data.timestamp || ''}]</span>
                <span class="mono" style="font-size: 10px; color: var(--text-tertiary);">${data.motor || 'NATIVO'}</span>
            </div>
            <div>${renderizarMarkdown(data.resposta)}</div>
        `;
    } catch (err) {
        console.error('Erro no Copilot:', err);
        bubbleAssist.innerHTML = `
            <div style="font-size: 11px; color: var(--status-inadimplente-text); font-weight: 700;">ERRO NA CONSULTA</div>
            <div style="color: var(--text-secondary);">Não foi possível consultar a base de dados no momento.</div>
        `;
    }

    container.scrollTop = container.scrollHeight;
}

function abrirModalCopilot() {
    const modal = document.getElementById('modalCopilot');
    if (modal) modal.classList.add('open');
    const input = document.getElementById('inputCopilotModal');
    if (input) setTimeout(() => input.focus(), 150);
}

function fecharModalCopilot() {
    const modal = document.getElementById('modalCopilot');
    if (modal) modal.classList.remove('open');
}

function submeterConsultaCopilot(e) {
    e.preventDefault();
    const input = document.getElementById('inputCopilotModal');
    if (!input || !input.value.trim()) return;
    const pergunta = input.value.trim();
    input.value = '';
    processarConsultaCopilot(pergunta, 'copilotModalMensagens');
}

function enviarPerguntaCopilot(pergunta) {
    const input = document.getElementById('inputCopilotModal');
    if (input) input.value = '';
    processarConsultaCopilot(pergunta, 'copilotModalMensagens');
}

function submeterConsultaCopilotView(e) {
    e.preventDefault();
    const input = document.getElementById('inputCopilotView');
    if (!input || !input.value.trim()) return;
    const pergunta = input.value.trim();
    input.value = '';
    processarConsultaCopilot(pergunta, 'copilotViewMensagens');
}

function enviarPerguntaCopilotView(pergunta) {
    const input = document.getElementById('inputCopilotView');
    if (input) input.value = '';
    processarConsultaCopilot(pergunta, 'copilotViewMensagens');
}

function limparChatCopilot() {
    const container = document.getElementById('copilotModalMensagens');
    if (container) {
        container.innerHTML = `
            <div class="copilot-bubble assistant">
                <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px; font-size: 11px;">
                    COPILOT MALHACORE — HISTÓRICO LIMPO
                </div>
                <div>Histórico reiniciado. Digite uma pergunta ou clique em um dos atalhos acima para consultar sua base de dados.</div>
            </div>
        `;
    }
}

function limparChatCopilotView() {
    const container = document.getElementById('copilotViewMensagens');
    if (container) {
        container.innerHTML = `
            <div class="copilot-bubble assistant">
                <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 6px; font-size: 11px;">
                    COPILOT MALHACORE — HISTÓRICO LIMPO
                </div>
                <div>Histórico reiniciado. Digite uma pergunta ou clique em um dos atalhos acima para consultar sua base de dados.</div>
            </div>
        `;
    }
}





