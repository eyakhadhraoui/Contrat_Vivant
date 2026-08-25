# 🏢 Le Contrat Vivant — Contrat Vivant API

**Plateforme intelligente de gestion d'assurances** combinant analyse de risque automatisée, système multi-agents IA, RAG contextuel, OCR et notifications multicanales.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-19.2.8-61DAFB?logo=react)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agents-purple)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![License](https://img.shields.io/badge/license-Interne-lightgrey)


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
