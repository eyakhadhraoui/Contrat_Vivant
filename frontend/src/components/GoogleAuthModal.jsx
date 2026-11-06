import React, { useState } from 'react';

export default function GoogleAuthModal({ isOpen, onClose, onSelectAccount, loading, error }) {
  const [customMode, setCustomMode] = useState(false);
  const [customData, setCustomData] = useState({
    prenom: '',
    nom: '',
    email: '',
  });
  const [customError, setCustomError] = useState('');

  if (!isOpen) return null;

  const defaultAccounts = [
    {
      prenom: 'Eya',
      nom: 'Khadhraoui',
      email: 'eyakhadhraoui249@gmail.com',
      picture: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
      google_id: 'google_1092837465928174',
      badge: 'Gestionnaire Sinistres'
    },
    {
      prenom: 'Sarra',
      nom: 'Khelifi',
      email: 'sarra.khelifi@gmail.com',
      picture: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100&auto=format&fit=crop&q=80',
      google_id: 'google_2091827364519283',
      badge: 'Gestionnaire Assurances'
    },
    {
      prenom: 'Souheil',
      nom: 'Khadhraoui',
      email: 'souheil.khadhraoui@gmail.com',
      picture: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
      google_id: 'google_3091827364519284',
      badge: 'Nouveau Gestionnaire'
    }
  ];

  const handleSelect = (account) => {
    onSelectAccount({
      email: account.email,
      nom: account.nom,
      prenom: account.prenom,
      google_id: account.google_id || `google_${Date.now()}`,
      picture: account.picture || null,
    });
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (!customData.email || !customData.email.includes('@')) {
      setCustomError('Veuillez renseigner une adresse Gmail valide.');
      return;
    }
    setCustomError('');
    onSelectAccount({
      email: customData.email.trim(),
      nom: customData.nom.trim() || 'Utilisateur',
      prenom: customData.prenom.trim() || 'Google',
      google_id: `google_${Date.now()}`,
      picture: null,
    });
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 99999,
      padding: '20px',
      animation: 'fadeIn 0.2s ease-out'
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: '20px',
        width: '100%',
        maxWidth: '440px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        overflow: 'hidden',
        border: '1px solid #e2e8f0',
        color: '#1e293b',
        fontFamily: "'Inter', sans-serif"
      }}>
        {/* Header Google */}
        <div style={{ padding: '24px 28px 16px 28px', borderBottom: '1px solid #f1f5f9' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <svg width="24" height="24" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
              </svg>
              <span style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>Google OAuth 2.0</span>
            </div>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '20px',
                color: '#94a3b8',
                padding: '4px',
                borderRadius: '8px'
              }}
            >
              ✕
            </button>
          </div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#0f172a' }}>
            Choisir un compte
          </h3>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
            pour poursuivre vers <strong style={{ color: '#0f172a' }}>Contrat Vivant — Vermeg</strong>
          </p>
        </div>

        {/* Message d'erreur s'il y a lieu */}
        {(error || customError) && (
          <div style={{
            margin: '12px 28px 0 28px',
            padding: '10px 14px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fee2e2',
            borderRadius: '10px',
            color: '#dc2626',
            fontSize: '13px'
          }}>
            ⚠️ {error || customError}
          </div>
        )}

        {/* Contenu principal */}
        <div style={{ padding: '20px 28px 24px 28px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '30px 0' }}>
              <div style={{
                width: '40px',
                height: '40px',
                border: '3px solid #e2e8f0',
                borderTopColor: '#4285F4',
                borderRadius: '50%',
                margin: '0 auto 16px auto',
                animation: 'spin 0.8s linear infinite'
              }}></div>
              <p style={{ margin: 0, fontWeight: 600, color: '#1e293b', fontSize: '14px' }}>
                Vérification et connexion en cours...
              </p>
              <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '12px' }}>
                Création/récupération automatique de votre session
              </p>
            </div>
          ) : !customMode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {defaultAccounts.map((acc, idx) => (
                <div
                  key={idx}
                  onClick={() => handleSelect(acc)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    padding: '12px 14px',
                    borderRadius: '12px',
                    border: '1px solid #f1f5f9',
                    backgroundColor: '#ffffff',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f8fafc';
                    e.currentTarget.style.borderColor = '#cbd5e1';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#ffffff';
                    e.currentTarget.style.borderColor = '#f1f5f9';
                  }}
                >
                  <img
                    src={acc.picture}
                    alt={acc.prenom}
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '2px solid #e2e8f0'
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, fontSize: '14px', color: '#0f172a' }}>
                        {acc.prenom} {acc.nom}
                      </span>
                      {acc.badge && (
                        <span style={{
                          fontSize: '10.5px',
                          fontWeight: 600,
                          padding: '2px 6px',
                          borderRadius: '6px',
                          backgroundColor: '#e0f2fe',
                          color: '#0369a1'
                        }}>
                          {acc.badge}
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '12px', color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {acc.email}
                    </div>
                  </div>
                  <span style={{ color: '#94a3b8', fontSize: '18px' }}>›</span>
                </div>
              ))}

              {/* Option Saisir un autre compte Google */}
              <div
                onClick={() => setCustomMode(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '12px 14px',
                  borderRadius: '12px',
                  border: '1px dashed #cbd5e1',
                  backgroundColor: '#fafafa',
                  cursor: 'pointer',
                  marginTop: '4px',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f1f5f9';
                  e.currentTarget.style.borderColor = '#94a3b8';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#fafafa';
                  e.currentTarget.style.borderColor = '#cbd5e1';
                }}
              >
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  backgroundColor: '#f1f5f9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#64748b',
                  fontSize: '20px'
                }}>
                  👤
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: '13.5px', color: '#1e293b' }}>
                    Utiliser un autre compte Google
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#64748b' }}>
                    Saisir votre adresse Gmail personnelle ou pro
                  </div>
                </div>
                <span style={{ color: '#94a3b8', fontSize: '18px' }}>+</span>
              </div>
            </div>
          ) : (
            <form onSubmit={handleCustomSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                    Prénom
                  </label>
                  <input
                    type="text"
                    placeholder="Eya"
                    value={customData.prenom}
                    onChange={(e) => setCustomData({ ...customData, prenom: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '13px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                    Nom
                  </label>
                  <input
                    type="text"
                    placeholder="Khadhraoui"
                    value={customData.nom}
                    onChange={(e) => setCustomData({ ...customData, nom: e.target.value })}
                    required
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '13px',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>
                  Adresse Google / Gmail
                </label>
                <input
                  type="email"
                  placeholder="nom.prenom@gmail.com"
                  value={customData.email}
                  onChange={(e) => setCustomData({ ...customData, email: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '13px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setCustomMode(false)}
                  style={{
                    flex: 1,
                    padding: '9px',
                    backgroundColor: '#f1f5f9',
                    border: 'none',
                    borderRadius: '10px',
                    fontWeight: 600,
                    fontSize: '13px',
                    color: '#475569',
                    cursor: 'pointer'
                  }}
                >
                  Retour
                </button>
                <button
                  type="submit"
                  style={{
                    flex: 2,
                    padding: '9px',
                    backgroundColor: '#4285F4',
                    border: 'none',
                    borderRadius: '10px',
                    fontWeight: 600,
                    fontSize: '13px',
                    color: '#ffffff',
                    cursor: 'pointer',
                    boxShadow: '0 2px 6px rgba(66, 133, 244, 0.3)'
                  }}
                >
                  Continuer avec ce compte
                </button>
              </div>
            </form>
          )}

          {/* Footer légal Google */}
          <div style={{ marginTop: '20px', paddingTop: '14px', borderTop: '1px solid #f1f5f9', fontSize: '11px', color: '#94a3b8', textAlign: 'center', lineHeight: '1.4' }}>
            Pour continuer, Google partagera votre nom, adresse e-mail et photo de profil avec l'application <strong>Contrat Vivant</strong> conformément aux règles de confidentialité.
          </div>
        </div>
      </div>
    </div>
  );
}
