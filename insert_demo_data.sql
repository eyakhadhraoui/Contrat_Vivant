-- ==============================================================================
-- SCRIPT D'INSERTION DES NOUVELLES DONNÉES DANS ASSURANCE_DB
-- Compatible phpMyAdmin / MySQL Workbench / Docker
-- ==============================================================================

USE `assurance_db`;

SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. INSERTION DES AGENCES
-- ------------------------------------------------------------------------------
INSERT INTO `agences` (`id`, `nom`, `ville`, `adresse`) VALUES
('AG01', 'Agence Tunis Centre', 'Tunis', 'Avenue Habib Bourguiba'),
('AG02', 'Agence Sfax', 'Sfax', 'Rue de la Republique')
ON DUPLICATE KEY UPDATE `nom`=VALUES(`nom`), `ville`=VALUES(`ville`), `adresse`=VALUES(`adresse`);

-- ------------------------------------------------------------------------------
-- 2. INSERTION DES GESTIONNAIRES (Mot de passe : password123)
-- ------------------------------------------------------------------------------
INSERT INTO `gestionnaires` (`id`, `nom`, `prenom`, `username`, `email`, `password_hash`, `role`, `agence_id`) VALUES
('G123', 'KHADHRAOUI', 'EYA', 'eya.khadhraoui', 'eya.khadhraoui@esprit.tn', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'sinistres', 'AG01'),
('G456', 'Khelifi', 'Sarra', 'sarra.khelifi', 'eyakhadhraoui249@gmail.com', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'assurances', 'AG01'),
('G789', 'Bouazizi', 'Karim', 'karim.bouazizi', 'karim.test@example.com', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'sinistres', 'AG02'),
('G321', 'Mansour', 'Lina', 'lina.mansour', 'lina.test@example.com', '$2b$12$v7C/x8..RlwF7/zg8eEpYuXf8uAGloro343YTpdXX5p84zaMjZLcy', 'assurances', 'AG02')
ON DUPLICATE KEY UPDATE `email`=VALUES(`email`), `role`=VALUES(`role`), `agence_id`=VALUES(`agence_id`);

-- ------------------------------------------------------------------------------
-- 3. INSERTION DES CLIENTS
-- ------------------------------------------------------------------------------
INSERT INTO `clients` (`id`, `nom`, `prenom`, `cin`, `email`, `telephone`, `adresse`, `date_naissance`) VALUES
('CL01', 'Ben Ayed', 'Sonia', '09876543', 'sonia.ba@mail.com', '20111111', 'Tunis Centre', '1988-04-12'),
('CL02', 'Hammami', 'Amine', '08765432', 'amine.h@mail.com', '20222222', 'Ariana Ville', '1992-09-24'),
('CL03', 'Maromi', 'Jalva', '07654321', 'jalva.m@mail.com', '20333333', 'Sfax Médina', '1985-11-03'),
('CL04', 'Trabelsi', 'Martra', '06543210', 'martra.t@mail.com', '20444444', 'La Marsa, Tunis', '1990-01-18'),
('CL05', 'Mansour', 'Karem', '05432109', 'karem.m@mail.com', '20555555', 'Sousse Ville', '1979-06-30'),
('CL06', 'Khadhraoui', 'Souheil', '14285930', 'souheil.khadhraoui@email.com', '98123456', 'Tunis Centre', '1984-07-15'),
('CL11', 'Khadhraoui', 'Souheil', '12345678', 'ayoutakoukou13@gmail.com', '+21658578910', 'Tunis Centre', '1984-07-15')
ON DUPLICATE KEY UPDATE `nom`=VALUES(`nom`), `prenom`=VALUES(`prenom`), `email`=VALUES(`email`), `telephone`=VALUES(`telephone`);

-- ------------------------------------------------------------------------------
-- 4. INSERTION DES CONTRATS
-- ------------------------------------------------------------------------------
INSERT INTO `contrats` (`id`, `numero_souscripteur`, `client_id`, `type_contrat`, `garantie_max`, `franchise`, `prime_mensuelle`, `prime_annuelle`, `duree_mois`, `date_debut`, `date_fin`, `statut`, `mode_paiement`, `frequence_paiement`, `couverture`, `exclusions`, `observations`, `gestionnaire_createur_id`, `agence_id`) VALUES
('CSTR00001', 'CTR-2024-001', 'CL01', 'auto', 150000.00, 500.00, 150.00, 1800.00, 12, '2024-01-01', '2027-01-01', 'actif', 'Prelevement', 'Mensuel', 'Tous risques', 'Usure normale', '', 'G456', 'AG01'),
('CSTR00002', 'CTR-2024-002', 'CL02', 'habitation', 120000.00, 300.00, 95.00, 1140.00, 12, '2024-02-10', '2027-02-10', 'actif', 'Prelevement', 'Mensuel', 'Multirisque', 'Faute intentionnelle', '', 'G456', 'AG01'),
('CSTR00003', 'CTR-2024-003', 'CL03', 'auto', 80000.00, 600.00, 110.00, 1320.00, 12, '2024-01-01', '2026-01-01', 'suspendu', 'Virement', 'Mensuel', 'Tiers étendu', 'Alcoolemie', '', 'G456', 'AG01'),
('CSTR00004', 'CTR-2023-004', 'CL04', 'auto', 200000.00, 750.00, 220.00, 2640.00, 12, '2023-12-20', '2026-12-20', 'actif', 'Prelevement', 'Annuel', 'Tous risques VIP', 'Usure', '', 'G321', 'AG02'),
('CSTR00005', 'CTR-2023-005', 'CL05', 'habitation', 50000.00, 250.00, 60.00, 720.00, 12, '2023-11-05', '2025-11-05', 'resilie', 'Cheque', 'Annuel', 'Basique', 'Inondation majeure', '', 'G321', 'AG02'),
('CSTR78199', 'CTR-2024-78199', 'CL11', 'auto', 100000.00, 500.00, 120.00, 1440.00, 12, '2026-08-09', '2027-08-09', 'suspendu', 'Virement', 'Mensuel', 'Tous risques', 'Usure normale', '', 'G456', 'AG01')
ON DUPLICATE KEY UPDATE `garantie_max`=VALUES(`garantie_max`), `statut`=VALUES(`statut`), `franchise`=VALUES(`franchise`), `prime_mensuelle`=VALUES(`prime_mensuelle`);

-- ------------------------------------------------------------------------------
-- 5. INSERTION DES SINISTRES
-- ------------------------------------------------------------------------------
INSERT INTO `sinistres` (`id`, `contrat_id`, `type_sinistre`, `lieu_sinistre`, `montant_declare`, `date_sinistre`, `date_declaration`, `statut`, `gestionnaire_traitant_id`, `agence_id`) VALUES
('CSIN00001', 'CSTR00001', 'Auto - Carambolage', 'Route de la Marsa, Tunis', 12000.00, '2024-03-28', '2024-03-31', 'en_cours', 'G123', 'AG01'),
('CSIN00002', 'CSTR00002', 'Habitation - Inondation', 'Ariana', 10000.00, '2024-03-20', '2024-03-21', 'en_traitement', 'G123', 'AG01'),
('CSIN00003', 'CSTR00003', 'Auto - Carambolage', 'Sfax', 3500.00, '2024-03-21', '2024-03-22', 'rejete', 'G789', 'AG02'),
('CSIN00004', 'CSTR00002', 'Habitation - Cambriolage', 'Ariana', 3000.00, '2024-03-20', '2024-03-22', 'en_cours', 'G123', 'AG01'),
('CSIN00005', 'CSTR00001', 'Auto - Carambolage', 'Avenue Habib Bourguiba, Tunis', 10000.00, '2024-03-19', '2024-03-21', 'en_cours', 'G123', 'AG01'),
('CSIN00006', 'CSTR00004', 'Auto - Carambolage', 'Sfax', 1400.00, '2024-01-30', '2024-02-02', 'complete', 'G789', 'AG02'),
('CSIN55979', 'CSTR78199', 'Auto - Carambolage', 'Tunis Centre', 1500.00, '2026-08-19', '2026-08-19', 'en_cours', 'G123', 'AG01'),
('CSIN78199', 'CSTR78199', 'Auto - Carambolage', 'Tunis', 1500.00, '2024-03-10', '2024-03-12', 'en_cours', 'G123', 'AG01')
ON DUPLICATE KEY UPDATE `montant_declare`=VALUES(`montant_declare`), `statut`=VALUES(`statut`);

-- ------------------------------------------------------------------------------
-- 6. INSERTION DE L'HISTORIQUE HITL
-- ------------------------------------------------------------------------------
INSERT INTO `historique` (`id`, `contrat_id`, `alert`, `validation_status`, `valide_par_gestionnaire_id`, `date_validation`) VALUES
(9, 'CSTR78199', '{"type": "nouveau_sinistre", "message": "Nouveau sinistre CSIN55979 déclaré sur le contrat CSTR78199 (Montant: 1500.0 DT)", "timestamp": "2026-08-19", "contrat_id": "CSTR78199", "sinistre_id": "CSIN55979", "gestionnaire_source_id": "G123"}', 'en_attente', 'G123', '2026-08-19 08:17:23')
ON DUPLICATE KEY UPDATE `validation_status`=VALUES(`validation_status`);

SET FOREIGN_KEY_CHECKS = 1;

-- Fin du script
