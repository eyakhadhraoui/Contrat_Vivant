# RAPPORT D'ANALYSE COMPLET — PROJET « LE CONTRAT VIVANT »

## 1. IDENTIFICATION GÉNÉRALE

| Élément | Valeur |
|---|---|
| **Nom du projet** | Le Contrat Vivant — Contrat Vivant API |
| **Domaine** | Assurance / Gestion de contrats et sinistres |
| **Langage principal** | Python 3.12 + JavaScript (React) |
| **Type** | Application web full-stack avec système multi-agents IA |
| **Localisation** | `C:\Users\eyakh\agent-assurance` |
| **Contexte** | Plateforme interne de gestion d'assurances avec analyse de risque automatisée, assistant RAG, OCR et notifications multicanales |

---

## 2. OBJECTIF MÉTIER

Le projet vise à digitaliser et automatiser le cycle de vie des contrats d'assurance :
- **Gestion des contrats** (création, modification, suppression, avenants)
- **Gestion des sinistres** (déclaration, traitement, analyse)
- **Analyse de risque intelligente** (moteur de règles déterministe + LLM)
- **Détection de fraude** (scoring 0-100, anomalies, patterns suspects)
- **Notifications multicomptes** (Email, Teams, in-app)
- **Assistant IA contextuel** (RAG sur procédures assurance, chat avec historique persistant)
- **OCR et extraction** (CIN, Constat Amiable, analyse de devis garage)
- **Traçabilité complète** (audit log, historique, rollback, export PDF/CSV)

---

## 3. ARCHITECTURE GLOBALE

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
│         │                │                                        │
│  ┌──────▼────────────────▼─────────────────────────────────────┐│
│  │              LANGGRAPH WORKFLOW (Multi-Agents)                ││
│  │  CollectorAgent → RiskAgent → AlertAgent → HITL → History    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          │                                        │
│  ┌───────────────────────▼─────────────────────────────────────┐│
│  │  COUCHES MÉTIER                                             ││
│  │  • rules_engine (score 0-100, anomalies déterministes)      ││
│  │  • llm (Gemini + fallback Ollama local)                     ││
│  │  • rag (FAISS + sentence-transformers + MySQL)              ││
│  │  • tools (contrats, sinistres, auth, notifications, OCR)    ││
│  └───────────────────────┬─────────────────────────────────────┘│
│                          │                                        │
│  ┌───────────────────────▼─────────────────────────────────────┐│
│  │              BASE DE DONNÉES MySQL 8.0                       ││
│  │  agences, gestionnaires, clients, contrats, sinistres,      ││
│  │  historique, audit_log, rag_documents, chat_messages        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼─────┐ ┌───▼────┐ ┌───▼─────┐
              │ Prometheus │ │ Teams  │ │  SMTP   │
              │ (monitoring│ │ Webhook│ │  Email  │
              │  port 9090)│ └────────┘ └─────────┘
              └───────────┘
```

---

## 4. STACK TECHNIQUE DÉTAILLÉE

### 4.1 Backend
| Composant | Version / Outil | Rôle |
|---|---|---|
| Framework | FastAPI >= 0.100.0 | API REST, CORS, static files |
| Orchestration IA | LangGraph >= 0.0.20 | Workflow multi-agents |
| LLM | Google GenAI (Gemini) + Ollama (local) | Analyse LLM, synthèse, chat |
| RAG | FAISS CPU + Sentence-Transformers + PyPDF | Ingestion et recherche procédures |
| Base de données | MySQL 8.0 (mysql-connector-python) | Persistance principale |
| Auth | PyJWT + bcrypt | Authentification Bearer JWT |
| OCR | pytesseract + Pillow | Extraction CIN et constats |
| PDF | ReportLab | Génération attestations, avenants, rapports |
| Monitoring | prometheus-fastapi-instrumentator | Métriques /metrics |

### 4.2 Frontend
| Composant | Version | Rôle |
|---|---|---|
| Framework | React 19.2.8 | SPA |
| Build | Vite 8.2.0 | Dev server + bundling |
| Cartographie | React-Leaflet 5.0.0 | Visualisation géographique |
| Linting | Oxlint 1.75.0 | Qualité code |

### 4.3 Infrastructure
| Composant | Version | Rôle |
|---|---|---|
| Conteneurisation | Docker + Docker Compose | MySQL, Backend, Frontend, Prometheus |
| Base de données | MySQL 8.0 (port 3307 host) | Container `assurance-mysql` |
| Monitoring | Prometheus 2.47.0 | Métriques applicatives |

---

## 5. MODÈLE DE DONNÉES (SCHEMA MySQL)

### Tables principales

| Table | Clé primaire | Champs principaux | Relations |
|---|---|---|---|
| `agences` | `id` (VARCHAR 10) | nom, ville, adresse | 1→N gestionnaires, contrats, sinistres |
| `gestionnaires` | `id` (VARCHAR 10) | nom, prenom, username, email, password_hash, role (`assurances`/`sinistres`), agence_id | N→1 agences |
| `clients` | `id` (VARCHAR 10) | nom, prenom, cin, email, telephone, adresse, date_naissance | 1→N contrats |
| `contrats` | `id` (VARCHAR 20) | client_id, type_contrat (auto/habitation/vie/sante), garantie_max, prime_mensuelle, franchise, date_debut, date_fin, statut (actif/suspendu/resilie), couverture, exclusions, observations, gestionnaire_createur_id, agence_id | N→1 clients, gestionnaires, agences ; 1→N sinistres |
| `sinistres` | `id` (VARCHAR 20) | contrat_id, type_sinistre, montant_declare, date_sinistre, date_declaration, responsabilite, statut (en_cours/en_traitement/complete/rejete), gestionnaire_traitant_id, agence_id | N→1 contrats, gestionnaires, agences |
| `historique` | `id` (AUTO) | contrat_id, alert (JSON), validation_status, valide_par_gestionnaire_id | N→1 contrats, gestionnaires |
| `audit_log` | `id` (AUTO) | step, data (JSON), gestionnaire_id, timestamp | Traçabilité universelle |
| `rag_documents` | `id` (AUTO) | filename, file_type, file_size, chunks_count, content_text, uploaded_by | Documents persistants RAG |
| `chat_messages` | `id` (AUTO) | session_id, gestionnaire_id, sender (user/bot), message, sources (JSON) | Historique chat persistant |

### Règles d'intégrité métier
- **Unicité contrat** : Un client ne peut avoir qu'un seul contrat actif/suspendu par type (`auto`, `habitation`, `vie`, `sante`)
- **Contrôle de statut** : Impossible d'ajouter un sinistre si le contrat est `suspendu` ou `resilie`
- **Contrôle de type** : Le type de sinistre doit correspondre au type de contrat (ex: sinistre Auto sur contrat Auto)

---

## 6. SYSTÈME MULTI-AGENTS (LANGGRAPH)

### 6.1 Workflow principal
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
   └─ Validation/Ajustement/Rejet par le gestionnaire
   │
   ▼
[5] History Update
   └─ Mise à jour historique SI si validé
   │
   ▼
Sortie : état complet du workflow
```

### 6.2 Agents spécialisés

| Agent | Rôle | Points d'entrée (nodes) |
|---|---|---|
| `CollectorAgent` | Collecte et intégration SI | `auth_node`, `collect_node` |
| `RiskAnalysisAgent` | Évaluation risques, détection anomalies | `cross_analysis_node`, `classify_node`, `urgency_node` |
| `AlertNotificationAgent` | Synthèse, alertes, notifications | `summarizer_node`, `alert_node`, `recommendation_node`, `routing_node`, `cross_notification_node` |
| `SupervisorAgent` | Orchestration, coordination HITL | `human_validation_node`, `history_update_node` |

---

## 7. MOTEUR DE RÈGLES (RISK_ANALYZER)

### 7.1 Facteurs de risque (poids configurables)

| Facteur | Poids | Description |
|---|---|---|
| `recurrence` | 20% | Nombre de sinistres, mêmes causes |
| `delai` | 20% | Écart temporel entre sinistres (< 180j rapproché, < 730j intermédiaire) |
| `montant_plafond` | 25% | Montant cumulé vs garantie_max, détection outlier |
| `anciennete` | 15% | Délai souscription → premier sinistre (< 90j = fraude potentielle) |
| `pattern_suspect` | 20% | Circonstances similaires, sinistre post-avenant, fréquence élevée |

### 7.2 Niveaux d'urgence (seuils configurables)

| Niveau | Score | Action recommandée |
|---|---|---|
| `critique` | >= 81 | Escalade anti-fraude + évaluation résiliation |
| `eleve` | 61-80 | Escalade anti-fraude + contrôle renforcé |
| `moyen` | 31-60 | Révision contractuelle (franchise, surprime) |
| `faible` | 0-30 | Surveillance, revue à 90 jours |

### 7.3 Règles déterministes
- `ecart_garantie_montant` : écart > 40% entre montant déclaré et plafond
- `sinistres_repetes` : 2+ sinistres en 30 jours
- `retard_paiement` : retard > 15 jours (configurable)

---

## 8. OUTILS MÉTIER (TOOLS)

| Module | Fonctionnalités |
|---|---|
| `si_contrats_tool.py` | CRUD contrats MySQL, unicité par type, notifications croisées |
| `si_sinistres_tool.py` | CRUD sinistres, validation statut contrat, notifications assurances |
| `si_delete_tool.py` | Suppression contrats/sinistres avec droits |
| `si_agences_clients_tool.py` | Gestion agences/clients, alertes in-app, historique |
| `auth_tool.py` | Login, création gestionnaire, Google SSO, JWT |
| `auth_context.py` | Résolution contexte gestionnaire depuis token |
| `audit_log_tool.py` | Logs structurés JSON, export CSV |
| `revert_tool.py` | Sauvegarde/rollback modifications contrats/sinistres |
| `pdf_generator_tool.py` | Attestation contrat, rapport sinistre, rapport audit, avenant |
| `cin_ocr_tool.py` | Extraction OCR CIN (pytesseract) |
| `constat_ocr_tool.py` | Extraction constat amiable |
| `devis_analyzer_tool.py` | Analyse devis garage, détection surfacturation |
| `cross_notification_tool.py` | Notification croisée assurances/sinistres |
| `notification_tool.py` | Envoi Email (SMTP) + Teams (webhook) |
| `chat_history_tool.py` | Historique chat persistant MySQL |
| `permissions_tool.py` | Vérification droits par rôle et agence |
| `analysis_helpers.py` | Helpers analyse croisée |

---

## 9. FONCTIONNALITÉS LLM / IA

### 9.1 Modèles utilisés
- **Gemini** (Google GenAI) : modèles Flash/Flash-Lite avec fallback automatique
- **Ollama** (local) : fallback gratuit si API cloud indisponible (`llama3.2`, `mistral`)
- **Priorité** : Ollama local → Gemini API → fallback déterministe

### 9.2 Cas d'usage LLM
| Cas d'usage | Fichier | Description |
|---|---|---|
| Analyse cross | `cross_analysis_prompt.py` | Anomalies complémentaires aux règles fixes |
| Synthèse dossier | `summarize_dossier.py` | Résumé professionnel du dossier |
| Notes vocales | `main_api.py` (endpoint notes) | Structuration Markdown des dictées |
| Chat RAG | `chat_node.py` | Assistant contextuel sur procédures |
| Avenant certifié | `main_api.py` | Génération contenu avenant |

### 9.3 RAG (Retrieval-Augmented Generation)
- **Vector store** : FAISS CPU
- **Embeddings** : Sentence-Transformers
- **Documents persistants** : MySQL (`rag_documents`) + indexation vectorielle
- **Ingestion** : PDF, TXT, JSON, DOCX via `/api/rag/ingest`
- **Recherche** : `/api/rag/search` avec sources citées

---

## 10. FRONTEND (REACT 19)

### 10.1 Structure
```
frontend/src/
├── App.jsx                    # Routing onglets + AuthProvider
├── context/
│   └── AuthContext.jsx         # Contexte auth (JWT localStorage)
├── components/
│   ├── Sidebar.jsx             # Navigation latérale
│   ├── ChatAssistant.jsx       # Chat IA flottant
│   └── ...
├── pages/
│   ├── LoginPage.jsx           # Connexion + Google SSO
│   ├── SignupPage.jsx          # Inscription
│   ├── AnalyseDossierView.jsx  # Vue analyse IA principale
│   ├── ContratsView.jsx        # Gestion contrats
│   ├── SinistresView.jsx       # Gestion sinistres
│   ├── ClientsView.jsx         # Gestion clients + OCR CIN
│   ├── HistoriqueView.jsx      # Audit log + exports
│   └── MapView.jsx             # Cartographie Leaflet
└── services/
    └── api.js                  # Clients API centralisés
```

### 10.2 Vues principales
| Vue | Rôle |
|---|---|
| **AnalyseDossierView** | Workflow IA complet, score risque, anomalies, recommandations, validation HITL |
| **ContratsView** | CRUD contrats, génération PDF, avenants |
| **SinistresView** | CRUD sinistres, OCR constat, analyse devis |
| **ClientsView** | CRUD clients, extraction OCR CIN |
| **HistoriqueView** | Audit log, export PDF/CSV, alertes validées |
| **MapView** | Visualisation géographique Leaflet |
| **ChatAssistant** | Assistant IA RAG flottant |

---

## 11. API REST (ENDPOINTS PRINCIPAUX)

| Méthode | Endpoint | Rôle |
|---|---|---|
| POST | `/api/login` | Authentification JWT |
| POST | `/api/auth/google` | SSO Google |
| POST | `/api/signup` | Inscription gestionnaire |
| GET | `/api/contrats` | Liste contrats par agence |
| POST | `/api/contrats` | Création contrat |
| PUT | `/api/contrats/{id}` | Modification contrat |
| DELETE | `/api/contrats/{id}` | Suppression contrat |
| POST | `/api/contrats/{id}/notes` | Note vocale structurée par LLM |
| GET | `/api/sinistres` | Liste sinistres par agence |
| POST | `/api/sinistres` | Création sinistre |
| PUT | `/api/sinistres/{id}` | Modification sinistre |
| DELETE | `/api/sinistres/{id}` | Suppression sinistre |
| POST | `/api/analyser` | Lancement workflow IA complet |
| POST | `/api/alerts/validate` | Validation/Ajustement/Rejet alerte |
| POST | `/api/alerts/rollback` | Rollback modification |
| POST | `/api/cin/extract` | OCR CIN |
| POST | `/api/ocr/constat` | Extraction constat amiable |
| POST | `/api/devis/analyser` | Analyse devis garage |
| GET | `/api/pdf/contrat/{id}` | PDF attestation |
| GET | `/api/pdf/sinistre/{id}` | PDF rapport sinistre |
| GET | `/api/pdf/avenant/{id}` | PDF avenant |
| GET | `/api/pdf/audit` | PDF rapport audit |
| GET | `/api/audit/csv` | Export CSV audit |
| GET | `/api/rag/documents` | Liste documents RAG |
| POST | `/api/rag/ingest` | Ingestion document RAG |
| DELETE | `/api/rag/documents/{id}` | Suppression document RAG |
| POST | `/api/chat` | Message chat IA |
| GET | `/api/chat/history` | Historique chat |
| DELETE | `/api/chat/history` | Effacer historique chat |
| GET | `/api/agences` | Liste agences |
| GET | `/api/clients` | Liste clients |
| POST | `/api/clients` | Création client |
| GET | `/api/alerts` | Alertes in-app |
| GET | `/metrics` | Métriques Prometheus |

---

## 12. TESTS

### 12.1 Couverture existante
| Fichier | Nature | Couverture |
|---|---|---|
| `tests/test_business_rules.py` | Unitaires + intégration | Permissions, règles métier, notifications croisées, CRUD |
| `tests/test_multi_agent.py` | Unitaires + intégration | Agents individuels, SupervisorAgent, workflow LangGraph complet |

### 12.2 Points testés
- Permissions par rôle (`assurances`/`sinistres`) et par agence
- Règles déterministes (`ecart_garantie_montant`, `sinistres_repetes`)
- Notifications croisées (Email + Teams simulés)
- Unicité contrat par type par client
- Blocage sinistre sur contrat suspendu/résilié
- Normalisation IDs contrat (C001 → CSTR00001)
- Exécution complète du workflow LangGraph avec mocks

### 12.3 Tests manuels / scripts
- `test_login.py`, `test_engine.py`, `test_email.py`, `test_chat.py`
- `test_rag_debug.py`, `test_mysql.py`

---

## 13. INFRASTRUCTURE & DÉPLOIEMENT

### 13.1 Docker Compose
| Service | Image | Ports | Rôle |
|---|---|---|---|
| `db` | mysql:8.0 | 3307→3306 | Base de données |
| `backend` | Build local | 8000 | API FastAPI |
| `frontend` | Build local (frontend/) | 80 | Nginx SPA |
| `prometheus` | prom/prometheus:v2.47.0 | 9090 | Monitoring |

### 13.2 Variables d'environnement critiques
- `MYSQL_*` : Connexion base de données
- `GOOGLE_API_KEY` : LLM Gemini
- `OPENAI_API_KEY` : Alternative LLM
- `TAVILY_API_KEY` : Recherche web (agent tools)
- `JWT_SECRET_KEY` : Signature tokens
- `EMAIL_SENDER` / `EMAIL_PASSWORD` : SMTP
- `TEAMS_WEBHOOK_URL` : Notifications Teams
- `AUTO_APPLY_LOW_RISK` : Application automatique modifications bas risque

---

## 14. POINTS FORTS DU PROJET

1. **Architecture multi-agents robuste** : Orchestration claire avec LangGraph, séparation des responsabilités
2. **Double analyse** : Règles déterministes + LLM complémentaire (résilience aux pannes LLM)
3. **Traçabilité complète** : Audit log, historique, rollback, export PDF/CSV
4. **Sécurité** : JWT, bcrypt, rôles par agence, CORS configuré
5. **RAG persistant** : Documents indexés dans MySQL + FAISS, interrogeables durablement
6. **OCR intégré** : Extraction CIN, constat amiable, analyse devis
7. **Notifications multicomptes** : Email, Teams, in-app avec routage intelligent
8. **Frontend moderne** : React 19, Vite, Leaflet, UX soignée
9. **Monitoring** : Prometheus embarqué
10. **Tests unitaires** : Couverture agents, règles, permissions, workflow

---

## 15. POINTS D'ATTENTION & RECOMMANDATIONS

### 15.1 Sécurité
| Risque | Recommandation |
|---|---|
| `JWT_SECRET_KEY` en dev par défaut | Forcer la rotation en production |
| CORS `allow_origins=['*']` | Restreindre aux domaines autorisés en production |
| Pas de rate limiting | Ajouter `slowapi` ou équivalent sur endpoints sensibles |
| Passwords stockées en bcrypt (OK) | Vérifier politique de rotation |

### 15.2 Robustesse
| Risque | Recommandation |
|---|---|
| Fallbacks silencieux LLM | Logger systématiquement les erreurs LLM pour debugging |
| Connexion MySQL par tentative multiples | Externaliser la configuration host/password |
| Pas de validation Pydantic sur tous les inputs | Étendre les `BaseModel` aux endpoints critiques |
| Pas de gestion de queue Redis/RabbitMQ (docs présentes mais absentes) | Implémenter le worker asynchrone pour ingestion événements |

### 15.3 Performance
| Risque | Recommandation |
|---|---|
| FAISS CPU sur documents volumineux | Évaluer FAISS GPU ou Pinecone/Weaviate pour scale |
| Pas de cache Redis | Ajouter cache sur lectures fréquentes (contrats, clients) |
| PDF généré à la volée | Ajouter cache ou stockage asynchrone pour rapports volumineux |

### 15.4 Code & Maintenabilité
| Risque | Recommandation |
|---|---|
| `main_api.py` fait 1159 lignes | Découper en routers FastAPI (`APIRouter`) |
| Logs via `print()` dans agents | Remplacer par `logging` structuré |
| Pas de typage complet sur tools | Ajouter type hints et validation Pydantic |
| Dépendance à `mysql.connector` (synchrone) | Évaluer `aiomysql` pour async |

### 15.5 Données
| Risque | Recommandation |
|---|---|
| Pas de backup automatisé visible | Configurer backup MySQL quotidien |
| `data/` utilisé comme fallback JSON | Purger les fallbacks JSON en production (garder MySQL seul) |
| Pas de migration Alembic/Django | Ajouter système de migrations versionnées |

---

## 16. CONCLUSION

Le projet **Le Contrat Vivant** est une application full-stack mature et bien architecturée pour la gestion d'assurances. Il combine :
- Une **architecture multi-agents** moderne (LangGraph)
- Un **moteur de risque hybride** (règles déterministes + LLM)
- Une **stack technique solide** (FastAPI, React 19, MySQL, FAISS, Docker)
- Des **fonctionnalités avancées** (RAG, OCR, SSO Google, notifications multicomptes, monitoring)

Les **points d'attention** concernent principalement la sécurisation en production, la découpe du monolithe `main_api.py`, et l'implémentation du worker asynchrone d'ingestion événementielle décrit dans la spec mais pas encore livré. Le projet dispose d'une base de tests unitaires couvrant les cas métier critiques et d'une infrastructure Docker prête pour le déploiement.
