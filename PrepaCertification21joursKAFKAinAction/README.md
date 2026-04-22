# 🚀 BOOTCAMP EXPERT KAFKA (22 JOURS : JOUR 0 + 21 JOURS)

## 🎯 OBJECTIF GLOBAL

Former un profil capable de :

* Concevoir une architecture **Event-Driven complète**
* Développer des pipelines streaming robustes
* Intégrer des SI complexes (ERP, CRM, IoT, API)
* Administrer Kafka en **production critique (DSI)**

---

# 🧠 JOUR 0 — FONDATIONS STRATÉGIQUES (TRÈS IMPORTANT)

## 🎯 Objectif pédagogique

Comprendre **le “pourquoi Kafka existe” avant le “comment l’utiliser”**.

---

## 1. 🏛 État de l’art des architectures SI

### 🔴 Ancien monde (pré-Kafka)

* Applications monolithiques
* ETL batch nocturnes
* ESB lourds (SOAP, middleware centralisé)
* Intégration point-à-point

### ⚠️ Problèmes majeurs

* Latence élevée (heures ou jours)
* Forte dépendance entre systèmes
* Difficulté de montée en charge
* Risque élevé de rupture SI

### 🟢 Nouveau paradigme

* Event-Driven Architecture (EDA)
* Streaming temps réel
* Microservices découplés
* Data as a stream (et non stockage statique)

---

## 2. 📜 Histoire de Kafka

Apache Kafka

### 📌 Origine

* Créé chez LinkedIn (2010)
* Open source en 2011
* Objectif : gérer des flux massifs de données

### 📌 Révolution conceptuelle

Kafka introduit :

* Le **log distribué immuable**
* La séparation producer / consumer
* La relecture d’événements (replayability)

### 📌 Évolution

* Kafka 0.x → simple messaging
* Kafka 2.x → streaming platform
* Kafka 3.x+ → KRaft (sans Zookeeper)

---

## 3. 🌍 Cas d’usage industriels réels

### ⚡ Énergie (ton contexte DSI)

* Smart Meter (consommation temps réel)
* Détection panne réseau électrique
* Facturation dynamique

### 💳 Banque

* Détection fraude instantanée
* Transactions temps réel
* Risk scoring

### 📡 Télécom

* Analyse appels (CDR)
* Monitoring réseau
* SMS routing

### 🛒 Digital / e-commerce

* Tracking utilisateur
* Recommandation temps réel
* Stock dynamique

---

## 4. 🧠 Concepts fondamentaux

### 🔹 Event

Un événement = fait métier :

* paiement effectué
* consommation mesurée
* utilisateur connecté

### 🔹 Topic

Flux logique d’événements

### 🔹 Partition

Division pour parallélisme

### 🔹 Offset

Position dans le flux

---

## 5. ⚙️ Kafka en production (CRITIQUE)

### ✔ Bonnes pratiques

* Toujours définir stratégie de partition
* Replication factor ≥ 3
* Monitoring obligatoire
* Schéma structuré (Avro/Protobuf)
* Idempotence activée

### ❌ Mauvaises pratiques

* Topics non gouvernés
* Pas de monitoring
* Pas de stratégie de retry
* Consumers non scalables
* Messages non structurés

---

## 6. 🔥 Retour d’expérience (REX réel)

### REX 1 — Banque

❌ problème : perte de messages
Cause : pas de replication + broker unique
✔ correction : cluster multi-brokers + ISR

---

### REX 2 — Énergie

❌ problème : latence critique
Cause : mauvaise partition key
✔ correction : redesign event model

---

## 7. 💡 Tips experts

* Kafka ≠ base de données
* Kafka = journal distribué
* Toujours penser "event first"
* Observer consumer lag = KPI critique
* Tester panne volontairement

---

## 🎁 LIVRABLE JOUR 0

* Glossaire Kafka complet
* Checklist production-ready
* Architecture cible SI événementiel

---

# 🗓️ JOUR 1 — INTRODUCTION & ENVIRONNEMENT

## 🎯 Objectif

Installer, comprendre et exécuter Kafka localement.

---

## 📚 Concepts détaillés

* Broker Kafka
* Producer / Consumer
* Topic creation
* CLI Kafka

---

## 🧪 Atelier

* Installation Docker Kafka
* Création cluster local
* Envoi de messages simples

---

## ⚠️ erreurs fréquentes

* Kafka lancé sans réseau correct
* Topics sans partition
* Consumer non groupé

---

## 🎁 livrable

* cluster local fonctionnel

---

# 🗓️ JOUR 2 — ARCHITECTURE INTERNE

## 🎯 Objectif

Comprendre le fonctionnement interne profond.

---

## 📚 concepts avancés

* Leader / follower
* ISR (In-Sync Replica)
* KRaft vs Zookeeper
* réplication synchrone vs asynchrone

---

## 🧪 atelier

* créer topic multi-partitions
* simuler crash broker

---

## ⚠️ erreurs

* replication factor = 1 (danger production)
* mauvaise configuration ISR

---

## 🎁 livrable

* cluster tolérant aux pannes

---

# 🗓️ JOUR 3 — PRODUCER AVANCÉ

## 🎯 objectif

Créer producteurs performants et fiables.

---

## 📚 concepts

* batching
* compression (gzip/snappy)
* retries
* idempotence
* acks (0, 1, all)

---

## 🧪 atelier

* producer Java haute performance
* benchmark throughput

---

## ⚠️ erreurs

* ack=0 en production
* pas de retry
* messages trop lourds

---

## 🎁 livrable

* producer optimisé production

---

# 🗓️ JOUR 4 — CONSUMER AVANCÉ

## 🎯 objectif

Consommation scalable et fiable

---

## 📚 concepts

* consumer group
* rebalance
* offset commit
* parallel consumption

---

## 🧪 atelier

* multi consumers
* crash simulation

---

## 🎁 livrable

* système scalable

---

# 🗓️ JOUR 5 — SCHEMA REGISTRY

## 🎯 objectif

Industrialiser les données

---

## 📚 concepts

* Avro / Protobuf
* compatibilité backward/forward
* schema evolution

---

## 🧪 atelier

* evolution schema sans casse

---

# 🗓️ JOUR 6 — KAFKA STREAMS

## 🎯 objectif

Traitement temps réel

---

## 📚 concepts

* KStream / KTable
* stateful processing
* windowing

---

## 🧪 atelier

* calcul consommation énergie

---

Parfait — on va passer en **mode architecture & expertise DSI**.

Voici le **détail approfondi des jours 7 à 21** du bootcamp Kafka sur Apache Kafka, avec **objectifs, concepts avancés, ateliers, erreurs critiques, patterns industriels et livrables**.

---

# 🗓️ JOUR 7 — MINI PROJET 1 (SMART METER / IOT TEMPS RÉEL)

## 🎯 Objectif

Construire un pipeline complet de streaming **end-to-end**.

---

## 📚 Architecture cible

* IoT / capteurs → Producer
* Kafka Topics → transport événementiel
* Kafka Streams → traitement
* Consumer → stockage / dashboard

---

## 🧠 Concepts clés

* Event ingestion haute fréquence
* Découplage total des systèmes
* Traitement streaming vs batch

---

## 🧪 Atelier

* Simuler capteurs énergie (consommation)
* Envoyer 1000 events/sec
* Agrégation par zone / compteur

---

## ⚠️ erreurs fréquentes

* Pas de partition strategy → goulot d’étranglement
* Payload trop lourd
* Pas de throttling producer

---

## 🎁 livrable

* Pipeline IoT complet fonctionnel

---

# 🗓️ JOUR 8 — INTRODUCTION ksqlDB

→ ksqlDB

## 🎯 Objectif

Faire du **SQL sur des flux Kafka en temps réel**

---

## 📚 Concepts

* Stream = table infinie
* SELECT en continu
* filtering live

---

## 🧪 Atelier

* créer stream consommation énergie
* requête temps réel :

```sql
SELECT zone, AVG(consommation)
FROM energie_stream
WINDOW TUMBLING (1 MINUTE)
GROUP BY zone;
```

---

## ⚠️ erreurs

* confusion stream vs table
* absence de clé de partition

---

## 🎁 livrable

* dashboard temps réel simple

---

# 🗓️ JOUR 9 — KSQLDB AVANCÉ

## 🎯 Objectif

Passer du simple stream à **analytics avancé**

---

## 📚 concepts

* JOIN streams
* fenêtres temporelles avancées
* alerting rules

---

## 🧪 atelier

* détection anomalie consommation
* comparaison 2 zones

---

## ⚠️ erreurs

* jointures non indexées
* surcharge CPU streaming

---

## 🎁 livrable

* système de détection anomalie temps réel

---

# 🗓️ JOUR 10 — KAFKA CONNECT (INTÉGRATION SI)

→ Kafka Connect

## 🎯 objectif

Connecter Kafka à des systèmes externes

---

## 📚 concepts

* Source Connector (DB → Kafka)
* Sink Connector (Kafka → DB)
* connect distributed mode

---

## 🧪 atelier

* MySQL → Kafka
* Kafka → Elasticsearch

---

## ⚠️ erreurs

* connect non scalable
* absence retry policy
* mapping incorrect

---

## 🎁 livrable

* pipeline d’intégration SI

---

# 🗓️ JOUR 11 — CONNECT AVANCÉ

## 🎯 objectif

Industrialiser Kafka Connect

---

## 📚 concepts

* SMT (Single Message Transform)
* error handling (DLQ)
* schema mapping

---

## 🧪 atelier

* transformation payload
* filtrage données sensibles

---

## ⚠️ erreurs

* transformations trop lourdes
* absence DLQ

---

## 🎁 livrable

* pipeline robuste production

---

# 🗓️ JOUR 12 — CDC AVEC DEBEZIUM

→ Debezium

## 🎯 objectif

Capturer les changements base de données en temps réel

---

## 📚 concepts

* log-based CDC (binlog / WAL)
* event sourcing DB
* outbox pattern

---

## 🧪 atelier

* MySQL CDC → Kafka topics
* capture INSERT / UPDATE / DELETE

---

## ⚠️ erreurs

* surcharge DB
* mauvaise configuration binlog

---

## 🎁 livrable

* CDC fonctionnel temps réel

---

# 🗓️ JOUR 13 — CDC AVANCÉ

## 🎯 objectif

Architecture microservices événementielle

---

## 📚 concepts

* outbox pattern
* eventual consistency
* data synchronization

---

## 🧪 atelier

* CRM → Billing sync
* simulation microservices découplés

---

## ⚠️ erreurs

* double écriture
* incohérence données

---

## 🎁 livrable

* architecture microservices event-driven

---

# 🗓️ JOUR 14 — MINI PROJET 2 (SI ENTREPRISE)

## 🎯 Cas réel

* CRM
* Billing
* Payment system

---

## 🧪 architecture

* Debezium CDC
* Kafka Connect
* ksqlDB enrichment
* consumers microservices

---

## 🎁 livrable

* système intégré temps réel

---

# 🗓️ JOUR 15 — EVENT-DRIVEN ARCHITECTURE

## 🎯 objectif

Passer niveau architecte

---

## 📚 concepts

* Event sourcing
* CQRS
* event-driven design

---

## 🧪 atelier

* modélisation SI énergie complet

---

## ⚠️ erreurs

* confusion event vs message
* surcharge event bus

---

## 🎁 livrable

* architecture EDA complète

---

# 🗓️ JOUR 16 — PERFORMANCE & SCALING

## 🎯 objectif

Optimiser Kafka en production

---

## 📚 concepts

* partition strategy avancée
* throughput tuning
* batching optimization

---

## 🧪 atelier

* benchmark 100k msg/sec

---

## ⚠️ erreurs

* mauvaise clé partition
* brokers sous-dimensionnés

---

## 🎁 livrable

* Kafka optimisé performance

---

# 🗓️ JOUR 17 — SÉCURITÉ

## 🎯 objectif

Sécuriser cluster Kafka

---

## 📚 concepts

* SSL encryption
* SASL authentication
* ACL authorization

---

## 🧪 atelier

* cluster sécurisé multi-users

---

## 🎁 livrable

* Kafka sécurisé production

---

# 🗓️ JOUR 18 — ADMINISTRATION

## 🎯 objectif

Exploiter Kafka en production

---

## 📚 concepts

* cluster multi-broker
* replication factor
* retention policies

---

## 🧪 atelier

* scaling cluster
* failover simulation

---

## 🎁 livrable

* cluster production-ready

---

# 🗓️ JOUR 19 — MONITORING

→ Prometheus
→ Grafana

## 🎯 objectif

Surveiller Kafka en temps réel

---

## 📚 métriques clés

* consumer lag
* throughput
* broker health
* partition skew

---

## 🧪 atelier

* dashboard monitoring complet

---

## 🎁 livrable

* supervision production

---

# 🗓️ JOUR 20 — TROUBLESHOOTING

## 🎯 objectif

Gérer incidents critiques

---

## 📚 scénarios

* broker down
* consumer lag élevé
* perte de messages
* saturation disque

---

## 🧪 atelier

* incident simulation + recovery

---

## 🎁 livrable

* runbook exploitation

---

# 🗓️ JOUR 21 — PROJET FINAL EXPERT

## 🎯 objectif

Architecture complète DSI

---

## 🏗️ architecture finale

* Kafka cluster HA
* Debezium CDC
* Kafka Connect pipelines
* ksqlDB analytics
* microservices consumers
* monitoring Grafana

---

## 🧪 cas réel

👉 Smart Grid énergie / Telco / Banque

---

## 📦 livrables finaux

* architecture diagramme
* code complet
* pipelines
* dashboards
* documentation exploitation

---

# 🧠 RÉSULTAT FINAL

Tu es capable de :

* concevoir une plateforme streaming entreprise
* gérer Kafka en production critique
* intégrer SI complexes (ERP, IoT, CRM)
* piloter une architecture événementielle complète

---


---

---

