

# 🚀 INTRODUCTION GÉNÉRALE (DATA STREAMING MODERNE)

Dans les architectures modernes, les entreprises ne traitent plus les données uniquement “après coup”.

👉 Elles veulent les traiter **en temps réel**, dès qu’elles sont générées.

C’est ce qu’on appelle le **streaming de données**.

Au cœur de cette architecture on retrouve :

* **Apache Kafka** → le bus d’événements
* Kafka Connect → ingestion sans code
* Debezium → capture des changements base de données

---

## 🧠 OBJECTIF GLOBAL

Construire des systèmes capables de :

* transférer des données automatiquement
* capturer les changements des bases
* alimenter des systèmes analytiques en temps réel

---

# 🧠 CONCEPTS CLÉS (À COMPRENDRE AVANT LE TP)

---

## 🔹 1. Kafka (base du système)

👉 Kafka est un système de messagerie distribué.

Il permet de :

* stocker des événements
* les diffuser en temps réel
* les rejouer

---

## 🔹 2. Kafka Topic

👉 Un topic = un flux de données

Exemple :

```
user_events
orders
payments
```

---

## 🔹 3. Kafka Connect

👉 Outil qui permet de connecter Kafka à des sources externes :

* fichiers CSV
* bases de données
* APIs

✔ Sans coder de producer

---

## 🔹 4. CDC (Change Data Capture)

👉 Technique qui capture automatiquement les changements d’une base :

* INSERT
* UPDATE
* DELETE

---

## 🔹 5. Debezium

👉 Outil spécialisé CDC qui lit les logs de la base (binlog)

✔ transforme chaque changement en événement Kafka

---

## 🔹 6. Event Streaming

👉 Chaque modification devient un événement en temps réel

---

## 🔹 7. Architecture globale

```
DB / Files → Connect / Debezium → Kafka → Consumers
```

---

# 🧱 PROJET 1 — KAFKA CONNECT (INGESTION SIMPLE)

---

# 📘 PRÉREQUIS

## AVANT

* Docker installé
* Kafka + Kafka Connect
* notion de topic
* fichier CSV

---

## PENDANT

### 📦 Connector configuration

```json id="kc_01"
{
  "name": "file-source",
  "config": {
    "connector.class": "FileStreamSource",
    "tasks.max": "1",
    "file": "/data/input.csv",
    "topic": "file_topic",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "org.apache.kafka.connect.storage.StringConverter"
  }
}
```

---

### ▶️ Lancement

```bash id="kc_02"
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" \
-d @connector.json
```

---

## 📊 RÉSULTAT

```text id="kc_out"
user1,click,phone
user2,purchase,tv
user3,click,laptop
```

---

## 🧠 EXPLICATION

* Kafka Connect lit le fichier
* transforme chaque ligne en événement Kafka
* pousse dans `file_topic`

---

## APRÈS

```bash id="kc_03"
kafka-console-consumer --topic file_topic --from-beginning
```

---

## 💡 TIPS

* utiliser batching pour gros fichiers
* monitorer le lag Connect
* éviter fichiers non structurés

---

---

# 🔄 PROJET 2 — CDC AVEC DEBEZIUM

---

# 📘 PRÉREQUIS

## AVANT

* MySQL installé
* Kafka + Connect
* logs binlog activés
* **Debezium**

---

## PENDANT

---

### 🗄️ TABLE SOURCE

```sql id="cdc_01"
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id VARCHAR(50),
    product VARCHAR(50),
    amount DOUBLE
);
```

---

### ⚙️ CONNECTOR CDC

```json id="cdc_02"
{
  "name": "mysql-cdc",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",

    "database.hostname": "localhost",
    "database.port": "3306",
    "database.user": "root",
    "database.password": "root",

    "database.server.id": "184054",
    "database.server.name": "mysql_server",

    "database.include.list": "shop",
    "table.include.list": "shop.orders",

    "database.history.kafka.bootstrap.servers": "localhost:9092",
    "database.history.kafka.topic": "schema-changes.orders"
  }
}
```

---

### ▶️ LANCEMENT

```bash id="cdc_03"
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" \
-d @debezium.json
```

---

## 📊 RÉSULTATS

### INSERT

```json id="cdc_out_01"
{
  "op": "c",
  "after": {
    "id": 1,
    "user_id": "u1",
    "product": "phone",
    "amount": 500
  }
}
```

---

### UPDATE

```json id="cdc_out_02"
{
  "op": "u",
  "before": { "amount": 500 },
  "after": { "amount": 700 }
}
```

---

### DELETE

```json id="cdc_out_03"
{
  "op": "d",
  "before": { "id": 1 }
}
```

---

## 🧠 EXPLICATION

* Debezium lit les logs MySQL
* transforme chaque changement en event Kafka
* Kafka diffuse en temps réel

---

## APRÈS

```bash id="cdc_04"
kafka-console-consumer --topic mysql_server.shop.orders --from-beginning
```

---

## 💡 TIPS PRODUCTION

### 🔐 Fiabilité

* replication Kafka ≥ 3
* schema registry obligatoire

### ⚡ Performance

* filtrer tables inutiles
* éviter full CDC inutile

### 🧠 Design

* CDC = source de vérité
* Kafka = event backbone

---

# 🎯 CONCLUSION GLOBALE

Tu maîtrises maintenant :

✔ Kafka Connect → ingestion
✔ Debezium CDC → capture base de données
✔ streaming temps réel
✔ architecture event-driven

👉 basé sur :

* **Apache Kafka**
* **Debezium**

---


# 🚀 PROJET 3 — PIPELINE DATA END-TO-END AVEC KAFKA CONNECT

## 📊 “Synchronisation base de données → Kafka → Data Lake”

---

# 📘 1. INTRODUCTION GÉNÉRALE

Dans les architectures modernes, les entreprises veulent :

* capturer les données automatiquement
* les centraliser dans un bus d’événements
* les rendre disponibles pour analytics, BI ou IA

👉 C’est le rôle de :

* **Apache Kafka**
* **Kafka Connect**

---

## 🎯 OBJECTIF DU PROJET

Construire un pipeline complet :

```text id="proj3_arch"
MySQL → Kafka Connect → Kafka Topic → S3 (Data Lake simulé)
```

---

## 💡 CAS MÉTIER

👉 Une plateforme e-commerce veut :

* suivre les commandes
* synchroniser les données en temps réel
* alimenter un data lake pour BI / IA

---

# 🧠 2. CONCEPTS CLÉS À COMPRENDRE

---

## 🔹 1. Kafka Connect

👉 Framework sans code pour connecter Kafka à des systèmes externes.

✔ sources :

* DB
* fichiers
* API

✔ sinks :

* S3
* Elasticsearch
* DB

---

## 🔹 2. Source Connector

👉 lit des données externes → envoie vers Kafka

---

## 🔹 3. Sink Connector

👉 lit Kafka → écrit vers un système externe

---

## 🔹 4. Topic Kafka

👉 flux de données central

---

## 🔹 5. Event streaming

👉 chaque modification = événement

---

# 🧱 3. ARCHITECTURE DU PROJET

```text id="proj3_arch2"
        ┌──────────────┐
        │   MySQL DB   │
        └──────┬───────┘
               │
        (CDC / Connector)
               │
        ┌──────▼───────┐
        │  Kafka Topic  │
        │ orders_events │
        └──────┬───────┘
               │
        ┌──────▼───────┐
        │ Kafka Connect │
        │   SINK S3    │
        └──────┬───────┘
               │
        ┌──────▼───────┐
        │  Data Lake    │
        │   (S3)        │
        └──────────────┘
```

---

# ⚙️ 4. PRÉREQUIS

---

## 🧰 AVANT LE TP

### 🔹 Outils

* Docker
* Kafka + Kafka Connect
* MySQL
* AWS S3 (ou simulation local)
* **Apache Kafka**

---

### 🔹 Connaissances

* SQL basique
* JSON
* notions de streaming

---

# 🧱 5. ÉTAPE 1 — BASE DE DONNÉES

```sql id="proj3_sql1"
CREATE DATABASE shop;

USE shop;

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id VARCHAR(50),
    product VARCHAR(50),
    amount DOUBLE,
    created_at TIMESTAMP
);
```

---

## 🧠 Explication

👉 Table source des événements métiers

---

# 🔄 6. ÉTAPE 2 — CDC AVEC KAFKA CONNECT (SOURCE)

👉 On capture les changements MySQL

---

```json id="proj3_connect1"
{
  "name": "mysql-source-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",

    "database.hostname": "localhost",
    "database.port": "3306",
    "database.user": "root",
    "database.password": "root",

    "database.server.id": "184055",
    "database.server.name": "mysql_server",

    "database.include.list": "shop",
    "table.include.list": "shop.orders",

    "database.history.kafka.bootstrap.servers": "localhost:9092",
    "database.history.kafka.topic": "schema-history.orders",

    "include.schema.changes": "true"
  }
}
```

---

## 🧠 Explication

👉 Chaque INSERT / UPDATE / DELETE devient un event Kafka

---

# ▶️ LANCEMENT CONNECTOR

```bash id="proj3_run1"
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" \
-d @mysql-source.json
```

---

# 📡 7. ÉTAPE 3 — TOPIC KAFKA

👉 Topic généré automatiquement :

```text id="proj3_topic"
mysql_server.shop.orders
```

---

## 📊 Exemple d’event

```json id="proj3_event"
{
  "op": "c",
  "after": {
    "id": 1,
    "user_id": "u1",
    "product": "phone",
    "amount": 500
  }
}
```

---

# ☁️ 8. ÉTAPE 4 — SINK CONNECTOR (DATA LAKE)

👉 On envoie Kafka → S3

---

```json id="proj3_sink"
{
  "name": "s3-sink-connector",
  "config": {
    "connector.class": "io.confluent.connect.s3.S3SinkConnector",
    "topics": "mysql_server.shop.orders",

    "s3.bucket.name": "data-lake-shop",
    "s3.region": "eu-west-1",

    "flush.size": "3",
    "format.class": "io.confluent.connect.s3.format.json.JsonFormat",

    "storage.class": "io.confluent.connect.s3.storage.S3Storage"
  }
}
```

---

## 🧠 Explication

👉 Kafka → S3 automatiquement
👉 chaque batch devient un fichier JSON

---

# ▶️ LANCEMENT SINK

```bash id="proj3_run2"
curl -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" \
-d @s3-sink.json
```

---

# 📊 9. RÉSULTAT FINAL (DATA LAKE)

```text id="proj3_output"
s3://data-lake-shop/orders/part-0001.json
```

---

## 📄 Contenu fichier S3

```json id="proj3_s3"
{
  "id": 1,
  "user_id": "u1",
  "product": "phone",
  "amount": 500
}
```

---

# 🧠 10. EXPLICATION END-TO-END

## 🔹 Étape 1

MySQL génère des données

## 🔹 Étape 2

Debezium capture les changements

## 🔹 Étape 3

Kafka stocke les événements

## 🔹 Étape 4

Kafka Connect Sink envoie vers S3

---

# ⚡ 11. TIPS PRODUCTION

---

## 🔐 Fiabilité

* activer replication Kafka (≥3)
* utiliser schema registry

---

## ⚡ Performance

* batch size optimisé (flush.size)
* éviter surcharge CDC inutile

---

## 🧠 Design

✔ MySQL = source of truth
✔ Kafka = event backbone
✔ S3 = data lake analytique

---

## 📊 Monitoring

* lag Kafka Connect
* erreurs connector
* throughput topics

---

# 🎯 12. CONCLUSION

Ce projet montre un pipeline complet :

✔ ingestion automatique
✔ CDC en temps réel
✔ streaming Kafka
✔ export data lake

👉 basé sur :

* **Apache Kafka**
* Kafka Connect
* CDC Debezium

---


