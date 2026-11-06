import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { riskAPI } from '../services/api';

const levelStyle = {
  critique: { color: '#991b1b', background: '#fee2e2', label: 'Critique' },
  eleve: { color: '#b45309', background: '#ffedd5', label: 'Élevé' },
  moyen: { color: '#a16207', background: '#fef3c7', label: 'Moyen' },
  faible: { color: '#047857', background: '#d1fae5', label: 'Faible' },
};

export default function PrioriteRisqueView() {
  const [dossiers, setDossiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('tous');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try { setDossiers(await riskAPI.getPriorities()); }
    catch (err) { setError(err.message || 'Chargement des scores impossible.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const counts = useMemo(() => ({
    prioritaires: dossiers.filter((d) => ['critique', 'eleve'].includes(String(d.niveau).toLowerCase())).length,
    moyens: dossiers.filter((d) => String(d.niveau).toLowerCase() === 'moyen').length,
    total: dossiers.length,
  }), [dossiers]);

  const filtered = filter === 'prioritaires'
    ? dossiers.filter((d) => ['critique', 'eleve'].includes(String(d.niveau).toLowerCase()))
    : dossiers;

  return <section className="risk-page">
    <header className="risk-heading">
      <div><h1>Prévision du risque</h1><p>Repérez les dossiers qui demandent une attention prioritaire.</p></div>
      <button type="button" className="risk-refresh" onClick={load} disabled={loading}>{loading ? 'Calcul…' : 'Actualiser les scores'}</button>
    </header>

    <div className="risk-summary">
      <article><span>Dossiers évalués</span><strong>{counts.total}</strong></article>
      <article><span>À traiter en priorité</span><strong className="risk-red">{counts.prioritaires}</strong></article>
      <article><span>Surveillance conseillée</span><strong className="risk-amber">{counts.moyens}</strong></article>
    </div>

    <div className="risk-disclaimer">
      Score indicatif calculé à partir des règles métier, des sinistres connus et des informations du contrat. Il sert à prioriser une revue humaine ; ce n’est ni une probabilité de fraude ni une décision automatique.
    </div>

    <div className="risk-list-header"><h2>Dossiers par niveau d’attention</h2><select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filtrer les dossiers"><option value="tous">Tous les dossiers</option><option value="prioritaires">Priorité élevée ou critique</option></select></div>

    {error && <div className="risk-error" role="alert">{error} <button type="button" onClick={load}>Réessayer</button></div>}
    {loading ? <div className="risk-empty">Calcul des scores en cours…</div>
      : !filtered.length ? <div className="risk-empty">Aucun dossier ne correspond à ce filtre.</div>
      : <div className="risk-cards">{filtered.map((dossier) => {
        const level = levelStyle[String(dossier.niveau || 'faible').toLowerCase()] || levelStyle.faible;
        const score = Math.max(0, Math.min(100, Number(dossier.score) || 0));
        return <article key={dossier.contrat_id} className="risk-card">
          <div className="risk-card-top">
            <div><div className="risk-reference">{dossier.contrat_id} <span>· {dossier.type_contrat}</span></div><div className="risk-client">{dossier.client}</div></div>
            <span className="risk-badge" style={{ color: level.color, background: level.background }}>{level.label}</span>
          </div>
          <div className="risk-score-row"><span>Score d’attention</span><strong>{score}<small>/100</small></strong></div>
          <div className="risk-track"><div style={{ width: `${score}%`, background: level.color }} /></div>
          <div className="risk-meta"><span>{dossier.sinistres_count} sinistre(s)</span><span>Confiance : {dossier.confidence || 'faible'}</span></div>
          {dossier.facteurs?.length > 0 && <div className="risk-factors"><strong>Facteurs principaux</strong>{dossier.facteurs.slice(0, 2).map((f) => <p key={f.key}><b>{f.label}</b> — {f.detail}</p>)}</div>}
          <div className="risk-recommendation"><strong>Prochaine étape suggérée</strong><p>{dossier.recommandation}</p></div>
          {dossier.donnees_manquantes?.length > 0 && <div className="risk-missing">Informations à compléter : {dossier.donnees_manquantes.join(', ')}</div>}
        </article>;
      })}</div>}
  </section>;
}
