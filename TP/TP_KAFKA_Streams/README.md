
# 📘 **Kafka Streams – Cheat Sheet Complet**

## Guide ultime avec concepts, exemples, tuning, bonnes pratiques et tips

---

## 1. 🏗️ **Concepts Fondamentaux**

### Définitions clés

| Concept | Définition | Analogue SQL |
|---------|------------|--------------|
| **KStream** | Flux d'enregistrements (append-only) | `SELECT * FROM table` |
| **KTable** | Vue mutable d'une clé (dernière valeur) | `CREATE TABLE ... PRIMARY KEY` |
| **GlobalKTable** | KTable répliquée sur toutes les instances | Table broadcastée |
| **KGroupedStream** | Stream après groupBy (prêt pour agrégation) | `GROUP BY` |
| **Windowed** | Clé avec intervalle temporel | Fenêtre de temps |
| **State Store** | Stockage local (RocksDB) pour l'état | Index matérialisé |
| **Processor** | Nœud de traitement bas niveau | UDF personnalisée |

### Types de fenêtres

```java
// 1. TUMBLING - Fixe, sans chevauchement
TimeWindows.ofSize(Duration.ofSeconds(10))

// 2. HOPPING - Avec chevauchement
TimeWindows.ofSizeAndGrace(Duration.ofSeconds(30), Duration.ofSeconds(10))
          .advanceBy(Duration.ofSeconds(10))

// 3. SESSION - Basée sur l'inactivité
SessionWindows.ofInactivityGapWithNoGrace(Duration.ofSeconds(30))

// 4. SLIDING - Basée sur la différence de timestamps
JoinWindows.ofTimeDifferenceWithNoGrace(Duration.ofMinutes(5))
```

### Topologie vs Sous-topologies

```java
// Une topologie peut être divisée en sous-topologies par Kafka Streams
// quand il y a des opérations de repartitioning (groupBy, join, etc.)

// Visualiser la topologie
Topology topology = builder.build();
System.out.println(topology.describe());
```

---

## 2. 🚀 **Configuration Optimale**

### Configuration de base (production)

```java
Properties props = new Properties();

// --- Identifiants ---
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "my-app");  // Unique!
props.put(StreamsConfig.CLIENT_ID_CONFIG, "my-app-client");
props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092,kafka2:9092");

// --- Sérialisation ---
props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

// --- Performance ---
props.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, 4);  // = nombre de cœurs
props.put(StreamsConfig.MAX_TASK_IDLE_MS_CONFIG, 10000); // Éviter les retards
props.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, 30000); // Commit toutes les 30s

// --- Tolérance aux pannes ---
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
props.put(StreamsConfig.NUM_STANDBY_REPLICAS_CONFIG, 1); // Réplicas standby

// --- Gestion des erreurs ---
props.put(StreamsConfig.DEFAULT_DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG, 
          LogAndContinueExceptionHandler.class);
props.put(StreamsConfig.DEFAULT_PRODUCTION_EXCEPTION_HANDLER_CLASS_CONFIG, 
          ProductionExceptionHandlerUtil.LogAndContinueProductionExceptionHandler.class);

// --- État (State Store) ---
props.put(StreamsConfig.STATE_DIR_CONFIG, "/data/kafka-streams");
props.put(StreamsConfig.ROCKSDB_CONFIG_SETTER_CLASS_CONFIG, 
          OptimizedRocksDBConfigSetter.class);

// --- Cache (pour KTable) ---
props.put(StreamsConfig.CACHE_MAX_BYTES_BUFFERING_CONFIG, 10 * 1024 * 1024L); // 10 MB
props.put(StreamsConfig.STATESTORE_CACHE_MAX_BYTES_CONFIG, 10 * 1024 * 1024L);
```

### Configuration RocksDB optimisée

```java
public class OptimizedRocksDBConfigSetter implements RocksDBConfigSetter {
    @Override
    public void setConfig(final String storeName, final Options options, final Map<String, Object> configs) {
        // Optimisations mémoire
        options.setWriteBufferSize(64 * 1024 * 1024);     // 64 MB
        options.setMaxWriteBufferNumber(3);
        options.setMinWriteBufferNumberToMerge(2);
        
        // Compression
        options.setCompressionType(CompressionType.LZ4_COMPRESSION);
        options.setBottommostCompressionType(CompressionType.ZSTD_COMPRESSION);
        
        // Cache
        final BlockBasedTableConfig tableConfig = new BlockBasedTableConfig();
        tableConfig.setBlockCacheSize(256 * 1024 * 1024);  // 256 MB
        tableConfig.setBlockSize(16 * 1024);               // 16 KB
        tableConfig.setCacheIndexAndFilterBlocks(true);
        options.setTableFormatConfig(tableConfig);
        
        // Parallélisme
        options.setIncreaseParallelism(Runtime.getRuntime().availableProcessors());
        options.setMaxBackgroundCompactions(Runtime.getRuntime().availableProcessors() / 2);
    }
}
```

---

## 3. 📝 **Patterns et Bonnes Pratiques**

### Pattern 1: Topologie modulaire

```java
public class OrderTopology {
    
    public static Topology build() {
        StreamsBuilder builder = new StreamsBuilder();
        
        // Séparer par responsabilité
        buildOrderValidationTopology(builder);
        buildOrderEnrichmentTopology(builder);
        buildOrderAggregationTopology(builder);
        
        return builder.build();
    }
    
    private static void buildOrderValidationTopology(StreamsBuilder builder) {
        builder.stream("orders-topic")
               .filter((k, v) -> isValid(v))
               .to("valid-orders-topic");
    }
    
    private static void buildOrderEnrichmentTopology(StreamsBuilder builder) {
        // ...
    }
}
```

### Pattern 2: Gestion des erreurs avancée

```java
// DLQ (Dead Letter Queue) personnalisé
builder.stream("input-topic")
       .mapValues(value -> {
           try {
               return processValue(value);
           } catch (Exception e) {
               // Envoyer vers DLQ
               produceToDLQ(value, e);
               return null;  // Ignorer
           }
       })
       .filter((k, v) -> v != null)
       .to("output-topic");

// Production vers DLQ
private void produceToDLQ(String value, Exception e) {
    String errorMsg = String.format("{\"error\":\"%s\",\"value\":\"%s\"}", 
                                     e.getMessage(), value);
    dlqProducer.send(new ProducerRecord<>("dlq-topic", errorMsg));
}
```

### Pattern 3: Idempotence et Exactly-Once

```java
// Utiliser des IDs de message uniques pour déduplication
KTable<String, String> processedIds = builder.table("processed-ids-topic");

builder.stream("input-topic")
       .selectKey((k, v) -> extractMessageId(v))  // Utiliser l'ID comme clé
       .leftJoin(processedIds, (value, processed) -> {
           if (processed != null) {
               return null;  // Déjà traité
           }
           return processValue(value);
       })
       .filter((k, v) -> v != null)
       .to("output-topic");
```

### Pattern 4: Reconnexion et reprise

```java
// Ajouter un StateListener pour surveiller la restauration
KafkaStreams streams = new KafkaStreams(topology, props);
streams.setStateListener((newState, oldState) -> {
    if (newState == KafkaStreams.State.RUNNING) {
        System.out.println("Application démarrée - état restauré");
    } else if (newState == KafkaStreams.State.ERROR) {
        System.err.println("Erreur fatale - redémarrage...");
        streams.close();
        // Logique de redémarrage
    }
});

// Uncaught exception handler
Thread.setDefaultUncaughtExceptionHandler((thread, exception) -> {
    System.err.println("Erreur non capturée: " + exception.getMessage());
    // Notification, logging, etc.
});
```

---

## 4. ⚡ **Optimisations Performance**

### Tuning Threads et Tasks

```java
// Nombre de threads = min(partitions, cœurs disponibles)
props.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, 
          Math.min(totalPartitions, Runtime.getRuntime().availableProcessors()));

// Max tasks (par défaut = nombre de partitions)
props.put(StreamsConfig.MAX_TASKS_PER_THREAD_CONFIG, 1);  // Éviter contention

// Buffer de réplication
props.put(StreamsConfig.REPLICATION_FACTOR_CONFIG, 3);
props.put(StreamsConfig.NUM_STANDBY_REPLICAS_CONFIG, 1);
```

### Cache et Mémoire

```java
// Ajuster le cache pour KTable (réduit les écritures)
props.put(StreamsConfig.CACHE_MAX_BYTES_BUFFERING_CONFIG, 50 * 1024 * 1024); // 50 MB

// RocksDB memory tuning
props.put(StreamsConfig.ROCKSDB_CONFIG_SETTER_CLASS_CONFIG, 
          OptimizedRocksDBConfigSetter.class);

// Off-heap memory
props.put(StreamsConfig.ROCKSDB_BLOCK_CACHE_SIZE_CONFIG, 512 * 1024 * 1024L);
```

### Repartitioning optimisation

```java
// Éviter le repartitioning implicite en utilisant Grouped
KGroupedStream<String, String> grouped = stream
    .groupBy((k, v) -> v, Grouped.with(Serdes.String(), Serdes.String()));

// Utiliser selectKey au lieu de groupBy si possible
stream.selectKey((k, v) -> v);  // Change la clé sans repartitioning

// Matérialiser pour réutiliser le store
KTable<String, Long> counts = stream
    .groupByKey()
    .count(Materialized.<String, Long, KeyValueStore<Bytes, byte[]>>as("count-store")
        .withCachingEnabled()
        .withLoggingEnabled(Map.of("segment.bytes", 1024 * 1024 * 100)));
```

---

## 5. 🔧 **Débogage et Monitoring**

### Métriques essentielles

```java
// Activer les métriques JMX
props.put(StreamsConfig.METRICS_RECORDING_LEVEL_CONFIG, "DEBUG");
props.put(StreamsConfig.METRICS_SAMPLE_WINDOW_MS_CONFIG, 30000);

// Métriques à surveiller dans JMX
// - kafka.streams:type=stream-metrics,client-id=*
// - kafka.streams:type=task-manager,client-id=*
// - kafka.streams:type=rocksdb,client-id=*,store=*

// Programmatiquement
for (MetricName metricName : streams.metrics().keySet()) {
    Metric metric = streams.metrics().get(metricName);
    System.out.println(metricName.name() + " = " + metric.metricValue());
}
```

### Debugging avec Peek

```java
// Peek pour inspecter les messages sans les modifier
builder.stream("input-topic")
       .peek((k, v) -> System.out.println("Input: " + k + " -> " + v))
       .filter((k, v) -> v.length() > 5)
       .peek((k, v) -> System.out.println("After filter: " + v))
       .to("output-topic");
```

### Tests unitaires

```java
@Test
void testTopology() {
    Properties props = new Properties();
    props.put(StreamsConfig.APPLICATION_ID_CONFIG, "test");
    props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "dummy");
    
    TopologyTestDriver driver = new TopologyTestDriver(topology, props);
    
    // Input
    TestInputTopic<String, String> input = driver.createInputTopic(
        "input-topic", 
        Serdes.String().serializer(), 
        Serdes.String().serializer()
    );
    input.pipeInput("key", "value");
    
    // Output
    TestOutputTopic<String, String> output = driver.createOutputTopic(
        "output-topic",
        Serdes.String().deserializer(),
        Serdes.String().deserializer()
    );
    assertEquals("VALUE", output.readValue());
}
```

---

## 6. 🎯 **Exemples de Code par Cas d'Usage**

### Cas 1: Détection de fraude (fenêtre + agrégation)

```java
KStream<String, Transaction> transactions = builder.stream("transactions-topic");

transactions
    .groupBy((k, v) -> v.getUserId())
    .windowedBy(TimeWindows.ofSizeAndGrace(Duration.ofMinutes(5), Duration.ofSeconds(30)))
    .aggregate(
        () -> new FraudAggregate(),
        (userId, transaction, aggregate) -> aggregate.add(transaction),
        Materialized.<String, FraudAggregate, WindowStore<Bytes, byte[]>>as("fraud-store")
    )
    .toStream()
    .filter((windowedKey, aggregate) -> aggregate.isSuspicious())
    .mapValues(aggregate -> createFraudAlert(aggregate))
    .to("fraud-alerts-topic");
```

### Cas 2: Enrichissement avec lookup externe

```java
// Utiliser GlobalKTable pour données de référence
GlobalKTable<String, Product> products = builder.globalTable("products-topic");

KStream<String, Order> orders = builder.stream("orders-topic");

orders.join(
    products,
    (orderId, order) -> order.getProductId(),
    (order, product) -> order.enrichWithProduct(product)
).to("enriched-orders-topic");
```

### Cas 3: Re-partitioning pour rééquilibrage

```java
// Problème: clés déséquilibrées
KStream<String, String> skewed = builder.stream("skewed-topic");

// Solution 1: Ajouter un salt
skewed.selectKey((k, v) -> k + "_" + (Math.random() * 10));

// Solution 2: Repartitioning explicite
skewed.through("repartitioned-topic", Produced.with(Serdes.String(), Serdes.String()));

// Solution 3: GroupBy avec partitionnement personnalisé
skewed.groupBy(
    (k, v) -> k,
    Grouped.with(Serdes.String(), Serdes.String())
          .withPartitioner((topic, key, value, numPartitions) -> 
              Math.abs(key.hashCode() % numPartitions))
);
```

### Cas 4: Suppression de doublons (deduplication)

```java
// Store pour suivre les IDs traités
KTable<String, Long> processed = builder.table("processed-ids-topic");

builder.stream("input-topic")
       .selectKey((k, v) -> extractUniqueId(v))
       .filter((id, value) -> {
           // Vérifier si déjà traité
           ReadOnlyKeyValueStore<String, Long> store = 
               kafkaStreams.store(StoreQueryParameters.fromNameAndType(
                   "processed-ids-store", QueryableStoreTypes.keyValueStore()));
           return store.get(id) == null;
       })
       .to("output-topic");
```

---

## 7. 📊 **Top 20 des commandes CLI essentielles**

```bash
# 1. Consommer un topic avec affichage des clés
kafka-console-consumer --topic my-topic --bootstrap-server localhost:9092 \
    --property print.key=true --property print.value=true

# 2. Consommer depuis le début
kafka-console-consumer --topic my-topic --bootstrap-server localhost:9092 \
    --from-beginning

# 3. Produire avec clés
kafka-console-producer --topic my-topic --bootstrap-server localhost:9092 \
    --property parse.key=true --property key.separator=:

# 4. Lister les topics
kafka-topics --list --bootstrap-server localhost:9092

# 5. Décrire un topic
kafka-topics --describe --topic my-topic --bootstrap-server localhost:9092

# 6. Voir les groupes de consommateurs
kafka-consumer-groups --list --bootstrap-server localhost:9092

# 7. Décrire un groupe de consommateurs (offset lag)
kafka-consumer-groups --describe --group my-app --bootstrap-server localhost:9092

# 8. Réinitialiser les offsets
kafka-consumer-groups --group my-app --topic my-topic --reset-offsets --to-earliest \
    --execute --bootstrap-server localhost:9092

# 9. Supprimer un topic
kafka-topics --delete --topic my-topic --bootstrap-server localhost:9092

# 10. Modifier le nombre de partitions
kafka-topics --alter --topic my-topic --partitions 10 --bootstrap-server localhost:9092

# 11. Voir la configuration d'un topic
kafka-configs --describe --topic my-topic --bootstrap-server localhost:9092

# 12. Modifier la rétention
kafka-configs --alter --topic my-topic --add-config retention.ms=604800000 \
    --bootstrap-server localhost:9092

# 13. Dump d'un segment de log
kafka-dump-log --files /var/lib/kafka/data/my-topic-0/00000000000000000000.log

# 14. Vérifier l'état d'un connecteur
curl -X GET http://localhost:8083/connectors/my-connector/status

# 15. Créer un connecteur
curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" \
    --data '{"name":"my-connector","config":{"connector.class":"..."}}'

# 16. Voir les métriques JMX
jconsole

# 17. Changer le niveau de log dynamiquement
kafka-configs --alter --entity-type brokers --entity-default --add-config log4j.logger.kafka.streams=DEBUG

# 18. Voir les topics internes de Kafka Streams
kafka-topics --list --bootstrap-server localhost:9092 | grep "my-app"

# 19. Consommer le changelog d'une KTable
kafka-console-consumer --topic my-app-store-changelog --bootstrap-server localhost:9092 \
    --property print.key=true --property value.deserializer=org.apache.kafka.common.serialization.ByteArrayDeserializer

# 20. Vérifier l'état des tâches
curl -X GET "http://localhost:8083/connectors?expand=info&expand=status"
```

---

## 8. 🎓 **Tips Pro par Thème**

### Performance

| Tip | Explication |
|-----|-------------|
| **Utiliser `cogroup` au lieu de multiples `groupBy`** | `cogroup` agrège plusieurs streams en une seule passe |
| **Matérialiser les stores avec `Materialized.as()`** | Permet les requêtes interactives et réutilisation |
| **Préférer `reduce` à `aggregate` si possible** | `reduce` est plus léger (pas de constructeur initial) |
| **Éviter `through` inutiles** | Chaque `through` crée un nouveau topic et repartitioning |
| **Utiliser `StreamsConfig.MAX_TASK_IDLE_MS_CONFIG`** | Évite l'attente sur les partitions vides |

### Fiabilité

| Tip | Explication |
|-----|-------------|
| **Toujours configurer `processing.guarantee=exactly_once_v2`** | Garantie exactly-once avec meilleures performances |
| **Ajouter des réplicas standby** | Récupération plus rapide après panne |
| **Utiliser `LogAndContinueExceptionHandler`** | Évite l'arrêt sur erreur de désérialisation |
| **Configurer des DLQ pour les erreurs métier** | Ne pas perdre les messages problématiques |
| **Surveiller les lag avec JMX** | Détecter les retards de traitement |

### Opérations

| Tip | Explication |
|-----|-------------|
| **Utiliser `kafka-streams-application-reset`** | Réinitialiser l'état d'une application |
| **Versionner les `application.id` lors de breaking changes** | Évite les conflits de state store |
| **Planifier les standby dans des AZ différentes** | Haute disponibilité géographique |
| **Utiliser `state.dir` sur un volume rapide (SSD)** | RocksDB est I/O intensif |
| **Monitorer la taille des stores** | `kafka-log-dirs --describe --broker 0` |

---

## 9. 📈 **Métriques clés à surveiller**

```java
// Métriques essentielles via JMX
metrics:
  - kafka.streams:type=stream-metrics,client-id=*
    - commit-latency-avg
    - commit-latency-max
    - poll-latency-avg
    - process-latency-avg
    
  - kafka.streams:type=task-manager,client-id=*
    - active-task-count
    - standby-task-count
    - assigned-task-count
    
  - kafka.streams:type=rocksdb,client-id=*,store=*
    - bytes-written-rate
    - bytes-read-rate
    - memtable-bytes-total
    - block-cache-usage
    
  - kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*
    - records-lag-max
    - records-consumed-rate
```

---

## 10. ⚠️ **Pièges courants et solutions**

| Piège | Symptôme | Solution |
|-------|----------|----------|
| **Repartitioning caché** | Performance dégradée, topics internes créés | Vérifier `topology.describe()`, utiliser `Grouped.with(...)` |
| **Mémoire RocksDB** | OOM, swap excessif | Configurer block cache, write buffer, off-heap |
| **Déséquilibre des tâches** | Certaines instances surchargées | Revoir la clé de partitionnement, ajouter salt |
| **Tombstone ignored** | DELETE non propagés | Vérifier que la clé existe, utiliser `.to()` avec Produced |
| **Grace period trop petit** | Messages ignorés | Augmenter `.grace(Duration.ofMinutes(5))` |
| **Cache mal configuré** | Trop d'écritures dans le changelog | Ajuster `cache.max.bytes.buffering` |

---

## 11. 🧪 **Tests et validation**

```java
// Test d'intégration avec EmbeddedKafka
@EmbeddedKafka(partitions = 1, topics = {"input", "output"})
class StreamIntegrationTest {
    
    @Test
    void testEndToEnd() {
        // Produire
        kafkaTemplate.send("input", "key", "value");
        
        // Attendre traitement
        Thread.sleep(5000);
        
        // Consommer
        ConsumerRecord<String, String> record = 
            KafkaTestUtils.getSingleRecord(consumer, "output", 10000);
        assertEquals("VALUE", record.value());
    }
}
```

---

## 12. 📚 **Ressources et références**

- [Kafka Streams Documentation](https://kafka.apache.org/documentation/streams/)
- [Kafka Streams DSL](https://kafka.apache.org/37/javadoc/org/apache/kafka/streams/kstream/package-summary.html)
- [RocksDB Tuning Guide](https://github.com/facebook/rocksdb/wiki/RocksDB-Tuning-Guide)
- [Kafka Streams Exactly-Once Semantics](https://www.confluent.io/blog/enabling-exactly-once-kafka-streams/)

---

## 🎯 **Quick Reference – Commandes et snippets**

```java
// ---------- Opérations de base ----------
builder.stream("topic")                    // KStream
builder.table("topic")                     // KTable
builder.globalTable("topic")               // GlobalKTable

// ---------- Transformation ----------
stream.filter((k, v) -> condition)         // Filtre
stream.mapValues(v -> transform)           // Transforme valeurs
stream.flatMapValues(v -> list)            // 1 vers N
stream.selectKey((k, v) -> newKey)         // Change clé
stream.peek((k, v) -> log)                 // Debug

// ---------- Agrégation ----------
stream.groupByKey()                        // Group par clé
stream.groupBy((k, v) -> newKey)           // Group par nouvelle clé
grouped.count()                            // Comptage
grouped.reduce((v1, v2) -> result)         // Réduction
grouped.aggregate(() -> init, (k, v, agg) -> update)

// ---------- Fenêtrage ----------
.windowedBy(TimeWindows.ofSize(Duration.ofSeconds(10)))
.windowedBy(TumblingWindows.of(Duration.ofMinutes(5)))
.windowedBy(SessionWindows.ofInactivityGap(Duration.ofSeconds(30)))

// ---------- Jointure ----------
stream.join(table, (sVal, tVal) -> result)          // Stream-Table
stream.leftJoin(table, (sVal, tVal) -> result)      // Left join
stream.join(stream2, (v1, v2) -> result, windows)   // Stream-Stream
stream.join(globalTable, keyMapper, valueJoiner)    // Avec GlobalKTable

// ---------- Écriture ----------
stream.to("topic")                                  // Écrire dans topic
stream.through("topic")                             // Écrire et relire
stream.print(Printed.toSysOut())                    // Print console

// ---------- État ----------
Materialized.as("store-name")                       // Nommer store
Materialized.with(Serdes.String(), Serdes.Long())   // Sérialisation
.withCachingEnabled()                               // Activer cache
.withLoggingEnabled(Map.of("retention.ms", "86400000"))

// ---------- Configuration ----------
NUM_STREAM_THREADS_CONFIG                          // Threads
PROCESSING_GUARANTEE_CONFIG                        // Exactly-once
STATE_DIR_CONFIG                                   // RocksDB dir
CACHE_MAX_BYTES_BUFFERING_CONFIG                   // Cache KTable
DEFAULT_DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG // Erreurs
```

---

Ce cheat sheet couvre l'essentiel pour maîtriser Kafka Streams en production. Gardez-le à portée de main pendant vos développements !
