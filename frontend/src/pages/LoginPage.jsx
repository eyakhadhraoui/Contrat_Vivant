import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage({ onNavigateToSignup }) {
  const { login } = useAuth();
  const [username, setUsername] = useState('sarra.khelifi');
  const [password, setPassword] = useState('password123');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="login-body" style={{ minHeight: '100vh', width: '100vw' }}>
      <div className="login-wrapper">
        <div className="login-card-container">
          
          {/* Panneau Gauche */}
          <div className="login-left-panel">
            <div className="left-header">
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
                <p>Accès réservé aux comptes autorisés</p>
              </div>
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
    </div>
  );
}
