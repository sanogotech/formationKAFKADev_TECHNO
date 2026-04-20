# 🚀 Guide complet : Installation, lancement et tests avancés de Apache Kafka 3.9.2 sous Windows (Single Node + Cluster 3 nœuds + Python)

---

## 📌 Introduction

Dans un contexte d’architecture moderne (microservices, streaming, IoT), Apache Kafka est devenu un **pilier pour la gestion de flux de données en temps réel**.

Ce guide te propose une approche **progressive et professionnelle** :

✔ Installation et démarrage (mode KRaft sans Apache ZooKeeper)
✔ Mise en place d’un **cluster Kafka 3 nœuds**
✔ Tests complets avec Producer / Consumer
✔ Script **Python avancé avec logs + 10 cas de test métiers**

---

# 🧭 1. Prérequis

### 🔧 Installer :

* Java JDK 11 ou 17

```bash
java -version
```

---

# 📦 2. Installation Kafka 3.9.2

1. Télécharger depuis Apache Software Foundation
2. Extraire dans :

```
C:\kafka
```

---

# ⚙️ 3. Mode KRaft (recommandé)

Kafka fonctionne sans ZooKeeper 👍

---

# 🔑 4. Initialisation (obligatoire)

```bash
bin\windows\kafka-storage.bat random-uuid
```

```bash
bin\windows\kafka-storage.bat format -t <UUID> -c config\kraft\server.properties
```

---

# 🚀 5. Démarrage (Single Node)

```bash
bin\windows\kafka-server-start.bat config\kraft\server.properties
```

---

# 🧪 6. Test rapide

```bash
kafka-topics.bat --create --topic test-topic --bootstrap-server localhost:9092
```

---

# 🧱 7. 🔥 Cluster Kafka 3 nœuds (KRaft)

## 📁 Créer 3 configs :

```
config\kraft\server1.properties
config\kraft\server2.properties
config\kraft\server3.properties
```

---

## ✏️ Exemple config node 1

```properties
process.roles=broker,controller
node.id=1
listeners=PLAINTEXT://localhost:9092
controller.quorum.voters=1@localhost:9093,2@localhost:9095,3@localhost:9097
controller.listener.names=CONTROLLER
listeners=PLAINTEXT://localhost:9092,CONTROLLER://localhost:9093
log.dirs=C:/kafka/logs-1
```

---

## ✏️ Node 2

```properties
node.id=2
listeners=PLAINTEXT://localhost:9094,CONTROLLER://localhost:9095
log.dirs=C:/kafka/logs-2
```

---

## ✏️ Node 3

```properties
node.id=3
listeners=PLAINTEXT://localhost:9096,CONTROLLER://localhost:9097
log.dirs=C:/kafka/logs-3
```

---

## 🔁 Formatage (une seule fois avec même UUID)

```bash
kafka-storage.bat format -t <UUID> -c server1.properties
kafka-storage.bat format -t <UUID> -c server2.properties
kafka-storage.bat format -t <UUID> -c server3.properties
```

---

## ▶️ Démarrage cluster

```bash
kafka-server-start.bat server1.properties
kafka-server-start.bat server2.properties
kafka-server-start.bat server3.properties
```

---

## 🧪 Test cluster

```bash
kafka-topics.bat --create \
--topic cluster-topic \
--bootstrap-server localhost:9092 \
--partitions 3 \
--replication-factor 3
```

---

# 🐍 8. Script Python COMPLET (Producer + Consumer + Logs)

👉 Installer :

```bash
pip install kafka-python
```

---

## 📄 Code complet

```python
import json
import logging
import time
from kafka import KafkaProducer, KafkaConsumer

# ========================
# CONFIGURATION LOGS
# ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

TOPIC = "test-topic"
BOOTSTRAP_SERVERS = ['localhost:9092']

# ========================
# PRODUCER
# ========================
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# ========================
# CAS DE TEST (10 USE CASES)
# ========================
messages = [
    {"type": "CREATE_STOCK", "product": "Riz", "qty": 100},
    {"type": "UPDATE_STOCK", "product": "Sucre", "qty": 50},
    {"type": "DELETE_STOCK", "product": "Huile"},
    {"type": "ALERT_LOW_STOCK", "product": "Sel", "qty": 5},
    {"type": "TRANSFER", "from": "A", "to": "B", "qty": 20},
    {"type": "INVENTORY_CHECK", "warehouse": "Abidjan"},
    {"type": "ERROR_CASE", "code": 500},
    {"type": "HIGH_VOLUME", "qty": 10000},
    {"type": "SECURITY_ALERT", "user": "admin"},
    {"type": "SYSTEM_HEALTH", "status": "OK"}
]

# ========================
# ENVOI DES MESSAGES
# ========================
def send_messages():
    for msg in messages:
        logging.info(f"Envoi message: {msg}")
        producer.send(TOPIC, msg)
        time.sleep(1)

    producer.flush()
    logging.info("Tous les messages ont été envoyés")

# ========================
# CONSUMER
# ========================
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset='earliest',
    group_id='test-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

def consume_messages():
    logging.info("Démarrage consommation...")
    for message in consumer:
        logging.info(f"Message reçu: {message.value}")

# ========================
# EXECUTION
# ========================
if __name__ == "__main__":
    send_messages()
    consume_messages()
```

---

# 📊 9. Résultat attendu (Logs)

```
INFO Envoi message: {'type': 'CREATE_STOCK', ...}
INFO Envoi message: {'type': 'UPDATE_STOCK', ...}
...
INFO Message reçu: {'type': 'CREATE_STOCK', ...}
INFO Message reçu: {'type': 'SYSTEM_HEALTH', ...}
```

---

# 🧠 10. Cas d’usage métier couverts

✔ Gestion de stock
✔ Alertes temps réel
✔ Sécurité
✔ Monitoring système
✔ Transferts logistiques
✔ Détection d’erreurs
✔ Haute volumétrie

---

# 🏁 Conclusion

Avec cette configuration tu as :

✅ Kafka en **mode moderne KRaft**
✅ Un **cluster 3 nœuds tolérant aux pannes**
✅ Une **simulation métier complète en Python**
✅ Une base solide pour :

* microservices
* event-driven architecture
* data streaming temps réel

---

# 🚀 Test complet d’un cluster 3 nœuds Apache Kafka (Python + logs + explications + fonctionnement)

---

## 📌 Introduction

Dans les architectures modernes (microservices, mobile backend, IoT, data platform), les systèmes doivent gérer **des millions de messages en temps réel sans interruption**.

C’est exactement le rôle de Apache Kafka :
👉 un **bus d’événements distribué, tolérant aux pannes et hautement scalable**.

Mais pour être réellement robuste en production, Kafka est déployé en **cluster** (plusieurs nœuds/brokers).

Dans ce guide, tu vas comprendre :

* ✔ Ce qu’est un cluster Kafka
* ✔ Pourquoi il est indispensable
* ✔ Comment il fonctionne quand un client envoie un message
* ✔ Un script Python complet de test cluster 3 nœuds
* ✔ Logs + cas métiers + failover

---

# 🧠 1. 🔥 C’est quoi un cluster Kafka ?

Un **cluster Kafka** est un ensemble de machines (nœuds appelés brokers) qui travaillent ensemble.

👉 Exemple :

* Node 1 → 9092
* Node 2 → 9094
* Node 3 → 9096

Chaque nœud :

* stocke des messages
* reçoit des données
* sert des consommateurs

---

# ⚙️ 2. Pourquoi utiliser un cluster Kafka ?

Un cluster permet :

## 🚀 1. Haute disponibilité

Si un nœud tombe :
👉 les autres continuent de fonctionner

## ⚡ 2. Scalabilité horizontale

Tu peux ajouter des brokers pour gérer plus de trafic

## 🔁 3. Réplication des données

Chaque message est copié sur plusieurs nœuds

## 🧯 4. Tolérance aux pannes

Pas de perte de données si un serveur crash

## 📦 5. Performance

Répartition de charge sur plusieurs machines

---

# 🔄 3. Comment fonctionne Kafka quand un client envoie un message ?

Voici le flux réel 👇

## 🧑‍💻 Étape 1 : Le client envoie un message

Exemple :

```json
{"type": "ORDER_CREATED", "id": 1001}
```

---

## 📡 Étape 2 : Le Producer choisit un broker

Le producer se connecte à :

```
bootstrap.servers = node1,node2,node3
```

👉 Il contacte un broker “leader”

---

## 🧭 Étape 3 : Partitionnement

Kafka décide :

* Partition 0
* Partition 1
* Partition 2

👉 Selon :

* clé du message
* ou round-robin

---

## 🧱 Étape 4 : Réplication

Si replication-factor = 3 :

```
Node 1 (leader)
Node 2 (follower)
Node 3 (follower)
```

👉 Le message est copié sur les 3 nœuds

---

## 📥 Étape 5 : Consommation

Le consumer :

* lit les messages
* depuis un consumer group
* chaque partition est lue par un seul consumer

---

## 🔁 Étape 6 : Failover (cas panne)

Si Node 1 tombe :

* Node 2 devient leader
* Node 3 prend le relais
* aucun message perdu

---

# 🧪 4. Script Python COMPLET (Test cluster 3 nœuds)

```python id="kafka_cluster_test_full"
import json
import logging
import time
import random
from kafka import KafkaProducer, KafkaConsumer

# =========================
# CLUSTER CONFIG
# =========================
BOOTSTRAP_SERVERS = [
    "localhost:9092",
    "localhost:9094",
    "localhost:9096"
]

TOPIC = "cluster-test-topic"
GROUP_ID = "cluster-test-group"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# =========================
# PRODUCER
# =========================
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    acks="all",
    retries=5,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# =========================
# 10 CAS MÉTIERS
# =========================
def get_messages():
    return [
        {"id": 1, "event": "ORDER_CREATED"},
        {"id": 2, "event": "ORDER_UPDATED"},
        {"id": 3, "event": "ORDER_DELETED"},
        {"id": 4, "event": "LOW_STOCK_ALERT"},
        {"id": 5, "event": "PAYMENT_SUCCESS"},
        {"id": 6, "event": "PAYMENT_FAILED"},
        {"id": 7, "event": "USER_LOGIN"},
        {"id": 8, "event": "USER_LOGOUT"},
        {"id": 9, "event": "SYSTEM_WARNING"},
        {"id": 10, "event": "SYSTEM_HEALTH_OK"}
    ]

# =========================
# PRODUCER TEST
# =========================
def produce():
    logging.info("🚀 PRODUCER START")

    for msg in get_messages():
        key = str(random.randint(1, 100)).encode()

        future = producer.send(TOPIC, key=key, value=msg)

        try:
            meta = future.get(timeout=10)
            logging.info(
                f"Sent → partition={meta.partition}, offset={meta.offset}, msg={msg}"
            )
        except Exception as e:
            logging.error(f"Error sending: {e}")

        time.sleep(0.5)

    producer.flush()
    logging.info("✅ PRODUCER FINISHED")

# =========================
# CONSUMER TEST
# =========================
def consume():
    logging.info("📥 CONSUMER START")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    count = 0

    for message in consumer:
        logging.info(
            f"Received → partition={message.partition}, offset={message.offset}, value={message.value}"
        )

        count += 1
        if count >= 10:
            break

    consumer.close()
    logging.info("✅ CONSUMER FINISHED")

# =========================
# FAILOVER TEST
# =========================
def failover_test():
    logging.info("⚠️ FAILOVER TEST START (stop a broker manually)")

    for i in range(5):
        msg = {"failover": i}

        try:
            producer.send(TOPIC, msg)
            logging.info(f"Failover msg sent: {msg}")
        except Exception as e:
            logging.error(f"Failover error: {e}")

        time.sleep(1)

    producer.flush()
    logging.info("✅ FAILOVER TEST FINISHED")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    logging.info("🔥 KAFKA CLUSTER TEST START")

    produce()
    consume()
    failover_test()

    logging.info("🏁 ALL TESTS COMPLETED")
```

---

# 🧪 5. Création du topic (obligatoire)

```bash id="create_topic_cluster"
kafka-topics.bat --create \
--topic cluster-test-topic \
--bootstrap-server localhost:9092 \
--partitions 3 \
--replication-factor 3
```

---

# 📊 6. Résultats attendus

## ✔ Distribution

```
partition=0
partition=1
partition=2
```

## ✔ Logs

```
Sent → partition=2 offset=10
Received → partition=1 offset=8
```

## ✔ Résilience

Même si un broker tombe :
👉 aucun arrêt du système

---

# 🧠 7. Résumé du fonctionnement client → Kafka

## 🧑 Client (API / mobile / backend)

⬇

## 📡 Producer Kafka

⬇

## 🧭 Broker leader (cluster)

⬇

## 🧱 Réplication sur 3 nœuds

⬇

## 📥 Consumer group

⬇

## 📊 Traitement applicatif

---

# 🏁 Conclusion

Un cluster Apache Kafka permet de construire des systèmes :

✔ ultra fiables
✔ scalables
✔ résilients
✔ temps réel

---

## 🚨 Que se passe-t-il dans un cluster Apache Kafka quand un nœud tombe (sans changer le code client) ?

---

## 📌 Introduction

L’un des plus grands avantages de Apache Kafka est justement celui-ci :

👉 **le code du client ne change jamais**, même si un broker tombe.

Pourquoi ?
Parce que Kafka est conçu comme un système **distribué avec tolérance aux pannes automatique**.

---

# 🧠 1. Principe clé : le client ne parle jamais à un seul serveur

Quand ton code Python ou Java se connecte :

```text
bootstrap.servers = node1,node2,node3
```

👉 Le client ne dépend pas d’un seul nœud
👉 Il demande automatiquement au cluster :

* qui est leader ?
* où écrire ?
* où lire ?

---

# 🔥 2. Cas concret : un nœud tombe (ex: Node 2)

## 🎯 Situation initiale

```
Node 1 = Leader partition 0
Node 2 = Follower
Node 3 = Follower
```

Messages en cours :

```
Partition 0 → leader Node 1
Partition 1 → leader Node 2
Partition 2 → leader Node 3
```

---

## 💥 Étape 1 : Node 2 tombe

```text
Node 2 OFF ❌
```

---

## 🧠 Étape 2 : détection automatique

Kafka utilise un mécanisme interne :

* Heartbeats
* ISR (In-Sync Replicas)

👉 En quelques secondes :

```
Node 2 = OUT OF ISR
```

---

## 🔁 Étape 3 : élection automatique d’un nouveau leader

Si Node 2 était leader d’une partition :

👉 Kafka déclenche :

```
New Leader Election
```

Exemple :

```
Avant :
Partition 1 → Node 2 (leader)

Après :
Partition 1 → Node 3 (new leader)
```

---

## 📡 Étape 4 : le client ne voit RIEN

Ton code Python continue :

```python
producer.send("topic", message)
```

👉 Sans modification

✔ Le client redemande metadata
✔ Il reçoit le nouveau leader
✔ Il continue à envoyer

---

## 🔄 Étape 5 : rééquilibrage

Quand Node 2 revient :

* il resynchronise les données
* il redevient follower
* il réintègre le cluster

---

# 🧪 3. Résumé visuel

## Avant panne

```
Producer → Node2 (leader)
Consumer → Node2
```

## Pendant panne

```
Node2 ❌ DOWN
Node3 → NEW leader
Producer → Node3
Consumer → Node3
```

## Après panne

```
Node2 → resync
Node2 → follower
```

---

# 🧠 4. Pourquoi le code client ne change jamais ?

Parce que Kafka est basé sur 3 principes :

## ✔ 1. Discovery dynamique

Le client demande toujours :
👉 “qui est leader maintenant ?”

---

## ✔ 2. Metadata refresh automatique

Le client met à jour :

```
partition → leader mapping
```

---

## ✔ 3. Retry intelligent

Dans ton code :

```python
retries=5
acks='all'
```

👉 Kafka réessaie automatiquement

---

# ⚙️ 5. Que fait ton code Python pendant la panne ?

Ton script :

```python
producer.send(...)
```

👉 en interne :

1. Échec sur node tombé
2. Refresh metadata
3. Nouvelle tentative
4. Envoi réussi sur nouveau leader

---

# 🧪 6. Cas réel côté Consumer

Le consumer :

* détecte perte de broker
* se reconnecte
* reprend offset exact

👉 grâce à :

```
Consumer Group + Offset Commit
```

---

# 📊 7. Résultat important

| Situation       | Résultat                |
| --------------- | ----------------------- |
| Node tombe      | ❌ invisible pour client |
| Leader change   | ⚙️ automatique          |
| Messages perdus | ❌ aucun                 |
| Code modifié    | ❌ jamais                |
| Reprise         | ✔ automatique           |

---

# 🧠 8. Réponse simple à ta question implicite

## ❓ “Pourquoi le système continue sans changer le code ?”

👉 Parce que :

> Le client Kafka n’est PAS connecté à un serveur,
> mais à un **CLUSTER intelligent auto-géré**

---

# 🚀 9. Conclusion

Un cluster Apache Kafka est conçu pour être :

✔ auto-réparateur
✔ auto-équilibré
✔ transparent pour les applications
✔ résilient aux pannes matérielles

---



