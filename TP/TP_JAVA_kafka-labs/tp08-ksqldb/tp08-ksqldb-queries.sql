-- ============================================================
--  TP08 — ksqlDB : SQL sur les Streams Kafka
-- ============================================================
--
--  OBJECTIF :
--   Interroger et transformer des flux Kafka avec du SQL
--   via ksqlDB — pas besoin d'écrire du code Java/Python !
--
--  PRÉREQUIS AVANT CE TP :
--   ✅ TP02 terminé (topic tp01-commandes avec données)
--   ✅ Docker Desktop installé
--
--  LANCER KSQLDB AVEC DOCKER :
--   Option 1 — Docker Compose (recommandé) :
--   > docker compose -f docker-compose-ksqldb.yml up -d
--   > docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
--
--   Option 2 — Sans Docker (Confluent Platform local) :
--   > bin/ksql-server-start etc/ksqldb/ksql-server.properties
--   > bin/ksql http://localhost:8088
--
--  VÉRIFIER QUE KSQLDB EST PRÊT :
--   > curl http://localhost:8088/info
--   Réponse attendue : {"KsqlServerInfo":{"version":"7.x.x",...}}
--
--  EXÉCUTER CE FICHIER SQL :
--   Dans l'interface ksqlDB :
--   RUN SCRIPT 'tp08-ksqldb-queries.sql';
-- ============================================================


-- ── ÉTAPE 1 : Configurer ksqlDB pour lire depuis le début ───────────────────
-- Par défaut : ksqlDB lit seulement les nouveaux messages
-- SET 'auto.offset.reset' = 'earliest' pour lire depuis le début
SET 'auto.offset.reset' = 'earliest';

-- ── ÉTAPE 2 : Créer un STREAM sur le topic existant ─────────────────────────
-- STREAM = flux infini de messages, immuable (append-only)
-- TABLE  = vue agrégée, mise à jour (upsert par clé)
CREATE OR REPLACE STREAM commandes_stream (
    id       VARCHAR,
    client   VARCHAR,
    produit  VARCHAR,
    quantite INT,
    montant  DOUBLE,
    statut   VARCHAR,
    timestamp VARCHAR
-- WITH : associer le stream au topic Kafka
) WITH (
    KAFKA_TOPIC  = 'tp01-commandes',  -- Topic Kafka source
    VALUE_FORMAT = 'JSON',            -- Format des messages
    PARTITIONS   = 3                  -- Nombre de partitions
);

-- Vérifier la création
DESCRIBE commandes_stream;

-- ── ÉTAPE 3 : Première requête — voir les messages en temps réel ─────────────
-- SELECT sur un STREAM = lit les messages en continu (ne termine pas!)
-- Ctrl+C pour arrêter
SELECT
    id,
    client,
    produit,
    montant,
    TIMESTAMPTOSTRING(ROWTIME, 'HH:mm:ss') AS heure
FROM commandes_stream
EMIT CHANGES
LIMIT 10;
-- LIMIT 10 : s'arrêter après 10 messages (pour ce TP)

-- ── ÉTAPE 4 : Filtrer les commandes VIP (montant > 500€) ────────────────────
-- Les filtres SQL fonctionnent sur les streams !
SELECT
    id,
    client,
    produit,
    ROUND(montant, 2) AS montant_eur
FROM commandes_stream
WHERE montant > 500.0
EMIT CHANGES;

-- ── ÉTAPE 5 : STREAM dérivé — commandes VIP persistées ──────────────────────
-- CREATE STREAM AS SELECT : crée un nouveau topic Kafka automatiquement !
-- C'est ksqlDB qui gère le Consumer + Producer en coulisses
CREATE OR REPLACE STREAM commandes_vip AS
SELECT
    id,
    UCASE(client)  AS client_upper,  -- Majuscules
    produit,
    montant,
    'VIP' AS categorie
FROM commandes_stream
WHERE montant > 500.0
PARTITION BY client;  -- Partitionner par client pour garder l'ordre

-- Vérifier : un nouveau topic a été créé automatiquement
-- > kafka-topics.sh --list --bootstrap-server localhost:9092
-- → COMMANDES_VIP

-- ── ÉTAPE 6 : TABLE d'agrégation — total des ventes par client ──────────────
-- GROUP BY + agrégation = TABLE (mise à jour continue)
CREATE OR REPLACE TABLE stats_clients AS
SELECT
    client,
    COUNT(*)       AS nb_commandes,     -- Nombre total
    SUM(montant)   AS total_achats,     -- Montant total
    AVG(montant)   AS panier_moyen,     -- Panier moyen
    MAX(montant)   AS plus_grosse_cmd,  -- Plus grande commande
    MIN(montant)   AS plus_petite_cmd   -- Plus petite commande
FROM commandes_stream
GROUP BY client
EMIT CHANGES;

-- Interroger la table (snapshot de l'état actuel)
SELECT * FROM stats_clients WHERE client = 'alice';

-- ── ÉTAPE 7 : Requête PUSH vs PULL ──────────────────────────────────────────
-- PUSH query (EMIT CHANGES) = abonnement continu, reçoit les màj en temps réel
-- Exemple : interface utilisateur qui se met à jour en live
SELECT client, nb_commandes, total_achats
FROM stats_clients
EMIT CHANGES;

-- PULL query (sans EMIT CHANGES) = snapshot à l'instant T
-- Exemple : API REST qui répond à une requête ponctuelle
SELECT client, nb_commandes, total_achats
FROM stats_clients
WHERE client = 'alice';

-- ── ÉTAPE 8 : JOINTURE Stream-Table ─────────────────────────────────────────
-- Enrichir les commandes avec des infos produits (table de référence)
CREATE OR REPLACE TABLE catalogue_produits (
    code_produit VARCHAR PRIMARY KEY,
    categorie    VARCHAR,
    poids_kg     DOUBLE
) WITH (
    KAFKA_TOPIC  = 'catalogue-produits',
    VALUE_FORMAT = 'JSON',
    PARTITIONS   = 1
);

-- Join Stream + Table = enrichissement en temps réel
CREATE OR REPLACE STREAM commandes_enrichies AS
SELECT
    c.id          AS commande_id,
    c.client,
    c.produit,
    c.montant,
    p.categorie   AS categorie_produit,
    p.poids_kg    AS poids_commande
FROM commandes_stream c
LEFT JOIN catalogue_produits p
    ON c.produit = p.code_produit
EMIT CHANGES;

-- ── ÉTAPE 9 : Fenêtres temporelles ──────────────────────────────────────────
-- TUMBLING WINDOW : fenêtres fixes non-chevauchantes
-- Compter les commandes par tranches de 1 heure
SELECT
    client,
    COUNT(*)     AS commandes_heure,
    SUM(montant) AS total_heure,
    WINDOWSTART  AS debut_fenetre,
    WINDOWEND    AS fin_fenetre
FROM commandes_stream
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY client
EMIT CHANGES;

-- ── ÉTAPE 10 : Vider et nettoyer ────────────────────────────────────────────
-- IMPORTANT : en TP, supprimer les streams/tables créés
-- DROP STREAM IF EXISTS commandes_vip DELETE TOPIC;
-- DROP TABLE  IF EXISTS stats_clients  DELETE TOPIC;
-- DROP STREAM IF EXISTS commandes_stream;
