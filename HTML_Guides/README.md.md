# 🚀 Confluent Certified Developer for Apache Kafka® (CCDAK)
## Complete Exam Preparation Guide

> **Exam format:** 60 questions · 90 minutes · ~70% passing score  
> **Domains:** Fundamentals · Application Development · Kafka Streams · Kafka Connect · Testing · Observability

---

## 📋 Table of Contents

1. [Apache Kafka Fundamentals](#1-apache-kafka-fundamentals)
2. [Apache Kafka Application Development](#2-apache-kafka-application-development)
3. [Apache Kafka Streams](#3-apache-kafka-streams)
4. [Kafka Connect](#4-kafka-connect)
5. [Application Testing](#5-application-testing)
6. [Application Observability](#6-application-observability)
7. [Master Quiz — 20 Questions](#7-master-quiz)
8. [Quick Reference Cheat Sheet](#8-quick-reference-cheat-sheet)
9. [Glossary](#9-glossary)
10. [Exam Day Tips](#10-exam-day-tips)

---

# 1. Apache Kafka Fundamentals

## 1.1 Kafka Resource Hierarchy

```
Cluster
  └── Broker (N brokers per cluster)
        └── Topic (N topics per broker)
              └── Partition (N partitions per topic)
                    └── Record / Message
                          ├── Key     (optional, byte[])
                          ├── Value   (byte[])
                          ├── Headers (key-value metadata)
                          ├── Timestamp
                          └── Offset  (unique per partition)
```

| Resource | Description | Key Facts |
|----------|-------------|-----------|
| **Cluster** | Group of brokers working together | Identified by cluster ID |
| **Broker** | Single Kafka server (JVM process) | Has a unique `broker.id` |
| **Topic** | Named, durable, append-only log | Logical grouping of related events |
| **Partition** | Ordered, immutable sequence of records | Unit of parallelism and fault tolerance |
| **Offset** | Monotonically increasing integer per partition | Unique **within** a partition only |
| **Leader** | Broker handling all reads/writes for a partition | 1 leader per partition |
| **ISR** | In-Sync Replica — follower caught up with leader | ISR ⊆ all replicas |
| **Controller** | Elected broker managing partition leadership | **Always exactly 1** active controller |

### KRaft vs ZooKeeper

| Aspect | ZooKeeper Mode | KRaft Mode |
|--------|---------------|------------|
| Metadata storage | External ZK ensemble | Internal `__cluster_metadata` topic |
| Status | **Deprecated** since Kafka 2.8 | **Default** since Kafka 3.3+ |
| Complexity | High (separate ZK cluster) | Low (embedded Raft quorum) |
| Controller | ZK-elected | Raft-elected quorum |
| Config key | `zookeeper.connect` (deprecated) | `controller.quorum.voters` |

> ⚠️ **Exam trap:** New questions reference KRaft. `zookeeper.connect` is deprecated — do not use in new deployments.

---

## 1.2 Connecting to a Secured Kafka Cluster

### Security Protocol Matrix

| Protocol | Encryption | Authentication |
|----------|-----------|----------------|
| `PLAINTEXT` | ❌ | ❌ |
| `SSL` | ✅ TLS | ✅ mTLS (optional) |
| `SASL_PLAINTEXT` | ❌ | ✅ SASL |
| `SASL_SSL` | ✅ TLS | ✅ SASL |

### SASL Mechanisms

| Mechanism | Description | Use Case |
|-----------|-------------|----------|
| `PLAIN` | Username/password in clear | Simple; must use with SSL |
| `SCRAM-SHA-256/512` | Challenge-response, salted hashes | More secure than PLAIN |
| `GSSAPI` | Kerberos | Enterprise / Active Directory |
| `OAUTHBEARER` | OAuth 2.0 JWT tokens | Confluent Cloud, modern apps |

### SSL Client Configuration

```properties
# SSL only
security.protocol=SSL
ssl.truststore.location=/path/to/truststore.jks
ssl.truststore.password=changeit
# mTLS (mutual TLS) — client also presents certificate
ssl.keystore.location=/path/to/keystore.jks
ssl.keystore.password=changeit
ssl.key.password=changeit
```

### SASL/PLAIN over SSL

```properties
security.protocol=SASL_SSL
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
  username="alice" \
  password="alice-secret";
ssl.truststore.location=/path/to/truststore.jks
ssl.truststore.password=changeit
```

### SASL/SCRAM

```properties
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required \
  username="alice" \
  password="alice-secret";
```

### ACL Authorization

```bash
# Grant alice READ on topic orders
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:alice \
  --operation Read --topic orders

# Grant service-account WRITE on topic payments
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add --allow-principal User:payment-svc \
  --operation Write --topic payments

# List all ACLs
kafka-acls.sh --bootstrap-server localhost:9092 --list
```

> 🔑 **Key:** Authorization is enforced per (Principal, Resource, Operation, Host). Resources include: Topic, Group, Cluster, TransactionalId.

---

## 1.3 Delivery Guarantees

### The Three Guarantees

```
at-most-once   →  Possible LOSS,     no duplicates   (acks=0)
at-least-once  →  No loss,           possible DUPES  (acks=1 or all + retries, no idempotence)
exactly-once   →  No loss,           no duplicates   (idempotence + transactions)
```

### Configuration Matrix

| Guarantee | acks | retries | enable.idempotence | isolation.level |
|-----------|------|---------|-------------------|-----------------|
| at-most-once | `0` | 0 | false | — |
| at-least-once | `1` or `all` | > 0 | false | read_uncommitted |
| exactly-once (producer) | `all` (auto) | MAX (auto) | **true** | — |
| exactly-once (E2E) | `all` | MAX | true | **read_committed** |

### Exactly-Once — How It Works

```
Producer PID:    Unique Producer ID assigned by broker per producer session
Sequence Number: Monotonic per (PID, Partition) — broker deduplicates
Epoch:           Incremented on restart — fences zombie producers
Transaction:     Groups writes across partitions into atomic unit
```

### Exactly-Once Code Pattern

```java
// 1. Configure
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "my-app-instance-1");
// ↑ automatically sets: acks=all, retries=MAX, max.in.flight≤5

// 2. Initialize
producer.initTransactions();

// 3. Transaction loop
producer.beginTransaction();
try {
    producer.send(new ProducerRecord<>("output", key, value));
    producer.sendOffsetsToTransaction(offsets, consumer.groupMetadata());
    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();  // rollback
}

// 4. Consumer side
props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");
```

> ⚠️ **Exam trap:** `enable.idempotence=true` with `max.in.flight > 5` → `ConfigException` at startup. Max is **5**.

> ⚠️ **Exam trap:** Idempotence gives exactly-once **per partition**. Cross-partition/cross-topic exactly-once requires full **transactions**.

---

## 1.4 Consumer Groups and Partitions

### Fundamental Rules

```
Rule 1: Each partition is consumed by exactly ONE consumer within a group
Rule 2: One consumer can handle MULTIPLE partitions
Rule 3: #consumers > #partitions → extra consumers sit IDLE (no error)
Rule 4: #consumers < #partitions → some consumers handle multiple partitions
Rule 5: Different groups are INDEPENDENT — each gets ALL records
```

### Visual: Partition Assignment

```
Topic: orders (4 partitions)

Group A (2 consumers):          Group B (5 consumers):
  Consumer-1 → P0, P1            Consumer-1 → P0
  Consumer-2 → P2, P3            Consumer-2 → P1
                                  Consumer-3 → P2
                                  Consumer-4 → P3
                                  Consumer-5 → IDLE ← wasted
```

### Rebalance Triggers

| Trigger | Description |
|---------|-------------|
| Consumer **joins** group | New consumer subscribes |
| Consumer **leaves** group | `close()` called or graceful shutdown |
| Consumer **heartbeat timeout** | No heartbeat within `session.timeout.ms` |
| Consumer **poll timeout** | No `poll()` within `max.poll.interval.ms` |
| **New partitions** added | Subscribed topic gets more partitions |
| **Subscription changed** | Consumer updates its topic list |

### Partition Assignment Strategies

| Strategy | Behavior | Best For |
|----------|----------|----------|
| `RangeAssignor` | Contiguous partitions per topic | Default (but can be uneven) |
| `RoundRobinAssignor` | Even round-robin | Better balance, multiple topics |
| `StickyAssignor` | Minimize movement on rebalance | Reduced churn |
| `CooperativeStickyAssignor` | **Incremental rebalance** — no stop-the-world | **Production recommended** |

> 🎯 **Exam:** "Minimize downtime during rebalance" → `CooperativeStickyAssignor`. Classic rebalancers stop all consumers; cooperative only revokes partitions that need to move.

### Timeout Configs

```properties
# Heartbeat thread frequency — must be << session.timeout.ms
heartbeat.interval.ms=3000          # default: 3s

# Consumer declared dead if no heartbeat received
session.timeout.ms=45000            # default: 45s

# Consumer kicked if poll() not called within this time
max.poll.interval.ms=300000         # default: 5 min — INCREASE for slow processing

# Records per poll() call
max.poll.records=500                # default: 500
```

> 💡 **Tip:** If processing is slow → reduce `max.poll.records` OR increase `max.poll.interval.ms` OR process in background thread and keep polling.

---

## 1.5 Topic Configuration

### Core Topic Configs

| Config | Default | Description |
|--------|---------|-------------|
| `retention.ms` | 604800000 (7d) | Time-based retention. `-1` = infinite |
| `retention.bytes` | -1 (unlimited) | Size-based retention per partition |
| `cleanup.policy` | `delete` | `delete`, `compact`, or `delete,compact` |
| `replication.factor` | 1 | Number of replicas (min 3 for production) |
| `min.insync.replicas` | 1 | Min ISR that must ACK when `acks=all` |
| `num.partitions` | 1 | Partition count — **can only increase** |
| `max.message.bytes` | 1048588 | Max batch size (~1MB) |
| `segment.ms` | 604800000 (7d) | When to roll a new log segment |
| `segment.bytes` | 1073741824 (1GB) | Size at which to roll segment |
| `compression.type` | `producer` | `producer`, `none`, `gzip`, `snappy`, `lz4`, `zstd` |
| `unclean.leader.election.enable` | `false` | Allow non-ISR leader? (data loss risk) |
| `delete.retention.ms` | 86400000 (1d) | How long tombstones kept in compacted topics |
| `min.cleanable.dirty.ratio` | 0.5 | Compaction trigger: 50% dirty → compact |
| `message.timestamp.type` | `CreateTime` | `CreateTime` (producer) or `LogAppendTime` (broker) |

### Topic Management CLI

```bash
# Create topic
kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic orders \
  --partitions 6 \
  --replication-factor 3 \
  --config retention.ms=86400000 \
  --config cleanup.policy=compact

# List topics
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Describe topic (shows partition leaders, ISR, configs)
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders

# Increase partitions (CANNOT decrease!)
kafka-topics.sh --bootstrap-server localhost:9092 \
  --alter --topic orders --partitions 12

# Modify config
kafka-configs.sh --bootstrap-server localhost:9092 \
  --entity-type topics --entity-name orders \
  --alter --add-config retention.ms=3600000

# Delete a specific config (revert to broker default)
kafka-configs.sh --bootstrap-server localhost:9092 \
  --entity-type topics --entity-name orders \
  --alter --delete-config retention.ms

# Delete topic
kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic orders
```

### Log Compaction Deep Dive

```
Compacted topic retains LATEST value per key:

Time →  [K1:A] [K2:B] [K1:C] [K3:D] [K2:E] [K1:null]
                                                 ↑
                                         Tombstone = delete K1

After compaction:
        [K2:E] [K3:D]   (K1 deleted, K2 has latest value E)
```

> ⚠️ **Exam trap:** Tombstone = record with **null value**. After `delete.retention.ms`, tombstone itself is deleted.

---

## 1.6 Consumer Group Offsets

### Offset Management

| Mode | Config | Risk | Use Case |
|------|--------|------|----------|
| **Auto commit** | `enable.auto.commit=true` | At-least-once (can lose uncommitted) | Simple, low-criticality |
| **Sync commit** | `commitSync()` | Blocks thread | Critical, ordered processing |
| **Async commit** | `commitAsync(callback)` | Non-blocking, needs error handling | High throughput |
| **Per-partition** | `commitSync(Map<TopicPartition, OffsetAndMetadata>)` | Fine-grained | Batch processing |

```java
// Manual per-partition commit after processing
Map<TopicPartition, OffsetAndMetadata> offsets = new HashMap<>();

for (ConsumerRecord<String, String> record : records) {
    process(record);
    // Commit offset + 1 (next record to consume)
    offsets.put(
        new TopicPartition(record.topic(), record.partition()),
        new OffsetAndMetadata(record.offset() + 1)
    );
}
consumer.commitSync(offsets);
```

### Offset Reset CLI

```bash
# Show current offsets and lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --describe

# Output:
# GROUP     TOPIC    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG  CONSUMER-ID
# my-group  orders   0          1500            1520            20   ...
# my-group  orders   1          2200            2200            0    ...

# Reset to earliest (dry-run first!)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --topic orders \
  --reset-offsets --to-earliest --dry-run

# Execute reset (group must be STOPPED)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --topic orders \
  --reset-offsets --to-earliest --execute

# Other reset options
--to-latest                         # reset to end
--to-offset 1000                    # specific offset
--to-datetime 2024-01-01T00:00:00.000  # by timestamp
--shift-by -100                     # relative shift
```

> ⚠️ **Exam trap:** You can ONLY reset offsets for a **STOPPED consumer group**. Active groups reject the reset.

---

## 1.7 Producer Partitioner

### How the Default Partitioner Works

```
Record has KEY?
    YES → murmur2(keyBytes) % numPartitions → SAME key → SAME partition (always)
    NO  → StickyPartitioner (since Kafka 2.4):
              Fill current partition batch → switch to next partition
              (Pre-2.4: pure round-robin, changed partition every record)
```

### Custom Partitioner

```java
public class PriorityPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes, Cluster cluster) {
        int numPartitions = cluster.partitionCountForTopic(topic);
        if (key != null && key.toString().startsWith("HIGH")) {
            return 0; // HIGH priority → always partition 0
        }
        // Everything else → distributed across remaining partitions
        return (Math.abs(Utils.murmur2(keyBytes)) % (numPartitions - 1)) + 1;
    }
}

// Register
props.put(ProducerConfig.PARTITIONER_CLASS_CONFIG, PriorityPartitioner.class.getName());
```

### Hot Partition Problem & Solutions

| Problem | Solution |
|---------|----------|
| One key dominates traffic | Key salting: `key + "|" + (counter % N)` |
| Low-cardinality key | Custom partitioner to spread further |
| Null key all same partition (pre-2.4) | Upgrade to Kafka 2.4+ (sticky partitioner) |

---

## 1.8 assign() vs subscribe()

| Aspect | `subscribe(topics)` | `assign(partitions)` |
|--------|--------------------|--------------------|
| Assignment | **Automatic** (Group Coordinator) | **Manual** (you choose partitions) |
| Rebalance | ✅ Automatic on join/leave | ❌ No rebalance ever |
| `group.id` | Required | Not required |
| Consumer Group | ✅ Participates | ❌ Does NOT participate |
| Offset commits | ✅ To `__consumer_offsets` | ✅ But no coordination |
| Pattern support | ✅ `subscribe(Pattern)` | ❌ |

```java
// subscribe() — automatic, group-based
consumer.subscribe(Arrays.asList("orders", "payments"));

// subscribe() with regex (auto-discovers new matching topics)
consumer.subscribe(Pattern.compile("app-.*"), new ConsumerRebalanceListener() {
    public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
        consumer.commitSync(); // save progress before rebalance
    }
    public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
        // partitions assigned — optionally seek
    }
});

// assign() — manual, no group coordination
TopicPartition tp = new TopicPartition("orders", 2);
consumer.assign(Collections.singletonList(tp));
consumer.seek(tp, 500L); // manually position offset
```

> ⚠️ **Exam trap:** `assign()` and `subscribe()` are **mutually exclusive**. Calling both → `IllegalStateException`.

---

## 1.9 Request Lifecycle

### Producer Request Lifecycle

```
Step 1: Serialize      Key + Value → byte[] using configured Serializers
Step 2: Partition      Partitioner determines target partition
Step 3: Accumulate     RecordAccumulator → batch by partition
                       (controlled by batch.size and linger.ms)
Step 4: Send           NetworkClient/Sender thread → ProduceRequest to leader
Step 5: Broker Write   Leader appends to log on disk
Step 6: Replicate      Followers replicate asynchronously
Step 7: ACK            Broker responds per acks config
Step 8: Retry          If error + retries > 0 → re-enqueue with backoff
Step 9: Callback       onCompletion(RecordMetadata, Exception) called
```

### Consumer Request Lifecycle

```
Step 1: FindCoordinator   → any broker → returns GroupCoordinator address
Step 2: JoinGroup         → first consumer becomes group LEADER
Step 3: SyncGroup         → leader computes partition assignment → all members receive assignments
Step 4: Fetch             → FetchRequest to partition leaders
Step 5: Process           → application processes records from poll()
Step 6: Commit Offset     → commitSync/Async to __consumer_offsets
Step 7: Heartbeat         → background thread → keeps session alive
```

---

# 2. Apache Kafka Application Development

## 2.1 Producer Configuration

### Complete Producer Config Reference

| Config | Default | Description |
|--------|---------|-------------|
| `bootstrap.servers` | — | `host:port` list for initial connection |
| `key.serializer` | — | Serializer class for keys |
| `value.serializer` | — | Serializer class for values |
| `acks` | `all` (3.0+) | `0`=none, `1`=leader, `all`=all ISR |
| `retries` | MAX_INT | Retry attempts on retryable errors |
| `retry.backoff.ms` | 100 | Wait between retries |
| `enable.idempotence` | `true` (3.0+) | Exactly-once per partition |
| `max.in.flight.requests.per.connection` | 5 | Unacked requests in flight. **≤5 with idempotence** |
| `batch.size` | 16384 (16KB) | Max batch bytes per partition |
| `linger.ms` | 0 | Wait before sending batch |
| `buffer.memory` | 33554432 (32MB) | Total accumulator memory |
| `compression.type` | `none` | `gzip`, `snappy`, `lz4`, `zstd` |
| `max.block.ms` | 60000 | Block time when buffer full |
| `request.timeout.ms` | 30000 | Broker response timeout |
| `delivery.timeout.ms` | 120000 | Total time for a record (incl. retries) |
| `transactional.id` | — | Required for transactions; unique per instance |
| `partitioner.class` | `DefaultPartitioner` | Custom partitioner |

### Throughput vs Durability Tuning

```properties
# ─── Maximum Throughput ────────────────────────────────────────────
linger.ms=20
batch.size=65536          # 64KB batches
compression.type=lz4      # fast compression
acks=1
buffer.memory=67108864    # 64MB

# ─── Maximum Durability (production) ──────────────────────────────
acks=all
min.insync.replicas=2     # set on topic
enable.idempotence=true   # auto-sets acks=all, retries=MAX, max.in.flight=5
retries=2147483647

# ─── Minimum Latency ──────────────────────────────────────────────
linger.ms=0
batch.size=1
acks=1
```

### Producer Send Modes

```java
KafkaProducer<String, String> producer = new KafkaProducer<>(props);

// 1. Fire-and-forget (at-most-once)
producer.send(new ProducerRecord<>("topic", "key", "value"));

// 2. Async with callback (at-least-once or exactly-once)
producer.send(new ProducerRecord<>("topic", "key", "value"),
    (metadata, exception) -> {
        if (exception != null) {
            log.error("Send failed for offset {}", metadata.offset(), exception);
        } else {
            log.info("Sent to partition={} offset={}", metadata.partition(), metadata.offset());
        }
    });

// 3. Synchronous (blocks until ACK)
RecordMetadata metadata = producer.send(record).get(); // throws ExecutionException

// 4. Always flush + close properly
producer.flush();  // drain buffer
producer.close();  // release resources, trigger graceful shutdown
```

---

## 2.2 Serialization and Deserialization

### Built-in Serializers

| Class | Java Type | Notes |
|-------|-----------|-------|
| `StringSerializer` | `String` | UTF-8 encoding |
| `IntegerSerializer` | `Integer` | 4-byte big-endian |
| `LongSerializer` | `Long` | 8-byte big-endian |
| `DoubleSerializer` | `Double` | 8-byte IEEE 754 |
| `ByteArraySerializer` | `byte[]` | No transformation |
| `UUIDSerializer` | `UUID` | As String |

### Confluent Schema Registry — Wire Format

```
Byte 0:    Magic byte = 0x00
Bytes 1-4: Schema ID (4-byte int from Schema Registry)
Bytes 5+:  Serialized payload (Avro/Protobuf/JSON)
```

### Schema Registry Serializers

| Format | Serializer | Deserializer | Config |
|--------|-----------|--------------|--------|
| Avro | `KafkaAvroSerializer` | `KafkaAvroDeserializer` | `schema.registry.url` |
| Protobuf | `KafkaProtobufSerializer` | `KafkaProtobufDeserializer` | `schema.registry.url` |
| JSON Schema | `KafkaJsonSchemaSerializer` | `KafkaJsonSchemaDeserializer` | `schema.registry.url` |

```java
// Avro producer
props.put("schema.registry.url", "http://schema-registry:8081");
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaAvroSerializer.class.getName());

// Avro consumer (specific record)
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, KafkaAvroDeserializer.class.getName());
props.put("specific.avro.reader", true);  // use generated Java classes

// Generic Avro record
Schema schema = new Schema.Parser().parse(schemaJson);
GenericRecord record = new GenericData.Record(schema);
record.put("userId", "user-123");
record.put("amount", 99.99);
producer.send(new ProducerRecord<>("payments", "key", record));
```

### Schema Compatibility Modes

| Mode | Rule | Who Upgrades First |
|------|------|--------------------|
| `BACKWARD` | New schema reads **old** data | Consumers first |
| `BACKWARD_TRANSITIVE` | BACKWARD for **all** previous versions | Consumers first |
| `FORWARD` | Old schema reads **new** data | Producers first |
| `FORWARD_TRANSITIVE` | FORWARD for **all** previous versions | Producers first |
| `FULL` | BACKWARD + FORWARD | Either order |
| `FULL_TRANSITIVE` | FULL for **all** previous versions | Either order |
| `NONE` | No checks | Dangerous in production |

```
BACKWARD compatibility — allowed changes:
  ✅ Add field WITH default value
  ✅ Remove field (existing data doesn't have it)
  ❌ Add required field (no default) — old data missing this field
  ❌ Change field type incompatibly

FORWARD compatibility — allowed changes:
  ✅ Add field WITH default value
  ✅ Remove optional field
  ❌ Remove required field
```

> 🎯 **Exam pattern:** "Add a new required Avro field" → breaks BACKWARD. Always add fields **with defaults**.

### Custom Serializer

```java
public class UserSerializer implements Serializer<User> {
    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public byte[] serialize(String topic, User user) {
        if (user == null) return null;
        try {
            return mapper.writeValueAsBytes(user);
        } catch (JsonProcessingException e) {
            throw new SerializationException("Error serializing User", e);
        }
    }
}

public class UserDeserializer implements Deserializer<User> {
    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public User deserialize(String topic, byte[] bytes) {
        if (bytes == null) return null;
        try {
            return mapper.readValue(bytes, User.class);
        } catch (IOException e) {
            throw new SerializationException("Error deserializing User", e);
        }
    }
}
```

---

## 2.3 Transactions

### Transaction API Sequence

```
initTransactions()          → register transactional.id with broker, get PID + epoch
    ↓
beginTransaction()          → mark start (local only, no broker call)
    ↓
send(records...)            → records written but NOT visible to read_committed consumers
    ↓
sendOffsetsToTransaction()  → atomically commit consumer offsets within same transaction
    ↓
commitTransaction()         → send COMMIT markers → records become visible
    OR
abortTransaction()          → send ABORT markers → records never visible
```

### Transaction Isolation Levels

| Level | Behavior |
|-------|----------|
| `read_uncommitted` | Default. Sees ALL records including in-progress/aborted transactions |
| `read_committed` | Only sees **committed** records. Aborted records filtered. Slight latency increase |

```java
// Complete read-process-write exactly-once
producer.initTransactions();

while (running) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    if (records.isEmpty()) continue;

    producer.beginTransaction();
    try {
        for (ConsumerRecord<String, String> record : records) {
            String result = businessLogic(record.value());
            producer.send(new ProducerRecord<>("output-topic", record.key(), result));
        }
        // Atomically commit input offsets with output write
        producer.sendOffsetsToTransaction(
            currentOffsets(records),
            consumer.groupMetadata()  // Kafka 2.5+: use groupMetadata() not groupId
        );
        producer.commitTransaction();
    } catch (ProducerFencedException | InvalidProducerEpochException e) {
        log.error("This producer was fenced, shutting down", e);
        producer.close();
        break; // cannot recover — restart application
    } catch (KafkaException e) {
        log.warn("Aborting transaction", e);
        producer.abortTransaction();
    }
}
```

> ⚠️ **Exam trap:** `ProducerFencedException` = another producer with same `transactional.id` started. **Cannot recover** — must restart.

> ⚠️ **Exam trap:** `transactional.id` must be **unique per application instance**. Two instances sharing one ID will fence each other.

---

## 2.4 Consumer Group Configuration

### Key Consumer Configs

| Config | Default | Description |
|--------|---------|-------------|
| `group.id` | — | Consumer group name. Required for `subscribe()` |
| `auto.offset.reset` | `latest` | `earliest`, `latest`, `none` |
| `enable.auto.commit` | `true` | Auto-commits every `auto.commit.interval.ms` |
| `auto.commit.interval.ms` | 5000 | Commit interval (auto-commit mode) |
| `max.poll.records` | 500 | Max records per `poll()` |
| `max.poll.interval.ms` | 300000 | Max time between polls |
| `session.timeout.ms` | 45000 | Heartbeat timeout |
| `heartbeat.interval.ms` | 3000 | Heartbeat frequency |
| `fetch.min.bytes` | 1 | Min data before returning fetch |
| `fetch.max.wait.ms` | 500 | Max wait if `fetch.min.bytes` not met |
| `max.partition.fetch.bytes` | 1048576 (1MB) | Max data per partition per fetch |
| `isolation.level` | `read_uncommitted` | Transaction visibility |

### auto.offset.reset Behavior

```
earliest  →  Start from first AVAILABLE offset
             (may not be 0 if retention deleted old records)
latest    →  Start from current end of log (only new messages)
none      →  Throw OffsetOutOfRangeException if no committed offset found
```

### Consume Loop Pattern

```java
consumer.subscribe(Arrays.asList("orders"));

// Rebalance listener — critical for manual offset management
consumer.subscribe(Arrays.asList("orders"), new ConsumerRebalanceListener() {
    public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
        // SAVE progress before partitions are taken away
        consumer.commitSync(currentOffsets);
    }
    public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
        // Optionally seek to desired position
        partitions.forEach(tp -> consumer.seek(tp, getLastProcessedOffset(tp)));
    }
});

try {
    while (running) {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
        for (ConsumerRecord<String, String> r : records) {
            System.out.printf("topic=%s partition=%d offset=%d key=%s value=%s%n",
                r.topic(), r.partition(), r.offset(), r.key(), r.value());
            // Read headers
            r.headers().forEach(h -> System.out.println(h.key() + ": " + new String(h.value())));
        }
        consumer.commitSync();
    }
} finally {
    consumer.close(); // triggers graceful rebalance + final commit
}
```

---

## 2.5 Design Keys for Partition Strategies

### Key Design Principles

| Principle | Rule |
|-----------|------|
| **Ordering** | All events for the same entity → same key → same partition → ordered |
| **Cardinality** | High-cardinality keys = better distribution across partitions |
| **Immutability** | Never change key in a compacted topic — old records won't be cleaned |
| **Null key** | Round-robin (no ordering). Cannot use log compaction meaningfully |
| **Hot partition** | One dominant key = one overloaded partition |

### Key Design Patterns

```
User events:      key = userId          → all user events ordered
Order lifecycle:  key = orderId         → all order state changes sequential
Multi-tenant:     key = tenantId+":"+entityId → per-tenant ordering
IoT devices:      key = deviceId        → per-device event stream
Geo-partitioned:  key = region+":"+id  → custom partitioner routes by region
Salted key:       key = originalKey+"|"+(seq % N)  → spread hot key across N partitions
```

---

## 2.6 Message Headers

### Header Use Cases

| Category | Example Headers |
|----------|----------------|
| Distributed tracing | `correlation-id`, `trace-id`, `span-id` |
| Event metadata | `event-type`, `source-system`, `schema-version` |
| GDPR / Privacy | Mark records containing PII; filter in processing |
| DLQ context | `original-topic`, `original-partition`, `original-offset`, `error-message` |
| Routing | `target-region`, `processing-priority` |

```java
// Producer — add headers
ProducerRecord<String, String> record = new ProducerRecord<>("payments", "key", "value");
record.headers().add("correlation-id", UUID.randomUUID().toString().getBytes(StandardCharsets.UTF_8));
record.headers().add("source-system", "payment-service".getBytes(StandardCharsets.UTF_8));
record.headers().add("schema-version", "3".getBytes(StandardCharsets.UTF_8));
producer.send(record);

// Consumer — read headers
for (Header header : record.headers()) {
    System.out.println(header.key() + " = " + new String(header.value(), StandardCharsets.UTF_8));
}
byte[] corrId = record.headers().lastHeader("correlation-id").value();
```

> 💡 **Note:** Headers are stored as `byte[]`. No built-in schema. Maximum header size limited by `max.request.size`.

---

## 2.7 Error Handling

### Producer Error Types

| Error | Retryable? | Action |
|-------|-----------|--------|
| `LEADER_NOT_AVAILABLE` | ✅ | Auto-retried |
| `NETWORK_EXCEPTION` | ✅ | Auto-retried |
| `NOT_ENOUGH_REPLICAS` | ✅ | Auto-retried |
| `MESSAGE_TOO_LARGE` | ❌ | Reduce message size |
| `INVALID_TOPIC` | ❌ | Fix topic name |
| `AUTHORIZATION_FAILED` | ❌ | Fix ACLs |
| `ProducerFencedException` | ❌ | Restart application |

### Consumer Error Handling

```java
// Handle deserialization errors without crashing
props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
          ErrorHandlingDeserializer.class.getName());
props.put(ErrorHandlingDeserializer.VALUE_DESERIALIZER_CLASS,
          KafkaAvroDeserializer.class.getName());

// Catch processing errors → Dead Letter Queue
for (ConsumerRecord<String, String> record : records) {
    try {
        process(record);
    } catch (ProcessingException e) {
        ProducerRecord<String, String> dlq =
            new ProducerRecord<>("my-topic.DLQ", record.key(), record.value());
        // Add context in headers
        dlq.headers().add("original-topic",     record.topic().getBytes());
        dlq.headers().add("original-partition", String.valueOf(record.partition()).getBytes());
        dlq.headers().add("original-offset",    String.valueOf(record.offset()).getBytes());
        dlq.headers().add("error-class",        e.getClass().getName().getBytes());
        dlq.headers().add("error-message",      e.getMessage().getBytes());
        dlqProducer.send(dlq);
        // Continue with next record — don't let one failure block the partition
    }
}
```

---

## 2.8 Common Data Formats

| Format | Encoding | Schema | Schema Registry | Best For |
|--------|----------|--------|-----------------|----------|
| **Avro** | Binary | ✅ Built-in | ✅ Required | High-volume production |
| **Protobuf** | Binary | ✅ Built-in | ✅ Supported | Cross-language, Google ecosystem |
| **JSON Schema** | Text (JSON) | ✅ External | ✅ Supported | Human-readable, REST integration |
| **JSON** | Text (JSON) | ❌ None | ❌ | Prototyping, flexibility |
| **String** | Text | ❌ None | ❌ | Simple pipelines, logs |
| **CSV** | Text | ❌ None | ❌ | Legacy integrations only |

---

## 2.9 Best Practices for Modifying Topics

| Action | Possible? | Caveats |
|--------|-----------|---------|
| ✅ Increase partitions | Yes | **Breaks key ordering** for existing records |
| ❌ Decrease partitions | **NEVER** | Must delete + recreate topic |
| ✅ Change `retention.ms` | Yes | Takes effect on next segment roll |
| ✅ Change `cleanup.policy` | Yes | Next compaction cycle |
| ✅ Change `max.message.bytes` | Yes | Also update consumer `fetch.message.max.bytes` |
| ⚙️ Change `replication.factor` | Complex | Use `kafka-reassign-partitions.sh` |
| ❌ Rename topic | Not supported | Create new, migrate, update consumers, delete old |

---

# 3. Apache Kafka Streams

## 3.1 Kafka Streams vs Consumer/Producer

| Aspect | Consumer/Producer API | Kafka Streams |
|--------|----------------------|---------------|
| Level | Low-level transport | High-level processing library |
| State | External (DB, cache) | Built-in RocksDB state stores |
| Joins | Manual implementation | Built-in (KStream-KTable, KStream-KStream) |
| Windowing | Manual | Tumbling, hopping, sliding, session |
| Fault tolerance | You implement | Automatic (changelog topics) |
| Deployment | Any JVM app | Any JVM app (no extra cluster!) |
| Scaling | Manual consumer group | Automatic task rebalancing |
| Dependency | `kafka-clients` | `kafka-streams` (includes clients) |

> 🔑 **Key:** Kafka Streams is a **library** running inside your app. No separate cluster needed. It uses the consumer/producer APIs internally.

---

## 3.2 Stateless vs Stateful Operations

### Stateless Operations (no state store)

| Operation | Input → Output | Key Change? |
|-----------|---------------|-------------|
| `filter(pred)` | 1 → 0 or 1 | No |
| `filterNot(pred)` | 1 → 0 or 1 | No |
| `map(kv-mapper)` | 1 → 1 | **Yes** → triggers repartition |
| `mapValues(v-mapper)` | 1 → 1 | No → **preferred** |
| `flatMap(kv-mapper)` | 1 → N | **Yes** → triggers repartition |
| `flatMapValues(v-mapper)` | 1 → N | No |
| `selectKey(key-mapper)` | 1 → 1 | **Yes** → triggers repartition |
| `foreach(action)` | Terminal, side effect | — |
| `peek(action)` | Pass-through + side effect | No |
| `branch(predicates)` | 1 stream → N streams | No |
| `merge(stream)` | 2 streams → 1 stream | No |

> ⚠️ **Repartition rule:** Any operation that changes the key (`map`, `selectKey`, `flatMap`) automatically inserts a **repartition topic** (through-topic) before downstream stateful operations.

### Stateful Operations (use RocksDB state stores)

| Operation | Description |
|-----------|-------------|
| `groupByKey()` | Group by current key — prerequisite for aggregation |
| `groupBy(selector)` | Re-key + group → **triggers repartition** |
| `count()` | Count per key → `KTable<K, Long>` |
| `aggregate(init, adder)` | Custom aggregation → `KTable<K, V>` |
| `reduce(reducer)` | Combine same-type values → `KTable<K, V>` |
| `windowedBy(windows)` | Apply time window before aggregation |
| `join()` | Inner join |
| `leftJoin()` | Left outer join |
| `outerJoin()` | Full outer join (KStream-KStream only) |

---

## 3.3 Exactly-Once in Kafka Streams

```properties
# Recommended for Kafka >= 2.5
processing.guarantee=exactly_once_v2

# Legacy (Kafka >= 0.11, deprecated)
processing.guarantee=exactly_once

# Default — higher throughput but at-least-once
processing.guarantee=at_least_once
```

### What exactly_once_v2 Does Internally

```
1. Configures internal consumer with isolation.level=read_committed
2. Configures internal producer with enable.idempotence=true
3. Uses shared transactional producer per thread (more efficient than exactly_once)
4. Atomic commit of: output records + input offsets + state store changelog
5. Commit interval: commit.interval.ms (default: 100ms for EOS)
```

> 🎯 **Exam:** "Which EOS setting is recommended for Kafka ≥ 2.5?" → `exactly_once_v2`

---

## 3.4 KStream vs KTable vs GlobalKTable

| Type | Semantics | State | Partitioning | Size |
|------|-----------|-------|-------------|------|
| `KStream` | **Insert** — each record is a new event | None | Same as source topic | Unbounded |
| `KTable` | **Upsert** — latest value per key | RocksDB | Same as source topic | Bounded |
| `GlobalKTable` | **Upsert** — fully replicated | RocksDB | **ALL partitions on EACH instance** | Bounded, small |

### Join Requirements

| Join | Co-partitioning Required? | Window Required? |
|------|--------------------------|-----------------|
| KStream ⨝ KStream | ✅ Yes | ✅ Yes (time window) |
| KStream ⨝ KTable | ✅ Yes | No |
| KStream ⨝ GlobalKTable | ❌ **No** | No |
| KTable ⨝ KTable | ✅ Yes | No |

> 🎯 **Exam:** "Join without co-partitioning constraint" → use **GlobalKTable**

### Windowing Types

| Window | Size | Overlapping? | Use Case |
|--------|------|-------------|----------|
| `Tumbling` | Fixed | ❌ Non-overlapping | Each record in exactly 1 window |
| `Hopping` | Fixed, advance < size | ✅ Overlapping | Record in multiple windows |
| `Sliding` | Fixed, event-time based | ✅ | Pairs of events within X time |
| `Session` | Dynamic (inactivity gap) | ❌ | User sessions, irregular events |

```java
// Tumbling window — 5-minute buckets
.windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)))

// Hopping window — 10-min window, advancing every 2 min
.windowedBy(TimeWindows.ofSizeAndGrace(Duration.ofMinutes(10), Duration.ofSeconds(0))
    .advanceBy(Duration.ofMinutes(2)))

// Session window — 30-min inactivity gap
.windowedBy(SessionWindows.ofInactivityGapWithNoGrace(Duration.ofMinutes(30)))
```

### Complete Streams Example

```java
Properties props = new Properties();
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "word-count");
props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);

StreamsBuilder builder = new StreamsBuilder();

// Enrich from reference table (no co-partitioning needed)
GlobalKTable<String, String> products = builder.globalTable("products");
KStream<String, String> orders = builder.stream("orders");

KStream<String, String> enriched = orders.join(products,
    (orderKey, orderValue) -> extractProductId(orderValue),  // key extractor
    (orderValue, productValue) -> enrich(orderValue, productValue)
);

// Aggregate with windowing
KTable<Windowed<String>, Long> countByProduct = enriched
    .groupBy((k, v) -> extractProductId(v))  // triggers repartition
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofHours(1)))
    .count(Materialized.as("product-counts-store"));

countByProduct
    .toStream()
    .map((windowedKey, count) -> KeyValue.pair(windowedKey.key(), count))
    .to("product-counts", Produced.with(Serdes.String(), Serdes.Long()));

KafkaStreams streams = new KafkaStreams(builder.build(), props);
streams.setUncaughtExceptionHandler(ex -> StreamThreadExceptionResponse.REPLACE_THREAD);
streams.start();
Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
```

---

## 3.5 DSL vs Processor API

| Aspect | Streams DSL | Processor API |
|--------|------------|---------------|
| Level | High-level functional | Low-level imperative |
| Code style | Lambda chains | Implement `Processor<K,V>` interface |
| State store access | Managed automatically | Direct via `ProcessorContext` |
| Punctuators (timers) | Not directly | ✅ `context.schedule()` |
| Custom state logic | Limited | ✅ Full control |
| Bridge | `transform()`, `transformValues()` | Can combine with DSL |

```java
// Processor API — custom stateful processor with timer
public class CountingProcessor implements Processor<String, String, String, String> {
    private ProcessorContext<String, String> context;
    private KeyValueStore<String, Long> store;

    @Override
    public void init(ProcessorContext<String, String> context) {
        this.context = context;
        this.store = context.getStateStore("count-store");

        // Punctuator: emit results every minute (wall-clock time)
        context.schedule(Duration.ofMinutes(1), PunctuationType.WALL_CLOCK_TIME, ts -> {
            store.all().forEachRemaining(kv ->
                context.forward(new Record<>(kv.key, kv.value.toString(), ts)));
        });
    }

    @Override
    public void process(Record<String, String> record) {
        Long current = store.get(record.key());
        store.put(record.key(), (current == null ? 0L : current) + 1);
    }
}

// Wire into topology
Topology topology = new Topology();
topology.addSource("Source", "input-topic")
        .addProcessor("CountingProcessor", CountingProcessor::new, "Source")
        .addStateStore(Stores.keyValueStoreBuilder(
            Stores.persistentKeyValueStore("count-store"),
            Serdes.String(), Serdes.Long()), "CountingProcessor")
        .addSink("Sink", "output-topic", "CountingProcessor");
```

---

# 4. Kafka Connect

## 4.1 Connect Architecture

```
External System                    Kafka                    External System
     │                              │                              │
     │  ┌──────────────────────┐    │    ┌───────────────────────┐ │
     └─►│   Source Connector   │───►│───►│    Sink Connector     │─┘
        │  (reads from source) │    │    │  (writes to target)   │
        └──────────────────────┘    │    └───────────────────────┘
               ↓ Tasks              │           ↓ Tasks
        ┌──────────────────┐        │    ┌──────────────────────┐
        │  Worker Process  │        │    │   Worker Process     │
        │  (JVM process)   │        │    │   (JVM process)      │
        └──────────────────┘        │    └──────────────────────┘
```

### Standalone vs Distributed Mode

| Aspect | Standalone | Distributed |
|--------|-----------|-------------|
| Workers | 1 process | Multiple processes |
| Offset storage | Local file | `offset.storage.topic` |
| Fault tolerance | ❌ No | ✅ Yes |
| Scalability | ❌ No | ✅ Yes |
| Use | Dev / testing | **Production** |
| REST API | ✅ | ✅ |

---

## 4.2 Worker Properties

```properties
# ─── Required ────────────────────────────────────────────────────
bootstrap.servers=broker1:9092,broker2:9092
group.id=connect-cluster                    # MUST be same for all workers in cluster

# ─── Converters ──────────────────────────────────────────────────
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=io.confluent.connect.avro.AvroConverter
value.converter.schema.registry.url=http://schema-registry:8081
key.converter.schemas.enable=false          # omit schema from JSON keys
value.converter.schemas.enable=true         # include schema in JSON values

# ─── Internal Topics (distributed mode) ──────────────────────────
config.storage.topic=connect-configs        # connector configs
offset.storage.topic=connect-offsets        # source connector offsets
status.storage.topic=connect-status         # connector/task status
config.storage.replication.factor=3
offset.storage.replication.factor=3
status.storage.replication.factor=3
offset.flush.interval.ms=10000              # how often to flush source offsets

# ─── Plugins ─────────────────────────────────────────────────────
plugin.path=/opt/kafka/plugins,/usr/share/kafka/plugins

# ─── REST Interface ───────────────────────────────────────────────
rest.host.name=0.0.0.0
rest.port=8083
rest.advertised.host.name=connect-worker-1  # for inter-worker communication
```

---

## 4.3 Source and Sink Connector Properties

### Source Connector — JDBC Example

```json
{
  "name": "jdbc-source-orders",
  "config": {
    "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
    "tasks.max": "4",
    "connection.url": "jdbc:postgresql://db:5432/mydb",
    "connection.user": "kafka_user",
    "connection.password": "${file:/opt/secrets/db.properties:password}",
    "mode": "incrementing",
    "incrementing.column.name": "id",
    "table.whitelist": "orders,line_items",
    "topic.prefix": "db.",
    "poll.interval.ms": "1000",
    "batch.max.rows": "1000",
    "timestamp.delay.interval.ms": "0",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081"
  }
}
```

### Sink Connector — Elasticsearch Example

```json
{
  "name": "elasticsearch-sink-orders",
  "config": {
    "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
    "tasks.max": "3",
    "topics": "db.orders",
    "connection.url": "http://elasticsearch:9200",
    "type.name": "_doc",
    "key.ignore": "false",
    "batch.size": "2000",
    "max.in.flight.requests": "5",
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "db.orders.DLQ",
    "errors.deadletterqueue.context.headers.enable": "true",
    "errors.log.enable": "true",
    "errors.log.include.messages": "true"
  }
}
```

---

## 4.4 Connector Scalability

```
Connector (1) → manages configuration and lifecycle
    ↓
Tasks (N) → actual I/O work, distributed across workers

tasks.max = UPPER LIMIT per connector
Actual tasks = min(tasks.max, source_parallelism)

For SINK connectors:
    source_parallelism = number of topic partitions
    → max tasks = min(tasks.max, partition_count)
    → tasks.max=10 with 4 partitions = only 4 tasks created

For SOURCE connectors:
    source_parallelism depends on source system
    (e.g., DB tables, file splits, Kinesis shards)
```

### Scaling Workers

```bash
# Distributed mode: add workers by starting them with same group.id
# Tasks are automatically redistributed (like consumer group rebalance)
CONNECT_GROUP_ID=connect-cluster ./bin/connect-distributed.sh config/connect-distributed.properties
```

---

## 4.5 Connect Offsets

| Offset Type | Storage Location | Description |
|-------------|-----------------|-------------|
| **Source offsets** | `offset.storage.topic` | Position in source system (row ID, file pos, LSN) |
| **Sink offsets** | `__consumer_offsets` | Standard consumer group offsets |

```
Source connector restarts → reads offset.storage.topic → resumes from last committed position
Sink connector restarts   → reads __consumer_offsets → resumes from last committed Kafka offset
```

> 💡 **Offset reset for source:** Delete the connector and recreate, OR delete specific entries from `offset.storage.topic` (advanced).

---

## 4.6 Single Message Transforms (SMT)

### Complete SMT Reference

| SMT | Applies To | Description |
|-----|-----------|-------------|
| `InsertField` | `$Key` / `$Value` | Add field with static value or record metadata |
| `ReplaceField` | `$Key` / `$Value` | Include (whitelist) or exclude (blacklist) fields |
| `MaskField` | `$Key` / `$Value` | Replace field value with null/zero/empty |
| `HoistField` | `$Key` / `$Value` | Wrap entire record in a named struct field |
| `ExtractField` | `$Key` / `$Value` | Extract one field as the new record |
| `ValueToKey` | — | Extract fields from value to create new key |
| `SetSchemaMetadata` | `$Key` / `$Value` | Set schema name/version |
| `TimestampConverter` | `$Key` / `$Value` | Convert timestamp format |
| `Cast` | `$Key` / `$Value` | Cast field to different type |
| `Filter` | — | Drop records matching condition |
| `Flatten` | `$Key` / `$Value` | Flatten nested struct to top-level |
| `RegexRouter` | — | Route to topic based on regex |
| `TimestampRouter` | — | Append timestamp to topic name |
| `TombstoneHandler` | — | Handle null-value records |

```properties
# SMT configuration in connector — applied in ORDER listed
transforms=addSource,maskPII,routeToDaily

transforms.addSource.type=org.apache.kafka.connect.transforms.InsertField$Value
transforms.addSource.static.field=source_system
transforms.addSource.static.value=payment-db

transforms.maskPII.type=org.apache.kafka.connect.transforms.MaskField$Value
transforms.maskPII.fields=credit_card,ssn,email

transforms.routeToDaily.type=org.apache.kafka.connect.transforms.TimestampRouter
transforms.routeToDaily.topic.format=${topic}-${timestamp}
transforms.routeToDaily.timestamp.format=yyyy-MM-dd
```

> ⚠️ **SMT Limitation:** SMTs process **one record at a time**. No joins, no aggregations, no external lookups. Use Kafka Streams for complex transformations.

---

## 4.7 Connect REST API

### Complete Endpoint Reference

```bash
# ─── Cluster Info ─────────────────────────────────────────────────
GET  /                                    # version, worker ID, cluster ID
GET  /connector-plugins                   # available plugin classes

# ─── Connector CRUD ───────────────────────────────────────────────
GET  /connectors                          # list connector names
POST /connectors                          # create connector
GET  /connectors/{name}                   # get config
PUT  /connectors/{name}/config            # update config (restarts connector)
DELETE /connectors/{name}                 # delete connector and its tasks

# ─── Connector Lifecycle ──────────────────────────────────────────
GET  /connectors/{name}/status            # RUNNING | PAUSED | FAILED
POST /connectors/{name}/restart           # restart connector
PUT  /connectors/{name}/pause             # pause (keeps offset, stops consuming)
PUT  /connectors/{name}/resume            # resume paused connector

# ─── Tasks ────────────────────────────────────────────────────────
GET  /connectors/{name}/tasks             # list tasks
GET  /connectors/{name}/tasks/{id}/status # task status
POST /connectors/{name}/tasks/{id}/restart # restart specific failed task

# ─── Validation ───────────────────────────────────────────────────
PUT  /connector-plugins/{class}/config/validate  # validate config without creating
```

```bash
# Create connector
curl -X POST http://connect:8083/connectors \
  -H 'Content-Type: application/json' \
  -d @connector-config.json

# Check all connector statuses
curl http://connect:8083/connectors?expand=status | jq .

# Restart only failed tasks
for connector in $(curl -s http://connect:8083/connectors); do
  curl -s http://connect:8083/connectors/$connector/tasks | jq -r '
    .[] | select(.state=="FAILED") | .id.task' |
  while read task_id; do
    curl -X POST http://connect:8083/connectors/$connector/tasks/$task_id/restart
  done
done
```

---

# 5. Application Testing

## 5.1 Testing Tools

### Tool Selection Matrix

| Scenario | Tool | Speed | Realism |
|----------|------|-------|---------|
| Unit test Kafka Streams | `TopologyTestDriver` | ⚡ Instant | Low (in-memory) |
| Unit test producer logic | `MockProducer` | ⚡ Instant | Low |
| Unit test consumer logic | `MockConsumer` | ⚡ Instant | Low |
| Integration test (Spring) | `EmbeddedKafka` | Fast | Medium |
| Full integration test | `Testcontainers` | Slow (Docker) | High (real broker) |

### TopologyTestDriver

```java
@Test
void testWordCountTopology() {
    // Setup
    Properties props = new Properties();
    props.put(StreamsConfig.APPLICATION_ID_CONFIG, "test");
    props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "dummy:1234"); // not used
    props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
    props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

    StreamsBuilder builder = new StreamsBuilder();
    buildWordCountTopology(builder);  // your topology

    try (TopologyTestDriver driver = new TopologyTestDriver(builder.build(), props)) {
        // Create test topics
        TestInputTopic<String, String> input = driver.createInputTopic(
            "words", new StringSerializer(), new StringSerializer());
        TestOutputTopic<String, Long> output = driver.createOutputTopic(
            "word-counts", new StringDeserializer(), new LongDeserializer());

        // Send test records
        input.pipeInput("k1", "hello world");
        input.pipeInput("k2", "hello kafka");

        // Verify output
        Map<String, Long> results = output.readKeyValuesToMap();
        assertEquals(2L, results.get("hello"));
        assertEquals(1L, results.get("world"));
        assertEquals(1L, results.get("kafka"));

        // Access state store directly
        KeyValueStore<String, Long> store = driver.getKeyValueStore("count-store");
        assertEquals(2L, store.get("hello"));
    }
}
```

### MockProducer and MockConsumer

```java
// MockProducer — test producer logic without broker
MockProducer<String, String> mockProducer = new MockProducer<>(
    true,                    // autoComplete — simulate successful send
    new StringSerializer(),
    new StringSerializer()
);
MyService service = new MyService(mockProducer);
service.processEvent("user-123", "USER_SIGNUP");

// Verify sent records
assertEquals(1, mockProducer.history().size());
ProducerRecord<String, String> sent = mockProducer.history().get(0);
assertEquals("user-123", sent.key());
assertEquals("events", sent.topic());

// Simulate send failure
mockProducer.errorNext(new KafkaException("Broker unavailable"));
assertThrows(KafkaException.class, () -> service.processEvent("k", "v"));

// MockConsumer — inject records manually
MockConsumer<String, String> mockConsumer = new MockConsumer<>(OffsetResetStrategy.EARLIEST);
mockConsumer.assign(List.of(new TopicPartition("orders", 0)));
mockConsumer.updateBeginningOffsets(Map.of(new TopicPartition("orders", 0), 0L));
mockConsumer.addRecord(new ConsumerRecord<>("orders", 0, 0L, "order-1", "{\"amount\":100}"));

MyConsumer myConsumer = new MyConsumer(mockConsumer);
myConsumer.poll();
assertEquals(1, myConsumer.getProcessedCount());
```

---

## 5.2 CLI Tools Reference

### kafka-topics.sh

```bash
# Create
kafka-topics.sh --bootstrap-server localhost:9092 --create \
  --topic my-topic --partitions 6 --replication-factor 3

# Describe (shows leader, ISR, replicas per partition)
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic my-topic

# List
kafka-topics.sh --bootstrap-server localhost:9092 --list

# Increase partitions
kafka-topics.sh --bootstrap-server localhost:9092 --alter \
  --topic my-topic --partitions 12

# Delete
kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic my-topic
```

### kafka-console-producer.sh / consumer.sh

```bash
# Produce with keys
kafka-console-producer.sh --bootstrap-server localhost:9092 --topic orders \
  --property parse.key=true \
  --property key.separator=":"
# Type: order-1:{"amount":100}

# Consume from beginning, show keys + timestamps
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders \
  --from-beginning \
  --property print.key=true \
  --property print.timestamp=true \
  --property print.partition=true \
  --max-messages 100

# Consume specific partition from offset 500
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders \
  --partition 2 --offset 500
```

### kafka-consumer-groups.sh

```bash
# List groups
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Describe (shows LAG per partition — most important!)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --describe

# Reset offsets (group MUST be stopped!)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --topic orders \
  --reset-offsets --to-earliest --dry-run     # preview
  --reset-offsets --to-earliest --execute     # apply

# Delete group
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --delete --group my-group
```

### Performance Testing

```bash
# Producer performance test — 1M records, 1KB each, max 100K/s
kafka-producer-perf-test.sh \
  --topic perf-test \
  --num-records 1000000 \
  --record-size 1024 \
  --throughput 100000 \
  --producer-props bootstrap.servers=localhost:9092 acks=1 linger.ms=5

# Output: records/sec, MB/sec, avg/max/50th/95th/99th latency

# Consumer performance test
kafka-consumer-perf-test.sh \
  --bootstrap-server localhost:9092 \
  --topic perf-test \
  --messages 1000000 \
  --group perf-consumer
```

---

## 5.3 Horizontal and Vertical Scaling

### Horizontal Scaling (Scale-Out)

| Component | Action | Benefit |
|-----------|--------|---------|
| Brokers | Add brokers → run `kafka-reassign-partitions.sh` | More storage, throughput |
| Consumers | Add consumers (up to partition count) | More processing parallelism |
| Producers | Add producer instances | More write throughput |
| Connect workers | Add workers with same `group.id` | Task redistribution |
| Streams apps | Add instances with same `application.id` | Task redistribution |

### Vertical Scaling (Scale-Up)

| Resource | Action | Benefit |
|----------|--------|---------|
| RAM | Increase heap + OS page cache | Larger page cache = faster reads |
| CPU | More cores | More network/IO threads |
| Disk | Faster SSDs | Lower write/read latency |
| Network | Higher bandwidth | More throughput |

### Partitions as Scaling Unit

```
Rule: max parallelism = partition count

Scale consumers: increase partitions FIRST, then add consumers
Scale Streams:   increase partitions → more tasks → distribute across instances
Connect sink:    increase partitions → more tasks up to tasks.max

WARNING: Increasing partitions breaks key ordering for existing records
```

---

## 5.4 Deployment Frameworks

| Framework | Type | Use Case |
|-----------|------|----------|
| **Docker Compose** | Local | Development, testing |
| **Kubernetes + Strimzi** | Container orchestration | Open-source K8s deployment |
| **Kubernetes + Confluent Operator** | Container orchestration | Enterprise K8s deployment |
| **Confluent Platform (cp-ansible)** | On-premises | Self-managed production |
| **Confluent Cloud** | Fully managed SaaS | Zero-ops, pay-per-use |
| **Amazon MSK** | Semi-managed | AWS ecosystem |
| **Azure Event Hubs (Kafka API)** | Semi-managed | Azure ecosystem |

---

# 6. Application Observability

## 6.1 Understanding Lag

### Lag Definition

```
Consumer Lag (per partition) = Log End Offset - Current Consumer Offset
Total Group Lag              = SUM of lag across all assigned partitions
```

### Lag Patterns

| Pattern | Meaning | Action |
|---------|---------|--------|
| Lag = 0 | Fully caught up | ✅ Normal |
| Lag stable (non-zero) | Consuming at same rate, but behind | Monitor, investigate |
| Lag **growing** | Consumer slower than producer | ⚠️ Scale up/out |
| Lag oscillating | Bursty production, catches up | Usually OK |
| One partition lagging | Slow/dead consumer on that partition | Check consumer instance |

### Reducing Lag

```
1. Add consumers (up to partition count)
2. Increase partition count (then add consumers)
3. Reduce max.poll.records (smaller batches = faster per-batch)
4. Optimize processing logic (batch DB writes, async I/O)
5. Increase consumer resources (more CPU/RAM)
6. Identify slow consumer instance → check logs
```

```bash
# Monitor lag continuously
watch -n 5 'kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --group my-group --describe'

# Lag by group (all topics)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --all-groups --describe
```

---

## 6.2 Performance Metrics

### Broker Metrics (JMX)

| Metric | Alert Threshold | Description |
|--------|----------------|-------------|
| `kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec` | — | Message ingestion rate |
| `kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec` | — | Bytes received per second |
| `kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec` | — | Bytes sent per second |
| `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions` | **> 0** | Partitions with lagging replicas |
| `kafka.server:type=ReplicaManager,name=OfflinePartitionsCount` | **> 0** | CRITICAL: partitions with no leader |
| `kafka.controller:type=KafkaController,name=ActiveControllerCount` | **≠ 1** | Must always be exactly 1 |
| `kafka.network:type=RequestMetrics,name=RequestsPerSec` | — | Request rate by type |
| `kafka.network:type=RequestMetrics,name=TotalTimeMs` | — | Request latency |
| `kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent` | **< 30%** | Thread saturation |

### Consumer Metrics (JMX)

| Metric | Alert Threshold | Description |
|--------|----------------|-------------|
| `records-lag-max` | **Growing** | Max lag across all partitions |
| `records-lag-avg` | — | Average lag |
| `fetch-rate` | — | Records fetched per second |
| `commit-latency-avg` | — | Offset commit time |
| `join-time-avg` | — | Group join time |
| `rebalance-rate-per-hour` | **Frequent** | Excessive rebalancing |

### Producer Metrics (JMX)

| Metric | Alert Threshold | Description |
|--------|----------------|-------------|
| `record-send-rate` | — | Records sent per second |
| `record-error-rate` | **> 0** | Failed sends (should be 0) |
| `request-latency-avg` | — | Producer request latency |
| `batch-size-avg` | **Low** | Low = batching inefficient |
| `record-queue-time-avg` | — | Time in RecordAccumulator |
| `buffer-available-bytes` | **→ 0** | Risk of `BufferExhaustedException` |

---

## 6.3 Logging with log4j

### Broker log4j.properties

```properties
log4j.rootLogger=INFO, stdout, kafkaAppender

# Console appender
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=[%d] %p %m (%c)%n

# Rolling file appender
log4j.appender.kafkaAppender=org.apache.log4j.DailyRollingFileAppender
log4j.appender.kafkaAppender.DatePattern='.'yyyy-MM-dd-HH
log4j.appender.kafkaAppender.File=${kafka.logs.dir}/server.log
log4j.appender.kafkaAppender.layout=org.apache.log4j.PatternLayout
log4j.appender.kafkaAppender.layout.ConversionPattern=[%d] %p %m (%c)%n

# Per-logger levels — tune for debugging
log4j.logger.kafka=INFO
log4j.logger.kafka.controller=INFO          # controller elections
log4j.logger.kafka.coordinator=INFO         # consumer group coordination
log4j.logger.kafka.network.RequestChannel=WARN  # request logs (verbose)
log4j.logger.kafka.log.LogCleaner=INFO      # compaction
log4j.logger.state.change.logger=INFO       # partition state changes
log4j.logger.org.apache.kafka=INFO
```

### Key Log Files

| File | Contents |
|------|----------|
| `server.log` | Main broker log — most important |
| `controller.log` | Controller election events |
| `kafka-request.log` | Request/response details (verbose) |
| `state-change.log` | Partition leader changes |
| `kafka-authorizer.log` | ACL authorization decisions |
| `connect.log` | Kafka Connect worker log |

### Dynamic Log Level Change

```bash
# Change log level at runtime without restart
kafka-configs.sh --bootstrap-server localhost:9092 \
  --entity-type brokers --entity-name 1 --alter \
  --add-config "log4j.logger.kafka.coordinator=DEBUG"

# Revert
kafka-configs.sh --bootstrap-server localhost:9092 \
  --entity-type brokers --entity-name 1 --alter \
  --delete-config "log4j.logger.kafka.coordinator"
```

---

## 6.4 Common Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `LEADER_NOT_AVAILABLE` | Partition leader election in progress | Transient — auto-retried |
| `NotLeaderForPartitionException` | Request sent to wrong broker | Producer refreshes metadata, retries |
| `NotEnoughReplicasException` | ISR count < `min.insync.replicas` | Check broker health; lower `min.isr` temporarily |
| `RecordTooLargeException` | Message > `max.message.bytes` | Increase limit or split message |
| `OffsetOutOfRangeException` | Requested offset deleted by retention | Set `auto.offset.reset=earliest` |
| `GroupCoordinatorNotAvailable` | Coordinator not yet elected | Transient — consumer retries |
| `RebalanceInProgressException` | Commit during rebalance | Handle in `onPartitionsRevoked` callback |
| `InvalidOffsetException` | Corrupt `__consumer_offsets` entry | Reset consumer group offsets |
| `TimeoutException` | Operation timed out | Check network, broker load, increase timeout configs |
| `UnknownTopicOrPartitionException` | Topic doesn't exist | Create topic or check name |
| `SerializationException` | Schema mismatch or corrupt data | Check schema versions, Deserializer config |
| `ProducerFencedException` | Zombie producer fenced | Restart app — cannot recover |
| `BufferExhaustedException` | `buffer.memory` full | Increase buffer, reduce produce rate |
| `NetworkException` | Network blip | Retryable — check connectivity |
| `ConfigException` | Invalid config combination | e.g., `max.in.flight > 5` with idempotence |

---

## 6.5 Configuring Alerts

### Critical Alerts (P0 — Immediate Action)

```yaml
# offline-partitions-count > 0
# → No leader. Data UNAVAILABLE. Immediate action.
alert: OfflinePartitions
  condition: kafka_controller_KafkaController_OfflinePartitionsCount > 0
  severity: CRITICAL

# active-controller-count ≠ 1
alert: ControllerCount
  condition: kafka_controller_KafkaController_ActiveControllerCount != 1
  severity: CRITICAL

# Broker down
alert: BrokerDown
  condition: up{job="kafka"} == 0
  severity: CRITICAL
```

### Warning Alerts (P1 — Investigate)

```yaml
# under-replicated-partitions > 0 for > 60s
alert: UnderReplicated
  condition: kafka_server_ReplicaManager_UnderReplicatedPartitions > 0
  for: 60s
  severity: WARNING

# Consumer lag growing for > 5 min
alert: ConsumerLagGrowing
  condition: kafka_consumer_records_lag_max > 10000
  for: 5m
  severity: WARNING

# Disk usage > 80%
alert: DiskUsage
  condition: disk_used_percent{mountpoint="/var/kafka"} > 80
  severity: WARNING

# Network thread idle < 30% (saturation)
alert: NetworkThreadSaturation
  condition: kafka_network_RequestMetrics_RequestHandlerAvgIdlePercent < 0.30
  severity: WARNING

# Producer error rate > 0
alert: ProducerErrors
  condition: kafka_producer_record_error_rate > 0
  for: 1m
  severity: WARNING
```

### Prometheus + JMX Exporter Setup

```yaml
# jmx_exporter config for Kafka
rules:
  - pattern: "kafka.server<type=BrokerTopicMetrics, name=(.+), topic=(.+)><>Count"
    name: kafka_server_brokertopicmetrics_$1_total
    labels:
      topic: $2

  - pattern: "kafka.server<type=ReplicaManager, name=(.+)><>Value"
    name: kafka_server_replicamanager_$1

  - pattern: "kafka.consumer<type=consumer-fetch-manager-metrics, client-id=(.+)><>records-lag-max"
    name: kafka_consumer_records_lag_max
    labels:
      client_id: $1
```

---

# 7. Master Quiz

## 20 Exam-Style Questions

---

**Q1.** A topic has 4 partitions and replication-factor=3 with `min.insync.replicas=2`. One broker fails. Producers use `acks=all`. What happens?

- A) All production stops immediately
- B) Production continues if 2+ ISRs remain per partition
- C) Kafka automatically downgrades to `acks=1`
- D) `NotEnoughReplicasException` is thrown immediately

**✅ Answer: B** — With RF=3 and min.isr=2, losing 1 broker leaves 2 replicas. If they remain in ISR, `acks=all` is still satisfied. Production continues.

---

**Q2.** `enable.idempotence=true` is set. The developer also sets `max.in.flight.requests.per.connection=6`. What happens?

- A) Works normally — max.in.flight only affects ordering, not idempotence
- B) `ConfigException` thrown at startup
- C) Idempotence is silently disabled
- D) Kafka auto-reduces to max.in.flight=5

**✅ Answer: B** — With idempotence, max.in.flight MUST be ≤ 5. Setting 6 throws `ConfigException`.

---

**Q3.** A consumer has `auto.offset.reset=earliest` and has never consumed from "events" topic. The topic has had 7 days of data but retention is 3 days. From which offset does consumption start?

- A) Offset 0
- B) The earliest **available** offset (not 0 — older records are deleted)
- C) The latest offset
- D) Throws `OffsetOutOfRangeException`

**✅ Answer: B** — `earliest` = first **available** offset. With retention, that may be far beyond 0.

---

**Q4.** You call `consumer.assign(partitions)` and then `consumer.subscribe(topics)` in the same consumer instance. What happens?

- A) `subscribe()` overrides `assign()`
- B) `assign()` takes precedence
- C) `IllegalStateException` is thrown
- D) Both work independently

**✅ Answer: C** — `assign()` and `subscribe()` are mutually exclusive. Mixing them throws `IllegalStateException`.

---

**Q5.** A Kafka Streams app uses `KTable<String, User>` (8 partitions) joined with `KStream<String, Order>` (6 partitions). What happens?

- A) Join works — Streams handles mismatched partitions
- B) `TopologyException` at startup — co-partitioning violated
- C) Streams automatically re-partitions the KTable
- D) Join works but ordering is not guaranteed

**✅ Answer: B** — KStream-KTable joins require co-partitioning: same partition count + same partitioner. Use `GlobalKTable` to avoid this.

---

**Q6.** A Connect Sink connector has `tasks.max=8` on a topic with 3 partitions. How many tasks run?

- A) 8 tasks
- B) 3 tasks
- C) 1 task
- D) 11 tasks

**✅ Answer: B** — Sink tasks = `min(tasks.max, partition_count)` = `min(8, 3)` = **3**.

---

**Q7.** You need to add a new field `"country"` (required, no default) to an existing Avro schema in the Schema Registry. Compatibility is set to BACKWARD. What happens?

- A) Schema registered successfully
- B) Schema Registry rejects the schema — BACKWARD compatibility broken
- C) Schema registered but old consumers get null for country
- D) Schema is registered and old data is migrated automatically

**✅ Answer: B** — BACKWARD: new schema must read old data. Old records have no `country` field. Required field with no default → old data unreadable → rejected.

---

**Q8.** Which SMT would you use to route records from topic "transactions" to "transactions-2024-01-15" based on the record's timestamp?

- A) `RegexRouter`
- B) `TimestampRouter`
- C) `TimestampConverter`
- D) `InsertField`

**✅ Answer: B** — `TimestampRouter` appends a formatted timestamp to the topic name.

---

**Q9.** A producer sends with `acks=1`. The leader acknowledges, then crashes before replication. What delivery guarantee was achieved?

- A) exactly-once (leader confirmed)
- B) at-least-once (producer will retry)
- C) at-most-once (message may be lost)
- D) at-least-once with deduplication

**✅ Answer: C** — `acks=1` = leader only. No follower replication. If leader crashes before replication → **message lost** → at-most-once risk.

---

**Q10.** In Kafka Streams, what does `selectKey()` automatically cause?

- A) A state store to be created
- B) A repartition through-topic to be inserted before downstream stateful operations
- C) A GlobalKTable lookup
- D) A session window to be applied

**✅ Answer: B** — `selectKey()` changes the key → Streams inserts a repartition topic to ensure correct co-partitioning for downstream operations.

---

**Q11.** `active-controller-count` shows 0 across all brokers. What is the impact?

- A) Cluster operates normally in read-only mode
- B) No partition leader elections can occur — cluster cannot recover from broker failures
- C) Consumers can still read but producers cannot write
- D) ZooKeeper takes over controller duties

**✅ Answer: B** — No controller = no leader elections = if a broker fails, affected partitions become offline. Critical outage scenario.

---

**Q12.** A GlobalKTable is built from a topic with 12 partitions. The Streams app has 4 instances. How much data does each instance hold?

- A) 3 partitions worth (12/4)
- B) All 12 partitions — full dataset
- C) 1 partition — only assigned partition
- D) Depends on available memory

**✅ Answer: B** — GlobalKTable is **fully replicated** to every instance. Each of the 4 instances holds a complete copy.

---

**Q13.** In distributed Connect mode, where are source connector offsets stored?

- A) In a local file on each worker
- B) In `offset.storage.topic` Kafka topic
- C) In `__consumer_offsets`
- D) In ZooKeeper

**✅ Answer: B** — Distributed mode: source offsets in `offset.storage.topic`. Standalone mode uses a local file.

---

**Q14.** You want to unit test a Kafka Streams topology without any Kafka broker. Which tool should you use?

- A) `EmbeddedKafka`
- B) `Testcontainers`
- C) `TopologyTestDriver`
- D) `MockProducer`

**✅ Answer: C** — `TopologyTestDriver` is entirely in-memory. No broker needed. Fastest Streams testing option.

---

**Q15.** Consumer group "orders-processors" has `consumer-lag-max = 50,000` and lag is growing every minute. What should you do FIRST?

- A) Increase `retention.ms` on the topic
- B) Investigate whether consumers are slower than producers; consider adding consumers or increasing partitions
- C) Decrease `max.poll.records` to reduce load on brokers
- D) Restart all producers to reduce throughput

**✅ Answer: B** — Growing lag = consumer can't keep up. First: diagnose the bottleneck (slow processing? too few consumers?). Then scale consumers or partitions if needed.

---

**Q16.** What is the purpose of `sendOffsetsToTransaction()` in a transactional producer?

- A) Commits consumer offsets to `__consumer_offsets` independently of the transaction
- B) Atomically includes consumer offset commits within the current transaction — ensures exactly-once read-process-write
- C) Saves producer offsets for recovery
- D) Flushes the transaction buffer to disk

**✅ Answer: B** — `sendOffsetsToTransaction()` makes the consumer offset commit part of the producer transaction. Either both the output records AND the offset commit succeed, or neither does.

---

**Q17.** A `CooperativeStickyAssignor` is configured. A new consumer joins the group. What happens differently compared to `RangeAssignor`?

- A) All consumers stop processing during the full rebalance
- B) Only partitions that need to move are revoked; other consumers continue processing
- C) No partitions are moved to the new consumer
- D) The new consumer gets all partitions immediately

**✅ Answer: B** — Cooperative incremental rebalancing: only partitions that need to be reassigned are revoked. Other consumers keep their partitions and keep processing. Eliminates "stop-the-world" rebalance.

---

**Q18.** `under-replicated-partitions` metric shows 5 on broker-1. What is the most likely cause?

- A) 5 consumers are lagging
- B) A broker is down or lagging — followers cannot replicate fast enough
- C) `min.insync.replicas` is set too low
- D) The topic was just created

**✅ Answer: B** — Under-replicated partitions = replicas not keeping up with leader. Most common cause: a broker is down, network issues, or disk saturation on a follower.

---

**Q19.** What happens if you set `cleanup.policy=compact,delete` on a topic?

- A) Invalid — cannot combine policies
- B) Compaction removes old key versions AND size/time-based deletion removes old segments
- C) Compact applies to keys, delete applies to values
- D) The policies alternate on each compaction cycle

**✅ Answer: B** — `compact,delete` combines both: compaction removes superseded key versions, AND retention (time/size) still deletes old segments. Both policies apply simultaneously.

---

**Q20.** A Kafka Streams app uses `processing.guarantee=exactly_once_v2`. The app crashes mid-transaction. What happens to the records that were produced but not committed?

- A) Records are committed immediately on the next startup
- B) The Transaction Coordinator marks the transaction as ABORT; records remain invisible to `read_committed` consumers
- C) Records are deleted from the topic
- D) Records become visible after `transaction.timeout.ms`

**✅ Answer: B** — The Transaction Coordinator detects the timeout (no COMMIT/ABORT received) → marks transaction ABORTED → all `read_committed` consumers skip those records permanently.

---

# 8. Quick Reference Cheat Sheet

## Critical Default Values

| Config | Default | Notes |
|--------|---------|-------|
| `session.timeout.ms` | 45000 ms | Was 10s in older versions |
| `heartbeat.interval.ms` | 3000 ms | Must be << session.timeout |
| `max.poll.interval.ms` | 300000 ms | 5 minutes |
| `max.poll.records` | 500 | |
| `auto.commit.interval.ms` | 5000 ms | |
| `fetch.min.bytes` | 1 byte | |
| `fetch.max.wait.ms` | 500 ms | |
| `max.partition.fetch.bytes` | 1 MB | |
| `fetch.max.bytes` | 50 MB | |
| `batch.size` | 16384 bytes (16KB) | |
| `linger.ms` | 0 ms | |
| `buffer.memory` | 32 MB | |
| `max.block.ms` | 60000 ms | |
| `request.timeout.ms` | 30000 ms | |
| `delivery.timeout.ms` | 120000 ms | 2 minutes |
| `retry.backoff.ms` | 100 ms | |
| `acks` | `all` (Kafka 3.0+) | Was `1` in older versions |
| `retries` | MAX_INT | |
| `max.in.flight.requests` | 5 | |
| `enable.idempotence` | `true` (Kafka 3.0+) | |
| `retention.ms` | 604800000 ms | 7 days |
| `segment.bytes` | 1 GB | |
| `max.message.bytes` | 1048588 bytes | ~1 MB |
| `num.partitions` | 1 | Broker default |
| `connect.rest.port` | 8083 | |
| `schema.registry.port` | 8081 | |

## Critical Rules — Memorize These

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Ordering guaranteed WITHIN a partition only — never across            │
│ 2. Max 1 active consumer per partition per consumer group                │
│ 3. assign() XOR subscribe() — mutually exclusive, both = IllegalState    │
│ 4. Idempotence: acks=all + retries=MAX + max.in.flight≤5 (auto-set)     │
│ 5. EOS = Idempotence + Transactions + read_committed                     │
│ 6. Partitions: can ONLY increase, NEVER decrease                         │
│ 7. KTable join: requires co-partitioning. GlobalKTable: no constraint    │
│ 8. Sink tasks = min(tasks.max, partition_count)                          │
│ 9. active-controller-count MUST always = 1                               │
│ 10. exactly_once_v2 recommended for Kafka ≥ 2.5                         │
│ 11. GlobalKTable = fully replicated to EVERY instance                    │
│ 12. selectKey() / map() → automatic repartition topic in Streams         │
│ 13. SMTs: one record at a time — no joins, no aggregations               │
│ 14. Source offsets: offset.storage.topic. Sink: __consumer_offsets       │
│ 15. BACKWARD: new schema reads old data → add fields WITH defaults       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Config Mnemonics

| Mnemonic | Meaning |
|----------|---------|
| **A-R-I** | **A**cks=all + **R**etries=MAX + **I**n-flight≤5 → required for idempotence |
| **EOS = I+T+RC** | **E**xactly-**O**nce = **I**dempotence + **T**ransactions + **R**ead_**C**ommitted |
| **CTRL=1** | Active **C**on**t**rolle**r** count must always equal **1** |
| **3-T Connect** | 3 internal **T**opics: config + offset + status storage |
| **B-F-N** | Schema modes: **B**ackward (new reads old), **F**orward (old reads new), **N**one (no check) |
| **PJS-FCH** | Consumer flow: **P**art assignment → **J**oinGroup → **S**yncGroup → **F**etch → **C**ommit → **H**eartbeat |

---

# 9. Glossary

| Term | Definition |
|------|-----------|
| **ACK** | Acknowledgment from broker confirming message receipt |
| **at-least-once** | No message loss; duplicates possible |
| **at-most-once** | Possible loss; no duplicates |
| **Batch** | Group of records sent together for throughput |
| **Bootstrap Server** | Initial broker(s) for cluster discovery |
| **Broker** | A single Kafka server (JVM process) |
| **Changelog topic** | Internal Kafka Streams topic backing a state store |
| **Cleanup policy** | How old data is removed: `delete` or `compact` |
| **Cluster** | Group of Kafka brokers |
| **Compaction** | Retain only latest value per key |
| **Consumer** | Client that reads from Kafka topics |
| **Consumer Group** | Group sharing partition consumption |
| **Controller** | Broker managing leader elections |
| **Co-partitioning** | Two topics with same #partitions + same partitioner |
| **DLQ** | Dead Letter Queue — topic for failed records |
| **Deserializer** | Converts `byte[]` to typed object |
| **DSL** | Domain-Specific Language — high-level Streams API |
| **Epoch** | Producer generation counter preventing zombie writes |
| **exactly-once** | No loss, no duplicates |
| **Follower** | Replica that copies from leader |
| **GlobalKTable** | Streams table fully replicated to every instance |
| **Group Coordinator** | Broker managing consumer group lifecycle |
| **Header** | Key-value metadata on a record (as `byte[]`) |
| **Idempotence** | Same result if operation repeated — deduplicates retries |
| **ISR** | In-Sync Replica — follower caught up with leader |
| **KRaft** | Kafka Raft — replaces ZooKeeper for metadata management |
| **KStream** | Append-only stream — insert semantics |
| **KTable** | Changelog stream — upsert semantics |
| **Lag** | Consumer offset distance behind log end offset |
| **Leader** | Replica handling all reads/writes for a partition |
| **Linger** | Wait time to accumulate records into a batch |
| **Log** | Underlying append-only file structure of a partition |
| **Offset** | Integer uniquely identifying a record in a partition |
| **Partition** | Ordered, immutable unit of parallelism |
| **PID** | Producer ID — unique identifier for idempotent producers |
| **Punctuator** | Time-triggered callback in Streams Processor API |
| **Rebalance** | Redistribution of partitions among consumers |
| **Replica** | Copy of a partition on another broker |
| **Retention** | How long records are kept (time or size) |
| **Schema Registry** | Service storing versioned Avro/Protobuf/JSON schemas |
| **Segment** | Physical log file making up part of a partition |
| **Serializer** | Converts typed object to `byte[]` |
| **SMT** | Single Message Transform — per-record Connect transformation |
| **State Store** | Kafka Streams local RocksDB storage for stateful ops |
| **Sticky Partitioner** | Default no-key partitioner since Kafka 2.4 |
| **Task** | Unit of work in Streams (per partition) or Connect (I/O) |
| **Through-topic** | Auto-inserted repartition topic in Kafka Streams |
| **Tombstone** | Record with null value — marks key for deletion |
| **Topic** | Named durable append-only log |
| **Transaction** | Atomic write across multiple partitions/topics |
| **Windowing** | Grouping records by time window for aggregation |

---

# 10. Exam Day Tips

## Top 10 Traps — Read Before You Enter

| # | Trap | Rule |
|---|------|------|
| 1 | `max.in.flight > 5` + idempotence | **`ConfigException`** at startup |
| 2 | `assign()` + `subscribe()` together | **`IllegalStateException`** |
| 3 | Reducing partitions | **IMPOSSIBLE** — delete + recreate |
| 4 | KTable join without co-partitioning | Use **GlobalKTable** |
| 5 | More consumers than partitions | Extra consumers = **idle** |
| 6 | `exactly_once` vs `exactly_once_v2` | Use **v2** for Kafka ≥ 2.5 |
| 7 | `auto.offset.reset=earliest` = offset 0 | No! = first **available** offset |
| 8 | Sink tasks.max > partition count | Actual tasks = **min(tasks.max, partitions)** |
| 9 | `acks=1` = safe | **No!** Leader crash before replication = loss |
| 10 | SMTs can join/aggregate | **No!** SMTs = one record only |

## Question Strategy

```
1. READ ALL 4 OPTIONS before answering
2. Watch for: "EXCEPT", "NOT", "NEVER", "ALWAYS", "BY DEFAULT"
3. Multi-select: select ALL correct answers (no partial credit)
4. Config questions → think: what does it control? what's the default? what's the risk?
5. Scenario questions → identify: failure mode? guarantee violated? fix?
6. ~90 seconds per question — flag uncertain, return at end
7. Trick words narrow answers: "ONLY", "CANNOT", "ALWAYS"
```

## Last-Minute Formula Sheet

```
Exactly-Once Producer:
  enable.idempotence=true → auto: acks=all + retries=MAX + max.in.flight≤5

Exactly-Once E2E:
  Producer(idempotence + transactions) + Consumer(read_committed)

Controller health:
  active-controller-count == 1 → OK
  active-controller-count == 0 → CRITICAL (no leader elections)
  active-controller-count == 2 → CRITICAL (split brain)

Max consumer parallelism:
  = number of topic partitions
  (additional consumers = idle)

Connect Sink tasks:
  actual_tasks = min(tasks.max, topic_partition_count)

Lag calculation:
  lag = log_end_offset - current_offset

Schema BACKWARD:
  new schema CAN read old data
  → add fields WITH defaults, or remove fields

Schema FORWARD:
  old schema CAN read new data
  → add fields WITH defaults

KTable join:
  requires co-partitioning (same count + same partitioner)

GlobalKTable join:
  no co-partitioning needed
  fully replicated to every Streams instance
```

---

> **Good luck! You've got this. 🚀**
>
> *Remember: The exam tests understanding, not memorization. If you understand WHY each config exists and what it protects against, you'll reason through even unfamiliar questions correctly.*
