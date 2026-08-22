
import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';

import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';

import AnalyseDossierView from './pages/AnalyseDossierView';
import SinistresView from './pages/SinistresView';
import ContratsView from './pages/ContratsView';
import ClientsView from './pages/ClientsView';
import HistoriqueView from './pages/HistoriqueView';

import ChatAssistant from './components/ChatAssistant';

import {
  sinistresAPI,
  contratsAPI,
  clientsAPI,
  alertsAPI
} from './services/api';

import './styles.css';


function MainDashboard() {

  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState('analyse');

  const [sinistres, setSinistres] = useState([]);
  const [contrats, setContrats] = useState([]);
  const [clients, setClients] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const [toastMsg, setToastMsg] = useState('');
  const [loading, setLoading] = useState(true);


  const loadData = async (triggerToastText) => {

    try {

      const [
        sList,
        cList,
        clList,
        aList
      ] = await Promise.all([
        sinistresAPI.getSinistres(),
        contratsAPI.getContrats(),
        clientsAPI.getClients(),
        alertsAPI.getAlerts().catch(() => [])
      ]);

      setSinistres(sList);
      setContrats(cList);
      setClients(clList);
      setAlerts(aList);

      if (triggerToastText) {
        setToastMsg(triggerToastText);

        setTimeout(() => {
          setToastMsg('');
        }, 5000);
      }

    } catch (e) {

      console.error('Erreur chargement données:', e);

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {
    loadData();
  }, []);


  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#f3f4f6',
        color: '#111827'
      }}
    >

      {/* SIDEBAR */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />


      <main
        className="main-content"
        style={{
          padding: '24px 32px'
        }}
      >

        {/* TOP ALERT BANNER */}

        <div
          style={{
            backgroundColor: '#1e1b4b',
            color: '#fff',
            borderRadius: '12px',
            padding: '14px 20px',
            marginBottom: '20px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >

            <span style={{ fontSize: '20px' }}>
              ⚠️
            </span>

            <div>

              <div
                style={{
                  fontSize: '13px',
                  fontWeight: 700,
                  color: '#fbbf24'
                }}
              >
                ALERTE SYSTEME — Session Active (
                {user?.role === 'sinistres'
                  ? 'Pôle Gestion des Sinistres'
                  : 'Pôle Gestion des Assurances'}
                )
              </div>

              <div
                style={{
                  fontSize: '12px',
                  color: '#cbd5e1',
                  marginTop: '2px'
                }}
              >
                {alerts.length > 0
                  ? `Vous avez ${alerts.length} alerte(s) contextuelle(s) non résolue(s) sur votre agence.`
                  : `Connecté en tant que ${user?.username || 'Gestionnaire'} (Agence ${user?.agence_id || 'AG01'}). Rôles et traçabilité d'audit actifs.`
                }
              </div>

            </div>

          </div>


          <button
            onClick={() => setActiveTab('historique')}
            style={{
              backgroundColor: '#e54838',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Voir l'Historique & Alertes →
          </button>

        </div>


        {/* TOAST */}

        {toastMsg && (

          <div
            style={{
              position: 'fixed',
              top: '24px',
              right: '24px',
              zIndex: 10000,
              backgroundColor: '#10b981',
              color: '#fff',
              padding: '12px 20px',
              borderRadius: '8px',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
              fontSize: '13px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <span>🔔</span>
            <span>{toastMsg}</span>
          </div>

        )}


        {/* ========================= */}
        {/* PAGES */}
        {/* ========================= */}

        {activeTab === 'analyse' && (
          <AnalyseDossierView
            sinistres={sinistres}
            contrats={contrats}
          />
        )}


        {activeTab === 'sinistres' && (
          <SinistresView
            sinistres={sinistres}
            contrats={contrats}
            onRefresh={() =>
              loadData(
                "🔔 Un nouveau sinistre a été déclaré et consigné dans l'historique !"
              )
            }
          />
        )}


        {activeTab === 'contrats' && (
          <ContratsView
            contrats={contrats}
            clients={clients}
            onRefresh={() =>
              loadData(
                '🔔 Un nouveau contrat a été créé et notifié au service !'
              )
            }
          />
        )}


        {activeTab === 'clients' && (
          <ClientsView
            clients={clients}
            contrats={contrats}
            onRefresh={() =>
              loadData(
                '🔔 Nouveau client ajouté avec succès dans la base commune !'
              )
            }
          />
        )}


        {/* HISTORIQUE */}

        {activeTab === 'historique' && (
          <HistoriqueView />
        )}

      </main>


      <ChatAssistant />

    </div>
  );
}



function AppContent() {

  const { isAuthenticated } = useAuth();

  const [authMode, setAuthMode] = useState('login');


  if (!isAuthenticated) {

    if (authMode === 'signup') {

      return (
        <SignupPage
          onNavigateToLogin={() => setAuthMode('login')}
        />
      );

    }

    return (
      <LoginPage
        onNavigateToSignup={() => setAuthMode('signup')}
      />
    );
  }


  // IMPORTANT :
  // lorsque l'utilisateur est connecté,
  // on affiche le dashboard.

  return <MainDashboard />;
}



export default function App() {

  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );

}

