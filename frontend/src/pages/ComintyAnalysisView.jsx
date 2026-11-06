import React, { useEffect, useState } from 'react';
import { getAuthHeaders } from '../services/api';

const AGENT_LABELS = ['Extraction documentaire', 'Détection d’anomalies', 'Analyse des risques', 'Rapport de synthèse'];
const severity = (value) => ({ High: 'Élevé', Medium: 'Moyen', Low: 'Faible' }[value] || value || 'À examiner');

export default function ComintyAnalysisView() {
  const [analyses, setAnalyses] = useState([]);
  const [selected, setSelected] = useState(null);
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [compareA, setCompareA] = useState(null);
  const [compareB, setCompareB] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [priorityList, setPriorityList] = useState(null);
  const [clarification, setClarification] = useState(null);
  const [checklist, setChecklist] = useState(null);
  const [actionBusy, setActionBusy] = useState('');

  const refresh = async () => {
    const response = await fetch('/api/contract-analysis', { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Impossible de charger les rapports.');
    const data = await response.json(); setAnalyses(data);
  };
  useEffect(() => { refresh().catch(() => {}); }, []);

  const submit = async (event) => {
    event.preventDefault(); if (!file) return;
    setBusy(true); setError(''); setSelected(null);
    try {
      const response = await fetch('/api/contract-analysis', { method: 'POST', headers: getAuthHeaders(), body: (() => { const form = new FormData(); form.append('file', file); return form; })() });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'L’analyse a échoué.');
      setSelected(data); setFile(null); event.target.reset(); await refresh();
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const download = async (item) => {
    const response = await fetch(`/api/contract-analysis/${item.id}/report.pdf`, { headers: getAuthHeaders() });
    if (!response.ok) { setError('Téléchargement du rapport impossible.'); return; }
    const url = URL.createObjectURL(await response.blob()); const link = document.createElement('a'); link.href = url; link.download = `Analyse_${item.filename.replace(/\.pdf$/i, '')}.pdf`; link.click(); URL.revokeObjectURL(url);
  };
  const runCompare = async (event) => {
    event.preventDefault(); if (!compareA || !compareB) return;
    setActionBusy('compare'); setError(''); setComparison(null);
    try { const form = new FormData(); form.append('version_a', compareA); form.append('version_b', compareB); const response = await fetch('/api/contract-analysis/compare', { method: 'POST', headers: getAuthHeaders(), body: form }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Comparaison impossible.'); setComparison(data); }
    catch (e) { setError(e.message); } finally { setActionBusy(''); }
  };
  const runAction = async (key, path, payload) => {
    if (!current) return; setActionBusy(key); setError('');
    try { const response = await fetch(`/api/contract-analysis/${current.id}/${path}`, { method: 'POST', headers: { ...getAuthHeaders(), ...(payload ? { 'Content-Type': 'application/json' } : {}) }, ...(payload ? { body: JSON.stringify(payload) } : {}) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Action Cominty impossible.'); if (key === 'ask') setAnswer(data); if (key === 'clarification') setClarification(data); if (key === 'compliance') setChecklist(data); }
    catch (e) { setError(e.message); } finally { setActionBusy(''); }
  };
  const runPriority = async () => {
    setActionBusy('priority'); setError('');
    try { const response = await fetch('/api/contract-analysis/prioritize', { method: 'POST', headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ analysis_ids: analyses.map(item => item.id) }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Classement impossible.'); setPriorityList(data); }
    catch (e) { setError(e.message); } finally { setActionBusy(''); }
  };
  const current = selected || analyses[0];
  const card = { background: '#fff', border: '1px solid #e3e9f0', borderRadius: 14, padding: 20, boxShadow: '0 4px 18px rgba(21,43,72,.04)' };
  const title = { color: '#142b4a', fontSize: 15, fontWeight: 750, marginBottom: 12 };
  const button = { border: 0, borderRadius: 9, color: '#fff', background: '#173b63', fontWeight: 700, padding: '11px 16px', cursor: busy ? 'wait' : 'pointer' };

  return <section style={{ maxWidth: 1200, margin: '0 auto', color: '#243247' }}>
    <header style={{ marginBottom: 22 }}><div style={{ color: '#3674ad', fontSize: 12, fontWeight: 800, letterSpacing: 1.3 }}>INSURAGENT AI · COMINTY</div><h1 style={{ color: '#142b4a', margin: '7px 0', fontSize: 28 }}>Analyse de contrats</h1><div style={{ color: '#6b7788' }}>Quatre agents managés examinent votre contrat et préparent un rapport PDF.</div></header>
    {error && <div role="alert" style={{ ...card, marginBottom: 16, borderColor: '#f2c7c4', background: '#fff7f6', color: '#9d3028' }}>{error}</div>}
    <div style={{ ...card, marginBottom: 20 }}><h2 style={title}>Téléverser un contrat</h2><form onSubmit={submit} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}><input type="file" accept="application/pdf,.pdf" onChange={e => { setFile(e.target.files?.[0] || null); setError(''); }} /><span style={{ color: '#798597', fontSize: 12 }}>PDF seulement · 20 Mo maximum</span><button style={button} disabled={!file || busy}>{busy ? 'Analyse Cominty en cours…' : 'Lancer l’analyse'}</button></form></div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(210px,1fr))', gap: 12, marginBottom: 20 }}>{AGENT_LABELS.map((name, i) => <div key={name} style={{ ...card, padding: 16 }}><div style={{ color: '#6d7b8e', fontSize: 12 }}>AGENT {i + 1}</div><strong style={{ display: 'block', color: '#183654', margin: '6px 0' }}>{name}</strong><span style={{ color: busy ? '#ad7419' : '#23815d', fontSize: 12 }}>{busy ? '● Workflow en cours' : '● Prêt'}</span></div>)}</div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(320px,1fr))', gap: 14, marginBottom: 16 }}>
      <div style={card}><h2 style={title}>Comparer deux versions</h2><form onSubmit={runCompare} style={{ display: 'grid', gap: 10 }}><label>Version A <input type="file" accept="application/pdf,.pdf" onChange={e => setCompareA(e.target.files?.[0] || null)} /></label><label>Version B <input type="file" accept="application/pdf,.pdf" onChange={e => setCompareB(e.target.files?.[0] || null)} /></label><button style={button} disabled={!compareA || !compareB || !!actionBusy}>{actionBusy === 'compare' ? 'Comparaison en cours…' : 'Comparer les versions'}</button></form>
        {comparison && <div style={{ marginTop: 14 }}><b>{comparison.summary}</b>{(comparison.changes || []).map((change, i) => <div key={i} style={{ background: '#f5f7fa', padding: 10, marginTop: 8, borderRadius: 8 }}><strong>{change.clause} · {change.change}</strong><p>Avant : {change.before || '—'}</p><p>Après : {change.after || '—'}</p><small>{change.impact}</small></div>)}</div>}
      </div>
      <div style={card}><h2 style={title}>Priorité du portefeuille</h2><p style={{ color: '#718095', fontSize: 13, marginBottom: 12 }}>Demande à l’agent Cominty de classer les analyses enregistrées selon l’urgence de revue.</p><button style={button} disabled={!analyses.length || !!actionBusy} onClick={runPriority}>{actionBusy === 'priority' ? 'Classement en cours…' : 'Classer mes contrats'}</button>
        {priorityList && (priorityList.rankings || []).map((entry, i) => <div key={entry.id || i} style={{ padding: 10, borderBottom: '1px solid #edf0f4' }}><strong>{entry.position || i + 1}. {analyses.find(a => a.id === entry.id)?.filename || entry.id}</strong><span style={{ float: 'right' }}>{entry.priority} · {entry.score}/100</span><p>{entry.rationale}</p><small>Prochaine action : {entry.next_action}</small></div>)}
      </div>
    </div>
    {current && <div style={{ ...card, marginBottom: 16 }}><h2 style={title}>Outils pour {current.filename}</h2>
      <form onSubmit={e => { e.preventDefault(); runAction('ask', 'ask', { question }); }} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}><input aria-label="Question sur le contrat" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ex. Quelle est la franchise ?" style={{ flex: '1 1 280px', padding: 11, border: '1px solid #dce3eb', borderRadius: 8 }} /><button style={button} disabled={!question.trim() || !!actionBusy}>{actionBusy === 'ask' ? 'Recherche…' : 'Poser la question'}</button></form>
      {answer && <div role="status" style={{ background: '#f4f8fc', padding: 12, borderRadius: 8, marginBottom: 12 }}><b>Réponse : </b>{answer.answer}<p><small>Preuve : {answer.evidence || 'Aucune citation précise'} · Confiance : {answer.confidence || '—'}</small></p></div>}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}><button style={button} disabled={!!actionBusy} onClick={() => runAction('clarification', 'clarification')}>{actionBusy === 'clarification' ? 'Rédaction…' : 'Préparer une demande de clarification'}</button><button style={{ ...button, background: '#496782' }} disabled={!!actionBusy} onClick={() => runAction('compliance', 'compliance')}>{actionBusy === 'compliance' ? 'Préparation…' : 'Générer la checklist conformité'}</button></div>
      {clarification && <div style={{ marginTop: 14, padding: 14, background: '#f5f7fa', borderRadius: 8 }}><h3 style={title}>Brouillon à relire — non envoyé</h3><b>{clarification.subject}</b><pre style={{ whiteSpace: 'pre-wrap', font: 'inherit', lineHeight: 1.6, marginTop: 8 }}>{clarification.body}</pre>{(clarification.questions || []).map((q, i) => <p key={i}>• {q}</p>)}</div>}
      {checklist && <div style={{ marginTop: 14 }}><h3 style={title}>Checklist de conformité · {checklist.contract_type || 'contrat'}</h3><p>Juridiction détectée : {checklist.jurisdiction_detected || 'non établie'} · {checklist.jurisdiction_basis || ''}</p>{(checklist.checklist || []).map((item, i) => <div key={i} style={{ padding: 10, marginTop: 6, background: '#f5f7fa', borderRadius: 8 }}><b>{item.item}</b> · {item.status}<p>{item.evidence}</p><small>Action : {item.action}</small></div>)}<p style={{ color: '#8a5a12', marginTop: 10 }}>À faire valider par une personne compétente. {checklist.limitations}</p></div>}
    </div>}
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(230px, .75fr) minmax(300px, 2fr)', gap: 16, alignItems: 'start' }}>
      <div style={card}><h2 style={title}>Rapports récents</h2>{analyses.length ? analyses.map(item => <button key={item.id} onClick={() => setSelected(item)} style={{ width: '100%', textAlign: 'left', padding: '12px 4px', border: 0, borderBottom: '1px solid #edf0f4', background: 'transparent', cursor: 'pointer', color: '#193653' }}><strong style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.filename}</strong><small style={{ color: '#7a8797' }}>{new Date(item.created_at).toLocaleString()}</small></button>) : <p style={{ color: '#7a8797', fontSize: 13 }}>Les analyses terminées apparaîtront ici.</p>}</div>
      <div style={card}>{current ? <><div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}><div><h2 style={title}>{current.filename}</h2><span style={{ color: '#718095', fontSize: 12 }}>Rapport du {new Date(current.created_at).toLocaleString()}</span></div><button style={button} onClick={() => download(current)}>Télécharger le PDF</button></div><hr style={{ border: 0, borderTop: '1px solid #edf0f4', margin: '18px 0'}}/><h3 style={title}>Activité des agents</h3>{(current.activities || []).map((a, i) => <div key={i} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f0f2f5', padding: '9px 0', gap: 10 }}><span><b>{a.agent}</b><small style={{ display: 'block', color: '#718095' }}>{a.task}</small></span><span style={{ color: '#23815d', whiteSpace: 'nowrap' }}>✓ Terminé</span></div>)}<h3 style={{ ...title, marginTop: 20 }}>Synthèse</h3><p style={{ lineHeight: 1.7 }}>{current.report?.executive_summary || '—'}</p><h3 style={{ ...title, marginTop: 20 }}>Informations extraites</h3><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))', gap: 10 }}>{Object.entries(current.extraction || {}).filter(([,v]) => v && !Array.isArray(v)).map(([key, value]) => <div key={key} style={{ background: '#f5f7fa', borderRadius: 8, padding: 10 }}><small style={{ color: '#718095', textTransform: 'capitalize' }}>{key.replaceAll('_',' ')}</small><div>{String(value)}</div></div>)}</div><h3 style={{ ...title, marginTop: 20 }}>Anomalies</h3>{(current.anomalies?.anomalies || []).map((a,i) => <div key={i} style={{ padding: 12, marginBottom: 8, background: '#f7f8fa', borderRadius: 8 }}><b>{a.title}</b> · {severity(a.severity)}<p style={{ marginTop: 5, lineHeight: 1.5 }}>{a.description}</p></div>)}<h3 style={{ ...title, marginTop: 20 }}>Risques et recommandations</h3>{(current.risk?.risks || []).map((r,i) => <div key={i} style={{ padding: 12, marginBottom: 8, background: '#f7f8fa', borderRadius: 8 }}><b>{r.title}</b> · {severity(r.priority)}<p style={{ marginTop: 5 }}>{r.description}</p><small>Recommandation : {r.recommendation}</small></div>)}{(current.risk?.recommendations || []).map((r,i)=><p key={i} style={{ margin: '8px 0' }}>• {r}</p>)}</> : <div style={{ color: '#718095', padding: 25 }}>Choisissez un rapport ou téléversez un PDF pour commencer.</div>}</div>
    </div>
  </section>;
}
