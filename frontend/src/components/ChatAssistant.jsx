import React, { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../services/api';
import DocumentIngestionBar from './DocumentIngestionBar';

export default function ChatAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'docs'
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(false);
  const chatEndRef = useRef(null);

  const defaultWelcome = {
    sender: 'bot',
    text: "Bonjour 👋 ! Je suis l'Assistant IA Contrat Vivant. Tous vos documents PDF et vos conversations sont sauvegardés de manière permanente. Posez-moi vos questions !",
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    sources: [],
  };

  // Chargement automatique de l'historique persistant depuis la base de données
  const loadChatHistory = async () => {
    setInitialLoading(true);
    try {
      const history = await chatAPI.getHistory();
      if (history && history.length > 0) {
        setMessages(history);
      } else {
        setMessages([defaultWelcome]);
      }
    } catch (err) {
      console.warn("Historique chat inaccessible :", err);
      setMessages([defaultWelcome]);
    } finally {
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    loadChatHistory();
  }, []);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen && activeTab === 'chat') {
      scrollToBottom();
    }
  }, [messages, isOpen, activeTab]);

  const handleSend = async (e, customText = null) => {
    if (e) e.preventDefault();
    const userText = (customText || inputMsg).trim();
    if (!userText || loading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setMessages((prev) => [
      ...prev,
      { sender: 'user', text: userText, time: timeStr, sources: [] },
    ]);
    if (!customText) setInputMsg('');
    setLoading(true);

    try {
      const res = await chatAPI.sendMessage(userText);
      const botAnswer = res.reponse || res.answer || res.response || res.result || 'Je reste à votre disposition.';
      const botSources = res.sources || [];

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: typeof botAnswer === 'string' ? botAnswer : JSON.stringify(botAnswer),
          sources: botSources,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `⚠️ Erreur : ${err.message || 'Impossible de joindre le serveur backend. Vérifiez que FastAPI est démarré sur le port 8000.'}`,
          sources: [],
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm("Effacer tout l'historique de discussion ?")) return;
    try {
      await chatAPI.clearHistory();
      setMessages([defaultWelcome]);
    } catch (err) {
      alert("Erreur lors de l'effacement de l'historique");
    }
  };

  const handleSelectDocumentForQuestion = (filename) => {
    setActiveTab('chat');
    const promptText = `Quelles sont les clauses clés, garanties et exclusions du document "${filename}" ?`;
    setInputMsg(promptText);
  };

  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999 }}>
      {!isOpen ? (
        <button
          onClick={() => {
            setIsOpen(true);
            loadChatHistory();
          }}
          style={{
            width: '62px',
            height: '62px',
            borderRadius: '50%',
            backgroundColor: '#e54838',
            color: '#fff',
            border: 'none',
            boxShadow: '0 8px 24px rgba(229, 72, 56, 0.45)',
            cursor: 'pointer',
            fontSize: '26px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'transform 0.2s ease, box-shadow 0.2s',
          }}
          title="Assistant IA RAG & Base Documentaire"
        >
          💬
        </button>
      ) : (
        <div
          style={{
            width: '460px',
            height: '620px',
            backgroundColor: '#0d0e12',
            borderRadius: '20px',
            boxShadow: '0 25px 65px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.12)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            color: '#fff',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '14px 18px',
              backgroundColor: '#161820',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: '#10b981',
                  boxShadow: '0 0 8px #10b981',
                }}
              />
              <div>
                <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
                  Assistant IA & RAG Persistant
                </h4>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                  Base documentaire et historique synchronisés
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={handleClearHistory}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#64748b',
                  fontSize: '14px',
                  cursor: 'pointer',
                  padding: '4px',
                }}
                title="Effacer l'historique de conversation"
              >
                🧹
              </button>
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '18px',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div
            style={{
              display: 'flex',
              backgroundColor: '#12141a',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              padding: '4px 8px',
            }}
          >
            <button
              onClick={() => setActiveTab('chat')}
              style={{
                flex: 1,
                padding: '8px',
                background: activeTab === 'chat' ? '#1e212b' : 'transparent',
                color: activeTab === 'chat' ? '#f8fafc' : '#94a3b8',
                border: 'none',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <span>💬</span> Discussion IA
            </button>
            <button
              onClick={() => setActiveTab('docs')}
              style={{
                flex: 1,
                padding: '8px',
                background: activeTab === 'docs' ? '#1e212b' : 'transparent',
                color: activeTab === 'docs' ? '#f8fafc' : '#94a3b8',
                border: 'none',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
              }}
            >
              <span>📚</span> Documents RAG
            </button>
          </div>

          {/* Tab Content: Docs Manager */}
          {activeTab === 'docs' && (
            <div style={{ flex: 1, padding: '14px', overflowY: 'auto' }}>
              <DocumentIngestionBar
                onIngestSuccess={(res) => {
                  setMessages((prev) => [
                    ...prev,
                    {
                      sender: 'bot',
                      text: `📌 Document "${res.filename}" enregistré de façon permanente dans MySQL et indexé dans le RAG. Vous pouvez maintenant poser vos questions sur son contenu !`,
                      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                      sources: [res.filename],
                    },
                  ]);
                }}
                onSelectDocumentForQuestion={handleSelectDocumentForQuestion}
              />
            </div>
          )}

          {/* Tab Content: Chat */}
          {activeTab === 'chat' && (
            <div
              style={{
                flex: 1,
                padding: '14px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              {initialLoading ? (
                <div style={{ textAlign: 'center', color: '#64748b', fontSize: '12px', marginTop: '20px' }}>
                  Restauration de la conversation... ⏳
                </div>
              ) : (
                messages.map((m, idx) => (
                  <div
                    key={idx}
                    style={{
                      alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '88%',
                      backgroundColor: m.sender === 'user' ? '#e54838' : '#1e212b',
                      color: '#fff',
                      padding: '12px 16px',
                      borderRadius: m.sender === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                      fontSize: '13px',
                      lineHeight: '1.5',
                      whiteSpace: 'pre-wrap',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                    }}
                  >
                    <div>{m.text}</div>

                    {/* Citations de Sources RAG */}
                    {m.sources && m.sources.length > 0 && (
                      <div
                        style={{
                          marginTop: '8px',
                          paddingTop: '6px',
                          borderTop: '1px solid rgba(255,255,255,0.1)',
                          fontSize: '11px',
                          color: '#38bdf8',
                          display: 'flex',
                          flexWrap: 'wrap',
                          gap: '6px',
                          alignItems: 'center',
                        }}
                      >
                        <span style={{ color: '#94a3b8' }}>Sources RAG :</span>
                        {m.sources.map((src, sIdx) => (
                          <span
                            key={sIdx}
                            style={{
                              backgroundColor: 'rgba(56, 189, 248, 0.15)',
                              border: '1px solid rgba(56, 189, 248, 0.3)',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '10px',
                            }}
                          >
                            📄 {src}
                          </span>
                        ))}
                      </div>
                    )}

                    <div
                      style={{
                        fontSize: '10px',
                        color: 'rgba(255,255,255,0.45)',
                        marginTop: '6px',
                        textAlign: 'right',
                      }}
                    >
                      {m.time}
                    </div>
                  </div>
                ))
              )}

              {loading && (
                <div
                  style={{
                    alignSelf: 'flex-start',
                    backgroundColor: '#1e212b',
                    padding: '10px 16px',
                    borderRadius: '16px',
                    fontSize: '13px',
                    color: '#94a3b8',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <span style={{ animation: 'spin 1s linear infinite' }}>🤖</span>
                  <span>Analyse RAG & Génération de la réponse...</span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}

          {/* Form Input (visible in chat tab) */}
          {activeTab === 'chat' && (
            <form
              onSubmit={(e) => handleSend(e)}
              style={{
                padding: '12px 16px',
                borderTop: '1px solid rgba(255,255,255,0.08)',
                backgroundColor: '#161820',
                display: 'flex',
                gap: '8px',
              }}
            >
              <input
                type="text"
                placeholder="Posez une question sur vos contrats ou PDFs..."
                value={inputMsg}
                onChange={(e) => setInputMsg(e.target.value)}
                style={{
                  flex: 1,
                  backgroundColor: '#0d0e12',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  color: '#fff',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
              <button
                type="submit"
                disabled={loading || !inputMsg.trim()}
                style={{
                  backgroundColor: inputMsg.trim() ? '#e54838' : '#334155',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '10px 16px',
                  cursor: inputMsg.trim() ? 'pointer' : 'not-allowed',
                  fontWeight: 600,
                  fontSize: '13px',
                  transition: 'background 0.2s',
                }}
              >
                Envoyer
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
