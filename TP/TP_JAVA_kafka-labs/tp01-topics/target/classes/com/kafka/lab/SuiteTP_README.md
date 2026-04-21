# Suite logique : 5 TP Kafka après la gestion des topics

Ce premier TP vous a permis de maîtriser l’administration des topics (création, listing, description, modification, suppression) avec `AdminClient`.  
Voici **5 travaux pratiques** qui prolongent logiquement vos compétences, en abordant la production, la consommation, l’administration avancée, le traitement de flux et la résilience.

---

## TP02 – Producteur Kafka (Producer) en Java

**Objectif** : Écrire un producteur Java capable d’envoyer des messages vers un topic créé précédemment (ex. `tp01-commandes`).  
**Concepts clés** :  
- Configuration du producteur (`bootstrap.servers`, `key.serializer`, `value.serializer`)  
- Envoi synchrone vs asynchrone (callback)  
- Gestion des accusés de réception (`acks=0,1,all`)  
- Compression (snappy, lz4)  
- Routage des messages par clé (partitionnement)

**Prérequis** : Kafka démarré, topics `tp01-commandes` (3 partitions) existant.

**Étapes typiques** :  
1. Créer une classe `CommandeProducer` avec `KafkaProducer<String, String>`.  
2. Envoyer 10 messages avec des clés différentes pour observer la répartition sur les partitions.  
3. Implémenter un callback pour gérer les succès/échecs.  
4. Modifier `acks=all` et `min.insync.replicas=1` (si replication>1).  
5. Utiliser la compression `snappy` et mesurer la taille des messages.

**Résultat attendu** : Les messages sont visibles dans les partitions du topic via le consommateur de console ou un consommateur Java.

---

## TP03 – Consommateur Kafka (Consumer) en Java

**Objectif** : Développer un consommateur Java lisant les messages du topic `tp01-commandes` au sein d’un groupe de consommateurs.  
**Concepts clés** :  
- Configuration du consommateur (`group.id`, `auto.offset.reset`, `enable.auto.commit`)  
- Souscription à un ou plusieurs topics  
- Lecture en boucle (`poll`)  
- Commit manuel des offsets (synchrone/asynchrone)  
- Rééquilibrage (rebalance) et gestion des partitions assignées

**Prérequis** : TP02 réalisé (des messages existent dans `tp01-commandes`).

**Étapes typiques** :  
1. Créer une classe `CommandeConsumer` avec `KafkaConsumer<String, String>`.  
2. Lire tous les messages depuis le début (`auto.offset.reset=earliest`).  
3. Passer en commit manuel (`enable.auto.commit=false`) et commiter après traitement.  
4. Lancer deux instances du même consommateur (même `group.id`) et observer la répartition des partitions.  
5. Simuler une panne (arrêter une instance) pour voir le rééquilibrage.

**Résultat attendu** : Les messages sont consommés exactement une fois par groupe, avec reprise sur panne.

---

## TP04 – Administration avancée (Configurations dynamiques, quotas, réassignation)

**Objectif** : Utiliser `AdminClient` pour modifier des configurations au niveau du broker, définir des quotas et réassigner des partitions.  
**Concepts clés** :  
- Modification dynamique de configurations broker/topic (ex. `log.retention.hours`)  
- Gestion des quotas (production, consommation, CPU)  
- Réassignation des réplicas (changer le facteur de réplication)  
- Décrire et supprimer des groupes de consommateurs

**Prérequis** : Avoir un cluster avec au moins 2 brokers (ou utiliser KRaft avec plusieurs nœuds).  
**Étapes typiques** :  
1. Changer la rétention du broker à 2 jours via `AdminClient` (ressource `BROKER`).  
2. Appliquer un quota de production de 1 Mo/s sur un utilisateur (ou client-id).  
3. Ajouter une partition à un topic existant (`createPartitions`).  
4. Réassigner les réplicas d’un topic pour passer de 1 à 3 (si brokers disponibles).  
5. Lire les offsets des groupes de consommateurs (`listConsumerGroupOffsets`).

**Résultat attendu** : Le cluster reflète les nouvelles configurations ; les quotas sont effectifs ; la réassignation s’exécute sans interruption.

---

## TP05 – Kafka Streams : traitement de flux simple

**Objectif** : Construire un topologie Kafka Streams qui lit le topic `tp01-commandes` et produit des résultats agrégés dans un autre topic.  
**Concepts clés** :  
- Topologie (source → transformateur → sink)  
- Sérialisation avec `Serdes`  
- Opérations stateless (`map`, `filter`, `selectKey`)  
- Opérations stateful (comptage par fenêtre, `groupByKey`, `count`)  
- Démarrage/arrêt de l’application Streams

**Prérequis** : Kafka Streams ajouté au `pom.xml` (dépendance `kafka-streams`).  
**Étapes typiques** :  
1. Créer une application qui lit le topic `tp01-commandes`.  
2. Filtrer les commandes d’un certain type (ex. montant > 100).  
3. Grouper par `clientId` et compter le nombre de commandes par minute (fenêtre tumbling).  
4. Écrire le résultat dans un topic `tp01-stats-clients`.  
5. Lancer le consommateur sur le topic de sortie pour vérifier les statistiques.

**Résultat attendu** : Des métriques temps réel sont produites et mises à jour chaque minute.

---

## TP06 – Transactions et exactly-once semantics (EOS)

**Objectif** : Implémenter un producteur transactionnel et un consommateur `read_committed` pour garantir l’exactly-once dans un pipeline de traitement.  
**Concepts clés** :  
- Configuration `transactional.id`  
- Initialisation de la transaction (`initTransactions`)  
- Délimitation `beginTransaction()` / `commitTransaction()` / `abortTransaction()`  
- Consommateur avec `isolation.level=read_committed`  
- Gestion des erreurs et reprise

**Prérequis** : Un topic source, un topic cible.  
**Étapes typiques** :  
1. Créer un producteur transactionnel qui envoie un lot de messages atomiquement.  
2. Provoquer une erreur au milieu du lot et appeler `abortTransaction()`.  
3. Démarrer un consommateur standard (`read_uncommitted`) et un autre `read_committed`.  
4. Constater que les messages du lot avorté ne sont pas vus par le consommateur `read_committed`.  
5. Implémenter une reprise : après crash, le producteur reprend avec le même `transactional.id` et Kafka garantit que les transactions incomplètes sont annulées.

**Résultat attendu** : Aucun message n’est perdu ni dupliqué en cas d’erreur.

---

## Tableau récapitulatif des prérequis techniques

| TP | Nouvelle dépendance Maven | Nouvelle classe Kafka |
|----|---------------------------|----------------------|
| 02 | kafka-clients (déjà) | `KafkaProducer` |
| 03 | kafka-clients | `KafkaConsumer` |
| 04 | kafka-clients (AdminClient) | – (utilise `AdminClient`) |
| 05 | kafka-streams | `KafkaStreams`, `Serdes` |
| 06 | kafka-clients | `KafkaProducer` transactionnel, `KafkaConsumer` avec `read_committed` |

---

# Les  codes complets des TP02 à TP06



---

## 📦 Dépendances Maven (pom.xml) pour tous les TP

```xml
<dependencies>
    <!-- Kafka clients pour Producer, Consumer, AdminClient -->
    <dependency>
        <groupId>org.apache.kafka</groupId>
        <artifactId>kafka-clients</artifactId>
        <version>3.9.0</version>
    </dependency>
    <!-- Kafka Streams pour le TP05 -->
    <dependency>
        <groupId>org.apache.kafka</groupId>
        <artifactId>kafka-streams</artifactId>
        <version>3.9.0</version>
    </dependency>
    <!-- Logging simple -->
    <dependency>
        <groupId>org.slf4j</groupId>
        <artifactId>slf4j-simple</artifactId>
        <version>2.0.16</version>
    </dependency>
</dependencies>
```

---

## TP02 – Producteur Kafka (avec clés, compression, ack=all)

**Fichier :** `CommandeProducer.java`

```java
package com.kafka.lab;

import org.apache.kafka.clients.producer.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;
import java.util.concurrent.ExecutionException;

/**
 * TP02 – Producteur Kafka
 * 
 * Objectifs :
 * - Envoyer des messages vers le topic "tp01-commandes" créé précédemment
 * - Utiliser une clé pour contrôler le partitionnement
 * - Mettre en œuvre la compression snappy et acks=all
 * - Envoi synchrone et asynchrone avec callback
 */
public class CommandeProducer {

    private static final Logger log = LoggerFactory.getLogger(CommandeProducer.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";
    private static final String TOPIC_NAME = "tp01-commandes";

    public static void main(String[] args) {
        log.info("=== TP02 : Producteur Kafka ===");
        log.info("Connexion à {}", BOOTSTRAP_SERVERS);
        log.info("Topic cible : {}", TOPIC_NAME);

        // 1. Configuration du producteur
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringSerializer");
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringSerializer");
        
        // Acks = "all" : attendre que tous les réplicas ISR aient écrit le message
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        // Compression snappy : bon compromis CPU / taille
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "snappy");
        // Taille maximale d'un lot avant envoi (16 Ko)
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, "16384");
        // Temps d'attente maximal pour remplir un lot (10 ms)
        props.put(ProducerConfig.LINGER_MS_CONFIG, "10");

        // 2. Création du producteur (try-with-resources pour fermeture auto)
        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {
            log.info("Producteur créé avec succès");

            // ---- Envoi synchrone (bloquant) ----
            log.info("--- Envoi synchrone de 10 messages ---");
            for (int i = 1; i <= 10; i++) {
                String key = "client_" + (i % 3); // clé : client_0, client_1, client_2
                String value = String.format("Commande n°%d - Montant : %d€ - Produit : article%d",
                        i, i * 100, i);

                ProducerRecord<String, String> record = new ProducerRecord<>(TOPIC_NAME, key, value);

                try {
                    // send().get() rend l'appel synchrone
                    RecordMetadata metadata = producer.send(record).get();
                    log.info("✓ Envoi synchrone réussi : topic={}, partition={}, offset={}, clé={}",
                            metadata.topic(), metadata.partition(), metadata.offset(), key);
                } catch (ExecutionException e) {
                    log.error("✗ Échec envoi synchrone : {}", e.getMessage());
                }
            }

            // ---- Envoi asynchrone avec callback ----
            log.info("--- Envoi asynchrone avec callback ---");
            ProducerRecord<String, String> asyncRecord = new ProducerRecord<>(TOPIC_NAME,
                    "client_async", "Commande asynchrone - Montant : 999€");
            producer.send(asyncRecord, (metadata, exception) -> {
                if (exception == null) {
                    log.info("✓ Envoi asynchrone réussi : partition={}, offset={}",
                            metadata.partition(), metadata.offset());
                } else {
                    log.error("✗ Échec envoi asynchrone : {}", exception.getMessage());
                }
            });

            // Forcer l'envoi de tous les messages en attente
            producer.flush();
            log.info("Tous les messages ont été vidés (flush).");

        } catch (Exception e) {
            log.error("Erreur générale du producteur : {}", e.getMessage(), e);
        }

        log.info("=== TP02 terminé ===");
    }
}
```

**Sortie console attendue (exemple) :**

```
[main] INFO com.kafka.lab.CommandeProducer - === TP02 : Producteur Kafka ===
[main] INFO com.kafka.lab.CommandeProducer - Connexion à localhost:9092
[main] INFO com.kafka.lab.CommandeProducer - Topic cible : tp01-commandes
[main] INFO com.kafka.lab.CommandeProducer - Producteur créé avec succès
[main] INFO com.kafka.lab.CommandeProducer - --- Envoi synchrone de 10 messages ---
[main] INFO com.kafka.lab.CommandeProducer - ✓ Envoi synchrone réussi : topic=tp01-commandes, partition=0, offset=0, clé=client_1
[main] INFO com.kafka.lab.CommandeProducer - ✓ Envoi synchrone réussi : topic=tp01-commandes, partition=1, offset=0, clé=client_2
[main] INFO com.kafka.lab.CommandeProducer - ✓ Envoi synchrone réussi : topic=tp01-commandes, partition=2, offset=0, clé=client_0
...
[main] INFO com.kafka.lab.CommandeProducer - --- Envoi asynchrone avec callback ---
[main] INFO com.kafka.lab.CommandeProducer - ✓ Envoi asynchrone réussi : partition=0, offset=10
[main] INFO com.kafka.lab.CommandeProducer - Tous les messages ont été vidés (flush).
[main] INFO com.kafka.lab.CommandeProducer - === TP02 terminé ===
```

---

## TP03 – Consommateur Kafka (commit manuel, rééquilibrage)

**Fichier :** `CommandeConsumer.java`

```java
package com.kafka.lab;

import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.TopicPartition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Properties;
import java.util.Set;

/**
 * TP03 – Consommateur Kafka
 * 
 * Objectifs :
 * - Lire les messages du topic "tp01-commandes"
 * - Utiliser un groupe de consommateurs pour le parallélisme
 * - Désactiver l'auto-commit et commiter manuellement les offsets
 * - Gérer le rééquilibrage (ConsumerRebalanceListener)
 */
public class CommandeConsumer {

    private static final Logger log = LoggerFactory.getLogger(CommandeConsumer.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";
    private static final String TOPIC_NAME = "tp01-commandes";
    private static final String GROUP_ID = "groupe-commandes-v3";

    public static void main(String[] args) {
        log.info("=== TP03 : Consommateur Kafka (commit manuel) ===");
        log.info("Connexion à {}", BOOTSTRAP_SERVERS);
        log.info("Topic : {}", TOPIC_NAME);
        log.info("Groupe : {}", GROUP_ID);

        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, GROUP_ID);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringDeserializer");
        // Lire depuis le début si aucun offset n'est stocké
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        // Désactiver l'auto-commit (nous commitons manuellement)
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");

        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props)) {
            // Souscription avec listener de rééquilibrage
            consumer.subscribe(List.of(TOPIC_NAME), new ConsumerRebalanceListener() {
                @Override
                public void onPartitionsRevoked(Set<TopicPartition> partitions) {
                    log.warn("⚠️ Partitions révoquées (avant rééquilibrage) : {}", partitions);
                    // Ici on pourrait commiter les offsets avant de perdre les partitions
                }

                @Override
                public void onPartitionsAssigned(Set<TopicPartition> partitions) {
                    log.info("✅ Nouvelles partitions assignées : {}", partitions);
                    // On peut repositionner l'offset si besoin (seek)
                }
            });

            log.info("Consommateur démarré, en attente de messages...");

            int messagesLus = 0;
            // Boucle de consommation (on peut l'arrêter après N messages, ici on tourne 30 secondes)
            long debut = System.currentTimeMillis();
            while (System.currentTimeMillis() - debut < 30_000) { // 30 secondes max
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                if (records.isEmpty()) {
                    log.debug("Aucun message reçu dans ce poll");
                    continue;
                }

                for (ConsumerRecord<String, String> record : records) {
                    log.info("📨 Message reçu : topic={}, partition={}, offset={}, clé={}, valeur={}",
                            record.topic(), record.partition(), record.offset(),
                            record.key(), record.value());
                    messagesLus++;
                }

                // Commit manuel synchrone des offsets
                consumer.commitSync();
                log.info("💾 Commit manuel effectué pour {} messages", records.count());
            }

            log.info("Fin de la période d'écoute. Total messages lus : {}", messagesLus);

        } catch (Exception e) {
            log.error("Erreur du consommateur : {}", e.getMessage(), e);
        }

        log.info("=== TP03 terminé ===");
    }
}
```

**Sortie console :**

```
[main] INFO com.kafka.lab.CommandeConsumer - === TP03 : Consommateur Kafka (commit manuel) ===
[main] INFO com.kafka.lab.CommandeConsumer - Connexion à localhost:9092
[main] INFO com.kafka.lab.CommandeConsumer - Topic : tp01-commandes
[main] INFO com.kafka.lab.CommandeConsumer - Groupe : groupe-commandes-v3
[main] INFO com.kafka.lab.CommandeConsumer - Consommateur démarré, en attente de messages...
[main] INFO com.kafka.lab.CommandeConsumer - ✅ Nouvelles partitions assignées : [tp01-commandes-0, tp01-commandes-1, tp01-commandes-2]
[main] INFO com.kafka.lab.CommandeConsumer - 📨 Message reçu : topic=tp01-commandes, partition=0, offset=0, clé=client_1, valeur=Commande n°1 - Montant : 100€ - Produit : article1
[main] INFO com.kafka.lab.CommandeConsumer - 💾 Commit manuel effectué pour 1 messages
...
[main] INFO com.kafka.lab.CommandeConsumer - Fin de la période d'écoute. Total messages lus : 11
[main] INFO com.kafka.lab.CommandeConsumer - === TP03 terminé ===
```

---

## TP04 – Administration avancée (AdminClient : quotas, partitions, configurations)

**Fichier :** `AdvancedAdminClient.java`

```java
package com.kafka.lab;

import org.apache.kafka.clients.admin.*;
import org.apache.kafka.common.config.ConfigResource;
import org.apache.kafka.common.quota.ClientQuotaAlteration;
import org.apache.kafka.common.quota.ClientQuotaEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ExecutionException;

/**
 * TP04 – Administration avancée avec AdminClient
 * 
 * Objectifs :
 * - Modifier la rétention d'un topic (déjà vu)
 * - Ajouter des partitions à un topic existant
 * - Définir un quota de production sur un client-id
 * - Décrire les configurations d'un broker
 */
public class AdvancedAdminClient {

    private static final Logger log = LoggerFactory.getLogger(AdvancedAdminClient.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";

    public static void main(String[] args) {
        log.info("=== TP04 : Administration avancée Kafka ===");

        Properties props = new Properties();
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "15000");

        try (AdminClient admin = AdminClient.create(props)) {
            log.info("AdminClient connecté à {}", BOOTSTRAP_SERVERS);

            // 1. Modifier la rétention d'un topic existant
            modifierRetentionTopic(admin, "tp01-commandes", 24 * 60 * 60 * 1000L); // 1 jour

            // 2. Ajouter des partitions à un topic (passer de 3 à 5 partitions)
            ajouterPartitions(admin, "tp01-commandes", 5);

            // 3. Définir un quota de production pour un client-id (ex: "mon-producer")
            definirQuotaProduction(admin, "mon-producer", 1024 * 1024L); // 1 Mo/s

            // 4. Lire la configuration actuelle d'un broker (broker 0)
            decrireConfigBroker(admin, 0);

            // 5. Lister les groupes de consommateurs
            listerGroupesConsommateurs(admin);

        } catch (Exception e) {
            log.error("Erreur : {}", e.getMessage(), e);
        }

        log.info("=== TP04 terminé ===");
    }

    private static void modifierRetentionTopic(AdminClient admin, String topic, long retentionMs)
            throws ExecutionException, InterruptedException {
        log.info("--- Modification de la rétention de {} ---", topic);
        ConfigResource resource = new ConfigResource(ConfigResource.Type.TOPIC, topic);
        Map<ConfigResource, Config> configs = new HashMap<>();
        configs.put(resource, new Config(List.of(
                new ConfigEntry("retention.ms", String.valueOf(retentionMs))
        )));
        admin.alterConfigs(configs).all().get();
        long jours = retentionMs / (24 * 60 * 60 * 1000L);
        log.info("✓ Rétention changée à {} jours ({} ms)", jours, retentionMs);
    }

    private static void ajouterPartitions(AdminClient admin, String topic, int newTotalPartitions)
            throws ExecutionException, InterruptedException {
        log.info("--- Augmentation des partitions de {} à {} ---", topic, newTotalPartitions);
        Map<String, NewPartitions> newPartitions = new HashMap<>();
        newPartitions.put(topic, NewPartitions.increaseTo(newTotalPartitions));
        admin.createPartitions(newPartitions).all().get();
        log.info("✓ Nombre de partitions passé à {}", newTotalPartitions);
    }

    private static void definirQuotaProduction(AdminClient admin, String clientId, long bytesPerSecond)
            throws ExecutionException, InterruptedException {
        log.info("--- Définition du quota de production pour client-id '{}' : {} Mo/s ---",
                clientId, bytesPerSecond / (1024 * 1024));
        // L'entité du quota : (client-id -> valeur)
        Map<ClientQuotaEntity.EntityType, String> entity = new HashMap<>();
        entity.put(ClientQuotaEntity.EntityType.CLIENT_ID, clientId);
        ClientQuotaAlteration.Op op = new ClientQuotaAlteration.Op("producer_byte_rate", bytesPerSecond);
        ClientQuotaAlteration alteration = new ClientQuotaAlteration(entity, List.of(op));
        admin.alterClientQuotas(List.of(alteration)).all().get();
        log.info("✓ Quota appliqué avec succès");
    }

    private static void decrireConfigBroker(AdminClient admin, int brokerId)
            throws ExecutionException, InterruptedException {
        log.info("--- Configuration du broker {} ---", brokerId);
        ConfigResource resource = new ConfigResource(ConfigResource.Type.BROKER, String.valueOf(brokerId));
        Config config = admin.describeConfigs(List.of(resource)).all().get().get(resource);
        // Afficher quelques paramètres importants
        for (ConfigEntry entry : config.entries()) {
            String name = entry.name();
            if (name.contains("retention") || name.contains("segment") || name.contains("log")) {
                log.info("  {} = {}", name, entry.value());
            }
        }
    }

    private static void listerGroupesConsommateurs(AdminClient admin)
            throws ExecutionException, InterruptedException {
        log.info("--- Groupes de consommateurs actifs ---");
        ListConsumerGroupsResult result = admin.listConsumerGroups();
        result.all().get().forEach(group -> {
            log.info("  Groupe : {}", group.groupId());
        });
    }
}
```

**Sortie console :**

```
[main] INFO com.kafka.lab.AdvancedAdminClient - === TP04 : Administration avancée Kafka ===
[main] INFO com.kafka.lab.AdvancedAdminClient - AdminClient connecté à localhost:9092
[main] INFO com.kafka.lab.AdvancedAdminClient - --- Modification de la rétention de tp01-commandes ---
[main] INFO com.kafka.lab.AdvancedAdminClient - ✓ Rétention changée à 1 jours (86400000 ms)
[main] INFO com.kafka.lab.AdvancedAdminClient - --- Augmentation des partitions de tp01-commandes à 5 ---
[main] INFO com.kafka.lab.AdvancedAdminClient - ✓ Nombre de partitions passé à 5
[main] INFO com.kafka.lab.AdvancedAdminClient - --- Définition du quota de production pour client-id 'mon-producer' : 1 Mo/s ---
[main] INFO com.kafka.lab.AdvancedAdminClient - ✓ Quota appliqué avec succès
[main] INFO com.kafka.lab.AdvancedAdminClient - --- Configuration du broker 0 ---
[main] INFO com.kafka.lab.AdvancedAdminClient -   log.retention.ms = 172800000
[main] INFO com.kafka.lab.AdvancedAdminClient -   log.segment.bytes = 1073741824
[main] INFO com.kafka.lab.AdvancedAdminClient - --- Groupes de consommateurs actifs ---
[main] INFO com.kafka.lab.AdvancedAdminClient -   Groupe : groupe-commandes-v3
[main] INFO com.kafka.lab.AdvancedAdminClient - === TP04 terminé ===
```

---

## TP05 – Kafka Streams (traitement de flux)

**Fichier :** `CommandeStreamsApp.java`

```java
package com.kafka.lab;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;
import org.apache.kafka.streams.kstream.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.Properties;

/**
 * TP05 – Kafka Streams
 * 
 * Objectifs :
 * - Lire le topic "tp01-commandes"
 * - Filtrer les commandes de montant > 200
 * - Grouper par clé (client) et compter le nombre de commandes par fenêtre de 1 minute
 * - Écrire les résultats dans un topic de sortie "tp01-stats-clients"
 */
public class CommandeStreamsApp {

    private static final Logger log = LoggerFactory.getLogger(CommandeStreamsApp.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";
    private static final String INPUT_TOPIC = "tp01-commandes";
    private static final String OUTPUT_TOPIC = "tp01-stats-clients";

    public static void main(String[] args) {
        log.info("=== TP05 : Kafka Streams - Topologie de traitement ===");

        // 1. Configuration de Kafka Streams
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "streams-commandes-stats");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        // Délai de traitement
        props.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, 1000);

        // 2. Construire la topologie
        StreamsBuilder builder = new StreamsBuilder();

        // Source : lire le topic d'entrée
        KStream<String, String> commandes = builder.stream(INPUT_TOPIC);

        // 3. Filtrer : garder seulement les commandes avec montant > 200€
        // On suppose que la valeur contient "Montant : X€", on extrait X
        KStream<String, String> commandesFiltrees = commandes.filter(
                (key, value) -> {
                    int montant = extraireMontant(value);
                    boolean ok = montant > 200;
                    if (ok) {
                        log.debug("Commande acceptée : key={}, montant={}", key, montant);
                    }
                    return ok;
                }
        );

        // 4. Transformer la valeur pour ne garder que le montant (optionnel)
        KStream<String, Integer> montantsParClient = commandesFiltrees.mapValues(
                value -> extraireMontant(value)
        );

        // 5. Regrouper par clé (client) et compter par fenêtre tumbling de 1 minute
        KGroupedStream<String, Integer> grouped = montantsParClient.groupByKey();
        TimeWindowedKStream<String, Integer> windowed = grouped.windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(1)));
        KTable<Windowed<String>, Long> nombreParClientParMinute = windowed.count();

        // 6. Convertir en KStream pour écrire dans le topic de sortie (avec clé et valeur lisibles)
        KStream<String, String> resultStream = nombreParClientParMinute.toStream()
                .map((windowedKey, count) -> {
                    String client = windowedKey.key();
                    String outputValue = String.format("Client %s : %d commandes entre %s et %s",
                            client, count, windowedKey.window().start(), windowedKey.window().end());
                    return KeyValue.pair(client, outputValue);
                });

        // 7. Écrire dans le topic de sortie
        resultStream.to(OUTPUT_TOPIC, Produced.with(Serdes.String(), Serdes.String()));

        // 8. Lancer l'application
        Topology topology = builder.build();
        log.info("Topologie construite :\n{}", topology.describe());

        try (KafkaStreams streams = new KafkaStreams(topology, props)) {
            streams.start();
            log.info("Application Streams démarrée. En attente de messages...");
            // Laisser tourner 60 secondes
            Thread.sleep(60_000);
            streams.close();
            log.info("Application arrêtée.");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        log.info("=== TP05 terminé ===");
    }

    /**
     * Extrait le montant d'une chaîne comme "Commande n°1 - Montant : 100€ - Produit : article1"
     * @return le montant entier, ou 0 si non trouvé
     */
    private static int extraireMontant(String message) {
        try {
            String[] parts = message.split("Montant : ");
            if (parts.length < 2) return 0;
            String montantStr = parts[1].split("€")[0].trim();
            return Integer.parseInt(montantStr);
        } catch (Exception e) {
            return 0;
        }
    }
}
```

**Sortie console :**

```
[main] INFO com.kafka.lab.CommandeStreamsApp - === TP05 : Kafka Streams - Topologie de traitement ===
[main] INFO com.kafka.lab.CommandeStreamsApp - Topologie construite :
Topologies:
   Sub-topology: 0
    Source: KSTREAM-SOURCE-0000000000 (topics: [tp01-commandes])
    ...
[main] INFO com.kafka.lab.CommandeStreamsApp - Application Streams démarrée. En attente de messages...
[main] DEBUG com.kafka.lab.CommandeStreamsApp - Commande acceptée : key=client_0, montant=300
[main] DEBUG com.kafka.lab.CommandeStreamsApp - Commande acceptée : key=client_1, montant=400
...
[main] INFO com.kafka.lab.CommandeStreamsApp - Application arrêtée.
[main] INFO com.kafka.lab.CommandeStreamsApp - === TP05 terminé ===
```

Pour voir les résultats, lancer un consommateur sur `tp01-stats-clients` :

```bash
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic tp01-stats-clients --from-beginning
```

---

## TP06 – Transactions et exactly-once semantics (EOS)

**Fichier :** `TransactionalProducer.java` et `ReadCommittedConsumer.java`

### A. Producteur transactionnel

```java
package com.kafka.lab;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;

/**
 * TP06 – Producteur transactionnel
 * 
 * Objectif : Envoyer un lot de messages de manière atomique (tout ou rien)
 */
public class TransactionalProducer {

    private static final Logger log = LoggerFactory.getLogger(TransactionalProducer.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";
    private static final String TOPIC_NAME = "tp01-commandes";
    private static final String TRANSACTIONAL_ID = "tx-producer-1";

    public static void main(String[] args) {
        log.info("=== TP06 : Producteur transactionnel ===");

        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringSerializer");
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringSerializer");
        // Configuration transactionnelle
        props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, TRANSACTIONAL_ID);
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
        props.put(ProducerConfig.ACKS_CONFIG, "all");

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {
            producer.initTransactions(); // Nécessaire pour les transactions
            log.info("Producteur initialisé avec transactional.id={}", TRANSACTIONAL_ID);

            // Démarrer une transaction
            producer.beginTransaction();
            log.info("Transaction démarrée");

            try {
                // Envoyer 5 messages
                for (int i = 1; i <= 5; i++) {
                    String key = "tx_client_" + i;
                    String value = "Message transactionnel n°" + i;
                    producer.send(new ProducerRecord<>(TOPIC_NAME, key, value));
                    log.info("Message {} envoyé dans la transaction", i);
                    // Simuler une erreur sur le 3ème message pour annuler
                    if (i == 3) {
                        throw new RuntimeException("Erreur simulée au message 3");
                    }
                }
                // Si tout est OK
                producer.commitTransaction();
                log.info("✅ Transaction committée avec succès");
            } catch (Exception e) {
                log.error("❌ Erreur détectée, annulation de la transaction", e);
                producer.abortTransaction();
                log.info("Transaction annulée (abort)");
            }

            producer.flush();
        }

        log.info("=== TP06 producteur terminé ===");
    }
}
```

### B. Consommateur `read_committed`

```java
package com.kafka.lab;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Properties;

/**
 * Consommateur read_committed : ne voit que les messages des transactions committées
 */
public class ReadCommittedConsumer {

    private static final Logger log = LoggerFactory.getLogger(ReadCommittedConsumer.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";
    private static final String TOPIC_NAME = "tp01-commandes";
    private static final String GROUP_ID = "read-committed-group";

    public static void main(String[] args) {
        log.info("=== TP06 : Consommateur read_committed ===");

        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, GROUP_ID);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
                "org.apache.kafka.common.serialization.StringDeserializer");
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "true");
        // Isolation level = read_committed : ignore les messages non committés
        props.put(ConsumerConfig.ISOLATION_LEVEL_CONFIG, "read_committed");

        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props)) {
            consumer.subscribe(List.of(TOPIC_NAME));
            log.info("Consommateur read_committed démarré");

            // Lire pendant 10 secondes
            long end = System.currentTimeMillis() + 10000;
            while (System.currentTimeMillis() < end) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                records.forEach(record -> {
                    log.info("Message validé : offset={}, key={}, value={}",
                            record.offset(), record.key(), record.value());
                });
            }
        }

        log.info("=== TP06 consommateur terminé ===");
    }
}
```

**Exécution :** Lancer d'abord le producteur transactionnel (il va planter et annuler la transaction), puis le consommateur `read_committed`. Les messages du lot annulé ne doivent pas apparaître.

**Sortie du producteur :**

```
[main] INFO com.kafka.lab.TransactionalProducer - === TP06 : Producteur transactionnel ===
[main] INFO com.kafka.lab.TransactionalProducer - Producteur initialisé avec transactional.id=tx-producer-1
[main] INFO com.kafka.lab.TransactionalProducer - Transaction démarrée
[main] INFO com.kafka.lab.TransactionalProducer - Message 1 envoyé dans la transaction
[main] INFO com.kafka.lab.TransactionalProducer - Message 2 envoyé dans la transaction
[main] INFO com.kafka.lab.TransactionalProducer - Message 3 envoyé dans la transaction
[main] ERROR com.kafka.lab.TransactionalProducer - ❌ Erreur détectée, annulation de la transaction
java.lang.RuntimeException: Erreur simulée au message 3
...
[main] INFO com.kafka.lab.TransactionalProducer - Transaction annulée (abort)
```

**Sortie du consommateur read_committed :**  
Aucun message n’est affiché (ou seulement ceux des transactions antérieures committées).  
Si on lance un consommateur standard (`isolation.level=read_uncommitted`), il verrait les messages 1 et 2 (même si la transaction a été annulée !) – d’où l’intérêt de `read_committed`.

---

## Récapitulatif des commandes d'exécution

| TP | Classe principale | Commande Maven |
|----|------------------|----------------|
| 02 | `CommandeProducer` | `mvn exec:java -Dexec.mainClass="com.kafka.lab.CommandeProducer"` |
| 03 | `CommandeConsumer` | `mvn exec:java -Dexec.mainClass="com.kafka.lab.CommandeConsumer"` |
| 04 | `AdvancedAdminClient` | `mvn exec:java -Dexec.mainClass="com.kafka.lab.AdvancedAdminClient"` |
| 05 | `CommandeStreamsApp` | `mvn exec:java -Dexec.mainClass="com.kafka.lab.CommandeStreamsApp"` |
| 06 | `TransactionalProducer` puis `ReadCommittedConsumer` | `mvn exec:java -Dexec.mainClass="com.kafka.lab.TransactionalProducer"` <br> `mvn exec:java -Dexec.mainClass="com.kafka.lab.ReadCommittedConsumer"` |

**Remarque :** Pour le TP06, le producteur va échouer volontairement. Relancez-le après avoir corrigé l'erreur (ou commentez la ligne `throw new RuntimeException`) pour voir un commit réussi.

---

Tous ces codes sont prêts à être copiés dans votre projet Maven. Assurez-vous que Kafka est bien démarré sur `localhost:9092` avant chaque exécution. Bonne continuation !

---