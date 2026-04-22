

# 🧪 TP COMPLET : ksqlDB (Streaming SQL sur Kafka)

---

# 📘 1. Introduction

Dans les architectures modernes de data streaming, les données circulent en continu sous forme d’événements.

👉 **Apache Kafka** est la base de ce système.

Mais écrire du code Java pour traiter ces flux peut être complexe.

👉 **ksqlDB** permet de traiter ces flux avec du SQL simple, en temps réel.

---

# 📘 2. Objectif du TP

Dans ce TP, tu vas apprendre à :

* Créer un STREAM
* Filtrer des événements
* Faire des agrégations temps réel
* Créer une TABLE d’état
* Simuler un pipeline complet streaming

---

# 📦 3. Dataset (topic Kafka simulé)

Topic : `user_events`

```json id="ksql_tp_01"
{"userId":"user1","eventType":"click","ts":1}
{"userId":"user2","eventType":"click","ts":2}
{"userId":"user1","eventType":"click","ts":3}
{"userId":"user3","eventType":"purchase","ts":4}
{"userId":"user1","eventType":"click","ts":5}
{"userId":"user2","eventType":"purchase","ts":6}
{"userId":"user3","eventType":"click","ts":7}
```

---

# 🧱 4. CRÉATION DU STREAM

```sql id="ksql_tp_02"
-- Création du stream sur le topic Kafka
-- Chaque message JSON devient une ligne SQL

CREATE STREAM user_events (
    userId VARCHAR,
    eventType VARCHAR,
    ts BIGINT
) WITH (
    KAFKA_TOPIC = 'user_events',
    VALUE_FORMAT = 'JSON'
);
```

---

## 🧠 Explication

* STREAM = flux continu d’événements
* Chaque message Kafka = une ligne SQL
* Format JSON utilisé pour simplicité

---

# 🔍 5. LECTURE DU STREAM (SELECT simple)

```sql id="ksql_tp_03"
-- Affiche tous les événements en temps réel

SELECT *
FROM user_events
EMIT CHANGES;
```

---

## 🖥️ Résultat simulé

```text id="ksql_out_01"
user1 | click    | 1
user2 | click    | 2
user1 | click    | 3
user3 | purchase | 4
```

---

## 🧠 Explication

* `EMIT CHANGES` = streaming continu
* comme un “log live” Kafka

---

# 🔍 6. FILTRAGE (WHERE)

```sql id="ksql_tp_04"
-- On garde uniquement les clicks

SELECT *
FROM user_events
WHERE eventType = 'click'
EMIT CHANGES;
```

---

## 🖥️ Résultat simulé

```text id="ksql_out_02"
user1 | click | 1
user2 | click | 2
user1 | click | 3
user1 | click | 5
user3 | click | 7
```

---

## 🧠 Explication

👉 ksqlDB agit comme SQL + streaming
👉 filtre en temps réel

---

# 📊 7. AGRÉGATION (COUNT par utilisateur)

```sql id="ksql_tp_05"
-- Nombre d'événements par utilisateur

SELECT userId, COUNT(*) AS total_events
FROM user_events
GROUP BY userId
EMIT CHANGES;
```

---

## 🖥️ Résultat simulé

```text id="ksql_out_03"
user1 | 3
user2 | 2
user3 | 2
```

---

## 🧠 Explication

👉 ksqlDB maintient un état interne (stateful processing)

---

# 📊 8. AGRÉGATION par type d’événement

```sql id="ksql_tp_06"
-- Comptage par type d’événement

SELECT eventType, COUNT(*) AS total
FROM user_events
GROUP BY eventType
EMIT CHANGES;
```

---

## 🖥️ Résultat simulé

```text id="ksql_out_04"
click    | 5
purchase | 2
```

---

# 🧱 9. CRÉATION D’UNE TABLE (STATEFUL)

```sql id="ksql_tp_07"
-- Table = état actuel (snapshot)

CREATE TABLE user_stats AS
SELECT userId, COUNT(*) AS total_events
FROM user_events
GROUP BY userId
EMIT CHANGES;
```

---

## 🧠 Explication

* STREAM = événements
* TABLE = état actuel (dernier état agrégé)

👉 Très important en architecture Kafka

---

# 🔗 10. JOIN STREAM + TABLE

```sql id="ksql_tp_08"
-- Enrichir les événements avec les stats utilisateur

SELECT s.userId, s.eventType, t.total_events
FROM user_events s
JOIN user_stats t
ON s.userId = t.userId
EMIT CHANGES;
```

---

## 🖥️ Résultat simulé

```text id="ksql_out_05"
user1 | click    | 3
user2 | click    | 2
user3 | purchase | 2
```

---

## 🧠 Explication

👉 On enrichit chaque événement avec un état global

---

# 🔥 11. PIPELINE COMPLET (logique réelle)

```sql id="ksql_tp_09"
-- Pipeline complet streaming

CREATE STREAM clicks_only AS
SELECT userId, ts
FROM user_events
WHERE eventType = 'click'
EMIT CHANGES;
```

---

## 🧠 Explication

👉 On crée un nouveau flux dérivé (comme un topic Kafka)

---

# 🧠 RÉSUMÉ PÉDAGOGIQUE

| Concept      | Explication simple  |
| ------------ | ------------------- |
| STREAM       | flux d’événements   |
| TABLE        | état actuel         |
| WHERE        | filtrage temps réel |
| GROUP BY     | agrégation          |
| JOIN         | enrichissement      |
| EMIT CHANGES | mode streaming      |

---

# 🚀 CONCLUSION

Ce TP t’a appris à :

✔ Manipuler des flux temps réel
✔ Écrire des requêtes streaming SQL
✔ Faire des agrégations dynamiques
✔ Créer des tables et streams dérivés

👉 Tout cela repose sur **ksqlDB** au-dessus de **Apache Kafka**

---


