# 📘 **Kafka Connect & Debezium CDC – Cheat Sheet Complet**

## Guide ultime avec concepts, exemples, tuning, bonnes pratiques et tips

---

## 1. 🏗️ **Concepts Fondamentaux**

### Définitions clés

| Concept | Définition | Rôle |
|---------|------------|------|
| **Kafka Connect** | Framework d'intégration entre Kafka et systèmes externes | ETL distribué |
| **Source Connector** | Importe des données vers Kafka (source → Kafka) | Producteur |
| **Sink Connector** | Exporte des données depuis Kafka (Kafka → destination) | Consommateur |
| **Task** | Unité de travail parallélisée d'un connecteur | Worker |
| **Converter** | Transforme les données (JSON, Avro, Protobuf) | Sérialisation |
| **SMT** | Single Message Transform – modifie chaque message | Transformation |
| **CDC (Change Data Capture)** | Capture les changements DB (INSERT, UPDATE, DELETE) | Réplication |
| **Debezium** | Plateforme CDC basée sur Kafka Connect | Capture DB |
| **Binlog** | Binary Log (MySQL) – journal des modifications | Source CDC |
| **WAL** | Write-Ahead Log (PostgreSQL) | Source CDC |
| **Oplog** | Operation Log (MongoDB) | Source CDC |
| **Snapshot** | État initial d'une table au démarrage | Initial load |
| **Offset** | Position dans le log (binlog position, LSN) | Reprise |
| **Connector State** | RUNNING, PAUSED, FAILED, RESTARTING | Monitoring |
| **DLQ** | Dead Letter Queue – messages en erreur | Tolérance |

### Types de connecteurs

```java
// 1. Source Connector (import)
SourceConnector → Kafka
- JDBC Source (bases relationnelles)
- Debezium CDC (binlog/WAL)
- File Source (fichiers)
- HTTP Source (webhooks)

// 2. Sink Connector (export)
Kafka → SinkConnector
- JDBC Sink (bases)
- Elasticsearch Sink
- S3 Sink
- HTTP Sink
```

### Modes de déploiement

```properties
# Standalone (développement, 1 worker)
bin/connect-standalone.sh worker.properties connector1.properties

# Distribué (production, cluster)
bin/connect-distributed.sh worker.properties
# API REST pour gestion connecteurs
```

---

## 2. 🚀 **Configuration Optimale**

### Connect Worker (connect-distributed.properties)

```properties
# ========== Base ==========
bootstrap.servers=kafka1:9092,kafka2:9092,kafka3:9092
group.id=connect-cluster-prod
rest.port=8083
rest.host.name=0.0.0.0

# ========== Performance ==========
tasks.max=8
worker.sync.timeout.ms=3000
worker.unsync.backoff.ms=300000

# ========== Offset et état ==========
offset.storage.topic=connect-offsets
offset.storage.replication.factor=3
offset.storage.partitions=25

config.storage.topic=connect-configs
config.storage.replication.factor=3

status.storage.topic=connect-status
status.storage.replication.factor=3

# ========== Converters ==========
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false

# Pour Avro avec Schema Registry
key.converter=io.confluent.connect.avro.AvroConverter
key.converter.schema.registry.url=http://schema-registry:8081
value.converter=io.confluent.connect.avro.AvroConverter
value.converter.schema.registry.url=http://schema-registry:8081

# ========== Tolérance pannes ==========
errors.tolerance=all
errors.deadletterqueue.topic.name=connect-dlq
errors.deadletterqueue.topic.replication.factor=3
errors.retry.timeout=300000
errors.retry.delay.max.ms=60000

# ========== Sécurité ==========
# SASL/SSL
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
    username="connect" password="password";

ssl.truststore.location=/etc/kafka/secrets/kafka.truststore.jks
ssl.truststore.password=password

# ========== Monitoring ==========
consumer.auto.offset.reset=earliest
producer.compression.type=snappy
producer.batch.size=16384
producer.linger.ms=100
```

### Debezium MySQL Connector

```json
{
    "name": "mysql-cdc-prod",
    "config": {
        // ========== Base ==========
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        "tasks.max": "4",
        "database.hostname": "mysql.example.com",
        "database.port": "3306",
        "database.user": "debezium",
        "database.password": "password",
        "database.server.id": "184054",
        "database.server.name": "mysql-prod",
        
        // ========== Inclusion/Exclusion ==========
        "database.include.list": "sales,hr",
        "table.include.list": "sales.orders,hr.employees",
        "column.exclude.list": "password,ssn",
        
        // ========== Historique ==========
        "database.history.kafka.bootstrap.servers": "kafka:9092",
        "database.history.kafka.topic": "schema-changes.prod",
        "database.history.kafka.recovery.poll.interval.ms": "10000",
        
        // ========== Snapshot ==========
        "snapshot.mode": "when_needed",
        "snapshot.locking.mode": "minimal",
        "snapshot.fetch.size": "2000",
        
        // ========== Performance ==========
        "max.batch.size": "2048",
        "max.queue.size": "8192",
        "poll.interval.ms": "1000",
        "event.processing.failure.handling.mode": "skip",
        
        // ========== Timeouts ==========
        "connect.timeout.ms": "30000",
        "connection.pool.size": "20",
        "keepalive.interval.ms": "300000",
        
        // ========== Format ==========
        "key.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "key.converter.schemas.enable": "false",
        "value.converter.schemas.enable": "false",
        
        // ========== Data Types ==========
        "decimal.handling.mode": "precise",
        "time.precision.mode": "adaptive_time_microseconds",
        "binary.handling.mode": "hex",
        "bigint.unsigned.handling.mode": "long",
        
        // ========== SMT ==========
        "transforms": "unwrap,route,extract",
        "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
        "transforms.unwrap.drop.tombstones": "true",
        "transforms.unwrap.delete.handling.mode": "rewrite",
        
        "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
        "transforms.route.regex": "mysql-prod.([^.]+).([^.]+)",
        "transforms.route.replacement": "cdc-$1-$2",
        
        "transforms.extract.type": "org.apache.kafka.connect.transforms.ExtractField$Value",
        "transforms.extract.field": "after"
    }
}
```

---

## 3. 📝 **Patterns et Bonnes Pratiques**

### Pattern 1: Configuration modulaire

```java
// ConfigurationManager.java
package com.example.connect;

import org.apache.kafka.common.config.AbstractConfig;
import org.apache.kafka.common.config.ConfigDef;
import java.util.Map;

public class ConfigurationManager {
    
    public static Map<String, String> getBaseConnectorConfig() {
        return Map.of(
            "connector.class", "io.debezium.connector.mysql.MySqlConnector",
            "tasks.max", "4",
            "key.converter", "org.apache.kafka.connect.json.JsonConverter",
            "value.converter", "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable", "false",
            "value.converter.schemas.enable", "false"
        );
    }
    
    public static Map<String, String> getDebeziumConfig(String dbHost, String dbUser, String dbPass) {
        Map<String, String> config = getBaseConnectorConfig();
        config.putAll(Map.of(
            "database.hostname", dbHost,
            "database.user", dbUser,
            "database.password", dbPass,
            "snapshot.mode", "when_needed",
            "errors.tolerance", "all",
            "errors.deadletterqueue.topic.name", "dlq-connector"
        ));
        return config;
    }
}
```

### Pattern 2: Gestion des erreurs avancée

```json
{
    "name": "resilient-connector",
    "config": {
        // Tolérance globale
        "errors.tolerance": "all",
        
        // Dead Letter Queue
        "errors.deadletterqueue.topic.name": "connect-dlq",
        "errors.deadletterqueue.topic.replication.factor": "3",
        "errors.deadletterqueue.context.headers.enable": "true",
        
        // Retry policy
        "errors.retry.timeout": "300000",
        "errors.retry.delay.max.ms": "60000",
        
        // Per-task error handling
        "task.max.retries": "10",
        "task.retry.backoff.ms": "5000",
        
        // Logging
        "log.enabled": "true",
        "log.include.message": "true"
    }
}
```

### Pattern 3: SMT personnalisé

```java
// CustomMaskingSMT.java
package com.example.connect.smt;

import org.apache.kafka.connect.connector.ConnectRecord;
import org.apache.kafka.connect.data.Struct;
import org.apache.kafka.connect.transforms.Transformation;
import org.apache.kafka.connect.transforms.util.SimpleConfig;
import java.util.Map;

public class CustomMaskingSMT<R extends ConnectRecord<R>> implements Transformation<R> {
    
    private static final String FIELDS_CONFIG = "fields";
    private static final String REPLACEMENT_CONFIG = "replacement";
    
    private String[] fields;
    private String replacement;
    
    @Override
    public R apply(R record) {
        if (record.value() instanceof Struct) {
            Struct value = (Struct) record.value();
            
            // Masquage des champs sensibles
            for (String field : fields) {
                if (value.schema().field(field) != null) {
                    value.put(field, replacement);
                }
            }
            
            // Ajout de métadonnées
            value.put("__processed_at", System.currentTimeMillis());
            value.put("__connector_version", "1.0");
        }
        return record;
    }
    
    @Override
    public ConfigDef config() {
        return new ConfigDef()
            .define(FIELDS_CONFIG, ConfigDef.Type.LIST, ConfigDef.Importance.HIGH, "Fields to mask")
            .define(REPLACEMENT_CONFIG, ConfigDef.Type.STRING, "***", ConfigDef.Importance.MEDIUM, "Replacement string");
    }
    
    @Override
    public void close() {}
    
    @Override
    public void configure(Map<String, ?> configs) {
        final SimpleConfig config = new SimpleConfig(config(), configs);
        this.fields = config.getList(FIELDS_CONFIG).toArray(new String[0]);
        this.replacement = config.getString(REPLACEMENT_CONFIG);
    }
}
```

### Pattern 4: Monitoring avancé

```java
// ConnectorMonitor.java
package com.example.connect.monitoring;

import org.apache.kafka.connect.runtime.rest.client.ConnectRestClient;
import org.apache.kafka.connect.runtime.rest.entities.ConnectorInfo;
import org.apache.kafka.connect.runtime.rest.entities.ConnectorStateInfo;

import javax.management.*;
import java.lang.management.ManagementFactory;

public class ConnectorMonitor implements NotificationListener {
    
    private final ConnectRestClient client;
    private final MBeanServer mBeanServer;
    
    public ConnectorMonitor(String connectUrl) {
        this.client = new ConnectRestClient(connectUrl);
        this.mBeanServer = ManagementFactory.getPlatformMBeanServer();
        registerJMXListeners();
    }
    
    private void registerJMXListeners() {
        try {
            ObjectName name = new ObjectName("kafka.connect:type=connect-worker-metrics");
            mBeanServer.addNotificationListener(name, this, null, null);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public void monitorConnector(String connectorName) {
        new Thread(() -> {
            while (true) {
                try {
                    ConnectorStateInfo state = client.connectorStatus(connectorName);
                    System.out.printf("Connector: %s | State: %s | Tasks: %d%n",
                        connectorName,
                        state.connector().state(),
                        state.tasks().size()
                    );
                    
                    // Vérification des tasks
                    for (ConnectorStateInfo.TaskState task : state.tasks()) {
                        if (!task.state().equals("RUNNING")) {
                            System.err.printf("Task %d failed: %s%n", task.id(), task.trace());
                            restartTask(connectorName, task.id());
                        }
                    }
                    
                    Thread.sleep(10000);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }).start();
    }
    
    private void restartTask(String connectorName, int taskId) {
        try {
            client.restartTask(connectorName, taskId);
            System.out.printf("Restarted task %d for connector %s%n", taskId, connectorName);
        } catch (Exception e) {
            System.err.printf("Failed to restart task: %s%n", e.getMessage());
        }
    }
    
    @Override
    public void handleNotification(Notification notification, Object handback) {
        System.out.printf("JMX Notification: %s - %s%n", 
            notification.getType(), notification.getMessage());
    }
}
```

---

## 4. ⚡ **Optimisations Performance**

### Tuning Debezium MySQL

```json
{
    "config": {
        // Batch processing
        "max.batch.size": "4096",
        "max.queue.size": "16384",
        "max.queue.size.in.bytes": "0",
        
        // Polling
        "poll.interval.ms": "100",
        "max.iteration.transactions": "100",
        
        // Connection pool
        "connection.pool.size": "30",
        "connect.timeout.ms": "30000",
        "keepalive.interval.ms": "300000",
        
        // Snapshot performance
        "snapshot.fetch.size": "5000",
        "snapshot.delay.ms": "100",
        
        // Binary log
        "binlog.buffer.size": "0",
        "binlog.offset.flush.interval.ms": "60000",
        
        // Event processing
        "event.processing.failure.handling.mode": "warn",
        "inconsistent.schema.handling.mode": "warn"
    }
}
```

### Tuning Debezium PostgreSQL

```json
{
    "config": {
        // Slot configuration
        "slot.name": "debezium_slot",
        "slot.max.retries": "10",
        "slot.retry.delay.ms": "10000",
        
        // WAL streaming
        "plugin.name": "pgoutput",
        "publication.name": "dbz_publication",
        "publication.autocreate.mode": "filtered",
        
        // Performance
        "max.batch.size": "2048",
        "max.queue.size": "8192",
        "poll.interval.ms": "1000",
        
        // Replication
        "replication.flush.timeout.ms": "10000",
        "replication.slot.drop.on.stop": "false"
    }
}
```

### Tuning JDBC Sink

```json
{
    "config": {
        // Batch configuration
        "batch.size": "3000",
        "max.retries": "10",
        "retry.backoff.ms": "5000",
        
        // Connection pool
        "connection.pool.max.size": "20",
        "connection.pool.min.size": "5",
        
        // Write modes
        "insert.mode": "upsert",
        "delete.enabled": "true",
        
        // Transaction
        "transaction.boundary": "poll",
        "auto.create": "true",
        "auto.evolve": "true"
    }
}
```

---

## 5. 🔧 **Débogage et Monitoring**

### Commandes API REST

```bash
# ========== Connecteurs ==========
# Lister les connecteurs
curl -X GET http://localhost:8083/connectors

# Créer un connecteur
curl -X POST http://localhost:8083/connectors \
    -H "Content-Type: application/json" \
    --data @connector.json

# Voir détails d'un connecteur
curl -X GET http://localhost:8083/connectors/my-connector

# Voir statut
curl -X GET http://localhost:8083/connectors/my-connector/status

# Voir configuration
curl -X GET http://localhost:8083/connectors/my-connector/config

# Mettre à jour configuration
curl -X PUT http://localhost:8083/connectors/my-connector/config \
    -H "Content-Type: application/json" \
    --data @new-config.json

# Redémarrer connecteur
curl -X POST http://localhost:8083/connectors/my-connector/restart

# Redémarrer une tâche
curl -X POST http://localhost:8083/connectors/my-connector/tasks/0/restart

# Pause/Resume
curl -X PUT http://localhost:8083/connectors/my-connector/pause
curl -X PUT http://localhost:8083/connectors/my-connector/resume

# Supprimer connecteur
curl -X DELETE http://localhost:8083/connectors/my-connector

# ========== Plugins ==========
# Lister les plugins disponibles
curl -X GET http://localhost:8083/connector-plugins

# Voir configuration d'un plugin
curl -X GET http://localhost:8083/connector-plugins/MyConnector/config/validate

# ========== Workers ==========
# Voir les workers actifs
curl -X GET http://localhost:8083/connectors/active

# ========== Logs ==========
# Configurer log4j dynamiquement
curl -X POST http://localhost:8083/admin/loggers/debezium \
    -H "Content-Type: application/json" \
    -d '{"level": "DEBUG"}'
```

### Métriques JMX essentielles

```java
// Métriques Kafka Connect
kafka.connect:type=connect-worker-metrics
  - connector-count
  - task-count
  - connector-startup-attempts-total
  - connector-startup-success-total
  - connector-startup-failure-total

kafka.connect:type=connector-metrics,connector="{connector}"
  - records-sent-rate
  - records-sent-total
  - records-consumed-rate
  - records-consumed-total

kafka.connect:type=task-metrics,connector="{connector}",task="{task}"
  - batch-size-avg
  - batch-size-max
  - offset-commit-avg-time-ms
  - offset-commit-max-time-ms

// Métriques Debezium
debezium.mysql:type=connector-metrics,context=snapshot,server={server}
  - snapshot-completed
  - snapshot-duration-seconds
  - snapshot-number-of-events

debezium.mysql:type=connector-metrics,context=streaming,server={server}
  - binlog-position
  - connected
  - current-gtid
  - milliseconds-behind-source
```

### Debug avec des topics internes

```bash
# 1. Voir les offsets du connecteur
kafka-console-consumer --topic connect-offsets \
    --bootstrap-server localhost:9092 \
    --property print.key=true \
    --from-beginning | head -20

# 2. Voir la configuration
kafka-console-consumer --topic connect-configs \
    --bootstrap-server localhost:9092 \
    --property print.key=true \
    --from-beginning

# 3. Voir les status
kafka-console-consumer --topic connect-status \
    --bootstrap-server localhost:9092 \
    --property print.key=true \
    --from-beginning

# 4. Voir le schema history (Debezium)
kafka-console-consumer --topic schema-changes.testdb \
    --bootstrap-server localhost:9092 \
    --from-beginning

# 5. Voir la DLQ
kafka-console-consumer --topic connect-dlq \
    --bootstrap-server localhost:9092 \
    --property print.headers=true \
    --from-beginning
```

---

## 6. 🎯 **Exemples par Cas d'Usage**

### Cas 1: CDC MySQL vers Elasticsearch

```json
// mysql-source.json
{
    "name": "mysql-cdc-elasticsearch",
    "config": {
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        "database.hostname": "mysql",
        "database.port": "3306",
        "database.user": "debezium",
        "database.password": "password",
        "database.server.id": "1",
        "database.server.name": "mysql",
        "database.include.list": "ecommerce",
        "table.include.list": "ecommerce.products,ecommerce.orders",
        "database.history.kafka.bootstrap.servers": "kafka:9092",
        "database.history.kafka.topic": "schema-changes.ecommerce",
        "transforms": "unwrap",
        "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
        "transforms.unwrap.drop.tombstones": "false",
        "transforms.unwrap.delete.handling.mode": "rewrite"
    }
}

// elasticsearch-sink.json
{
    "name": "elasticsearch-sink",
    "config": {
        "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        "tasks.max": "4",
        "topics": "mysql.ecommerce.products,mysql.ecommerce.orders",
        "connection.url": "http://elasticsearch:9200",
        "type.name": "_doc",
        "key.ignore": "false",
        "schema.ignore": "true",
        "write.method": "upsert",
        "behavior.on.null.values": "delete",
        "max.buffered.records": "5000",
        "flush.timeout.ms": "10000",
        "retry.on.conflict": "true",
        "max.retries": "10"
    }
}
```

### Cas 2: PostgreSQL vers S3 (parquet)

```json
{
    "name": "postgres-s3-connector",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "postgres",
        "database.port": "5432",
        "database.user": "debezium",
        "database.password": "password",
        "database.dbname": "analytics",
        "database.server.name": "postgres",
        "plugin.name": "pgoutput",
        "table.include.list": "public.events",
        "transforms": "unwrap,convert",
        "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
        "transforms.convert.type": "org.apache.kafka.connect.transforms.Cast$Value",
        "transforms.convert.spec": "timestamp:string",
        
        "s3.sink.connector.class": "io.confluent.connect.s3.S3SinkConnector",
        "s3.bucket.name": "data-lake",
        "s3.region": "us-east-1",
        "s3.part.size": "5242880",
        "flush.size": "10000",
        "format.class": "io.confluent.connect.s3.format.parquet.ParquetFormat",
        "partitioner.class": "io.confluent.connect.storage.partitioner.TimeBasedPartitioner",
        "path.format": "'year'=YYYY/'month'=MM/'day'=dd",
        "locale": "en-US",
        "timezone": "UTC"
    }
}
```

### Cas 3: MongoDB vers Snowflake

```json
{
    "name": "mongodb-snowflake",
    "config": {
        "connector.class": "io.debezium.connector.mongodb.MongoDbConnector",
        "mongodb.hosts": "rs0/mongo1:27017,mongo2:27017",
        "mongodb.name": "mongo-cluster",
        "mongodb.user": "debezium",
        "mongodb.password": "password",
        "database.include.list": "inventory",
        "collection.include.list": "inventory.products,inventory.orders",
        "snapshot.mode": "initial",
        "transforms": "flatten",
        "transforms.flatten.type": "org.apache.kafka.connect.transforms.Flatten$Value",
        "transforms.flatten.delimiter": "_",
        
        "snowflake.sink.connector.class": "com.snowflake.kafka.connector.SnowflakeSinkConnector",
        "snowflake.url.name": "https://account.snowflakecomputing.com",
        "snowflake.user.name": "kafka_user",
        "snowflake.private.key": "MII...",
        "snowflake.database.name": "KAFKA_DB",
        "snowflake.schema.name": "CDC_SCHEMA",
        "snowflake.role.name": "KAFKA_ROLE",
        "buffer.flush.time": "300",
        "buffer.count.records": "10000"
    }
}
```

### Cas 4: Multi-tenancy avec SMT

```json
{
    "name": "multi-tenant-connector",
    "config": {
        "connector.class": "io.debezium.connector.mysql.MySqlConnector",
        "database.hostname": "mysql",
        "database.user": "debezium",
        "database.password": "password",
        "database.server.name": "saas",
        
        // Multi-tenant routing
        "transforms": "tenant,route",
        
        "transforms.tenant.type": "org.apache.kafka.connect.transforms.InsertField$Value",
        "transforms.tenant.static.field": "tenant_id",
        "transforms.tenant.static.value": "{{tenant}}",
        
        "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
        "transforms.route.regex": "saas.([^.]+).([^.]+)",
        "transforms.route.replacement": "tenant-$1-$2",
        
        // Per-tenant DLQ
        "errors.deadletterqueue.topic.name": "dlq-{{tenant}}",
        "errors.deadletterqueue.context.headers.enable": "true"
    }
}
```

---

## 7. 📊 **Commandes CLI essentielles**

```bash
# ========== Gestion des connecteurs ==========
# 1. Liste complète avec détails
curl -s "http://localhost:8083/connectors?expand=info&expand=status" | jq '.'

# 2. Voir les tâches d'un connecteur
curl -s "http://localhost:8083/connectors/my-connector/tasks" | jq '.'

# 3. Voir les offsets d'un connecteur
curl -s "http://localhost:8083/connectors/my-connector/offsets" | jq '.'

# 4. Modifier le niveau de log
curl -X POST "http://localhost:8083/admin/loggers/io.debezium" \
    -H "Content-Type: application/json" \
    -d '{"level": "TRACE"}'

# ========== Validation ==========
# 5. Valider configuration plugin
curl -X POST "http://localhost:8083/connector-plugins/MyConnector/config/validate" \
    -H "Content-Type: application/json" \
    -d @config.json

# ========== Sauvegarde ==========
# 6. Exporter tous les connecteurs
for connector in $(curl -s "http://localhost:8083/connectors" | jq -r '.[]'); do
    curl -s "http://localhost:8083/connectors/$connector" > "backup/$connector.json"
done

# ========== Restauration ==========
# 7. Importer tous les connecteurs
for file in backup/*.json; do
    curl -X POST "http://localhost:8083/connectors" \
        -H "Content-Type: application/json" \
        --data @"$file"
done

# ========== Health check ==========
# 8. Vérifier l'état des workers
curl -s "http://localhost:8083/connectors/active" | jq '.'

# 9. Métriques complètes
curl -s "http://localhost:8083/admin/metrics" | jq '.'

# ========== Debezium spécifique ==========
# 10. Refaire snapshot
curl -X POST "http://localhost:8083/connectors/my-connector/offsets" \
    -H "Content-Type: application/json" \
    -d '{"offset.flush.interval.ms": 1000}'
```

---

## 8. 🎓 **Tips Pro par Thème**

### Performance

| Tip | Explication |
|-----|-------------|
| **Ajuster `tasks.max`** | = nombre de partitions du topic source |
| **Batch size optimal** | 2048-4096 pour MySQL, 10000 pour JDBC Sink |
| **Compression Snappy** | Réduit bande passante de 70% |
| **Connection pool sizing** | max= partitions * threads * 2 |
| **Snapshot lock minimal** | `snapshot.locking.mode=minimal` pour éviter blocages |

### Fiabilité

| Tip | Explication |
|-----|-------------|
| **Exactly-once avec idempotence** | `processing.guarantee=exactly_once_v2` |
| **DLQ pour tous les connecteurs** | Ne jamais perdre les messages en erreur |
| **Snapshot when_needed** | Évite snapshots répétés inutiles |
| **Replication factor 3** | Pour tous les topics internes |
| **Standby tasks** | Récupération rapide sur panne |

### Monitoring

| Tip | Explication |
|-----|-------------|
| **Alert sur `milliseconds-behind-source`** | Détecte les retards |
| **Monitorer `connect-status` topic** | Pour état des connecteurs |
| **Logs structurés JSON** | Facilite ingestion ELK |
| **JMX exporters** | Prometheus + Grafana |
| **SLO tracking** | Records sent/sec, error rate |

### Sécurité

| Tip | Explication |
|-----|-------------|
| **SASL/SCRAM** | Authentification forte |
| **SSL/TLS mutual** | Chiffrement et authentification |
| **Secrets externalisés** | HashiCorp Vault, AWS Secrets Manager |
| **Column exclusion** | `column.exclude.list` pour données sensibles |
| **Audit logs** | Traçabilité des accès |

---

## 9. 📈 **Métriques à surveiller**

```yaml
# Alertes Prometheus
groups:
  - name: kafka_connect_alerts
    rules:
      - alert: ConnectorFailed
        expr: kafka_connect_connector_status{state="FAILED"} == 1
        annotations:
          summary: "Connector {{ $labels.connector }} failed"
          
      - alert: TaskFailed
        expr: kafka_connect_task_status{state="FAILED"} == 1
        annotations:
          summary: "Task {{ $labels.task }} failed"
          
      - alert: HighLag
        expr: debezium_mysql_milliseconds_behind_source > 60000
        annotations:
          summary: "CDC lag > 60s"
          
      - alert: HighErrorRate
        expr: rate(kafka_connect_task_error_total[5m]) > 10
        annotations:
          summary: "High error rate > 10/5min"
```

---

## 10. ⚠️ **Pièges courants et solutions**

| Piège | Symptôme | Solution |
|-------|----------|----------|
| **Snapshot bloque tables** | Timeout, locks | `snapshot.locking.mode=minimal` |
| **Partitions déséquilibrées** | Une tâche surchargée | Augmenter `tasks.max` |
| **Schéma incompatible** | Conversion errors | Schema Registry + Avro |
| **Binlog purgé** | Connecteur crash | Augmenter `binlog.retention.hours` |
| **WAL non conservé** | Slot dropped | `replication.slot.drop.on.stop=false` |
| **Mémoire heap** | OOM | `KAFKA_HEAP_OPTS="-Xmx2g"` |
| **Transactions longues** | Lag, mémoire | Découper transactions |
| **DLQ non configurée** | Messages perdus | `errors.deadletterqueue.topic.name` |

---

## 11. 🧪 **Tests unitaires**

```java
// ConnectorTest.java
package com.example.connect.test;

import org.apache.kafka.connect.runtime.AbstractHerder;
import org.apache.kafka.connect.runtime.rest.entities.ConnectorInfo;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class ConnectorTest {
    
    @Test
    void testConnectorConfiguration() {
        Map<String, String> config = Map.of(
            "connector.class", "io.debezium.connector.mysql.MySqlConnector",
            "database.hostname", "localhost",
            "database.user", "test",
            "database.password", "test"
        );
        
        assertNotNull(config);
        assertTrue(config.containsKey("connector.class"));
    }
    
    @Test
    void testSMTTransformation() {
        CustomMaskingSMT smt = new CustomMaskingSMT();
        smt.configure(Map.of("fields", "password,ssn"));
        
        Struct input = createTestRecord();
        Struct output = smt.apply(input);
        
        assertEquals("***", output.get("password"));
        assertEquals("***", output.get("ssn"));
    }
}
```

---

## 12. 📚 **Resources utiles**

```bash
# Plugins populaires
# Debezium
https://repo1.maven.org/maven2/io/debezium/

# Confluent Hub
confluent-hub install confluentinc/kafka-connect-jdbc:latest
confluent-hub install confluentinc/kafka-connect-elasticsearch:latest
confluent-hub install mongodb/kafka-connect-mongodb:latest

# Configuration templates
/etc/kafka/connect-distributed.properties
/etc/kafka/connect-log4j.properties

# Docker images
docker pull debezium/connect:2.4
docker pull confluentinc/cp-kafka-connect:latest
```

---

## 13. 🚨 **Dépannage rapide**

```bash
# 1. Connecteur ne démarre pas
curl -X GET http://localhost:8083/connectors/my-connector/status
kafka-console-consumer --topic connect-offsets --bootstrap-server kafka:9092 | grep my-connector

# 2. Lag CDC
kafka-consumer-groups --describe --group connect-mysql-prod --bootstrap-server kafka:9092
mysql> SHOW SLAVE STATUS;

# 3. Schema history corrompu
kafka-console-consumer --topic schema-changes.testdb --from-beginning --max-messages 1
# Reset: DELETE FROM connect-offsets WHERE key LIKE '%schema-changes%'

# 4. Performances lentes
curl -X GET http://localhost:8083/connectors/my-connector/tasks/0/status
# Augmenter tasks.max, batch.size, poll.interval.ms

# 5. Mémoire insuffisante
export KAFKA_HEAP_OPTS="-Xmx4g -Xms2g"
export KAFKA_JVM_PERFORMANCE_OPTS="-server -XX:+UseG1GC"
```

---

## 14. 🎯 **Quick Reference – API REST**

```bash
# ========== CRUD Connectors ==========
GET    /connectors
POST   /connectors
GET    /connectors/{name}
PUT    /connectors/{name}/config
DELETE /connectors/{name}

# ========== Status ==========
GET    /connectors/{name}/status
GET    /connectors/{name}/tasks
GET    /connectors/{name}/tasks/{task}/status

# ========== Control ==========
PUT    /connectors/{name}/pause
PUT    /connectors/{name}/resume
POST   /connectors/{name}/restart
POST   /connectors/{name}/tasks/{task}/restart

# ========== Plugins ==========
GET    /connector-plugins
POST   /connector-plugins/{plugin}/config/validate

# ========== Admin ==========
GET    /admin/metrics
GET    /admin/loggers
POST   /admin/loggers/{logger}
GET    /connectors/active
```

---

## 15. 💡 **Patterns avancés**

### Pattern: Circuit Breaker

```json
{
    "errors.retry.timeout": "300000",
    "errors.retry.delay.max.ms": "60000",
    "errors.tolerance": "all",
    "task.max.retries": "5",
    "task.retry.backoff.ms": "10000"
}
```

### Pattern: Blue/Green deployment

```bash
# 1. Nouveau connecteur (green)
curl -X POST http://localhost:8083/connectors \
    -d @connector-v2.json

# 2. Vérifier green
curl -X GET http://localhost:8083/connectors/connector-v2/status

# 3. Arrêter blue
curl -X PUT http://localhost:8083/connectors/connector-v1/pause

# 4. Supprimer blue
curl -X DELETE http://localhost:8083/connectors/connector-v1
```

---

Ce cheat sheet vous permettra de maîtriser Kafka Connect et Debezium CDC en production. Gardez-le comme référence quotidienne !
