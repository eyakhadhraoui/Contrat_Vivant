import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Coordonnées GPS préférentielles des gouvernorats et villes tunisiennes
const TUNISIA_CITIES_COORDS = {
  'tunis': { lat: 36.8065, lng: 10.1815, region: 'Tunis' },
  'ariana': { lat: 36.8665, lng: 10.1930, region: 'Ariana' },
  'ben arous': { lat: 36.7531, lng: 10.2283, region: 'Ben Arous' },
  'nabeul': { lat: 36.4561, lng: 10.7376, region: 'Nabeul / Hammamet' },
  'sousse': { lat: 35.8256, lng: 10.6369, region: 'Sousse' },
  'monastir': { lat: 35.7833, lng: 10.8333, region: 'Monastir' },
  'sfax': { lat: 34.7406, lng: 10.7603, region: 'Sfax' },
  'bizerte': { lat: 37.2744, lng: 9.8739, region: 'Bizerte' },
  'kairouan': { lat: 35.6781, lng: 10.0963, region: 'Kairouan' },
  'gabes': { lat: 33.8815, lng: 10.0982, region: 'Gabès' },
};

// Factory d'icônes Leaflet personnalisées avec gradients HSL
const createCustomPin = (color, label = '🚗') => {
  return L.divIcon({
    className: 'custom-leaflet-pin',
    html: `
      <div style="
        background: ${color};
        width: 34px;
        height: 34px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.35);
        border: 2px solid #ffffff;
      ">
        <div style="
          transform: rotate(45deg);
          font-size: 14px;
        ">${label}</div>
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -34],
  });
};

export default function MapView({ sinistres = [], contrats = [], onSelectContratForAnalyse }) {
  const [selectedRegion, setSelectedRegion] = useState('toutes');
  const [selectedType, setSelectedType] = useState('tous');
  const [selectedUrgency, setSelectedUrgency] = useState('tous');

  // Associe des coordonnées GPS réelles à chaque sinistre
  const geocodedSinistres = sinistres.map((s, idx) => {
    const lieuStr = (s.lieu || s.lieu_sinistre || s.agence_nom || 'Tunis').toLowerCase();

    let coords = { lat: 36.8065 + (idx * 0.015) % 0.08, lng: 10.1815 + (idx * 0.02) % 0.09, region: 'Tunis' };

    for (const [key, cityInfo] of Object.entries(TUNISIA_CITIES_COORDS)) {
      if (lieuStr.includes(key)) {
        // Ajouter une légère variation aléatoire pour ne pas superposer exactement les marqueurs
        const latOffset = ((idx * 7) % 10 - 5) * 0.005;
        const lngOffset = ((idx * 13) % 10 - 5) * 0.005;
        coords = { lat: cityInfo.lat + latOffset, lng: cityInfo.lng + lngOffset, region: cityInfo.region };
        break;
      }
    }

    const mDec = parseFloat(s.montant_declare || 0);
    let pinColor = '#10b981'; // Vert par défaut
    let riskLevel = 'faible';

    if (mDec > 8000 || (s.description && s.description.toLowerCase().includes('lourd'))) {
      pinColor = '#ef4444'; // Rouge
      riskLevel = 'eleve';
    } else if (mDec > 2500 || s.statut === 'en_cours') {
      pinColor = '#f59e0b'; // Ambre
      riskLevel = 'moyen';
    }

    let pinIcon = '🚗';
    const sType = (s.type_sinistre || s.type || '').toLowerCase();
    if (sType.includes('incendie')) pinIcon = '🔥';
    else if (sType.includes('inondation') || sType.includes('eau')) pinIcon = '🌊';
    else if (sType.includes('vol')) pinIcon = '🚨';
    else if (sType.includes('habitation')) pinIcon = '🏠';

    return {
      ...s,
      lat: coords.lat,
      lng: coords.lng,
      regionName: coords.region,
      pinColor,
      pinIcon,
      riskLevel,
      montantVal: mDec,
    };
  });

  // Filtrage dynamique
  const filteredSinistres = geocodedSinistres.filter((s) => {
    if (selectedRegion !== 'toutes' && !s.regionName.toLowerCase().includes(selectedRegion.toLowerCase())) return false;
    if (selectedType !== 'tous' && !s.type_sinistre?.toLowerCase().includes(selectedType.toLowerCase())) return false;
    if (selectedUrgency !== 'tous' && s.riskLevel !== selectedUrgency) return false;
    return true;
  });

  // KPIs Géographiques
  const totalMontant = filteredSinistres.reduce((sum, s) => sum + s.montantVal, 0);
  const totalUrgent = filteredSinistres.filter((s) => s.riskLevel === 'eleve').length;

  const formatDT = (val) => Number(val || 0).toLocaleString('fr-FR') + ' DT';

  return (
    <section id="page-map" className="page-view active">
      <header className="page-header">
        <div>
          <h1 className="page-title">🗺️ Carte Géographique des Risques & Sinistres</h1>
          <p className="page-subtitle">Visualisation spatiale interactive, heatmap d'accidentologie et analyse par gouvernorat.</p>
        </div>
      </header>

      {/* PANNEAU DE FILTRES GÉOGRAPHIQUES ET MÉTIER */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', background: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
        <div>
          <label style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Gouvernorat / Région</label>
          <select
            className="form-control"
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            style={{ marginTop: '4px', width: '100%', fontSize: '13px' }}
          >
            <option value="toutes">Toutes les régions (Tunisie)</option>
            <option value="tunis">Grand Tunis</option>
            <option value="ariana">Ariana</option>
            <option value="nabeul">Nabeul / Cap Bon</option>
            <option value="sousse">Sousse / Sahel</option>
            <option value="sfax">Sfax</option>
            <option value="bizerte">Bizerte</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Type de Sinistre</label>
          <select
            className="form-control"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            style={{ marginTop: '4px', width: '100%', fontSize: '13px' }}
          >
            <option value="tous">Tous les types</option>
            <option value="auto">Auto (Accidents / Carambolages)</option>
            <option value="incendie">Incendie</option>
            <option value="inondation">Inondation / Dégâts des eaux</option>
            <option value="vol">Vol & Vandalisme</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Niveau de Risque / Sévérité</label>
          <select
            className="form-control"
            value={selectedUrgency}
            onChange={(e) => setSelectedUrgency(e.target.value)}
            style={{ marginTop: '4px', width: '100%', fontSize: '13px' }}
          >
            <option value="tous">Tous les niveaux</option>
            <option value="eleve">🔴 Élevé / Sinistre Lourd (&gt; 8000 DT)</option>
            <option value="moyen">🟠 Moyen (2500 DT - 8000 DT)</option>
            <option value="faible">🟢 Faible (&lt; 2500 DT)</option>
          </select>
        </div>
      </div>

      {/* KPI GRID SPATIAL */}
      <div className="kpi-grid" style={{ marginBottom: '16px' }}>
        <div className="kpi-card">
          <div className="kpi-label">Sinistres Géolocalisés</div>
          <div className="kpi-value">{filteredSinistres.length} dossier(s)</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Sinistralité Totale</div>
          <div className="kpi-value" style={{ color: '#dc2626' }}>{formatDT(totalMontant)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Dossiers à Haut Risque</div>
          <div className="kpi-value" style={{ color: '#ea580c' }}>{totalUrgent} alerte(s)</div>
        </div>
      </div>

      {/* CARTE LEAFLET INTERACTIVE */}
      <div style={{ height: '520px', width: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid #cbd5e1', boxShadow: '0 4px 14px rgba(0,0,0,0.08)' }}>
        <MapContainer
          center={[35.8000, 10.2000]}
          zoom={7}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Zones de concentration de risque (Heatmap Circles) */}
          {filteredSinistres.filter(s => s.riskLevel === 'eleve').map((s, idx) => (
            <Circle
              key={`circle-${idx}`}
              center={[s.lat, s.lng]}
              radius={8000}
              pathOptions={{ fillColor: '#ef4444', fillOpacity: 0.18, color: '#dc2626', weight: 1 }}
            />
          ))}

          {/* Marqueurs individuels de sinistres */}
          {filteredSinistres.map((s, idx) => (
            <Marker
              key={`marker-${idx}`}
              position={[s.lat, s.lng]}
              icon={createCustomPin(s.pinColor, s.pinIcon)}
            >
              <Popup>
                <div style={{ padding: '4px', maxWidth: '240px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>
                    Dossier N° {s.id}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#475569', marginBottom: '2px' }}>
                    • <strong>Client :</strong> {s.client || s.client_nom || 'Client Assuré'}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#475569', marginBottom: '2px' }}>
                    • <strong>Contrat :</strong> {s.contrat_id}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#475569', marginBottom: '2px' }}>
                    • <strong>Région :</strong> {s.regionName} ({s.lieu || 'N/A'})
                  </div>
                  <div style={{ fontSize: '12px', fontWeight: 800, color: '#dc2626', marginTop: '6px' }}>
                    Montant : {formatDT(s.montant_declare)}
                  </div>
                  {onSelectContratForAnalyse && (
                    <button
                      onClick={() => onSelectContratForAnalyse(s.contrat_id)}
                      style={{ marginTop: '8px', width: '100%', padding: '6px', backgroundColor: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
                    >
                      🔍 Analyser ce dossier
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </section>
  );
}
