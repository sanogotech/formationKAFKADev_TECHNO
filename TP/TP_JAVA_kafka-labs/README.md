# 🚀 Kafka Labs — 10 TPs Complets Java 17 + Maven

Formation Apache Kafka de Zéro à Hero — Kafka 3.9+ | Java 17 | Maven 3.9+

---

## 📋 Vue d'ensemble des TPs

| TP  | Titre                                      | Niveau    | Durée est. |
|-----|--------------------------------------------|-----------|------------|
| 01  | Gestion des Topics (AdminClient)           | Débutant  | 30 min     |
| 02  | Producer — Envoyer des messages            | Débutant  | 45 min     |
| 03  | Consumer — Lire des messages               | Débutant  | 45 min     |
| 04  | Consumer Groups & Rebalancing              | Interméd. | 60 min     |
| 05  | Sérialisation Avro & Schema Registry       | Interméd. | 60 min     |
| 06  | Kafka Streams — WordCount                  | Interméd. | 90 min     |
| 07  | Kafka Streams — Fenêtres & KTable Joins    | Avancé    | 90 min     |
| 08  | ksqlDB — SQL sur les Streams               | Avancé    | 60 min     |
| 09  | Kafka Connect — MySQL vers Kafka           | Avancé    | 60 min     |
| 10  | Debezium CDC — Capture des changements     | Expert    | 90 min     |

---

## ⚙️ Prérequis Globaux

### Obligatoires

```bash
# Vérifier Java 17+
java -version
# Attendu : openjdk version "17.x.x" ou plus

# Vérifier Maven 3.9+
mvn -version
# Attendu : Apache Maven 3.9.x

# Vérifier Docker (pour TPs 08-10)
docker --version
docker compose version
```

### Installation Kafka Local (TPs 01-07)

```bash
# 1. Télécharger Kafka 3.9.x
wget https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz
tar -xzf kafka_2.13-3.9.0.tgz
cd kafka_2.13-3.9.0

# 2. Formater le stockage KRaft (sans ZooKeeper)
KAFKA_CLUSTER_ID=$(bin/kafka-storage.sh random-uuid)
bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft/server.properties

# 3. Démarrer Kafka
bin/kafka-server-start.sh config/kraft/server.properties &

# 4. Vérifier (attendre 5 secondes)
sleep 5
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### Variables d'environnement utiles

```bash
export KAFKA_HOME=/chemin/vers/kafka_2.13-3.9.0
export PATH=$PATH:$KAFKA_HOME/bin
```

---

## 🏃 Démarrage Rapide

### Chaque TP suit la même structure :

```
tp0X-nom/
├── pom.xml                          # Dépendances Maven
├── src/
│   ├── main/
│   │   ├── java/com/kafka/lab/      # Code source principal
│   │   └── resources/
│   │       └── logback.xml          # Configuration des logs
│   └── test/
│       └── java/com/kafka/lab/      # Tests JUnit 5
└── README.md                        # Instructions spécifiques au TP
```

### Commandes standard pour chaque TP :

```bash
# Dans le dossier du TP
cd tp0X-nom

# Compiler
mvn clean package -q

# Exécuter la classe principale
mvn exec:java -Dexec.mainClass="com.kafka.lab.NomDeLaClasse"

# Lancer les tests
mvn test

# Lancer un test spécifique
mvn test -Dtest=NomDuTest

# Voir les logs détaillés
mvn exec:java -Dexec.mainClass="com.kafka.lab.NomDeLaClasse" \
    -Dlogback.configurationFile=src/main/resources/logback.xml
```

---

## 📚 Commandes Kafka Utiles

```bash
# Créer un topic
bin/kafka-topics.sh --create \
    --bootstrap-server localhost:9092 \
    --topic mon-topic \
    --partitions 3 \
    --replication-factor 1

# Lister les topics
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Décrire un topic
bin/kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --topic mon-topic

# Producer console (envoi manuel)
bin/kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic mon-topic

# Consumer console (lire depuis le début)
bin/kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic mon-topic \
    --from-beginning

# Consumer avec clés affichées
bin/kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic mon-topic \
    --from-beginning \
    --property print.key=true \
    --property key.separator=" → "

# Voir le lag d'un consumer group
bin/kafka-consumer-groups.sh \
    --bootstrap-server localhost:9092 \
    --describe \
    --group mon-groupe

# Supprimer un topic
bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --delete --topic mon-topic
```

---

## 🐳 Docker Compose (TPs 08-10)

```bash
# TP08 — ksqlDB
cd tp08-ksqldb
docker compose -f docker-compose-ksqldb.yml up -d
# Accès ksqlDB CLI :
docker exec -it tp08-ksqldb-cli ksql http://ksqldb-server:8088

# TP09/10 — Kafka Connect + MySQL + phpMyAdmin
cd tp09-connect-cdc
docker compose -f docker-compose-connect.yml up -d
# phpMyAdmin : http://localhost:8090 (root/rootpass)
# Kafka Connect : http://localhost:8083
# Kafka UI     : http://localhost:8080

# Arrêter et nettoyer
docker compose down -v
```

---

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| `Connection refused localhost:9092` | Kafka non démarré — vérifier le processus |
| `Topic already exists` | Normal — le topic existe déjà |
| `Leader not available` | Attendre 2-3s après création du topic |
| `Docker: port already in use` | `docker ps` puis `docker stop <container>` |
| `Maven: Cannot find class` | Relancer `mvn clean package` |
| `Schema Registry refused` | Vérifier `docker ps` et les logs |

---

## 📦 Structure des Dépendances

```
kafka-clients 3.9.0    → Tous les TPs (Producer, Consumer, AdminClient)
kafka-streams 3.9.0    → TPs 06, 07 (Kafka Streams)
avro 1.11.3            → TP05 (sérialisation Avro)
jackson-databind 2.17  → TPs 02, 03, 09, 10 (JSON)
logback-classic 1.4.14 → Tous (logging)
junit-jupiter 5.10.1   → Tous (tests)
```

---

*Formation Kafka — Zéro à Hero | Java 17 | Kafka 3.9+ | Maven 3.9+*
