

# 🚀 INTRODUCTION GLOBALE : COMPRENDRE KAFKA PAR LA PRATIQUE

Apache Kafka est une plateforme de streaming distribuée utilisée pour :

* transporter des flux de données en temps réel 📡
* découpler les systèmes (microservices) 🔗
* gérer des millions de messages par seconde ⚡

👉 L’objectif de ce guide est de te permettre de comprendre **Kafka comme un flux réel d’entreprise** :

```
Application → Kafka → Autres applications
```

---

# 🧱 1. PHASE AVANT LANCEMENT (PRÉPARATION DU CLUSTER)

## 1. Générer l’UUID du cluster KRaft

🎯 Objectif :
Créer un identifiant unique pour ton cluster Kafka.

📖 Explication :
Kafka en mode KRaft (sans Zookeeper) a besoin d’un identifiant global.

💻 Commande :

```bash
kafka-storage.sh random-uuid
```

📤 Résultat :

```
8a1f2b3c-9d10-4e2f-a111-xxxxxx
```

🔍 Interprétation :
👉 Identité unique du cluster Kafka

💡 Tip :
👉 Ne change jamais cet UUID après formatage

---

## 2. Formater le stockage Kafka

🎯 Objectif :
Initialiser les disques Kafka avant démarrage.

📖 Explication :
Kafka doit structurer ses dossiers de logs.

💻 Commande :

```bash
kafka-storage.sh format -t <UUID> -c config/kraft/server.properties
```

📤 Résultat :

```
Formatting storage directories
```

🔍 Interprétation :
👉 Prépare Kafka à stocker les messages

💡 Tip :
👉 À faire UNE seule fois

---

## 3. Vérifier la configuration

🎯 Objectif :
Comprendre le fonctionnement interne du broker.

📖 Explication :
Fichier critique : ports, logs, rôle broker/controller.

💻 Commande :

```bash
cat config/kraft/server.properties
```

🔍 Interprétation :
👉 Cœur de configuration Kafka

💡 Tip :
👉 Vérifie toujours `9092` (port Kafka)

---

## 4. Créer le dossier de logs

🎯 Objectif :
Définir l’emplacement de stockage des messages.

💻 Commande :

```bash
mkdir -p /tmp/kafka-logs
```

🔍 Interprétation :
👉 Kafka stocke les messages physiquement ici

💡 Tip :
👉 En production → disque SSD recommandé

---

## 5. Vérifier la version Kafka

🎯 Objectif :
S’assurer de compatibilité outils.

💻 Commande :

```bash
kafka-topics.sh --version
```

📤 Résultat :

```
3.7.0
```

💡 Tip :
👉 Toujours aligner client et broker versions

---

## 🧠 CONCLUSION PHASE 1

👉 Ici tu as préparé le terrain :

* identité du cluster
* stockage
* configuration

Sans cette phase → Kafka ne peut pas démarrer.

---

# ⚙️ 2. PHASE DÉMARRAGE DU CLUSTER

## 6. Démarrer Kafka Server

🎯 Objectif :
Lancer le broker Kafka.

📖 Explication :
C’est le serveur qui reçoit et distribue les messages.

💻 Commande :

```bash
kafka-server-start.sh config/kraft/server.properties
```

📤 Résultat :

```
Kafka Server started
```

💡 Tip :
👉 Toujours vérifier logs au démarrage

---

## 7. Vérifier que Kafka écoute

🎯 Objectif :
Confirmer que Kafka est actif.

💻 Commande :

```bash
netstat -tulnp | grep 9092
```

📤 Résultat :

```
LISTEN 9092
```

🔍 Interprétation :
👉 Kafka est prêt à recevoir producteurs

---

## 8. Lire les logs serveur

🎯 Objectif :
Diagnostiquer les erreurs système.

💻 Commande :

```bash
tail -f logs/server.log
```

💡 Tip :
👉 Toujours garder ce terminal ouvert en prod

---

## 🧠 CONCLUSION PHASE 2

👉 Kafka est maintenant actif et prêt à recevoir :

* producers
* consumers

---

# 🧱 3. PHASE TOPICS (STRUCTURE DES DONNÉES)

## 9. Créer un topic

🎯 Objectif :
Créer un canal de messages.

📖 Explication :
Un topic = une file distribuée.

💻 Commande :

```bash
kafka-topics.sh --create \
--topic orders \
--bootstrap-server localhost:9092 \
--partitions 3 \
--replication-factor 1
```

📤 Résultat :

```
Created topic orders
```

💡 Tip :
👉 + partitions = + performance

---

## 10. Lister les topics

🎯 Objectif :
Voir les canaux existants.

💻 Commande :

```bash
kafka-topics.sh --list --bootstrap-server localhost:9092
```

---

## 11. Décrire un topic

🎯 Objectif :
Comprendre sa structure interne.

💻 Commande :

```bash
kafka-topics.sh --describe --topic orders --bootstrap-server localhost:9092
```

🔍 Interprétation :

* leaders
* partitions
* replicas

💡 Tip :
👉 Très utile pour debug production

---

## 12. Supprimer un topic

🎯 Objectif :
Nettoyer un environnement.

💻 Commande :

```bash
kafka-topics.sh --delete --topic orders --bootstrap-server localhost:9092
```

💡 Tip :
👉 Danger en production ⚠️

---

## 🧠 CONCLUSION PHASE 3

👉 Les topics sont le cœur logique de Kafka :

* organisation des flux
* séparation des domaines métier

---

# 📤 4. PHASE PRODUCER (ENVOI DE DONNÉES)

## 13. Producer simple

🎯 Objectif :
Envoyer des messages.

💻 Commande :

```bash
kafka-console-producer.sh --topic orders --bootstrap-server localhost:9092
```

📤 Résultat :
Tu tapes :

```
order1
order2
```

💡 Tip :
👉 Chaque ligne = 1 message

---

## 14. Producer clé/valeur

🎯 Objectif :
Envoyer des messages structurés.

💻 Commande :

```bash
kafka-console-producer.sh \
--topic orders \
--bootstrap-server localhost:9092 \
--property "parse.key=true" \
--property "key.separator=:"
```

📤 Exemple :

```
user1:orderA
user2:orderB
```

🔍 Interprétation :
👉 routing par clé (partition)

💡 Tip :
👉 utile pour e-commerce / banking

---

## 🧠 CONCLUSION PHASE 4

👉 Producer = point d’entrée des données temps réel

---

# 📥 5. PHASE CONSUMER (LECTURE DES DONNÉES)

## 15. Consumer complet

🎯 Objectif :
Lire tout l’historique.

💻 Commande :

```bash
kafka-console-consumer.sh \
--topic orders \
--bootstrap-server localhost:9092 \
--from-beginning
```

💡 Tip :
👉 utile pour audit

---

## 16. Consumer temps réel

🎯 Objectif :
Lire uniquement les nouveaux messages.

💡 Tip :
👉 utilisé en monitoring

---

## 17. Consumer group

🎯 Objectif :
Distribuer charge entre consommateurs.

💻 Commande :

```bash
kafka-console-consumer.sh \
--topic orders \
--bootstrap-server localhost:9092 \
--group billing-group
```

💡 Tip :
👉 scale horizontal automatiquement

---

## 18. Lister consumer groups

💻 Commande :

```bash
kafka-consumer-groups.sh --list --bootstrap-server localhost:9092
```

---

## 19. Analyser un consumer group

🎯 Objectif :
Voir retard de traitement.

💻 Commande :

```bash
kafka-consumer-groups.sh \
--describe --group billing-group \
--bootstrap-server localhost:9092
```

🔍 Interprétation :

* lag élevé = problème

💡 Tip :
👉 KPI critique en production

---

## 🧠 CONCLUSION PHASE 5

👉 Consumer = cerveau de traitement des données

---

# 🔧 6. MONITORING & OFFSET

## 20. Lire les offsets

🎯 Objectif :
Voir progression des consumers.

💻 Commande :

```bash
kafka-run-class.sh kafka.tools.GetOffsetShell \
--broker-list localhost:9092 \
--topic orders
```

🔍 Interprétation :

```
orders:0:15
```

👉 15 messages déjà traités

💡 Tip :
👉 essentiel pour debugging production

---

# 🎯 CONCLUSION GLOBALE

Kafka fonctionne comme un **système nerveux numérique** :

```
Producer → Topic → Partition → Consumer Group
```

### 🔥 Concepts clés retenus :

* Topic = canal
* Partition = parallélisme
* Offset = position lecture
* Consumer group = scalabilité
* Broker = serveur Kafka

---

# 🚀 TIPS EXPERT (TRÈS IMPORTANT)

💡 Toujours :

* surveiller les logs
* utiliser consumer groups
* éviter suppression topics en prod
* bien dimensionner partitions

💡 En entreprise :
Kafka est utilisé pour :

* paiement bancaire 💳
* log système 📊
* IoT 📡
* microservices 🧩

---


---

# 🚀 INTRODUCTION GLOBALE : Mise en Pratique  KAFKA + AKHQ  UI supervision

Tu vas simuler une vraie plateforme data streaming :

```text
Applications → Kafka → Consumers → AKHQ (supervision)
```

AKHQ est ton **cockpit de contrôle Kafka**.

---

# ⚙️ TP 1 — DÉMARRER KAFKA (CLUSTER KRAFT)

## 🎯 Objectif

Lancer le moteur Kafka

## 🪜 Actions

1. Ouvre terminal 1
2. Va dans dossier Kafka
3. Formate le storage (une seule fois)
4. Lance le broker

## 💻 Commandes

```bash
kafka-storage.sh random-uuid
kafka-storage.sh format -t <UUID> -c config/kraft/server.properties
kafka-server-start.sh config/kraft/server.properties
```

## 👀 Résultat

```
Kafka Server started
```

## 🔍 Interprétation

Kafka est prêt à recevoir producteurs et consommateurs

## 💡 Tip

👉 Ne ferme jamais ce terminal

---

# ⚙️ TP 2 — LANCER AKHQ (JAVA -JAR)

## 🎯 Objectif

Démarrer interface web Kafka

## 🪜 Actions

1. Ouvre nouveau terminal
2. Va dans dossier AKHQ
3. Lance le jar

## 💻 Commande

```bash
java -jar akhq-0.24.0-all.jar
```

## 👀 Résultat

```
AKHQ started on http://localhost:8080
```

## 🌐 Action navigateur

👉 Ouvre :

```
http://localhost:8080
```

## 🔍 Interprétation

Interface Kafka opérationnelle

## 💡 Tip

👉 Toujours lancer Kafka AVANT AKHQ

---

# ⚙️ TP 3 — CRÉER UN TOPIC

## 🎯 Objectif

Créer canal de messages

## 🪜 Actions

1. Ouvre terminal
2. Exécute commande create topic
3. Vérifie dans AKHQ

## 💻 Commande

```bash
kafka-topics.sh --create --topic orders --bootstrap-server localhost:9092 --partitions 3
```

## 👀 Résultat

```
Created topic orders
```

## 🔍 AKHQ

👉 Topic visible dans interface

## 💡 Tip

👉 3 partitions = base du parallélisme

---

# ⚙️ TP 4 — PRODUCER (ENVOI DE MESSAGES)

## 🎯 Objectif

Envoyer événements dans Kafka

## 🪜 Actions

1. Ouvre terminal
2. Lance producer
3. Tape messages

## 💻 Commande

```bash
kafka-console-producer.sh --topic orders --bootstrap-server localhost:9092
```

## ✍️ Actions utilisateur

Tape :

```
order1
order2
order3
```

## 👀 Résultat AKHQ

Messages visibles instantanément

## 🔍 Interprétation

Chaque ligne = 1 événement

## 💡 Tip

👉 Kafka = log append-only

---

# ⚙️ TP 5 — CONSUMER SIMPLE

## 🎯 Objectif

Lire messages

## 🪜 Actions

1. Ouvre terminal
2. Lance consumer
3. Observer flux

## 💻 Commande

```bash
kafka-console-consumer.sh --topic orders --from-beginning --bootstrap-server localhost:9092
```

## 👀 Résultat

```
order1
order2
```

## 🔍 Interprétation

Lecture complète historique

## 💡 Tip

👉 utile pour debug

---

# ⚙️ TP 6 — VISUALISATION AKHQ

## 🎯 Objectif

Voir messages sans CLI

## 🪜 Actions

1. Ouvre AKHQ
2. Clique topic orders
3. Onglet "Messages"

## 👀 Résultat

Messages affichés UI

## 🔍 Interprétation

AKHQ = observabilité Kafka

## 💡 Tip

👉 outil indispensable en prod

---

# ⚙️ TP 7 — CONSUMER GROUP

## 🎯 Objectif

Tester scalabilité

## 🪜 Actions

1. Lance consumer group
2. Observe répartition

## 💻 Commande

```bash
kafka-console-consumer.sh --topic orders --group billing-group --bootstrap-server localhost:9092
```

## 👀 AKHQ

* group visible
* offsets affichés

## 🔍 Interprétation

Kafka distribue charge automatiquement

## 💡 Tip

👉 base microservices scaling

---

# ⚙️ TP 8 — MULTI CONSUMERS

## 🎯 Objectif

Tester parallélisme

## 🪜 Actions

1. Ouvre 3 terminaux
2. Lance consumer dans chacun
3. Observe distribution

## 👀 Résultat

Messages répartis

## 🔍 Interprétation

Partitioning actif

## 💡 Tip

👉 scaling horizontal natif Kafka

---

# ⚙️ TP 9 — PRODUCER KEY/VALUE

## 🎯 Objectif

Routing intelligent

## 🪜 Actions

1. Lancer producer clé/valeur
2. Envoyer messages structurés

## 💻 Commande

```bash
kafka-console-producer.sh --topic orders --property "parse.key=true" --property "key.separator=:"
```

## ✍️ Exemple

```
user1:orderA
user2:orderB
```

## 🔍 Interprétation

Même clé → même partition

## 💡 Tip

👉 essentiel e-commerce / banking

---

# ⚙️ TP 10 — MONITORING AKHQ (LAG)

## 🎯 Objectif

Voir retard consommation

## 🪜 Actions

1. Ouvre AKHQ
2. Consumer Groups
3. Regarde lag

## 🔍 Interprétation

* lag = messages non traités

## 💡 Tip

👉 KPI critique production

---

# ⚙️ TP 11 — SUPPRESSION TOPIC

## 🎯 Objectif

Nettoyage cluster

## 🪜 Actions

1. Stop producer/consumer
2. Supprimer topic
3. Vérifier AKHQ

## 💻 Commande

```bash
kafka-topics.sh --delete --topic orders --bootstrap-server localhost:9092
```

## 👀 Résultat

Topic disparaît

## ⚠️ Warning

Danger en production

---

# ⚙️ TP 12 — MULTI-TOPICS ARCHITECTURE

## 🎯 Objectif

Simuler entreprise

## 🪜 Actions

Créer topics :

```
orders
payments
inventory
```

## 🔍 Interprétation

Architecture event-driven

## 💡 Tip

👉 base microservices modernes

---

# ⚙️ TP 13 — MONITORING CLUSTER AKHQ

## 🎯 Objectif

Superviser Kafka

## 🪜 Actions

1. Ouvrir AKHQ
2. Aller brokers
3. Vérifier health

## 👀 Résultat

Cluster status OK

## 💡 Tip

👉 AKHQ = mini Grafana Kafka

---

# ⚙️ TP 14 — SIMULATION PANNE

## 🎯 Objectif

Tester résilience Kafka

## 🪜 Actions

1. Stop consumer
2. Envoyer messages
3. Redémarrer consumer
4. Observer reprise

## 🔍 Interprétation

Kafka stocke tout

## 💡 Tip

👉 Kafka = système durable (log)

---

# ⚙️ TP 15 — ARCHITECTURE ENTREPRISE COMPLETE

## 🎯 Objectif

Simuler système réel

## 🪜 Actions

1. Créer topics
2. Lancer producers
3. Lancer consumers
4. Observer AKHQ

## 📡 Flux

```text
Order Service → Kafka → Payment → Inventory → AKHQ
```

## 🔍 Interprétation

Architecture event-driven complète

## 💡 Tip

👉 utilisé en banque, e-commerce, IoT

---

# 🧠 CONCLUSION GLOBALE

Après ces 15 TP tu maîtrises :

✔ Kafka cluster
✔ Producer / Consumer
✔ Consumer groups
✔ Partitions
✔ Offsets
✔ AKHQ (Java -jar)
✔ Monitoring production
✔ Architecture microservices

---


