import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { agencesAPI } from '../services/api';
import GoogleAuthModal from '../components/GoogleAuthModal';

export default function SignupPage({ onNavigateToLogin }) {
  const { signup, loginWithGoogle } = useAuth();
  const [agences, setAgences] = useState([]);
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    username: '',
    email: '',
    role: 'assurances',
    agence_id: 'AG01',
    password: '',
    passwordConfirm: '',
  });

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Google OAuth state
  const [isGoogleModalOpen, setIsGoogleModalOpen] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleError, setGoogleError] = useState('');

  useEffect(() => {
    async function loadAgences() {
      try {
        const list = await agencesAPI.getAgences();
        if (list && list.length > 0) {
          setAgences(list);
          setFormData((prev) => ({ ...prev, agence_id: list[0].id }));
        }
      } catch (e) {
        console.warn('Fallback agences par défaut');
      }
    }
    loadAgences();
  }, []);

  const handleChange = (e) => {
    const { id, value } = e.target;
    const fieldName = id.replace('signup-', '');
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (formData.password !== formData.passwordConfirm) {
      setErrorMsg('Les mots de passe ne correspondent pas.');
      return;
    }

    if (formData.password.length < 4) {
      setErrorMsg('Le mot de passe doit contenir au moins 4 caractères.');
      return;
    }

    try {
      setLoading(true);
      const res = await signup({
        nom: formData.nom,
        prenom: formData.prenom,
        username: formData.username,
        email: formData.email,
        role: formData.role,
        agence_id: formData.agence_id,
        password: formData.password,
      });

      setSuccessMsg('Compte créé avec succès ! Connexion en cours...');
    } catch (err) {
      setErrorMsg(err.message || 'Échec de l\'inscription.');
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
                Rejoignez la gestion <span className="accent-italic">intelligente</span><br />des contrats.
              </h1>
              <p className="hero-quote">
                Accédez à la plateforme autonome de gestion d'assurance, d'analyse du risque et d'orchestration multi-agents.
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
          <div className="login-right-panel" style={{ padding: '34px 44px' }}>
            <div className="login-form-header" style={{ marginBottom: '14px' }}>
              <div className="icon-badge">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="8.5" cy="7" r="4"></circle>
                  <line x1="20" y1="8" x2="20" y2="14"></line>
                  <line x1="17" y1="11" x2="23" y2="11"></line>
                </svg>
              </div>
              <div className="header-text">
                <h2>Créer un compte gestionnaire</h2>
                <p>Inscription rapide ou via compte Google</p>
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
                marginBottom: '12px',
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '8px 0 14px 0' }}>
              <span style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }}></span>
              <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700, letterSpacing: '0.8px' }}>OU FORMULAIRE CLASSIQUE</span>
              <span style={{ flex: 1, height: '1px', backgroundColor: '#e2e8f0' }}></span>
            </div>

            <form onSubmit={handleSubmit} className="auth-form" style={{ gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-field">
                  <label htmlFor="signup-nom">Nom</label>
                  <input
                    id="signup-nom"
                    className="custom-input"
                    type="text"
                    placeholder="Ex: Trabelsi"
                    value={formData.nom}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="signup-prenom">Prénom</label>
                  <input
                    id="signup-prenom"
                    className="custom-input"
                    type="text"
                    placeholder="Ex: Ahmed"
                    value={formData.prenom}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <div className="form-field">
                <label htmlFor="signup-username">Nom d'utilisateur (Identifiant)</label>
                <input
                  id="signup-username"
                  className="custom-input"
                  type="text"
                  placeholder="Ex: ahmed.trabelsi"
                  value={formData.username}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="signup-email">Adresse Email</label>
                <input
                  id="signup-email"
                  className="custom-input"
                  type="email"
                  placeholder="Ex: ahmed@assurance.tn"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-field">
                  <label htmlFor="signup-role">Rôle / Spécialité</label>
                  <select
                    id="signup-role"
                    className="custom-input"
                    value={formData.role}
                    onChange={handleChange}
                    required
                  >
                    <option value="assurances">Gestionnaire Assurances</option>
                    <option value="sinistres">Gestionnaire Sinistres</option>
                  </select>
                </div>
                <div className="form-field">
                  <label htmlFor="signup-agence_id">Agence</label>
                  <select
                    id="signup-agence_id"
                    className="custom-input"
                    value={formData.agence_id}
                    onChange={handleChange}
                    required
                  >
                    {agences.length > 0 ? (
                      agences.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.id} - {a.nom} ({a.ville || ''})
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="AG01">AG01 - Agence Tunis Centre</option>
                        <option value="AG02">AG02 - Agence Sfax</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div className="form-field">
                  <label htmlFor="signup-password">Mot de passe</label>
                  <input
                    id="signup-password"
                    className="custom-input"
                    type="password"
                    placeholder="••••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="signup-passwordConfirm">Confirmation</label>
                  <input
                    id="signup-passwordConfirm"
                    className="custom-input"
                    type="password"
                    placeholder="••••••••••"
                    value={formData.passwordConfirm}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>

              <button type="submit" className="submit-btn" style={{ marginTop: '4px' }} disabled={loading}>
                {loading ? 'Inscription...' : 'S\'inscrire et se connecter'}
              </button>

              {errorMsg && <p className="form-error-msg">{errorMsg}</p>}
              {successMsg && <p className="form-error-msg" style={{ color: '#059669' }}>{successMsg}</p>}

              <div className="security-footer" style={{ marginTop: '8px' }}>
                <span>
                  Déjà un compte ?{' '}
                  <button
                    type="button"
                    onClick={onNavigateToLogin}
                    className="forgot-password"
                    style={{ textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                  >
                    Se connecter
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
