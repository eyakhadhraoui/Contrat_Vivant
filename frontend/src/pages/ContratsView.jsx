import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { contratsAPI, cinAPI } from '../services/api';

export default function ContratsView({ contrats, clients, onRefresh }) {
  const { isAssurances, isSinistres } = useAuth();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedContrat, setSelectedContrat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [formData, setFormData] = useState({
    id: '',
    client_id: '',
    type: 'auto',
    garantie_max: '100000',
    prime_mensuelle: '120',
    prime_annuelle: '1440',
    franchise: '500',
    duree_mois: '12',
    date_debut: new Date().toISOString().split('T')[0],
    date_fin: new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0],
    statut: 'actif',
    mode_paiement: 'Virement',
    frequence_paiement: 'Mensuel',
    couverture: 'Tous risques, assistance 24/7',
    exclusions: 'Usure normale, usage non autorisé',
    observations: '',
  });

  const formatDT = (val) => {
    if (!val && val !== 0) return '0 DT';
    return Number(val).toLocaleString('fr-FR') + ' DT';
  };

  const kpis = {
    actifs: contrats.filter((c) => c.statut === 'actif').length,
    suspendus: contrats.filter((c) => c.statut === 'suspendu').length,
    totalGarantie: contrats.reduce((sum, c) => sum + (c.garantie_max || 0), 0),
  };

  const handleOpenAdd = () => {
    if (isSinistres && !isAssurances) {
      alert('Action réservée exclusivement aux gestionnaires Assurances.');
      return;
    }
    setErrorMsg('');
    setSuccessMsg('');
    setFormData({
      id: `CSTR${Math.floor(10000 + Math.random() * 90000)}`,
      client_id: clients[0]?.id || 'CL01',
      type: 'auto',
      garantie_max: '100000',
      prime_mensuelle: '120',
      prime_annuelle: '1440',
      franchise: '500',
      duree_mois: '12',
      date_debut: new Date().toISOString().split('T')[0],
      date_fin: new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0],
      statut: 'actif',
      mode_paiement: 'Virement',
      frequence_paiement: 'Mensuel',
      couverture: 'Tous risques',
      exclusions: 'Usure normale',
      observations: '',
    });
    setShowAddModal(true);
  };

  const handleCINUpload = async (e) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    setOcrLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const res = await cinAPI.extractCIN(file);
      if (res.cin_data) {
        const d = res.cin_data;
        setSuccessMsg(`✨ Données CIN lues : ${d.prenom} ${d.nom} (CIN: ${d.cin || 'détectée'})`);
      }
    } catch (err) {
      setErrorMsg(`Notice OCR : Données partielles.`);
    } finally {
      setOcrLoading(false);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    // Contrôle de saisie
    const gMax = parseFloat(formData.garantie_max || 0);
    if (isNaN(gMax) || gMax <= 0) {
      setErrorMsg('La garantie maximale doit être un montant strictement positif (> 0 DT).');
      return;
    }

    if (formData.date_debut && formData.date_fin && formData.date_fin < formData.date_debut) {
      setErrorMsg('La date de fin de contrat ne peut pas être antérieure à la date de début.');
      return;
    }

    setLoading(true);

    try {
      await contratsAPI.addContrat({
        id: formData.id,
        client_id: formData.client_id,
        type: formData.type,
        type_contrat: formData.type,
        garantie_max: gMax,
        prime_mensuelle: parseFloat(formData.prime_mensuelle || 0),
        prime_annuelle: parseFloat(formData.prime_annuelle || 0),
        franchise: parseFloat(formData.franchise || 0),
        duree_mois: parseInt(formData.duree_mois || 12),
        date_debut: formData.date_debut,
        date_fin: formData.date_fin,
        statut: formData.statut,
        mode_paiement: formData.mode_paiement,
        frequence_paiement: formData.frequence_paiement,
        couverture: formData.couverture,
        exclusions: formData.exclusions,
        observations: formData.observations,
      });

      setShowAddModal(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Erreur lors de l\'ajout du contrat');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (id, newStatut) => {
    if (isSinistres && !isAssurances) {
      alert('Modification réservée exclusivement aux gestionnaires Assurances.');
      return;
    }
    try {
      await contratsAPI.updateContrat(id, { statut: newStatut });
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err.message || 'Erreur de mise à jour du contrat');
    }
  };

  const handleDeleteContrat = async (id) => {
    if (isSinistres && !isAssurances) {
      alert('Suppression réservée exclusivement aux gestionnaires Assurances.');
      return;
    }
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer le contrat ${id} ? Cette action est irréversible.`)) {
      return;
    }
    try {
      await contratsAPI.deleteContrat(id);
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(err.message || 'Erreur lors de la suppression du contrat');
    }
  };

  const handleDownloadPDF = async (id) => {
    try {
      await contratsAPI.downloadPDF(id);
    } catch (err) {
      alert(err.message || 'Échec du téléchargement PDF');
    }
  };

  return (
    <section id="page-contrats" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">Mes contrats </h1>
          <p className="page-subtitle">{contrats.length} contrat(s) répertorié(s)</p>
        </div>
        {isAssurances ? (
          <button className="btn-primary" onClick={handleOpenAdd}>
            + Ajouter un contrat
          </button>
        ) : (
          <button
            className="btn-primary"
            style={{ opacity: 0.5, cursor: 'not-allowed' }}
            title="Réservé aux gestionnaires Assurances"
            onClick={() => alert('Réservé aux gestionnaires Assurances')}
          >
            🔒 Ajout Contrat (Assurances)
          </button>
        )}
      </header>

      {/* KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Actifs</div>
          <div className="kpi-value">{kpis.actifs}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Suspendus</div>
          <div className="kpi-value">{kpis.suspendus}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Garantie totale</div>
          <div className="kpi-value">{formatDT(kpis.totalGarantie)}</div>
        </div>
      </div>

      {/* Data Table */}
      <div className="table-card" style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>N° CONTRAT</th>
              <th>CLIENT</th>
              <th>AGENCE</th>
              <th>TYPE</th>
              <th>GARANTIE MAX</th>
              <th>PRIME M.</th>
              <th>PRIME A.</th>
              <th>FRANCHISE</th>
              <th>DURÉE</th>
              <th>PÉRIODE</th>
              <th>PAIEMENT</th>
              <th>STATUT</th>
              <th>CRÉATEUR</th>
              <th>MODIFIÉ LE</th>
              <th>ACTIONS & PDF</th>
            </tr>
          </thead>
          <tbody>
            {contrats.length === 0 ? (
              <tr>
                <td colSpan="15" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                  Aucun contrat trouvé dans la base MySQL.
                </td>
              </tr>
            ) : (
              contrats.map((c) => (
                <tr key={c.id}>
                  <td className="cell-bold">{c.id}</td>
                  <td className="cell-bold">{c.client || c.client_nom || c.client_id || 'Client Assuré'}</td>
                  <td>{c.agence_nom || c.agence_id || 'Agence Tunis Centre'}</td>
                  <td>
                    <span style={{ textTransform: 'uppercase', fontWeight: 600, fontSize: '11px', color: '#4f46e5' }}>
                      {c.type_contrat || c.type}
                    </span>
                  </td>
                  <td className="cell-bold" style={{ color: '#059669' }}>{formatDT(c.garantie_max)}</td>
                  <td>{c.prime_mensuelle ? formatDT(c.prime_mensuelle) : 'N/A'}</td>
                  <td>{c.prime_annuelle ? formatDT(c.prime_annuelle) : 'N/A'}</td>
                  <td>{c.franchise ? formatDT(c.franchise) : '0 DT'}</td>
                  <td>{c.duree_mois ? `${c.duree_mois} mois` : '12 mois'}</td>
                  <td style={{ fontSize: '11px' }}>
                    {c.date_debut ? `${c.date_debut} au ${c.date_fin}` : 'N/A'}
                  </td>
                  <td style={{ fontSize: '11px' }}>
                    {c.mode_paiement || 'Virement'} ({c.frequence_paiement || 'Mensuel'})
                  </td>
                  <td>
                    <span className={`status-badge status-${c.statut}`}>
                      {c.statut === 'actif'
                        ? 'Actif'
                        : c.statut === 'suspendu'
                          ? 'Suspendu'
                          : c.statut === 'resilie'
                            ? 'Résilié'
                            : c.statut}
                    </span>
                  </td>
                  <td>{c.gestionnaire_nom || c.gestionnaire_createur_id || 'Sarra Khelifi'}</td>
                  <td>{c.date_derniere_modif || '2026-08-08'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                      {isAssurances ? (
                        <select
                          className="form-select"
                          style={{ padding: '4px 6px', fontSize: '11px' }}
                          value={c.statut}
                          onChange={(e) => handleUpdateStatus(c.id, e.target.value)}
                        >
                          <option value="actif">Actif</option>
                          <option value="suspendu">Suspendu</option>
                          <option value="resilie">Résilié</option>
                        </select>
                      ) : (
                        <span style={{ fontSize: '11px', color: '#64748b' }}>Lecture seule</span>
                      )}
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '11px' }}
                        onClick={() => setSelectedContrat(c)}
                        title="Voir détails"
                      >
                        👁️
                      </button>
                      <button
                        className="btn-primary"
                        style={{ padding: '4px 8px', fontSize: '11px', backgroundColor: '#0284c7', borderColor: '#0284c7' }}
                        onClick={() => handleDownloadPDF(c.id)}
                        title="Télécharger Attestation PDF"
                      >
                        📄 PDF
                      </button>
                      {isAssurances && (
                        <button
                          className="btn-danger"
                          style={{ padding: '4px 8px', fontSize: '11px', backgroundColor: '#ef4444', color: '#ffffff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                          onClick={() => handleDeleteContrat(c.id)}
                          title="Supprimer le contrat"
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

      {/* Modal Détails Contrat */}
      {selectedContrat && (
        <div className="modal-overlay" style={{ display: 'flex' }}>
          <div className="modal-card" style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Détails du contrat #{selectedContrat.id}</h3>
              <button className="btn-close" onClick={() => setSelectedContrat(null)}>&times;</button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px', color: '#1e293b' }}>
              <div><strong>Client :</strong> {selectedContrat.client}</div>
              <div><strong>Agence :</strong> {selectedContrat.agence_id}</div>
              <div><strong>Type :</strong> {selectedContrat.type_contrat || selectedContrat.type}</div>
              <div><strong>Garantie Max :</strong> {formatDT(selectedContrat.garantie_max)}</div>
              <div><strong>Prime Mensuelle :</strong> {formatDT(selectedContrat.prime_mensuelle)}</div>
              <div><strong>Prime Annuelle :</strong> {formatDT(selectedContrat.prime_annuelle)}</div>
              <div><strong>Franchise :</strong> {formatDT(selectedContrat.franchise)}</div>
              <div><strong>Durée :</strong> {selectedContrat.duree_mois} mois</div>
              <div><strong>Couverture :</strong> {selectedContrat.couverture || 'N/A'}</div>
              <div><strong>Exclusions :</strong> {selectedContrat.exclusions || 'N/A'}</div>
              <div style={{ gridColumn: 'span 2' }}>
                <strong>Observations :</strong> {selectedContrat.observations || 'Aucune observation'}
              </div>
            </div>
            <div className="modal-footer" style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between' }}>
              <button
                className="btn-primary"
                style={{ backgroundColor: '#0284c7', borderColor: '#0284c7' }}
                onClick={() => handleDownloadPDF(selectedContrat.id)}
              >
                📄 Exporter Attestation PDF
              </button>
              <button className="btn-secondary" onClick={() => setSelectedContrat(null)}>Fermer</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Ajouter Contrat */}
      {showAddModal && (
        <div className="modal-overlay" style={{ display: 'flex' }}>
          <div className="modal-card" style={{ maxWidth: '720px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Ajouter un nouveau contrat</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>
                &times;
              </button>
            </div>

            {/* Scan CIN Box */}
            <div style={{ backgroundColor: '#f1f5f9', border: '1px dashed #64748b', borderRadius: '8px', padding: '10px 12px', marginBottom: '14px' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#1e293b', marginBottom: '4px' }}>
                📷 Importer une photo de CIN (Vérification et détection d'identité)
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleCINUpload}
                disabled={ocrLoading}
                style={{ fontSize: '12px' }}
              />
              {ocrLoading && <span style={{ fontSize: '11px', color: '#0284c7', marginLeft: '8px' }}>Scan OCR en cours... ⏳</span>}
            </div>

            {errorMsg && <div style={{ color: '#ef4444', backgroundColor: '#fef2f2', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>{errorMsg}</div>}
            {successMsg && <div style={{ color: '#10b981', backgroundColor: '#ecfdf5', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>{successMsg}</div>}

            <form onSubmit={handleAddSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">N° Contrat *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: CSTR00006"
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Client *</label>
                  <select
                    className="form-select"
                    value={formData.client_id}
                    onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                    required
                  >
                    {clients.map((cli) => (
                      <option key={cli.id} value={cli.id}>
                        {cli.id} - {cli.prenom || ''} {cli.nom || cli.client || ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Type de contrat *</label>
                  <select
                    className="form-select"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    required
                  >
                    <option value="auto">Auto (1 max par client)</option>
                    <option value="habitation">Habitation (1 max par client)</option>
                    <option value="vie">Vie (1 max par client)</option>
                    <option value="sante">Santé (1 max par client)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Garantie Max (DT) *</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="ex: 150000000"
                    value={formData.garantie_max}
                    onChange={(e) => setFormData({ ...formData, garantie_max: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Prime Mensuelle (DT)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="ex: 120"
                    value={formData.prime_mensuelle}
                    onChange={(e) => setFormData({ ...formData, prime_mensuelle: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Prime Annuelle (DT)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="ex: 1440"
                    value={formData.prime_annuelle}
                    onChange={(e) => setFormData({ ...formData, prime_annuelle: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Franchise (DT)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="ex: 500"
                    value={formData.franchise}
                    onChange={(e) => setFormData({ ...formData, franchise: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Date Début *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.date_debut}
                    onChange={(e) => setFormData({ ...formData, date_debut: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Date Fin *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.date_fin}
                    onChange={(e) => setFormData({ ...formData, date_fin: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Couverture & Garanties</label>
                  <textarea
                    className="form-input"
                    rows="2"
                    value={formData.couverture}
                    onChange={(e) => setFormData({ ...formData, couverture: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Exclusions</label>
                  <textarea
                    className="form-input"
                    rows="2"
                    value={formData.exclusions}
                    onChange={(e) => setFormData({ ...formData, exclusions: e.target.value })}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Annuler
                </button>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Création...' : 'Ajouter le contrat'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
