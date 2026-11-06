import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import GoogleAuthModal from '../components/GoogleAuthModal';

export default function LoginPage({ onNavigateToSignup }) {
  const { login, loginWithGoogle } = useAuth();
  const [username, setUsername] = useState('sarra.khelifi');
  const [password, setPassword] = useState('password123');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Google OAuth state
  const [isGoogleModalOpen, setIsGoogleModalOpen] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleError, setGoogleError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!username.trim() || !password.trim()) {
      setErrorMsg('Veuillez renseigner votre identifiant et mot de passe.');
      return;
    }

    try {
      setLoading(true);
      await login(username.trim(), password.trim());
    } catch (err) {
      setErrorMsg(err.message || 'Impossible de contacter le serveur.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAccountSelected = async (accountData) => {
    setGoogleError('');
    setGoogleLoading(true);
    try {
      await loginWithGoogle(accountData);
      setIsGoogleModalOpen(false);
    } catch (err) {
      setGoogleError(err.message || 'Échec de l\'authentification avec Google.');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="login-body" style={{ minHeight: '100vh', width: '100vw' }}>
      <div className="login-wrapper">
        <div className="login-card-container">
          
          {/* Panneau Gauche */}
          <div className="login-left-panel">
            <div className="left-header">
              {/* Logo Vermeg Officiel */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '2px', marginBottom: '8px' }}>
                <span style={{ color: '#e54838', fontWeight: 900, fontSize: '32px', lineHeight: '1', display: 'inline-block', transform: 'skewX(-10deg)', textShadow: '0 0 14px rgba(229, 72, 56, 0.6)' }}>/</span>
                <span style={{ color: '#ffffff', fontWeight: 800, fontSize: '26px', letterSpacing: '-0.5px', fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>vermeg</span>
              </div>
              <div className="brand-title">
                <span className="brand-contrat">Contrat</span>
                <span className="brand-vivant">Vivant</span>
              </div>
              <p className="brand-subtitle">PLATEFORME DE GESTION CONTRACTUELLE</p>
            </div>

            <div className="left-hero">
              <h1 className="hero-headline">
                Un contrat qui <span className="accent-italic">évolue</span><br />avec chaque décision.
              </h1>
              <p className="hero-quote">
                « Contrat vivant » relie vos équipes, vos clauses et vos clients dans un seul flux, mis à jour en continu.
              </p>
            </div>

            <div className="left-graphic-section">
              <div className="ecg-graphic-row">
                <svg className="ecg-svg" viewBox="0 0 160 50" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M0 25 L40 25 L48 10 L56 40 L64 5 L72 35 L80 25 L160 25" stroke="#e54838" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <div className="ecg-bars">
                  <span className="bar"></span>
                  <span className="bar"></span>
                  <span className="bar"></span>
                </div>
              </div>
              <p className="graphic-caption">CHAQUE SIGNAL DEVIENT UNE CLAUSE À JOUR — EN TEMPS RÉEL</p>
            </div>

            <div className="left-stats-footer">
              <div className="stat-item">
                <span className="stat-value">2 400+</span>
                <span className="stat-label">CONTRATS SUIVIS</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">98,2%</span>
                <span className="stat-label">ALERTES TRAITÉES &lt;24H</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">12</span>
                <span className="stat-label">AGENCES CONNECTÉES</span>
              </div>
            </div>
          </div>

          {/* Panneau Droit */}
          <div className="login-right-panel">
            <div className="login-form-header">
              <div className="icon-badge">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div className="header-text">
                <h2>Connexion gestionnaire</h2>
                <p>Accès sécurisé à la plateforme Contrat Vivant</p>
              </div>
            </div>

            {/* Bouton d'authentification Google */}
            <button
              type="button"
              className="google-signin-btn"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                padding: '11px 16px',
                backgroundColor: '#ffffff',
                color: '#1e293b',
                border: '1.5px solid #e2e8f0',
                borderRadius: '12px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.04)',
                transition: 'all 0.2s ease',
                marginTop: '10px',
                marginBottom: '14px',
              }}
              onClick={() => {
                setGoogleError('');
                setIsGoogleModalOpen(true);
              }}
              disabled={loading || googleLoading}
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
              </svg>
              <span>Continuer avec Google</span>
            </button>

            {/* Séparateur élégant */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '10px 0 16px 0' }}>
              <span style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }}></span>
              <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, letterSpacing: '0.8px' }}>OU IDENTIFIANTS</span>
              <span style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }}></span>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-field">
                <label htmlFor="login-username">Nom d'utilisateur</label>
                <input
                  id="login-username"
                  className="custom-input"
                  type="text"
                  placeholder="sarra.khelifi"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="login-password">Mot de passe</label>
                <input
                  id="login-password"
                  className="custom-input"
                  type="password"
                  placeholder="••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <div className="form-options">
                <label className="remember-me">
                  <input type="checkbox" defaultChecked />
                  <span>Se souvenir de moi</span>
                </label>
                <a href="#" onClick={(e) => e.preventDefault()} className="forgot-password">
                  Mot de passe oublié ?
                </a>
              </div>

              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Connexion...' : 'Se connecter'}
              </button>

              {errorMsg && <p className="form-error-msg">{errorMsg}</p>}

              <div className="security-footer">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
                <span>Connexion chiffrée — conforme aux normes de sécurité</span>
              </div>

              <div className="security-footer" style={{ marginTop: '8px' }}>
                <span>
                  Pas encore de compte ?{' '}
                  <button
                    type="button"
                    onClick={onNavigateToSignup}
                    className="forgot-password"
                    style={{ textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                  >
                    S'inscrire
                  </button>
                </span>
              </div>
            </form>
          </div>

        </div>
      </div>

      {/* Modal SSO Google */}
      <GoogleAuthModal
        isOpen={isGoogleModalOpen}
        onClose={() => setIsGoogleModalOpen(false)}
        onSelectAccount={handleGoogleAccountSelected}
        loading={googleLoading}
        error={googleError}
      />
    </div>
  );
}

