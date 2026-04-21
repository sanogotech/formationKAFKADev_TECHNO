# 12 TPs complets sur Kafka Connect et CDC avec Debezium**, fonctionnant avec **Kafka en mode KRaft** (sans ZooKeeper)
---

## Table des matières

1. [Architecture et prérequis](#1-architecture-et-pr%C3%A9requis)
2. [TP1 : Kafka Connect standalone – premier connecteur fichier](#2-tp1--kafka-connect-standalone--premier-connecteur-fichier)
3. [TP2 : Connecteur JDBC Source (H2)](#3-tp2--connecteur-jdbc-source-h2)
4. [TP3 : Connecteur JDBC Sink](#4-tp3--connecteur-jdbc-sink)
5. [TP4 : Debezium MySQL CDC – installation et configuration](#5-tp4--debezium-mysql-cdc--installation-et-configuration)
6. [TP5 : Debezium MySQL CDC – capture des changements](#6-tp5--debezium-mysql-cdc--capture-des-changements)
7. [TP6 : Filtrage et transformation avec SMT (Single Message Transform)](#7-tp6--filtrage-et-transformation-avec-smt-single-message-transform)
8. [TP7 : Connecteur Debezium PostgreSQL](#8-tp7--connecteur-debezium-postgresql)
9. [TP8 : Connecteur Debezium MongoDB](#9-tp8--connecteur-debezium-mongodb)
10. [TP9 : Connecteur HTTP Sink (webhooks)](#10-tp9--connecteur-http-sink-webhooks)
11. [TP10 : Connecteur Elasticsearch Sink](#11-tp10--connecteur-elasticsearch-sink)
12. [TP11 : API REST Kafka Connect – gestion des connecteurs](#12-tp11--api-rest-kafka-connect--gestion-des-connecteurs)
13. [TP12 : Client Java pour Kafka Connect API](#13-tp12--client-java-pour-kafka-connect-api)

---

## 1. Architecture et prérequis

### 🔑 Définitions importantes

| Concept | Définition |
|---------|-------------|
| **Kafka Connect** | Framework pour intégrer Kafka avec des systèmes externes (bases de données, fichiers, services cloud) via des connecteurs source/sink. |
| **Source Connector** | Importe des données depuis un système externe vers Kafka. |
| **Sink Connector** | Exporte des données depuis Kafka vers un système externe. |
| **CDC (Change Data Capture)** | Technique capturant les modifications (INSERT, UPDATE, DELETE) d'une base de données pour les propager en temps réel. |
| **Debezium** | Plateforme CDC distribuée basée sur Kafka Connect, supportant MySQL, PostgreSQL, MongoDB, etc. |
| **Converter** | Transforme les données entre Kafka Connect et Kafka (ex: JsonConverter, AvroConverter). |
| **SMT (Single Message Transform)** | Modifie chaque message individuellement (filtrage, renommage de champs, masquage). |
| **Tasks** | Unités de travail parallélisables d'un connecteur. |
| **Offset** | Stocke la position du connecteur source (ex: binlog position, numéro de ligne). |
| **KRaft** | Mode de Kafka sans ZooKeeper (utilisé dans tous les TPs). |

### 📦 Prérequis techniques

1. **Java 17** : `java -version`
2. **Maven 3.8+** : `mvn -version`
3. **Kafka 3.6+** (mode KRaft) – [téléchargement](https://kafka.apache.org/downloads)
4. **Docker** (pour MySQL, PostgreSQL, MongoDB – optionnel mais recommandé pour les TPs CDC)

### ⚙️ Configuration de Kafka en mode KRaft

```bash
# 1. Générer un ID de cluster unique
cd kafka-3.6.0
bin/kafka-storage.sh random-uuid
# Exemple : 5zZq9TbhRxS5Iq3P6gvW6Q

# 2. Formater le répertoire de logs
bin/kafka-storage.sh format -t <UUID> -c config/kraft/server.properties

# 3. Démarrer Kafka
bin/kafka-server-start.sh config/kraft/server.properties

# 4. Démarrer Kafka Connect (mode distribué)
bin/connect-distributed.sh config/connect-distributed.properties
```

### 📥 Configuration de Kafka Connect (connect-distributed.properties)

```properties
# config/connect-distributed.properties
bootstrap.servers=localhost:9092
group.id=connect-cluster
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false
offset.storage.topic=connect-offsets
offset.storage.replication.factor=1
config.storage.topic=connect-configs
config.storage.replication.factor=1
status.storage.topic=connect-status
status.storage.replication.factor=1
plugin.path=/usr/share/java,/usr/local/share/kafka/plugins
```

---

## 2. TP1 : Kafka Connect standalone – premier connecteur fichier

### Objectif
Comprendre le fonctionnement de base d'un connecteur source/sink avec des fichiers.

### Concepts
- **Standalone vs Distribué** : mode simple pour développement
- **FileStreamSourceConnector** : lecture d'un fichier ligne par ligne
- **FileStreamSinkConnector** : écriture dans un fichier

### Configuration

**config/connect-standalone.properties** :
```properties
bootstrap.servers=localhost:9092
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false
offset.storage.file.filename=/tmp/connect.offsets
offset.flush.interval.ms=10000
```

**config/source-file.properties** :
```properties
name=file-source
connector.class=org.apache.kafka.connect.file.FileStreamSourceConnector
tasks.max=1
file=/tmp/input.txt
topic=file-topic
```

**config/sink-file.properties** :
```properties
name=file-sink
connector.class=org.apache.kafka.connect.file.FileStreamSinkConnector
tasks.max=1
file=/tmp/output.txt
topics=file-topic
```

### Exécution et test

```bash
# Créer le fichier source
echo "Hello Kafka Connect" > /tmp/input.txt
echo "Ligne 2" >> /tmp/input.txt

# Démarrer standalone (source + sink)
bin/connect-standalone.sh config/connect-standalone.properties \
    config/source-file.properties config/sink-file.properties

# Vérifier la sortie
cat /tmp/output.txt
```

### Résultat attendu
```
Hello Kafka Connect
Ligne 2
```

---

## 3. TP2 : Connecteur JDBC Source (H2)

### Objectif
Importer des données depuis une base de données H2 vers Kafka.

### Prérequis Maven

```xml
<!-- pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.apache.kafka</groupId>
        <artifactId>connect-api</artifactId>
        <version>3.6.0</version>
    </dependency>
    <dependency>
        <groupId>com.h2database</groupId>
        <artifactId>h2</artifactId>
        <version>2.2.224</version>
    </dependency>
    <dependency>
        <groupId>io.confluent</groupId>
        <artifactId>kafka-connect-jdbc</artifactId>
        <version>10.7.4</version>
    </dependency>
</dependencies>
```

### Initialisation de la base H2

```java
// com/example/tp2_h2/H2DatabaseSetup.java
package com.example.tp2_h2;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;

public class H2DatabaseSetup {
    public static void main(String[] args) throws Exception {
        Connection conn = DriverManager.getConnection("jdbc:h2:~/testdb", "sa", "");
        Statement stmt = conn.createStatement();
        
        stmt.execute("CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100))");
        stmt.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')");
        stmt.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@example.com')");
        
        System.out.println("Base H2 initialisée avec données");
        conn.close();
    }
}
```

### Configuration du connecteur

```json
// config/jdbc-source.json
{
    "name": "jdbc-source-connector",
    "config": {
        "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
        "tasks.max": "1",
        "connection.url": "jdbc:h2:~/testdb",
        "connection.user": "sa",
        "mode": "incrementing",
        "incrementing.column.name": "id",
        "topic.prefix": "jdbc-h2-",
        "table.whitelist": "users",
        "poll.interval.ms": "5000"
    }
}
```

### Envoi via API REST

```bash
curl -X POST -H "Content-Type: application/json" \
    --data @config/jdbc-source.json \
    http://localhost:8083/connectors

# Consommer les données
bin/kafka-console-consumer --topic jdbc-h2-users --bootstrap-server localhost:9092 --from-beginning
```

### Résultat attendu
```json
{"id":1,"name":"Alice","email":"alice@example.com"}
{"id":2,"name":"Bob","email":"bob@example.com"}
```

---

## 4. TP3 : Connecteur JDBC Sink

### Objectif
Écrire des données Kafka vers une base de données.

### Configuration

```json
// config/jdbc-sink.json
{
    "name": "jdbc-sink-connector",
    "config": {
        "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
        "tasks.max": "1",
        "topics": "users-sink-topic",
        "connection.url": "jdbc:h2:~/sinkdb",
        "connection.user": "sa",
        "auto.create": "true",
        "auto.evolve": "true",
        "insert.mode": "upsert",
        "pk.mode": "record_key",
        "pk.fields": "id"
    }
}
```

### Production de données

```java
// com/example/tp3_sink/ProduceToSink.java
package com.example.tp3_sink;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import java.util.Properties;

public class ProduceToSink {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092");
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.connect.json.JsonSerializer");
        
        KafkaProducer<String, String> producer = new KafkaProducer<>(props);
        
        String json = "{\"schema\":{\"type\":\"struct\",\"fields\":[{\"type\":\"int32\",\"field\":\"id\"},{\"type\":\"string\",\"field\":\"name\"}],\"optional\":false},\"payload\":{\"id\":3,\"name\":\"Charlie\"}}";
        producer.send(new ProducerRecord<>("users-sink-topic", "3", json));
        producer.flush();
    }
}
```

---

## 5. TP4 : Debezium MySQL CDC – installation et configuration

### Objectif
Configurer Debezium pour capturer les changements d'une base MySQL.

### Docker Compose MySQL

```yaml
# docker-compose-mysql.yml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: mysql-debezium
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: testdb
      MYSQL_USER: debezium
      MYSQL_PASSWORD: dbzpass
    ports:
      - "3306:3306"
    command: --server-id=1 --log-bin=mysql-bin --binlog-format=ROW
```

```bash
docker-compose -f docker-compose-mysql.yml up -d

# Configuration MySQL pour CDC
docker exec -it mysql-debezium mysql -uroot -prootpass

# Dans MySQL :
CREATE USER 'debezium'@'%' IDENTIFIED BY 'dbzpass';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;
```

### Téléchargement du connecteur Debezium MySQL

```bash
# Télécharger depuis Maven Central
wget https://repo1.maven.org/maven2/io/debezium/debezium-connector-mysql/2.4.0/debezium-connector-mysql-2.4.0-plugin.tar.gz
tar -xzf debezium-connector-mysql-2.4.0-plugin.tar.gz -C /usr/share/java/
```

### Configuration du connecteur MySQL

```json
// config/mysql-source.json
{
    "name": "mysql-debezium-connector",
    "config": {
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        "tasks.max": "1",
        "database.hostname": "localhost",
        "database.port": "3306",
        "database.user": "debezium",
        "database.password": "dbzpass",
        "database.server.id": "184054",
        "database.server.name": "mysql-server",
        "database.include.list": "testdb",
        "table.include.list": "testdb.users",
        "database.history.kafka.bootstrap.servers": "localhost:9092",
        "database.history.kafka.topic": "schema-changes.testdb",
        "include.schema.changes": "true",
        "snapshot.mode": "initial",
        "topic.prefix": "mysql"
    }
}
```

---

## 6. TP5 : Debezium MySQL CDC – capture des changements

### Objectif
Observer les changements en temps réel (INSERT, UPDATE, DELETE).

### Configuration avancée

```json
// config/mysql-cdc-advanced.json
{
    "name": "mysql-cdc-connector",
    "config": {
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        "database.hostname": "localhost",
        "database.port": "3306",
        "database.user": "debezium",
        "database.password": "dbzpass",
        "database.server.id": "184055",
        "database.server.name": "cdc-mysql",
        "database.include.list": "testdb",
        "table.include.list": "testdb.users,testdb.orders",
        "database.history.kafka.bootstrap.servers": "localhost:9092",
        "database.history.kafka.topic": "schema-changes.testdb",
        "snapshot.mode": "when_needed",
        "snapshot.locking.mode": "none",
        "time.precision.mode": "adaptive_time_microseconds",
        "decimal.handling.mode": "precise",
        "binary.handling.mode": "hex",
        "errors.retry.timeout": "30000",
        "errors.max.retries": "10",
        "retry.restart.wait": "10000"
    }
}
```

### Tests en SQL

```sql
-- INSERT
INSERT INTO users VALUES (3, 'David', 'david@example.com');

-- UPDATE
UPDATE users SET name='Alice Updated' WHERE id=1;

-- DELETE
DELETE FROM users WHERE id=2;
```

### Consommation des changements

```bash
# Chaque changement produit un message
bin/kafka-console-consumer --topic cdc-mysql.testdb.users --bootstrap-server localhost:9092 --from-beginning
```

### Format du message CDC (Debezium)

```json
{
    "before": null,
    "after": {"id": 3, "name": "David", "email": "david@example.com"},
    "source": {
        "version": "2.4.0",
        "name": "cdc-mysql",
        "server_id": 184055,
        "ts_sec": 1734567890,
        "gtid": null,
        "file": "mysql-bin.000001",
        "pos": 1234,
        "row": 0,
        "snapshot": false,
        "thread": 123,
        "db": "testdb",
        "table": "users"
    },
    "op": "c",
    "ts_ms": 1734567890123,
    "transaction": null
}
```

**Champ `op`** : `c` = create, `u` = update, `d` = delete, `r` = read (snapshot)

---

## 7. TP6 : Filtrage et transformation avec SMT

### Objectif
Modifier les messages CDC avant qu'ils n'atteignent Kafka.

### Configuration avec SMT

```json
// config/mysql-with-smt.json
{
    "name": "mysql-smt-connector",
    "config": {
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        "database.hostname": "localhost",
        "database.port": "3306",
        "database.user": "debezium",
        "database.password": "dbzpass",
        "database.server.id": "184056",
        "database.server.name": "smt-mysql",
        "database.include.list": "testdb",
        "table.include.list": "testdb.users",
        "database.history.kafka.bootstrap.servers": "localhost:9092",
        "database.history.kafka.topic": "schema-changes.smt",
        
        "transforms": "mask_email,rename_field,filter",
        
        "transforms.mask_email.type": "org.apache.kafka.connect.transforms.MaskField$Value",
        "transforms.mask_email.fields": "email",
        "transforms.mask_email.replacement": "***@***.com",
        
        "transforms.rename_field.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
        "transforms.rename_field.renames": "name:full_name",
        
        "transforms.filter.type": "io.debezium.transforms.Filter",
        "transforms.filter.language": "jsr223.groovy",
        "transforms.filter.condition": "value.op != 'd'",
        
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter"
    }
}
```

### SMT personnalisé en Java

```java
// com/example/tp6_smt/CustomSMT.java
package com.example.tp6_smt;

import org.apache.kafka.connect.connector.ConnectRecord;
import org.apache.kafka.connect.data.Struct;
import org.apache.kafka.connect.transforms.Transformation;
import org.apache.kafka.connect.transforms.util.SimpleConfig;
import java.util.Map;

public class CustomSMT<R extends ConnectRecord<R>> implements Transformation<R> {
    
    @Override
    public R apply(R record) {
        Struct value = (Struct) record.value();
        if (value != null) {
            Struct after = value.getStruct("after");
            if (after != null) {
                String name = after.getString("name");
                // Ajouter un champ "name_upper" si le nom existe
                after.put("name_upper", name != null ? name.toUpperCase() : null);
            }
        }
        return record;
    }
    
    @Override
    public void configure(Map<String, ?> configs) {}
    
    @Override
    public void close() {}
}
```

### Résultat après SMT

```json
{
    "before": null,
    "after": {"id": 3, "full_name": "David", "email": "***@***.com", "name_upper": "DAVID"},
    "op": "c"
}
```

---

## 8. TP7 : Connecteur Debezium PostgreSQL

### Docker Compose PostgreSQL

```yaml
# docker-compose-postgres.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: postgres-debezium
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgrespass
    ports:
      - "5432:5432"
    command: |
      postgres 
      -c wal_level=logical
      -c max_replication_slots=10
      -c max_wal_senders=10
```

### Configuration PostgreSQL pour CDC

```bash
docker exec -it postgres-debezium psql -U postgres -d testdb

# Créer une table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

CREATE TABLE public.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

ALTER TABLE products REPLICA IDENTITY FULL;

INSERT INTO products (name, price) VALUES ('Laptop', 999.99), ('Mouse', 19.99);
```

### Configuration connecteur PostgreSQL

```json
// config/postgres-source.json
{
    "name": "postgres-debezium-connector",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "tasks.max": "1",
        "database.hostname": "localhost",
        "database.port": "5432",
        "database.user": "postgres",
        "database.password": "postgrespass",
        "database.dbname": "testdb",
        "database.server.name": "postgres-server",
        "plugin.name": "pgoutput",
        "table.include.list": "public.products",
        "snapshot.mode": "initial",
        "publication.name": "dbz_publication",
        "slot.name": "debezium_slot",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter"
    }
}
```

### Test CDC PostgreSQL

```sql
INSERT INTO products (name, price) VALUES ('Keyboard', 49.99);
UPDATE products SET price = 899.99 WHERE name = 'Laptop';
DELETE FROM products WHERE name = 'Mouse';
```

```bash
bin/kafka-console-consumer --topic postgres-server.public.products --bootstrap-server localhost:9092 --from-beginning
```

---

## 9. TP8 : Connecteur Debezium MongoDB

### Docker Compose MongoDB

```yaml
# docker-compose-mongo.yml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb-debezium
    ports:
      - "27017:27017"
    command: ["--replSet", "rs0", "--bind_ip_all"]
```

```bash
docker-compose -f docker-compose-mongo.yml up -d

# Initialiser le replica set
docker exec -it mongodb-debezium mongosh --eval 'rs.initiate({_id:"rs0", members:[{_id:0, host:"localhost:27017"}]})'
```

### Configuration connecteur MongoDB

```json
// config/mongodb-source.json
{
    "name": "mongodb-debezium-connector",
    "config": {
        "connector.class": "io.debezium.connector.mongodb.MongoDbConnector",
        "tasks.max": "1",
        "mongodb.hosts": "rs0/localhost:27017",
        "mongodb.name": "mongo-server",
        "mongodb.user": "",
        "mongodb.password": "",
        "database.include.list": "testdb",
        "collection.include.list": "testdb.users",
        "snapshot.mode": "initial",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter"
    }
}
```

### Test MongoDB

```javascript
use testdb;
db.users.insertOne({name: "Alice", email: "alice@example.com", age: 28});
db.users.updateOne({name: "Alice"}, {$set: {age: 29}});
db.users.deleteOne({name: "Alice"});
```

---

## 10. TP9 : Connecteur HTTP Sink (webhooks)

### Objectif
Envoyer des messages Kafka vers des endpoints HTTP externes.

### Configuration

```json
// config/http-sink.json
{
    "name": "http-sink-connector",
    "config": {
        "connector.class": "io.confluent.connect.http.HttpSinkConnector",
        "tasks.max": "1",
        "topics": "cdc-mysql.testdb.users",
        "http.api.url": "http://localhost:8080/webhook",
        "request.method": "POST",
        "request.content.type": "application/json",
        "batch.size": "1",
        "http.connect.timeout.ms": "5000",
        "http.read.timeout.ms": "10000",
        "headers": "X-Source:Kafka,Content-Type:application/json",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter"
    }
}
```

### Serveur HTTP de test (Node.js)

```javascript
// webhook-server.js
const express = require('express');
const app = express();
app.use(express.json());

app.post('/webhook', (req, res) => {
    console.log('Reçu:', req.body);
    res.status(200).send('OK');
});

app.listen(8080, () => console.log('Webhook sur 8080'));
```

---

## 11. TP10 : Connecteur Elasticsearch Sink

### Docker Compose Elasticsearch

```yaml
# docker-compose-elastic.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
```

### Configuration connecteur Elasticsearch

```json
// config/elastic-sink.json
{
    "name": "elastic-sink-connector",
    "config": {
        "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        "tasks.max": "1",
        "topics": "cdc-mysql.testdb.users",
        "connection.url": "http://localhost:9200",
        "type.name": "_doc",
        "key.ignore": "false",
        "schema.ignore": "true",
        "write.method": "upsert",
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter"
    }
}
```

### Vérification dans Elasticsearch

```bash
curl -X GET "localhost:9200/users/_search?pretty"
```

---

## 12. TP11 : API REST Kafka Connect – gestion des connecteurs

### Commandes essentielles

```bash
# 1. Lister les connecteurs
curl -X GET http://localhost:8083/connectors

# 2. Créer un connecteur
curl -X POST http://localhost:8083/connectors \
    -H "Content-Type: application/json" \
    --data @config/mysql-source.json

# 3. Vérifier le statut
curl -X GET http://localhost:8083/connectors/mysql-debezium-connector/status

# 4. Modifier un connecteur
curl -X PUT http://localhost:8083/connectors/mysql-debezium-connector/config \
    -H "Content-Type: application/json" \
    --data @config/mysql-updated.json

# 5. Redémarrer un connecteur
curl -X POST http://localhost:8083/connectors/mysql-debezium-connector/restart

# 6. Redémarrer une tâche spécifique
curl -X POST http://localhost:8083/connectors/mysql-debezium-connector/tasks/0/restart

# 7. Supprimer un connecteur
curl -X DELETE http://localhost:8083/connectors/mysql-debezium-connector

# 8. Obtenir la configuration
curl -X GET http://localhost:8083/connectors/mysql-debezium-connector/config

# 9. Obtenir les plugins disponibles
curl -X GET http://localhost:8083/connector-plugins

# 10. Pause/Resume
curl -X PUT http://localhost:8083/connectors/mysql-debezium-connector/pause
curl -X PUT http://localhost:8083/connectors/mysql-debezium-connector/resume
```

---

## 13. TP12 : Client Java pour Kafka Connect API

### Code complet

```java
// com/example/tp12_client/KafkaConnectClient.java
package com.example.tp12_client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * TP12 : Client Java pour l'API REST Kafka Connect
 * 
 * Objectif : Gérer les connecteurs programmatiquement depuis Java.
 * 
 * Prérequis : Kafka Connect démarré sur localhost:8083
 * 
 * Fonctionnalités :
 * - Lister les connecteurs
 * - Créer/supprimer des connecteurs
 * - Vérifier le statut
 * - Redémarrer des connecteurs/tâches
 */
public class KafkaConnectClient {
    
    private static final String CONNECT_URL = "http://localhost:8083";
    private static final HttpClient client = HttpClient.newHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();
    
    /**
     * Lister tous les connecteurs actifs
     */
    public static void listConnectors() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors"))
            .timeout(Duration.ofSeconds(10))
            .GET()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode connectors = mapper.readTree(response.body());
        
        System.out.println("=== Connecteurs actifs ===");
        for (JsonNode connector : connectors) {
            System.out.println("- " + connector.asText());
            getConnectorStatus(connector.asText());
        }
    }
    
    /**
     * Créer un connecteur source (Debezium MySQL)
     */
    public static void createMySqlConnector() throws Exception {
        ObjectNode config = mapper.createObjectNode();
        config.put("connector.class", "io.debezium.connector.mysql.MySqlConnector");
        config.put("tasks.max", 1);
        config.put("database.hostname", "localhost");
        config.put("database.port", 3306);
        config.put("database.user", "debezium");
        config.put("database.password", "dbzpass");
        config.put("database.server.id", 184057);
        config.put("database.server.name", "java-mysql");
        config.put("database.include.list", "testdb");
        config.put("table.include.list", "testdb.users");
        config.put("database.history.kafka.bootstrap.servers", "localhost:9092");
        config.put("database.history.kafka.topic", "schema-changes.java");
        config.put("snapshot.mode", "initial");
        
        ObjectNode connectorJson = mapper.createObjectNode();
        connectorJson.set("config", config);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/mysql-java-connector"))
            .timeout(Duration.ofSeconds(30))
            .header("Content-Type", "application/json")
            .PUT(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(connectorJson)))
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Création connecteur : " + response.statusCode());
        System.out.println("Réponse : " + response.body());
    }
    
    /**
     * Vérifier le statut d'un connecteur et de ses tâches
     */
    public static void getConnectorStatus(String connectorName) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName + "/status"))
            .GET()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode status = mapper.readTree(response.body());
        
        System.out.println("  Statut: " + status.path("connector").path("state").asText());
        System.out.println("  Tâches: " + status.path("tasks").size());
        for (JsonNode task : status.path("tasks")) {
            System.out.println("    - Tâche " + task.path("id").asInt() + ": " + task.path("state").asText());
        }
    }
    
    /**
     * Redémarrer un connecteur (utile après une erreur)
     */
    public static void restartConnector(String connectorName) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName + "/restart"))
            .POST(HttpRequest.BodyPublishers.noBody())
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Redémarrage du connecteur " + connectorName + ": " + response.statusCode());
    }
    
    /**
     * Redémarrer une tâche spécifique
     */
    public static void restartTask(String connectorName, int taskId) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName + "/tasks/" + taskId + "/restart"))
            .POST(HttpRequest.BodyPublishers.noBody())
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Redémarrage tâche " + taskId + ": " + response.statusCode());
    }
    
    /**
     * Supprimer un connecteur
     */
    public static void deleteConnector(String connectorName) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName))
            .DELETE()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Suppression de " + connectorName + ": " + response.statusCode());
    }
    
    /**
     * Obtenir la configuration d'un connecteur
     */
    public static void getConnectorConfig(String connectorName) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName))
            .GET()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Configuration de " + connectorName + ":");
        System.out.println(response.body());
    }
    
    /**
     * Mettre à jour la configuration d'un connecteur
     */
    public static void updateConnectorConfig(String connectorName, Map<String, String> updates) throws Exception {
        // D'abord récupérer la config actuelle
        HttpRequest getRequest = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName + "/config"))
            .GET()
            .build();
        
        HttpResponse<String> getResponse = client.send(getRequest, HttpResponse.BodyHandlers.ofString());
        ObjectNode config = (ObjectNode) mapper.readTree(getResponse.body());
        
        // Appliquer les mises à jour
        updates.forEach((key, value) -> config.put(key, value));
        
        ObjectNode connectorJson = mapper.createObjectNode();
        connectorJson.set("config", config);
        
        // Mettre à jour
        HttpRequest putRequest = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connectors/" + connectorName + "/config"))
            .header("Content-Type", "application/json")
            .PUT(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(connectorJson)))
            .build();
        
        HttpResponse<String> putResponse = client.send(putRequest, HttpResponse.BodyHandlers.ofString());
        System.out.println("Mise à jour config: " + putResponse.statusCode());
    }
    
    /**
     * Lister les plugins disponibles
     */
    public static void listPlugins() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(CONNECT_URL + "/connector-plugins"))
            .GET()
            .build();
        
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode plugins = mapper.readTree(response.body());
        
        System.out.println("=== Plugins disponibles ===");
        for (JsonNode plugin : plugins) {
            System.out.println("- " + plugin.path("class").asText());
        }
    }
    
    /**
     * Méthode principale : démonstration complète
     */
    public static void main(String[] args) throws Exception {
        System.out.println("=== Gestion des connecteurs via API REST ===\n");
        
        // 1. Lister les connecteurs existants
        listConnectors();
        
        // 2. Lister les plugins disponibles
        listPlugins();
        
        // 3. Créer un nouveau connecteur MySQL
        System.out.println("\n=== Création d'un nouveau connecteur ===");
        createMySqlConnector();
        
        // 4. Attendre un peu que le connecteur démarre
        Thread.sleep(2000);
        
        // 5. Vérifier le statut
        System.out.println("\n=== Statut du connecteur ===");
        getConnectorStatus("mysql-java-connector");
        
        // 6. Obtenir la configuration
        System.out.println("\n=== Configuration du connecteur ===");
        getConnectorConfig("mysql-java-connector");
        
        // 7. Exemple de mise à jour (changer le polling interval)
        Map<String, String> updates = new HashMap<>();
        updates.put("poll.interval.ms", "10000");
        System.out.println("\n=== Mise à jour de la configuration ===");
        updateConnectorConfig("mysql-java-connector", updates);
        
        // 8. Redémarrer si nécessaire
        System.out.println("\n=== Redémarrage du connecteur ===");
        restartConnector("mysql-java-connector");
        
        // 9. Nettoyage : supprimer le connecteur (décommenter pour supprimer)
        // System.out.println("\n=== Suppression du connecteur ===");
        // deleteConnector("mysql-java-connector");
        
        System.out.println("\n=== Fin de la démonstration ===");
    }
}
```

### Configuration Maven complète

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>kafka-connect-tp</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <kafka.version>3.6.0</kafka.version>
        <debezium.version>2.4.0</debezium.version>
        <jackson.version>2.15.2</jackson.version>
    </properties>

    <repositories>
        <repository>
            <id>confluent</id>
            <url>https://packages.confluent.io/maven/</url>
        </repository>
    </repositories>

    <dependencies>
        <!-- Kafka Connect API -->
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>connect-api</artifactId>
            <version>${kafka.version}</version>
        </dependency>
        
        <!-- Kafka Connect Transforms -->
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>connect-transforms</artifactId>
            <version>${kafka.version}</version>
        </dependency>
        
        <!-- Debezium Core -->
        <dependency>
            <groupId>io.debezium</groupId>
            <artifactId>debezium-core</artifactId>
            <version>${debezium.version}</version>
        </dependency>
        
        <!-- Debezium MySQL Connector -->
        <dependency>
            <groupId>io.debezium</groupId>
            <artifactId>debezium-connector-mysql</artifactId>
            <version>${debezium.version}</version>
        </dependency>
        
        <!-- Debezium PostgreSQL Connector -->
        <dependency>
            <groupId>io.debezium</groupId>
            <artifactId>debezium-connector-postgres</artifactId>
            <version>${debezium.version}</version>
        </dependency>
        
        <!-- JDBC Connector Confluent -->
        <dependency>
            <groupId>io.confluent</groupId>
            <artifactId>kafka-connect-jdbc</artifactId>
            <version>10.7.4</version>
        </dependency>
        
        <!-- H2 Database pour tests -->
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <version>2.2.224</version>
            <scope>test</scope>
        </dependency>
        
        <!-- Jackson pour JSON -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>${jackson.version}</version>
        </dependency>
        
        <!-- Logging -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-simple</artifactId>
            <version>2.0.9</version>
        </dependency>
        
        <!-- Tests -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.1</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <release>17</release>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.5.0</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

---

## Récapitulatif des résultats

| TP | Thème | Résultat attendu |
|----|-------|------------------|
| 1 | Connecteur fichier | Lecture/écriture de fichiers avec Kafka Connect |
| 2 | JDBC Source H2 | Import des données H2 vers Kafka |
| 3 | JDBC Sink | Export des données Kafka vers H2 |
| 4 | Debezium MySQL – Setup | Connecteur MySQL configuré et prêt |
| 5 | Debezium MySQL – CDC | Capture des INSERT/UPDATE/DELETE |
| 6 | SMT Transformations | Modification des messages CDC (masquage, filtrage) |
| 7 | Debezium PostgreSQL | CDC avec PostgreSQL |
| 8 | Debezium MongoDB | CDC avec MongoDB |
| 9 | HTTP Sink | Envoi de messages vers webhook |
| 10 | Elasticsearch Sink | Indexation des changements dans Elasticsearch |
| 11 | API REST Connect | Gestion des connecteurs via curl |
| 12 | Client Java Connect | Gestion programmatique des connecteurs |

---

## 💡 Définitions et Tips supplémentaires

### Définitions clés
- **Binlog (MySQL)** : Binary Log – journal des modifications de la base.
- **WAL (PostgreSQL)** : Write-Ahead Log – pré-écriture des modifications.
- **Oplog (MongoDB)** : Operation Log – journal des opérations pour replica sets.
- **Snapshot** : Capture initiale de l'état existant avant de suivre les changements.
- **LSN (Log Sequence Number)** : Position dans le log PostgreSQL.
- **GTID (Global Transaction ID)** : Identifiant unique de transaction (MySQL).

### Tips pour la production

1. **Utiliser Avro Converter** avec Schema Registry pour l'évolution des schémas.
2. **Configurer la tolérance aux pannes** : `errors.tolerance=all` + `errors.deadletterqueue.topic.name`
3. **Surveiller les délais** : `consumer.max.poll.records`, `task.max.retries`
4. **Pour Debezium** :
   - Définir `snapshot.mode=when_needed` pour éviter les snapshots répétés
   - Configurer `slot.name` pour PostgreSQL (un slot par connecteur)
   - Utiliser `table.include.list` pour limiter les tables capturées
5. **En KRaft** : Pas de ZooKeeper, mais vérifier que les topics internes de Connect sont créés automatiquement.

---

## 🚀 Exécution rapide

```bash
# 1. Démarrer Kafka KRaft
cd kafka-3.6.0
bin/kafka-storage.sh format -t <UUID> -c config/kraft/server.properties
bin/kafka-server-start.sh config/kraft/server.properties

# 2. Démarrer Kafka Connect
bin/connect-distributed.sh config/connect-distributed.properties

# 3. Démarrer les bases (Docker)
docker-compose -f docker-compose-mysql.yml up -d
docker-compose -f docker-compose-postgres.yml up -d

# 4. Télécharger les plugins Debezium dans plugin.path

# 5. Créer les connecteurs via API REST
curl -X POST -H "Content-Type: application/json" --data @config/mysql-source.json http://localhost:8083/connectors

# 6. Compiler et exécuter le client Java
mvn clean compile exec:java -Dexec.mainClass="com.example.tp12_client.KafkaConnectClient"
```

Ces 12 TPs couvrent l'écosystème complet de Kafka Connect et CDC avec Debezium, sur une architecture moderne sans ZooKeeper. Chaque TP est commenté, testable et prêt pour la production.
