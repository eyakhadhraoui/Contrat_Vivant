import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { sinistresAPI } from '../services/api';

export default function SinistresView({ sinistres, contrats, onRefresh }) {
  const { isAssurances, isSinistres } = useAuth();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedSinistre, setSelectedSinistre] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const [formData, setFormData] = useState({
    id: '',
    contrat_id: '',
    type: 'Auto - Carambolage',
    lieu: 'Tunis Centre',
    montant_declare: '1500',
    date_sinistre: new Date().toISOString().split('T')[0],
    date: new Date().toISOString().split('T')[0],
    responsabilite: 'indetermine',
    statut: 'en_cours',
    description: '',
    observations: '',
  });

  const formatDT = (val) => {
    if (!val && val !== 0) return '0 DT';
    return Number(val).toLocaleString('fr-FR') + ' DT';
  };

  const kpis = {
    enCours: sinistres.filter((s) => s.statut === 'en_cours' || s.statut === 'nouveau').length,
    enTraitement: sinistres.filter((s) => s.statut === 'en_traitement').length,
    complete: sinistres.filter((s) => s.statut === 'complete' || s.statut === 'cloture').length,
  };

  const getSinistreOptionsForContrat = (contratId) => {
    const contrat = contrats.find((c) => c.id === contratId);
    const cType = (contrat?.type_contrat || contrat?.type || 'auto').toLowerCase();

    if (cType.includes('auto')) {
      return [
        { label: 'Auto - Carambolage', value: 'Auto - Carambolage' },
        { label: 'Auto - Vol', value: 'Auto - Vol' },
        { label: 'Auto - Inondation', value: 'Auto - Inondation' },
      ];
    }
    if (cType.includes('habitation')) {
      return [
        { label: 'Habitation - Incendie', value: 'Habitation - Incendie' },
        { label: 'Habitation - Inondation', value: 'Habitation - Inondation' },
        { label: 'Habitation - Cambriolage', value: 'Habitation - Cambriolage' },
      ];
    }
    if (cType.includes('vie')) {
      return [
        { label: 'Vie - Hospitalisation', value: 'Vie - Hospitalisation' },
        { label: 'Vie - Invalidité', value: 'Vie - Invalidité' },
      ];
    }
    if (cType.includes('sante')) {
      return [
        { label: 'Sante - Soins', value: 'Sante - Soins' },
        { label: 'Sante - Chirurgie', value: 'Sante - Chirurgie' },
      ];
    }
    return [{ label: 'Autre Sinistre', value: 'Autre Sinistre' }];
  };

  const handleOpenAdd = () => {
    if (isAssurances && !isSinistres) {
      alert('Déclaration de sinistre réservée exclusivement aux gestionnaires Sinistres.');
      return;
    }
    setErrorMsg('');
    const firstActiveContrat = contrats.find((c) => c.statut === 'actif' || !c.statut) || contrats[0];
    const targetC = firstActiveContrat?.id || '';
    const availableTypes = getSinistreOptionsForContrat(targetC);

    setFormData({
      id: `CSIN${Math.floor(10000 + Math.random() * 90000)}`,
      contrat_id: targetC,
      type: availableTypes[0]?.value || 'Auto - Carambolage',
      lieu: 'Tunis Centre',
      montant_declare: '1500',
      date_sinistre: new Date().toISOString().split('T')[0],
      date: new Date().toISOString().split('T')[0],
      responsabilite: 'indetermine',
      statut: 'en_cours',
      description: 'Sinistre à évaluer',
      observations: '',
    });
    setShowAddModal(true);
  };

  const handleContratChange = (e) => {
    const newContratId = e.target.value;
    const availableTypes = getSinistreOptionsForContrat(newContratId);
    setFormData((prev) => ({
      ...prev,
      contrat_id: newContratId,
      type: availableTypes[0]?.value || 'Auto - Carambolage',
    }));
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    // Vérification du statut du contrat sélectionné
    const selectedContrat = contrats.find((c) => c.id === formData.contrat_id);
    const selectedStatut = (selectedContrat?.statut || '').toLowerCase();
    if (selectedStatut === 'suspendu') {
      setErrorMsg(`Impossible de déclarer un sinistre : le contrat ${formData.contrat_id} est actuellement suspendu.`);
      return;
    }
    if (selectedStatut === 'resilie' || selectedStatut === 'résilié') {
      setErrorMsg(`Impossible de déclarer un sinistre : le contrat ${formData.contrat_id} est résilié.`);
      return;
    }

    // Contrôle de saisie
    const mDec = parseFloat(formData.montant_declare || 0);
    if (isNaN(mDec) || mDec <= 0) {
      setErrorMsg('Le montant déclaré du sinistre doit être un montant strictement positif (> 0 DT).');
      return;
    }

    const todayStr = new Date().toISOString().split('T')[0];
    if (formData.date_sinistre && formData.date_sinistre > todayStr) {
      setErrorMsg('La date de survenance du sinistre ne peut pas être dans le futur.');
      return;
    }

    setLoading(true);

    try {
      await sinistresAPI.addSinistre({
        id: formData.id || undefined,
        contrat_id: formData.contrat_id,
        type: formData.type,
        type_sinistre: formData.type,
        montant_declare: mDec,
        lieu: formData.lieu,
        lieu_sinistre: formData.lieu,
        date_sinistre: formData.date_sinistre,
        date_declaration: formData.date,
        date: formData.date,
        responsabilite: formData.responsabilite,
        description: formData.description,
        observations: formData.observations,
        statut: formData.statut,
      });

      setShowAddModal(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Erreur lors de la déclaration du sinistre');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (id, newStatut) => {
    if (isAssurances && !isSinistres) {
      alert('Modification de sinistre réservée exclusivement aux gestionnaires Sinistres.');
      return;
    }
    try {
      await sinistresAPI.updateSinistre(id, { statut: newStatut });
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err.message || 'Erreur lors de la mise à jour');
    }
  };

  const handleDeleteSinistre = async (id) => {
    if (isAssurances && !isSinistres) {
      alert('Suppression réservée exclusivement aux gestionnaires Sinistres.');
      return;
    }
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer le sinistre ${id} ? Cette action est irréversible.`)) {
      return;
    }
    try {
      await sinistresAPI.deleteSinistre(id);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err.message || 'Erreur lors de la suppression du sinistre');
    }
  };

  const handleDownloadPDF = async (id) => {
    try {
      await sinistresAPI.downloadPDF(id);
    } catch (err) {
      alert(err.message || 'Échec du téléchargement PDF');
    }
  };

  const [showConstatModal, setShowConstatModal] = useState(false);
  const [showDevisModal, setShowDevisModal] = useState(false);
  const [constatResult, setConstatResult] = useState(null);
  const [constatLoading, setConstatLoading] = useState(false);
  const [devisResult, setDevisResult] = useState(null);
  const [devisLoading, setDevisLoading] = useState(false);

  const handleConstatFileUpload = async (e) => {
    const file = e.target && e.target.files && e.target.files[0];
    if (!file) return;
    setConstatLoading(true);
    setConstatResult(null);
    try {
      const data = await sinistresAPI.extractConstat(file);
      setConstatResult(data);
    } catch (err) {
      alert(err.message || "Erreur lors de l'analyse OCR du constat");
    } finally {
      setConstatLoading(false);
      if (e.target) e.target.value = '';
    }
  };

  const handleConstatDemo = async () => {
    setConstatLoading(true);
    setConstatResult(null);
    try {
      const dummyFile = new File(['constat_sample'], 'constat_amiable_demo.png', { type: 'image/png' });
      const data = await sinistresAPI.extractConstat(dummyFile);
      setConstatResult(data);
    } catch (err) {
      alert(err.message || "Erreur lors du test de démonstration du constat");
    } finally {
      setConstatLoading(false);
    }
  };

  const handleDevisFileUpload = async (e) => {
    const file = e.target && e.target.files && e.target.files[0];
    if (!file) return;
    setDevisLoading(true);
    setDevisResult(null);
    try {
      const data = await sinistresAPI.analyzeDevis(file);
      setDevisResult(data);
    } catch (err) {
      alert(err.message || "Erreur lors de l'analyse du devis de réparation");
    } finally {
      setDevisLoading(false);
      if (e.target) e.target.value = '';
    }
  };

  const handleDevisDemo = async () => {
    setDevisLoading(true);
    setDevisResult(null);
    try {
      const dummyFile = new File(['devis_sample'], 'devis_carrosserie_demo.png', { type: 'image/png' });
      const data = await sinistresAPI.analyzeDevis(dummyFile);
      setDevisResult(data);
    } catch (err) {
      alert(err.message || "Erreur lors du test de démonstration du devis");
    } finally {
      setDevisLoading(false);
    }
  };

  return (
    <section id="page-sinistres" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">Mes sinistres </h1>
          <p className="page-subtitle">{sinistres.length} dossier(s) répertorié(s)</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-secondary" onClick={() => setShowConstatModal(true)} style={{ backgroundColor: '#eff6ff', color: '#1d4ed8', borderColor: '#bfdbfe', fontWeight: 600 }}>
            📝 OCR Constat Amiable
          </button>
          <button className="btn-secondary" onClick={() => setShowDevisModal(true)} style={{ backgroundColor: '#faf5ff', color: '#7e22ce', borderColor: '#e9d5ff', fontWeight: 600 }}>
            🛠️ Contrôle Devis Garagiste
          </button>
          {isSinistres ? (
            <button className="btn-primary" onClick={handleOpenAdd}>
              + Déclarer un sinistre
            </button>
          ) : (
            <button
              className="btn-primary"
              style={{ opacity: 0.5, cursor: 'not-allowed' }}
              title="Réservé aux gestionnaires Sinistres"
              onClick={() => alert('Réservé aux gestionnaires Sinistres')}
            >
              🔒 Déclaration Sinistre (Sinistres)
            </button>
          )}
        </div>
      </header>

      {/* KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">En cours</div>
          <div className="kpi-value">{kpis.enCours}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">En traitement</div>
          <div className="kpi-value">{kpis.enTraitement}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Complétés</div>
          <div className="kpi-value">{kpis.complete}</div>
        </div>
      </div>

      {/* SECTION BANNIÈRE D'OUTILS IA POUR LES SINISTRES */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', margin: '16px 0' }}>
        {/* CARTE 1 : CONSTAT AMIABLE */}
        <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #bfdbfe', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#1d4ed8', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>📝</span>
              <span>OCR Constat Amiable Manuscrit</span>
            </div>
        
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
            Extrait les informations lisibles ; la responsabilité reste à valider manuellement.
          </div>
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={handleConstatFileUpload}
            disabled={constatLoading}
            style={{ width: '100%', padding: '6px', borderRadius: '6px', border: '1px dashed #93c5fd', backgroundColor: '#eff6ff', fontSize: '11.5px', cursor: 'pointer' }}
          />
          {constatLoading && <div style={{ fontSize: '11.5px', color: '#2563eb', fontWeight: 600, marginTop: '6px' }}>⏳ Extraction en cours...</div>}
        </div>

        {/* CARTE 2 : DEVIS GARAGISTE */}
        <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e9d5ff', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#7e22ce', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>🛠️</span>
              <span>Contrôle Devis Garagiste (Surfacturation)</span>
            </div>
         
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
            Compare les lignes de pièces & main d'œuvre par rapport à la grille tarifaire officielle.
          </div>
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={handleDevisFileUpload}
            disabled={devisLoading}
            style={{ width: '100%', padding: '6px', borderRadius: '6px', border: '1px dashed #d8b4fe', backgroundColor: '#faf5ff', fontSize: '11.5px', cursor: 'pointer' }}
          />
          {devisLoading && <div style={{ fontSize: '11.5px', color: '#9333ea', fontWeight: 600, marginTop: '6px' }}>⏳ Analyse du devis en cours...</div>}
        </div>
      </div>

      {/* RÉSULTAT DE L'ANALYSE DU CONSTAT AMIABLE (INLINE) */}
      {constatResult && (
        <div style={{ marginBottom: '16px', backgroundColor: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1.5px solid #3b82f6', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#1d4ed8' }}>
              📝 Résultat d'extraction du Constat Amiable — {constatResult.lieu_accident || 'Lieu non détecté'} ({constatResult.date_accident || 'Date non détectée'})
            </div>
            <div style={{ padding: '4px 12px', borderRadius: '999px', backgroundColor: '#fef2f2', color: '#b91c1c', fontSize: '12px', fontWeight: 700 }}>
              ⚖️ Responsabilité à valider : {constatResult.responsabilite_estimee || 'À déterminer manuellement'}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ padding: '12px', background: '#eff6ff', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#1d4ed8', marginBottom: '6px' }}>🚗 Véhicule A (Assuré)</div>
              <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Matricule :</strong> {constatResult.vehicule_a?.immatriculation || 'Non détecté'}</div>
              <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Conducteur :</strong> {constatResult.vehicule_a?.souscripteur || 'Non détecté'}</div>
              <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Modèle :</strong> {constatResult.vehicule_a?.marque_modele || 'Non détecté'}</div>
              <div style={{ fontSize: '12px', color: '#dc2626', marginTop: '4px' }}>• <strong>Dégâts :</strong> {constatResult.vehicule_a?.degats_apparents || 'Non détectés'}</div>
            </div>

            <div style={{ padding: '12px', background: '#fffbeb', borderRadius: '8px', border: '1px solid #fde68a' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#b45309', marginBottom: '6px' }}>🚙 Véhicule B (Tiers)</div>
              <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Matricule :</strong> {constatResult.vehicule_b?.immatriculation || 'Non détecté'}</div>
              <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Conducteur :</strong> {constatResult.vehicule_b?.souscripteur || 'Non détecté'}</div>
              <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Modèle :</strong> {constatResult.vehicule_b?.marque_modele || 'Non détecté'}</div>
              <div style={{ fontSize: '12px', color: '#dc2626', marginTop: '4px' }}>• <strong>Dégâts :</strong> {constatResult.vehicule_b?.degats_apparents || 'Non détectés'}</div>
            </div>
          </div>

          {constatResult.observations_expert && (
            <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#ffffff', borderRadius: '6px', borderLeft: '4px solid #3b82f6', fontSize: '12px', color: '#1e293b' }}>
              💡 <strong>Avis d'expert IA :</strong> {constatResult.observations_expert}
            </div>
          )}
        </div>
      )}

      {/* RÉSULTAT DE L'ANALYSE DU DEVIS GARAGISTE (INLINE) */}
      {devisResult && (
        <div style={{ marginBottom: '16px', backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1.5px solid #9333ea', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#7e22ce', marginBottom: '12px' }}>
            🛠️ Analyse du Devis Garagiste — {devisResult.garage_nom} ({devisResult.immatriculation})
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '12px', textAlign: 'center' }}>
            <div style={{ padding: '8px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '10px', color: '#64748b' }}>Réclamé Garage</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#0f172a' }}>{devisResult.montant_total_reclaime?.toLocaleString('fr-FR')} DT</div>
            </div>
            <div style={{ padding: '8px', background: '#ecfdf5', borderRadius: '8px', border: '1px solid #a7f3d0' }}>
              <div style={{ fontSize: '10px', color: '#047857' }}>Barème Référence</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#059669' }}>{devisResult.montant_total_bareme?.toLocaleString('fr-FR')} DT</div>
            </div>
            <div style={{ padding: '8px', background: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
              <div style={{ fontSize: '10px', color: '#b91c1c' }}>Économie Potentielle</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#dc2626' }}>{devisResult.economie_potentielle?.toLocaleString('fr-FR')} DT</div>
            </div>
            <div style={{ padding: '8px', background: devisResult.est_surfacture ? '#fff1f2' : '#ecfdf5', borderRadius: '8px', border: devisResult.est_surfacture ? '1px solid #fda4af' : '1px solid #a7f3d0' }}>
              <div style={{ fontSize: '10px', color: devisResult.est_surfacture ? '#be123c' : '#047857' }}>Écart vs Barème</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: devisResult.est_surfacture ? '#e11d48' : '#059669' }}>
                {devisResult.surfacturation_globale_pct > 0 ? `+${devisResult.surfacturation_globale_pct}%` : `${devisResult.surfacturation_globale_pct}%`}
              </div>
            </div>
          </div>

          <div style={{ padding: '10px 14px', backgroundColor: devisResult.est_surfacture ? '#fff1f2' : '#f0fdf4', borderRadius: '8px', borderLeft: devisResult.est_surfacture ? '4px solid #e11d48' : '4px solid #16a34a', fontSize: '12px', color: '#1e293b', marginBottom: '12px' }}>
            {devisResult.recommandation_expert}
          </div>

          <table className="data-table" style={{ fontSize: '11.5px' }}>
            <thead>
              <tr>
                <th>Poste / Désignation</th>
                <th>Qte</th>
                <th>Prix Garage (DT)</th>
                <th>Barème Réf (DT)</th>
                <th>Écart %</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {devisResult.items?.map((item, idx) => (
                <tr key={idx} style={{ backgroundColor: item.surfacture ? '#fef2f2' : 'transparent' }}>
                  <td style={{ fontWeight: 600 }}>{item.designation}</td>
                  <td>{item.quantite}</td>
                  <td style={{ fontWeight: 700, color: item.surfacture ? '#dc2626' : '#0f172a' }}>{item.prix_unitaire_reclaime} DT</td>
                  <td style={{ color: '#059669', fontWeight: 600 }}>{item.prix_unitaire_bareme} DT</td>
                  <td style={{ fontWeight: 700, color: item.ecart_pct > 0 ? '#dc2626' : '#059669' }}>
                    {item.ecart_pct > 0 ? `+${item.ecart_pct}%` : `${item.ecart_pct}%`}
                  </td>
                  <td>
                    <span style={{ padding: '2px 8px', borderRadius: '999px', fontSize: '10px', fontWeight: 700, backgroundColor: item.surfacture ? '#fee2e2' : '#d1fae5', color: item.surfacture ? '#b91c1c' : '#047857' }}>
                      {item.alerte}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Data Table */}
      <div className="table-card" style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>N° SINISTRE</th>
              <th>CONTRAT</th>
              <th>CLIENT</th>
              <th>AGENCE</th>
              <th>TYPE SINISTRE</th>
              <th>MONTANT DÉCLARÉ</th>
              <th>LIEU</th>
              <th>DATE SINISTRE</th>
              <th>DATE DÉCLARATION</th>
              <th>RESPONSABILITÉ</th>
              <th>STATUT</th>
              <th>GESTIONNAIRE</th>
              <th>ACTIONS & PDF</th>
            </tr>
          </thead>
          <tbody>
            {sinistres.length === 0 ? (
              <tr>
                <td colSpan="13" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                  Aucun sinistre trouvé dans la base MySQL.
                </td>
              </tr>
            ) : (
              sinistres.map((s, index) => (
                <tr key={`${s.id}-${index}`}>
                  <td className="cell-bold">{s.id}</td>
                  <td className="cell-bold">{s.contrat_id}</td>
                  <td className="cell-bold">{s.client || s.client_nom || 'Client Assuré'}</td>
                  <td>{s.agence_nom || s.agence_id || 'Agence Tunis Centre'}</td>
                  <td>{s.type_sinistre || s.type}</td>
                  <td className="cell-bold" style={{ color: '#dc2626' }}>{formatDT(s.montant_declare)}</td>
                  <td>{s.lieu || s.lieu_sinistre || 'N/A'}</td>
                  <td style={{ fontSize: '11px' }}>{s.date_sinistre || 'N/A'}</td>
                  <td style={{ fontSize: '11px' }}>{s.date || s.date_declaration || '2026-08-08'}</td>
                  <td>{s.responsabilite || 'Indéterminée'}</td>
                  <td>
                    <span className={`status-badge status-${s.statut}`}>
                      {s.statut === 'en_cours'
                        ? 'En cours'
                        : s.statut === 'en_traitement'
                        ? 'En traitement'
                        : s.statut === 'complete'
                        ? 'Complété'
                        : s.statut}
                    </span>
                  </td>
                  <td>{s.gestionnaire_nom || s.gestionnaire_traitant_id || 'Ahmed Trabelsi'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                      {isSinistres ? (
                        <select
                          className="form-select"
                          style={{ padding: '4px 6px', fontSize: '11px' }}
                          value={s.statut}
                          onChange={(e) => handleUpdateStatus(s.id, e.target.value)}
                        >
                          <option value="en_cours">En cours</option>
                          <option value="en_traitement">En traitement</option>
                          <option value="complete">Complété</option>
                          <option value="rejete">Rejeté</option>
                        </select>
                      ) : (
                        <span style={{ fontSize: '11px', color: '#64748b' }}>Lecture seule</span>
                      )}
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '11px' }}
                        onClick={() => setSelectedSinistre(s)}
                        title="Voir détails"
                      >
                        👁️
                      </button>
                      <button
                        className="btn-primary"
                        style={{ padding: '4px 8px', fontSize: '11px', backgroundColor: '#dc2626', borderColor: '#dc2626' }}
                        onClick={() => handleDownloadPDF(s.id)}
                        title="Télécharger Rapport PDF"
                      >
                        📄 PDF
                      </button>
                      {isSinistres && (
                        <button
                          className="btn-danger"
                          style={{ padding: '4px 8px', fontSize: '11px', backgroundColor: '#ef4444', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                          onClick={() => handleDeleteSinistre(s.id)}
                          title="Supprimer le sinistre"
                        >
                          🗑️ Supprimer
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Détails Sinistre */}
      {selectedSinistre && (
        <div className="modal-overlay" style={{ display: 'flex' }}>
          <div className="modal-card" style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Détails du sinistre #{selectedSinistre.id}</h3>
              <button className="btn-close" onClick={() => setSelectedSinistre(null)}>&times;</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px', color: '#1e293b' }}>
              <div><strong>Client :</strong> {selectedSinistre.client}</div>
              <div><strong>Contrat :</strong> {selectedSinistre.contrat_id}</div>
              <div><strong>Agence :</strong> {selectedSinistre.agence_id}</div>
              <div><strong>Type :</strong> {selectedSinistre.type_sinistre || selectedSinistre.type}</div>
              <div><strong>Montant :</strong> {formatDT(selectedSinistre.montant_declare)}</div>
              <div><strong>Lieu :</strong> {selectedSinistre.lieu || selectedSinistre.lieu_sinistre || 'N/A'}</div>
              <div><strong>Date Sinistre :</strong> {selectedSinistre.date_sinistre || 'N/A'}</div>
              <div><strong>Date Déclaration :</strong> {selectedSinistre.date || selectedSinistre.date_declaration}</div>
              <div><strong>Responsabilité :</strong> {selectedSinistre.responsabilite}</div>
              <div><strong>Statut :</strong> {selectedSinistre.statut}</div>
              <div style={{ gridColumn: 'span 2' }}>
                <strong>Description :</strong> {selectedSinistre.description || 'Aucune description'}
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <strong>Observations :</strong> {selectedSinistre.observations || 'Aucune observation'}
              </div>
            </div>
            <div className="modal-footer" style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between' }}>
              <button
                className="btn-primary"
                style={{ backgroundColor: '#dc2626', borderColor: '#dc2626' }}
                onClick={() => handleDownloadPDF(selectedSinistre.id)}
              >
                📄 Exporter Rapport PDF
              </button>
              <button className="btn-secondary" onClick={() => setSelectedSinistre(null)}>Fermer</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Declarer Sinistre */}
      {showAddModal && (
        <div className="modal-overlay" style={{ display: 'flex' }}>
          <div className="modal-card" style={{ maxWidth: '680px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Déclarer un nouveau sinistre</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>
                &times;
              </button>
            </div>

            {errorMsg && <div style={{ color: '#ef4444', backgroundColor: '#fef2f2', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>{errorMsg}</div>}

            <form onSubmit={handleAddSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">N° Sinistre *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: CSIN00015"
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">N° Contrat *</label>
                  <select
                    className="form-select"
                    value={formData.contrat_id}
                    onChange={handleContratChange}
                    required
                  >
                    {contrats.map((c) => {
                      const s = (c.statut || 'actif').toLowerCase();
                      const isSusp = s === 'suspendu';
                      const isRes = s === 'resilie' || s === 'résilié';
                      let statusBadge = 'Actif';
                      if (isSusp) statusBadge = '⚠️ SUSPENDU - Inéligible';
                      else if (isRes) statusBadge = '⛔ RÉSILIÉ - Inéligible';

                      return (
                        <option key={c.id} value={c.id}>
                          {c.id} - {c.client || c.client_nom || c.client_id} [{statusBadge}] (Formule: {c.type_contrat || c.type})
                        </option>
                      );
                    })}
                  </select>
                </div>
              </div>

              {/* Alerte si contrat suspendu ou résilié */}
              {(() => {
                const selC = contrats.find((c) => c.id === formData.contrat_id);
                const s = (selC?.statut || 'actif').toLowerCase();
                const isSusp = s === 'suspendu';
                const isRes = s === 'resilie' || s === 'résilié';

                if (isSusp || isRes) {
                  return (
                    <div
                      style={{
                        backgroundColor: isSusp ? '#fffbeb' : '#fef2f2',
                        color: isSusp ? '#b45309' : '#b91c1c',
                        border: `1px solid ${isSusp ? '#fde68a' : '#fecaca'}`,
                        padding: '10px 14px',
                        borderRadius: '8px',
                        fontSize: '13px',
                        fontWeight: 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        marginBottom: '12px',
                      }}
                    >
                      <span style={{ fontSize: '18px' }}>{isSusp ? '⚠️' : '⛔'}</span>
                      <div>
                        <strong>Déclaration bloquée :</strong> Le contrat <u>{formData.contrat_id}</u> est actuellement <strong>{isSusp ? 'suspendu' : 'résilié'}</strong>. Aucun sinistre ne peut être rattaché à un contrat suspendu ou résilié.
                      </div>
                    </div>
                  );
                }
                return null;
              })()}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Type de sinistre (Adapté au contrat) *</label>
                  <select
                    className="form-select"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    required
                  >
                    {getSinistreOptionsForContrat(formData.contrat_id).map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Lieu du sinistre</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: Sfax, Rue de la République"
                    value={formData.lieu}
                    onChange={(e) => setFormData({ ...formData, lieu: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Montant Déclaré (DT) *</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="ex: 12000"
                    value={formData.montant_declare}
                    onChange={(e) => setFormData({ ...formData, montant_declare: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Date Sinistre</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.date_sinistre}
                    onChange={(e) => setFormData({ ...formData, date_sinistre: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Date Déclaration *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Responsabilité</label>
                  <select
                    className="form-select"
                    value={formData.responsabilite}
                    onChange={(e) => setFormData({ ...formData, responsabilite: e.target.value })}
                  >
                    <option value="indetermine">Indéterminée</option>
                    <option value="assure">Assuré</option>
                    <option value="tiers">Tiers</option>
                    <option value="partage">Partagée</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Statut</label>
                  <select
                    className="form-select"
                    value={formData.statut}
                    onChange={(e) => setFormData({ ...formData, statut: e.target.value })}
                  >
                    <option value="en_cours">En cours</option>
                    <option value="en_traitement">En traitement</option>
                    <option value="complete">Clôturé / Complété</option>
                    <option value="rejete">Rejeté</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Description des faits</label>
                <textarea
                  className="form-input"
                  rows="2"
                  placeholder="Détails du sinistre, circonstances..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                ></textarea>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Annuler
                </button>
                {(() => {
                  const selC = contrats.find((c) => c.id === formData.contrat_id);
                  const s = (selC?.statut || 'actif').toLowerCase();
                  const isBlocked = s === 'suspendu' || s === 'resilie' || s === 'résilié';

                  return (
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={loading || isBlocked}
                      style={{
                        opacity: isBlocked ? 0.5 : 1,
                        cursor: isBlocked ? 'not-allowed' : 'pointer',
                        backgroundColor: isBlocked ? '#94a3b8' : undefined,
                        borderColor: isBlocked ? '#94a3b8' : undefined,
                      }}
                      title={isBlocked ? 'Impossible de déclarer un sinistre sur un contrat suspendu ou résilié' : ''}
                    >
                      {loading ? 'Création...' : isBlocked ? 'Contrat non éligible' : 'Déclarer le sinistre'}
                    </button>
                  );
                })()}
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 1 : OCR CONSTAT AMIABLE MANUSCRIT */}
      {showConstatModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '750px', width: '90%' }}>
            <div className="modal-header">
              <h2 className="modal-title" style={{ color: '#1d4ed8' }}>📝 Lecture Automatique de Constat Amiable (OCR Multimodal)</h2>
              <button className="modal-close" onClick={() => setShowConstatModal(false)}>×</button>
            </div>
            <div className="modal-body" style={{ padding: '16px 24px' }}>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '14px' }}>
                Chargez une image ou un scan du formulaire de constat amiable d'accident pour extraire automatiquement les véhicules, circonstances et la responsabilité présumée.
              </p>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '12px' }}>
                <input
                  type="file"
                  accept="image/*,.pdf"
                  onChange={handleConstatFileUpload}
                  disabled={constatLoading}
                  style={{ flex: 1, padding: '10px', borderRadius: '8px', border: '2px dashed #93c5fd', backgroundColor: '#eff6ff', cursor: 'pointer' }}
                />
          
              </div>

              {constatLoading && (
                <div style={{ marginTop: '16px', textAlign: 'center', color: '#2563eb', fontWeight: 600, fontSize: '13px' }}>
                  ⏳ Extraction OCR & analyse multimodale par Gemini Vision en cours...
                </div>
              )}

              {constatResult && (
                <div style={{ marginTop: '18px', backgroundColor: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #cbd5e1' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>
                      📍 Lieu & Date : {constatResult.lieu_accident || 'Lieu non détecté'} ({constatResult.date_accident || 'Date non détectée'})
                    </div>
                    <div style={{ padding: '4px 12px', borderRadius: '999px', backgroundColor: '#fef2f2', color: '#b91c1c', fontSize: '12px', fontWeight: 700 }}>
                      ⚖️ {constatResult.responsabilite_estimee || 'À déterminer manuellement'}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div style={{ padding: '12px', background: '#eff6ff', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: '#1d4ed8', marginBottom: '6px' }}>🚗 Véhicule A (Assuré)</div>
                      <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Matricule :</strong> {constatResult.vehicule_a?.immatriculation || 'Non détecté'}</div>
                      <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Conducteur :</strong> {constatResult.vehicule_a?.souscripteur || 'Non détecté'}</div>
                      <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Modèle :</strong> {constatResult.vehicule_a?.marque_modele || 'Non détecté'}</div>
                      <div style={{ fontSize: '12px', color: '#dc2626', marginTop: '4px' }}>• <strong>Dégâts :</strong> {constatResult.vehicule_a?.degats_apparents || 'Non détectés'}</div>
                    </div>

                    <div style={{ padding: '12px', background: '#fffbeb', borderRadius: '8px', border: '1px solid #fde68a' }}>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: '#b45309', marginBottom: '6px' }}>🚙 Véhicule B (Tiers)</div>
                      <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Matricule :</strong> {constatResult.vehicule_b?.immatriculation || 'Non détecté'}</div>
                      <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Conducteur :</strong> {constatResult.vehicule_b?.souscripteur || 'Non détecté'}</div>
                      <div style={{ fontSize: '12px', color: '#334155' }}>• <strong>Modèle :</strong> {constatResult.vehicule_b?.marque_modele || 'Non détecté'}</div>
                      <div style={{ fontSize: '12px', color: '#dc2626', marginTop: '4px' }}>• <strong>Dégâts :</strong> {constatResult.vehicule_b?.degats_apparents || 'Non détectés'}</div>
                    </div>
                  </div>

                  {constatResult.circonstances?.length > 0 && (
                    <div style={{ marginTop: '12px', fontSize: '12px', color: '#334155' }}>
                      <strong>📝 Circonstances déclarées :</strong>
                      <ul style={{ paddingLeft: '18px', marginTop: '4px', margin: 0 }}>
                        {constatResult.circonstances.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {constatResult.observations_expert && (
                    <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#ffffff', borderRadius: '6px', borderLeft: '4px solid #3b82f6', fontSize: '12px', color: '#1e293b' }}>
                      💡 <strong>Avis d'expert IA :</strong> {constatResult.observations_expert}
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowConstatModal(false)}>Fermer</button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2 : CONTRÔLE DEVIS GARAGISTE & SURFACTURATION */}
      {showDevisModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '850px', width: '90%' }}>
            <div className="modal-header">
              <h2 className="modal-title" style={{ color: '#7e22ce' }}>🛠️ Analyseur de Devis Garagiste & Détection de Surfacturation</h2>
              <button className="modal-close" onClick={() => setShowDevisModal(false)}>×</button>
            </div>
            <div className="modal-body" style={{ padding: '16px 24px' }}>
              <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '14px' }}>
                Uploadez une facture ou un devis de carrosserie/garage pour comparer automatiquement chaque poste avec la grille tarifaire officielle de référence de l'assurance.
              </p>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '12px' }}>
                <input
                  type="file"
                  accept="image/*,.pdf"
                  onChange={handleDevisFileUpload}
                  disabled={devisLoading}
                  style={{ flex: 1, padding: '10px', borderRadius: '8px', border: '2px dashed #d8b4fe', backgroundColor: '#faf5ff', cursor: 'pointer' }}
                />
            
              </div>

              {devisLoading && (
                <div style={{ marginTop: '16px', textAlign: 'center', color: '#9333ea', fontWeight: 600, fontSize: '13px' }}>
                  ⏳ Comparaison des lignes de devis par rapport au barème des assurances en cours...
                </div>
              )}

              {devisResult && (
                <div style={{ marginTop: '18px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '14px', textAlign: 'center' }}>
                    <div style={{ padding: '10px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: '10px', color: '#64748b' }}>Réclamé Garage</div>
                      <div style={{ fontSize: '14px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>{devisResult.montant_total_reclaime?.toLocaleString('fr-FR')} DT</div>
                    </div>
                    <div style={{ padding: '10px', background: '#ecfdf5', borderRadius: '8px', border: '1px solid #a7f3d0' }}>
                      <div style={{ fontSize: '10px', color: '#047857' }}>Barème Référence</div>
                      <div style={{ fontSize: '14px', fontWeight: 800, color: '#059669', marginTop: '2px' }}>{devisResult.montant_total_bareme?.toLocaleString('fr-FR')} DT</div>
                    </div>
                    <div style={{ padding: '10px', background: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
                      <div style={{ fontSize: '10px', color: '#b91c1c' }}>Économie Potentielle</div>
                      <div style={{ fontSize: '14px', fontWeight: 800, color: '#dc2626', marginTop: '2px' }}>{devisResult.economie_potentielle?.toLocaleString('fr-FR')} DT</div>
                    </div>
                    <div style={{ padding: '10px', background: devisResult.est_surfacture ? '#fff1f2' : '#ecfdf5', borderRadius: '8px', border: devisResult.est_surfacture ? '1px solid #fda4af' : '1px solid #a7f3d0' }}>
                      <div style={{ fontSize: '10px', color: devisResult.est_surfacture ? '#be123c' : '#047857' }}>Écart vs Barème</div>
                      <div style={{ fontSize: '14px', fontWeight: 800, color: devisResult.est_surfacture ? '#e11d48' : '#059669', marginTop: '2px' }}>
                        {devisResult.surfacturation_globale_pct > 0 ? `+${devisResult.surfacturation_globale_pct}%` : `${devisResult.surfacturation_globale_pct}%`}
                      </div>
                    </div>
                  </div>

                  <div style={{ padding: '10px 14px', backgroundColor: devisResult.est_surfacture ? '#fff1f2' : '#f0fdf4', borderRadius: '8px', borderLeft: devisResult.est_surfacture ? '4px solid #e11d48' : '4px solid #16a34a', fontSize: '12.5px', color: '#1e293b', marginBottom: '14px' }}>
                    {devisResult.recommandation_expert}
                  </div>

                  <table className="data-table" style={{ fontSize: '12px' }}>
                    <thead>
                      <tr>
                        <th>Poste / Désignation</th>
                        <th>Qte</th>
                        <th>Prix Garage (DT)</th>
                        <th>Barème Réf (DT)</th>
                        <th>Écart %</th>
                        <th>Statut</th>
                      </tr>
                    </thead>
                    <tbody>
                      {devisResult.items?.map((item, idx) => (
                        <tr key={idx} style={{ backgroundColor: item.surfacture ? '#fef2f2' : 'transparent' }}>
                          <td style={{ fontWeight: 600 }}>{item.designation}</td>
                          <td>{item.quantite}</td>
                          <td style={{ fontWeight: 700, color: item.surfacture ? '#dc2626' : '#0f172a' }}>{item.prix_unitaire_reclaime} DT</td>
                          <td style={{ color: '#059669', fontWeight: 600 }}>{item.prix_unitaire_bareme} DT</td>
                          <td style={{ fontWeight: 700, color: item.ecart_pct > 0 ? '#dc2626' : '#059669' }}>
                            {item.ecart_pct > 0 ? `+${item.ecart_pct}%` : `${item.ecart_pct}%`}
                          </td>
                          <td>
                            <span style={{ padding: '2px 8px', borderRadius: '999px', fontSize: '10.5px', fontWeight: 700, backgroundColor: item.surfacture ? '#fee2e2' : '#d1fae5', color: item.surfacture ? '#b91c1c' : '#047857' }}>
                              {item.alerte}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowDevisModal(false)}>Fermer</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
