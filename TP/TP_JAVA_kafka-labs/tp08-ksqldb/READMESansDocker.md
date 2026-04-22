## TP08 – ksqlDB : Guide pas à pas (sans Docker, sans code Java)

Ce guide vous permet d’exécuter le TP08 sur votre machine **sans Docker**, en utilisant une installation manuelle de **Kafka (mode KRaft)** et de **ksqlDB**. Aucune programmation Java n’est nécessaire ; tout se fait en ligne de commande et en SQL.

---

### 1. Prérequis

- **Java 11 ou 17** installé (`java -version`)
- **curl**, **wget**, **tar** (présents par défaut sur Linux/macOS, sur Windows utiliser WSL2 ou Git Bash)
- Au moins **4 Go** d’espace disque libre
- Ports libres : `9092` (Kafka), `8088` (ksqlDB), `8081` (Schema Registry optionnel)

---

### 2. Télécharger et installer Confluent Platform (qui contient Kafka + ksqlDB)

ksqlDB est fourni avec la plateforme Confluent. Nous allons télécharger l’archive **gratuite** (pas de licence requise).

```bash
# Télécharger Confluent Platform 7.6.0 (stable)
wget https://packages.confluent.io/archive/7.6/confluent-7.6.0.tar.gz

# Extraire l’archive
tar -xzf confluent-7.6.0.tar.gz

# Se déplacer dans le répertoire
cd confluent-7.6.0
```

> 💡 Sur **Windows sans WSL** : téléchargez le fichier `.zip` depuis [https://www.confluent.io/download/](https://www.confluent.io/download/) et décompressez‑le. Utilisez ensuite les scripts `.bat` dans `bin\windows`.

---

### 3. Configurer Kafka en mode KRaft (sans ZooKeeper)

Le mode KRaft élimine la dépendance à ZooKeeper. Nous allons créer un fichier de configuration dédié.

Créez le fichier `etc/kafka/kraft/server.properties` avec le contenu suivant :

```properties
# Identifiant unique du nœud
node.id=1

# Rôles : broker et controller (mode combiné)
process.roles=broker,controller

# Listeners pour les clients et le protocole controller
listeners=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093

# Adresse annoncée aux clients (ici localhost)
advertised.listeners=PLAINTEXT://localhost:9092

# Listener pour le quorum controller
controller.listener.names=CONTROLLER

# Quorum des controllers (un seul nœud)
controller.quorum.voters=1@localhost:9093

# Répertoire de stockage des logs Kafka
log.dirs=/tmp/kraft-combined-logs
```

#### 3.1 Générer un identifiant de cluster et formater les logs

```bash
# Générer un UUID unique
bin/kafka-storage random-uuid
# Exemple de sortie : Hc8gR1RqTqW9Z3yG5xPv7A
```

Formatez les répertoires de logs avec l’UUID obtenu :

```bash
bin/kafka-storage format -t <VOTRE_UUID> -c etc/kafka/kraft/server.properties
```

#### 3.2 Démarrer Kafka

```bash
bin/kafka-server-start etc/kafka/kraft/server.properties
```

> Pour un démarrage en arrière‑plan (daemon) : `bin/kafka-server-start -daemon etc/kafka/kraft/server.properties`

**Vérification** : dans un autre terminal, exécutez :

```bash
bin/kafka-topics --bootstrap-server localhost:9092 --list
```

Si la commande renvoie la liste (vide pour l’instant), Kafka fonctionne.

---

### 4. (Optionnel mais recommandé) Démarrer Schema Registry

Schema Registry est utile pour gérer les schémas (Avro, JSON) et permet à ksqlDB de fonctionner avec ces formats.

Modifiez `etc/schema-registry/schema-registry.properties` :

```properties
listeners=http://0.0.0.0:8081
kafkastore.bootstrap.servers=PLAINTEXT://localhost:9092
```

Démarrez Schema Registry :

```bash
bin/schema-registry-start etc/schema-registry/schema-registry.properties
```

Vérifiez : `curl http://localhost:8081/subjects` doit renvoyer `[]`.

---

### 5. Configurer et démarrer le serveur ksqlDB

Créez ou modifiez le fichier `etc/ksqldb/ksql-server.properties` :

```properties
bootstrap.servers=localhost:9092
listeners=http://0.0.0.0:8088

# Si vous utilisez Schema Registry (décommentez) :
# ksql.schema.registry.url=http://localhost:8081

# Paramètres recommandés pour le TP
ksql.streams.processing.guarantee=exactly_once_v2
ksql.streams.cache.max.bytes.buffering=0
```

Démarrez le serveur ksqlDB :

```bash
bin/ksql-server-start etc/ksqldb/ksql-server.properties
```

**Vérification** : dans un autre terminal, exécutez :

```bash
curl http://localhost:8088/info
```

Vous devriez voir un JSON contenant la version de ksqlDB.

---

### 6. Se connecter à ksqlDB CLI (client en ligne de commande)

Le client est fourni dans le même répertoire `bin/` :

```bash
bin/ksql http://localhost:8088
```

Vous arrivez à l’invite `ksql>`.

> **Note** : si vous voulez exécuter des commandes depuis un script, utilisez `bin/ksql http://localhost:8088 <<< "SELECT ..."`.

---

### 7. Alimenter le topic source `tp01-commandes` (sans Java)

Nous allons utiliser le **producteur console** de Kafka pour envoyer des messages JSON.

Laissez tourner le serveur Kafka et ksqlDB. Ouvrez **un nouveau terminal**, allez dans le dossier `confluent-7.6.0` et exécutez :

```bash
bin/kafka-console-producer --bootstrap-server localhost:9092 --topic tp01-commandes \
  --property parse.key=true --property key.separator=,
```

Copiez-collez ensuite les lignes suivantes (une par une) :

```
cmd001,{"id":"cmd001","client":"alice","produit":"laptop","quantite":1,"montant":1200.0,"statut":"PAYEE","timestamp":"2025-03-20T10:00:00"}
cmd002,{"id":"cmd002","client":"bob","produit":"souris","quantite":2,"montant":50.0,"statut":"PAYEE","timestamp":"2025-03-20T10:05:00"}
cmd003,{"id":"cmd003","client":"alice","produit":"clavier","quantite":1,"montant":80.0,"statut":"PAYEE","timestamp":"2025-03-20T10:10:00"}
cmd004,{"id":"cmd004","client":"charlie","produit":"ecran","quantite":1,"montant":350.0,"statut":"PAYEE","timestamp":"2025-03-20T10:15:00"}
cmd005,{"id":"cmd005","client":"bob","produit":"laptop","quantite":1,"montant":1250.0,"statut":"PAYEE","timestamp":"2025-03-20T10:20:00"}
```

Appuyez sur **Ctrl+C** pour quitter le producteur.

> **Alternative** : si vous avez déjà un topic `tp01-commandes` avec des données du TP02, vous pouvez passer cette étape.

---

### 8. Exécuter les requêtes SQL du TP08

Retournez dans le terminal où la CLI ksqlDB est lancée (`bin/ksql http://localhost:8088`).  
Exécutez les commandes suivantes (copiez-collez chaque bloc).

#### 8.1 Configurer la lecture depuis le début

```sql
SET 'auto.offset.reset' = 'earliest';
```

#### 8.2 Créer un stream sur le topic existant

```sql
CREATE OR REPLACE STREAM commandes_stream (
    id VARCHAR,
    client VARCHAR,
    produit VARCHAR,
    quantite INT,
    montant DOUBLE,
    statut VARCHAR,
    timestamp VARCHAR
) WITH (
    KAFKA_TOPIC = 'tp01-commandes',
    VALUE_FORMAT = 'JSON',
    PARTITIONS = 3
);
```

#### 8.3 Première requête : voir les messages en temps réel

```sql
SELECT id, client, produit, montant,
       TIMESTAMPTOSTRING(ROWTIME, 'HH:mm:ss') AS heure
FROM commandes_stream
EMIT CHANGES
LIMIT 10;
```

> La requête s’arrête après 10 messages. Vous verrez les commandes que vous avez envoyées.

#### 8.4 Filtrer les commandes VIP (montant > 500)

```sql
SELECT id, client, produit, ROUND(montant,2) AS montant_eur
FROM commandes_stream
WHERE montant > 500.0
EMIT CHANGES
LIMIT 5;
```

#### 8.5 Créer un stream dérivé persisté (nouveau topic)

```sql
CREATE OR REPLACE STREAM commandes_vip AS
SELECT
    id,
    UCASE(client) AS client_upper,
    produit,
    montant,
    'VIP' AS categorie
FROM commandes_stream
WHERE montant > 500.0;
```

Vérifiez que le topic `COMMANDES_VIP` a été créé :

```sql
SHOW TOPICS;
```

#### 8.6 Créer une table d’agrégation (stats par client)

```sql
CREATE OR REPLACE TABLE stats_clients AS
SELECT
    client,
    COUNT(*) AS nb_commandes,
    SUM(montant) AS total_achats,
    AVG(montant) AS panier_moyen,
    MAX(montant) AS plus_grosse_cmd
FROM commandes_stream
GROUP BY client
EMIT CHANGES;
```

#### 8.7 Requête pull (snapshot) sur la table

```sql
SELECT client, nb_commandes, total_achats
FROM stats_clients
WHERE client = 'alice';
```

#### 8.8 (Bonus) Fenêtre temporelle : commandes par heure

```sql
SELECT client,
       COUNT(*) AS commandes_heure,
       SUM(montant) AS total_heure,
       WINDOWSTART AS debut_fenetre,
       WINDOWEND AS fin_fenetre
FROM commandes_stream
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY client
EMIT CHANGES
LIMIT 10;
```

---

### 9. Visualisation (optionnelle) – Consulter les topics avec un consommateur console

Pour voir le contenu du topic `COMMANDES_VIP` (créé par ksqlDB) :

```bash
# Dans un nouveau terminal, dans le dossier confluent-7.6.0
bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic COMMANDES_VIP --from-beginning
```

Vous verrez les messages JSON correspondant aux commandes VIP.

---

### 10. Interface web alternative : AKHQ (optionnel)

Si vous souhaitez une interface graphique sans Docker, installez AKHQ (Java).

```bash
wget https://github.com/akhq/akhq/releases/download/0.25.0/akhq-0.25.0-all.jar
```

Créez un fichier `application.yml` :

```yaml
akhq:
  connections:
    local:
      properties:
        bootstrap.servers: "localhost:9092"
      ksqldb:
        url: "http://localhost:8088"
```

Lancez AKHQ :

```bash
java -jar akhq-0.25.0-all.jar server application.yml
```

Accédez à [http://localhost:8082](http://localhost:8082) pour voir les topics, messages, et exécuter des requêtes ksqlDB.

---

### 11. Arrêt et nettoyage

Pour arrêter tous les services (dans l’ordre inverse) :

- **ksqlDB CLI** : tapez `exit` ou `Ctrl+D`
- **Serveur ksqlDB** : `Ctrl+C` dans son terminal
- **Schema Registry** : `Ctrl+C`
- **Kafka** : `Ctrl+C`

Pour supprimer toutes les données et repartir à zéro :

```bash
rm -rf /tmp/kraft-combined-logs
```

---

## Résumé des commandes essentielles (sans Docker)

| Étape | Commande |
|-------|----------|
| Démarrer Kafka | `bin/kafka-server-start etc/kafka/kraft/server.properties` |
| Démarrer Schema Registry | `bin/schema-registry-start etc/schema-registry/schema-registry.properties` |
| Démarrer ksqlDB Server | `bin/ksql-server-start etc/ksqldb/ksql-server.properties` |
| Lancer ksqlDB CLI | `bin/ksql http://localhost:8088` |
| Envoyer des messages (producteur console) | `bin/kafka-console-producer --bootstrap-server localhost:9092 --topic tp01-commandes --property parse.key=true --property key.separator=,` |
| Lire un topic (consommateur console) | `bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic COMMANDES_VIP --from-beginning` |

---

## Points clés à retenir

- **ksqlDB** transforme des topics Kafka en streams/table SQL.
- Les **requêtes push** (`EMIT CHANGES`) sont des flux continus ; utilisez `LIMIT` pour les arrêter.
- Les **requêtes pull** donnent un instantané d’une table.
- Le mode **KRaft** remplace ZooKeeper, simplifiant l’installation.
- Aucun code Java n’est nécessaire : tout se fait en SQL via la CLI.

Vous pouvez maintenant exécuter le TP08 entièrement **sans Docker**, avec une stack locale légère et maîtrisée.