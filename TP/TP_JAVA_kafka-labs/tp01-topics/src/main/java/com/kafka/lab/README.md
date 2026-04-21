# TP Kafka Simplifié : Gestion des Topics avec AdminClient Java

## Introduction détaillée

Ce Travail Pratique a pour objectif de vous familiariser avec l’utilisation de l’API **AdminClient** de Kafka en Java. L’`AdminClient` permet d’effectuer des opérations d’administration sur un cluster Kafka de manière programmatique : création, listing, description, modification et suppression de topics.

Dans ce TP simplifié, nous allons :
- Créer trois topics avec des configurations de base (nombre de partitions, rétention des messages)
- Lister l’ensemble des topics présents sur le cluster (en excluant les topics internes)
- Décrire un topic spécifique pour obtenir ses métadonnées (nombre de partitions, configuration de rétention)
- Modifier la durée de rétention d’un topic existant
- Supprimer un topic temporaire

Ce code est volontairement **allégé** par rapport à une version avancée : pas de gestion fine des réplicas, des ISR ou des leaders. Il est conçu pour des débutants souhaitant comprendre les bases de l’administration Kafka en Java.

### Prérequis avant de commencer

Avant d’exécuter ce code, assurez-vous d’avoir :

1. **Java 17+** installé et configuré (vérifiez avec `java -version`)
2. **Maven 3.9+** installé (vérifiez avec `mvn -version`)
3. **Kafka 3.9+** démarré localement sur `localhost:9092`  
   → Démarrage rapide (mode KRaft) :
   ```bash
   bin/kafka-server-start.sh config/kraft/server.properties
   ```
4. **Aucun topic existant** nommé `tp01-commandes`, `tp01-notifications` ou `tp01-test-temporaire` – s’ils existent, supprimez-les avec :
   ```bash
   bin/kafka-topics.sh --delete --topic nom_du_topic --bootstrap-server localhost:9092
   ```

### Structure Maven minimale

Créez un fichier `pom.xml` à la racine de votre projet avec les dépendances suivantes :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.kafka.lab</groupId>
    <artifactId>kafka-tp-simple</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-clients</artifactId>
            <version>3.9.0</version>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-simple</artifactId>
            <version>2.0.16</version>
        </dependency>
    </dependencies>
</project>
```

### Exécution du TP

Une fois le code ci-dessous enregistré dans `src/main/java/com/kafka/lab/TopicManagerSimple.java` :

```bash
mvn clean package
mvn exec:java -Dexec.mainClass="com.kafka.lab.TopicManagerSimple"
```

---

## Code complet (version simplifiée)

```java
package com.kafka.lab;

import org.apache.kafka.clients.admin.*;
import org.apache.kafka.common.config.ConfigResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ExecutionException;

public class TopicManagerSimple {

    private static final Logger log = LoggerFactory.getLogger(TopicManagerSimple.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";

    public static void main(String[] args) {
        log.info("=== TP SIMPLIFIÉ : Gestion des topics Kafka ===");

        // Configuration de connexion
        Properties props = new Properties();
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "10000");

        try (AdminClient admin = AdminClient.create(props)) {
            log.info("Connecté à {}", BOOTSTRAP_SERVERS);

            creerTopics(admin);
            listerTopics(admin);
            decrireTopic(admin, "tp01-commandes");
            modifierRetention(admin, "tp01-commandes", 2 * 24 * 60 * 60 * 1000L); // 2 jours
            supprimerTopic(admin, "tp01-test-temporaire");

            log.info("=== TP TERMINÉ AVEC SUCCÈS ===");
        } catch (Exception e) {
            log.error("Erreur inattendue : {}", e.getMessage(), e);
        }
    }

    /**
     * Crée trois topics avec des configurations simples.
     */
    private static void creerTopics(AdminClient admin) throws ExecutionException, InterruptedException {
        log.info("--- Création des topics ---");

        List<NewTopic> topics = new ArrayList<>();

        NewTopic commandes = new NewTopic("tp01-commandes", 3, (short) 1);
        commandes.configs(Map.of("retention.ms", "604800000")); // 7 jours
        topics.add(commandes);

        NewTopic notifs = new NewTopic("tp01-notifications", 2, (short) 1);
        notifs.configs(Map.of("retention.ms", "86400000")); // 1 jour
        topics.add(notifs);

        NewTopic temp = new NewTopic("tp01-test-temporaire", 1, (short) 1);
        topics.add(temp);

        admin.createTopics(topics).all().get();
        log.info("✓ Topics créés : commandes(3p), notifications(2p), test-temporaire(1p)");
    }

    /**
     * Liste tous les topics non internes du cluster.
     */
    private static void listerTopics(AdminClient admin) throws ExecutionException, InterruptedException {
        log.info("--- Liste des topics du cluster ---");

        ListTopicsOptions options = new ListTopicsOptions();
        options.listInternal(false);

        Set<String> noms = admin.listTopics(options).names().get();
        noms.stream().sorted().forEach(nom -> log.info("  📌 {}", nom));
        log.info("✓ Total : {} topics", noms.size());
    }

    /**
     * Décrit un topic : nombre de partitions, configuration de rétention.
     */
    private static void decrireTopic(AdminClient admin, String topicName)
            throws ExecutionException, InterruptedException {
        log.info("--- Description du topic : {} ---", topicName);

        TopicDescription description = admin.describeTopics(List.of(topicName))
                .allTopicNames().get().get(topicName);

        log.info("Nom : {}", description.name());
        log.info("Nombre de partitions : {}", description.partitions().size());
        log.info("Interne ? {}", description.isInternal());

        // Récupération de la configuration (ex: retention.ms)
        ConfigResource resource = new ConfigResource(ConfigResource.Type.TOPIC, topicName);
        Config config = admin.describeConfigs(List.of(resource)).all().get().get(resource);

        for (ConfigEntry entry : config.entries()) {
            if (entry.name().equals("retention.ms")) {
                long retentionMs = Long.parseLong(entry.value());
                long jours = retentionMs / (24 * 60 * 60 * 1000L);
                log.info("Rétention : {} ms ({} jours)", retentionMs, jours);
            }
        }
    }

    /**
     * Modifie la durée de rétention d'un topic.
     */
    private static void modifierRetention(AdminClient admin, String topicName, long nouvelleRetentionMs)
            throws ExecutionException, InterruptedException {
        log.info("--- Modification de la rétention de {} ---", topicName);

        ConfigResource resource = new ConfigResource(ConfigResource.Type.TOPIC, topicName);
        Map<ConfigResource, Config> configs = new HashMap<>();
        configs.put(resource, new Config(List.of(
                new ConfigEntry("retention.ms", String.valueOf(nouvelleRetentionMs))
        )));

        admin.alterConfigs(configs).all().get();

        long jours = nouvelleRetentionMs / (24 * 60 * 60 * 1000L);
        log.info("✓ Rétention modifiée : {} jours", jours);
    }

    /**
     * Supprime un topic.
     */
    private static void supprimerTopic(AdminClient admin, String topicName)
            throws ExecutionException, InterruptedException {
        log.info("--- Suppression du topic {} ---", topicName);
        admin.deleteTopics(List.of(topicName)).all().get();
        log.info("✓ Topic {} supprimé", topicName);
    }
}
```

---

## Exemple de sortie console attendue

```
[main] INFO com.kafka.lab.TopicManagerSimple - === TP SIMPLIFIÉ : Gestion des topics Kafka ===
[main] INFO com.kafka.lab.TopicManagerSimple - Connecté à localhost:9092
[main] INFO com.kafka.lab.TopicManagerSimple - --- Création des topics ---
[main] INFO com.kafka.lab.TopicManagerSimple - ✓ Topics créés : commandes(3p), notifications(2p), test-temporaire(1p)
[main] INFO com.kafka.lab.TopicManagerSimple - --- Liste des topics du cluster ---
[main] INFO com.kafka.lab.TopicManagerSimple -   📌 tp01-commandes
[main] INFO com.kafka.lab.TopicManagerSimple -   📌 tp01-notifications
[main] INFO com.kafka.lab.TopicManagerSimple -   📌 tp01-test-temporaire
[main] INFO com.kafka.lab.TopicManagerSimple - ✓ Total : 3 topics
[main] INFO com.kafka.lab.TopicManagerSimple - --- Description du topic : tp01-commandes ---
[main] INFO com.kafka.lab.TopicManagerSimple - Nom : tp01-commandes
[main] INFO com.kafka.lab.TopicManagerSimple - Nombre de partitions : 3
[main] INFO com.kafka.lab.TopicManagerSimple - Interne ? false
[main] INFO com.kafka.lab.TopicManagerSimple - Rétention : 604800000 ms (7 jours)
[main] INFO com.kafka.lab.TopicManagerSimple - --- Modification de la rétention de tp01-commandes ---
[main] INFO com.kafka.lab.TopicManagerSimple - ✓ Rétention modifiée : 2 jours
[main] INFO com.kafka.lab.TopicManagerSimple - --- Suppression du topic tp01-test-temporaire ---
[main] INFO com.kafka.lab.TopicManagerSimple - ✓ Topic tp01-test-temporaire supprimé
[main] INFO com.kafka.lab.TopicManagerSimple - === TP TERMINÉ AVEC SUCCÈS ===
```

---

## Nettoyage après le TP

Les topics `tp01-commandes` et `tp01-notifications` persistent sur le cluster. Pour les supprimer définitivement :

```bash
bin/kafka-topics.sh --delete --topic tp01-commandes --bootstrap-server localhost:9092
bin/kafka-topics.sh --delete --topic tp01-notifications --bootstrap-server localhost:9092
```

---

**Bon TP !** Ce code constitue une base solide pour comprendre l’administration Kafka en Java. Vous pouvez ensuite l’enrichir avec la gestion des réplicas, des configurations avancées ou des opérations asynchrones.