import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { clientsAPI, cinAPI } from '../services/api';

export default function ClientsView({ clients, contrats, onRefresh }) {
  const { isAssurances, isSinistres } = useAuth();
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [formData, setFormData] = useState({
    id: '',
    nom: '',
    prenom: '',
    cin: '',
    email: '',
    telephone: '',
    adresse: 'Tunisie',
  });

  const villesSet = new Set(clients.map((c) => c.adresse).filter(Boolean));

  const handleOpenAdd = () => {
    setErrorMsg('');
    setSuccessMsg('');
    setFormData({
      id: `CL${Math.floor(10 + Math.random() * 90)}`,
      nom: '',
      prenom: '',
      cin: '',
      email: '',
      telephone: '',
      adresse: 'Tunis Centre',
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
        setFormData((prev) => ({
          ...prev,
          nom: d.nom || prev.nom,
          prenom: d.prenom || prev.prenom,
          cin: d.cin || prev.cin,
          adresse: d.adresse || prev.adresse,
        }));
        setSuccessMsg(`✨ Données de la CIN extraites avec succès ! (CIN: ${d.cin || 'détectée'})`);
      }
    } catch (err) {
      setErrorMsg(`⚠️ Notice OCR : ${err.message || 'Informations partielles pré-remplies.'}`);
    } finally {
      setOcrLoading(false);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    // Contrôle de saisie
    if (!formData.nom.trim() || !formData.prenom.trim()) {
      setErrorMsg('Le nom et le prénom du client sont obligatoires.');
      return;
    }
    if (formData.cin && !/^\d{8}$/.test(formData.cin.trim())) {
      setErrorMsg('Le numéro de CIN doit comporter exactement 8 chiffres.');
      return;
    }

    setLoading(true);

    try {
      await clientsAPI.addClient(formData);
      setShowAddModal(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      setErrorMsg(err.message || 'Erreur lors de la création du client');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="page-clients" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">Mes clients </h1>
          <p className="page-subtitle">{clients.length} client(s) répertorié(s)</p>
        </div>
        {(isAssurances || isSinistres) && (
          <button className="btn-primary" onClick={handleOpenAdd}>
            + Ajouter un client
          </button>
        )}
      </header>

      {/* KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Clients Totaux</div>
          <div className="kpi-value">{clients.length}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Villes Couvertes</div>
          <div className="kpi-value">{villesSet.size || 1}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Contrats Rattachés</div>
          <div className="kpi-value">{contrats.length}</div>
        </div>
      </div>

      {/* Data Table */}
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>N° CLIENT</th>
              <th>NOM & PRÉNOM</th>
              <th>CIN / IDENTIFIANT</th>
              <th>EMAIL</th>
              <th>TÉLÉPHONE</th>
              <th>ADRESSE / VILLE</th>
              <th>DATE CRÉATION</th>
            </tr>
          </thead>
          <tbody>
            {clients.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                  Aucun client trouvé dans la base MySQL.
                </td>
              </tr>
            ) : (
              clients.map((c) => {
                const nameStr =
                  c.prenom || c.nom
                    ? `${c.prenom || ''} ${c.nom || ''}`.trim()
                    : c.client || 'Client Assuré';

                return (
                  <tr key={c.id}>
                    <td className="cell-bold">{c.id}</td>
                    <td className="cell-bold">{nameStr}</td>
                    <td>{c.cin || 'N/A'}</td>
                    <td>{c.email || 'N/A'}</td>
                    <td>{c.telephone || 'N/A'}</td>
                    <td>{c.adresse || 'Tunisie'}</td>
                    <td>{c.date_creation ? String(c.date_creation).split('T')[0] : '2026-08-08'}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Ajouter Client */}
      {showAddModal && (
        <div className="modal-overlay" style={{ display: 'flex' }}>
          <div className="modal-card" style={{ maxWidth: '640px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Créer un nouveau client commun</h3>
              <button className="btn-close" onClick={() => setShowAddModal(false)}>&times;</button>
            </div>

            {/* Scan CIN Box */}
            <div style={{ backgroundColor: '#f1f5f9', border: '1px dashed #64748b', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#1e293b', marginBottom: '6px' }}>
                📷 Scanner / Téleverser une photo de CIN (Remplissage Automatique OCR)
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleCINUpload}
                disabled={ocrLoading}
                style={{ fontSize: '12px' }}
              />
              {ocrLoading && <span style={{ fontSize: '11px', color: '#0284c7', marginLeft: '8px' }}>Extraction OCR en cours... ⏳</span>}
            </div>

            {errorMsg && <div style={{ color: '#ef4444', backgroundColor: '#fef2f2', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>{errorMsg}</div>}
            {successMsg && <div style={{ color: '#10b981', backgroundColor: '#ecfdf5', padding: '8px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '12px' }}>{successMsg}</div>}

            <form onSubmit={handleAddSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Nom *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: Trabelsi"
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Prénom *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder=""
                    value={formData.prenom}
                    onChange={(e) => setFormData({ ...formData, prenom: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">N° CIN (8 chiffres)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: 08849201"
                    maxLength="8"
                    value={formData.cin}
                    onChange={(e) => setFormData({ ...formData, cin: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">N° Identifiant Client</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: CL15"
                    value={formData.id}
                    onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Adresse Email</label>
                  <input
                    type="email"
                    className="form-input"
                    placeholder=""
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Téléphone</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ex: +216 98 123 456"
                    value={formData.telephone}
                    onChange={(e) => setFormData({ ...formData, telephone: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Adresse / Ville</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="ex: Sfax, Rue Habib Bourguiba"
                  value={formData.adresse}
                  onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
                />
              </div>

              <div className="modal-footer" style={{ marginTop: '20px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Annuler
                </button>
                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Création...' : 'Créer le client'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
