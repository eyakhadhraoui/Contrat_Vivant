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
    { id: 'analyse', label: 'Analyse de dossier', icon: '🔍' },
    { id: 'sinistres', label: 'Mes sinistres', icon: '📋' },
    { id: 'contrats', label: 'Mes contrats', icon: '📄' },
    { id: 'clients', label: 'Mes clients', icon: '👥' },
    { id: 'historique', label: "Historique d'audit", icon: '🕒' },
  ];

  return (
    <aside className="sidebar">
      {/* Logo en haut */}
      <div className="sidebar-logo">
        <img src="/logo-transparent.png" alt="Logo" className="logo-img" />
      </div>

      {/* Profil + rôle + déconnexion en dessous du logo */}
        <div className="profile-header">
        <div className="avatar-circle" id="profile-avatar">
          {getAvatarInitials(user?.username)}
        </div>
        <div className="user-info">
          <div className="user-name" id="profile-name">
            {user?.username || 'Ahmed Trabelsi'}
          </div>
          <div className="user-role" id="profile-role">
            {roleText}
          </div>
        </div>

      <ul className="nav-menu">
        {menuItems.map((item) => (
          <li
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </li>
        ))}
      </ul>
    
        <button className="btn-logout" onClick={logout}>
          Déconnexion
        </button>
      </div>
    </aside>
  );
}