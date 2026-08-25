# 🏢 Le Contrat Vivant — Contrat Vivant API

**Plateforme intelligente de gestion d'assurances** combinant analyse de risque automatisée, système multi-agents IA, RAG contextuel, OCR et notifications multicanales.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-19.2.8-61DAFB?logo=react)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agents-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![License](https://img.shields.io/badge/license-Interne-lightgrey)

---

## 📋 Table des matières

- [Aperçu](#-aperçu)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Stack technique](#-stack-technique)
- [Système multi-agents](#-système-multi-agents-langgraph)
- [Moteur de règles](#-moteur-de-règles-risk-analyzer)
- [Modèle de données](#-modèle-de-données)
- [Installation](#-installation)
- [Variables d'environnement](#-variables-denvironnement)
- [API — Endpoints principaux](#-api--endpoints-principaux)
- [Tests](#-tests)
- [Déploiement Docker](#-déploiement-docker)
- [Points d'attention & Roadmap](#-points-dattention--roadmap)

---

## 🔍 Aperçu

**Le Contrat Vivant** est une application web full-stack interne destinée à digitaliser et automatiser le cycle de vie complet des contrats d'assurance : de la création du contrat à la gestion des sinistres, en passant par l'analyse de risque, la détection de fraude et l'assistance IA contextuelle.

| | |
|---|---|
| **Domaine** | Assurance — Gestion de contrats et sinistres |
| **Type** | Application full-stack + système multi-agents IA |
| **Langages** | Python 3.12 (backend) · JavaScript / React (frontend) |

---

## ✨ Fonctionnalités

- 📄 **Gestion des contrats** : création, modification, suppression, avenants
- 🚨 **Gestion des sinistres** : déclaration, traitement, analyse
- 🧠 **Analyse de risque intelligente** : moteur de règles déterministe + LLM complémentaire
- 🕵️ **Détection de fraude** : scoring 0–100, anomalies, patterns suspects
- 🔔 **Notifications multicanales** : Email, Microsoft Teams, in-app
- 💬 **Assistant IA contextuel** : RAG sur procédures d'assurance, chat avec historique persistant
- 🔎 **OCR & extraction** : CIN, constat amiable, analyse de devis garage
- 🧾 **Traçabilité complète** : audit log, historique, rollback, export PDF/CSV

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 19)                       │
│  Pages : Analyse | Carte | Sinistres | Contrats | Clients | Chat │
└───────────────────────────────┬─────────────────────────────────┘
                                 │ HTTP/JSON
┌───────────────────────────────▼─────────────────────────────────┐
│                   BACKEND (FastAPI 0.100+)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   API REST   │  │  Auth JWT    │  │  Prometheus /metrics    │  │
│  └──────┬──────┘  └──────┬───────┘  └─────────────────────────┘  │
│         │                │                                       │
│  ┌──────▼────────────────▼─────────────────────────────────────┐│
│  │              LANGGRAPH WORKFLOW (Multi-Agents)               ││
│  │  CollectorAgent → RiskAgent → AlertAgent → HITL → History    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐│
│  │  COUCHES MÉTIER                                              ││
│  │  • rules_engine (score 0-100, anomalies déterministes)       ││
│  │  • llm (Gemini + fallback Ollama local)                      ││
│  │  • rag (FAISS + sentence-transformers + MySQL)               ││
│  │  • tools (contrats, sinistres, auth, notifications, OCR)     ││
│  └────────────────────────┬────────────────────────────────────┘│
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────────┐│
│  │              BASE DE DONNÉES MySQL 8.0                       ││
│  │  agences, gestionnaires, clients, contrats, sinistres,       ││
│  │  historique, audit_log, rag_documents, chat_messages         ││
│  └───────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
                                 │
                     ┌───────────┼───────────┐
                     │           │           │
               ┌─────▼─────┐ ┌───▼────┐ ┌───▼─────┐
               │ Prometheus │ │ Teams  │ │  SMTP   │
               │ (port 9090)│ │Webhook │ │  Email  │
               └───────────┘  └────────┘ └─────────┘
```

---

## 🛠️ Stack technique

### Backend

| Composant | Version / Outil | Rôle |
|---|---|---|
| Framework | FastAPI ≥ 0.100.0 | API REST, CORS, static files |
| Orchestration IA | LangGraph ≥ 0.0.20 | Workflow multi-agents |
| LLM | Google GenAI (Gemini) + Ollama (local) | Analyse LLM, synthèse, chat |
| RAG | FAISS CPU + Sentence-Transformers + PyPDF | Ingestion et recherche de procédures |
| Base de données | MySQL 8.0 (mysql-connector-python) | Persistance principale |
| Auth | PyJWT + bcrypt | Authentification Bearer JWT |
| OCR | pytesseract + Pillow | Extraction CIN et constats |
| PDF | ReportLab | Génération attestations, avenants, rapports |
| Monitoring | prometheus-fastapi-instrumentator | Métriques `/metrics` |

### Frontend

| Composant | Version | Rôle |
|---|---|---|
| Framework | React 19.2.8 | SPA |
| Build | Vite 8.2.0 | Dev server + bundling |
| Cartographie | React-Leaflet 5.0.0 | Visualisation géographique |
| Linting | Oxlint 1.75.0 | Qualité du code |

### Infrastructure

| Composant | Version | Rôle |
|---|---|---|
| Conteneurisation | Docker + Docker Compose | MySQL, Backend, Frontend, Prometheus |
| Base de données | MySQL 8.0 (port 3307 host) | Container `assurance-mysql` |
| Monitoring | Prometheus 2.47.0 | Métriques applicatives |

---

## 🤖 Système multi-agents (LangGraph)

### Workflow principal

```
Entrée : { token, contrat_id, modification_type }
   │
   ▼
[1] CollectorAgent
   ├─ Authentification (résolution rôle via JWT)
   ├─ Collecte contrat + sinistres depuis MySQL
   ├─ Contrôle d'intégrité (données manquantes)
   └─ Évaluation confiance (haute/moyenne/faible)
   │
   ▼
[2] RiskAnalysisAgent
   ├─ cross_analysis : moteur de règles déterministe + LLM complémentaire
   ├─ classify_event : classification contrat/sinistre/risque
   └─ calculate_urgency : score 0-100 + niveau d'urgence
   │
   ▼
[3] AlertNotificationAgent
   ├─ summarize_dossier : synthèse LLM du dossier
   ├─ build_alert : construction carte d'alerte
   ├─ generate_recommendation : recommandation graduée
   ├─ route_to_gestionnaire : routage assurances/sinistres
   └─ cross_notify : notifications Email + Teams + in-app
   │
   ▼
[4] Human Validation (HITL)
   └─ Validation / Ajustement / Rejet par le gestionnaire
   │
   ▼
[5] History Update
   └─ Mise à jour historique SI si validé
   │
   ▼
Sortie : état complet du workflow
```

### Agents spécialisés

| Agent | Rôle | Points d'entrée (nodes) |
|---|---|---|
| `CollectorAgent` | Collecte et intégration SI | `auth_node`, `collect_node` |
| `RiskAnalysisAgent` | Évaluation risques, détection anomalies | `cross_analysis_node`, `classify_node`, `urgency_node` |
| `AlertNotificationAgent` | Synthèse, alertes, notifications | `summarizer_node`, `alert_node`, `recommendation_node`, `routing_node`, `cross_notification_node` |
| `SupervisorAgent` | Orchestration, coordination HITL | `human_validation_node`, `history_update_node` |

---

## ⚙️ Moteur de règles (Risk Analyzer)

### Facteurs de risque (poids configurables)

| Facteur | Poids | Description |
|---|---|---|
| `recurrence` | 20% | Nombre de sinistres, mêmes causes |
| `delai` | 20% | Écart temporel entre sinistres (< 180j rapproché, < 730j intermédiaire) |
| `montant_plafond` | 25% | Montant cumulé vs garantie_max, détection outlier |
| `anciennete` | 15% | Délai souscription → premier sinistre (< 90j = fraude potentielle) |
| `pattern_suspect` | 20% | Circonstances similaires, sinistre post-avenant, fréquence élevée |

### Niveaux d'urgence (seuils configurables)

| Niveau | Score | Action recommandée |
|---|---|---|
| 🔴 `critique` | ≥ 81 | Escalade anti-fraude + évaluation résiliation |
| 🟠 `eleve` | 61–80 | Escalade anti-fraude + contrôle renforcé |
| 🟡 `moyen` | 31–60 | Révision contractuelle (franchise, surprime) |
| 🟢 `faible` | 0–30 | Surveillance, revue à 90 jours |

### Règles déterministes

- `ecart_garantie_montant` : écart > 40 % entre montant déclaré et plafond
- `sinistres_repetes` : 2+ sinistres en 30 jours
- `retard_paiement` : retard > 15 jours (configurable)

---

## 🗄️ Modèle de données

| Table | Clé primaire | Champs principaux | Relations |
|---|---|---|---|
| `agences` | `id` (VARCHAR 10) | nom, ville, adresse | 1→N gestionnaires, contrats, sinistres |
| `gestionnaires` | `id` (VARCHAR 10) | nom, prenom, username, email, password_hash, role, agence_id | N→1 agences |
| `clients` | `id` (VARCHAR 10) | nom, prenom, cin, email, telephone, adresse, date_naissance | 1→N contrats |
| `contrats` | `id` (VARCHAR 20) | client_id, type_contrat, garantie_max, prime_mensuelle, franchise, dates, statut, couverture, exclusions | N→1 clients/gestionnaires/agences ; 1→N sinistres |
| `sinistres` | `id` (VARCHAR 20) | contrat_id, type_sinistre, montant_declare, dates, responsabilite, statut | N→1 contrats/gestionnaires/agences |
| `historique` | `id` (AUTO) | contrat_id, alert (JSON), validation_status | N→1 contrats, gestionnaires |
| `audit_log` | `id` (AUTO) | step, data (JSON), gestionnaire_id, timestamp | Traçabilité universelle |
| `rag_documents` | `id` (AUTO) | filename, file_type, file_size, chunks_count, content_text | Documents persistants RAG |
| `chat_messages` | `id` (AUTO) | session_id, gestionnaire_id, sender, message, sources (JSON) | Historique chat persistant |

### Règles d'intégrité métier

- ✅ Un client ne peut avoir qu'**un seul contrat actif/suspendu par type** (`auto`, `habitation`, `vie`, `sante`)
- ✅ Impossible d'ajouter un sinistre si le contrat est `suspendu` ou `resilie`
- ✅ Le type de sinistre doit correspondre au type de contrat

---

## 🚀 Installation

### Prérequis

- Python 3.12+
- Node.js 18+ / npm
- MySQL 8.0
- Docker & Docker Compose (optionnel, recommandé)

### 1. Cloner le dépôt

```bash
git clone https://github.com/<votre-org>/agent-assurance.git
cd agent-assurance
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # renseigner les variables (voir section suivante)
uvicorn main_api:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Base de données

```bash
mysql -u root -p < schema.sql
```

---

## 🔐 Variables d'environnement

| Variable | Description |
|---|---|
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | Connexion base de données |
| `GOOGLE_API_KEY` | Clé LLM Gemini |
| `OPENAI_API_KEY` | Alternative LLM |
| `TAVILY_API_KEY` | Recherche web (agent tools) |
| `JWT_SECRET_KEY` | Signature des tokens JWT |
| `EMAIL_SENDER` / `EMAIL_PASSWORD` | Configuration SMTP |
| `TEAMS_WEBHOOK_URL` | Notifications Microsoft Teams |
| `AUTO_APPLY_LOW_RISK` | Application automatique des modifications à bas risque |

> ⚠️ En production, veillez à générer un `JWT_SECRET_KEY` fort et à restreindre `CORS` aux domaines autorisés.

---

## 🌐 API — Endpoints principaux

| Méthode | Endpoint | Rôle |
|---|---|---|
| `POST` | `/api/login` | Authentification JWT |
| `POST` | `/api/auth/google` | SSO Google |
| `POST` | `/api/signup` | Inscription gestionnaire |
| `GET` / `POST` / `PUT` / `DELETE` | `/api/contrats` | CRUD contrats |
| `POST` | `/api/contrats/{id}/notes` | Note vocale structurée par LLM |
| `GET` / `POST` / `PUT` / `DELETE` | `/api/sinistres` | CRUD sinistres |
| `POST` | `/api/analyser` | Lancement du workflow IA complet |
| `POST` | `/api/alerts/validate` | Validation / ajustement / rejet d'alerte |
| `POST` | `/api/alerts/rollback` | Rollback d'une modification |
| `POST` | `/api/cin/extract` | OCR CIN |
| `POST` | `/api/ocr/constat` | Extraction constat amiable |
| `POST` | `/api/devis/analyser` | Analyse devis garage |
| `GET` | `/api/pdf/contrat/{id}` | PDF attestation |
| `GET` | `/api/pdf/sinistre/{id}` | PDF rapport sinistre |
| `GET` | `/api/pdf/avenant/{id}` | PDF avenant |
| `GET` | `/api/pdf/audit` | PDF rapport audit |
| `GET` | `/api/audit/csv` | Export CSV audit |
| `GET` / `POST` / `DELETE` | `/api/rag/documents` · `/api/rag/ingest` | Gestion RAG |
| `POST` / `GET` / `DELETE` | `/api/chat` · `/api/chat/history` | Chat IA & historique |
| `GET` | `/api/agences` · `/api/clients` · `/api/alerts` | Référentiels & alertes |
| `GET` | `/metrics` | Métriques Prometheus |

📖 Documentation interactive disponible via Swagger : `http://localhost:8000/docs`

---

## 🧪 Tests

| Fichier | Nature | Couverture |
|---|---|---|
| `tests/test_business_rules.py` | Unitaires + intégration | Permissions, règles métier, notifications croisées, CRUD |
| `tests/test_multi_agent.py` | Unitaires + intégration | Agents individuels, SupervisorAgent, workflow LangGraph complet |

**Points testés :**
- Permissions par rôle (`assurances` / `sinistres`) et par agence
- Règles déterministes (`ecart_garantie_montant`, `sinistres_repetes`)
- Notifications croisées (Email + Teams simulés)
- Unicité contrat par type par client
- Blocage sinistre sur contrat suspendu/résilié
- Normalisation des IDs contrat (C001 → CSTR00001)
- Exécution complète du workflow LangGraph avec mocks

```bash
pytest tests/ -v
```

---

## 🐳 Déploiement Docker

```bash
docker compose up -d --build
```

| Service | Image | Ports | Rôle |
|---|---|---|---|
| `db` | mysql:8.0 | 3307 → 3306 | Base de données |
| `backend` | Build local | 8000 | API FastAPI |
| `frontend` | Build local (`frontend/`) | 80 | Nginx SPA |
| `prometheus` | prom/prometheus:v2.47.0 | 9090 | Monitoring |

---

## ⚠️ Points d'attention & Roadmap

### Sécurité
- [ ] Forcer la rotation du `JWT_SECRET_KEY` en production
- [ ] Restreindre `CORS` aux domaines autorisés (actuellement `allow_origins=['*']`)
- [ ] Ajouter du rate limiting (`slowapi` ou équivalent) sur les endpoints sensibles

### Robustesse
- [ ] Logger systématiquement les erreurs LLM (fallbacks actuellement silencieux)
- [ ] Externaliser la configuration MySQL host/password
- [ ] Étendre la validation Pydantic à tous les endpoints critiques
- [ ] Implémenter le worker asynchrone d'ingestion événementielle (Redis/RabbitMQ — documenté mais non livré)

### Performance
- [ ] Évaluer FAISS GPU ou Pinecone/Weaviate pour la mise à l'échelle du RAG
- [ ] Ajouter un cache Redis sur les lectures fréquentes (contrats, clients)
- [ ] Mettre en cache ou générer de façon asynchrone les rapports PDF volumineux

### Code & Maintenabilité
- [ ] Découper `main_api.py` (1159 lignes) en routers FastAPI (`APIRouter`)
- [ ] Remplacer les `print()` par un logging structuré
- [ ] Ajouter des type hints complets sur les tools
- [ ] Évaluer `aiomysql` pour un accès base de données asynchrone

### Données
- [ ] Configurer un backup MySQL automatisé quotidien
- [ ] Purger les fallbacks JSON du dossier `data/` en production
- [ ] Ajouter un système de migrations versionnées (Alembic)

---

## 📌 Résumé

**Le Contrat Vivant** est une application full-stack mature combinant :
- une **architecture multi-agents** moderne (LangGraph)
- un **moteur de risque hybride** (règles déterministes + LLM)
- une **stack technique solide** (FastAPI, React 19, MySQL, FAISS, Docker)
- des **fonctionnalités avancées** (RAG, OCR, SSO Google, notifications multicanales, monitoring)

Le projet dispose d'une base de tests unitaires couvrant les cas métier critiques et d'une infrastructure Docker prête pour le déploiement.

---

## 📄 Licence

Projet interne — usage restreint.
