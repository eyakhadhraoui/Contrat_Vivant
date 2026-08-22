import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { agencesAPI } from '../services/api';

export default function SignupPage({ onNavigateToLogin }) {
  const { signup } = useAuth();
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
          <div className="login-right-panel" style={{ padding: '40px 44px' }}>
            <div className="login-form-header" style={{ marginBottom: '20px' }}>
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
                <p>Renseignez vos informations pour accéder au portail</p>
              </div>
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
    </div>
  );
}
