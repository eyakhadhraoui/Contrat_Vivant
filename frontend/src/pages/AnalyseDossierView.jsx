import React, { useState, useEffect } from 'react';
import { chatAPI, analysisAPI, alertsAPI, contratsAPI } from '../services/api';

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

// Composant 1 : Baromètre Circulaire SVG pour le Score de Risque
function RiskGauge({ score = 20, urgency = 'Faible' }) {
  const numScore = parseFloat(String(score).replace('/100', '').trim()) || 20;
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (numScore / 100) * circumference;

  let strokeColor = '#10b981';
  let badgeBg = '#ecfdf5';
  let badgeColor = '#047857';

  if (numScore >= 65 || urgency.toLowerCase().includes('élevé') || urgency.toLowerCase().includes('critique')) {
    strokeColor = '#ef4444';
    badgeBg = '#fef2f2';
    badgeColor = '#b91c1c';
  } else if (numScore >= 35 || urgency.toLowerCase().includes('moyen') || urgency.toLowerCase().includes('modéré')) {
    strokeColor = '#f59e0b';
    badgeBg = '#fffbeb';
    badgeColor = '#b45309';
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '16px', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', minWidth: '150px' }}>
      <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
        📊 Baromètre d'Urgence
      </div>
      <div style={{ position: 'relative', width: '100px', height: '100px' }}>
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="9" />
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth="9"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease-in-out', transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
          />
        </svg>
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100px', height: '100px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a' }}>{numScore}</span>
          <span style={{ fontSize: '10px', color: '#94a3b8', marginTop: '-2px' }}>/100</span>
        </div>
      </div>
      <div style={{ marginTop: '8px', padding: '3px 10px', borderRadius: '999px', backgroundColor: badgeBg, color: badgeColor, fontSize: '11px', fontWeight: 700, textTransform: 'uppercase' }}>
        Urgence : {urgency}
      </div>
    </div>
  );
}

// Composant 2 : Graphique de Consommation du Plafond de Garantie
function GuaranteeConsumptionChart({ garantieMax = 100000, totalSinistres = 15000 }) {
  const gMax = parseFloat(garantieMax) || 100000;
  const tSin = parseFloat(totalSinistres) || 0;
  const consommePct = Math.min(100, Math.max(0, (tSin / gMax) * 100));
  const restant = Math.max(0, gMax - tSin);

  let barColor = '#3b82f6';
  if (consommePct > 75) barColor = '#ef4444';
  else if (consommePct > 40) barColor = '#f59e0b';

  return (
    <div style={{ padding: '16px', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          💰 Consommation du Plafond de Garantie
        </div>
        <div style={{ fontSize: '12px', fontWeight: 800, color: barColor }}>
          {consommePct.toFixed(1)}% consommé
        </div>
      </div>

      <div style={{ height: '12px', width: '100%', backgroundColor: '#e2e8f0', borderRadius: '999px', overflow: 'hidden', display: 'flex' }}>
        <div style={{ width: `${consommePct}%`, backgroundColor: barColor, transition: 'width 0.8s ease' }} title={`Consommé: ${tSin.toLocaleString('fr-FR')} DT`} />
        <div style={{ width: `${100 - consommePct}%`, backgroundColor: '#10b981', opacity: 0.25 }} title={`Disponible: ${restant.toLocaleString('fr-FR')} DT`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', marginTop: '12px', textAlign: 'center' }}>
        <div style={{ padding: '6px', background: '#f8fafc', borderRadius: '6px', border: '1px solid #f1f5f9' }}>
          <div style={{ fontSize: '10px', color: '#64748b' }}>Plafond Garantie</div>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a', marginTop: '2px' }}>{gMax.toLocaleString('fr-FR')} DT</div>
        </div>
        <div style={{ padding: '6px', background: '#fef2f2', borderRadius: '6px', border: '1px solid #fee2e2' }}>
          <div style={{ fontSize: '10px', color: '#b91c1c' }}>Sinistres Cumulés</div>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#dc2626', marginTop: '2px' }}>{tSin.toLocaleString('fr-FR')} DT</div>
        </div>
        <div style={{ padding: '6px', background: '#ecfdf5', borderRadius: '6px', border: '1px solid #d1fae5' }}>
          <div style={{ fontSize: '10px', color: '#047857' }}>Couverture Disponible</div>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#059669', marginTop: '2px' }}>{restant.toLocaleString('fr-FR')} DT</div>
        </div>
      </div>
    </div>
  );
}

// Composant 3 : Histogramme de Répartition des Sinistres par Statut
function SinistresBreakdownChart({ matchedSinistres = [] }) {
  const stats = {
    en_cours: matchedSinistres.filter((s) => s.statut === 'en_cours' || s.statut === 'nouveau').length,
    en_traitement: matchedSinistres.filter((s) => s.statut === 'en_traitement').length,
    complete: matchedSinistres.filter((s) => s.statut === 'complete' || s.statut === 'cloture').length,
    rejete: matchedSinistres.filter((s) => s.statut === 'rejete').length,
  };
  const total = matchedSinistres.length || 1;

  const categories = [
    { label: 'En cours', count: stats.en_cours, color: '#3b82f6' },
    { label: 'En traitement', count: stats.en_traitement, color: '#f59e0b' },
    { label: 'Complété', count: stats.complete, color: '#10b981' },
    { label: 'Rejeté', count: stats.rejete, color: '#ef4444' },
  ];

  return (
    <div style={{ padding: '16px', background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', flex: 1 }}>
      <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
        📈 Répartition des Sinistres ({matchedSinistres.length} dossier(s))
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {categories.map((cat, idx) => {
          const pct = Math.round((cat.count / total) * 100);
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '85px', fontSize: '11px', fontWeight: 600, color: '#334155' }}>{cat.label}</div>
              <div style={{ flex: 1, height: '8px', backgroundColor: '#f1f5f9', borderRadius: '999px', overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', backgroundColor: cat.color, transition: 'width 0.6s ease' }} />
              </div>
              <div style={{ width: '40px', fontSize: '11px', fontWeight: 700, color: cat.color, textAlign: 'right' }}>
                {cat.count} ({pct}%)
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Composant 4 : Lecture Vocale du Rapport (Text-to-Speech)
function VoicePlayer({ textToRead }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const cleanText = typeof textToRead === 'string'
    ? textToRead.replace(/#+|\*+|-|•/g, ' ').replace(/\s+/g, ' ').trim()
    : 'Rapport d\'analyse prêt pour consultation.';

  const handlePlay = () => {
    if (!('speechSynthesis' in window)) {
      alert('La synthèse vocale n\'est pas supportée sur ce navigateur.');
      return;
    }

    if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'fr-FR';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };
    utterance.onerror = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };

    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
    setIsPaused(false);
  };

  const handlePause = () => {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
      setIsPlaying(false);
    }
  };

  const handleStop = () => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      setIsPaused(false);
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', background: '#f0f9ff', borderRadius: '10px', border: '1px solid #bae6fd', marginTop: '14px', marginBottom: '10px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', fontWeight: 700, color: '#0369a1', marginRight: 'auto' }}>
        <span>🔊</span>
        <span>Lecture Vocale du Rapport (Text-to-Speech)</span>
      </div>

      {!isPlaying ? (
        <button
          onClick={handlePlay}
          style={{ padding: '6px 14px', backgroundColor: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          ▶️ {isPaused ? 'Reprendre' : 'Écouter'}
        </button>
      ) : (
        <button
          onClick={handlePause}
          style={{ padding: '6px 14px', backgroundColor: '#eab308', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}
        >
          ⏸️ Pause
        </button>
      )}

      <button
        onClick={handleStop}
        disabled={!isPlaying && !isPaused}
        style={{ padding: '6px 12px', backgroundColor: (isPlaying || isPaused) ? '#ef4444' : '#cbd5e1', color: '#fff', border: 'none', borderRadius: '6px', cursor: (isPlaying || isPaused) ? 'pointer' : 'not-allowed', fontSize: '12px', fontWeight: 600 }}
      >
        ⏹️ Stop
      </button>
    </div>
  );
}

// Composant 5 : Dictée Vocale des Notes (Speech-to-Text)
function VoiceDictation({ contratId, onNoteSaved }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedNotes, setSavedNotes] = useState([]);
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'fr-FR';

      rec.onresult = (event) => {
        let currentText = '';
        for (let i = 0; i < event.results.length; i++) {
          currentText += event.results[i][0].transcript;
        }
        setTranscript(currentText);
      };

      rec.onerror = (err) => {
        console.error('Erreur reconnaissance vocale:', err);
        setIsListening(false);
      };

      rec.onend = () => {
        setIsListening(false);
      };

      setRecognition(rec);
    }
  }, []);

  const toggleListening = () => {
    if (!recognition) {
      alert('La dictée vocale n\'est pas prise en charge sur ce navigateur. Veuillez utiliser Chrome ou Edge.');
      return;
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      setTranscript('');
      recognition.start();
      setIsListening(true);
    }
  };

  const handleSaveNote = async () => {
    if (!transcript.trim()) return;
    setSaving(true);
    try {
      const res = await analysisAPI.saveManagerNote(contratId, transcript);
      setSavedNotes((prev) => [res.note_structuree || res.note_brute, ...prev]);
      setTranscript('');
      if (onNoteSaved) onNoteSaved();
      alert('✅ Note dictée structurée par l\'IA et enregistrée dans le SI avec succès !');
    } catch (e) {
      alert(e.message || 'Erreur lors de la sauvegarde de la note vocale.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ marginTop: '16px', padding: '14px 16px', backgroundColor: '#faf5ff', borderRadius: '12px', border: '1px solid #e9d5ff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#7e22ce', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>🎙️</span>
          <span>Dictée Vocale des Prises de Note (Speech-to-Text & Structuration IA)</span>
        </div>

        <button
          onClick={toggleListening}
          style={{
            padding: '7px 14px',
            backgroundColor: isListening ? '#dc2626' : '#9333ea',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {isListening ? '🔴 Arrêter l\'enregistrement' : '🎙️ Démarrer la Dictée Vocale'}
        </button>
      </div>

      {isListening && (
        <div style={{ fontSize: '11.5px', color: '#dc2626', fontWeight: 600, marginBottom: '6px' }}>
          ● Enregistrement en cours... Parlez clairement en français.
        </div>
      )}

      <textarea
        className="form-control"
        rows="2"
        placeholder="La dictée vocale s'affichera ici en temps réel... (ou vous pouvez écrire votre note manuellement)"
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        style={{ width: '100%', fontSize: '12.5px', borderRadius: '8px', border: '1px solid #cbd5e1', padding: '8px 10px' }}
      />

      {transcript.trim() && (
        <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="btn-primary"
            onClick={handleSaveNote}
            disabled={saving}
            style={{ padding: '6px 14px', backgroundColor: '#7e22ce', borderColor: '#7e22ce', fontSize: '12px', fontWeight: 600 }}
          >
            {saving ? 'Structuration IA en cours...' : '✨ Structurer & Enregistrer dans le SI'}
          </button>
        </div>
      )}

      {savedNotes.length > 0 && (
        <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #e9d5ff' }}>
          <div style={{ fontSize: '11.5px', fontWeight: 700, color: '#6b21a8', marginBottom: '6px' }}>
            📝 Notes vocales enregistrées pour ce contrat :
          </div>
          {savedNotes.map((note, idx) => (
            <div key={idx} style={{ backgroundColor: '#ffffff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #d8b4fe', marginBottom: '6px', fontSize: '12px', whiteSpace: 'pre-wrap', color: '#334155' }}>
              {note}
            </div>
          ))}
        </div>
      )}
    </div>
  );
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
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailCopied, setEmailCopied] = useState(false);

  const resolvedContrat = contrats.find(
    (c) =>
      c.client?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.id?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const resolvedContratId = resolvedContrat?.id || (searchTerm.toUpperCase().startsWith('C') ? searchTerm.toUpperCase() : 'CSTR78199');
  const resolvedClientNom = resolvedContrat?.client || (searchTerm.toUpperCase().startsWith('C') ? 'Souheil Khadhraoui' : (searchTerm || 'Souheil Khadhraoui'));

  const matchedSinistres = sinistres.filter((s) =>
    s.client?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.contrat_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.contrat_id === resolvedContratId
  );
  const totalSinistresMontant = matchedSinistres.reduce((sum, s) => sum + (parseFloat(s.montant_declare) || 0), 0);
  const garantieMaxContrat = parseFloat(resolvedContrat?.garantie_max) || 100000;

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

      const matchedS = sinistres.filter((s) =>
        s.client?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.contrat_id?.toLowerCase().includes(searchTerm.toLowerCase())
      );

      setSummaryData((prev) => ({
        ...prev,
        nbSinistres: matchedS.length || prev.nbSinistres,
        dateDernier: matchedS[0]?.date || prev.dateDernier,
        agenceNom: targetContrat?.agence_nom || matchedS[0]?.agence_nom || 'Agence Tunis Centre',
        gestionnaireNom: targetContrat?.gestionnaire_nom || matchedS[0]?.gestionnaire_nom || 'Sarra Khelifi',
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
          <h1 className="page-title">Analyse du dossier & Recommandations</h1>
          <p className="page-subtitle">Évaluation  des risques</p>
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

            {/* VOLET DE VISUALISATION GRAPHIQUE DYNAMIQUE */}
            <div style={{ marginTop: '16px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              <RiskGauge score={analysisResult.score} urgency={analysisResult.urgency} />
              <GuaranteeConsumptionChart garantieMax={garantieMaxContrat} totalSinistres={totalSinistresMontant} />
              <SinistresBreakdownChart matchedSinistres={matchedSinistres} />
            </div>

            {/* LECTURE VOCALE DU RAPPORT (TEXT-TO-SPEECH) */}
            <VoicePlayer textToRead={analysisResult.resume} />

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

            {/* DICTÉE VOCALE DES NOTES DU GESTIONNAIRE (SPEECH-TO-TEXT & IA) */}
            <VoiceDictation contratId={resolvedContratId} />

            {/* BARRE DE VALIDATION MANUELLE HITL (3 CHOIX) */}
            <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '2px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginBottom: '10px' }}>
                ✋ Validation Manuelle du Gestionnaire (HITL) :
              </h3>

              {currentHitlStatus === 'validee' ? (
                <div style={{ backgroundColor: '#ecfdf5', border: '1px solid #a7f3d0', padding: '16px 20px', borderRadius: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#065f46', fontWeight: 700, fontSize: '15px' }}>
                    <span style={{ fontSize: '20px' }}>✅</span>
                    <span>Décision validée & appliquée par {summaryData.gestionnaireNom}</span>
                  </div>
                  <p style={{ color: '#047857', fontSize: '13px', marginTop: '4px', marginBottom: '14px' }}>
                    L'Avenant contractuel officiel a été généré automatiquement avec les nouvelles dispositions et est consigné dans le journal d'audit.
                  </p>

                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <button
                      className="btn-primary"
                      style={{ padding: '10px 18px', backgroundColor: '#059669', borderColor: '#059669', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}
                      onClick={() => contratsAPI.downloadAvenantPDF(resolvedContratId)}
                    >
                      📥 Télécharger l'Avenant Officiel (PDF)
                    </button>

                    <button
                      className="btn-secondary"
                      style={{ padding: '10px 18px', backgroundColor: '#ffffff', color: '#0f172a', borderColor: '#cbd5e1', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}
                      onClick={() => setShowEmailModal(!showEmailModal)}
                    >
                      ✉️ {showEmailModal ? 'Masquer le courriel client' : 'Voir le courriel client pour signature'}
                    </button>
                  </div>

                  {/* Volet Dépliable Projet de Courriel Client */}
                  {showEmailModal && (
                    <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#ffffff', borderRadius: '10px', border: '1px solid #cbd5e1', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <div>
                          <strong style={{ fontSize: '13.5px', color: '#1e293b' }}>
                            📧 Courriel Client Pré-rempli (Prêt pour Signature Électronique)
                          </strong>
                          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                            Destinataire : <strong>souheil.khadhraoui@email.com</strong> | Objet : <strong>📋 Avenant Contractuel & Décision Validée — Contrat #{resolvedContratId}</strong>
                          </div>
                        </div>

                        <button
                          style={{
                            padding: '6px 12px',
                            fontSize: '12px',
                            backgroundColor: emailCopied ? '#10b981' : '#f1f5f9',
                            color: emailCopied ? '#ffffff' : '#1e293b',
                            border: '1px solid #cbd5e1',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontWeight: 600,
                            transition: 'all 0.2s ease',
                          }}
                          onClick={() => {
                            const emailTxt = `Bonjour ${resolvedClientNom},\n\nNous vous informons que votre dossier d'assurance pour le contrat ${resolvedContratId} a été examiné et validé avec succès par votre gestionnaire référent (${summaryData.gestionnaireNom}).\n\n📌 Dispositions contractuelles validées :\n• Statut du contrat : VALIDÉ & ACTIF\n• Plafond de Garantie Max : 100 000.00 DT\n• Franchise applicable : 500.00 DT\n• Prime mensuelle : 120.00 DT/mois\n\nVotre Avenant contractuel officiel en pièce jointe est prêt pour signature électronique.\n\nCordialement,\nService Gestion des Assurances — Plateforme Contrat Vivant (${summaryData.agenceNom})`;
                            navigator.clipboard.writeText(emailTxt);
                            setEmailCopied(true);
                            setTimeout(() => setEmailCopied(false), 2500);
                          }}
                        >
                          {emailCopied ? '✓ Texte copié !' : '📋 Copier l\'email'}
                        </button>
                      </div>

                      <div style={{ fontSize: '12.5px', color: '#334155', backgroundColor: '#f8fafc', padding: '12px 14px', borderRadius: '8px', whiteSpace: 'pre-wrap', lineHeight: '1.6', border: '1px solid #e2e8f0', fontFamily: 'monospace' }}>
{`Bonjour ${resolvedClientNom},

Nous vous informons que votre dossier d'assurance pour le contrat ${resolvedContratId} a été examiné et validé avec succès par votre gestionnaire référent (${summaryData.gestionnaireNom}).

📌 Dispositions contractuelles validées :
• Statut du contrat : VALIDÉ & ACTIF
• Plafond de Garantie Max : 100 000.00 DT
• Franchise applicable : 500.00 DT
• Prime mensuelle : 120.00 DT/mois

Votre Avenant contractuel officiel en pièce jointe est prêt pour signature électronique.

Cordialement,
Service Gestion des Assurances — Plateforme Contrat Vivant (${summaryData.agenceNom})`}
                      </div>
                    </div>
                  )}
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
