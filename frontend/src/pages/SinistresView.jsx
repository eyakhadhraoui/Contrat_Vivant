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

  return (
    <section id="page-sinistres" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">Mes sinistres </h1>
          <p className="page-subtitle">{sinistres.length} dossier(s) répertorié(s)</p>
        </div>
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
              sinistres.map((s) => (
                <tr key={s.id}>
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
    </section>
  );
}
