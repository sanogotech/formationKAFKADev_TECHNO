# formationKAFKADev_TECHNO

# 🚀 Formation KAFKA PAR LA PRATIQUE (Version 9 jours optimisée)



# 🚀 SYLLABUS DE FORMATION

## Apache Kafka (Apache Kafka) – Développement, Architecture, Administration & Debezium (9 jours)

---

# 📌 1. Introduction générale

Apache Kafka est aujourd’hui la technologie centrale des architectures de streaming temps réel modernes. Elle permet de traiter, transporter et distribuer des flux de données à grande échelle avec une faible latence et une forte résilience.

Dans les systèmes modernes (microservices, data mesh, event-driven architecture), Kafka joue le rôle de **colonne vertébrale des échanges asynchrones**.

Cette formation intensive de 9 jours a pour objectif de transformer les participants en profils **opérationnels et experts Kafka**, capables de :

* développer des applications événementielles,
* administrer un cluster Kafka en production,
* construire des pipelines de données temps réel,
* intégrer des bases de données via CDC avec Debezium,
* et optimiser des systèmes distribués critiques.

---

# 🎯 2. Objectifs généraux de la formation

À la fin de la formation, le participant sera capable de :

## 🧑‍💻 Développement (Java / Python / autres)

* Développer des Producers et Consumers en **Java (principal)** et **Python (secondaire)**
* Comprendre et implémenter les patterns Kafka (Pub/Sub, Event Streaming)
* Manipuler les sérialisations (JSON, Avro, String)
* Gérer les groupes de consommateurs et offsets

## 🧠 Architecture & Streaming

* Concevoir des architectures event-driven scalables
* Utiliser Kafka Streams pour les traitements temps réel
* Comprendre KStream, KTable et fenêtres temporelles

## 🛠️ Administration Kafka

* Déployer et gérer un cluster Kafka (mode KRaft)
* Superviser les brokers, partitions et réplication
* Gérer la haute disponibilité et les incidents

## 🔄 Data Engineering / CDC

* Mettre en place la capture de données avec Debezium
* Construire des pipelines de données complets
* Gérer l’évolution des schémas sans interruption

## ⚙️ Production & performance

* Optimiser producteurs et consommateurs
* Gérer exactly-once processing et transactions
* Sécuriser un cluster (TLS / SASL / ACL)

---

# 🎓 3. Public cible

Cette formation s’adresse à :

* 👨‍💻 Développeurs backend (Java / Python / Node.js)
* 🧠 Architectes logiciels et architectes SI
* 🛠️ DevOps / Administrateurs systèmes
* 📊 Data Engineers / Data Architects
* 🔁 Ingénieurs intégration / ETL
* 🚀 Consultants techniques en systèmes distribués

---

# 💻 4. Stack technique complet utilisé dans les TP

## 🧱 Core streaming platform

* Apache Kafka (cluster 3 brokers minimum)
* Kafka CLI tools
* Kafka Connect
* Kafka Streams

## 🔄 CDC & intégration bases de données

* Debezium
* PostgreSQL / MySQL (bases source)
* Schema Registry (Avro / JSON Schema)

## 🧑‍💻 Langages de développement

* ☕ Java (11 ou 17) → langage principal des TP
* 🐍 Python 3.9+ → consumers, scripts, data processing
* (Optionnel) Node.js pour démonstration API event-driven

## 🐳 Infrastructure

* Docker & Docker Compose
* Linux (Ubuntu recommandé)

## 📊 Monitoring & observabilité

* Prometheus
* Grafana
* Kafka Exporter

## 🔍 Data sink / analytics

* Elasticsearch
* Kibana

## ⚙️ Outils de test & performance

* kafka-producer-perf-test
* kafka-consumer-groups CLI
* Postman (API tests)

---

# 🧪 5. Travaux pratiques (TP)

## 💡 Langages utilisés dans les TP

| Type de TP         | Langage principal  |
| ------------------ | ------------------ |
| Producer Kafka     | Java               |
| Consumer Kafka     | Python             |
| Kafka Streams      | Java               |
| Kafka Connect      | YAML / JSON config |
| Debezium CDC       | SQL + config JSON  |
| Monitoring scripts | Python             |
| API event-driven   | Java / Python      |

---

## 🧪 Exemples de TP structurés

| Domaine       | TP                               |
| ------------- | -------------------------------- |
| Développement | Producer Java + Consumer Python  |
| Streaming     | Kafka Streams agrégation         |
| Connect       | PostgreSQL → Kafka (JDBC)        |
| CDC           | MySQL → Kafka via Debezium       |
| Admin         | Crash broker + recovery          |
| Performance   | Benchmark 10k msg/s              |
| Sécurité      | TLS + ACL configuration          |
| Production    | Exactly-once pipeline            |
| Projet final  | Data pipeline complet end-to-end |

---

# 💻 6. Prérequis sur les postes étudiants

Chaque participant doit disposer d’un environnement prêt pour exécuter les TP.

## 🖥️ Configuration matérielle minimale

| Élément  | Requis                          |
| -------- | ------------------------------- |
| RAM      | 8 Go minimum (16 Go recommandé) |
| CPU      | 4 cœurs minimum                 |
| Stockage | 20 Go libres                    |
| OS       | Windows 10/11, Linux ou macOS   |

---

## 🧰 Logiciels obligatoires

* Docker Desktop (ou Docker Engine Linux)
* Docker Compose
* Java JDK 11 ou 17
* Python 3.9+
* Maven ou Gradle
* Git
* VS Code ou IntelliJ IDEA

---

## 📦 Environnement préconfiguré recommandé

Chaque étudiant doit pouvoir lancer :

```bash
docker compose up -d
```

Pour démarrer automatiquement :

* Kafka cluster (3 brokers)
* Zookeeper remplacé par KRaft
* Kafka Connect
* PostgreSQL
* Debezium
* Kafka UI (optionnel)
* Prometheus + Grafana

```

---

## 🌐 Connaissances préalables requises

| Domaine | Niveau attendu |
|--------|---------------|
| Java | Bases (classes, méthodes, exceptions) |
| Python | Bases (fonctions, boucles, JSON) |
| SQL | SELECT / INSERT / UPDATE |
| Linux | Commandes basiques |
| Réseau | Notions API REST |

---

# 🧠 7. Compétences développées

À la fin de la formation, le participant saura :

## 🟢 Développement
- Construire des applications Kafka en Java & Python
- Gérer production et consommation d’événements

## 🟡 Architecture
- Concevoir des systèmes event-driven robustes
- Structurer des flux de données temps réel

## 🟠 Administration
- Installer et administrer un cluster Kafka production-ready

## 🔵 Data Engineering
- Implémenter CDC avec Debezium
- Construire des pipelines de données industriels

## 🔴 Production
- Optimiser performance et latence
- Sécuriser et fiabiliser Kafka

---

# 🔁 8. Retours d’expérience (REX industriels)

## 🏦 Banque & finance
- Transactions temps réel
- Détection fraude streaming

## 🛒 E-commerce
- Tracking commandes live
- Recommandations dynamiques

## 🚚 Logistique
- Tracking GPS flotte véhicules
- Optimisation livraison temps réel

## 📊 Data platform
- Data lake streaming (Kafka → S3 / Elasticsearch)

---

# 🏁 9. Conclusion

Cette formation fournit une maîtrise complète de Kafka, de la programmation à l’administration en passant par le streaming avancé et la capture de données avec Debezium.

Elle prépare les participants à devenir des profils **hautement opérationnels en architecture de données temps réel**, capables de travailler directement sur des systèmes de production modernes.


---



## 🧭 Titre

**Apache Kafka de A à Z : Développement, Architecture, Administration, Debezium & Production (9 jours intensifs)**

---

## 🎯 Introduction

Apache Kafka est aujourd’hui un pilier central des architectures modernes : microservices, data mesh, event-driven architecture, CDC (Change Data Capture) et streaming temps réel.

Cette formation **intensive de 9 jours (3 blocs de 3 jours)** permet de passer progressivement :

* 👨‍💻 **Développeur Kafka (Java / Python)**
* 🧠 **Architecte & expert streaming**
* 🛠️ **Administrateur Kafka production-ready**
* 🔄 **Spécialiste Debezium & CDC**
* ⚙️ **Ingénieur performance & fiabilité**
* 🏆 **Préparation certification Confluent**

---

# 🧱 STRUCTURE GLOBALE (9 JOURS)

| Session      | Durée   | Objectif principal                           |
| ------------ | ------- | -------------------------------------------- |
| 🟦 Session 1 | J1 → J3 | Développement Kafka & Architecture Streaming |
| 🟧 Session 2 | J4 → J6 | Administration Kafka & Production            |
| 🟩 Session 3 | J7 → J9 | Debezium, CDC, optimisation & projet final   |

---

# 🟦 SESSION 1 — DÉVELOPPEMENT & ARCHITECTURE KAFKA (3 JOURS)

## 🎯 Objectif

Devenir opérationnel sur Kafka en tant que **développeur & architecte de flux événementiels**

---

## 📘 Jour 1 — Fondations Kafka & Architecture

### Concepts

* Event-driven architecture
* Broker, Topic, Partition, Offset
* Producer / Consumer
* KRaft (sans ZooKeeper)

### TP

* Déploiement cluster Kafka via Docker
* Création topics
* Production / consommation via CLI
* Analyse des partitions et offsets

---

## 📘 Jour 2 — Développement Kafka (Java & Python)

### Concepts

* Kafka Producer API (acks, retries, batching)
* Kafka Consumer API (group.id, commit)
* Sérialisation JSON

### TP

* Producer Java (événements métiers)
* Consumer Python (traitement + commit manuel)
* Gestion des erreurs et rebalancing

---

## 📘 Jour 3 — Kafka Streams & Kafka Connect (bases)

### Concepts

* KStream vs KTable
* Windows (tumbling, hopping)
* Introduction Kafka Connect

### TP

* Agrégation temps réel (Kafka Streams Java)
* Requêtes simples avec ksqlDB
* JDBC Source → Kafka (PostgreSQL)

---

# 🟧 SESSION 2 — ADMINISTRATION & PRODUCTION KAFKA (3 JOURS)

## 🎯 Objectif

Maîtriser **Kafka en environnement production (cluster, monitoring, performance, sécurité)**

---

## 📘 Jour 4 — Administration Cluster Kafka

### Concepts

* Architecture KRaft (controller / broker)
* ISR & réplication
* Partition leadership

### TP

* Simulation cluster instable
* Réélection leader
* Réassignation partitions

---

## 📘 Jour 5 — Monitoring & Troubleshooting

### Concepts

* Métriques Kafka (lag, throughput)
* Logs brokers
* Consumer lag

### TP

* Monitoring avec Prometheus/Grafana
* Analyse consumer lag
* Debug d’un cluster dégradé

---

## 📘 Jour 6 — Performance & Sécurité

### Concepts

* Tuning Producer & Consumer
* Compression, batch.size, linger.ms
* TLS / SASL / ACL

### TP

* Benchmark 10k+ msg/s
* Activation TLS basique
* Simulation surcharge + optimisation

---

# 🟩 SESSION 3 — DEBEZIUM, CDC & PROJET FINAL (3 JOURS)

## 🎯 Objectif

Construire une architecture **data streaming complète en production (CDC + transformation + sink + observabilité)**

---

## 📘 Jour 7 — Debezium & Change Data Capture (CDC)

### Concepts

* CDC (Change Data Capture)
* Architecture Debezium
* Event types (c / u / d)
* Schema evolution

### TP

* MySQL/PostgreSQL → Kafka via Debezium
* Analyse des événements CRUD
* Ajout colonne sans downtime

---

## 📘 Jour 8 — Streaming avancé & fiabilité

### Concepts

* Exactly-once processing
* Kafka transactions
* Idempotence
* Retry & DLQ (Dead Letter Queue)

### TP

* Producer transactionnel
* Pipeline fiable end-to-end
* Simulation panne + reprise

---

## 📘 Jour 9 — Projet final + Simulation certification

### 🎯 Projet fil rouge (end-to-end)

Architecture complète :

```
PostgreSQL
   ↓ (Debezium CDC)
Kafka
   ↓ (Kafka Streams enrichment)
API externe (ex: météo / finance)
   ↓
Elasticsearch
   ↓
Kibana Dashboard
```

---

### 🎓 Simulation certification

* QCM type Confluent (CCDAK / CCAAK)
* Cas pratiques chronométrés
* Correction détaillée + stratégie d’examen

---

# 🧠 COMPÉTENCES ACQUISES

| Domaine                 | Niveau atteint         |
| ----------------------- | ---------------------- |
| Kafka Développement     | ✔ Avancé               |
| Architecture streaming  | ✔ Expert               |
| Kafka administration    | ✔ Production           |
| Kafka Streams           | ✔ Avancé               |
| Kafka Connect           | ✔ Opérationnel         |
| Debezium / CDC          | ✔ Expert               |
| Performance tuning      | ✔ Expert               |
| Sécurité Kafka          | ✔ Intermédiaire/Avancé |
| Certification readiness | ✔ Oui                  |

---

# 🧰 ENVIRONNEMENT TECHNIQUE

* Kafka 3.x (KRaft)
* Docker / Docker Compose
* Kafka Connect
* Debezium
* PostgreSQL / MySQL
* Java 11+ / Python 3.9+
* Prometheus + Grafana
* Elasticsearch + Kibana

---

# 🧪 PÉDAGOGIE

* 40% théorie / 60% pratique
* 1 cluster Kafka par stagiaire
* 1 projet fil rouge évolutif
* 1 TP par concept clé
* Simulation panne réelle
* Mode “production mindset”

---

# 🏁 LIVRABLES

À la fin de la formation :

* Code source Kafka (Java + Python)
* Pipeline CDC complet
* Dashboard monitoring
* Projet final industrialisable
* Simulation certification corrigée
* Architecture prête production

---

# 🚀 VALEUR AJOUTÉE DE CETTE VERSION

✔ Réduction intelligente de 10 → 9 jours
✔ Structuration en 3 blocs cohérents
✔ Progression logique (Dev → Ops → Data Engineering)
✔ Accent fort sur production réelle
✔ Ajout Debezium au cœur du système
✔ Préparation certification intégrée
✔ Projet final réaliste industrie

---
