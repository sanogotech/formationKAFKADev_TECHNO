-- ============================================================
--  TP09 — Initialisation MySQL pour Kafka Connect + CDC
-- ============================================================
--  Ce script est exécuté automatiquement au premier démarrage
--  du conteneur MySQL (via /docker-entrypoint-initdb.d/)
--
--  Il crée :
--  1. La base de données shopdb (déjà créée via env variable)
--  2. Les tables produits, commandes, clients
--  3. Des données de test initiales
--  4. Les permissions pour Debezium (CDC)
-- ============================================================

USE shopdb;

-- ── Activer binlog pour Debezium (CDC) ──────────────────────────────────────
-- Le binlog MySQL enregistre TOUS les changements (INSERT/UPDATE/DELETE)
-- Debezium lit ce binlog pour capturer les changements
-- NOTE : En production, configurer my.cnf plutôt que SET GLOBAL
SET GLOBAL binlog_format = 'ROW';

-- ── TABLE : clients ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS clients (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    nom        VARCHAR(100) NOT NULL,
    email      VARCHAR(150) UNIQUE NOT NULL,
    ville      VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── TABLE : produits ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS produits (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,
    nom         VARCHAR(200) NOT NULL,
    categorie   VARCHAR(100),
    prix        DECIMAL(10,2) NOT NULL,
    stock       INT DEFAULT 0,
    actif       TINYINT(1) DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ── TABLE : commandes ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS commandes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    client_id   INT NOT NULL,
    produit_id  INT NOT NULL,
    quantite    INT NOT NULL DEFAULT 1,
    montant     DECIMAL(10,2) NOT NULL,
    statut      ENUM('EN_ATTENTE','CONFIRMEE','EXPEDIEE','LIVREE','ANNULEE')
                DEFAULT 'EN_ATTENTE',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id)  REFERENCES clients(id),
    FOREIGN KEY (produit_id) REFERENCES produits(id)
) ENGINE=InnoDB;

-- ── DONNÉES INITIALES : Clients ──────────────────────────────────────────────
INSERT INTO clients (nom, email, ville) VALUES
    ('Alice Martin',  'alice@example.com',   'Paris'),
    ('Bob Dupont',    'bob@example.com',     'Lyon'),
    ('Claire Lebrun', 'claire@example.com',  'Bordeaux'),
    ('David Moreau',  'david@example.com',   'Marseille'),
    ('Emma Bernard',  'emma@example.com',    'Toulouse');

-- ── DONNÉES INITIALES : Produits ─────────────────────────────────────────────
INSERT INTO produits (code, nom, categorie, prix, stock) VALUES
    ('LAP-001', 'Laptop Pro 15',      'Informatique', 1299.99, 50),
    ('MOU-002', 'Souris Ergonomique', 'Accessoires',    49.99, 200),
    ('KEY-003', 'Clavier Mécanique',  'Accessoires',    89.99, 150),
    ('MON-004', 'Moniteur 4K 27"',    'Écrans',        449.99,  75),
    ('USB-005', 'Hub USB-C 7 ports',  'Accessoires',    35.99, 300);

-- ── DONNÉES INITIALES : Commandes ────────────────────────────────────────────
INSERT INTO commandes (client_id, produit_id, quantite, montant, statut) VALUES
    (1, 1, 1, 1299.99, 'CONFIRMEE'),
    (2, 2, 2,   99.98, 'LIVREE'),
    (3, 3, 1,   89.99, 'EXPEDIEE'),
    (4, 4, 1,  449.99, 'EN_ATTENTE'),
    (5, 5, 3,  107.97, 'CONFIRMEE'),
    (1, 2, 1,   49.99, 'EN_ATTENTE'),
    (2, 4, 2,  899.98, 'CONFIRMEE');

-- ── PERMISSIONS POUR DEBEZIUM (CDC) ──────────────────────────────────────────
-- Debezium a besoin de droits spéciaux pour lire le binlog
CREATE USER IF NOT EXISTS 'debezium'@'%' IDENTIFIED BY 'debezium_pass';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE,
      REPLICATION CLIENT ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;

-- Vérification
SELECT 'MySQL initialisé avec succès !' AS message;
SELECT COUNT(*) AS nb_clients  FROM clients;
SELECT COUNT(*) AS nb_produits FROM produits;
SELECT COUNT(*) AS nb_commandes FROM commandes;
