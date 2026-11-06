-- ==============================================================================
-- BASE DE DONNÉES COMPLÈTE ASSURANCE_DB (SCHEMA + DONNÉES DE DÉMONSTRATION)
-- Plateforme d'Assurance Multi-Agents « Contrat Vivant »
-- Compatible MySQL 8.0+ / MariaDB / phpMyAdmin
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `assurance_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `assurance_db`;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. TABLE : AGENCES
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `agences`;
CREATE TABLE `agences` (
    `id` VARCHAR(10) NOT NULL,
    `nom` VARCHAR(150) NOT NULL,
    `ville` VARCHAR(100) DEFAULT NULL,
    `adresse` VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `agences` (`id`, `nom`, `ville`, `adresse`) VALUES
('AG01', 'Agence Tunis Centre', 'Tunis', 'Avenue Habib Bourguiba'),
('AG02', 'Agence Sfax', 'Sfax', 'Rue de la Republique');

-- ------------------------------------------------------------------------------
-- 2. TABLE : GESTIONNAIRES
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `gestionnaires`;
CREATE TABLE `gestionnaires` (
    `id` VARCHAR(10) NOT NULL,
    `nom` VARCHAR(100) NOT NULL,
    `prenom` VARCHAR(100) NOT NULL,
    `username` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('assurances','sinistres','admin') NOT NULL,
    `agence_id` VARCHAR(10) DEFAULT NULL,
    `date_creation` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `username` (`username`),
    KEY `agence_id` (`agence_id`),
    CONSTRAINT `gestionnaires_ibfk_1` FOREIGN KEY (`agence_id`) REFERENCES `agences` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `gestionnaires` (`id`, `nom`, `prenom`, `username`, `email`, `password_hash`, `role`, `agence_id`) VALUES
('G123', 'KHADHRAOUI', 'EYA', 'eya.khadhraoui', 'eya.khadhraoui@esprit.tn', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'sinistres', 'AG01'),
('G456', 'Khelifi', 'Sarra', 'sarra.khelifi', 'eyakhadhraoui249@gmail.com', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'assurances', 'AG01'),
('G789', 'Bouazizi', 'Karim', 'karim.bouazizi', 'karim.test@example.com', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'sinistres', 'AG02'),
('G321', 'Mansour', 'Lina', 'lina.mansour', 'lina.test@example.com', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'assurances', 'AG02');

-- ------------------------------------------------------------------------------
-- 3. TABLE : CLIENTS
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `clients`;
CREATE TABLE `clients` (
    `id` VARCHAR(20) NOT NULL,
    `nom` VARCHAR(100) NOT NULL,
    `prenom` VARCHAR(100) NOT NULL,
    `cin` VARCHAR(20) DEFAULT NULL,
    `email` VARCHAR(150) DEFAULT NULL,
    `telephone` VARCHAR(20) DEFAULT NULL,
    `adresse` VARCHAR(255) DEFAULT NULL,
    `date_naissance` DATE DEFAULT NULL,
    `date_creation` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `clients` (`id`, `nom`, `prenom`, `cin`, `email`, `telephone`, `adresse`, `date_naissance`) VALUES
('CL01', 'Ben Ayed', 'Sonia', '09876543', 'sonia.ba@mail.com', '20111111', 'Tunis Centre', '1988-04-12'),
('CL02', 'Hammami', 'Amine', '08765432', 'amine.h@mail.com', '20222222', 'Ariana Ville', '1992-09-24'),
('CL03', 'Maromi', 'Jalva', '07654321', 'jalva.m@mail.com', '20333333', 'Sfax Médina', '1985-11-03'),
('CL04', 'Trabelsi', 'Martra', '06543210', 'martra.t@mail.com', '20444444', 'La Marsa, Tunis', '1990-01-18'),
('CL05', 'Mansour', 'Karem', '05432109', 'karem.m@mail.com', '20555555', 'Sousse Ville', '1979-06-30'),
('CL06', 'Khadhraoui', 'Souheil', '14285930', 'souheil.khadhraoui@email.com', '98123456', 'Tunis Centre', '1984-07-15'),
('CL11', 'Khadhraoui', 'Souheil', '12345678', 'ayoutakoukou13@gmail.com', '+21658578910', 'Tunis Centre', '1984-07-15');

-- ------------------------------------------------------------------------------
-- 4. TABLE : CONTRATS
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS `contrats`;
CREATE TABLE `contrats` (
    `id` VARCHAR(20) NOT NULL,
    `numero_souscripteur` VARCHAR(50) DEFAULT NULL,
    `client_id` VARCHAR(20) NOT NULL,
    `type_contrat` ENUM('auto','habitation','vie','sante') DEFAULT 'auto',
    `garantie_max` DECIMAL(15,2) NOT NULL DEFAULT '0.00',
    `franchise` DECIMAL(15,2) DEFAULT '0.00',
    `prime_mensuelle` DECIMAL(15,2) DEFAULT '0.00',
    `prime_annuelle` DECIMAL(15,2) DEFAULT '0.00',
    `duree_mois` INT DEFAULT '12',
    `date_debut` DATE DEFAULT NULL,
    `date_fin` DATE DEFAULT NULL,
    `statut` ENUM('actif','suspendu','resilie') DEFAULT 'actif',
    `mode_paiement` VARCHAR(50) DEFAULT 'Virement',
    `frequence_paiement` VARCHAR(50) DEFAULT 'Mensuel',
    `couverture` TEXT,
    `exclusions` TEXT,
    `observations` TEXT,
    `date_creation` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    `date_derniere_modif` DATE DEFAULT NULL,
    `gestionnaire_createur_id` VARCHAR(10) DEFAULT NULL,
    `agence_id` VARCHAR(10) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `client_id` (`client_id`),
    KEY `gestionnaire_createur_id` (`gestionnaire_createur_id`),
    KEY `agence_id` (`agence_id`),
    CONSTRAINT `contrats_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    CONSTRAINT `contrats_ibfk_2` FOREIGN KEY (`gestionnaire_createur_id`) REFERENCES `gestionnaires` (`id`) ON DELETE SET NULL,
    CONSTRAINT `contrats_ibfk_3` FOREIGN KEY (`agence_id`) REFERENCES `agences` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `contrats` (`id`, `numero_souscripteur`, `client_id`, `type_contrat`, `garantie_max`, `franchise`, `prime_mensuelle`, `prime_annuelle`, `duree_mois`, `date_debut`, `date_fin`, `statut`, `mode_paiement`, `frequence_paiement`, `couverture`, `exclusions`, `observations`, `gestionnaire_createur_id`, `agence_id`) VALUES
('CSTR00001', 'CTR-2024-001', 'CL01', 'auto', 150000.00, 500.00, 150.00, 1800.00, 12, '2024-01-01', '2027-01-01', 'actif', 'Prelevement', 'Mensuel', 'Tous risques', 'Usure normale', '', 'G456', 'AG01'),
('CSTR00002', 'CTR-2024-002', 'CL02', 'habitation', 120000.00, 300.00, 95.00, 1140.00, 12, '2024-02-10', '2027-02-10', 'actif', 'Prelevement', 'Mensuel', 'Multirisque', 'Faute intentionnelle', '', 'G456', 'AG01'),
('CSTR00003', 'CTR-2024-003', 'CL03', 'auto', 80000.00, 600.00, 110.00, 1320.00, 12, '2024-01-01', '2026-01-01', 'suspendu', 'Virement', 'Mensuel', 'Tiers étendu', 'Alcoolemie', '', 'G456', 'AG01'),
('CSTR00004', 'CTR-2023-004', 'CL04', 'auto', 200000.00, 750.00, 220.00, 2640.00, 12, '2023-12-20', '2026-12-20', 'actif', 'Prelevement', 'Annuel', 'Tous risques VIP', 'Usure', '', 'G321', 'AG02'),
('CSTR00005', 'CTR-2023-005', 'CL05', 'habitation', 50000.00, 250.00, 60.00, 720.00, 12, '2023-11-05', '2025-11-05', 'resilie', 'Cheque', 'Annuel', 'Basique', 'Inondation majeure', '', 'G321', 'AG02'),
('CSTR78199', 'CTR-2024-78199', 'CL11', 'auto', 100000.00, 500.00, 120.00, 1440.00, 12, '2026-08-09', '2027-08-09', 'suspendu', 'Virement', 'Mensuel', 'Tous risques', 'Usure normale', '', 'G456', 'AG01');

-- --------------------------------------------------------
-- 5. TABLE : SINISTRES
-- --------------------------------------------------------
DROP TABLE IF EXISTS `sinistres`;
CREATE TABLE `sinistres` (
    `id` VARCHAR(20) NOT NULL,
    `contrat_id` VARCHAR(20) NOT NULL,
    `type_sinistre` VARCHAR(100) NOT NULL,
    `lieu_sinistre` VARCHAR(255) DEFAULT NULL,
    `montant_declare` DECIMAL(15,2) NOT NULL DEFAULT '0.00',
    `date_sinistre` DATE DEFAULT NULL,
    `date_declaration` DATE NOT NULL,
    `date_reglement` DATE DEFAULT NULL,
    `responsabilite` VARCHAR(50) DEFAULT 'indetermine',
    `statut` ENUM('en_cours','en_traitement','complete','rejete') DEFAULT 'en_cours',
    `description` TEXT,
    `observations` TEXT,
    `gestionnaire_traitant_id` VARCHAR(10) DEFAULT NULL,
    `agence_id` VARCHAR(10) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `contrat_id` (`contrat_id`),
    KEY `gestionnaire_traitant_id` (`gestionnaire_traitant_id`),
    KEY `agence_id` (`agence_id`),
    CONSTRAINT `sinistres_ibfk_1` FOREIGN KEY (`contrat_id`) REFERENCES `contrats` (`id`) ON DELETE CASCADE,
    CONSTRAINT `sinistres_ibfk_2` FOREIGN KEY (`gestionnaire_traitant_id`) REFERENCES `gestionnaires` (`id`) ON DELETE SET NULL,
    CONSTRAINT `sinistres_ibfk_3` FOREIGN KEY (`agence_id`) REFERENCES `agences` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `sinistres` (`id`, `contrat_id`, `type_sinistre`, `lieu_sinistre`, `montant_declare`, `date_sinistre`, `date_declaration`, `statut`, `gestionnaire_traitant_id`, `agence_id`) VALUES
('CSIN00001', 'CSTR00001', 'Auto - Carambolage', 'Route de la Marsa, Tunis', 12000.00, '2024-03-28', '2024-03-31', 'en_cours', 'G123', 'AG01'),
('CSIN00002', 'CSTR00002', 'Habitation - Inondation', 'Ariana', 10000.00, '2024-03-20', '2024-03-21', 'en_traitement', 'G123', 'AG01'),
('CSIN00003', 'CSTR00003', 'Auto - Carambolage', 'Sfax', 3500.00, '2024-03-21', '2024-03-22', 'rejete', 'G789', 'AG02'),
('CSIN00004', 'CSTR00002', 'Habitation - Cambriolage', 'Ariana', 3000.00, '2024-03-20', '2024-03-22', 'en_cours', 'G123', 'AG01'),
('CSIN00005', 'CSTR00001', 'Auto - Carambolage', 'Avenue Habib Bourguiba, Tunis', 10000.00, '2024-03-19', '2024-03-21', 'en_cours', 'G123', 'AG01'),
('CSIN00006', 'CSTR00004', 'Auto - Carambolage', 'Sfax', 1400.00, '2024-01-30', '2024-02-02', 'complete', 'G789', 'AG02'),
('CSIN55979', 'CSTR78199', 'Auto - Carambolage', 'Tunis Centre', 1500.00, '2026-08-19', '2026-08-19', 'en_cours', 'G123', 'AG01'),
('CSIN78199', 'CSTR78199', 'Auto - Carambolage', 'Tunis', 1500.00, '2024-03-10', '2024-03-12', 'en_cours', 'G123', 'AG01');

-- --------------------------------------------------------
-- 6. TABLE : HISTORIQUE (HITL)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `historique`;
CREATE TABLE `historique` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `contrat_id` VARCHAR(20) DEFAULT NULL,
    `alert` JSON DEFAULT NULL,
    `validation_status` VARCHAR(50) DEFAULT 'en_attente',
    `valide_par_gestionnaire_id` VARCHAR(10) DEFAULT NULL,
    `date_validation` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `contrat_id` (`contrat_id`),
    KEY `valide_par_gestionnaire_id` (`valide_par_gestionnaire_id`),
    CONSTRAINT `historique_ibfk_1` FOREIGN KEY (`contrat_id`) REFERENCES `contrats` (`id`) ON DELETE CASCADE,
    CONSTRAINT `historique_ibfk_2` FOREIGN KEY (`valide_par_gestionnaire_id`) REFERENCES `gestionnaires` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `historique` (`id`, `contrat_id`, `alert`, `validation_status`, `valide_par_gestionnaire_id`, `date_validation`) VALUES
(9, 'CSTR78199', '{"type": "nouveau_sinistre", "message": "Nouveau sinistre CSIN55979 déclaré sur le contrat CSTR78199 (Montant: 1500.0 DT)", "timestamp": "2026-08-19", "contrat_id": "CSTR78199", "sinistre_id": "CSIN55979", "gestionnaire_source_id": "G123"}', 'en_attente', 'G123', '2026-08-19 08:17:23');

-- --------------------------------------------------------
-- 7. TABLE : JOURNAL D'AUDIT (AUDIT_LOG)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `audit_log`;
CREATE TABLE `audit_log` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `step` VARCHAR(100) DEFAULT NULL,
    `data` JSON DEFAULT NULL,
    `gestionnaire_id` VARCHAR(10) DEFAULT NULL,
    `timestamp` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `audit_log` (`step`, `data`, `gestionnaire_id`, `timestamp`) VALUES
('system_init', '{"action": "Initialisation du schéma de données complet de la plateforme Contrat Vivant"}', 'G456', NOW()),
('contrat_created', '{"action": "Création du contrat Auto pour Souheil Khadhraoui avec garantie 100,000 DT"}', 'G456', NOW()),
('sinistre_declared', '{"action": "Déclaration sinistre Auto 1,500 DT avec notification croisée"}', 'G123', NOW());

-- --------------------------------------------------------
-- 8. TABLE : RAG DOCUMENTS
-- --------------------------------------------------------
DROP TABLE IF EXISTS `rag_documents`;
CREATE TABLE `rag_documents` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `filename` VARCHAR(255) NOT NULL,
    `file_type` VARCHAR(50) DEFAULT 'pdf',
    `file_size` INT DEFAULT '0',
    `chunks_count` INT DEFAULT '0',
    `content_text` LONGTEXT,
    `uploaded_by` VARCHAR(50) DEFAULT 'system',
    `uploaded_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 9. TABLE : CHAT MESSAGES
-- --------------------------------------------------------
DROP TABLE IF EXISTS `chat_messages`;
CREATE TABLE `chat_messages` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `session_id` VARCHAR(100) DEFAULT 'default',
    `gestionnaire_id` VARCHAR(50) NOT NULL,
    `sender` ENUM('user','bot') NOT NULL,
    `message` LONGTEXT NOT NULL,
    `sources` JSON DEFAULT NULL,
    `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 10. TABLE : REVERTS (ROLLBACK HITL)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `reverts`;
CREATE TABLE `reverts` (
    `id` VARCHAR(64) NOT NULL,
    `kind` VARCHAR(32) NOT NULL,
    `target_id` VARCHAR(64) NOT NULL,
    `previous_data` JSON NOT NULL,
    `actor` VARCHAR(64) DEFAULT NULL,
    `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- Fin du script SQL
