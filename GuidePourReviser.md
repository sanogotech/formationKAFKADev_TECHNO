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

---

## Observabilité, monitoring et tests – Guide détaillé pour la certification

### Introduction

Une application Kafka fiable ne se limite pas à produire et consommer des messages. Elle doit être **observable** (comprendre son état interne), **monitorée** (collecter des métriques et alertes) et **testée** (valider son comportement en conditions normales et dégradées). La certification Confluent Developer attend que vous maîtrisiez :

- Les **métriques clés** (latence, débit, lag, taux d’erreur)
- Les **outils** (JMX, Control Center, Confluent CLI, REST API)
- Les **stratégies de test** (unitaires, d’intégration, end‑to‑end, with fault injection)

Détaillons chaque pilier.

---

## 1. Observabilité

L’observabilité permet de **diagnostiquer un problème sans avoir à déployer du nouveau code**. Elle repose sur trois piliers : **logs**, **métriques** et **traces**.

### 1.1 Logs structurés

- **Logs Kafka brokers** : situés dans `logs/server.log` (config `log4j.properties`).  
  Niveaux utiles : `INFO` (démarrage/arrêt, élections de leader), `WARN` (répliques en retard), `ERROR` (panne disque, échec réseau).
- **Logs des clients** (producteurs, consommateurs, Streams) : configurable via `org.apache.kafka.clients.producer.ProducerConfig` (ex. `log4j.logger.org.apache.kafka=DEBUG`).
- **Bonnes pratiques** :  
  - Ajouter un `client.id` unique pour tracer chaque instance.  
  - En production, utiliser un niveau `INFO` sauf pour déboguer.  
  - Centraliser les logs (ELK, Splunk) avec un **correlation ID** (ex. `X-Request-Id` dans l’en‑tête du message).

### 1.2 Métriques internes via JMX

Kafka expose **des centaines de métriques JMX** (Java Management Extensions). La certification exige de connaître les plus critiques :

| Composant | MBean ObjectName | Métrique utile |
|-----------|------------------|----------------|
| Broker | `kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec` | Débit entrant (bytes/sec) |
| Broker | `kafka.controller:type=ControllerStats,name=ActiveControllerCount` | 1 si le broker est le contrôleur |
| Producteur | `kafka.producer:type=producer-metrics,client-id=*` | `request-latency-avg`, `outgoing-byte-rate` |
| Consommateur | `kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*` | `records-lag-max` (retard maximum) |
| Kafka Streams | `kafka.streams:type=stream-metrics,client-id=*` | `commit-latency-avg`, `process-ratio` |

**Activation** : Démarrer le broker avec `JMX_PORT=9999` et connecter JConsole, ou utiliser l’API REST JMX.

### 1.3 Tracing distribué (OpenTelemetry)

- Confluent supporte l’injection de **span context** dans les en‑têtes de messages.  
- Pour les applications Streams, on peut activer le tracing avec `spring.cloud.stream.kafka.binder.metrics-collection-enabled` ou via l’agent OpenTelemetry.  
- À savoir pour l’examen : le tracing permet de suivre un message de sa production à sa consommation à travers plusieurs microservices.

### 1.4 Observabilité avec Confluent Cloud

- **Audit logs** : enregistre chaque accès à un topic ou une API key.  
- **Cloud Metrics API** : récupère les métriques au format JSON (latence p99, débit, lag).  
- **Kafka Lag Exporter** : outil open source pour exporter les lags vers Prometheus.

---

## 2. Monitoring

Le monitoring est l’action de **collecter, visualiser et alerter** sur les métriques d’observabilité. La certification se concentre sur les outils natifs Confluent et les métriques à surveiller.

### 2.1 Outils de monitoring officiels

| Outil | Rôle | Utilisation en examen |
|-------|------|----------------------|
| **Control Center** | Interface web (gratuite pour un broker, payante en production) : view topics, consumers, lags, quotas, alerts | Savoir interpréter un graphique de lag, identifier un consommateur mort |
| **Confluent CLI** | Commandes `confluent kafka consumer-lag get --group myGroup` | Vérifier rapidement le lag depuis un terminal |
| **REST Proxy** | Endpoints `/metrics`, `/topics/{topic}/partitions/{partition}/consumers` | Récupérer des métriques par HTTP |
| **JMX Exporter + Prometheus + Grafana** | Solution open source (non spécifique Confluent mais acceptée) | Connaître l’existence pour les environnements sur‑prem |

### 2.2 Métriques à surveiller absolument

Pour l’examen, mémorisez ces **KPI** et leurs seuils critiques :

| Métrique | Seuil d’alerte | Que faire ? |
|----------|----------------|--------------|
| **Consumer lag** | > 10 000 messages ou croissance continue | Augmenter les threads, les partitions, ou optimiser le traitement |
| **Request handler idle ratio** | < 20% (broker saturé) | Ajouter des brokers, revoir la configuration `num.io.threads` |
| **Under‑replicated partitions** | > 0 | Vérifier les brokers morts ou les répliques lentes |
| **Produce request latency (p99)** | > 100 ms | Réduire `batch.size`, augmenter `linger.ms`, ou améliorer le réseau |
| **Active controller count** | ≠ 1 | Un seul broker doit être contrôleur ; sinon, forcer une élection (`kafka.controller.shutdown`) |

### 2.3 Configuration des alertes

Dans Control Center, on peut définir des **alertes** sur :  
- Lag maximum par groupe  
- Délai avant que le rééquilibrage d’un groupe ne se termine  
- Taux d’erreur de production (exceptions dans le callback)

Pour un cluster géré (Confluent Cloud), les alertes se paramètrent dans l’interface web (email, webhook PagerDuty).

### 2.4 Monitoring spécifique Kafka Streams

- **`commit-latency-avg`** : temps moyen pour sauvegarder l’état. Si > 1 s, risque de rebalancement.
- **`active-process-ratio`** : nombre de threads actifs / total. Si faible, sous‑utilisation.
- **`state-store-tasks`** : surveiller que tous les stores sont restaurés après un redémarrage.

---

## 3. Tests

La certification évalue votre capacité à **tester des applications Kafka** à différents niveaux. Les tests sont indispensables pour garantir l’exactly‑once, la tolérance aux pannes et l’évolution des schémas.

### 3.1 Tests unitaires (sans Kafka réel)

**Objectif** : valider la logique métier d’un processor, d’un sérialiseur, ou d’une transformation.

**Outils** : JUnit + Mockito, ou mieux : `org.apache.kafka.streams: kafka-streams-test-utils`.

**Exemple** pour un test unitaire de Streams DSL :

```java
import org.apache.kafka.streams.*;
import org.junit.jupiter.api.Test;

@Test
void testUppercaseStream() {
    StreamsBuilder builder = new StreamsBuilder();
    builder.stream("input").mapValues(v -> v.toString().toUpperCase()).to("output");
    
    try (TopologyTestDriver driver = new TopologyTestDriver(builder.build(), new Properties())) {
        TestInputTopic<String, String> input = driver.createInputTopic("input", new StringSerializer(), new StringSerializer());
        TestOutputTopic<String, String> output = driver.createOutputTopic("output", new StringDeserializer(), new StringDeserializer());
        
        input.pipeInput("key", "hello");
        assertThat(output.readValue()).isEqualTo("HELLO");
    }
}
```

**Ce qu’il faut savoir pour l’examen** :  
- `TopologyTestDriver` simule le temps (windowing, punctuation) sans démarrer de broker.  
- Permet de tester les state stores, les jointures, les fenêtres.

### 3.2 Tests d’intégration (avec un broker embarqué)

**Objectif** : valider l’interaction réelle avec Kafka (sérialisation Avro, commits, reprises après panne).

**Outils** : `kafka-clients` + `kafka-junit` (EmbeddedKafkaCluster de Spring Kafka, ou `kafka-server-start` dans un conteneur Testcontainers).

**Exemple avec Testcontainers** :

```java
@Testcontainers
public class KafkaIntegrationTest {
    @Container
    static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:latest"));
    
    @Test
    void testProducerConsumer() {
        String bootstrap = kafka.getBootstrapServers();
        // créer producteur, envoyer, consommer, assert
    }
}
```

**Points clés pour la certification** :  
- Vérifier le comportement avec `acks=0` vs `acks=all` (perte de messages simulée en tuant le container).  
- Tester le rééquilibrage en ajoutant/supprimant des consommateurs dynamiquement.

### 3.3 Tests end‑to‑end (E2E) avec environnement complet

**Objectif** : valoir l’ensemble du pipeline (source Kafka Connect → Streams → sink).  

**Bonnes pratiques** :  
- Utiliser un environnement de staging identique à la production (même nombre de partitions, même stratégie de sérialisation).  
- Injecter des messages de test avec des **headers** de corrélation.  
- Vérifier que le **lag final** est nul après traitement.

**Outil recommandé** : `kcat` (anciennement `kafkacat`) pour produire/consommer en ligne de commande, combiné avec des scripts bash d’assertion.

### 3.4 Tests de tolérance aux pannes (Fault Injection)

La certification vous demandera comment vous assurer que votre application résiste à :

- **Mort d’un broker** : le producteur avec `acks=all` et `retries > 0` doit continuer.  
- **Rejet d’un message** (sérialisation erronée) : utiliser un **DLQ** (Dead Letter Queue) dans Kafka Streams via `.to("dlq")` dans le gestionnaire d’exceptions.  
- **Lenteur d’un consommateur** : tester le dépassement de `max.poll.interval.ms` (doit déclencher un rééquilibrage).  
- **Perte de l’état RocksDB** : redémarrer une application Streams et vérifier la restauration à partir du changelog topic.

**Exemple de test d’injection** :  
```java
// Avec EmbeddedKafka, tuer un broker artificiellement
kafkaCluster.stopBroker(0);
// Vérifier que le producteur reprend après élection du nouveau leader
```

### 3.5 Tests de schéma (Schema Registry)

- **Compatibilité** : Tester qu’un nouveau schéma Avro est `BACKWARD`, `FORWARD` ou `FULL` compatible.  
- **Évolution** : Vérifier qu’un producteur avec un champ `optional` ne casse pas un consommateur qui attend l’ancien schéma.  
- Utiliser `io.confluent.kafka.schemaregistry.client.rest.RestService` dans les tests.

### 3.6 Intégration dans CI/CD

Pour la certification, sachez que Confluent recommande d’exécuter les tests d’intégration dans un pipeline avec **Testcontainers** (car `EmbeddedKafka` n’est plus maintenu pour les nouvelles versions). Les tests unitaires (TopologyTestDriver) doivent être extrêmement rapides et exécutés à chaque commit.

---

## Tableau récapitulatif pour la certification

| Thème | Outils / Métriques | Ce qu’il faut absolument maîtriser |
|-------|--------------------|--------------------------------------|
| **Observabilité** | JMX, logs structurés, OpenTelemetry | MBeans clés (`BytesInPerSec`, `records-lag-max`), audit logs Confluent Cloud |
| **Monitoring** | Control Center, Confluent CLI, Prometheus | Lire un lag graph, configurer une alerte sur under‑replicated partitions |
| **Tests unitaires** | TopologyTestDriver, JUnit | Simuler une topologie Streams sans broker |
| **Tests intégration** | Testcontainers, EmbeddedKafka | Tester les commits, la reprise après panne broker |
| **Tests end‑to‑end** | kcat, scripts, environnement staging | Vérifier le lag zéro et la transformation correcte |
| **Fault injection** | Arrêt manuel de broker, injection d’exceptions | DLQ, retries, exactly‑once |

---

## Conclusion

Pour réussir la certification **Confluent Developer**, vous devez être capable de :

1. **Observer** : savoir où regarder les logs et les métriques JMX pour diagnostiquer un lag ou une sous‑réplication.  
2. **Monitorer** : utiliser Control Center ou la CLI pour lister les groupes, lire leur lag, et interpréter les alertes.  
3. **Tester** : écrire un test unitaire avec `TopologyTestDriver`, un test d’intégration avec Testcontainers, et simuler la panne d’un broker.

Pratiquez ces trois piliers sur un petit projet (par exemple, un pipeline de transformations avec exactly‑once, puis déployez‑le sur Confluent Cloud et surveillez‑le). Cela vous donnera l’expérience concrète attendue par l’examen.

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
