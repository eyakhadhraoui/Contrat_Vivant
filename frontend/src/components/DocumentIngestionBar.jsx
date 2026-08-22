import React, { useState, useEffect } from 'react';
import { ragAPI } from '../services/api';

export default function DocumentIngestionBar({ onIngestSuccess, onSelectDocumentForQuestion }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const docs = await ragAPI.getDocuments();
      setDocuments(docs || []);
    } catch (err) {
      console.error('Erreur chargement documents RAG:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatusMsg('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setStatusMsg('');

    try {
      const res = await ragAPI.ingestDocument(file);
      setStatusMsg(`✅ "${res.filename}" enregistré et indexé avec succès ! (${res.chunks_added} sections prêtes)`);
      setFile(null);
      await fetchDocuments();
      if (onIngestSuccess) onIngestSuccess(res);
    } catch (err) {
      setStatusMsg(`❌ Erreur : ${err.message || 'Échec de l\'ingestion'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Supprimer définitivement "${filename}" de la base RAG ?`)) return;
    try {
      await ragAPI.deleteDocument(docId || filename);
      setStatusMsg(`🗑️ Document "${filename}" supprimé.`);
      await fetchDocuments();
    } catch (err) {
      setStatusMsg(`❌ Erreur suppression : ${err.message}`);
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#161820',
        borderRadius: '12px',
        padding: '14px',
        border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      {/* Upload Zone */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#e54838', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span>📄</span>
            <span>Ajouter un Contrat ou Document (PDF / Texte)</span>
          </div>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>
            {documents.length} document{documents.length > 1 ? 's' : ''} persistant{documents.length > 1 ? 's' : ''}
          </span>
        </div>

        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="file"
            accept=".pdf,.txt,.json,.docx,.md"
            onChange={handleFileChange}
            style={{
              fontSize: '12px',
              color: '#cbd5e1',
              backgroundColor: '#0d0e12',
              padding: '6px 10px',
              borderRadius: '6px',
              border: '1px solid rgba(255,255,255,0.12)',
              flex: 1,
              cursor: 'pointer',
            }}
          />
          <button
            type="submit"
            disabled={!file || loading}
            style={{
              backgroundColor: file ? '#e54838' : '#334155',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '7px 14px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: file ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'background 0.2s',
            }}
          >
            {loading ? '⏳ Indexation...' : '📥 Enregistrer & Indexer'}
          </button>
        </form>

        {statusMsg && (
          <div
            style={{
              fontSize: '11px',
              marginTop: '8px',
              padding: '6px 10px',
              borderRadius: '6px',
              backgroundColor: statusMsg.startsWith('✅') ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              color: statusMsg.startsWith('✅') ? '#34d399' : '#f87171',
              border: statusMsg.startsWith('✅') ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
            }}
          >
            {statusMsg}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '6px' }}>
          📚 Base Documentaire RAG Enregistrée :
        </div>

        {loadingDocs ? (
          <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic' }}>Chargement des documents...</div>
        ) : documents.length === 0 ? (
          <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic' }}>
            Aucun document externe enregistré. Uploadez un PDF pour commencer à l'interroger !
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
            {documents.map((doc) => (
              <div
                key={doc.id || doc.filename}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  backgroundColor: '#0d0e12',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  border: '1px solid rgba(255,255,255,0.06)',
                  fontSize: '12px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                  <span style={{ fontSize: '14px' }}>
                    {doc.filename?.toLowerCase().endsWith('.pdf') ? '📕' : '📄'}
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 500, color: '#f1f5f9', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden', maxWidth: '200px' }}>
                      {doc.filename}
                    </span>
                    <span style={{ fontSize: '10px', color: '#64748b' }}>
                      {doc.chunks_count} section{doc.chunks_count > 1 ? 's' : ''} • {doc.uploaded_at || 'Enregistré'}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  {onSelectDocumentForQuestion && (
                    <button
                      onClick={() => onSelectDocumentForQuestion(doc.filename)}
                      style={{
                        background: 'rgba(229, 72, 56, 0.15)',
                        border: '1px solid rgba(229, 72, 56, 0.3)',
                        color: '#f87171',
                        borderRadius: '4px',
                        padding: '3px 8px',
                        fontSize: '11px',
                        cursor: 'pointer',
                      }}
                      title="Poser une question sur ce document"
                    >
                      Questionner 💬
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748b',
                      cursor: 'pointer',
                      fontSize: '12px',
                      padding: '2px 4px',
                    }}
                    title="Supprimer ce document"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
