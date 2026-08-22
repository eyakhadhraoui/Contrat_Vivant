import React, { useState, useEffect } from 'react';
import { historiqueAPI } from '../services/api';

export default function HistoriqueView() {
  const [logs, setLogs] = useState([]);
  const [filterText, setFilterText] = useState('');
  const [filterStep, setFilterStep] = useState('');
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await historiqueAPI.getHistorique();
      setLogs(data);
    } catch (e) {
      console.error('Erreur chargement historique:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleExportPDF = async () => {
    setExporting(true);
    try {
      await historiqueAPI.downloadAuditPDF();
    } catch (e) {
      console.error('Erreur export PDF audit:', e);
      alert(e.message || "Impossible de générer le rapport PDF d'audit.");
    } finally {
      setExporting(false);
    }
  };

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      await historiqueAPI.downloadAuditCSV();
    } catch (e) {
      console.error('Erreur export CSV audit:', e);
      alert(e.message || "Impossible de générer l'export CSV.");
    } finally {
      setExporting(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    const textMatch =
      !filterText ||
      JSON.stringify(log).toLowerCase().includes(filterText.toLowerCase());

    const stepMatch =
      !filterStep ||
      (log.step || log.agent || '').toLowerCase().includes(filterStep.toLowerCase());

    return textMatch && stepMatch;
  });

  const stats = {
    total: logs.length,
    validations: logs.filter((l) => (l.step || l.action || '').toLowerCase().includes('hitl')).length,
    alerts: logs.filter((l) => (l.step || l.action || '').toLowerCase().includes('alert')).length,
    agents: logs.filter((l) => (l.step || l.action || '').toLowerCase().includes('agent')).length,
  };

  return (
    <section id="page-historique" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">Historique d'audit</h1>
          <p className="page-subtitle">
            Suivi chronologique complet des validations, décisions d'agents et notifications inter-services.
          </p>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="audit-stats-grid">
        <div className="stat-card">
          <div className="stat-card-val">{stats.total}</div>
          <div className="stat-card-lbl">ÉVÉNEMENTS D'AUDIT</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-val" style={{ color: '#10b981' }}>
            {stats.validations}
          </div>
          <div className="stat-card-lbl">VALIDATIONS HITL</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-val" style={{ color: '#f59e0b' }}>
            {stats.alerts}
          </div>
          <div className="stat-card-lbl">ALERTES & ROUTAGES</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-val" style={{ color: '#6366f1' }}>
            {stats.agents}
          </div>
          <div className="stat-card-lbl">EXÉCUTIONS MULTI-AGENTS</div>
        </div>
      </div>

      {/* Filtres */}
      <div className="search-container" style={{ marginBottom: '20px' }}>
        <input
          type="text"
          className="search-input"
          placeholder="Filtrer par contrat (CSTR...), gestionnaire, agent ou action..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
        />
        <select
          className="form-select"
          style={{ maxWidth: '260px' }}
          value={filterStep}
          onChange={(e) => setFilterStep(e.target.value)}
        >
          <option value="">Tous les événements</option>
          <option value="collector">Collecte SI (CollectorAgent)</option>
          <option value="risk">Évaluation Risques (RiskAgent)</option>
          <option value="alert">Alertes & Routage (AlertAgent)</option>
          <option value="validation">Validation Humaine (HITL)</option>
          <option value="history">Historique & Timeline SI</option>
        </select>
        <button
          className="btn-primary"
          style={{ padding: '12px 18px' }}
          onClick={fetchLogs}
          disabled={loading}
        >
          {loading ? '...' : '🔄 Rafraîchir'}
        </button>
        <button
          className="btn-secondary"
          style={{ padding: '12px 18px' }}
          onClick={handleExportPDF}
          disabled={exporting}
        >
          {exporting ? '...' : '📄 Rapport PDF'}
        </button>
        <button
          className="btn-secondary"
          style={{ padding: '12px 18px' }}
          onClick={handleExportCSV}
          disabled={exporting}
        >
          {exporting ? '...' : '📊 Exporter CSV'}
        </button>
      </div>

      {/* Data Table */}
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>HORODATAGE</th>
              <th>ÉTAPE / AGENT</th>
              <th>DOSSIER / CONTRAT</th>
              <th>ACTEUR / CIBLE</th>
              <th>DÉTAILS DE L'ACTION ET RÉSULTAT MÉTIER</th>
              <th>STATUT / RISQUE</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                  {loading ? 'Chargement du journal...' : 'Aucun événement d\'audit trouvé.'}
                </td>
              </tr>
            ) : (
              filteredLogs.map((log, idx) => (
                <tr key={idx}>
                  <td>{log.timestamp || log.date || '2026-08-09 10:00'}</td>
                  <td className="cell-bold">{log.step || log.agent || 'SystemAgent'}</td>
                  <td>{log.contrat_id || log.dossier || 'C001'}</td>
                  <td>{log.actor || log.user || 'Sarra Khelifi'}</td>
                  <td>{log.details || log.message || log.action}</td>
                  <td>
                    <span className={`status-badge status-${log.status || 'actif'}`}>
                      {log.status || 'OK'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}