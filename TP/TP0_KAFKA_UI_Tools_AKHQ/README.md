# 📘 Programme ultra-détaillé de Travaux Pratiques

## 🚀 Kafka (mode KRaft) + AKHQ — Niveau débutant → intermédiaire

---

## 🧭 Introduction approfondie

Ce parcours contient **15 TP très détaillés (version approfondie x2)** pour maîtriser progressivement Apache Kafka en **mode KRaft** (sans ZooKeeper), ainsi que la supervision via AKHQ.

👉 Chaque TP est structuré avec :

* 🟦 **Avant (préparation technique & compréhension)**
* 🟨 **Pendant (actions pas à pas + commandes)**
* 🟩 **Après (validation, analyse, erreurs possibles, extensions)**

---

# 🧪 TP1 — Installation Kafka en mode KRaft (ultra détaillé)

## 🟦 Avant

* Installer Java 11 ou 17 (vérifier avec `java -version`)
* Télécharger Kafka depuis le site officiel
* Décompresser dans un dossier (ex: `C:\kafka`)
* Comprendre que KRaft remplace ZooKeeper

📌 Vérifier :

* variable `JAVA_HOME`
* accès aux scripts `.bat` ou `.sh`

---

## 🟨 Pendant

### Étape 1 — Générer un ID de cluster

```bash
kafka-storage.bat random-uuid
```

👉 Copier l’ID généré

---

### Étape 2 — Formater le stockage KRaft

```bash
kafka-storage.bat format -t <CLUSTER_ID> -c config/kraft/server.properties
```

👉 Cela initialise :

* logs metadata
* stockage Kafka interne

---

### Étape 3 — Démarrer Kafka

```bash
kafka-server-start.bat config/kraft/server.properties
```

---

## 🟩 Après

✔️ Kafka démarre sans ZooKeeper
✔️ Logs indiquent “started”
✔️ Port 9092 actif

### Vérification :

```bash
netstat -an | find "9092"
```

### ❗ Problèmes possibles

* Java non reconnu
* mauvais CLUSTER_ID
* port déjà utilisé

---

# 🧪 TP2 — Analyse du mode KRaft

## 🟦 Avant

* Kafka lancé

## 🟨 Pendant

Ouvrir :

```bash
config/kraft/server.properties
```

Analyser :

* `process.roles=broker,controller`
* `node.id=1`
* `controller.quorum.voters=1@localhost:9093`

---

## 🟩 Après

✔️ Comprendre :

* Kafka gère ses propres métadonnées
* différence avec ZooKeeper

### 💡 Bonus

Comparer avec ancienne config ZooKeeper

---

# 🧪 TP3 — Création avancée de topics

## 🟦 Avant

Kafka actif

## 🟨 Pendant

```bash
kafka-topics.bat --create \
--topic orders \
--partitions 3 \
--replication-factor 1 \
--bootstrap-server localhost:9092
```

---

## 🟩 Après

✔️ Vérifier :

```bash
kafka-topics.bat --describe --topic orders --bootstrap-server localhost:9092
```

✔️ Comprendre :

* partition = parallélisme
* replication = tolérance panne

---

# 🧪 TP4 — Production JSON

## 🟦 Avant

Topic `orders` existant

## 🟨 Pendant

```bash
kafka-console-producer.bat --topic orders --bootstrap-server localhost:9092
```

Envoyer :

```json
{"id":1,"amount":100}
{"id":2,"amount":200}
```

---

## 🟩 Après

✔️ Messages stockés
✔️ Kafka ne valide pas le JSON (important)

### ⚠️ Attention

Kafka ne vérifie pas le format

---

# 🧪 TP5 — Consommation avancée

## 🟦 Avant

Messages présents

## 🟨 Pendant

```bash
kafka-console-consumer.bat \
--topic orders \
--from-beginning \
--bootstrap-server localhost:9092
```

---

## 🟩 Après

✔️ Tous les messages visibles
✔️ Flux temps réel

### 💡 Bonus

Tester sans `--from-beginning`

---

# 🧪 TP6 — Installation AKHQ

## 🟦 Avant

Créer `application.yml`

## 🟨 Pendant

```bash
java -Dmicronaut.config.files=application.yml -jar akhq-0.24.0-all.jar
```

---

## 🟩 Après

✔️ Accès UI
✔️ Cluster visible

### ❗ erreurs possibles

* YAML incorrect
* mauvais port Kafka

---

# 🧪 TP7 — Exploration UI AKHQ

## 🟦 Avant

AKHQ actif

## 🟨 Pendant

Explorer :

* Topics
* Partitions
* Messages

---

## 🟩 Après

✔️ Visualisation complète
✔️ Remplacement CLI

---

# 🧪 TP8 — Consumer groups

## 🟦 Avant

Créer group

## 🟨 Pendant

```bash
kafka-console-consumer.bat \
--topic orders \
--group g1 \
--bootstrap-server localhost:9092
```

---

## 🟩 Après

✔️ Voir group dans AKHQ
✔️ offsets suivis

---

# 🧪 TP9 — Lag analysis

## 🟦 Avant

Consumer actif

## 🟨 Pendant

* stop consumer
* produire messages

---

## 🟩 Après

✔️ Lag augmente
✔️ visible dans AKHQ

---

# 🧪 TP10 — Multi-consumers

## 🟦 Avant

Topic partitions = 3

## 🟨 Pendant

Lancer 2 consumers

---

## 🟩 Après

✔️ messages répartis
✔️ load balancing

---

# 🧪 TP11 — Microservices simulation

## 🟦 Avant

Créer topics

## 🟨 Pendant

Flux :

```text
orders → payments → notifications
```

---

## 🟩 Après

✔️ Event chain

---

# 🧪 TP12 — Gestion erreurs

## 🟦 Avant

Topic existant

## 🟨 Pendant

Envoyer mauvais JSON

---

## 🟩 Après

✔️ Kafka accepte
✔️ problème côté consumer

---

# 🧪 TP13 — Performance test

## 🟦 Avant

Kafka actif

## 🟨 Pendant

Produire 1000 messages

---

## 🟩 Après

✔️ mesurer débit
✔️ observer latence

---

# 🧪 TP14 — Debug avancé

## 🟦 Avant

Créer problème

## 🟨 Pendant

* consumer lent
* backlog

---

## 🟩 Après

✔️ diagnostic AKHQ

---

# 🧪 TP15 — Projet final

## 🟦 Avant

Créer topics

## 🟨 Pendant

```text
Order → Payment → Shipping → Notification
```

---

## 🟩 Après

✔️ flux complet
✔️ supervision AKHQ

---

# 🏁 Conclusion

Tu maîtrises maintenant :

✔️ Kafka KRaft
✔️ Producer / Consumer
✔️ AKHQ UI
✔️ Debug & lag
✔️ Architecture event-driven

---

# 🚀 Étape suivante

Ajouter :

* 📊 Prometheus
* 📈 Grafana
* 🤖 Tests automatisés

---
