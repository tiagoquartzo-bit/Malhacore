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
    const visoes = ['visaoFinanceiro', 'visaoApps', 'visaoErros', 'visaoAcessos'];
    const btns = {
        'visaoFinanceiro': 'btnVisaoFinanceiro',
        'visaoApps': 'btnVisaoApps',
        'visaoErros': 'btnVisaoErros',
        'visaoAcessos': 'btnVisaoAcessos'
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




