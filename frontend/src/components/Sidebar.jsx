import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout, isAssurances, isSinistres } = useAuth();

  const getAvatarInitials = (name) => {
    if (!name) return 'AT';
    const parts = name.split(/[\s._-]+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const roleText = isAssurances && isSinistres
    ? 'Gestionnaire Global'
    : isAssurances
    ? 'Gestionnaire Assurances'
    : 'Gestionnaire Sinistres';

  const menuItems = [
    { id: 'cominty', label: 'Analyse de contrats IA', icon: 'AI' },
    { id: 'risque', label: 'Prévision du risque', icon: 'R' },
    { id: 'analyse', label: 'Analyse de dossier', icon: '🔍' },
    { id: 'map', label: 'Carte des risques', icon: '🗺️' },
    { id: 'sinistres', label: 'Mes sinistres', icon: '📋' },
    { id: 'contrats', label: 'Mes contrats', icon: '📄' },
    { id: 'clients', label: 'Mes clients', icon: '👥' },
    { id: 'historique', label: 'Historique d\u0027activit\u00e9', icon: 'H' },
    { id: 'courriers', label: 'Courriers IA', icon: 'C' },
  ];

  return (
    <aside className="sidebar">
      {/* Logo Vermeg en haut (Ultra Net & Contrasté) */}
      <div className="sidebar-logo" style={{ padding: '8px 6px 14px 6px', display: 'flex', flexDirection: 'column', gap: '4px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
          <span style={{ color: '#e54838', fontWeight: 900, fontSize: '30px', lineHeight: '1', display: 'inline-block', transform: 'skewX(-10deg)', textShadow: '0 0 12px rgba(229, 72, 56, 0.5)' }}>/</span>
          <span style={{ color: '#ffffff', fontWeight: 800, fontSize: '24px', letterSpacing: '-0.5px', fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>vermeg</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981', boxShadow: '0 0 6px #10b981' }}></span>
          <span style={{ color: '#cbd5e1', fontSize: '10px', fontWeight: 700, letterSpacing: '1.2px', textTransform: 'uppercase' }}>
            CONTRAT VIVANT
          </span>
        </div>
      </div>

      {/* Profil + rôle + déconnexion en dessous du logo */}
      <div className="sidebar-profile">
        <div className="avatar-circle" id="profile-avatar">{getAvatarInitials(user?.username)}</div>
        <div className="user-info"><div className="user-name" id="profile-name">{user?.username || 'Ahmed Trabelsi'}</div><div className="user-role" id="profile-role">{roleText}</div></div>
      </div>
      <ul className="nav-menu">{menuItems.map((item) => <li key={item.id} className={`nav-item ${activeTab === item.id ? 'active' : ''}`} onClick={() => setActiveTab(item.id)}><span className="nav-icon">{item.icon}</span>{item.label}</li>)}</ul>
      <button className="btn-logout" onClick={logout}>Déconnexion</button>
    </aside>
  );
}
