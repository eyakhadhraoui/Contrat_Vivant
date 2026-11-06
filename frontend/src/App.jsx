
import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';

import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';

import AnalyseDossierView from './pages/AnalyseDossierView';
import MapView from './pages/MapView';
import SinistresView from './pages/SinistresView';
import ContratsView from './pages/ContratsView';
import ClientsView from './pages/ClientsView';
import HistoriqueView from './pages/HistoriqueView';
import DocumentsView from './pages/DocumentsView';
import DashboardView from './pages/DashboardView';
import ValidationsView from './pages/ValidationsView';
import SettingsView from './pages/SettingsView';
import CourriersView from './pages/CourriersView';
import PrioriteRisqueView from './pages/PrioriteRisqueView';
import ComintyAnalysisView from './pages/ComintyAnalysisView';

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

  const [activeTab, setActiveTab] = useState('risque');

  const [sinistres, setSinistres] = useState([]);
  const [contrats, setContrats] = useState([]);
  const [clients, setClients] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [preferences, setPreferences] = useState(() => {
    try { return JSON.parse(localStorage.getItem('appPreferences') || '{"emailAlerts":true,"compactView":false}'); }
    catch { return { emailAlerts: true, compactView: false }; }
  });

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
          padding: preferences.compactView ? '14px 18px' : '24px 32px'
        }}
      >

        {/* TOP ALERT BANNER */}

        <div
          style={{
            backgroundColor: '#fff4e5',
            color: '#6b3d16',
            borderRadius: '12px',
            padding: '14px 20px',
            marginBottom: '20px',
            border: '1px solid #f4d8b5',
            boxShadow: '0 2px 5px rgba(0,0,0,0.03)',
            display: preferences.emailAlerts ? 'flex' : 'none',
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
                  color: '#8b4a0c'
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
                  color: '#825d3a',
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
              backgroundColor: '#0c093a',
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


        {activeTab === 'map' && (
          <MapView
            sinistres={sinistres}
            contrats={contrats}
            onSelectContratForAnalyse={(contratId) => {
              setActiveTab('analyse');
            }}
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


        {activeTab === 'documents' && <DocumentsView />}

        {activeTab === 'dashboard' && (
          <DashboardView sinistres={sinistres} contrats={contrats} clients={clients} alerts={alerts} onNavigate={setActiveTab} />
        )}

        {activeTab === 'validations' && <ValidationsView onRefresh={() => loadData()} />}

        {/* HISTORIQUE */}
        {activeTab === 'historique' && <HistoriqueView />}

        {activeTab === 'settings' && <SettingsView onPreferencesChange={setPreferences} />}

        {activeTab === 'courriers' && <CourriersView contrats={contrats} sinistres={sinistres} />}

        {activeTab === 'risque' && <PrioriteRisqueView />}
        {activeTab === 'cominty' && <ComintyAnalysisView />}

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

