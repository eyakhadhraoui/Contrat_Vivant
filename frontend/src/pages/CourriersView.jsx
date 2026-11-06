import React, { useEffect, useMemo, useState } from 'react';
import { courrierAPI } from '../services/api';

const types = [
  { value: 'demande_pieces', label: 'Demande de pièces' },
  { value: 'accuse_reception', label: 'Accusé de réception' },
  { value: 'reponse_client', label: 'Réponse au client' },
];
const field = { display: 'block', width: '100%', boxSizing: 'border-box', marginTop: 6, padding: '9px 12px', border: '1px solid #d8deeb', borderRadius: 8, background: '#fff', color: '#171b35', font: 'inherit', fontSize: 12 };
const action = { border: 0, borderRadius: 8, padding: '10px 18px', background: '#ed3f2d', color: '#fff', fontSize: 12, fontWeight: 700, cursor: 'pointer' };
const card = { background: '#fff', border: '1px solid #e8eaf1', borderRadius: 13, padding: 22, boxShadow: '0 2px 5px rgba(18,23,56,.035)' };

export default function CourriersView({ contrats = [], sinistres = [] }) {
  const records = useMemo(() => [
    ...contrats.map((item) => ({ ...item, ref: item.id || item.contrat_id, kind: 'Contrat' })),
    ...sinistres.map((item) => ({ ...item, ref: item.id || item.sinistre_id, kind: 'Sinistre' })),
  ].filter((item) => item.ref), [contrats, sinistres]);
  const [recordId, setRecordId] = useState('');
  const [type, setType] = useState('accuse_reception');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [reference, setReference] = useState('');
  const [context, setContext] = useState('');
  const [draft, setDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState(false);

  const chooseRecord = (value) => {
    setRecordId(value);
    const record = records.find((item) => String(item.ref) === value);
    if (!record) return;
    setReference(String(record.ref));
    setName(record.client || record.client_nom || record.nom_client || '');
    setEmail(record.client_email || record.email || '');
  };
  useEffect(() => {
    if (recordId || !records.length) return;
    const record = records[0];
    setRecordId(String(record.ref));
    setReference(String(record.ref));
    setName(record.client || record.client_nom || record.nom_client || '');
    setEmail(record.client_email || record.email || '');
  }, [records, recordId]);
  const generate = async (event) => {
    event.preventDefault(); setLoading(true); setMessage(''); setError(false);
    try {
      const result = await courrierAPI.generate({ type_courrier: type, client_nom: name || 'Madame, Monsieur', client_email: email || null, reference, contexte: context, ton: 'professionnel et cordial' });
      setDraft(result.courrier || ''); setMessage('Brouillon généré. Relisez-le et complétez les champs si nécessaire.');
    } catch (err) { setError(true); setMessage(`Génération impossible. Le service n’a pas répondu (${err.message || 'erreur inconnue'}). Réessayez dans un instant.`); }
    finally { setLoading(false); }
  };
  const copyDraft = async () => { try { await navigator.clipboard.writeText(draft); setMessage('Courrier copié dans le presse-papiers.'); setError(false); } catch { setMessage('Copie indisponible dans ce navigateur.'); setError(true); } };
  const downloadDraft = () => {
    const url = URL.createObjectURL(new Blob([draft], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = `courrier-${reference || 'client'}.txt`; link.click(); URL.revokeObjectURL(url);
  };
  const placeholder = type === 'demande_pieces' ? 'Indiquez les pièces demandées et les faits à communiquer.' : 'Indiquez les faits et la r\u00e9ponse à communiquer au client.';

  return <section className="courriers-page">
    <header className="courriers-heading"><h1>Courriers IA</h1><p>Préparez un brouillon à relire avant de l’envoyer au client.</p></header>
    <div className="courriers-layout">
      <form onSubmit={generate} className="courriers-form" style={card}>
        <div className="courriers-fields-two">
          <label>Type de courrier<select value={type} onChange={(e) => setType(e.target.value)} style={field}>{types.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          <label>Dossier existant <span className="courriers-muted">(facultatif)</span><select value={recordId} onChange={(e) => chooseRecord(e.target.value)} style={field}><option value="">Sélectionner un dossier</option>{records.map((item) => <option key={`${item.kind}-${item.ref}`} value={item.ref}>{item.kind} {item.ref} - {item.client || item.client_nom || 'Client'}</option>)}</select></label>
        </div>
        <div className="courriers-fields-two">
          <label>Nom du client<input value={name} onChange={(e) => setName(e.target.value)} placeholder="Madame, Monsieur" style={field} /></label>
          <label>Email du client<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="client@exemple.tn" style={field} /></label>
        </div>
        <label>Référence du dossier<input value={reference} onChange={(e) => setReference(e.target.value)} style={field} /></label>
        <label>Contexte et informations à inclure<textarea value={context} onChange={(e) => setContext(e.target.value)} rows={5} placeholder={placeholder} style={{ ...field, resize: 'vertical', minHeight: 100 }} /></label>
        <button type="submit" disabled={loading} style={{ ...action, opacity: loading ? .7 : 1 }}>{loading ? 'Génération en cours...' : 'G\u00e9n\u00e9rer le brouillon'}</button>
      </form>
      <aside className="courriers-preview" style={card}>
        <h2>Aperçu du brouillon</h2>
        {message && <div role="status" className={`courriers-status ${error ? 'is-error' : 'is-success'}`}>{message}</div>}
        {draft ? <textarea aria-label="Brouillon modifiable" value={draft} onChange={(e) => setDraft(e.target.value)} className="courriers-draft" /> : <div className="courriers-empty">Le courrier généré s’affichera ici, pr&ecirc;t à être relu et modifié.</div>}
        {draft && <div className="courriers-actions"><button type="button" onClick={copyDraft} style={action}>Copier</button><button type="button" onClick={downloadDraft} className="courriers-download">Télécharger .txt</button></div>}
      </aside>
    </div>
  </section>;
}
