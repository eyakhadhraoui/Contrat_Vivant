// Data Store chargé dynamiquement depuis la base MySQL (DB-first, aucun tableau statique)
let sinistresData = [];
let contratsData = [];


document.addEventListener('DOMContentLoaded', initializeApp);

let authToken = localStorage.getItem('authToken') || null;
let authUser = localStorage.getItem('authUser') ? JSON.parse(localStorage.getItem('authUser')) : null;

let clientsData = [];

async function initializeApp() {
  if (!authToken) {
    window.location.href = '/login';
    return;
  }
  setUserInfo();
  await fetchBackendData();
  await fetchClients();
  await fetchInAppAlerts();
  renderSinistres();
  renderContrats();
  loadHistoriqueAudit();
}

function setUserInfo() {
  if (!authUser) return;
  const profileName = document.getElementById('profile-name');
  const profileAvatar = document.getElementById('profile-avatar');
  const profileRole = document.getElementById('profile-role');
  if (profileName) profileName.innerText = authUser.username;
  if (profileAvatar) profileAvatar.innerText = authUser.username.slice(0, 2).toUpperCase();

  const roleStr = (authUser.role || '').toLowerCase();
  const isAssurances = roleStr.includes('assurances');
  const isSinistres = roleStr.includes('sinistres');

  if (profileRole) {
    profileRole.innerText = isAssurances ? 'Gestionnaire Assurances' : 'Gestionnaire Sinistres';
  }

  const btnAddContrat = document.getElementById('btn-ajouter-contrat');
  const btnAddSinistre = document.getElementById('btn-declarer-sinistre');

  if (btnAddContrat) {
    if (isSinistres && !isAssurances) {
      btnAddContrat.disabled = true;
      btnAddContrat.style.opacity = '0.5';
      btnAddContrat.style.cursor = 'not-allowed';
      btnAddContrat.title = 'Réservé aux gestionnaires Assurances';
      btnAddContrat.onclick = (e) => { e.preventDefault(); alert('Réservé aux gestionnaires Assurances'); };
    } else {
      btnAddContrat.disabled = false;
      btnAddContrat.style.opacity = '1';
      btnAddContrat.style.cursor = 'pointer';
      btnAddContrat.title = '';
      btnAddContrat.onclick = () => openModal('modal-ajouter-contrat');
    }
  }

  if (btnAddSinistre) {
    if (isAssurances && !isSinistres) {
      btnAddSinistre.disabled = true;
      btnAddSinistre.style.opacity = '0.5';
      btnAddSinistre.style.cursor = 'not-allowed';
      btnAddSinistre.title = 'Réservé aux gestionnaires Sinistres';
      btnAddSinistre.onclick = (e) => { e.preventDefault(); alert('Réservé aux gestionnaires Sinistres'); };
    } else {
      btnAddSinistre.disabled = false;
      btnAddSinistre.style.opacity = '1';
      btnAddSinistre.style.cursor = 'pointer';
      btnAddSinistre.title = '';
      btnAddSinistre.onclick = () => openModal('modal-declarer-sinistre');
    }
  }
}


function getAuthHeaders() {
  const headers = {};
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }
  return headers;
}

function logoutAndRedirect() {
  localStorage.removeItem('authToken');
  localStorage.removeItem('authUser');
  authToken = null;
  authUser = null;
  window.location.href = '/login';
}

async function fetchWithAuth(url, options = {}) {
  options.headers = {
    ...options.headers,
    ...getAuthHeaders(),
  };

  const response = await fetch(url, options);
  if (response.status === 401) {
    logoutAndRedirect();
    return response;
  }
  return response;
}

// Tab Switcher
function switchTab(tabId, el) {
  document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
  document.querySelectorAll('.page-view').forEach(view => view.classList.remove('active'));

  if (el) el.classList.add('active');
  const target = document.getElementById(`page-${tabId}`);
  if (target) target.classList.add('active');

  if (tabId === 'historique') {
    loadHistoriqueAudit();
  }
}


// Format DT Currency
function formatDT(amount) {
  if (!amount && amount !== 0) return '0 DT';
  return Number(amount).toLocaleString('fr-FR') + ' DT';
}

// Fetch Backend API Data (DB-first depuis MySQL)
async function fetchBackendData() {
  try {
    const resSinistres = await fetchWithAuth('/api/sinistres');
    if (resSinistres.ok) {
      const data = await resSinistres.json();
      sinistresData = (data.sinistres || []).map(s => ({
        ...s,
        id: s.id,
        client: s.client || s.client_nom || 'Client Assuré',
        type: s.type || s.type_sinistre || 'Auto - Carambolage',
        contrat_id: s.contrat_id,
        montant_declare: parseFloat(s.montant_declare || 0),
        date: s.date || s.date_declaration || '',
        statut: s.statut || 'en_cours'
      }));
    } else {
      sinistresData = [];
      console.warn('Échec récupération sinistres, statut:', resSinistres.status);
    }
  } catch (e) {
    sinistresData = [];
    console.error("Erreur récupération sinistres depuis MySQL:", e);
  }

  try {
    const resContrats = await fetchWithAuth('/api/contrats');
    if (resContrats.ok) {
      const data = await resContrats.json();
      contratsData = (data.contrats || []).map(c => ({
        ...c,
        id: c.id,
        client: c.client || c.client_nom || c.client_id || 'Client Assuré',
        type: c.type || c.type_contrat || 'Auto',
        garantie_max: parseFloat(c.garantie_max || 0),
        statut: c.statut || 'actif',
        date_derniere_modif: c.date_derniere_modif || ''
      }));
    } else {
      contratsData = [];
      console.warn('Échec récupération contrats, statut:', resContrats.status);
    }
  } catch (e) {
    contratsData = [];
    console.error("Erreur récupération contrats depuis MySQL:", e);
  }

  renderSinistres();
  renderContrats();
  populateContratsSelect();
}



async function fetchClients() {
  try {
    const res = await fetchWithAuth('/api/clients');
    if (res.ok) {
      const data = await res.json();
      clientsData = data.clients || [];
    } else {
      clientsData = [];
      console.warn('Échec du chargement des clients, statut:', res.status);
    }
  } catch (e) {
    clientsData = [];
    console.warn("Échec du chargement des clients depuis l'API", e);
  } finally {
    populateClientsSelect();
    renderClients();
  }
}

function renderClients() {
  const tbody = document.getElementById('clients-table-body');
  if (!tbody) return;

  tbody.innerHTML = '';

  if (!clientsData || clientsData.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 24px; color:#94a3b8;">Aucun client trouvé dans la base MySQL.</td></tr>';
    const sub = document.getElementById('clients-count-subtitle');
    if (sub) sub.innerText = `0 client au total`;
    const kpiTotal = document.getElementById('kpi-clients-total');
    if (kpiTotal) kpiTotal.innerText = 0;
    const kpiVilles = document.getElementById('kpi-clients-villes');
    if (kpiVilles) kpiVilles.innerText = 0;
    const kpiDossiers = document.getElementById('kpi-clients-dossiers');
    if (kpiDossiers) kpiDossiers.innerText = 0;
    return;
  }

  const villesSet = new Set();

  clientsData.forEach(c => {
    const id = c.id || '';
    const nameStr = (c.prenom || c.nom) ? `${c.prenom || ''} ${c.nom || ''}`.trim() : (c.client || 'Client Assuré');
    const cin = c.cin || 'N/A';
    const email = c.email || 'N/A';
    const telephone = c.telephone || 'N/A';
    const adresse = c.adresse || 'Tunisie';

    if (c.adresse) villesSet.add(c.adresse);

    const dateCreation = c.date_creation ? String(c.date_creation).split('T')[0] : '2026-08-08';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-bold">${id}</td>
      <td class="cell-bold">${nameStr}</td>
      <td>${cin}</td>
      <td>${email}</td>
      <td>${telephone}</td>
      <td>${adresse}</td>
      <td>${dateCreation}</td>
    `;
    tbody.appendChild(tr);
  });

  const sub = document.getElementById('clients-count-subtitle');
  if (sub) sub.innerText = `${clientsData.length} clients au total`;
  const kpiTotal = document.getElementById('kpi-clients-total');
  if (kpiTotal) kpiTotal.innerText = clientsData.length;
  const kpiVilles = document.getElementById('kpi-clients-villes');
  if (kpiVilles) kpiVilles.innerText = villesSet.size || 1;
  const kpiDossiers = document.getElementById('kpi-clients-dossiers');
  if (kpiDossiers) kpiDossiers.innerText = contratsData ? contratsData.length : 0;
}

function populateClientsSelect() {
  const datalist = document.getElementById('clients-datalist');
  const select = document.getElementById('contrat-input-client');
  try {
    if (!clientsData || clientsData.length === 0) {
      if (datalist) datalist.innerHTML = '';
      if (select && select.tagName === 'SELECT') select.innerHTML = '<option value="">-- Aucun client trouvé en base --</option>';
      return;
    }
    const datalistOptions = clientsData.map(c => {
      if (!c) return '';
      const id = c.id || '';
      const prenom = c.prenom || '';
      const nom = c.nom || '';
      const nameStr = (prenom || nom) ? `${prenom} ${nom}`.trim() : (c.client || 'Client Assuré');
      return `<option value="${id} - ${nameStr}">${nameStr} (${c.adresse || c.email || 'Tunisie'})</option>
              <option value="${nameStr}">${id}</option>`;
    }).join('');
    if (datalist) datalist.innerHTML = datalistOptions;

    if (select && select.tagName === 'SELECT') {
      const selectOptions = clientsData.map(c => {
        const id = c.id || '';
        const nameStr = (c.prenom || c.nom) ? `${c.prenom || ''} ${c.nom || ''}`.trim() : (c.client || 'Client Assuré');
        return `<option value="${id}">${id} - ${nameStr}</option>`;
      }).join('');
      select.innerHTML = '<option value="">-- Sélectionner un client --</option>' + selectOptions;
    }
  } catch (e) {
    console.error("Erreur remplissage clients:", e);
  }
}

function populateContratsSelect() {
  const datalist = document.getElementById('contrats-datalist');
  const select = document.getElementById('sinistre-input-contrat');
  try {
    if (!contratsData || contratsData.length === 0) {
      if (datalist) datalist.innerHTML = '';
      if (select && select.tagName === 'SELECT') select.innerHTML = '<option value="">-- Aucun contrat disponible --</option>';
      return;
    }
    const datalistOptions = contratsData.map(c => {
      if (!c) return '';
      const id = c.id || '';
      const clientName = c.client || c.client_nom || 'Client Assuré';
      const typeStr = (c.type || c.type_contrat || 'auto').toUpperCase();
      return `<option value="${id} - ${clientName}">${typeStr} - Max: ${formatDT(c.garantie_max || 0)}</option>
              <option value="${id}">${clientName} (${typeStr})</option>`;
    }).join('');
    if (datalist) datalist.innerHTML = datalistOptions;

    if (select && select.tagName === 'SELECT') {
      const selectOptions = contratsData.map(c => {
        const id = c.id || '';
        const clientName = c.client || c.client_nom || 'Client Assuré';
        return `<option value="${id}">${id} - ${clientName}</option>`;
      }).join('');
      select.innerHTML = '<option value="">-- Sélectionner un contrat --</option>' + selectOptions;
    }
  } catch (e) {
    console.error("Erreur remplissage contrats:", e);
  }
}

function updateSinistreTypeSuggestions() {
  const contratInput = document.getElementById('sinistre-input-contrat');
  const typeSelect = document.getElementById('sinistre-input-type');
  if (!contratInput || !typeSelect) return;

  const rawVal = contratInput.value.trim().toLowerCase();
  const c = contratsData.find(item => item.id.toLowerCase().includes(rawVal) || (item.client && item.client.toLowerCase().includes(rawVal)));
  const cType = (c?.type || c?.type_contrat || 'auto').toLowerCase();

  if (cType.includes('auto')) {
    typeSelect.innerHTML = `
      <option value="Auto - Carambolage">Auto - Carambolage</option>
      <option value="Auto - Vol">Auto - Vol</option>
      <option value="Auto - Inondation">Auto - Inondation</option>
      <option value="Auto - Incendie">Auto - Incendie</option>
    `;
  } else if (cType.includes('habitation')) {
    typeSelect.innerHTML = `
      <option value="Habitation - Incendie">Habitation - Incendie</option>
      <option value="Habitation - Inondation">Habitation - Inondation</option>
      <option value="Habitation - Vol">Habitation - Vol</option>
      <option value="Habitation - Dégât des eaux">Habitation - Dégât des eaux</option>
    `;
  } else if (cType.includes('vie')) {
    typeSelect.innerHTML = `
      <option value="Vie - Hospitalisation">Vie - Hospitalisation</option>
      <option value="Vie - Décès">Vie - Décès</option>
      <option value="Vie - Invalidité">Vie - Invalidité</option>
    `;
  } else {
    typeSelect.innerHTML = `
      <option value="Sante - Soins">Sante - Soins</option>
      <option value="Sante - Hospitalisation">Sante - Hospitalisation</option>
    `;
  }
}


async function fetchInAppAlerts() {
  try {
    const res = await fetchWithAuth('/api/alerts');
    if (res.ok) {
      const data = await res.json();
      const alerts = data.alerts || [];
      const countBadge = document.getElementById('header-alert-count');
      if (countBadge) {
        if (alerts.length > 0) {
          countBadge.innerText = alerts.length;
          countBadge.style.display = 'inline-block';
        } else {
          countBadge.style.display = 'none';
        }
      }
    }
  } catch (e) {
    console.warn("Échec de la récupération des alertes in-app");
  }
}


function renderAnalysisResult(data, matchContrat) {
  const resultPanel = document.getElementById('analysis-result-panel');
  if (!resultPanel) return;

  const score = data.alert?.urgency_score ?? data.score ?? data.urgency_score ?? null;
  const urgencyLevel = data.alert?.urgency_level ?? data.urgency_level ?? data.urgency_level ?? 'N/A';
  const recommendationLabel = data.alert?.recommendation_label || data.recommendation?.label || data.recommendation?.detail || 'Aucune recommandation disponible';
  const resume = data.resume_dossier || data.alert?.explication_llm || 'Aucun résumé disponible.';
  const topFactors = data.alert?.top_factors || data.top_factors || [];
  const anomalies = data.alert?.anomalies || data.anomalies || [];

  document.getElementById('analysis-score').innerText = score !== null ? `${score}` : 'N/A';
  document.getElementById('analysis-urgency-level').innerText = urgencyLevel;
  document.getElementById('analysis-recommendation').innerText = recommendationLabel;
  document.getElementById('analysis-resume').innerText = resume;

  const factorsList = document.getElementById('analysis-factors');
  factorsList.innerHTML = '';
  if (topFactors.length === 0) {
    const li = document.createElement('li');
    li.innerText = 'Aucun facteur détecté.';
    factorsList.appendChild(li);
  } else {
    topFactors.slice(0, 5).forEach(factor => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${factor.label || factor.key}</strong> — score ${factor.subscore ?? factor.contribution ?? 'N/A'}%${factor.detail ? ` : ${factor.detail}` : ''}`;
      factorsList.appendChild(li);
    });
  }

  const anomaliesList = document.getElementById('analysis-anomalies');
  anomaliesList.innerHTML = '';
  if (anomalies.length === 0) {
    const li = document.createElement('li');
    li.innerText = 'Aucune anomalie majeure détectée.';
    anomaliesList.appendChild(li);
  } else {
    anomalies.slice(0, 5).forEach(item => {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${item.rule || item.label || 'Anomalie'}</strong> — ${item.detail || item.description || JSON.stringify(item)}`;
      anomaliesList.appendChild(li);
    });
  }

  document.getElementById('analyse-alert-title').innerText = `Contrat #${matchContrat.id} analysé`; 
  document.getElementById('analyse-alert-desc').innerText = `Score d'urgence ${score !== null ? score : 'N/A'} — niveau ${urgencyLevel}.`; 
  resultPanel.style.display = 'block';

  const iaPanel = document.getElementById('ia-capabilities-panel');
  if (iaPanel) iaPanel.style.display = 'block';
}

function renderAnalysisError(message) {
  const iaPanel = document.getElementById('ia-capabilities-panel');
  if (iaPanel) iaPanel.style.display = 'none';
  const resultPanel = document.getElementById('analysis-result-panel');
  if (!resultPanel) return;

  document.getElementById('analysis-score').innerText = '--';
  document.getElementById('analysis-urgency-level').innerText = 'Erreur';
  document.getElementById('analysis-recommendation').innerText = 'Analyse impossible';
  document.getElementById('analysis-resume').innerText = message;
  document.getElementById('analysis-factors').innerHTML = '<li>Impossible de récupérer les facteurs.</li>';
  document.getElementById('analysis-anomalies').innerHTML = '<li>Impossible de récupérer les anomalies.</li>';
  resultPanel.style.display = 'block';
}

// Render Sinistres Page
function renderSinistres() {
  const tbody = document.getElementById('sinistres-table-body');
  if (!tbody) return;

  tbody.innerHTML = '';

  let enCours = 0;
  let enTraitement = 0;
  let complete = 0;

  sinistresData.forEach(s => {
    if (s.statut === 'en_cours') enCours++;
    else if (s.statut === 'en_traitement') enTraitement++;
    else if (s.statut === 'complete' || s.statut === 'cloture') complete++;

    let badgeClass = 'badge-en-cours';
    let badgeText = 'En cours';
    if (s.statut === 'en_traitement') {
      badgeClass = 'badge-en-traitement';
      badgeText = 'En traitement';
    } else if (s.statut === 'complete' || s.statut === 'cloture') {
      badgeClass = 'badge-complete';
      badgeText = 'Complete';
    }

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-bold">${s.id}</td>
      <td class="cell-bold">${s.client}</td>
      <td>${s.type}</td>
      <td>${s.contrat_id}</td>
      <td class="cell-bold">${formatDT(s.montant_declare)}</td>
      <td>${s.date}</td>
      <td><span class="badge ${badgeClass}">${badgeText}</span></td>
      <td><button class="btn-modifier" onclick="openEditModal('sinistre', '${s.id}')">Modifier</button></td>
    `;
    tbody.appendChild(tr);

  });

  document.getElementById('sinistres-count-subtitle').innerText = `${sinistresData.length} dossiers au total`;
  document.getElementById('kpi-sinistres-encours').innerText = enCours;
  document.getElementById('kpi-sinistres-traitement').innerText = enTraitement;
  document.getElementById('kpi-sinistres-complete').innerText = complete;
}

// Render Contrats Page
function renderContrats() {
  const tbody = document.getElementById('contrats-table-body');
  if (!tbody) return;

  tbody.innerHTML = '';

  let actifs = 0;
  let suspendus = 0;
  let totalGarantie = 0;

  contratsData.forEach(c => {
    if (c.statut === 'actif') actifs++;
    else if (c.statut === 'suspendu') suspendus++;
    totalGarantie += Number(c.garantie_max || 0);

    let badgeClass = c.statut === 'actif' ? 'badge-actif' : 'badge-suspendu';
    let badgeText = c.statut === 'actif' ? 'Actif' : 'Suspendu';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="cell-bold">${c.id}</td>
      <td>${c.client}</td>
      <td>${c.type || 'Auto'}</td>
      <td class="cell-bold">${formatDT(c.garantie_max)}</td>
      <td><span class="badge ${badgeClass}">${badgeText}</span></td>
      <td>${c.date_derniere_modif}</td>
      <td><button class="btn-modifier" onclick="openEditModal('contrat', '${c.id}')">Modifier</button></td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('contrats-count-subtitle').innerText = `${contratsData.length} contrats au total`;
  document.getElementById('kpi-contrats-actifs').innerText = actifs;
  document.getElementById('kpi-contrats-suspendus').innerText = suspendus;
  document.getElementById('kpi-contrats-garantie').innerText = formatDT(totalGarantie);
}

// Analyse Action
async function runAnalyse() {
  const inputVal = document.getElementById('analyse-search-input').value.trim();
  if (!inputVal) return;

  // Find matching client or contract
  const matchContrat = contratsData.find(c => c.id.toLowerCase().includes(inputVal.toLowerCase()) || c.client.toLowerCase().includes(inputVal.toLowerCase())) || contratsData[0];
  const relatedSinistres = sinistresData.filter(s => s.contrat_id === matchContrat.id || s.client.toLowerCase().includes(inputVal.toLowerCase()));

  document.getElementById('analyse-alert-title').innerText = `Contrat #${matchContrat.id} - Analyse requise`;
  document.getElementById('analyse-alert-desc').innerText = `Dossier ${matchContrat.client} analysé avec succès par le moteur d'agent IA.`;
  document.getElementById('analyse-summary-title').innerText = `Synthese du dossier ${matchContrat.id}`;

  document.getElementById('summary-statut').innerText = matchContrat.statut === 'actif' ? 'Actif' : 'Suspendu';
  document.getElementById('summary-nb-sinistres').innerText = relatedSinistres.length;
  document.getElementById('summary-taux-alerte').innerText = relatedSinistres.length >= 2 ? '40%' : '0%';
  document.getElementById('summary-nb-docs').innerText = '3';
  document.getElementById('summary-date-dernier').innerText = relatedSinistres.length > 0 ? relatedSinistres[0].date : matchContrat.date_derniere_modif;

  const resultPanel = document.getElementById('analysis-result-panel');
  if (resultPanel) {
    resultPanel.style.display = 'none';
  }

  // Backend POST /api/analyser
  try {
    const res = await fetchWithAuth('/api/analyser', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token: authToken, contrat_id: matchContrat.id, modification_type: 'contrat' })
    });

    if (!res.ok) {
      const errText = await res.text();
      renderAnalysisError(`Erreur ${res.status} : ${errText}`);
      return;
    }

    const data = await res.json();
    renderAnalysisResult(data, matchContrat);
  } catch(e) {
    renderAnalysisError(e?.message || 'Erreur de connexion au serveur');
  }
}

// Modal Controls
async function openModal(id) {
  const m = document.getElementById(id);
  if (m) {
    m.classList.add('active');
    const today = new Date().toISOString().split('T')[0];
    const nextYear = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    if (id === 'modal-ajouter-contrat') {
      const inputId = document.getElementById('contrat-input-id');
      const inputDateDeb = document.getElementById('contrat-input-date-debut');
      const inputDateFin = document.getElementById('contrat-input-date-fin');
      if (inputId && !inputId.value) inputId.value = `CSTR${Math.floor(10000 + Math.random() * 90000)}`;
      if (inputDateDeb && !inputDateDeb.value) inputDateDeb.value = today;
      if (inputDateFin && !inputDateFin.value) inputDateFin.value = nextYear;

      await fetchClients();
      populateClientsSelect();
    } else if (id === 'modal-declarer-sinistre') {
      const inputId = document.getElementById('sinistre-input-id');
      const inputDate = document.getElementById('sinistre-input-date');
      const inputDateSin = document.getElementById('sinistre-input-date-sinistre');
      if (inputId && !inputId.value) inputId.value = `CSIN${Math.floor(10000 + Math.random() * 90000)}`;
      if (inputDate && !inputDate.value) inputDate.value = today;
      if (inputDateSin && !inputDateSin.value) inputDateSin.value = today;

      await fetchBackendData();
      populateContratsSelect();
      updateSinistreTypeSuggestions();
    }
  }
}




function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

function openEditModal(type, id) {
  document.getElementById('edit-item-type').value = type;
  document.getElementById('edit-item-id').value = id;
  const title = document.getElementById('edit-modal-title');
  const labelVal = document.getElementById('edit-label-valeur');
  const inputVal = document.getElementById('edit-input-valeur');
  const selectStatut = document.getElementById('edit-input-statut');
  const inputOpt1 = document.getElementById('edit-input-opt1');
  const inputOpt2 = document.getElementById('edit-input-opt2');
  const labelOpt1 = document.getElementById('edit-label-opt1');
  const labelOpt2 = document.getElementById('edit-label-opt2');
  const inputObs = document.getElementById('edit-input-observations');

  if (type === 'sinistre') {
    if (title) title.innerText = `Modifier le sinistre ${id}`;
    if (labelVal) labelVal.innerText = `Montant Déclaré (DT)`;
    if (labelOpt1) labelOpt1.innerText = `Type de Sinistre`;
    if (labelOpt2) labelOpt2.innerText = `Lieu du Sinistre`;

    const item = sinistresData.find(s => s.id === id);
    if (item) {
      if (selectStatut) selectStatut.value = item.statut || 'en_cours';
      if (inputVal) inputVal.value = item.montant_declare || 0;
      if (inputOpt1) inputOpt1.value = item.type || item.type_sinistre || '';
      if (inputOpt2) inputOpt2.value = item.lieu_sinistre || '';
      if (inputObs) inputObs.value = item.observations || '';
    }
  } else {
    if (title) title.innerText = `Modifier le contrat ${id}`;
    if (labelVal) labelVal.innerText = `Garantie Maximale (DT)`;
    if (labelOpt1) labelOpt1.innerText = `Prime Mensuelle (DT)`;
    if (labelOpt2) labelOpt2.innerText = `Franchise (DT)`;

    const item = contratsData.find(c => c.id === id);
    if (item) {
      if (selectStatut) selectStatut.value = item.statut || 'actif';
      if (inputVal) inputVal.value = item.garantie_max || 0;
      if (inputOpt1) inputOpt1.value = item.prime_mensuelle || '';
      if (inputOpt2) inputOpt2.value = item.franchise || '';
      if (inputObs) inputObs.value = item.observations || '';
    }
  }
  openModal('modal-edit-item');
}


// Form Handlers
async function handleCreateSinistre(e) {
  e.preventDefault();
  console.log(">>> [NETWORK HTTP POST] Submitting new sinistre...");

  const customId = document.getElementById('sinistre-input-id')?.value.trim();
  const rawContratVal = document.getElementById('sinistre-input-contrat').value.trim();
  let contrat_id = rawContratVal;
  const foundContrat = contratsData.find(c => c.id.toLowerCase() === rawContratVal.toLowerCase() || rawContratVal.startsWith(c.id) || (c.client && c.client.toLowerCase().includes(rawContratVal.toLowerCase())));
  if (foundContrat) {
    contrat_id = foundContrat.id;
  }

  const type_sinistre = document.getElementById('sinistre-input-type').value;
  const lieu_sinistre = document.getElementById('sinistre-input-lieu')?.value.trim();
  const montant_declare = parseFloat(document.getElementById('sinistre-input-montant').value);
  const date_sinistre = document.getElementById('sinistre-input-date-sinistre')?.value;
  const date_declaration = document.getElementById('sinistre-input-date').value || new Date().toISOString().split('T')[0];
  const responsabilitesSelect = document.getElementById('sinistre-input-responsabilite');
  const statutSelect = document.getElementById('sinistre-input-statut');
  const description = document.getElementById('sinistre-input-description')?.value;
  const observations = document.getElementById('sinistre-input-observations')?.value;

  if (!contrat_id) {
    alert("Veuillez saisir un N° de contrat ou choisir dans les suggestions.");
    return;
  }


  const sid = customId || `CSIN${String(sinistresData.length + 10).padStart(5, '0')}`;

  const payload = {
    id: sid,
    contrat_id: contrat_id,
    type_sinistre: type_sinistre,
    lieu_sinistre: lieu_sinistre || null,
    montant_declare: montant_declare,
    date_sinistre: date_sinistre || date_declaration,
    date_declaration: date_declaration,
    responsabilite: responsabilitesSelect ? responsabilitesSelect.value : 'indetermine',
    statut: statutSelect ? statutSelect.value : 'en_cours',
    description: description || null,
    observations: observations || null
  };

  try {
    const res = await fetchWithAuth('/api/sinistres', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      alert(`Échec de création du sinistre: ${data.detail || 'Erreur inconnue'}`);
      return;
    }

    closeModal('modal-declarer-sinistre');
    await fetchBackendData();
    fetchInAppAlerts();
    alert(`Sinistre ${sid} créé avec succès via HTTP POST réseau et enregistré dans MySQL !`);
  } catch(err) {
    alert(`Erreur réseau: ${err.message}`);
  }
}

async function handleCreateContrat(e) {
  e.preventDefault();
  console.log(">>> [NETWORK HTTP POST] Submitting new contrat...");

  const id = document.getElementById('contrat-input-id').value.trim();
  const numero_souscripteur = document.getElementById('contrat-input-souscripteur')?.value.trim();
  const rawClientVal = document.getElementById('contrat-input-client').value.trim();
  let client_id = rawClientVal;

  const foundClient = clientsData.find(c => {
    const full = `${c.prenom || ''} ${c.nom || ''}`.trim().toLowerCase();
    return c.id.toLowerCase() === rawClientVal.toLowerCase() ||
           full === rawClientVal.toLowerCase() ||
           rawClientVal.toLowerCase().includes(c.id.toLowerCase());
  });
  if (foundClient) {
    client_id = foundClient.id;
  } else if (!client_id && clientsData.length > 0) {
    client_id = clientsData[0].id;
  }

  const type_contrat = document.getElementById('contrat-input-type').value;
  const garantie_max = parseFloat(document.getElementById('contrat-input-garantie').value);
  const franchiseVal = document.getElementById('contrat-input-franchise')?.value;
  const primeMensVal = document.getElementById('contrat-input-prime-mensuelle')?.value;
  const primeAnnVal = document.getElementById('contrat-input-prime-annuelle')?.value;
  const dureeVal = document.getElementById('contrat-input-duree')?.value;

  const date_debut = document.getElementById('contrat-input-date-debut').value || new Date().toISOString().split('T')[0];
  const date_fin = document.getElementById('contrat-input-date-fin').value || new Date().toISOString().split('T')[0];
  const statut = document.getElementById('contrat-input-statut').value;
  const mode_paiement = document.getElementById('contrat-input-mode-paiement').value;
  const frequence_paiement = document.getElementById('contrat-input-frequence-paiement')?.value;
  const couverture = document.getElementById('contrat-input-couverture')?.value;
  const exclusions = document.getElementById('contrat-input-exclusions')?.value;
  const observations = document.getElementById('contrat-input-observations')?.value;

  if (!client_id) {
    alert("Veuillez saisir un nom ou identifiant de client.");
    return;
  }



  const payload = {
    id: id,
    numero_souscripteur: numero_souscripteur || null,
    client_id: client_id,
    type_contrat: type_contrat,
    garantie_max: garantie_max,
    franchise: franchiseVal ? parseFloat(franchiseVal) : null,
    prime_mensuelle: primeMensVal ? parseFloat(primeMensVal) : null,
    prime_annuelle: primeAnnVal ? parseFloat(primeAnnVal) : null,
    duree_mois: dureeVal ? parseInt(dureeVal) : 12,
    date_debut: date_debut,
    date_fin: date_fin,
    statut: statut,
    mode_paiement: mode_paiement,
    frequence_paiement: frequence_paiement || null,
    couverture: couverture || null,
    exclusions: exclusions || null,
    observations: observations || null
  };

  try {
    const res = await fetchWithAuth('/api/contrats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      alert(`Échec de création du contrat: ${data.detail || 'Erreur inconnue'}`);
      return;
    }

    closeModal('modal-ajouter-contrat');
    await fetchBackendData();
    fetchInAppAlerts();
    alert(`Contrat ${id} créé avec succès via HTTP POST réseau et enregistré dans MySQL !`);
  } catch(err) {
    alert(`Erreur réseau: ${err.message}`);
  }
}

async function handleUpdateItem(e) {
  e.preventDefault();
  console.log(">>> [NETWORK HTTP PUT] Submitting update item...");

  const type = document.getElementById('edit-item-type').value;
  const id = document.getElementById('edit-item-id').value;
  const newStatut = document.getElementById('edit-input-statut').value;
  const valInput = document.getElementById('edit-input-valeur').value;
  const opt1Input = document.getElementById('edit-input-opt1')?.value;
  const opt2Input = document.getElementById('edit-input-opt2')?.value;
  const obsInput = document.getElementById('edit-input-observations')?.value;

  const payload = { id: id, statut: newStatut, observations: obsInput || null };
  if (type === 'sinistre') {
    if (valInput) payload.montant_declare = parseFloat(valInput);
    if (opt1Input) payload.type_sinistre = opt1Input;
    if (opt2Input) payload.lieu_sinistre = opt2Input;
  } else {
    if (valInput) payload.garantie_max = parseFloat(valInput);
    if (opt1Input) payload.prime_mensuelle = parseFloat(opt1Input);
    if (opt2Input) payload.franchise = parseFloat(opt2Input);
  }

  const endpoint = type === 'sinistre' ? `/api/sinistres/modifier` : `/api/contrats/modifier`;

  try {
    const res = await fetchWithAuth(endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      alert(`Échec de modification: ${data.detail || 'Erreur inconnue'}`);
      return;
    }

    closeModal('modal-edit-item');
    await fetchBackendData();
    fetchInAppAlerts();
    alert(`Mise à jour de ${id} effectuée avec succès via HTTP PUT réseau et enregistrée dans MySQL !`);
  } catch(err) {
    alert(`Erreur réseau: ${err.message}`);
  }
}





// Chat RAG Assistant
function toggleChatDrawer() {
  const drawer = document.getElementById('chat-drawer');
  if (drawer) drawer.classList.toggle('active');
}

function handleChatKeyPress(e) {
  if (e.key === 'Enter') sendChatMessage();
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input-text');
  const msgText = input.value.trim();
  if (!msgText) return;

  const messagesBox = document.getElementById('chat-messages');

  // Append User Msg
  const userDiv = document.createElement('div');
  userDiv.className = 'chat-msg user';
  userDiv.innerText = msgText;
  messagesBox.appendChild(userDiv);
  input.value = '';
  messagesBox.scrollTop = messagesBox.scrollHeight;

  // Append Typing Assistant Msg
  const assistantDiv = document.createElement('div');
  assistantDiv.className = 'chat-msg assistant';
  assistantDiv.innerText = 'Recherche dans la base de connaissances RAG...';
  messagesBox.appendChild(assistantDiv);
  messagesBox.scrollTop = messagesBox.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msgText })
    });
    if (res.ok) {
      const data = await res.json();
      assistantDiv.innerText = data.reponse;
    } else {
      assistantDiv.innerText = "Une erreur s'est produite lors de la consultation RAG.";
    }
  } catch(e) {
    assistantDiv.innerText = "Mode démonstration : Réponse RAG local générée.";
  }
  messagesBox.scrollTop = messagesBox.scrollHeight;
}


// ==========================================================================
// HISTORIQUE D'AUDIT CHRONOLOGIQUE ET SUIVI INTER-SERVICES
// ==========================================================================

let rawAuditLogs = [];

async function loadHistoriqueAudit() {
  const tbody = document.getElementById('audit-table-body');
  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 32px; color: #94a3b8;">Chargement de l\'historique d\'audit...</td></tr>';
  }

  try {
    const resAudit = await fetchWithAuth('/api/audit');
    const resHist = await fetchWithAuth('/api/historique');

    let auditData = resAudit.ok ? await resAudit.json() : [];
    let histData = resHist.ok ? await resHist.json() : [];

    rawAuditLogs = [];

    // Normalisation des entrées du journal d'audit
    if (Array.isArray(auditData)) {
      auditData.forEach(item => {
        const stepName = item.step || 'unknown';
        const itemData = item.data || {};
        
        let typeCategory = 'agent';
        let badgeClass = 'agent';
        let actionTitle = stepName;
        let actionDetail = typeof itemData === 'string' ? itemData : JSON.stringify(itemData);
        let actor = itemData.gestionnaire_id || itemData.actor || 'Système Multi-Agents';
        let contratId = itemData.contrat_id || itemData.target_id || (itemData.sinistres_ids && itemData.sinistres_ids.length > 0 ? itemData.sinistres_ids[0] : 'CSTR00001');
        let statusText = itemData.status || itemData.urgency_level || 'EXÉCUTÉ';

        if (stepName.includes('collector') || stepName === 'collect_data') {
          typeCategory = 'collector';
          badgeClass = 'info';
          actionTitle = 'Collecte & Intégration SI (CollectorAgent)';
          actionDetail = `Contrat ${itemData.contrat_id || 'CSTR00001'} — ${itemData.nb_sinistres || 0} sinistre(s) associé(s)`;
        } else if (stepName.includes('risk') || stepName === 'cross_analysis' || stepName === 'urgency') {
          typeCategory = 'risk';
          badgeClass = itemData.urgency_level === 'eleve' || itemData.urgency_level === 'critique' ? 'error' : 'agent';
          actionTitle = 'Évaluation des Risques (RiskAnalysisAgent)';
          actionDetail = `Score d'urgence: ${itemData.score || itemData.urgency_score || 'N/A'} | Niveau: ${itemData.urgency_level || 'N/A'} | Règle: ${itemData.dominant_rule || 'N/A'}`;
        } else if (stepName.includes('alert') || stepName === 'routing' || stepName === 'cross_notify') {
          typeCategory = 'alert';
          badgeClass = 'alert';
          actionTitle = 'Structuration Alerte & Routage (AlertNotificationAgent)';
          actionDetail = itemData.raison || `Routé vers : ${(itemData.gestionnaires_noms || []).join(', ') || 'Gestionnaire'}`;
        } else if (stepName.includes('validation') || stepName === 'alert_validation_request') {
          typeCategory = 'validation';
          badgeClass = 'validation';
          actionTitle = 'Validation Humaine (HITL)';
          actionDetail = `Action: ${itemData.action || itemData.status || 'soumise'} | Commentaire: ${itemData.comment || 'Aucun'}`;
        } else if (stepName === 'history_update') {
          typeCategory = 'history';
          badgeClass = 'validation';
          actionTitle = 'Mise à jour Historique Timeline SI';
          actionDetail = `Statut: ${itemData.status || 'Historique mis à jour'}`;
        }

        rawAuditLogs.push({
          timestamp: item.timestamp ? item.timestamp.replace('T', ' ').substring(0, 19) : new Date().toISOString().replace('T', ' ').substring(0, 19),
          step: stepName,
          category: typeCategory,
          badgeClass: badgeClass,
          contrat_id: contratId,
          actor: actor,
          actionTitle: actionTitle,
          actionDetail: actionDetail,
          statusText: statusText
        });
      });
    }

    // Normalisation des entrées de l'historique validé
    if (Array.isArray(histData)) {
      histData.forEach(h => {
        rawAuditLogs.push({
          timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19),
          step: 'historique_valide',
          category: 'history',
          badgeClass: 'validation',
          contrat_id: h.contrat_id || 'CSTR00001',
          actor: `${h.valide_par_gestionnaire_id || 'Gestionnaire'} (${h.valide_par_role || 'assurances'})`,
          actionTitle: 'Validation & Mise à jour Timeline SI',
          actionDetail: `Statut validation: ${h.validation_status || 'Valide'} | Alerte: ${h.alert ? h.alert.urgency_level : 'traitee'}`,
          statusText: h.validation_status || 'VALIDE'
        });
      });
    }

    // Tri chronologique décroissant (plus récents en haut)
    rawAuditLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    // Mise à jour des compteurs statistiques
    updateAuditStats();

    // Rendu du tableau
    renderAuditTable(rawAuditLogs);

  } catch (err) {
    console.error('Erreur chargement audit:', err);
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 24px; color: #dc2626;">Erreur de connexion lors du chargement des journaux d\'audit.</td></tr>';
    }
  }
}

function updateAuditStats() {
  const statTotal = document.getElementById('audit-stat-total');
  const statValidations = document.getElementById('audit-stat-validations');
  const statAlerts = document.getElementById('audit-stat-alerts');
  const statAgents = document.getElementById('audit-stat-agents');

  if (statTotal) statTotal.innerText = rawAuditLogs.length;
  if (statValidations) {
    const valCount = rawAuditLogs.filter(e => e.category === 'validation' || e.category === 'history').length;
    statValidations.innerText = valCount;
  }
  if (statAlerts) {
    const alertCount = rawAuditLogs.filter(e => e.category === 'alert').length;
    statAlerts.innerText = alertCount;
  }
  if (statAgents) {
    const agentCount = rawAuditLogs.filter(e => e.category === 'collector' || e.category === 'risk').length;
    statAgents.innerText = agentCount;
  }
}

function renderAuditTable(logs) {
  const tbody = document.getElementById('audit-table-body');
  if (!tbody) return;

  if (logs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 32px; color: #94a3b8;">Aucun événement d\'audit disponible.</td></tr>';
    return;
  }

  tbody.innerHTML = logs.map(item => `
    <tr>
      <td class="audit-time">${item.timestamp}</td>
      <td><span class="audit-badge ${item.badgeClass}">${item.step}</span></td>
      <td><strong>${item.contrat_id}</strong></td>
      <td>${item.actor}</td>
      <td>
        <div class="audit-action-title">${item.actionTitle}</div>
        <div class="audit-action-detail">${item.actionDetail}</div>
      </td>
      <td><span class="status-badge ${item.badgeClass === 'error' ? 'escalade' : 'complete'}">${item.statusText}</span></td>
    </tr>
  `).join('');
}

function filterAuditTable() {
  const searchInput = document.getElementById('audit-search-input');
  const stepFilter = document.getElementById('audit-filter-step');

  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
  const selectedStep = stepFilter ? stepFilter.value.toLowerCase() : '';

  const filtered = rawAuditLogs.filter(item => {
    const matchesSearch = !query || 
      item.contrat_id.toLowerCase().includes(query) ||
      item.actor.toLowerCase().includes(query) ||
      item.step.toLowerCase().includes(query) ||
      item.actionTitle.toLowerCase().includes(query) ||
      item.actionDetail.toLowerCase().includes(query);

    const matchesStep = !selectedStep || item.category === selectedStep;

    return matchesSearch && matchesStep;
  });

  renderAuditTable(filtered);
}

