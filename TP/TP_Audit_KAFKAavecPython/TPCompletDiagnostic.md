

# 🚀 TP COMPLET KAFKA (KRaft + Windows + Diagnostic Production)

---

# 🧭 0. Contexte & objectif

👉 Ce TP simule un environnement réel de production pour :

* détecter les problèmes de **lag**
* analyser le **throughput**
* tester la **scalabilité**
* comprendre les **goulots d’étranglement**

⚠️ Important :
👉 Ce TP est conçu pour **Kafka en mode KRaft (moderne)**
👉 Fonctionne sous **Windows (CMD ou PowerShell)**

---

# 🏗️ 1. Démarrage Kafka KRaft sous Windows

## 📌 Étape 1 : Configurer KRaft (une seule fois)

Dans `config/kraft/server.properties` :

```properties
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@localhost:9093

listeners=PLAINTEXT://localhost:9092,CONTROLLER://localhost:9093
inter.broker.listener.name=PLAINTEXT

log.dirs=C:/kafka/kraft-logs
```

---

## 📌 Étape 2 : Formater le cluster (⚠️ UNE SEULE FOIS)

```bash
kafka-storage.bat random-uuid
```

➡️ Copier l'UUID

```bash
kafka-storage.bat format -t YOUR_UUID -c config/kraft/server.properties
```

---

## 📌 Étape 3 : Démarrer Kafka

```bash
kafka-server-start.bat config/kraft/server.properties
```

---

# 🧱 2. Création du Topic (important pour tous les tests)

```bash
kafka-topics.bat --create ^
--topic tp-kafka-diagnostic ^
--bootstrap-server localhost:9092 ^
--partitions 6 ^
--replication-factor 1
```

---

## 💡 Explication

| Paramètre     | Pourquoi                  |
| ------------- | ------------------------- |
| partitions=6  | permet parallélisme       |
| replication=1 | simplifie (local Windows) |

---

# 👥 3. Création du Consumer Group

```bash
kafka-console-consumer.bat ^
--topic tp-kafka-diagnostic ^
--bootstrap-server localhost:9092 ^
--group tp-group ^
--from-beginning
```

👉 Kafka crée automatiquement le groupe

---

# 🧪 4. Producer Python 

```python
from kafka import KafkaProducer
import json
import time
import random

# ==========================================
# CONFIGURATION DU PRODUCER
# ==========================================

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',

    # Sérialisation JSON → bytes
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),

    # 🔥 Envoie par batch (améliore performance)
    linger_ms=5,  # attend 5ms pour regrouper messages

    # Taille max du batch
    batch_size=16384,

    # 🔐 Fiabilité
    acks='all',  # attend confirmation de tous les brokers

    # 🔁 Retry en cas d’échec
    retries=5,

    # 🚀 Idempotence = pas de doublons
    enable_idempotence=True
)

# ==========================================
# ENVOI DES MESSAGES
# ==========================================

for i in range(100000):

    # Simulation de données métier
    data = {
        "id": i,
        "user_id": random.randint(1, 100),  # clé métier
        "amount": random.random() * 1000,
        "timestamp": time.time()
    }

    # 🔑 IMPORTANT : clé de partition
    # Permet de garantir l’ordre par utilisateur
    key = str(data["user_id"]).encode()

    producer.send(
        "tp-kafka-diagnostic",
        key=key,
        value=data
    )

    # Monitoring simple
    if i % 1000 == 0:
        print(f"[Producer] Sent {i} messages")

# Flush final
producer.flush()

print("✅ Fin envoi")
```

---

# 📥 5. Consumer Python (SIMULATION PROBLÈME)

```python
from kafka import KafkaConsumer
import json
import time

consumer = KafkaConsumer(
    'tp-kafka-diagnostic',

    bootstrap_servers='localhost:9092',

    group_id='tp-group',

    # Désérialisation JSON
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),

    # ⚠️ Auto commit (risque en prod)
    enable_auto_commit=True,

    auto_offset_reset='earliest'
)

print("🚀 Consumer démarré...")

for message in consumer:

    data = message.value

    print(f"[Consumer] {data}")

    # ==========================================
    # 🔥 SIMULATION D’UN PROBLÈME
    # ==========================================

    # Simule un traitement lent (ex: appel API / DB)
    time.sleep(0.05)

    # 👉 Résultat attendu :
    # accumulation de LAG
```

# 🧪 5. TESTS À EXÉCUTER (SCÉNARIOS RÉELS )

---

# 🔥 TEST 1 — Throughput MAX (capacité brute Kafka)

## 🎯 Objectif

Mesurer la **capacité maximale du cluster Kafka** :

* combien de messages/sec Kafka peut encaisser
* latence moyenne
* stabilité sous charge

---

## 🧭 Étapes détaillées

### 1️⃣ Vérifier que Kafka tourne

```bash
kafka-topics.bat --list --bootstrap-server localhost:9092
```

---

### 2️⃣ Lancer le test de performance

```bash
kafka-producer-perf-test.bat ^
--topic tp-kafka-diagnostic ^
--num-records 100000 ^
--record-size 100 ^
--throughput -1 ^
--producer-props bootstrap.servers=localhost:9092
```

---

## 🔍 Explication ligne par ligne

| Paramètre     | Rôle                       |
| ------------- | -------------------------- |
| num-records   | volume total               |
| record-size   | taille message             |
| throughput=-1 | envoie max (pas de limite) |

---

## 👀 Ce que tu dois observer

* messages/sec (ex: 50k msg/sec)
* latence moyenne (ms)
* CPU broker

---

## ⚠️ Problèmes typiques

| Symptôme          | Cause               |
| ----------------- | ------------------- |
| throughput faible | mauvais batch       |
| latence élevée    | réseau ou disque    |
| CPU élevé         | compression absente |

---

## ✅ Solutions

* augmenter `batch.size`
* activer compression (`lz4`, `snappy`)
* ajouter partitions

---

---

# 🐢 TEST 2 — Consumer lent → LAG

---

## 🎯 Objectif

Comprendre :
👉 pourquoi le **lag apparaît**
👉 comment le détecter
👉 comment le corriger

---

## 🧭 Étapes détaillées

### 1️⃣ Lancer consumer lent (avec sleep)

```python
time.sleep(0.05)
```

---

### 2️⃣ Lancer producer (charge)

---

### 3️⃣ Observer le lag

```bash
kafka-consumer-groups.bat ^
--bootstrap-server localhost:9092 ^
--describe --group tp-group
```

---

## 🔍 Comprendre le résultat

| Champ          | Signification |
| -------------- | ------------- |
| CURRENT-OFFSET | consommé      |
| LOG-END-OFFSET | produit       |
| LAG            | retard        |

---

## 📊 Exemple

```
LAG = 50000
```

👉 50 000 messages en attente

---

## 🧠 Analyse

👉 Le consumer est plus lent que le producer
👉 Kafka accumule les messages

---

## ✅ Solutions

* ajouter consumers
* réduire temps traitement
* paralléliser (threads)

---

---

# ⚖️ TEST 3 — Multi-consumers (scaling horizontal)

---

## 🎯 Objectif

Tester la **scalabilité Kafka côté consommation**

---

## 🧭 Étapes

### 1️⃣ Lancer 3 consumers

👉 Ouvrir 3 terminaux

---

### 2️⃣ Observer

```bash
kafka-consumer-groups.bat  --bootstrap-server localhost:9092  --describe --group tp-group
```

---

## 👀 Ce que tu dois voir

* partitions réparties :

```
Consumer 1 → partitions 0,1
Consumer 2 → partitions 2,3
Consumer 3 → partitions 4,5
```

---

## 🧠 Règle clé

👉 **1 partition = 1 consumer max**

---

## 📉 Résultat attendu

* lag diminue
* débit augmente

---

## ⚠️ Cas problématique

| Cas                        | Impact     |
| -------------------------- | ---------- |
| + consumers que partitions | inutiles   |
| partitions déséquilibrées  | bottleneck |

---

## ✅ Solutions

* augmenter partitions
* équilibrer clés

---

---

# 💥 TEST 4 — Déséquilibre partitions (data skew)

---

## 🎯 Objectif

Comprendre un des pires problèmes Kafka : **skew**

---

## 🧭 Étapes

Modifier producer :

```python
key = b"fixed_key"
```

---

## 🔍 Résultat

👉 Tous les messages vont dans **1 seule partition**

---

## 👀 Observation

```bash
kafka-consumer-groups.bat --describe --group tp-group
```

➡️ 1 partition saturée
➡️ autres vides

---

## 🧠 Impact réel

* 1 consumer surchargé
* latence élevée
* lag localisé

---

## ✅ Solutions

* utiliser clé métier (user_id)
* hashing équilibré

---

---

# 🔁 TEST 5 — Rebalancing (comportement réel)

---

## 🎯 Objectif

Comprendre les **rebalancing Kafka (critique en prod)**

---

## 🧭 Étapes

1. Lancer 3 consumers
2. Stop brutalement 1

---

## 👀 Observation

* pause consommation (quelques secondes)
* redistribution partitions

---

## 🧠 Explication

Kafka doit :

* détecter consumer mort
* recalculer assignment

---

## ⚠️ Problème réel

👉 trop de rebalancing = instabilité

---

## ✅ Solutions

* augmenter `session.timeout.ms`
* utiliser `static membership`

---

---

# 🧱 TEST 6 — Saturation broker

---

## 🎯 Objectif

Tester limites mémoire / réseau

---

## 🧭 Étapes

```bash
--record-size 1000000
```

---

## 👀 Résultat

* latence ↑
* mémoire ↑
* GC ↑

---

## ⚠️ Risques

* OOM broker
* timeouts

---

## ✅ Solutions

* limiter taille messages
* compression

---

---

# 💾 TEST 7 — Disk IO saturation

---

## 🎯 Objectif

Identifier bottleneck disque

---

## 🧭 Étapes

Linux :

```bash
iostat -x 1
```

Windows :

```powershell
Get-Counter '\PhysicalDisk(*)\% Disk Time'
```

---

## 👀 Observer

* disk usage > 80%
* latence disque

---

## 🧠 Impact

👉 Kafka est disk-heavy → critique

---

## ✅ Solutions

* SSD obligatoire
* augmenter partitions/disques

---

---

# 🌐 TEST 8 — Réseau lent

---

## 🎯 Objectif

Simuler latence réseau

---

## 🧠 Impact

* latence ↑
* retries ↑

---

## ✅ Solutions

* compression
* tuning buffer

---

---

# 🧠 TEST 9 — Mauvaise config batch

---

## 🎯 Objectif

Comprendre impact config producer

---

## 🧭 Étapes

```python
linger_ms=0
batch_size=1
```

---

## 👀 Résultat

* throughput ↓↓↓
* CPU ↑

---

## 🧠 Explication

👉 envoi message par message

---

## ✅ Solution

* augmenter batch
* linger > 5ms

---

---

# ⚠️ TEST 10 — Auto commit dangereux

---

## 🎯 Objectif

Comprendre perte de données

---

## 🧭 Étapes

1. consumer avec auto_commit
2. kill process

---

## 👀 Résultat

👉 messages non traités mais commités

---

## 🧠 Impact

❌ perte de données

---

## ✅ Solution

```python
enable_auto_commit=False
```


---

# 🧨 6. TOP 20 PROBLÈMES KAFKA (GUIDE EXPERT TERRAIN)

---

# 🔴 1. Lag élevé (LE PROBLÈME N°1 EN PROD)

## 🎯 Définition

Le **lag** = nombre de messages **produits mais non consommés**

---

## 🔍 Symptômes

* backlog qui augmente
* consommateurs “en retard”
* dashboards rouges

---

## 🧠 Causes possibles

| Cause                    | Détail                    |
| ------------------------ | ------------------------- |
| consumer lent            | traitement long (DB, API) |
| trop peu de consumers    | pas assez de parallélisme |
| partitions insuffisantes | limite physique           |

---

## 🔎 Vérification

```bash
kafka-consumer-groups.bat --describe --group tp-group
```

👉 Regarder colonne **LAG**

---

## ✅ Solutions concrètes

### 1. Scaling horizontal

* ajouter consumers
* augmenter partitions

---

### 2. Optimisation traitement

* éviter appels bloquants
* batch processing

---

### 3. Async processing

```python
# exemple pseudo
process_async(message)
```

---

## 🧠 Bonne pratique

👉 Toujours dimensionner :

```
#consumers <= #partitions
```

---

---

# 🔴 2. Mauvaise clé (DATA SKEW)

---

## 🎯 Définition

Tous les messages vont dans une seule partition

---

## 🔍 Symptômes

* 1 consumer saturé
* autres idle
* lag localisé

---

## 🧠 Cause

```python
key = "fixed_key"
```

---

## 🔎 Vérification

```bash
kafka-consumer-groups.bat --describe --group tp-group
```

👉 Une seule partition avec lag

---

## ✅ Solutions

### ✔ Clé métier équilibrée

```python
key = str(user_id).encode()
```

---

### ✔ Hash distribué

---

## 🧠 Bonne pratique

👉 Toujours choisir une clé :

* stable
* répartie uniformément

---

---

# 🔴 3. Trop peu de partitions

---

## 🎯 Impact

* pas de scaling
* limite consommation

---

## 🔍 Symptômes

* consumers inutilisés
* lag persistant

---

## 🔎 Vérification

```bash
kafka-topics.bat --describe --topic tp-kafka-diagnostic
```

---

## ✅ Solution

```bash
kafka-topics.bat --alter --partitions 12 --topic tp-kafka-diagnostic
```

---

## ⚠️ Attention

* impossible de réduire partitions
* impact ordering

---

## 🧠 Bonne pratique

👉 prévoir partitions dès le départ

---

---

# 🔴 4. Rebalancing fréquent

---

## 🎯 Définition

Redistribution partitions entre consumers

---

## 🔍 Symptômes

* pauses fréquentes
* logs “rebalance in progress”

---

## 🧠 Causes

* consumers crash
* timeouts courts

---

## 🔎 Vérification

logs consumer

---

## ✅ Solutions

### ✔ Augmenter timeout

```properties
session.timeout.ms=30000
```

---

### ✔ Static membership

---

## 🧠 Bonne pratique

👉 éviter redémarrages fréquents

---

---

# 🔴 5. Throughput faible

---

## 🔍 Symptômes

* faible msg/sec
* latence élevée

---

## 🧠 Causes

* pas de batching
* compression désactivée

---

## ✅ Solutions

```python
linger_ms=10
batch_size=32768
compression_type='lz4'
```

---

## 🧠 Bonne pratique

👉 toujours activer batching

---

---

# 🔴 6. Doublons (duplication messages)

---

## 🎯 Cause

* retry producer

---

## 🔍 Symptômes

* messages en double

---

## ✅ Solution

```python
enable_idempotence=True
```

---

## 🧠 Bonne pratique

👉 toujours activer idempotence en prod

---

---

# 🔴 7. Perte de messages

---

## 🎯 Cause

```python
acks=0
```

---

## 🔍 Symptômes

* messages manquants

---

## ✅ Solution

```python
acks='all'
```

---

## 🧠 Bonne pratique

👉 ne jamais utiliser acks=0 en prod

---

---

# 🔴 8. Latence élevée

---

## 🧠 Causes

* réseau lent
* batch mal configuré

---

## 🔎 Vérification

* métriques latence

---

## ✅ Solutions

* ajuster linger
* optimiser réseau

---

---

# 🔴 9. Saturation disque

---

## 🔍 Symptômes

* Kafka lent
* disk usage élevé

---

## 🔎 Vérification

Windows :

```powershell
Get-Counter '\PhysicalDisk(*)\% Disk Time'
```

---

## ✅ Solutions

* SSD
* retention config

```properties
log.retention.hours=24
```

---

---

# 🔴 10. Consumer bloqué

---

## 🧠 Cause

* traitement synchrone long

---

## 🔍 Symptômes

* lag augmente

---

## ✅ Solution

* async processing
* multi-thread

---

---

# 🔴 11. OOM (Out Of Memory)

---

## 🔍 Symptômes

* crash JVM

---

## 🧠 Causes

* batch trop grand
* messages volumineux

---

## ✅ Solutions

* limiter batch
* tuning heap

---

---

# 🔴 12. Mauvais topic config

---

## 🧠 Cause

* mauvaise policy

---

## ✅ Solutions

```properties
cleanup.policy=compact
```

---

## 🧠 Cas usage

| Mode    | Usage     |
| ------- | --------- |
| log     | streaming |
| compact | état      |

---

---

# 🔴 13. Mauvais offset

---

## 🔍 Symptômes

* messages sautés
* doublons

---

## 🧠 Cause

* auto commit

---

## ✅ Solution

```python
enable_auto_commit=False
```

---

---

# 🔴 14. Réseau saturé

---

## 🔍 Symptômes

* latence ↑
* retries ↑

---

## ✅ Solution

```python
compression_type='snappy'
```

---

---

# 🔴 15. Trop de petits messages

---

## 🧠 Impact

* overhead réseau

---

## ✅ Solution

* batching

---

---

# 🔴 16. KRaft instable

---

## 🧠 Causes

* cluster sous-dimensionné

---

## ✅ Solutions

* 3 nodes minimum
* quorum correct

---

---

# 🔴 17. Timeout producer

---

## 🔍 Symptômes

* erreurs timeout

---

## ✅ Solution

```python
retries=5
request_timeout_ms=30000
```

---

---

# 🔴 18. CPU élevé

---

## 🔍 Symptômes

* CPU > 80%

---

## 🧠 Causes

* compression
* trop partitions

---

## ✅ Solution

* scaling horizontal

---

---

# 🔴 19. Leader overload

---

## 🎯 Définition

Une partition leader surchargée

---

## ✅ Solution

```bash
kafka-leader-election.bat
```

---

---

# 🔴 20. Pas de monitoring

---

## 🎯 Impact

* pas de visibilité
* incidents invisibles

---

## ✅ Solution

* Prometheus
* Grafana

---

## 🧠 KPIs clés

| KPI        | Description |
| ---------- | ----------- |
| Lag        | backlog     |
| Throughput | débit       |
| Latence    | temps       |
| CPU        | charge      |
| Disk       | saturation  |

---

# 🧠 CONCLUSION EXPERT

👉 Ce TOP 20 couvre **90% des incidents Kafka réels**

Avec ce guide tu peux :

✅ diagnostiquer rapidement
✅ corriger efficacement
✅ anticiper les problèmes
✅ dimensionner un cluster

---


