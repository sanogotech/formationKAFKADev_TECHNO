

# 🎯 100 paramètres de tuning Kafka (avec focus sur réplicas & partitions)

## Catégorie 1 : Réplication – Paramètres broker (15 paramètres)

*Introduction : Ces réglages contrôlent la façon dont les réplicas sont gérés : élection du leader, synchronisation, ISR, et reprise après panne.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 1 | `default.replication.factor` | `min(3, nb_brokers)` | 5 brokers → 3 |
| 2 | `min.insync.replicas` | `(replication.factor // 2) + 1` | RF=3 → 2 |
| 3 | `unclean.leader.election.enable` | `false` si perte de données interdite | false |
| 4 | `replica.lag.time.max.ms` | `max(10000, 2 * replica.fetch.wait.max.ms)` | fetch.wait=500 → 10000 ms |
| 5 | `num.replica.fetchers` | `min(4, ceil(0.5 * num.io.threads))` | io threads=16 → 4 |
| 6 | `replica.fetch.max.bytes` | `max(1 MB, 2 * message.max.bytes)` | message.max=10 MB → 20 MB |
| 7 | `replica.fetch.wait.max.ms` | `min(500, replica.lag.time.max.ms / 2)` | lag=10000 → 500 ms |
| 8 | `replica.fetch.min.bytes` | `max(1024, fetch.min.bytes du consommateur)` | consommateur=1 → 1024 |
| 9 | `replica.socket.receive.buffer.bytes` | `socket.receive.buffer.bytes` du broker | 1 048 576 |
| 10 | `replica.high.watermark.checkpoint.interval.ms` | `5000` (fixe recommandé) | 5000 |
| 11 | `leader.replication.throttled.rate` | `débit_disque * 0.8` (réplication en throttling) | disque 200 MB/s → 160 MB/s |
| 12 | `follower.replication.throttled.rate` | idem leader | 160 MB/s |
| 13 | `replica.alter.log.dirs.io.max.bytes.per.second` | `débit_disque * 0.5` | 100 MB/s |
| 14 | `replica.selector.class` | `null` (par défaut) ou `"RackAwareReplicaSelector"` si rack awareness | `RackAwareReplicaSelector` |
| 15 | `reserved.broker.max.id` | `max(10000, nb_max_brokers_attendus * 2)` | 500 brokers → 10000 |

---

## Catégorie 2 : Partitions – Création et gestion (15 paramètres)

*Introduction : Combien de partitions ? Comment les répartir ? Quel impact sur le cluster ? Ces paramètres répondent à ces questions.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 16 | `num.partitions` (défaut topic) | `max(10, ceil(débit_MB/s / 20))` | débit 200 MB/s → 10 (ou 20 si plus de brokers) |
| 17 | `log.segment.bytes` | `débit_écriture_MB/s * 3600 * heures_rotation` | 100 MB/s, 1h → 360 GB → 1 GB = 1 073 741 824 |
| 18 | `log.roll.ms` | `max(86400000, 2 * log.segment.bytes / débit_écriture)` | débit 100 MB/s, segment 1 GB → 10 s → au moins 86400000 ms (24h) |
| 19 | `log.retention.hours` | `espace_disque_total_GB * 0.8 / (débit_écriture_GB/h)` | 2 To, débit 10 GB/h → 160 h → 168 h |
| 20 | `log.retention.bytes` | `espace_disque_par_partition * nb_partitions` | 200 GB/partition, 100 partitions → 20 000 GB |
| 21 | `log.index.size.max.bytes` | `log.segment.bytes / 100` | 1 GB → 10 MB = 10 485 760 |
| 22 | `log.index.interval.bytes` | `4096` (par défaut) ou `log.segment.bytes / 10000` | 1 GB → 100 KB → 4096 plus petit |
| 23 | `num.recovery.threads.per.data.dir` | `min(2, nb_cœurs / 4)` | 8 cœurs → 2 |
| 24 | `auto.create.topics.enable` | `false` en production (calcul : éviter la prolifération) | false |
| 25 | `delete.topic.enable` | `true` | true |
| 26 | `compression.type` | `"producer"` (laisse le producteur décider) ou `"lz4"` | producer |
| 27 | `message.timestamp.difference.max.ms` | `max(60000, 2 * request.timeout.ms)` | request.timeout=30000 → 60000 ms |
| 28 | `message.timestamp.type` | `"CreateTime"` (préféré) ou `"LogAppendTime"` | CreateTime |
| 29 | `max.message.bytes` (par topic) | `message.max.bytes` du broker | 10 485 760 |
| 30 | `segment.jitter.ms` | `0.1 * log.roll.ms` | log.roll.ms=86400000 → 8 640 000 ms |

---

## Catégorie 3 : Rééquilibrage des réplicas (Rebalance) (10 paramètres)

*Introduction : Lorsqu’un broker tombe ou qu’on ajoute des partitions, Kafka réassigne les réplicas. Ces paramètres contrôlent la vitesse et la douceur de ce processus.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 31 | `rebalance.max.retries` | `min(10, (retention.hours * 3600) / rebalance.retry.backoff.ms)` | 168h, backoff=60000 → 10 |
| 32 | `rebalance.retry.backoff.ms` | `max(60000, 2 * group.max.session.timeout.ms)` | session.timeout=30000 → 60000 |
| 33 | `controlled.shutdown.enable` | `true` | true |
| 34 | `controlled.shutdown.max.retries` | `5` (fixe) | 5 |
| 35 | `controlled.shutdown.retry.backoff.ms` | `5000` | 5000 |
| 36 | `auto.leader.rebalance.enable` | `false` (préférable manuel) | false |
| 37 | `leader.imbalance.per.broker.percentage` | `10` (si auto.leader.rebalance.enable=true) | 10 |
| 38 | `leader.imbalance.check.interval.seconds` | `300` | 300 |
| 39 | `replica.selector.class` (déjà vu) | voir #14 | – |
| 40 | `zookeeper.session.timeout.ms` | `min(40000, 10 * zookeeper.sync.time.ms)` | sync.time=2000 → 20000 ms |

---

## Catégorie 4 : Producteur – Parallélisme et partitions (10 paramètres)

*Introduction : Le producteur écrit dans des partitions. Ces réglages optimisent l’équilibrage de charge et la résilience.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 41 | `partitioner.class` | `UniformRoundRobinPartitioner` (si clé absente) ou `DefaultPartitioner` | DefaultPartitioner |
| 42 | `partition.assignment.strategy` (producteur ? non, consommateur) – plutôt `key.serializer` | – | – |
| 43 | `enable.idempotence` | `true` si exactly‑once ou ordre strict par partition | true |
| 44 | `max.in.flight.requests.per.connection` | `1` si idempotence=false, `5` si idempotence=true | 5 |
| 45 | `batch.size` | `(débit_attendu_producteur_MB/s * 1000) / messages_par_seconde` | 10 MB/s, 10k msg/s → 1 KB/msg → batch 16 KB = 16384 |
| 46 | `linger.ms` | `min(20, (batch.size * 1000) / débit_bytes_par_ms)` | batch 16 KB, débit 1 KB/ms → 16 ms → 10 |
| 47 | `buffer.memory` | `max(32 MB, 2 * batch.size * (nb_partitions_actives + 5))` | batch 16 KB, 10 partitions → 480 KB → 32 MB |
| 48 | `max.request.size` | `max(1 MB, 1.5 * message.max.bytes)` | message.max=10 MB → 15 MB = 15 728 640 |
| 49 | `retries` | `min(5, ceil(log(1‑fiabilité)/log(1‑proba_erreur)))` | fiabilité 99.99%, erreur 1% → 920 → mais max 5 |
| 50 | `delivery.timeout.ms` | `max(120000, request.timeout.ms + linger.ms + retry.backoff.ms * retries)` | 30000+10+100*5=30510 → 120000 |

---

## Catégorie 5 : Consommateur – Parallélisme et rééquilibrage (15 paramètres)

*Introduction : Le consommateur lit les partitions. Pour exploiter 300 partitions, il faut jusqu’à 300 consumers. Ces réglages contrôlent l’affectation des partitions et la stabilité du groupe.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 51 | `partition.assignment.strategy` | `CooperativeStickyAssignor` (Kafka ≥ 2.4) pour rebalance incrémental | `CooperativeStickyAssignor` |
| 52 | `max.poll.interval.ms` | `max(300000, 2 * temps_traitement_lot_ms)` | traitement lot = 120 s → 300000 |
| 53 | `session.timeout.ms` | `max(10000, 3 * heartbeat.interval.ms)` | heartbeat=3000 → 10000 |
| 54 | `heartbeat.interval.ms` | `session.timeout.ms / 3` | 10000/3 ≈ 3333 |
| 55 | `max.poll.records` | `min(500, (max.poll.interval.ms * débit_msg_par_ms) / 2)` | débit 100 msg/s, intervalle 300 s → 15000 → 500 |
| 56 | `fetch.min.bytes` | `max(1024, batch.size producteur / 2)` | batch=16384 → 8192 |
| 57 | `fetch.max.bytes` | `max(50 MB, 2 * max.poll.records * taille_moyenne_message)` | taille 1 KB, 500 records → 1 MB → 50 MB |
| 58 | `fetch.max.wait.ms` | `min(500, max.poll.interval.ms / 10)` | 300000/10=30000 → 500 |
| 59 | `max.partition.fetch.bytes` | `fetch.max.bytes / (nb_partitions_par_consumer * 2)` | fetch=50 MB, 10 partitions → 2,5 MB |
| 60 | `check.crcs` | `false` (si performance prioritaire) | false |
| 61 | `enable.auto.commit` | `false` (préférer commit manuel) | false |
| 62 | `auto.commit.interval.ms` | `min(5000, max.poll.interval.ms / 10)` | 300000/10=30000 → 5000 |
| 63 | `auto.offset.reset` | `"earliest"` (si reprise après panne) ou `"latest"` | earliest |
| 64 | `exclude.internal.topics` | `true` | true |
| 65 | `client.rack` | `broker.rack` correspondant pour consommer local | rack-1 |

---

## Catégorie 6 : Réseau & Quotas (10 paramètres)

*Introduction : Pour éviter les « noisy neighbors » et garantir un débit minimal aux réplicas.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 66 | `quota.producer.default` | `(débit_total_entrant_MB/s * 0.7) / nb_producteurs_moyen` | débit 500 MB/s, 10 producteurs → 35 MB/s = 36 700 000 |
| 67 | `quota.consumer.default` | idem pour consommateurs | 35 MB/s |
| 68 | `quota.replication.default` | `débit_disque * 0.5` | disque 200 MB/s → 100 MB/s |
| 69 | `leader.replication.throttled.rate` | déjà vu #11 | 160 MB/s |
| 70 | `follower.replication.throttled.rate` | #12 | 160 MB/s |
| 71 | `socket.send.buffer.bytes` | `max(65536, bande_Mbps * 1024 * 1024 / (8 * latence_ms))` | 1 Gbps, latence 10 ms → 1,3 MB → 1 048 576 |
| 72 | `socket.receive.buffer.bytes` | idem | 1 048 576 |
| 73 | `socket.request.max.bytes` | `max(100 MB, 10 * fetch.max.bytes)` | fetch.max=50 MB → 500 MB |
| 74 | `connections.max.idle.ms` | `600000` (10 min) | 600000 |
| 75 | `max.connections.per.ip` | `ceil((nb_total_clients) / nb_brokers) * 1.2` | 300 clients, 3 brokers → 120 |

---

## Catégorie 7 : Fichiers et I/O (10 paramètres)

*Introduction : Kafka repose sur le système de fichiers. Ces réglages optimisent les lectures/écritures pour les partitions et leurs réplicas.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 76 | `log.dirs` | `1 répertoire par disque monté` | `/data/kafka0,/data/kafka1` |
| 77 | `log.flush.interval.messages` | `désactivé (Long.MAX_VALUE)` laisser OS gérer | 9223372036854775807 |
| 78 | `log.flush.interval.ms` | `désactivé` | 9223372036854775807 |
| 79 | `log.flush.scheduler.interval.ms` | `Long.MAX_VALUE` | idem |
| 80 | `log.flush.offset.checkpoint.interval.ms` | `60000` (1 min) | 60000 |
| 81 | `log.cleaner.dedupe.buffer.size` | `max(134217728, 0.05 * heap_size)` | heap 4 GB → 200 MB = 209 715 200 |
| 82 | `log.cleaner.io.buffer.size` | `max(524288, log.segment.bytes / 10000)` | 1 GB → 100 KB → 524288 |
| 83 | `log.cleaner.io.buffer.load.factor` | `0.9` | 0.9 |
| 84 | `log.cleaner.threads` | `min(8, nb_disques)` | 4 disques → 4 |
| 85 | `log.cleaner.backoff.ms` | `15000` | 15000 |

---

## Catégorie 8 : Gestion des offsets et transactions (8 paramètres)

*Introduction : Les offsets des consommateurs et les transactions utilisent des topics internes qui doivent être répliqués comme les autres partitions.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 86 | `offsets.topic.num.partitions` | `max(50, nb_brokers * 2)` | 3 brokers → 50 |
| 87 | `offsets.topic.replication.factor` | `min(3, nb_brokers)` | 3 |
| 88 | `offsets.retention.minutes` | `max(10080, 3 * log.retention.hours * 60)` | retention 168h → 10080 min |
| 89 | `offsets.topic.compression.codec` | `0` (no compression) | 0 |
| 90 | `transaction.state.log.num.partitions` | `max(50, nb_brokers * 2)` | 50 |
| 91 | `transaction.state.log.replication.factor` | `min(3, nb_brokers)` | 3 |
| 92 | `transaction.state.log.min.isr` | `min(2, replication.factor)` | 2 |
| 93 | `transaction.abort.timed.out.transaction.cleanup.interval.ms` | `60000` | 60000 |

---

## Catégorie 9 : Monitoring et logging (7 paramètres)

*Introduction : Pour détecter les goulots d’étranglement liés aux partitions ou aux réplicas.*

| # | Paramètre | Règle de calcul | Exemple |
|---|-----------|----------------|---------|
| 94 | `metric.reporters` | `"com.example.MyReporter"` si personnalisé | – |
| 95 | `metrics.num.samples` | `2` | 2 |
| 96 | `metrics.sample.window.ms` | `30000` | 30000 |
| 97 | `log.cleanup.policy` | `"delete"` (ou `"compact"` pour topics clés) | delete |
| 98 | `log.preallocate` | `false` (sauf si disques très lents) | false |
| 99 | `background.threads` | `10` (fixe) | 10 |
| 100 | `queued.max.requests` | `(num.network.threads + num.io.threads) * 2` | 16+16=32 → 64 |

---

# 🧠 Conclusion sur le tuning réplicas vs partitions

- **Réplicas** : Jouez sur `default.replication.factor` et `min.insync.replicas`. La performance n’augmente pas avec plus de réplicas, mais la durabilité oui. Un facteur de réplication de 3 est un standard.
- **Partitions** : Utilisez `num.partitions` et `log.segment.bytes` pour contrôler la croissance. Trop de partitions (> 10 000) dégradent le broker. La règle empirique : **1 partition = 10-20 MB/s de débit soutenable**.

**Formule finale pour dimensionner vos partitions** :  
```
nb_partitions = max( ceil(débit_crête_MB/s / 10), 2 * nb_consumers_prévus )
```

Avec 100 paramètres documentés, vous avez une base exhaustive pour tout réglage avancé sur Kafka. Testez chaque changement en staging avant production.
