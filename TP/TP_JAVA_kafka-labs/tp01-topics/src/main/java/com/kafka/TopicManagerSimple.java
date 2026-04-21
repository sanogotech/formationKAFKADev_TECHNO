package com.kafka;

// ============================================================
//  TP SIMPLIFIÉ – Gestion des topics Kafka avec AdminClient
// ============================================================
//
//  OBJECTIF : Créer, lister, décrire, modifier et supprimer
//             des topics Kafka via Java.
//
//  ✅ PRÉREQUIS AVANT DE LANCER :
//     1. Java 17+ installé  (java -version)
//     2. Maven 3.9+ installé (mvn -version)
//     3. Kafka 3.9+ démarré localement sur localhost:9092
//        → Commande : bin/kafka-server-start.sh config/kraft/server.properties
//     4. Aucun topic existant nommé "tp01-commandes", "tp01-notifications"
//        (vous pouvez les supprimer avec kafka-topics.sh --delete si besoin)
//
//  ▶️ COMMENT LANCER :
//       mvn clean package
//       mvn exec:java -Dexec.mainClass="com.kafka.lab.TopicManagerSimple"
//
//  🧹 APRÈS EXÉCUTION :
//     - Les topics créés restent dans Kafka (sauf "tp01-test-temporaire" qui est supprimé)
//     - Vous pouvez les réutiliser ou les supprimer manuellement :
//       bin/kafka-topics.sh --delete --topic tp01-commandes --bootstrap-server localhost:9092
//
// ============================================================

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.ExecutionException;

import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.admin.Config;
import org.apache.kafka.clients.admin.ConfigEntry;
import org.apache.kafka.clients.admin.ListTopicsOptions;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.admin.TopicDescription;
import org.apache.kafka.common.config.ConfigResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TopicManagerSimple {

    private static final Logger log = LoggerFactory.getLogger(TopicManagerSimple.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";

    public static void main(String[] args) {
        log.info("=== TP SIMPLIFIÉ : Gestion des topics Kafka ===");

        // 1. Configuration de connexion à Kafka
        Properties props = new Properties();
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "10000"); // timeout 10s

        // 2. Création de l'AdminClient (fermeture automatique avec try-with-resources)
        try (AdminClient admin = AdminClient.create(props)) {

            log.info("Connecté à {}", BOOTSTRAP_SERVERS);

            // 3. Création de 3 topics
            creerTopics(admin);

            // 4. Lister tous les topics
            listerTopics(admin);

            // 5. Décrire un topic spécifique (partitions, configuration)
            decrireTopic(admin, "tp01-commandes");

            // 6. Modifier la rétention d'un topic
            modifierRetention(admin, "tp01-commandes", 2 * 24 * 60 * 60 * 1000L); // 2 jours

            // 7. Supprimer le topic temporaire
            supprimerTopic(admin, "tp01-test-temporaire");

            log.info("=== TP TERMINÉ AVEC SUCCÈS ===");

        } catch (Exception e) {
            log.error("Erreur inattendue : {}", e.getMessage(), e);
        }
    }

    // ------------------------------------------------------------------
    // Création de topics avec configurations simples
    // ------------------------------------------------------------------
    private static void creerTopics(AdminClient admin) throws ExecutionException, InterruptedException {
        log.info("--- Création des topics ---");

        List<NewTopic> topics = new ArrayList<>();

        // Topic 1 : 3 partitions, facteur de réplication 1 (dev)
        NewTopic commandes = new NewTopic("tp01-commandes", 3, (short) 1);
        commandes.configs(Map.of("retention.ms", "604800000")); // 7 jours
        topics.add(commandes);

        // Topic 2 : 2 partitions pour les notifications
        NewTopic notifs = new NewTopic("tp01-notifications", 2, (short) 1);
        notifs.configs(Map.of("retention.ms", "86400000")); // 1 jour
        topics.add(notifs);

        // Topic 3 : temporaire, 1 partition
        NewTopic temp = new NewTopic("tp01-test-temporaire", 1, (short) 1);
        topics.add(temp);

        // Envoi de la requête (attente synchrone)
        admin.createTopics(topics).all().get();

        log.info("✓ Topics créés : commandes(3p), notifications(2p), test-temporaire(1p)");
    }

    // ------------------------------------------------------------------
    // Lister tous les topics (sauf les internes comme __consumer_offsets)
    // ------------------------------------------------------------------
    private static void listerTopics(AdminClient admin) throws ExecutionException, InterruptedException {
        log.info("--- Liste des topics du cluster ---");

        ListTopicsOptions options = new ListTopicsOptions();
        options.listInternal(false); // on cache les topics internes

        Set<String> noms = admin.listTopics(options).names().get();
        noms.stream().sorted().forEach(nom -> log.info("  📌 {}", nom));

        log.info("✓ Total : {} topics", noms.size());
    }

    // ------------------------------------------------------------------
    // Décrire un topic : nombre de partitions, réplicas, configuration
    // (on évite TopicPartitionInfo pour rester simple)
    // ------------------------------------------------------------------
    private static void decrireTopic(AdminClient admin, String topicName)
            throws ExecutionException, InterruptedException {

        log.info("--- Description du topic : {} ---", topicName);

        // Récupération des métadonnées du topic
        TopicDescription description = admin.describeTopics(List.of(topicName))
                .allTopicNames().get().get(topicName);

        log.info("Nom : {}", description.name());
        log.info("Nombre de partitions : {}", description.partitions().size());
        log.info("Interne ? {}", description.isInternal());

        // Récupération des configurations (ex: retention.ms)
        ConfigResource resource = new ConfigResource(ConfigResource.Type.TOPIC, topicName);
        Config config = admin.describeConfigs(List.of(resource)).all().get().get(resource);

        for (ConfigEntry entry : config.entries()) {
            if (entry.name().equals("retention.ms")) {
                long retentionMs = Long.parseLong(entry.value());
                long retentionJours = retentionMs / (24 * 60 * 60 * 1000L);
                log.info("Rétention : {} ms ({} jours)", retentionMs, retentionJours);
            }
        }
    }

    // ------------------------------------------------------------------
    // Modifier la rétention d'un topic (alterConfigs simple)
    // ------------------------------------------------------------------
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

    // ------------------------------------------------------------------
    // Supprimer un topic
    // ------------------------------------------------------------------
    private static void supprimerTopic(AdminClient admin, String topicName)
            throws ExecutionException, InterruptedException {

        log.info("--- Suppression du topic {} ---", topicName);
        admin.deleteTopics(List.of(topicName)).all().get();
        log.info("✓ Topic {} supprimé", topicName);
    }
}