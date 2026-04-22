# Guide complet de révision par chapitre – Certification Confluent Developer

## Introduction

La certification **Confluent Certified Developer for Apache Kafka** valide votre capacité à concevoir, développer et dépanner des applications Kafka (producteurs, consommateurs, Kafka Streams, Connect). Elle couvre à la fois les fondamentaux et les fonctionnalités avancées comme l’exactly‑once semantics, les topologies stateful, ou l’intégration avec Confluent Cloud.

Pour réussir, il ne suffit pas de connaître la théorie : il faut **pratiquer chaque chapitre** en écrivant du code, en analysant des configurations et en simulant des pannes. Ce guide détaille les 6 chapitres clés, avec pour chacun :  
- Les notions à maîtriser  
- Les commandes / API à connaître  
- Les exercices pratiques indispensables  
- Les pièges fréquents à l’examen  

---

## Chapitre 1 – Fondamentaux de Kafka

### 🔹 Notions clés
- Rôle d’un **topic** (catégorie logique), d’une **partition** (unité de parallélisme), d’un **broker** (serveur Kafka)
- **Offsets** : identifiant unique d’un message dans une partition
- **ISR** (In‑Sync Replicas) : répliques synchronisées, leader/follower
- **Retention** : basée sur le temps (`log.retention.hours`) ou la taille (`log.retention.bytes`)

### 🔹 Commandes CLI essentielles
```bash
kafka-topics --create --topic test --partitions 3 --replication-factor 2
kafka-topics --describe --topic test
kafka-run-class kafka.tools.GetOffsetShell --topic test --time -1
```

### 🔹 Pratique recommandée
- Créez un topic avec différents nombres de partitions, envoyez des messages et observez la distribution.
- Simulez l’arrêt d’un broker et vérifiez que le leader change (commande `kafka-topics --describe`).

### 🔹 Piège typique à l’examen
- Un topic avec `replication‑factor = 1` ne tolère aucune panne de broker.  
- L’ISR peut être inférieur au facteur de réplication si un follower est en retard.

---

## Chapitre 2 – Producteurs Kafka

### 🔹 Notions clés
- Paramètres de configuration majeurs :  
  - `acks=0 / 1 / all` (garantie de réception)  
  - `compression.type` (gzip, snappy, lz4, zstd)  
  - `batch.size` et `linger.ms` (performance)  
  - `enable.idempotence=true` (exactly‑once du producteur)
- Sérialisation : `StringSerializer`, `JsonSerializer`, `AvroSerializer` (avec Schema Registry)
- Partitionnement personnalisé : implémentation de `Partitioner`

### 🔹 API Java à maîtriser
```java
Properties props = new Properties();
props.put("acks", "all");
props.put("enable.idempotence", "true");
KafkaProducer<String, String> producer = new KafkaProducer<>(props);
producer.send(new ProducerRecord<>("topic", "key", "value"), (metadata, exception) -> {
    // callback
});
```

### 🔹 Exercice pratique
- Envoyez 1 million de messages avec `acks=1` puis `acks=all` – comparez la latence.
- Activez l’idempotence et vérifiez qu’aucun doublon n’apparaît après une coupure réseau simulée.

### 🔹 Piège typique
- `acks=all` n’empêche pas les doublons sans `enable.idempotence=true`.  
- Un producteur qui ne gère pas les callbacks peut perdre des erreurs silencieusement.

---

## Chapitre 3 – Consommateurs Kafka

### 🔹 Notions clés
- **Groupe de consommateurs** : chaque partition est lue par un seul consommateur du groupe.
- **Rééquilibrage** : déclenché quand un consommateur rejoint/quitte le groupe.
- Gestion des offsets :  
  - `auto.offset.reset = earliest / latest / none`  
  - `enable.auto.commit = true/false`  
  - `commitSync()` vs `commitAsync()`
- Stratégies d’assignation : `RangeAssignor`, `RoundRobinAssignor`, `CooperativeStickyAssignor`

### 🔹 Commandes CLI utiles
```bash
kafka-consumer-groups --group monGroupe --describe
kafka-consumer-groups --group monGroupe --reset-offsets --to-earliest --execute
```

### 🔹 Exercice pratique
- Écrivez un consommateur avec commit manuel après traitement.  
- Simulez un traitement long qui dépasse `max.poll.interval.ms` – observez le rééquilibrage.

### 🔹 Piège typique
- Un `auto.commit` tous les 5s peut causer des “at‑least‑once” (messages retraités après une panne).  
- Ne pas gérer `WakeupException` empêche un arrêt propre du consommateur.

---

## Chapitre 4 – Kafka Connect

### 🔹 Notions clés
- **Connecteurs** : Source (import) et Sink (export)
- **Modes** : standalone (un seul processus) vs distribué (plusieurs workers, rebalancement)
- **Tasks** : parallélisme défini par `tasks.max`
- **Single Message Transforms (SMT)** : modification du message à la volée (ex. `InsertField`, `RegexRouter`)
- **Converters** : `JsonConverter`, `AvroConverter`, `StringConverter`

### 🔹 Configuration type (source JDBC)
```json
{
  "name": "jdbc-source",
  "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
  "connection.url": "jdbc:postgresql://localhost/db",
  "mode": "incrementing",
  "incrementing.column.name": "id",
  "topic.prefix": "jdbc-"
}
```

### 🔹 Pratique recommandée
- Déployez un connecteur source FileStream (intégré) et un sink vers S3.
- Ajoutez un SMT pour supprimer un champ avant d’écrire dans le topic.

### 🔹 Piège typique
- Un `tasks.max` trop élevé par rapport au nombre de partitions peut créer des tâches inactives.  
- Un connecteur distribué doit utiliser le même `group.id` sur tous les workers.

---

## Chapitre 5 – Kafka Streams

### 🔹 Notions clés
- **Topologie** : graphe de nœuds de traitement (source → processor → sink)
- **DSL** (Domain Specific Language) : `groupByKey()`, `windowedBy()`, `join()`
- **State stores** : stores persistants (RocksDB) pour les opérations stateful (agrégations, jointures)
- **Windowing** : hopping, tumbling, session, slidding
- **Exactly‑once semantics** avec `processing.guarantee=exactly_once_v2`

### 🔹 API DSL à connaître
```java
KStream<String, String> stream = builder.stream("input");
KTable<Windowed<String>, Long> counts = stream
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
    .count();
```

### 🔹 Exercice pratique
- Écrivez une application qui joint un stream de commandes avec une table d’utilisateurs (`KStream-KTable`).
- Gérez les fenêtres tumbling et écrivez le résultat dans un topic.

### 🔹 Piège typique
- Une opération stateful sans state store (ex. `reduce`) échoue au redémarrage si le store n’est pas configuré.  
- Le rééquilibrage des tâches Streams peut échouer si `num.stream.threads` est trop élevé par rapport aux ressources.

---

## Chapitre 6 – Administration, monitoring et Confluent Cloud

### 🔹 Notions clés
- **Configurations critiques brokers** : `unclean.leader.election.enable`, `min.insync.replicas`
- **Outils Confluent** : Control Center, Confluent CLI, REST Proxy
- **Métriques clés** :  
  - Production : `kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec`  
  - Consommation : `kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*`
- **Confluent Cloud** : clusters serverless, gestion des API keys, quotas, audits logs

### 🔹 Commandes Confluent CLI
```bash
confluent login --save
confluent kafka topic list
confluent kafka consumer-lag get --group monGroupe
```

### 🔹 Pratique recommandée
- Créez un cluster Confluent Cloud (essai gratuit), générez une API key, et connectez un producteur local.
- Utilisez Control Center pour surveiller la latence end‑to‑end.

### 🔹 Piège typique
- Laisser `unclean.leader.election.enable=true` peut entraîner une perte de données.  
- Sur Confluent Cloud, oublier de configurer les ACLs (si pas d’API key) bloque tout accès.

---

## Plan de révision détaillé (4 semaines)

| Semaine | Chapitres | Activités clés |
|---------|-----------|----------------|
| 1 | 1 + 2 | Topics, partitions, producteurs (acks, idempotence, batch) + 2 mini‑projets |
| 2 | 3 | Consommateurs, groupes, commits, rééquilibrage – simulateur de panne |
| 3 | 4 + 5 | Connect (source/sink) + Streams (DSL stateful, windowing) |
| 4 | 6 + examens blancs | Admin, métriques, Confluent Cloud + 3 exams blancs chronométrés |

## Ressources finales

- **Cours officiel gratuit** : [Confluent Developer Skills for Apache Kafka](https://developer.confluent.io/courses/)
- **Examens blancs** : [Practice Exam sur Confluent](https://developer.confluent.io/certification/practice-exam/)
- **Code d’entraînement** : repo GitHub `confluentinc/examples` – volet `clients` et `streams`

> 💡 **Conseil du jour de l’examen** :  
> - Lisez d’abord les questions sur les extraits de code Java (elles sont longues mais très formatives).  
> - Méfiez‑vous des questions pièges sur `auto.offset.reset` vs `auto.commit`.  
> - Sachez identifier rapidement si une situation demande `acks=all` ou `min.insync.replicas=2`.

Bonne préparation, et n’hésitez pas à refaire chaque chapitre plusieurs fois jusqu’à maîtriser les configurations et les cas de panne !
