-- Donnees de demonstration initiales

USE assurance_db;

-- Agences
INSERT IGNORE INTO agences (id, nom, ville, adresse) VALUES 
('AG01', 'Agence Tunis Centre', 'Tunis', 'Avenue Habib Bourguiba'),
('AG02', 'Agence Sfax', 'Sfax', 'Rue de la Republique');

-- Gestionnaires (mots de passe haches en bcrypt : password123, password456, password789, password321)
INSERT IGNORE INTO gestionnaires (id, nom, prenom, username, email, password_hash, role, agence_id) VALUES 
('G123', 'Trabelsi', 'Ahmed', 'ahmed.trabelsi', 'eya.khadhraoui@esprit.tn', '$2b$12$e6m5JzUa4GfWpD6a.m0.eex7wUaLrq3NlIq3CqGf1XUvXy7vH7m6e', 'sinistres', 'AG01'),
('G456', 'Khelifi', 'Sarra', 'sarra.khelifi', 'eyakhadhraoui249@gmail.com', '$2b$12$K8yR2u4y1qFqRkC5V2e5xe1o8r3k7YpWqLmN.wOv9k5hI2dY0pZ3q', 'assurances', 'AG01'),
('G789', 'Bouazizi', 'Karim', 'karim.bouazizi', 'karim.test@example.com', '$2b$12$e6m5JzUa4GfWpD6a.m0.eex7wUaLrq3NlIq3CqGf1XUvXy7vH7m6e', 'sinistres', 'AG02'),
('G321', 'Mansour', 'Lina', 'lina.mansour', 'lina.test@example.com', '$2b$12$K8yR2u4y1qFqRkC5V2e5xe1o8r3k7YpWqLmN.wOv9k5hI2dY0pZ3q', 'assurances', 'AG02');

-- Clients
INSERT IGNORE INTO clients (id, nom, prenom, email, telephone, adresse) VALUES 
('CL01', 'Ben Ayed', 'Sonia', 'sonia.ba@mail.com', '20111111', 'Tunis'),
('CL02', 'Hammami', 'Amine', 'amine.h@mail.com', '20222222', 'Ariana'),
('CL03', 'Maromi', 'Jalva', 'jalva.m@mail.com', '20333333', 'Sfax'),
('CL04', 'Trabelsi', 'Martra', 'martra.t@mail.com', '20444444', 'Tunis'),
('CL05', 'Mansour', 'Karem', 'karem.m@mail.com', '20555555', 'Sousse');

-- Contrats
INSERT IGNORE INTO contrats (id, client_id, type_contrat, garantie_max, statut, date_creation, date_derniere_modif, gestionnaire_createur_id, agence_id) VALUES 
('CSTR00001', 'CL01', 'auto', 150000.00, 'actif', '2024-03-15', '2024-03-15', 'G456', 'AG01'),
('CSTR00002', 'CL02', 'habitation', 120000.00, 'actif', '2024-02-10', '2024-02-10', 'G456', 'AG01'),
('CSTR00003', 'CL03', 'auto', 80000.00, 'suspendu', '2024-01-01', '2024-01-01', 'G456', 'AG01'),
('CSTR00004', 'CL04', 'auto', 200000.00, 'actif', '2023-12-20', '2023-12-20', 'G321', 'AG02'),
('CSTR00005', 'CL05', 'habitation', 50000.00, 'resilie', '2023-11-05', '2023-11-05', 'G321', 'AG02');

-- Sinistres
INSERT IGNORE INTO sinistres (id, contrat_id, type_sinistre, montant_declare, date_declaration, statut, gestionnaire_traitant_id, agence_id) VALUES 
('CSIN00001', 'CSTR00001', 'Auto - Carambolage', 12000.00, '2024-03-31', 'en_cours', 'G123', 'AG01'),
('CSIN00002', 'CSTR00002', 'Habitation - Inondation', 10000.00, '2024-03-21', 'en_traitement', 'G123', 'AG01'),
('CSIN00003', 'CSTR00003', 'Auto - Carambolage', 3500.00, '2024-03-22', 'rejete', 'G789', 'AG02'),
('CSIN00004', 'CSTR00002', 'Habitation - Cambriolage', 3000.00, '2024-03-22', 'en_cours', 'G123', 'AG01'),
('CSIN00005', 'CSTR00001', 'Auto - Carambolage', 10000.00, '2024-03-21', 'en_cours', 'G123', 'AG01'),
('CSIN00006', 'CSTR00004', 'Auto - Carambolage', 1400.00, '2024-02-02', 'complete', 'G789', 'AG02');
