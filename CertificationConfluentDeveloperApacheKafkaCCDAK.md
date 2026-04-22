# 📘 Guide complet – Certification Developer (CCDAK) Apache Kafka

*(Objectifs, thèmes, conditions + 20 questions type examen corrigées)*

---

## 🔎 Introduction détaillée

Dans les architectures modernes, la capacité à traiter les données **en temps réel** est devenue un avantage stratégique majeur. Les entreprises (banques, télécoms, e-commerce, énergie, IoT…) ont besoin de systèmes capables de :

* 📡 traiter des flux continus de données
* ⚡ réagir instantanément (temps réel)
* 🔄 découpler les applications
* 📊 alimenter des plateformes data et IA

C’est dans ce contexte que Apache Kafka s’impose comme une **technologie centrale**.

---

### 🧠 Pourquoi cette certification est importante ?

La certification **Developer (CCDAK)** proposée par Confluent permet de valider ta capacité à :

* développer des applications basées sur Kafka
* maîtriser les mécanismes internes (partitions, offsets, consumer groups)
* gérer la fiabilité et la performance
* implémenter du traitement de données en temps réel

👉 Elle constitue une **référence mondiale** pour les développeurs travaillant sur :

* microservices
* event-driven architecture
* data streaming
* systèmes distribués

---

### 🎯 À qui s’adresse cette certification ?

Cette certification est idéale pour :

* 👨‍💻 Développeurs backend (Java, Python, Node.js)
* 🧑‍💻 Data engineers
* 🏗️ Architectes techniques (orientés développement)
* ⚙️ Ingénieurs logiciels travaillant sur systèmes distribués

---

### 🚀 Objectif de ce guide

Ce document te permet de :

* comprendre **les attentes de l’examen**
* maîtriser **les concepts clés testés**
* t’entraîner avec **20 questions proches du réel**
* identifier **les pièges fréquents**

👉 Si tu maîtrises ce contenu + pratique, tu es prêt à passer l’examen.

---

# 🎯 1. Présentation de la certification CCDAK

## 🧠 Objectif

Valider ta capacité à :

* Développer des applications Kafka
* Produire et consommer des messages efficacement
* Gérer le streaming temps réel

---

## 👨‍💻 Cible

* Développeurs (Java, Python, Node.js)
* Backend engineers
* Data engineers début/intermédiaire
* Architectes techniques (niveau dev)

---

## 📚 Thèmes officiels

### 🔹 1. Kafka Fundamentals

* Topics, partitions
* Brokers, cluster
* Replication

### 🔹 2. Producers

* Envoi de messages
* Clé / partitionnement
* Retry, ack

### 🔹 3. Consumers

* Consumer groups
* Offset management
* Rebalancing

### 🔹 4. Data Processing

* Kafka Streams
* Transformations

### 🔹 5. Data Integration

* Kafka Connect
* Source / Sink

### 🔹 6. Configuration & Reliability

* Performance
* Fault tolerance
* Delivery guarantees

---

## 📊 Format examen

* ⏱️ Durée : 90 minutes
* ❓ Questions : ~60 QCM
* 🎯 Score minimum : **70%**
* 🌐 Langue : Anglais
* 💻 Mode : en ligne (proctoring)
* 💰 Prix : ~**150 USD (~90 000 FCFA)**
* 📅 Validité : 2 ans

---
Voici le programme détaillé de la certification **Confluent Certified Developer for Apache Kafka (CCDAK)**.  
Cette certification s’adresse aux développeurs et architectes qui conçoivent et maintiennent des applications de streaming avec Apache Kafka.  
L’examen couvre à la fois les fondamentaux du courtier de messages, les API producteur/consommateur, Kafka Streams, Kafka Connect, les tests et l’observabilité.  
Voici le plan des thèmes évalués, avec leur pondération approximative.

---

# Programme détaillé – Certification CCDAK (Apache Kafka)

## Récapitulatif de l’examen

| Caractéristique | Détail |
| :--- | :--- |
| **Code** | CCDAK |
| **Durée** | 90 minutes |
| **Nombre de questions** | 60 (QCM / QRM) |
| **Tarif** | 150 USD |
| **Score de passage** | ~70 % (mention *Pass/Fail*) |

---

## Pondération des thèmes

| Thème | Poids |
| :--- | :--- |
| 1. Fondamentaux d’Apache Kafka | 23 % |
| 2. Développement d’applications Kafka | 28 % |
| 3. Kafka Streams | 12 % |
| 4. Kafka Connect | 15 % |
| 5. Tests d’application | 8 % |
| 6. Observabilité | 13 % |

---

## Détail par thème

### 1. Fondamentaux d’Apache Kafka (23 %)

- **Concepts de base** : topics, partitions, producteurs, consommateurs, offsets.  
- **Architecture d’un cluster** : brokers, réplication, rôles leader/follower.  
- **Métadonnées** : compréhension de **KRaft** (sans ZooKeeper) et de ZooKeeper.  
- **Fiabilité** : ISR (*In-Sync Replicas*), *High Watermark*, paramètres `acks`, `min.insync.replicas`.

### 2. Développement d’applications Kafka (28 %)

- **API Producteur** : configuration (`acks`, `compression.type`, `batch.size`), sérialisation, partitionnement personnalisé, accusés de réception.  
- **API Consommateur** : groupes de consommateurs, stratégies de partitionnement (`RangeAssignor`, `RoundRobinAssignor`), gestion des commits (auto/manuel), isolation `read_committed`.  
- **API Admin** : gestion des topics, partitions et configurations.  
- **Gestion des erreurs** : retry, *dead letter queues*, erreurs de désérialisation.

### 3. Kafka Streams (12 %)

- **Topologies** : *Processor Topology* et DSL (`KStream`, `KTable`, `GlobalKTable`).  
- **Transformations** : `filter`, `map`, `groupBy`, `join`, `aggregate`, fenêtrage (`window`).  
- **État** : *state stores* (RocksDB), persistance et restauration après échec.

### 4. Kafka Connect (15 %)

- **Architecture** : connecteurs source (import) et sink (export).  
- **Configuration** : workers, tâches, convertisseurs (`JsonConverter`, `AvroConverter`).  
- **Avancé** : transformations SMT (*Single Message Transforms*), `errors.tolerance`, *dead letter queues*.

### 5. Tests d’application (8 %)

- **Tests unitaires** : `TopologyTestDriver` pour Kafka Streams (sans cluster réel).  
- **Tests d’intégration** : cluster Kafka embarqué (`EmbeddedKafkaCluster`).

### 6. Observabilité (13 %)

- **Métriques clés** : taux d’erreur producteur, latence des requêtes, *lag* consommateur (`records-lag-max`).  
- **Monitoring** : métriques JMX, logs, surveillance du *state store*.  
- **Optimisation** : identification des goulots d’étranglement, ajustement des configurations.

---

## Ressources recommandées

- **Cours gratuits** : [Confluent Developer](https://developer.confluent.io/) (*Introduction to Events*, *Kafka Internals & Architecture*).  
- **Documentation** : Documentation officielle Confluent (Connect, Streams).  
- **Environnement de test** : `cp-all-in-one` avec Docker.  
- **Exemples de questions** : plateformes comme ExamTopics (pour le format).

---

---

# 🧪 2. 20 Questions type examen (avec corrections détaillées)

---

## ✅ Q1

**Que garantit une partition Kafka ?**

A. Ordre global
B. Ordre par clé
C. Ordre par topic
D. Aucun ordre

👉 ✅ **Réponse : B**

💡 Kafka garantit l’ordre **dans une partition**, donc même clé → même partition → ordre respecté.

---

## ✅ Q2

**Que fait un Consumer Group ?**

A. Duplique les messages
B. Partage la consommation
C. Supprime les messages
D. Compresse les données

👉 ✅ **Réponse : B**

💡 Les consumers d’un même groupe se partagent les partitions.

---

## ✅ Q3

**Que se passe-t-il si 2 consumers > partitions ?**

👉 ✅ Réponse :
Un consumer reste **inactif**

💡 1 partition = 1 consumer actif max.

---

## ✅ Q4

**Ack=all signifie :**

A. Leader only
B. Aucun ack
C. Tous les replicas
D. Retry infini

👉 ✅ **Réponse : C**

💡 Tous les replicas doivent confirmer.

---

## ✅ Q5

**Offset = ?**

👉 ✅ Réponse :
Position d’un message dans une partition

---

## ✅ Q6

**Auto commit = ?**

👉 ✅ Réponse :
Kafka enregistre automatiquement l’offset

⚠️ Risque :

* duplication ou perte

---

## ✅ Q7

**Rebalancing se produit quand ?**

A. Ajout consumer
B. Suppression consumer
C. Crash
D. Tous

👉 ✅ **Réponse : D**

---

## ✅ Q8

**Idempotence producer permet :**

A. Compression
B. Eviter duplications
C. Sécurité
D. Partitionnement

👉 ✅ **Réponse : B**

---

## ✅ Q9

**Exactly-once nécessite :**

👉 ✅ Réponse :
Idempotence + transactions

---

## ✅ Q10

**Kafka Streams sert à :**

👉 ✅ Réponse :
Traitement temps réel

---

## ✅ Q11

**Une clé Kafka permet :**

A. Sécurité
B. Partitionnement
C. Compression
D. Ack

👉 ✅ **Réponse : B**

---

## ✅ Q12

**Retention policy = ?**

👉 ✅ Réponse :
Durée de conservation des messages

---

## ✅ Q13

**Compaction = ?**

👉 ✅ Réponse :
Garder la dernière valeur par clé

---

## ✅ Q14

**Kafka Connect = ?**

👉 ✅ Réponse :
Intégration avec systèmes externes

---

## ✅ Q15

**Consumer lag = ?**

👉 ✅ Réponse :
Retard de consommation

---

## ✅ Q16

**Si un broker tombe :**

👉 ✅ Réponse :
Un replica devient leader

---

## ✅ Q17

**Partition key impacte :**

👉 ✅ Réponse :
Distribution + ordre

---

## ✅ Q18

**Batching permet :**

👉 ✅ Réponse :
Améliorer performance

---

## ✅ Q19

**At least once = ?**

👉 ✅ Réponse :
Pas de perte, duplication possible

---

## ✅ Q20

**At most once = ?**

👉 ✅ Réponse :
Pas de duplication, perte possible

---

# 🧠 Résumé des pièges fréquents

* Mauvaise gestion des offsets
* Confusion entre garanties (at least / exactly once)
* Mauvaise compréhension des consumer groups
* Ignorer le rebalancing

---

# 🚀 Conclusion

👉 Avec ce guide :

* 📚 Tu comprends les attentes réelles
* 🧪 Tu t’entraînes sur des cas concrets
* 🎯 Tu te rapproches fortement du niveau certification

---

# 🧪 📘 40 Questions avancées (niveau expert) – Certification Developer (CCDAK)

*(QCM A–E + cas pratiques + réponses détaillées + tips + bonnes pratiques + définitions)*
Basé sur Apache Kafka et les standards Confluent

---

## 🔎 Introduction

Ces questions reproduisent le **niveau réel (voire supérieur)** de l’examen CCDAK.
👉 Chaque question est basée sur un **cas pratique réel**, avec 5 options (A–E).
👉 L’objectif est de tester :

* ta compréhension **profonde**
* ta capacité à **raisonner en production**
* ton niveau **architecte développeur**

---

# 🧠 PARTIE 1 – PRODUCERS & DELIVERY

---

## ✅ Q1

Une application de paiement critique envoie des transactions vers Kafka. Tu dois garantir qu’aucune donnée ne soit perdue même en cas de panne réseau ou broker.

A. acks=1
B. acks=0
C. acks=all + retries
D. retries uniquement
E. compression activée

👉 ✅ **Réponse : C**

💬 **Commentaire :**
acks=all garantit que tous les replicas confirment. retries assure la résilience.

💡 **Tip :** ajouter `enable.idempotence=true`
📌 **Bonne pratique :** configurer `min.insync.replicas ≥ 2`
📖 **Définition :** *acks = niveau de garantie d’écriture*

---

## ✅ Q2

Un système e-commerce envoie des commandes sans clé Kafka. Tu observes une perte d’ordre logique.

A. Augmenter partitions
B. Ajouter clé métier
C. Activer compression
D. Réduire batch
E. Activer retries

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Sans clé → distribution aléatoire → perte d’ordre métier.

💡 **Tip :** utiliser userId ou orderId
📌 **Bonne pratique :** définir stratégie de partitionnement
📖 **Définition :** *clé = déterminant de partition*

---

## ✅ Q3

Un producer IoT envoie beaucoup de petits messages et subit une latence réseau élevée.

A. Désactiver batching
B. Activer linger.ms + batching
C. Réduire retries
D. Désactiver compression
E. Réduire partitions

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Batching améliore le throughput en regroupant les messages.

💡 **Tip :** linger.ms = délai d’attente batch
📌 **Bonne pratique :** équilibrer latence / performance
📖 **Définition :** *batching = regroupement messages*

---

## ✅ Q4

Un système bancaire exige exactement une seule livraison de message.

A. acks=1
B. retries=0
C. idempotence seule
D. transactions + idempotence
E. compression

👉 ✅ **Réponse : D**

💬 **Commentaire :**
Exactly-once nécessite transactions + idempotence.

💡 **Tip :** utiliser transactional.id
📌 **Bonne pratique :** tester crash recovery
📖 **Définition :** *exactly-once = sans perte ni duplication*

---

## ✅ Q5

Un producer surcharge le broker et génère des timeouts fréquents.

A. Augmenter buffer.memory
B. Réduire retries
C. Désactiver ack
D. Augmenter partitions uniquement
E. Désactiver compression

👉 ✅ **Réponse : A**

💬 **Commentaire :**
buffer.memory gère la capacité d’envoi côté producer.

💡 **Tip :** surveiller backpressure
📌 **Bonne pratique :** monitorer métriques producer
📖 **Définition :** *backpressure = saturation flux*

---

## ✅ Q6

Tu veux garantir l’ordre même avec retries.

A. retries=0
B. max.in.flight=1
C. compression
D. partitions=1
E. acks=1

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Plusieurs requêtes simultanées cassent l’ordre.

💡 **Tip :** utiliser avec idempotence
📌 **Bonne pratique :** éviter reorder
📖 **Définition :** *in-flight = requêtes non confirmées*

---

## ✅ Q7

Tu veux réduire la taille des messages envoyés.

A. acks=all
B. compression
C. retries
D. batching
E. partition

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Compression réduit trafic réseau.

💡 **Tip :** snappy recommandé
📌 **Bonne pratique :** tester CPU impact
📖 **Définition :** *compression = réduction taille*

---

## ✅ Q8

Tu dois gérer des pics de charge imprévisibles.

A. Désactiver batching
B. Scaling horizontal
C. Réduire topics
D. Désactiver retries
E. Réduire replication

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Kafka scale horizontalement.

💡 **Tip :** ajouter partitions
📌 **Bonne pratique :** capacity planning
📖 **Définition :** *scalabilité = montée en charge*

---

## ✅ Q9

Tu veux éviter duplication en cas de retry.

A. retries=0
B. idempotence=true
C. acks=1
D. compression
E. partitions=1

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Idempotence empêche duplication.

💡 **Tip :** activé par défaut récent
📌 **Bonne pratique :** toujours activer
📖 **Définition :** *idempotence = effet unique*

---

## ✅ Q10

Tu veux haute disponibilité des données.

A. replication=1
B. replication=2
C. replication≥3
D. compression
E. batching

👉 ✅ **Réponse : C**

💬 **Commentaire :**
3 replicas = standard production.

💡 **Tip :** tolérance panne 1 broker
📌 **Bonne pratique :** min.insync.replicas=2
📖 **Définition :** *replication = duplication données*

---

# 🧠 PARTIE 2 – CONSUMERS & OFFSETS

---

## ✅ Q11

Un consumer crash avant commit, entraînant duplication.

A. auto commit
B. commit manuel après traitement
C. retries=0
D. partitions=1
E. compression

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Commit après traitement garantit cohérence.

💡 **Tip :** éviter auto commit
📌 **Bonne pratique :** idempotence consumer
📖 **Définition :** *offset = position lecture*

---

## ✅ Q12

Un système critique ne doit pas perdre de messages.

A. at most once
B. at least once
C. exactly once uniquement
D. retries=0
E. compression

👉 ✅ **Réponse : B**

💬 **Commentaire :**
At least once garantit aucune perte.

💡 **Tip :** gérer duplication
📌 **Bonne pratique :** logique idempotente
📖 **Définition :** *delivery semantics*

---

## ✅ Q13

5 consumers pour 3 partitions.

A. Tous actifs
B. 2 inactifs
C. 3 inactifs
D. duplication
E. erreur

👉 ✅ **Réponse : B**

💬 **Commentaire :**
1 partition = 1 consumer actif.

💡 **Tip :** dimensionner partitions
📌 **Bonne pratique :** scaling correct
📖 **Définition :** *consumer group*

---

## ✅ Q14

Lag élevé sur un consumer.

A. réduire partitions
B. scaler consumers
C. désactiver commit
D. réduire retries
E. désactiver ack

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Plus de consumers → traitement parallèle.

💡 **Tip :** surveiller lag
📌 **Bonne pratique :** monitoring
📖 **Définition :** *lag = retard*

---

## ✅ Q15

Rebalancing fréquent.

A. augmenter timeout
B. réduire partitions
C. désactiver consumer
D. compression
E. retries

👉 ✅ **Réponse : A**

💬 **Commentaire :**
Timeout mal configuré → rebalancing.

💡 **Tip :** session.timeout.ms
📌 **Bonne pratique :** stabilité
📖 **Définition :** *rebalancing*

---

## ✅ Q16

Lire depuis début.

A. latest
B. earliest
C. none
D. commit
E. reset

👉 ✅ **Réponse : B**

💬 **Commentaire :**
earliest → début topic.

💡 **Tip :** utile replay
📌 **Bonne pratique :** test env
📖 **Définition :** *offset reset*

---

## ✅ Q17

Multi-applications consomment même topic.

A. même group
B. différents groups
C. même offset
D. duplication
E. erreur

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Chaque group indépendant.

💡 **Tip :** Kafka multi-consumer
📌 **Bonne pratique :** nommage
📖 **Définition :** *group logique*

---

## ✅ Q18

Message bloquant.

A. retry infini
B. DLQ
C. delete message
D. reset offset
E. commit

👉 ✅ **Réponse : B**

💬 **Commentaire :**
DLQ évite blocage pipeline.

💡 **Tip :** gérer erreurs
📌 **Bonne pratique :** retry limité
📖 **Définition :** *DLQ*

---

## ✅ Q19

Traitement long.

A. réduire poll
B. augmenter max.poll.interval
C. réduire offset
D. compression
E. retries

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Sinon rebalancing.

💡 **Tip :** tuning nécessaire
📌 **Bonne pratique :** optimisation code
📖 **Définition :** *poll cycle*

---

## ✅ Q20

Tu veux éviter duplication côté consumer.

A. retries
B. idempotence
C. compression
D. partitions
E. ack

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Traitement idempotent.

💡 **Tip :** clé unique
📌 **Bonne pratique :** stockage état
📖 **Définition :** *idempotence*

---

---

# 🧠 PARTIE 3 – STREAMS & PROCESSING (Q21 → Q30)

---

## ✅ Q21 – Agrégation temps réel de transactions

Une application bancaire reçoit des milliers de transactions par seconde. Tu dois calculer le total des montants par utilisateur en temps réel.

A. map()
B. filter()
C. count()
D. aggregate()
E. commit()

👉 ✅ **Réponse : D. aggregate()**

💬 **Commentaire :**
`aggregate()` permet de faire des calculs d’état (somme, moyenne, etc.) sur un flux continu. Ici, c’est parfait pour additionner les transactions par utilisateur.

💡 **Tip expert :** utiliser un `state store` pour stocker les résultats intermédiaires.
📌 **Bonne pratique :** toujours définir une clé (userId) pour éviter mélange des données.
📖 **Définition :** *Aggregation = opération de regroupement et calcul sur flux.*

---

## ✅ Q22 – Jointure entre deux flux temps réel

Tu dois joindre un flux de commandes et un flux de paiements pour vérifier si chaque commande est payée.

A. filter()
B. join()
C. map()
D. reduce()
E. commit()

👉 ✅ **Réponse : B. join()**

💬 **Commentaire :**
`join()` permet de combiner deux streams en fonction d’une clé commune.

💡 **Tip expert :** toujours définir une **window temporelle** pour éviter des jointures infinies.
📌 **Bonne pratique :** gérer les délais (late events).
📖 **Définition :** *Stream join = fusion de flux sur clé commune.*

---

## ✅ Q23 – Résilience d’un traitement stateful

Ton application Kafka Streams doit survivre à un crash sans perdre les données de calcul intermédiaire.

A. cache uniquement
B. changelog topic + state store
C. retry only
D. compression
E. batch only

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Kafka sauvegarde automatiquement l’état via un **changelog topic**.

💡 **Tip expert :** activer la réplication des state stores.
📌 **Bonne pratique :** monitorer la restauration d’état après restart.
📖 **Définition :** *Stateful processing = traitement avec mémoire interne.*

---

## ✅ Q24 – Filtrage de transactions frauduleuses

Tu dois bloquer les transactions supérieures à 10 000 dans un flux Kafka.

A. map()
B. filter()
C. reduce()
D. join()
E. aggregate()

👉 ✅ **Réponse : B. filter()**

💬 **Commentaire :**
`filter()` permet d’éliminer les messages non conformes.

💡 **Tip expert :** ne jamais modifier les données dans filter, seulement les exclure.
📌 **Bonne pratique :** logger les messages filtrés (audit).
📖 **Définition :** *Filter = sélection conditionnelle.*

---

## ✅ Q25 – Transformation de données

Tu reçois des messages JSON et tu dois extraire uniquement l’ID utilisateur.

A. filter()
B. map()
C. join()
D. aggregate()
E. commit()

👉 ✅ **Réponse : B. map()**

💬 **Commentaire :**
`map()` transforme chaque message individuellement.

💡 **Tip expert :** utiliser pour normalisation des données.
📌 **Bonne pratique :** garder transformation pure (sans état).
📖 **Définition :** *map = transformation 1→1.*

---

## ✅ Q26 – Tolérance aux pannes dans Kafka Streams

Ton pipeline doit continuer à fonctionner même si un nœud tombe.

A. disable replication
B. enable state store only
C. replication + state store + Kafka Streams restore
D. reduce partitions
E. disable commit

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Kafka Streams restaure automatiquement l’état via les logs Kafka.

💡 **Tip expert :** toujours activer la réplication des topics d’état.
📌 **Bonne pratique :** tester crash recovery.
📖 **Définition :** *Fault tolerance = capacité à survivre aux pannes.*

---

## ✅ Q27 – Gestion des événements tardifs

Des événements arrivent en retard dans un flux de paiement et faussent les résultats.

A. ignore events
B. increase batch size
C. grace period + windowing
D. disable streams
E. retry only

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Les fenêtres temporelles avec `grace period` gèrent les événements tardifs.

💡 **Tip expert :** ajuster la fenêtre selon latence réseau.
📌 **Bonne pratique :** définir stratégie out-of-order.
📖 **Définition :** *Late event = événement hors délai attendu.*

---

## ✅ Q28 – Comptage d’événements

Tu dois compter le nombre de clics par page web en temps réel.

A. map()
B. filter()
C. count()
D. join()
E. reduce()

👉 ✅ **Réponse : C. count()**

💬 **Commentaire :**
`count()` est une opération d’agrégation simple et optimisée.

💡 **Tip expert :** nécessite une clé (pageId).
📌 **Bonne pratique :** partitionner par clé métier.
📖 **Définition :** *count = agrégation numérique.*

---

## ✅ Q29 – Détection d’anomalies

Tu dois détecter des pics anormaux dans les transactions financières.

A. filter() simple
B. map()
C. stream + rules ou ML model
D. commit
E. compression

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Les anomalies nécessitent logique avancée (statistique ou ML).

💡 **Tip expert :** combiner Kafka Streams + machine learning.
📌 **Bonne pratique :** stocker historique pour comparaison.
📖 **Définition :** *Anomaly detection = identification comportement anormal.*

---

## ✅ Q30 – Architecture pipeline temps réel

Tu dois concevoir un pipeline complet pour analyser des données IoT en temps réel.

A. DB → API → file batch
B. Producer → Kafka → Streams → Consumer
C. FTP → batch processing
D. REST polling
E. cache only

👉 ✅ **Réponse : B**

💬 **Commentaire :**
C’est l’architecture standard event-driven avec Kafka.

💡 **Tip expert :** découpler chaque couche pour scalabilité.
📌 **Bonne pratique :** monitorer chaque étape du flux.
📖 **Définition :** *Pipeline = chaîne de traitement de données.*

---

# 🏁 Conclusion PARTIE 3

👉 Cette section couvre :

* 🔄 Kafka Streams (map, filter, join, aggregate)
* 📊 processing temps réel
* ⚡ stateful vs stateless
* 🧠 cas réels (banque, IoT, fraude)

---

*
# 🧠 PARTIE 4 – ARCHITECTURE, PRODUCTION & SÉCURITÉ

*(Questions 31 → 40 – niveau expert CCDAK)*
Basé sur Apache Kafka et les pratiques de Confluent

---

## 🔎 Introduction PARTIE 4

Cette partie est la plus proche du **monde réel en production**.
Elle teste ta capacité à comprendre :

* 🏗️ l’architecture distribuée Kafka
* ⚙️ les déploiements en production
* 🔐 la sécurité des flux
* 📊 la supervision et la résilience
* 🚀 les bonnes pratiques enterprise

👉 C’est typiquement le niveau **architecte / senior developer / SRE**

---

# 🧠 Q31 – Architecture haute disponibilité bancaire

Une banque veut construire une plateforme Kafka pour traiter des paiements critiques 24/7. Elle exige aucune perte de données même en cas de panne d’un datacenter.

A. replication=1 + compression
B. replication=2 sans monitoring
C. replication=3 + min.insync.replicas=2 + multi-brokers
D. batch only
E. disable acks

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Une architecture critique nécessite **réplication multiple + quorum d’écriture**.

💡 **Tip expert :** prévoir multi-AZ (zones de disponibilité).
📌 **Bonne pratique :** toujours monitorer ISR (in-sync replicas).
📖 **Définition :** *HA = High Availability*

---

# 🧠 Q32 – Scalabilité IoT massive

Un système IoT envoie des millions d’événements/seconde. Le cluster Kafka doit absorber la charge sans perte.

A. réduire partitions
B. augmenter replication uniquement
C. augmenter partitions + scaling brokers
D. activer compression seule
E. réduire consumers

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Kafka scale horizontalement via **partitions + brokers**.

💡 **Tip expert :** plus de partitions = plus de parallélisme.
📌 **Bonne pratique :** dimensionner partitions dès la conception.
📖 **Définition :** *Scalability = capacité à absorber la charge*

---

# 🧠 Q33 – Intégration systèmes externes

Une entreprise veut connecter une base MySQL à Kafka sans développer de code custom.

A. REST polling
B. Kafka Streams
C. Kafka Connect
D. batch ETL
E. manual export

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Kafka Connect permet intégration standardisée (source/sink).

💡 **Tip expert :** utiliser connecteurs officiels.
📌 **Bonne pratique :** éviter code maison pour intégration.
📖 **Définition :** *Connector = pont entre systèmes*

---

# 🧠 Q34 – Architecture event-driven

Une entreprise veut découpler totalement ses microservices (commande, paiement, livraison).

A. communication REST directe
B. shared database
C. event-driven architecture avec Kafka
D. FTP exchange
E. polling API

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Kafka agit comme **bus d’événements central**.

💡 **Tip expert :** chaque domaine = topic dédié.
📌 **Bonne pratique :** découplage fort des services.
📖 **Définition :** *EDA = Event Driven Architecture*

---

# 🧠 Q35 – Audit et traçabilité

Une entreprise doit conserver toutes les transactions pendant 2 ans pour audit.

A. delete logs immédiatement
B. retention policy Kafka
C. disable topics
D. batch processing only
E. reduce partitions

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Kafka permet la **rétention configurée des données**.

💡 **Tip expert :** combiner retention + compaction.
📌 **Bonne pratique :** adapter retention par type de donnée.
📖 **Définition :** *Retention = durée conservation messages*

---

# 🧠 Q36 – Migration ESB vers Kafka

Une entreprise migre d’un ESB traditionnel vers Kafka pour améliorer performance et scalabilité.

A. remplacer Kafka par FTP
B. transformer flux synchrone en asynchrone
C. supprimer middleware
D. réduire partitions
E. utiliser polling API

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Kafka introduit un modèle **asynchrone événementiel**.

💡 **Tip expert :** migration progressive recommandée.
📌 **Bonne pratique :** hybrid ESB + Kafka temporaire.
📖 **Définition :** *Asynchrone = non bloquant*

---

# 🧠 Q37 – Sécurité Kafka en production

Une entreprise bancaire veut sécuriser totalement son cluster Kafka.

A. aucun chiffrement
B. SSL + SASL + ACL
C. compression uniquement
D. partitions
E. batching

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Sécurité Kafka repose sur **authentification + chiffrement + autorisation**.

💡 **Tip expert :** rotation régulière des credentials.
📌 **Bonne pratique :** principe du moindre privilège.
📖 **Définition :** *ACL = contrôle d’accès*

---

# 🧠 Q38 – Monitoring et observabilité

Une équipe SRE doit surveiller un cluster Kafka en production.

A. logs uniquement
B. monitoring metrics + lag + AKHQ
C. supprimer logs
D. batch processing
E. disable replication

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Monitoring Kafka repose sur métriques + lag + dashboards.

💡 **Tip expert :** alerter sur consumer lag.
📌 **Bonne pratique :** utiliser outils comme AKHQ.
📖 **Définition :** *Observabilité = visibilité système*

---

# 🧠 Q39 – Réduction du couplage système

Une architecture monolithique est transformée pour réduire les dépendances entre services.

A. base de données partagée
B. API directe
C. Kafka comme bus d’événements
D. FTP
E. polling

👉 ✅ **Réponse : C**

💬 **Commentaire :**
Kafka devient le **cœur de communication**.

💡 **Tip expert :** événements métier bien définis.
📌 **Bonne pratique :** éviter couplage direct.
📖 **Définition :** *Couplage = dépendance entre systèmes*

---

# 🧠 Q40 – Pipeline critique en production

Une plateforme critique doit garantir fiabilité, scalabilité et résilience pour des millions d’événements par jour.

A. simple REST API
B. Producer → Kafka → Consumers + monitoring + retries
C. FTP batch
D. polling DB
E. cache only

👉 ✅ **Réponse : B**

💬 **Commentaire :**
Architecture complète event-driven avec résilience intégrée.

💡 **Tip expert :** ajouter alerting + DLQ + retries.
📌 **Bonne pratique :** observabilité complète de bout en bout.
📖 **Définition :** *Pipeline = chaîne de traitement des événements*

---

# 🏁 CONCLUSION PARTIE 4

👉 Cette partie valide ta capacité à :

* 🏗️ concevoir des architectures Kafka réelles
* ⚙️ gérer production et scalabilité
* 🔐 sécuriser les flux critiques
* 📊 superviser un système distribué

---


