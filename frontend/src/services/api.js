const API_BASE_URL = '/api';

export function getAuthHeaders() {
  const token = localStorage.getItem('authToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });
  
  if (response.status === 401) {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    window.location.href = '/';
    throw new Error('Session expirée');
  }

  return response;
}

export const authAPI = {
  async login(username, password) {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Échec de connexion');
    return data;
  },

  async signup(userData) {
    const res = await fetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Échec d\'inscription');
    return data;
  },
};

export const agencesAPI = {
  async getAgences() {
    const res = await fetch('/api/agences');
    if (!res.ok) return [];
    const data = await res.json();
    return data.agences || [];
  },
};

export const sinistresAPI = {
  async getSinistres() {
    const res = await apiFetch('/api/sinistres');
    if (!res.ok) return [];
    const data = await res.json();
    return data.sinistres || [];
  },
  async addSinistre(sinistreData) {
    const res = await apiFetch('/api/sinistres', {
      method: 'POST',
      body: JSON.stringify(sinistreData),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de l\'ajout du sinistre');
    }
    return await res.json();
  },
  async updateSinistre(id, payload) {
    const res = await apiFetch(`/api/sinistres/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la modification du sinistre');
    }
    return await res.json();
  },
  async deleteSinistre(id) {
    const res = await apiFetch(`/api/sinistres/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la suppression du sinistre');
    }
    return await res.json();
  },
  async downloadPDF(id) {
    const headers = getAuthHeaders();
    const res = await fetch(`/api/pdf/sinistre/${id}`, { headers });
    if (!res.ok) throw new Error('Impossible de générer le PDF du sinistre');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Rapport_Sinistre_${id}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
};

export const contratsAPI = {
  async getContrats() {
    const res = await apiFetch('/api/contrats');
    if (!res.ok) return [];
    const data = await res.json();
    return data.contrats || [];
  },
  async addContrat(contratData) {
    const res = await apiFetch('/api/contrats', {
      method: 'POST',
      body: JSON.stringify(contratData),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de l\'ajout du contrat');
    }
    return await res.json();
  },
  async updateContrat(id, payload) {
    const res = await apiFetch(`/api/contrats/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la modification du contrat');
    }
    return await res.json();
  },
  async deleteContrat(id) {
    const res = await apiFetch(`/api/contrats/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la suppression du contrat');
    }
    return await res.json();
  },
  async downloadPDF(id) {
    const headers = getAuthHeaders();
    const res = await fetch(`/api/pdf/contrat/${id}`, { headers });
    if (!res.ok) throw new Error('Impossible de générer le PDF du contrat');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Attestation_Contrat_${id}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
};

export const clientsAPI = {
  async getClients() {
    const res = await apiFetch('/api/clients');
    if (!res.ok) return [];
    const data = await res.json();
    return data.clients || [];
  },
  async addClient(clientData) {
    const res = await apiFetch('/api/clients', {
      method: 'POST',
      body: JSON.stringify(clientData),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la création du client');
    }
    return await res.json();
  },
};

export const cinAPI = {
  async extractCIN(file) {
    const formData = new FormData();
    formData.append('file', file);

    const headers = getAuthHeaders();
    const res = await fetch('/api/cin/extract', {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Échec de l\'extraction OCR de la CIN');
    }

    return await res.json();
  },
};


export const historiqueAPI = {
  async getHistorique() {
    const res = await apiFetch('/api/historique');
    if (!res.ok) return [];
    const data = await res.json();
    return data.logs || data.historique || [];
  },
  async downloadAuditPDF() {
    const headers = getAuthHeaders();
    const res = await fetch('/api/pdf/audit', { headers });
    if (!res.ok) throw new Error('Impossible de générer le rapport PDF d\'audit');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Rapport_Audit_${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
  async downloadAuditCSV() {
    const headers = getAuthHeaders();
    const res = await fetch('/api/audit/csv', { headers });
    if (!res.ok) throw new Error('Impossible d\'exporter le journal d\'audit en CSV');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Journal_Audit_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },
};

export const alertsAPI = {
  async getAlerts() {
    const res = await apiFetch('/api/alerts');
    if (!res.ok) return [];
    const data = await res.json();
    return data.alerts || [];
  },
  async validateAlert(alertId, action, comment = '', state = {}) {
    const res = await apiFetch('/api/alerts/validate', {
      method: 'POST',
      body: JSON.stringify({
        alert_id: alertId,
        action: action,
        comment: comment,
        state: state,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la validation de l\'alerte');
    }
    return await res.json();
  },
};

export const ragAPI = {
  async getDocuments() {
    const res = await apiFetch('/api/rag/documents');
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la récupération des documents RAG');
    }
    const data = await res.json();
    return data.documents || [];
  },

  async ingestDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const headers = getAuthHeaders();
    const res = await fetch('/api/rag/ingest', {
      method: 'POST',
      headers: {
        ...headers,
      },
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de l\'ingestion documentaire');
    }

    return await res.json();
  },

  async deleteDocument(docId) {
    const res = await apiFetch(`/api/rag/documents/${docId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la suppression du document');
    }
    return await res.json();
  },
};

export const chatAPI = {
  async getHistory() {
    const res = await apiFetch('/api/chat/history');
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur chargement historique chat');
    }
    const data = await res.json();
    return data.history || [];
  },

  async sendMessage(message, contextData = {}) {
    const res = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, ...contextData }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de la communication avec l\'assistant');
    }
    return await res.json();
  },

  async clearHistory() {
    const res = await apiFetch('/api/chat/history', {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur effacement historique');
    }
    return await res.json();
  },
};

export const analysisAPI = {
  async runAnalyse(contratId, modificationType = 'standard') {
    const res = await apiFetch('/api/analyser', {
      method: 'POST',
      body: JSON.stringify({ contrat_id: contratId, modification_type: modificationType }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors de l\'analyse du dossier');
    }
    return await res.json();
  },
};
