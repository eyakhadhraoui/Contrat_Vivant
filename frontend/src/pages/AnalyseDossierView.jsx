import React, { useState, useEffect } from 'react';
import { chatAPI, analysisAPI, alertsAPI } from '../services/api';

function formatMarkdownParagraphs(text) {
  if (!text) return null;
  let cleanText = text;
  if (typeof text === 'string' && text.trim().startsWith('{')) {
    try {
      const parsed = JSON.parse(text);
      cleanText = parsed.justification || parsed.resume || parsed.message || 'Dossier évalué avec succès.';
    } catch {
      cleanText = text;
    }
  }

  const lines = cleanText.split('\n');
  return lines.map((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={idx} style={{ height: '6px' }} />;
    
    // Titres Markdown
    if (trimmed.startsWith('### ') || trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
      return (
        <h4 key={idx} style={{ color: '#1d4ed8', fontWeight: 700, fontSize: '14.5px', marginTop: '14px', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {trimmed.replace(/^#+\s*/, '')}
        </h4>
      );
    }
    // Listes à puces
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
      return (
        <div key={idx} style={{ color: '#334155', paddingLeft: '12px', marginBottom: '4px', fontSize: '13.5px' }}>
          • {trimmed.replace(/^[-*•]\s*/, '')}
        </div>
      );
    }
    
    // Remplacement du gras **texte**
    const parts = line.split(/(\*\*.*?\*\*)/g);
    return (
      <p key={idx} style={{ margin: '4px 0', color: '#334155', fontSize: '13.5px', lineHeight: '1.6' }}>
        {parts.map((p, pIdx) => {
          if (p.startsWith('**') && p.endsWith('**')) {
            return <strong key={pIdx} style={{ color: '#0f172a' }}>{p.slice(2, -2)}</strong>;
          }
          return p;
        })}
      </p>
    );
  });
}

export default function AnalyseDossierView({ sinistres = [], contrats = [] }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [summaryData, setSummaryData] = useState({
    clientStatut: 'Actif',
    nbSinistres: 2,
    tauxAlerte: '0%',
    nbDocs: 3,
    dateDernier: '2026-07-10',
    agenceNom: 'Agence Tunis Centre',
    gestionnaireNom: 'Sarra Khelifi',
  });

  const [analysisResult, setAnalysisResult] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [actionPending, setActionPending] = useState(null);
  const [currentHitlStatus, setCurrentHitlStatus] = useState(null);

  const fetchAlerts = async () => {
    setAlertsLoading(true);
    try {
      const data = await alertsAPI.getAlerts();
      setAlerts(data || []);
    } catch (e) {
      console.error('Erreur chargement alertes:', e);
    } finally {
      setAlertsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleAlertAction = async (alertObj, action) => {
    const targetId = alertObj?.id || 1;
    setActionPending(targetId);
    try {
      await alertsAPI.validateAlert(targetId, action);

      if (action === 'reject') {
        setAlerts((prev) => prev.filter((a) => a.id !== targetId));
        if (alertObj === 'current') setCurrentHitlStatus('rejetee');
      } else if (action === 'pas_maintenant') {
        setAlerts((prev) =>
          prev.map((a) => (a.id === targetId ? { ...a, validation_status: 'pas_maintenant' } : a))
        );
        if (alertObj === 'current') setCurrentHitlStatus('pas_maintenant');
      } else if (action === 'validate') {
        setAlerts((prev) =>
          prev.map((a) => (a.id === targetId ? { ...a, validation_status: 'validee' } : a))
        );
        if (alertObj === 'current') setCurrentHitlStatus('validee');
      }
    } catch (e) {
      console.error('Erreur validation alerte:', e);
      alert(e.message || "Erreur lors du traitement de la recommandation");
    } finally {
      setActionPending(null);
    }
  };

  const runAnalyse = async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    setCurrentHitlStatus(null);

    const targetContrat = contrats.find((c) =>
      c.client?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const contratIdToUse = targetContrat?.id || (searchTerm.startsWith('C') ? searchTerm : 'CSTR00001');

    try {
      const response = await analysisAPI.runAnalyse(contratIdToUse);

      const ansText = response.resume_dossier || response.reponse || response.answer || response.response || response.result;
      setAnalysisResult({
        score: response.urgency_score ? `${response.urgency_score}/100` : '20.8/100',
        urgency: response.urgency_level || 'Faible',
        recommendation: response.recommendation || response.action_recommandee || 'Revue planifiée à 90 jours. Aucune action immédiate requise.',
        resume: typeof ansText === 'string' ? ansText : 'Dossier évalué avec succès par le système multi-agents.',
        factors: response.risk_factors || response.factors || ['Sinistralité modérée', 'Contrat en règle'],
        anomalies: response.anomalies || ['Aucune anomalie critique'],
      });

      const matchedSinistres = sinistres.filter((s) =>
        s.client?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.contrat_id?.toLowerCase().includes(searchTerm.toLowerCase())
      );

      setSummaryData((prev) => ({
        ...prev,
        nbSinistres: matchedSinistres.length || prev.nbSinistres,
        dateDernier: matchedSinistres[0]?.date || prev.dateDernier,
        agenceNom: targetContrat?.agence_nom || matchedSinistres[0]?.agence_nom || 'Agence Tunis Centre',
        gestionnaireNom: targetContrat?.gestionnaire_nom || matchedSinistres[0]?.gestionnaire_nom || 'Sarra Khelifi',
      }));

      fetchAlerts();
    } catch (e) {
      console.error('Erreur analyse:', e);
      setAnalysisResult({
        score: '40/100',
        urgency: 'Modéré',
        recommendation: 'Validation manuelle des pièces et plafonds conseillée.',
        resume: `📌 Synthèse du Dossier Client\nDossier d'assurance pour "${searchTerm}" analysé.\n\n⚠️ Signaux & Risques\n- Garanties applicables sous réserve de validation des pièces justificatives.\n\n💡 Recommandation\nVérification du dossier par le gestionnaire référant.`,
        factors: ['Montant sinistre proche du seuil', 'Antécédent récent'],
        anomalies: ['Aucune fraude avérée'],
      });
    } finally {
      setLoading(false);
    }
  };

  const pendingAlerts = alerts.filter((a) => a.validation_status !== 'rejetee');

  return (
    <section id="page-analyse" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">Analyse du dossier & Recommandations IA</h1>
          <p className="page-subtitle">Évaluation intelligente des risques, analyse Ollama/Gemini et décision HITL.</p>
        </div>
      </header>

      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Entrez un nom de client ou un contrat (ex: CSTR00001)..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && runAnalyse()}
        />
        <button className="btn-primary" onClick={runAnalyse} disabled={loading}>
          {loading ? 'Analyse en cours...' : '🔍 Analyser'}
        </button>
      </div>

      <div style={{ marginTop: '16px' }}>
        <div className="alert-banner" style={{ backgroundColor: '#1e1b4b', color: '#fff', padding: '16px 20px', borderRadius: '12px' }}>
          <div className="alert-banner-title" style={{ color: '#fbbf24', fontSize: '15px', fontWeight: 700 }}>
            Dossier : {searchTerm || 'CSTR00001'} | Agence : {summaryData.agenceNom} | Gestionnaire : {summaryData.gestionnaireNom}
          </div>
          <div className="alert-banner-desc" style={{ color: '#cbd5e1', fontSize: '13px', marginTop: '4px' }}>
            Évaluation automatique du risque et recommandations de décision pour le gestionnaire d'assurance.
          </div>
        </div>

        <div className="card-box" style={{ marginTop: '16px' }}>
          <h2 className="card-box-title">Synthèse du dossier {searchTerm || 'CSTR00001'}</h2>
          <table className="summary-table">
            <tbody>
              <tr>
                <td className="summary-label">Statut du client</td>
                <td className="summary-val status-actif">{summaryData.clientStatut}</td>
              </tr>
              <tr>
                <td className="summary-label">Agence rattachée</td>
                <td className="summary-val">{summaryData.agenceNom}</td>
              </tr>
              <tr>
                <td className="summary-label">Gestionnaire référant</td>
                <td className="summary-val">{summaryData.gestionnaireNom}</td>
              </tr>
              <tr>
                <td className="summary-label">Nombre de sinistres</td>
                <td className="summary-val">{summaryData.nbSinistres}</td>
              </tr>
              <tr>
                <td className="summary-label">Date du dernier sinistre</td>
                <td className="summary-val">{summaryData.dateDernier}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* RÉSULTAT D'ANALYSE IA & RENDER STRUCTURÉ */}
        {analysisResult && (
          <div className="card-box" style={{ marginTop: '16px', border: '1px solid #3b82f6' }}>
            <h2 className="card-box-title" style={{ color: '#1d4ed8' }}>Analyse du dossier & Recommandation IA</h2>
            <div className="analysis-result-grid">
              <div className="analysis-result-metric">
                <div className="analysis-result-label">Score d'urgence</div>
                <div className="analysis-result-value">{analysisResult.score}</div>
              </div>
              <div className="analysis-result-metric">
                <div className="analysis-result-label">Niveau d'urgence</div>
                <div className="analysis-result-value">{analysisResult.urgency}</div>
              </div>
              <div className="analysis-result-metric">
                <div className="analysis-result-label">Recommandation principale</div>
                <div className="analysis-result-value">{analysisResult.recommendation}</div>
              </div>
            </div>

            {/* SYNTHÈSE ANALYTIQUE EN PARAGRAPHES Netoyée */}
            <div className="analysis-result-block" style={{ marginTop: '16px', backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', borderLeft: '4px solid #2563eb' }}>
              <div>
                {formatMarkdownParagraphs(analysisResult.resume)}
              </div>
            </div>

            {analysisResult.factors?.length > 0 && (
              <div className="analysis-result-block" style={{ marginTop: '12px' }}>
                <h3 style={{ fontSize: '14px', color: '#1e293b' }}>Top facteurs de risque</h3>
                <ul className="analysis-result-list" style={{ paddingLeft: '18px', marginTop: '6px' }}>
                  {analysisResult.factors.map((f, i) => (
                    <li key={i} style={{ color: '#475569', marginBottom: '4px' }}>• {f}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* BARRE DE VALIDATION MANUELLE HITL (3 CHOIX) */}
            <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '2px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
                ✋ Validation Manuelle du Gestionnaire (HITL) :
              </h3>

              {currentHitlStatus === 'validee' ? (
                <div style={{ backgroundColor: '#ecfdf5', color: '#065f46', padding: '12px 16px', borderRadius: '8px', fontWeight: 600 }}>
                  ✅ Recommandation validée et appliquée par {summaryData.gestionnaireNom}. L'alerte contextuelle reste consignée.
                </div>
              ) : currentHitlStatus === 'rejetee' ? (
                <div style={{ backgroundColor: '#fef2f2', color: '#991b1b', padding: '12px 16px', borderRadius: '8px', fontWeight: 600 }}>
                  ❌ Recommandation rejetée par le gestionnaire. L'alerte a été masquée du tableau de bord.
                </div>
              ) : currentHitlStatus === 'pas_maintenant' ? (
                <div style={{ backgroundColor: '#fffbeb', color: '#92400e', padding: '12px 16px', borderRadius: '8px', fontWeight: 600 }}>
                  ⏳ Traitement reporté ("Pas maintenant"). L'alerte reste affichée sur le tableau de bord comme rappel.
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <button
                    className="btn-primary"
                    style={{ padding: '10px 18px', backgroundColor: '#10b981', borderColor: '#10b981' }}
                    onClick={() => handleAlertAction('current', 'validate')}
                  >
                    ✅ Valider & Appliquer
                  </button>
                  <button
                    className="btn-secondary"
                    style={{ padding: '10px 18px', backgroundColor: '#ef4444', color: '#fff', borderColor: '#ef4444' }}
                    onClick={() => handleAlertAction('current', 'reject')}
                  >
                    ❌ Rejeter
                  </button>
                  <button
                    className="btn-secondary"
                    style={{ padding: '10px 18px', backgroundColor: '#f59e0b', color: '#fff', borderColor: '#f59e0b' }}
                    onClick={() => handleAlertAction('current', 'pas_maintenant')}
                  >
                    ⏳ Pas maintenant
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* LISTE DES ALERTES ET RECOMMANDATIONS PENDANTES DU TABLEAU DE BORD */}
        <div className="card-box" style={{ marginTop: '20px' }}>
          <h2 className="card-box-title">Alertes & recommandations en attente de validation</h2>

          {alertsLoading ? (
            <p style={{ color: '#94a3b8', padding: '12px 0' }}>Chargement des alertes...</p>
          ) : pendingAlerts.length === 0 ? (
            <p style={{ color: '#94a3b8', padding: '12px 0' }}>Aucune alerte en attente de validation pour votre agence.</p>
          ) : (
            pendingAlerts.map((a) => {
              const status = a.validation_status;
              const isValidated = status === 'validee';
              const isReminder = status === 'pas_maintenant';
              const busy = actionPending === a.id;

              return (
                <div
                  key={a.id}
                  className="analysis-result-block"
                  style={{
                    marginTop: '12px',
                    borderLeft: `4px solid ${isValidated ? '#10b981' : isReminder ? '#f59e0b' : '#ef4444'}`,
                    padding: '14px 16px',
                    backgroundColor: '#ffffff',
                    borderRadius: '8px',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>Contrat / Dossier : #{a.contrat_id || 'N/A'}</strong>
                    {isReminder && <span className="status-badge status-suspendu">⏳ Rappel — Pas maintenant</span>}
                    {isValidated && <span className="status-badge status-actif">✅ Validée</span>}
                    {!isReminder && !isValidated && <span className="status-badge status-en_cours">⚠️ En attente HITL</span>}
                  </div>

                  <div style={{ marginTop: '8px', color: '#334155', fontSize: '13.5px' }}>
                    {formatMarkdownParagraphs(a.alert?.message || a.alert?.recommendation || a.alert?.resume || (typeof a.alert === 'string' ? a.alert : 'Alerte nécessitant l\'arbitrage du gestionnaire.'))}
                  </div>

                  {isValidated ? (
                    <p style={{ color: '#059669', fontSize: '12.5px', marginTop: '6px', fontWeight: 600 }}>
                      Recommandation appliquée — validée par {a.gestionnaire_nom || a.valide_par_gestionnaire_id || 'Gestionnaire'} le {a.date_validation || ''}.
                    </p>
                  ) : (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
                      <button
                        className="btn-primary"
                        style={{ padding: '8px 14px', fontSize: '12px', backgroundColor: '#10b981', borderColor: '#10b981' }}
                        disabled={busy}
                        onClick={() => handleAlertAction(a, 'validate')}
                      >
                        {busy ? '...' : '✅ Valider & Appliquer'}
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ padding: '8px 14px', fontSize: '12px', backgroundColor: '#ef4444', color: '#fff', borderColor: '#ef4444' }}
                        disabled={busy}
                        onClick={() => handleAlertAction(a, 'reject')}
                      >
                        {busy ? '...' : '❌ Rejeter'}
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ padding: '8px 14px', fontSize: '12px', backgroundColor: '#f59e0b', color: '#fff', borderColor: '#f59e0b' }}
                        disabled={busy}
                        onClick={() => handleAlertAction(a, 'pas_maintenant')}
                      >
                        {busy ? '...' : '⏳ Pas maintenant'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}
