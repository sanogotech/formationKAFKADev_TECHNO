# 5 TPs complets sur ksqlDB** fonctionnant avec **Kafka en mode KRaft** (sans ZooKeeper) 

---

## Table des matières

1. [Architecture KRaft et prérequis](#1-architecture-kraft-et-pr%C3%A9requis)
2. [TP1 : Prise en main – Création de Stream et requêtes Push](#2-tp1--prise-en-main--création-de-stream-et-requêtes-push)
3. [TP2 : Filtrage, Projection et Transformation](#3-tp2--filtrage-projection-et-transformation)
4. [TP3 : Agrégations et Fenêtrage Temporel](#4-tp3--agrégations-et-fenêtrage-temporel)
5. [TP4 : Jointures (Stream-Table)](#5-tp4--jointures-stream-table)
6. [TP5 : Client Java ksqlDB (Pull Queries)](#6-tp5--client-java-ksqldb-pull-queries)
7. [Récapitulatif des résultats](#7-récapitulatif-des-résultats)

---

## 1. Architecture KRaft et prérequis

### 🔑 Définitions importantes

| Concept | Définition |
|---------|-------------|
| **KRaft (KIP-500)** | Mode de fonctionnement de Kafka sans ZooKeeper. Le contrôle du cluster est géré par des **controllers** intégrés, simplifiant l'architecture et l'administration. |
| **ksqlDB** | Moteur de streaming SQL construit sur Kafka Streams. Permet de traiter des flux de données en temps réel avec une syntaxe SQL simple . |
| **Stream** | Collection partitionnée, immuable et append-only représentant une série d'événements (ex: transactions, clics) . |
| **Table** | Collection mutable représentant l'état actuel d'une clé (ex: dernière position d'un véhicule). Une table dérive d'un stream . |
| **Push Query** | Requête continue qui envoie les résultats au client au fur et à mesure que de nouveaux événements arrivent (`EMIT CHANGES`) . |
| **Pull Query** | Requête ponctuelle (request/response) qui interroge l'état actuel d'une matérialisation (`SELECT * FROM table WHERE ...`) . |
| **Persistent Query** | Requête exécutée côté serveur qui écrit les résultats dans un topic Kafka (création d'un nouveau stream ou table) . |

### 📦 Prérequis techniques

1. **Java 17** installé : `java -version`
2. **Maven 3.8+** installé : `mvn -version`
3. **Kafka 3.6+** (compatible KRaft) – télécharger depuis [kafka.apache.org](https://kafka.apache.org/downloads)

### ⚙️ Configuration de Kafka en mode KRaft (sans Docker)

```bash
# 1. Générer un ID de cluster unique
cd kafka-3.6.0
bin/kafka-storage.sh random-uuid
# Exemple de sortie : 5zZq9TbhRxS5Iq3P6gvW6Q

# 2. Formater le répertoire de logs avec l'ID généré
bin/kafka-storage.sh format -t <VOTRE_UUID> -c config/kraft/server.properties

# 3. Démarrer Kafka (mode KRaft)
bin/kafka-server-start.sh config/kraft/server.properties
```

**Création des topics nécessaires** :

```bash
bin/kafka-topics.sh --create --topic users-topic --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic clicks-topic --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic products-topic --bootstrap-server localhost:9092
```

### 📥 Installation et démarrage de ksqlDB Server

```bash
# Télécharger ksqlDB (version 0.28+ compatible KRaft)
wget https://github.com/confluentinc/ksql/releases/download/v0.28.0/ksqldb-0.28.0.tar.gz
tar -xzf ksqldb-0.28.0.tar.gz
cd ksqldb-0.28.0

# Configurer ksqlDB (editer etc/ksqldb-server.properties)
# Ajouter :
bootstrap.servers=localhost:9092
listeners=http://localhost:8088

# Démarrer le serveur
bin/ksql-server-start etc/ksqldb-server.properties

# Dans un autre terminal, démarrer le CLI
bin/ksql http://localhost:8088
```

### 💡 Tips KRaft

- Le mode KRaft élimine la dépendance à ZooKeeper : un seul processus à gérer .
- Les topics internes de ksqlDB sont stockés directement sur Kafka.
- Pour la production, utilisez plusieurs controllers pour la redondance.

---

## 2. TP1 : Prise en main – Création de Stream et requêtes Push

### Objectif
Créer un stream à partir d'un topic Kafka et exécuter des requêtes push pour visualiser les événements en temps réel.

### Concepts clés
- **Stream** : représentation SQL d'un topic Kafka
- **Push query** : `SELECT ... EMIT CHANGES` – flux continu de résultats

### Code SQL (à exécuter dans ksqlDB CLI)

```sql
-- ============================================================
-- TP1 - Partie 1 : Création d'un Stream
-- ============================================================

-- 1. Créer un stream basé sur le topic 'users-topic'
-- Le stream lit les données au format JSON
CREATE STREAM users_stream (
    user_id VARCHAR KEY,   -- La clé Kafka devient user_id
    name VARCHAR,
    age INT,
    city VARCHAR
) WITH (
    KAFKA_TOPIC = 'users-topic',
    VALUE_FORMAT = 'JSON',
    PARTITIONS = 1
);

-- 2. Afficher la structure du stream
DESCRIBE users_stream;

-- 3. Voir les données en temps réel (Push Query)
-- Cette requête reste active et affiche chaque nouvel événement
SELECT user_id, name, age, city 
FROM users_stream 
EMIT CHANGES;

-- 4. Insérer des données de test (dans un autre terminal ou en CLI)
INSERT INTO users_stream (user_id, name, age, city) 
VALUES ('1', 'Alice Dupont', 28, 'Paris');
INSERT INTO users_stream (user_id, name, age, city) 
VALUES ('2', 'Bernard Martin', 35, 'Lyon');
INSERT INTO users_stream (user_id, name, age, city) 
VALUES ('3', 'Claire Petit', 42, 'Marseille');
```

### Résultats attendus commentés

```sql
-- Après chaque INSERT, la push query affiche :
+-------+---------------+---------------+------+
|USER_ID|NAME           |AGE            |CITY  |
+-------+---------------+---------------+------+
|1      |Alice Dupont   |28             |Paris |
|2      |Bernard Martin |35             |Lyon  |
|3      |Claire Petit   |42             |Marseille|
```

**Explication** : La clause `EMIT CHANGES` transforme la requête SELECT en **push query** : le résultat est envoyé au client chaque fois qu'un nouvel enregistrement correspond aux critères .

### Test avec producteur Kafka (alternatif)

```bash
# Produire directement dans le topic
echo '{"user_id":"4","name":"David","age":31,"city":"Toulouse"}' | \
bin/kafka-console-producer --topic users-topic --bootstrap-server localhost:9092
```

---

## 3. TP2 : Filtrage, Projection et Transformation

### Objectif
Appliquer des transformations sur les données : filtrage, sélection de champs, calculs simples.

### Concepts clés
- **Filtre** : clause `WHERE`
- **Projection** : sélection des colonnes
- **Fonctions scalaires** : `UCASE`, `LCASE`, `CONCAT`, calculs arithmétiques

### Code SQL

```sql
-- ============================================================
-- TP2 - Filtrage et transformation
-- ============================================================

-- 1. Stream de clics utilisateurs (topic existant)
CREATE STREAM clicks_stream (
    user_id VARCHAR KEY,
    page_url VARCHAR,
    duration_seconds INT,
    timestamp BIGINT
) WITH (
    KAFKA_TOPIC = 'clicks-topic',
    VALUE_FORMAT = 'JSON',
    TIMESTAMP = 'timestamp',
    TIMESTAMP_FORMAT = 'ISO_8601'
);

-- 2. Insérer des données de test
INSERT INTO clicks_stream (user_id, page_url, duration_seconds, timestamp)
VALUES ('1', '/home', 45, UNIX_TIMESTAMP());
INSERT INTO clicks_stream (user_id, page_url, duration_seconds, timestamp)
VALUES ('1', '/products', 120, UNIX_TIMESTAMP());
INSERT INTO clicks_stream (user_id, page_url, duration_seconds, timestamp)
VALUES ('2', '/home', 30, UNIX_TIMESTAMP());

-- 3. Push query avec filtre : clics de plus de 60 secondes
SELECT user_id, page_url, duration_seconds
FROM clicks_stream
WHERE duration_seconds > 60
EMIT CHANGES;

-- 4. Transformation : URL en majuscules + calcul du coût estimé
SELECT 
    user_id,
    UCASE(page_url) AS url_upper,
    duration_seconds,
    duration_seconds * 0.01 AS estimated_cost
FROM clicks_stream
WHERE page_url = '/products'
EMIT CHANGES;

-- 5. Créer un nouveau stream persisté (tableau de bord des clics longs)
CREATE STREAM long_clicks_stream AS
SELECT 
    user_id,
    page_url,
    duration_seconds,
    CASE 
        WHEN duration_seconds > 120 THEN 'very_long'
        WHEN duration_seconds > 60 THEN 'long'
        ELSE 'normal'
    END AS duration_category
FROM clicks_stream
WHERE duration_seconds > 60
EMIT CHANGES;

-- Vérifier le nouveau stream
SELECT * FROM long_clicks_stream EMIT CHANGES;
```

### Résultats attendus

**Requête 3** (filtre duration > 60) :
```
+---------+------------+------------------+
|USER_ID  |PAGE_URL    |DURATION_SECONDS  |
+---------+------------+------------------+
|1        |/products   |120               |
```

**Requête 4** (transformation) :
```
+---------+------------+------------------+----------------+
|USER_ID  |URL_UPPER   |DURATION_SECONDS  |ESTIMATED_COST  |
+---------+------------+------------------+----------------+
|1        |/PRODUCTS   |120               |1.20            |
```

**Tip** : Les requêtes `CREATE STREAM AS SELECT` (CSAS) sont des **persistent queries** – elles s'exécutent indéfiniment et écrivent les résultats dans un topic Kafka dédié .

---

## 4. TP3 : Agrégations et Fenêtrage Temporel

### Objectif
Réaliser des comptages et agrégations par fenêtre de temps (tumbling, hopping, session).

### Concepts clés
- **Window types** : TUMBLING, HOPPING, SESSION
- **Fonctions d'agrégation** : COUNT, SUM, AVG, LATEST_BY_OFFSET
- **Table vs Stream** : Une agrégation produit une TABLE

### Code SQL

```sql
-- ============================================================
-- TP3 - Agrégations et fenêtrage
-- ============================================================

-- 1. Créer un stream d'événements de clics
CREATE STREAM clicks_windowed_stream (
    user_id VARCHAR KEY,
    click_count INT,
    event_time BIGINT
) WITH (
    KAFKA_TOPIC = 'clicks-topic',
    VALUE_FORMAT = 'JSON',
    TIMESTAMP = 'event_time'
);

-- 2. Insérer des données avec timestamps différents
INSERT INTO clicks_windowed_stream (user_id, click_count, event_time) 
VALUES ('user1', 1, UNIX_TIMESTAMP());
-- Attendre 5 secondes
INSERT INTO clicks_windowed_stream (user_id, click_count, event_time) 
VALUES ('user1', 1, UNIX_TIMESTAMP());
-- Attendre 8 secondes
INSERT INTO clicks_windowed_stream (user_id, click_count, event_time) 
VALUES ('user2', 1, UNIX_TIMESTAMP());

-- 3. Fenêtre TUMBLING (fixe, sans chevauchement)
-- Taille : 10 secondes
SELECT 
    user_id,
    COUNT(*) AS clicks_per_window,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end
FROM clicks_windowed_stream
WINDOW TUMBLING (SIZE 10 SECONDS)
GROUP BY user_id
EMIT CHANGES;

-- 4. Fenêtre HOPPING (avec chevauchement)
-- Taille : 30 secondes, avance : 10 secondes
SELECT 
    user_id,
    SUM(click_count) AS total_clicks,
    WINDOWSTART AS window_start
FROM clicks_windowed_stream
WINDOW HOPPING (SIZE 30 SECONDS, ADVANCE BY 10 SECONDS)
GROUP BY user_id
EMIT CHANGES;

-- 5. Fenêtre SESSION (inactive après 20 secondes)
SELECT 
    user_id,
    COUNT(*) AS session_clicks,
    WINDOWSTART AS session_start
FROM clicks_windowed_stream
WINDOW SESSION (20 SECONDS)
GROUP BY user_id
EMIT CHANGES;

-- 6. Créer une table persistante des clics par utilisateur (état actuel)
CREATE TABLE user_click_counts AS
SELECT 
    user_id,
    SUM(click_count) AS total_clicks,
    LATEST_BY_OFFSET(event_time) AS last_click_time
FROM clicks_windowed_stream
GROUP BY user_id
EMIT CHANGES;

-- 7. Pull query sur la table (interroge l'état actuel)
-- À exécuter après avoir reçu des données
SELECT user_id, total_clicks, last_click_time 
FROM user_click_counts
WHERE user_id = 'user1';
```

### Résultats attendus

**Fenêtre TUMBLING** (user1, deux clics dans la même fenêtre de 10s) :
```
+---------+-------------------+------------------+----------------+
|USER_ID  |CLICKS_PER_WINDOW  |WINDOW_START      |WINDOW_END      |
+---------+-------------------+------------------+----------------+
|user1    |2                  |1734567890000     |1734567900000   |
|user2    |1                  |1734567900000     |1734567910000   |
```

**Pull query finale** :
```
+---------+-------------+------------------+
|USER_ID  |TOTAL_CLICKS |LAST_CLICK_TIME   |
+---------+-------------+------------------+
|user1    |2            |1734567895000     |
```

**Explication** : 
- Une **fenêtre TUMBLING** divise le temps en segments contigus sans chevauchement.
- Une **fenêtre SESSION** s'arrête après une période d'inactivité .
- La **pull query** (`SELECT ... FROM table WHERE ...`) interroge l'état matérialisé et se termine, contrairement aux push queries .

---

## 5. TP4 : Jointures (Stream-Table)

### Objectif
Enrichir un flux d'événements avec une table de référence (ex: clics + infos utilisateur).

### Concepts clés
- **Stream-Table Join** : chaque événement du stream est enrichi avec l'état actuel de la table.
- **Enrichissement en temps réel** : idéal pour les données de référence changeantes.

### Code SQL

```sql
-- ============================================================
-- TP4 - Jointure Stream-Table
-- ============================================================

-- 1. Table des utilisateurs (état mutable)
-- Les mises à jour de profil sont reflétées immédiatement
CREATE TABLE users_table (
    user_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    city VARCHAR,
    user_segment VARCHAR
) WITH (
    KAFKA_TOPIC = 'users-topic',
    VALUE_FORMAT = 'JSON'
);

-- 2. Insérer / mettre à jour des utilisateurs
INSERT INTO users_table (user_id, name, city, user_segment) 
VALUES ('1', 'Alice', 'Paris', 'premium');
INSERT INTO users_table (user_id, name, city, user_segment) 
VALUES ('2', 'Bernard', 'Lyon', 'standard');

-- 3. Stream des clics (enrichissement)
CREATE STREAM clicks_enriched AS
SELECT 
    c.user_id,
    u.name AS user_name,
    u.city AS user_city,
    u.user_segment,
    c.page_url,
    c.duration_seconds
FROM clicks_stream c
LEFT JOIN users_table u ON c.user_id = u.user_id
EMIT CHANGES;

-- 4. Observer l'enrichissement en temps réel
SELECT * FROM clicks_enriched EMIT CHANGES;

-- 5. Exemple : agrégation par segment utilisateur
CREATE TABLE clicks_by_segment AS
SELECT 
    user_segment,
    COUNT(*) AS total_clicks,
    SUM(duration_seconds) AS total_duration
FROM clicks_enriched
GROUP BY user_segment
EMIT CHANGES;

-- 6. Pull query : état actuel des clics par segment
SELECT user_segment, total_clicks, total_duration
FROM clicks_by_segment
WHERE user_segment = 'premium';
```

### Résultats attendus

**Stream enrichi** (clic de user1) :
```
+---------+-----------+--------+--------------+----------+------------------+
|USER_ID  |USER_NAME  |USER_CITY|USER_SEGMENT |PAGE_URL  |DURATION_SECONDS  |
+---------+-----------+--------+--------------+----------+------------------+
|1        |Alice      |Paris   |premium       |/products |120               |
```

**Table par segment** (pull query) :
```
+--------------+-------------+----------------+
|USER_SEGMENT  |TOTAL_CLICKS |TOTAL_DURATION  |
+--------------+-------------+----------------+
|premium       |5            |450             |
```

**Tip important** : Dans une jointure Stream-Table, la table peut être mise à jour. Si le profil d'Alice change (ex: passe de 'premium' à 'standard'), les **futurs clics** utiliseront la nouvelle valeur. Les clics passés ne sont pas rétroactivement modifiés .

---

## 6. TP5 : Client Java ksqlDB (Pull Queries)

### Objectif
Interagir avec ksqlDB depuis une application Java : exécuter des pull queries et des push queries.

### Structure Maven

**pom.xml** :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>ksqldb-client-tp5</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <ksqldb.version>0.28.0</ksqldb.version>
    </properties>

    <repositories>
        <repository>
            <id>ksqlDB</id>
            <name>ksqlDB Maven Repository</name>
            <url>https://ksqldb-maven.s3.amazonaws.com/maven/</url>
        </repository>
    </repositories>

    <dependencies>
        <!-- Client ksqlDB officiel -->
        <dependency>
            <groupId>io.confluent.ksql</groupId>
            <artifactId>ksqldb-api-client</artifactId>
            <version>${ksqldb.version}</version>
        </dependency>
        <!-- Jackson pour JSON -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.15.2</version>
        </dependency>
    </dependencies>
</project>
```

### Code Java complet

```java
package com.example.ksqldb;

import io.confluent.ksql.api.client.Client;
import io.confluent.ksql.api.client.ClientOptions;
import io.confluent.ksql.api.client.Row;
import io.confluent.ksql.api.client.StreamedQueryResult;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * TP5 : Client Java ksqlDB
 * 
 * Objectif : Interagir avec ksqlDB Server depuis une application Java.
 * 
 * Concepts :
 * - Pull Query : requête ponctuelle sur une table matérialisée (similaire à SQL classique)
 * - Push Query : requête continue qui reçoit les changements en temps réel
 * - Insertion de données via le client
 * 
 * Prérequis :
 * - ksqlDB Server démarré sur http://localhost:8088
 * - Les streams et tables du TP4 doivent exister
 * 
 * Test :
 * Exécuter la méthode main, puis vérifier les résultats dans la console.
 */
public class KsqlDBClientDemo {

    private static final String KSQLDB_HOST = "localhost";
    private static final int KSQLDB_PORT = 8088;
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        // 1. Configuration du client
        ClientOptions options = ClientOptions.create()
            .setHost(KSQLDB_HOST)
            .setPort(KSQLDB_PORT)
            .setUseAlpn(false);  // Désactiver ALPN pour les connexions simples

        Client client = Client.create(options);
        System.out.println("Client ksqlDB connecté à " + KSQLDB_HOST + ":" + KSQLDB_PORT);

        // 2. Pull Query : interroger l'état actuel d'une table
        // La pull query se termine après avoir retourné le résultat
        String pullQuery = "SELECT user_id, name, city, user_segment FROM users_table WHERE user_id = '1';";
        
        System.out.println("\n=== Pull Query ===");
        System.out.println("Exécution : " + pullQuery);
        
        List<Row> results = client.executeQuery(pullQuery).get(5, TimeUnit.SECONDS);
        
        for (Row row : results) {
            System.out.println("user_id: " + row.getString("USER_ID"));
            System.out.println("name: " + row.getString("NAME"));
            System.out.println("city: " + row.getString("CITY"));
            System.out.println("segment: " + row.getString("USER_SEGMENT"));
        }

        // 3. Pull Query sur la table agrégée du TP3
        String clickStatsQuery = "SELECT user_id, total_clicks FROM user_click_counts;";
        
        System.out.println("\n=== Statistiques des clics (Pull Query) ===");
        List<Row> clickStats = client.executeQuery(clickStatsQuery).get(5, TimeUnit.SECONDS);
        
        for (Row row : clickStats) {
            System.out.println("user_id: " + row.getString("USER_ID") + 
                             ", total_clicks: " + row.getLong("TOTAL_CLICKS"));
        }

        // 4. Push Query : écouter les changements en continu
        // La push query reste active et reçoit chaque nouvel événement
        System.out.println("\n=== Push Query (écoute des clics enrichis) ===");
        System.out.println("En attente des nouveaux événements... (Ctrl+C pour arrêter)");
        
        String pushQuery = "SELECT user_id, user_name, page_url, duration_seconds " +
                          "FROM clicks_enriched " +
                          "EMIT CHANGES;";
        
        // Exécuter la push query de manière asynchrone
        CompletableFuture<StreamedQueryResult> streamFuture = client.streamQuery(pushQuery);
        StreamedQueryResult streamedResult = streamFuture.get(5, TimeUnit.SECONDS);
        
        // Traiter les résultats en continu (bloquant pour la démo)
        while (streamedResult.hasNext()) {
            Row row = streamedResult.next();
            System.out.println(String.format("Nouveau clic | User: %s | URL: %s | Durée: %d",
                row.getString("USER_NAME"),
                row.getString("PAGE_URL"),
                row.getInteger("DURATION_SECONDS")
            ));
        }

        // 5. Insertion de données via le client Java
        // Insérer un nouvel utilisateur
        String insertUserSql = "INSERT INTO users_table (user_id, name, city, user_segment) " +
                              "VALUES ('3', 'Claire', 'Marseille', 'standard');";
        
        client.executeStatement(insertUserSql).get(5, TimeUnit.SECONDS);
        System.out.println("\nNouvel utilisateur inséré avec succès");

        // Fermer le client proprement
        client.close();
    }
}
```

### Test avec insertion depuis le producteur Kafka

```bash
# Alternative : produire des clics directement
echo '{"user_id":"1","page_url":"/checkout","duration_seconds":85,"event_time":1734567890}' | \
bin/kafka-console-producer --topic clicks-topic --bootstrap-server localhost:9092
```

### Résultats attendus dans la console Java

```
Client ksqlDB connecté à localhost:8088

=== Pull Query ===
Exécution : SELECT user_id, name, city, user_segment FROM users_table WHERE user_id = '1';
user_id: 1
name: Alice
city: Paris
segment: premium

=== Statistiques des clics (Pull Query) ===
user_id: 1, total_clicks: 5
user_id: 2, total_clicks: 2

=== Push Query (écoute des clics enrichis) ===
En attente des nouveaux événements...
Nouveau clic | User: Alice | URL: /checkout | Durée: 85
```

**Explication du client Java**  :
- `client.executeQuery()` : exécute une **pull query** – retourne un résultat ponctuel (List<Row>).
- `client.streamQuery()` : exécute une **push query** – retourne un StreamedQueryResult qui reçoit les événements en continu.
- Les deux méthodes sont asynchrones (retournent `CompletableFuture`).

**Remarque sur la compatibilité KRaft** : ksqlDB 0.28+ est entièrement compatible avec Kafka en mode KRaft (KIP-500). Aucune configuration spéciale n'est requise .

---

## 7. Récapitulatif des résultats

| TP | Compétence | Résultat attendu |
|----|------------|------------------|
| **TP1** | Création de Stream, Push Query | Visualisation des INSERTs en temps réel |
| **TP2** | Filtrage, projection, transformation | `long_clicks_stream` avec catégorisation |
| **TP3** | Agrégations fenêtrées | Comptages par fenêtre de 10s et état courant |
| **TP4** | Jointure Stream-Table | Enrichissement des clics avec infos utilisateur |
| **TP5** | Client Java ksqlDB | Pull/Push queries depuis application Java |

---

## 📚 Définitions finales et rappels

| Terme | Définition |
|-------|-------------|
| **KRaft** | Mode de Kafka sans ZooKeeper, plus simple à administrer |
| **ksqlDB Server** | Service qui exécute les requêtes SQL sur Kafka  |
| **Command Topic** | Topic interne stockant l'historique des commandes SQL (interactive mode)  |
| **Headless Mode** | Mode où les requêtes sont définies dans un fichier, pas de REST API |
| **UDF** | User Defined Function – étendre ksqlDB avec des fonctions Java personnalisées |

---

## ⚠️ Tips de production

1. **Pour la production**, utilisez plusieurs instances de ksqlDB Server derrière un load balancer.
2. **Surveillez les topics internes** : `_confluent-ksql-<service-id>command_topic` .
3. **Schema Evolution** : privilégiez Avro ou Protobuf avec Schema Registry pour l'évolution des schémas .
4. **Performance** : les agrégations avec fenêtrage créent des stores RocksDB – surveillez la mémoire.

---

## 🚀 Exécution rapide

```bash
# 1. Démarrer Kafka (KRaft)
cd kafka-3.6.0 && bin/kafka-server-start.sh config/kraft/server.properties

# 2. Démarrer ksqlDB Server
cd ksqldb-0.28.0 && bin/ksql-server-start etc/ksqldb-server.properties

# 3. Lancer le CLI ksqlDB pour les TPs 1-4
bin/ksql http://localhost:8088

# 4. Pour le TP5, compiler et exécuter l'application Java
mvn clean compile exec:java -Dexec.mainClass="com.example.ksqldb.KsqlDBClientDemo"
```

Ces 5 TPs couvrent l'essentiel de ksqlDB : des concepts fondamentaux (Streams/Tables) aux jointures et à l'intégration Java, le tout sur une architecture moderne sans ZooKeeper.
