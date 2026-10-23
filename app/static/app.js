
const $ = selector => document.querySelector(selector);
let meta, rows = [], activeView = 'scout', query = new URLSearchParams();
let requestId = 0, loading = false, toastTimer;
let saved = readShortlist();

function candidateKey(row, model) {
    return `${row.player_id}-${row.season}-${row.scenario_club}-${model}`;
}

function readShortlist() {
    try {
        const records = JSON.parse(localStorage.getItem('transferlens-shortlist') || '[]');
        if (!Array.isArray(records)) return [];
        const seen = new Set();
        return records.filter(row => {
            if (!row || typeof row !== 'object') return false;
            const textFields = ['player_name', 'position', 'origin_club', 'scenario_club', 'key'];
            const numberFields = ['player_id', 'season', 'age', 'pre_minutes', 'prediction', 'persistence', 'context_prediction'];
            if (!textFields.every(field => typeof row[field] === 'string')) return false;
            if (!numberFields.every(field => Number.isFinite(row[field]))) return false;
            if (![2023, 2024].includes(row.season)) return false;
            if (!['individual_rf', 'formation_rf'].includes(row.model)) return false;
            if (row.key !== candidateKey(row, row.model) || seen.has(row.key)) return false;
            seen.add(row.key);
            return true;
        });
    } catch {
        return [];
    }
}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const fmt=x=>Number(x).toFixed(3);

function toast(message, undo) {
    clearTimeout(toastTimer);
    const notice = $('#toast');
    notice.textContent = message;
    if (undo) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'toast-undo';
        button.textContent = 'Undo';
        button.onclick = () => {
            undo();
            toast('Shortlist restored');
        };
        notice.append(button);
    }
    notice.style.display = 'block';
    toastTimer = setTimeout(() => notice.style.display = 'none', undo ? 7000 : 2300);
}
function persist(){try{localStorage.setItem('transferlens-shortlist',JSON.stringify(saved))}catch{toast('Browser storage unavailable; shortlist lasts this session.')}$('#saved-count').textContent=saved.length;$('#clear-saved').disabled=saved.length===0}

function updateDetailSave(row) {
    const button = $('#detail-save');
    if (!button || Number(button.dataset.player) !== row.player_id) return;
    const selected = saved.some(item => item.key === candidateKey(row, query.get('model')));
    button.textContent = selected ? '★ Remove from shortlist' : '☆ Save candidate';
    button.setAttribute('aria-pressed', String(selected));
}

function saveRow(id) {
    const row = rows.find(item => item.player_id === id);
    if (!row || loading) return;
    const key = candidateKey(row, query.get('model'));
    const index = saved.findIndex(item => item.key === key);
    if (index >= 0) {
        saved.splice(index, 1);
        toast('Removed from shortlist');
    } else {
        saved.push({...row, key, model: query.get('model')});
        toast('Candidate saved');
    }
    persist();
    renderRows();
    updateDetailSave(row);
}

function removeSaved(index) {
    const previous = saved.slice();
    saved.splice(index, 1);
    persist();
    renderSaved();
    renderRows();
    toast('Candidate removed', () => {
        saved = previous;
        persist();
        renderSaved();
        renderRows();
    });
}

function clearShortlist() {
    if (!saved.length) return;
    const previous = saved.slice();
    saved = [];
    persist();
    renderSaved();
    renderRows();
    toast('Shortlist cleared', () => {
        saved = previous;
        persist();
        renderSaved();
        renderRows();
    });
}
function updateClubs(){if(!meta)return;const old=$('#club').value;const season=Number($('#filters').elements.season.value);$('#club').innerHTML='<option value="">Recorded destination</option>'+meta.clubs.filter(c=>c.season===season).map(c=>`<option value="${c.to_club_id}">${esc(c.destination_club)}</option>`).join('');if([...$('#club').options].some(o=>o.value===old))$('#club').value=old}
function renderRows(){const filtered=rows.filter(r=>r.player_name.toLowerCase().includes($('#search').value.trim().toLowerCase()));$('#result-count').textContent=filtered.length;$('#export').disabled=loading||filtered.length===0;$('#players').innerHTML=filtered.length?filtered.map((r,i)=>{const key=candidateKey(r,query.get('model'));const selected=saved.some(item=>item.key===key);return `<tr><td>${String(i+1).padStart(2,'0')}</td><td><span class="avatar">${esc(r.player_name.split(' ').map(x=>x[0]).slice(0,2).join(''))}</span><button class="player" data-player="${r.player_id}">${esc(r.player_name)}</button><div class="player-meta">${esc(r.origin_club)} · ${esc(r.position)}</div></td><td>${r.age.toFixed(0)}</td><td>${fmt(r.persistence)}</td><td class="prediction">${fmt(r.prediction)}<span class="mini-bar"><i style="width:${Math.min(100,r.prediction*100)}%"></i></span></td><td><button class="save ${selected?'selected':''}" data-save="${r.player_id}" aria-pressed="${selected}" aria-label="${selected?'Remove':'Save'} ${esc(r.player_name)} ${selected?'from':'to'} shortlist">${selected?'★':'☆'}</button></td></tr>`}).join(''):'<tr><td colspan="6" class="empty">No candidates match this brief. Adjust the filters.</td></tr>';$('#result-note').textContent=`${filtered.length} candidates · Historical snapshot · Not a transfer guarantee`;$('#players').querySelectorAll('[data-player]').forEach(b=>b.onclick=()=>profile(Number(b.dataset.player)));$('#players').querySelectorAll('[data-save]').forEach(b=>b.onclick=()=>saveRow(Number(b.dataset.save)))}

async function load() {
    const id = ++requestId;
    const nextQuery = new URLSearchParams(new FormData($('#filters')));
    loading = true;
    rows = [];
    $('#error').hidden = true;
    $('#filters .primary').disabled = true;
    $('#export').disabled = true;
    $('#result-count').textContent = '—';
    $('#players').innerHTML = '<tr><td colspan="6" class="empty">Finding candidates…</td></tr>';
    $('#result-note').textContent = 'Loading candidates…';
    $('.table-wrap').setAttribute('aria-busy', 'true');
    try {
        const response = await fetch('/api/rank?' + nextQuery);
        const data = await response.json();
        if (id !== requestId) return;
        if (!response.ok) throw Error(data.error || 'Request failed');
        query = nextQuery;
        rows = data.rows;
        $('#result-context').textContent = `${data.context} · ${query.get('model') === 'individual_rf' ? 'Individual RF' : 'RF + formations'}`;
    } catch (error) {
        if (id !== requestId) return;
        rows = [];
        $('#error').textContent = error.message;
        $('#error').hidden = false;
        $('#result-context').textContent = 'Could not load candidates. Try again.';
    } finally {
        if (id === requestId) {
            loading = false;
            $('#filters .primary').disabled = false;
            $('.table-wrap').setAttribute('aria-busy', 'false');
            renderRows();
        }
    }
}
function profile(id){const r=rows.find(x=>x.player_id===id);if(!r)return;$('#detail-content').innerHTML=`<h2 id="detail-name" class="detail-name">${esc(r.player_name)}</h2><p class="detail-meta">${esc(r.position)} · ${r.age.toFixed(1)} years · ${esc(r.origin_club)}</p><div class="score-row"><div><small>INDIVIDUAL RF</small><strong>${fmt(r.individual_prediction)}</strong></div><div><small>RF + FORMATIONS</small><strong>${fmt(r.context_prediction)}</strong></div><div><small>PRIOR GA90</small><strong>${fmt(r.persistence)}</strong></div></div><p class="detail-lines">Scenario destination: <b>${esc(r.scenario_club)}</b><br>Historical transfer: ${esc(r.transfer_date)} → ${esc(r.destination_club)}<br>Last player input: ${esc(r.pre_last_date)}<br>Last club context: ${esc(r.context_last_date)}</p><table class="detail-table"><tr><td>Prior goals / 90</td><td>${fmt(r.pre_goals90)}</td></tr><tr><td>Prior assists / 90</td><td>${fmt(r.pre_assists90)}</td></tr><tr><td>Prior minutes / appearances</td><td>${r.pre_minutes} / ${r.pre_appearances}</td></tr><tr><td>4-3-3 / 4-2-3-1 / 4-4-2 share</td><td>${(r.share_433*100).toFixed(0)}% / ${(r.share_4231*100).toFixed(0)}% / ${(r.share_442*100).toFixed(0)}%</td></tr><tr><td>Formation data coverage</td><td>${(r.formation_coverage*100).toFixed(0)}%</td></tr></table><p class="detail-lines">${r.factual_context?`Observed GA90 at the recorded destination: <b>${fmt(r.observed_original_ga90)}</b>. This outcome is shown after inference and never supplied to either model.`:'Destination changed. No observed outcome exists for this scenario; this is an associative model estimate.'}</p><p class="hint">Club formations are a weak tactical proxy. GA90 does not measure defensive contribution, affordability or causal fit. Population RMSE is not an individual confidence interval.</p><button class="primary" id="detail-save" data-player="${r.player_id}">☆ Save or remove candidate</button>`;$('#detail-save').onclick=()=>saveRow(id);updateDetailSave(r);$('#detail').showModal()}
function renderSaved(){$('#saved-content').innerHTML=saved.length?`<div class="saved-grid">${saved.map((r,i)=>`<article class="saved-card"><small class="eyebrow">${esc(r.position)} · ${r.season}</small><h3>${esc(r.player_name)}</h3><p>${esc(r.origin_club)} → ${esc(r.scenario_club)}<br>${esc(r.model)}<br>Age ${r.age.toFixed(1)} · ${r.pre_minutes} prior minutes</p><strong>${fmt(r.prediction)}</strong> <small>predicted GA90</small><p>Previous GA90 ${fmt(r.persistence)}<br>Context prediction ${fmt(r.context_prediction)}</p><button class="secondary" data-remove="${i}" aria-label="Remove ${esc(r.player_name)} from shortlist">Remove</button></article>`).join('')}</div>`:'<p class="empty">Your shortlist is empty. Save candidates with ☆ in Discover players.</p>';$('#saved-content').querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>removeSaved(Number(b.dataset.remove)))}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{activeView=b.dataset.view;['scout','shortlist','evidence'].forEach(v=>$(`#${v}-view`).hidden=v!==activeView);document.querySelectorAll('[data-view]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});$('#breadcrumb').textContent={scout:'Discover players',shortlist:'My shortlist',evidence:'Model evidence'}[activeView];$('#page-title').textContent={scout:'Find your next signing.',shortlist:'Build a considered shortlist.',evidence:'See the evidence behind the score.'}[activeView];$('#page-desc').textContent={scout:'Explore real transfer candidates with transparent machine learning.',shortlist:'Compare saved candidates and keep the assumptions visible.',evidence:'Measured results, reproducible data and the limits of this prototype.'}[activeView];if(activeView==='shortlist')renderSaved()});
$('#filters').onsubmit=e=>{e.preventDefault();load()};$('#filters').elements.season.onchange=updateClubs;$('#filters').onreset=()=>setTimeout(()=>{$('#search').value='';updateClubs();load()},0);$('#search').oninput=renderRows;$('#export').onclick=()=>{const p=new URLSearchParams(query);p.set('search',$('#search').value);const a=document.createElement('a');a.href='/api/export?'+p;a.download='transferlens-candidates.csv';a.click()};$('#clear-saved').onclick=clearShortlist;$('#close-detail').onclick=()=>$('#detail').close();$('#detail').onclick=e=>{if(e.target===$('#detail'))$('#detail').close()};
(async()=>{try{const r=await fetch('/api/meta');if(!r.ok)throw Error('Could not load model metadata');meta=await r.json();updateClubs();persist();await load()}catch(e){$('#error').textContent=e.message;$('#error').hidden=false}})();
