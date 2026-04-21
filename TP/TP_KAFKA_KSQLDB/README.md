# 📘 **ksqlDB – Cheat Sheet Complet**

## Guide ultime avec concepts, exemples, tuning, bonnes pratiques et tips

---

## 1. 🏗️ **Concepts Fondamentaux**

### Définitions clés

| Concept | Définition | Analogie |
|---------|------------|----------|
| **STREAM** | Flux immuable, append-only d'événements | `INSERT ONLY` |
| **TABLE** | Vue mutable, état actuel par clé | `UPDATE/DELETE` |
| **Push Query** | Requête continue (`EMIT CHANGES`) | WebSocket / Streaming |
| **Pull Query** | Requête ponctuelle (SELECT simple) | SQL classique |
| **Persistent Query** | Requête qui écrit dans un topic | Materialized View |
| **Window** | Agrégation temporelle | TUMBLING, HOPPING, SESSION |
| **Materialization** | Stockage local du résultat | Index |
| **UDF/UDAF** | Fonctions personnalisées | User Defined Functions |

### Types de fenêtres

```sql
-- 1. TUMBLING - Fixe sans chevauchement (10 secondes)
WINDOW TUMBLING (SIZE 10 SECONDS)

-- 2. HOPPING - Avec chevauchement (taille 30s, avance 10s)
WINDOW HOPPING (SIZE 30 SECONDS, ADVANCE BY 10 SECONDS)

-- 3. SESSION - Basée sur inactivité (gap 30s)
WINDOW SESSION (30 SECONDS)

-- 4. TIMEZONE spécifique
WINDOW TUMBLING (SIZE 1 HOUR, RETENTION 7 DAYS, GRACE PERIOD 1 HOUR)
```

### Types de données supportés

```sql
-- Primitifs
BOOLEAN, INTEGER, BIGINT, DOUBLE, VARCHAR, DECIMAL

-- Complexes
ARRAY<VARCHAR>, MAP<VARCHAR, INT>, STRUCT<id INT, name VARCHAR>

-- Temporels
DATE, TIME, TIMESTAMP
```

---

## 2. 🚀 **Configuration Optimale**

### ksqlDB Server (etc/ksqldb-server.properties)

```properties
# ========== Base ==========
bootstrap.servers=localhost:9092
listeners=http://0.0.0.0:8088

# ========== Performance ==========
ksql.streams.num.stream.threads=4
ksql.streams.cache.max.bytes.buffering=10485760
ksql.streams.commit.interval.ms=30000
ksql.streams.auto.offset.reset=earliest

# ========== Tolérance pannes ==========
ksql.streams.processing.guarantee=exactly_once_v2
ksql.streams.num.standby.replicas=1
ksql.service.id=ksql_prod_001

# ========== State Store ==========
ksql.streams.state.dir=/data/ksqldb/state
ksql.streams.rocksdb.config.setter=io.confluent.ksql.rocksdb.KsqlRocksDBConfigSetter

# ========== Queries ==========
ksql.query.pull.table.scan.enabled=true
ksql.query.pull.table.scan.cache.capacity=10000
ksql.query.pull.router.max.threads=100

# ========== Sécurité ==========
# SSL/TLS
listeners=https://0.0.0.0:8088
ssl.keystore.location=/path/to/keystore.jks
ssl.keystore.password=password

# Authentication
authentication.method=BASIC
authentication.roles=admin,user
```

### Configuration client Java

```java
// Client Java pour ksqlDB
ClientOptions options = ClientOptions.create()
    .setHost("localhost")
    .setPort(8088)
    .setUseAlpn(false)
    .setConnectionTimeout(30)
    .setRetries(3)
    .setRetryBackoff(1000);

Client client = Client.create(options);
```

---

## 3. 📝 **Patterns et Bonnes Pratiques**

### Pattern 1: Création sécurisée (IF NOT EXISTS)

```sql
-- Éviter les erreurs de duplication
CREATE STREAM IF NOT EXISTS orders_stream (
    order_id VARCHAR KEY,
    product_id VARCHAR,
    quantity INT,
    price DECIMAL(10,2)
) WITH (
    KAFKA_TOPIC = 'orders-topic',
    VALUE_FORMAT = 'JSON',
    PARTITIONS = 6,
    REPLICAS = 3
);

CREATE TABLE IF NOT EXISTS product_table (
    product_id VARCHAR PRIMARY KEY,
    product_name VARCHAR,
    category VARCHAR
) WITH (
    KAFKA_TOPIC = 'products-topic',
    VALUE_FORMAT = 'AVRO'
);
```

### Pattern 2: Gestion des erreurs et DLQ

```sql
-- Stream avec gestion des erreurs
CREATE STREAM orders_validated AS
SELECT 
    order_id,
    product_id,
    quantity,
    price
FROM orders_stream
WHERE quantity > 0 
  AND price > 0
EMIT CHANGES;

-- Dead Letter Queue pour les erreurs
CREATE STREAM orders_dlq AS
SELECT 
    order_id,
    product_id,
    quantity,
    price,
    'invalid_data' AS error_reason
FROM orders_stream
WHERE quantity <= 0 OR price <= 0
EMIT CHANGES;
```

### Pattern 3: Exactly-once et idempotence

```sql
-- Utiliser INSERT VALUES avec gestion des duplicats
INSERT INTO processed_orders (order_id, status, processed_at)
VALUES ('order_123', 'COMPLETED', UNIX_TIMESTAMP());

-- Vérifier avant insertion (table pour tracking)
CREATE TABLE order_tracker (
    order_id VARCHAR PRIMARY KEY,
    status VARCHAR
) WITH (KAFKA_TOPIC='order-tracker', VALUE_FORMAT='JSON');

-- Insertion conditionnelle (via left join)
CREATE STREAM new_orders AS
SELECT o.order_id, o.data
FROM orders_stream o
LEFT JOIN order_tracker t ON o.order_id = t.order_id
WHERE t.order_id IS NULL
EMIT CHANGES;
```

### Pattern 4: Reconnexion et résilience

```sql
-- Configurer les requêtes persistantes avec reprise
CREATE STREAM resilient_stream WITH (
    KAFKA_TOPIC = 'source',
    VALUE_FORMAT = 'JSON'
);

-- Ajouter un timeout et retry
SET 'ksql.streams.retry.backoff.ms'='5000';
SET 'ksql.streams.retry.max.attempts'='10';
SET 'ksql.streams.request.timeout.ms'='60000';

CREATE TABLE aggregated_results AS
SELECT 
    user_id,
    COUNT(*) AS count
FROM resilient_stream
GROUP BY user_id
EMIT CHANGES;
```

---

## 4. ⚡ **Optimisations Performance**

### Tuning des requêtes

```sql
-- 1. Utiliser des partitions adéquates
CREATE STREAM optimized_stream (
    id VARCHAR KEY,
    data VARCHAR
) WITH (
    KAFKA_TOPIC='source',
    PARTITIONS=12,  -- Multiple de vos threads
    REPLICAS=3
);

-- 2. Limiter les projections (éviter SELECT *)
SELECT user_id, name, city FROM users EMIT CHANGES;

-- 3. Filtrer tôt dans la pipeline
CREATE STREAM filtered AS
SELECT * FROM raw_stream
WHERE filter_condition;  -- Filtre immédiat

-- 4. Matérialiser les résultats intermédiaires
CREATE TABLE daily_sales WITH (MATERIALIZED='true') AS
SELECT 
    product_id,
    SUM(quantity) AS total
FROM orders_stream
WINDOW TUMBLING (SIZE 1 DAY)
GROUP BY product_id
EMIT CHANGES;
```

### Configuration des stores

```sql
-- 1. Définir la rétention des fenêtres
CREATE TABLE long_term_aggregates AS
SELECT 
    user_id,
    COUNT(*) AS events
FROM event_stream
WINDOW HOPPING (SIZE 1 HOUR, ADVANCE BY 5 MINUTES, RETENTION 30 DAYS)
GROUP BY user_id
EMIT CHANGES;

-- 2. Ajouter GRACE PERIOD pour les données tardives
CREATE TABLE graceful_aggregate AS
SELECT 
    product_id,
    SUM(amount) AS total
FROM sales_stream
WINDOW TUMBLING (SIZE 10 SECONDS, GRACE PERIOD 5 SECONDS)
GROUP BY product_id
EMIT CHANGES;

-- 3. Utiliser CACHE pour réduire les écritures
SET 'ksql.streams.cache.max.bytes.buffering'='52428800'; -- 50 MB
```

### Optimisations avancées

```sql
-- 1. Co-partitionnement (éviter repartitioning)
-- S'assurer que les streams ont le même nombre de partitions
CREATE STREAM stream_a WITH (PARTITIONS=6) AS ...;
CREATE TABLE table_b WITH (PARTITIONS=6) AS ...;

-- 2. Utiliser le key format approprié
CREATE STREAM orders (
    order_id VARCHAR KEY,  -- Partition par order_id
    data VARCHAR
) WITH (KAFKA_TOPIC='orders');

-- 3. Supprimer les colonnes inutiles (réduire la sérialisation)
CREATE STREAM slim_stream AS
SELECT 
    order_id,
    total_amount
FROM full_stream
EMIT CHANGES;
```

---

## 5. 🔧 **Débogage et Monitoring**

### Commandes de diagnostic

```sql
-- 1. Lister tous les streams/tables
LIST STREAMS;
LIST TABLES;
LIST ALL;

-- 2. Décrire un stream/table
DESCRIBE orders_stream;
DESCRIBE EXTENDED orders_stream;

-- 3. Voir les requêtes actives
LIST QUERIES;
EXPLAIN SELECT * FROM orders_stream EMIT CHANGES;

-- 4. Voir les propriétés de runtime
SHOW PROPERTIES;

-- 5. Voir les topics internes
SHOW TOPICS;

-- 6. Voir les connecteurs
SHOW CONNECTORS;
```

### Métriques essentielles

```sql
-- Métriques JMX pour ksqlDB
-- - ksql:type=ksql-engine,ksql-service-id=*
-- - ksql:type=query-stats,ksql-query-id=*

-- Métriques à surveiller
SELECT * FROM ksql_query_stats EMIT CHANGES;

-- Voir les lags
SELECT 
    consumer_group,
    topic,
    partition,
    lag
FROM kafka_consumer_groups;
```

### Debug avec PRINT

```sql
-- 1. Lire un topic directement
PRINT 'orders-topic' FROM BEGINNING;
PRINT 'orders-topic' LIMIT 10;

-- 2. Avec format JSON
PRINT 'orders-topic' FROM BEGINNING WITH (FORMAT='JSON');

-- 3. Voir les changements en temps réel
PRINT 'orders-topic' INTERVAL 1;

-- 4. Filtrer les messages
PRINT 'orders-topic' FROM BEGINNING WHERE value->product_id = 'P001';
```

---

## 6. 🎯 **Exemples par Cas d'Usage**

### Cas 1: Détection de fraude en temps réel

```sql
-- Stream des transactions
CREATE STREAM transactions (
    transaction_id VARCHAR KEY,
    user_id VARCHAR,
    amount DECIMAL(10,2),
    location VARCHAR,
    timestamp BIGINT
) WITH (
    KAFKA_TOPIC = 'transactions',
    VALUE_FORMAT = 'JSON',
    TIMESTAMP = 'timestamp'
);

-- Fenêtre glissante 5 minutes
CREATE TABLE fraud_detection AS
SELECT 
    user_id,
    COUNT(*) AS tx_count,
    SUM(amount) AS total_amount,
    COLLECT_LIST(location) AS locations
FROM transactions
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY user_id
HAVING COUNT(*) > 10 OR SUM(amount) > 10000
EMIT CHANGES;

-- Alertes
CREATE STREAM fraud_alerts AS
SELECT 
    user_id,
    tx_count,
    total_amount,
    locations,
    'SUSPICIOUS' AS alert_type
FROM fraud_detection
EMIT CHANGES;
```

### Cas 2: Enrichissement avec données de référence

```sql
-- Table produits (référence)
CREATE TABLE products (
    product_id VARCHAR PRIMARY KEY,
    product_name VARCHAR,
    category VARCHAR,
    price DECIMAL(10,2)
) WITH (
    KAFKA_TOPIC = 'products',
    VALUE_FORMAT = 'AVRO'
);

-- Stream ventes
CREATE STREAM sales (
    sale_id VARCHAR KEY,
    product_id VARCHAR,
    quantity INT,
    sale_time BIGINT
) WITH (
    KAFKA_TOPIC = 'sales',
    VALUE_FORMAT = 'JSON'
);

-- Enrichissement
CREATE STREAM enriched_sales AS
SELECT 
    s.sale_id,
    s.product_id,
    p.product_name,
    p.category,
    s.quantity,
    (s.quantity * p.price) AS total_amount
FROM sales s
LEFT JOIN products p ON s.product_id = p.product_id
EMIT CHANGES;
```

### Cas 3: Session utilisateur avancée

```sql
-- Clics utilisateur
CREATE STREAM user_clicks (
    user_id VARCHAR KEY,
    page VARCHAR,
    timestamp BIGINT
) WITH (
    KAFKA_TOPIC = 'clicks',
    VALUE_FORMAT = 'JSON',
    TIMESTAMP = 'timestamp'
);

-- Sessions (inactivité 30 secondes)
CREATE TABLE user_sessions AS
SELECT 
    user_id,
    COUNT(*) AS clicks_in_session,
    MIN(timestamp) AS session_start,
    MAX(timestamp) AS session_end,
    COLLECT_LIST(page) AS pages_visited
FROM user_clicks
WINDOW SESSION (30 SECONDS)
GROUP BY user_id
HAVING COUNT(*) > 1
EMIT CHANGES;

-- Session analytics
CREATE TABLE session_analytics AS
SELECT 
    user_id,
    clicks_in_session,
    (session_end - session_start) AS session_duration_ms,
    pages_visited
FROM user_sessions
EMIT CHANGES;
```

### Cas 4: Jointure Stream-Table

```sql
-- Table des comptes
CREATE TABLE accounts (
    account_id VARCHAR PRIMARY KEY,
    balance DECIMAL(10,2),
    status VARCHAR
) WITH (KAFKA_TOPIC='accounts');

-- Stream des débits
CREATE STREAM debits (
    debit_id VARCHAR KEY,
    account_id VARCHAR,
    amount DECIMAL(10,2),
    timestamp BIGINT
) WITH (KAFKA_TOPIC='debits', TIMESTAMP='timestamp');

-- Vérification de solde
CREATE STREAM verified_debits AS
SELECT 
    d.debit_id,
    d.account_id,
    a.balance,
    d.amount,
    CASE 
        WHEN a.balance >= d.amount THEN 'APPROVED'
        ELSE 'REJECTED'
    END AS status
FROM debits d
LEFT JOIN accounts a ON d.account_id = a.account_id
EMIT CHANGES;

-- Rejet des transactions
CREATE STREAM rejected_debits AS
SELECT * FROM verified_debits
WHERE status = 'REJECTED'
EMIT CHANGES;
```

---

## 7. 📊 **Commandes CLI essentielles**

```bash
# 1. Démarrer ksqlDB CLI
ksql http://localhost:8088

# 2. Exécuter un fichier SQL
ksql http://localhost:8088 --file queries.sql

# 3. Exécuter une requête en ligne
ksql http://localhost:8088 --execute "LIST STREAMS;"

# 4. Mode headless (sans API REST)
ksql-server-start etc/ksqldb-server.properties --queries-file queries.sql

# 5. Vérifier la santé
curl -X GET http://localhost:8088/healthcheck

# 6. Voir les métriques
curl -X GET http://localhost:8088/admin/metrics

# 7. Arrêter une requête
POST /ksql -d '{"ksql":"TERMINATE query_id;","streamsProperties":{}}'

# 8. Voir les queries actives
curl -X GET http://localhost:8088/queries

# 9. Démarrer une query push via REST
curl -X POST http://localhost:8088/query \
    -H "Content-Type: application/vnd.ksql.v1+json" \
    -d '{"ksql":"SELECT * FROM orders_stream EMIT CHANGES;"}'

# 10. Pull query via REST
curl -X POST http://localhost:8088/query \
    -d '{"ksql":"SELECT * FROM user_table WHERE user_id='123';"}'
```

---

## 8. 🎓 **Tips Pro par Thème**

### Performance

| Tip | Explication |
|-----|-------------|
| **Partitionner correctement** | Les streams doivent avoir le même nombre de partitions pour les jointures |
| **Utiliser `MATERIALIZED` pour les tables** | Accélère les pull queries |
| **Privilégier les pull queries pour l'état** | Push queries pour le temps réel uniquement |
| **Éviter `COLLECT_LIST` sur grands volumes** | Peut causer des OOM |
| **Configurer la rétention des fenêtres** | Réduit l'utilisation disque |

### Fiabilité

| Tip | Explication |
|-----|-------------|
| **Toujours utiliser `IF NOT EXISTS`** | Évite les erreurs de recréation |
| **Configurer `processing.guarantee=exactly_once_v2`** | Exactly-once semantics |
| **Ajouter des réplicas standby** | Récupération plus rapide |
| **Utiliser `GRACE PERIOD`** | Accepte les données tardives |
| **Monitorer les lag** | Détecte les retards |

### Opérations

| Tip | Explication |
|-----|-------------|
| **Versionner les streams dans leur nom** | `orders_v1`, `orders_v2` pour évolution |
| **Utiliser des topics séparés pour tests/prod** | Évite les interférences |
| **Sauvegarder les requêtes persistantes** | Dans un repo Git |
| **Planifier les backups des stores** | Répertoire `state.dir` |
| **Utiliser `SHOW QUERIES` régulièrement** | Vérifie l'état des requêtes |

---

## 9. 📈 **Métriques à surveiller**

```sql
-- Métriques clés (via JMX)
1. ksql.queries.running          -- Requêtes actives
2. ksql.messages.consumed        -- Messages consommés/sec
3. ksql.messages.produced         -- Messages produits/sec
4. ksql.task.avg.lag              -- Lag moyen par tâche
5. ksql.task.max.lag              -- Lag maximum
6. ksql.streams.state             -- État du stream
7. ksql.streams.commit.rate       -- Taux de commit
8. ksql.rocksdb.bytes.written     -- Écritures RocksDB
9. ksql.rocksdb.bytes.read        -- Lectures RocksDB
10. ksql.query.throughput         -- Débit par query
```

---

## 10. ⚠️ **Pièges courants et solutions**

| Piège | Symptôme | Solution |
|-------|----------|----------|
| **Co-partitionnement manquant** | Jointure lente, repartitioning | Vérifier nombre de partitions |
| **TIMESTAMP incorrect** | Fenêtres vides | Configurer `TIMESTAMP='col'` |
| **Grace period trop petit** | Messages ignorés | Ajouter `GRACE PERIOD` |
| **Rétention trop courte** | Données perdues | Augmenter `RETENTION` |
| **SELECT * dans push query** | Performance dégradée | Projeter uniquement colonnes utiles |
| **INSERT sans clé** | Duplication | Toujours spécifier PRIMARY KEY |
| **Pull query sans matérialisation** | Résultat vide | Ajouter `MATERIALIZED` |

---

## 11. 🧪 **Tests et validation**

```sql
-- 1. Créer un stream de test
CREATE STREAM test_stream (
    id VARCHAR KEY,
    value VARCHAR
) WITH (
    KAFKA_TOPIC = 'test-topic',
    VALUE_FORMAT = 'JSON',
    PARTITIONS = 1
);

-- 2. Insérer des données de test
INSERT INTO test_stream (id, value) VALUES ('1', 'test1');
INSERT INTO test_stream (id, value) VALUES ('2', 'test2');

-- 3. Valider la transformation
CREATE STREAM test_result AS
SELECT 
    id,
    UCASE(value) AS upper_value
FROM test_stream
EMIT CHANGES;

-- 4. Vérifier les résultats
SELECT * FROM test_result EMIT CHANGES;
PRINT 'TEST_RESULT' FROM BEGINNING LIMIT 10;

-- 5. Nettoyer
DROP STREAM test_stream;
DROP STREAM test_result;
```

---

## 12. 📚 **Fonctions essentielles**

### Scalaires

```sql
-- Chaînes
UCASE(str), LCASE(str), TRIM(str), SUBSTR(str, pos, len)
CONCAT(str1, str2), REPLACE(str, old, new)

-- Math
ABS(x), CEIL(x), FLOOR(x), ROUND(x, d), POW(x, y)

-- Date/Time
UNIX_TIMESTAMP(), TIMESTAMP_TO_STRING(ts, format)
STRING_TO_TIMESTAMP(str, format)

-- JSON
EXTRACTJSONFIELD(json, '$.field')

-- Conversion
CAST(value AS TYPE)
```

### Agrégations

```sql
COUNT(*), COUNT(col), SUM(col), AVG(col), MIN(col), MAX(col)
COLLECT_LIST(col), COLLECT_SET(col)
EARLIEST_BY_OFFSET(col), LATEST_BY_OFFSET(col)
TOP_K(col, k), TOP_K_DISTINCT(col, k)
```

### Fenêtrage

```sql
WINDOWSTART, WINDOWEND
HOPPING, TUMBLING, SESSION
```

---

## 13. 🔄 **Migration et évolution**

### Versioning des schémas

```sql
-- Version 1
CREATE STREAM orders_v1 (
    order_id VARCHAR KEY,
    product_id VARCHAR,
    quantity INT
) WITH (KAFKA_TOPIC='orders', VALUE_FORMAT='JSON');

-- Version 2 (ajout champ price)
CREATE STREAM orders_v2 (
    order_id VARCHAR KEY,
    product_id VARCHAR,
    quantity INT,
    price DECIMAL(10,2)
) WITH (KAFKA_TOPIC='orders', VALUE_FORMAT='JSON');

-- Migration progressive
CREATE STREAM orders_migration AS
SELECT 
    order_id,
    product_id,
    quantity,
    IFNULL(price, 0.00) AS price
FROM orders_v2
EMIT CHANGES;
```

---

## 14. 🚨 **Dépannage rapide**

```sql
-- 1. Query bloquée
LIST QUERIES;
TERMINATE query_id;

-- 2. Lag trop élevé
SHOW TOPICS EXTENDED;
-- Augmenter partitions ou threads

-- 3. Erreur de désérialisation
PRINT 'error-topic' FROM BEGINNING;
-- Vérifier format JSON

-- 4. Table non matérialisée
DESCRIBE EXTENDED my_table;
-- Vérifier MATERIALIZED flag

-- 5. Conflit de nom
DROP STREAM old_stream;
CREATE STREAM new_stream ...;

-- 6. Reset complet
-- Arrêter queries, supprimer topics internes
-- ksql-server-start --queries-file=reset.sql
```

---

## 15. 🎯 **Quick Reference – Commandes SQL**

```sql
-- ========== DDL ==========
CREATE STREAM s (id KEY, col TYPE) WITH (kafka_topic='t', value_format='JSON');
CREATE TABLE t (id PRIMARY KEY, col TYPE) WITH (kafka_topic='t', value_format='AVRO');
DROP STREAM s;
DROP TABLE t;

-- ========== DML ==========
INSERT INTO stream (id, col) VALUES ('1', 'value');
INSERT INTO stream SELECT ... FROM source EMIT CHANGES;

-- ========== Queries ==========
SELECT * FROM stream EMIT CHANGES;           -- Push
SELECT * FROM table WHERE id='1';            -- Pull
CREATE STREAM new AS SELECT ... EMIT CHANGES; -- Persistent

-- ========== Window ==========
WINDOW TUMBLING (SIZE 10 SECONDS)
WINDOW HOPPING (SIZE 1 MINUTE, ADVANCE BY 10 SECONDS)
WINDOW SESSION (30 SECONDS)

-- ========== Join ==========
FROM stream JOIN table ON key
FROM stream LEFT JOIN table ON key
FROM stream JOIN stream WITHIN 5 MINUTES ON key

-- ========== Properties ==========
SET 'property.name'='value';
SHOW PROPERTIES;
```

---

## 💡 **Bonus: Pattern Anti-Défaillance**

```sql
-- Surveillance et auto-réparation
CREATE STREAM heartbeat AS
SELECT 
    'ksqldb' AS source,
    UNIX_TIMESTAMP() AS ts
FROM orders_stream
EMIT CHANGES;

-- Alerte sur absence de données
CREATE TABLE dead_letter_monitor AS
SELECT 
    WINDOWSTART AS window,
    COUNT(*) AS error_count
FROM orders_dlq
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY 'all'
HAVING COUNT(*) > 100
EMIT CHANGES;
```

---

Ce cheat sheet vous accompagnera quotidiennement dans votre utilisation de ksqlDB. Gardez-le à portée de main et n'hésitez pas à l'adapter à vos cas d'usage spécifiques !
