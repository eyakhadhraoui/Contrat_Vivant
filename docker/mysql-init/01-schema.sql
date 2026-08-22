-- Schema d'initialisation pour la base de donnees assurance_db

CREATE DATABASE IF NOT EXISTS assurance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE assurance_db;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS agences (
    id VARCHAR(10) PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    ville VARCHAR(100),
    adresse VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gestionnaires (
    id VARCHAR(10) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('assurances', 'sinistres') NOT NULL,
    agence_id VARCHAR(10),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agence_id) REFERENCES agences(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS clients (
    id VARCHAR(10) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    cin VARCHAR(20) DEFAULT NULL,
    email VARCHAR(150),
    telephone VARCHAR(20),
    adresse VARCHAR(255),
    date_naissance DATE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contrats (
    id VARCHAR(20) PRIMARY KEY,
    numero_souscripteur VARCHAR(50) DEFAULT NULL,
    client_id VARCHAR(10) NOT NULL,
    type_contrat ENUM('auto', 'habitation', 'vie', 'sante') DEFAULT 'auto',
    garantie_max DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    franchise DECIMAL(15,2) DEFAULT NULL,
    prime_mensuelle DECIMAL(15,2) DEFAULT NULL,
    prime_annuelle DECIMAL(15,2) DEFAULT NULL,
    duree_mois INT DEFAULT 12,
    date_debut DATE,
    date_fin DATE,
    statut ENUM('actif', 'suspendu', 'resilie') DEFAULT 'actif',
    mode_paiement VARCHAR(50) DEFAULT NULL,
    frequence_paiement VARCHAR(50) DEFAULT NULL,
    couverture TEXT DEFAULT NULL,
    exclusions TEXT DEFAULT NULL,
    observations TEXT DEFAULT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_derniere_modif DATE,
    gestionnaire_createur_id VARCHAR(10),
    agence_id VARCHAR(10),
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (gestionnaire_createur_id) REFERENCES gestionnaires(id),
    FOREIGN KEY (agence_id) REFERENCES agences(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sinistres (
    id VARCHAR(20) PRIMARY KEY,
    contrat_id VARCHAR(20) NOT NULL,
    type_sinistre VARCHAR(100) NOT NULL,
    lieu_sinistre VARCHAR(255) DEFAULT NULL,
    montant_declare DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    date_sinistre DATE DEFAULT NULL,
    date_declaration DATE NOT NULL,
    date_reglement DATE DEFAULT NULL,
    responsabilite VARCHAR(50) DEFAULT 'indetermine',
    statut ENUM('en_cours', 'en_traitement', 'complete', 'rejete') DEFAULT 'en_cours',
    description TEXT DEFAULT NULL,
    observations TEXT DEFAULT NULL,
    gestionnaire_traitant_id VARCHAR(10),
    agence_id VARCHAR(10),
    FOREIGN KEY (contrat_id) REFERENCES contrats(id),
    FOREIGN KEY (gestionnaire_traitant_id) REFERENCES gestionnaires(id),
    FOREIGN KEY (agence_id) REFERENCES agences(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS historique (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contrat_id VARCHAR(20),
    alert JSON,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'en_attente',
    validation_status VARCHAR(50) DEFAULT 'en_attente',
    validation_par VARCHAR(100) DEFAULT NULL,
    date_validation DATETIME DEFAULT NULL,
    gestionnaire_id VARCHAR(10) DEFAULT NULL,
    FOREIGN KEY (contrat_id) REFERENCES contrats(id),
    FOREIGN KEY (gestionnaire_id) REFERENCES gestionnaires(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    details JSON,
    gestionnaire_id VARCHAR(10),
    agence_id VARCHAR(10),
    FOREIGN KEY (gestionnaire_id) REFERENCES gestionnaires(id),
    FOREIGN KEY (agence_id) REFERENCES agences(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
