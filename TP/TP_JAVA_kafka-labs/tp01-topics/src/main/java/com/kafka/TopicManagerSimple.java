package com.kafka;

// ============================================================
//  TP SIMPLIFIÉ – Gestion des topics Kafka avec AdminClient
//  Version : aucune création / suppression programmatique
// ============================================================
//
//  OBJECTIF : 
//    - Utiliser AdminClient Java pour lister, décrire et 
//      modifier la configuration d'un topic existant.
//    - Les topics doivent être créés manuellement (ligne de commande)
//
//  ✅ PRÉREQUIS AVANT DE LANCER CE PROGRAMME :
//     1. Java 17+ installé  (java -version)
//     2. Maven 3.9+ installé (mvn -version)
//     3. Kafka 3.9+ démarré localement sur localhost:9092
//        → Commande : bin/kafka-server-start.sh config/kraft/server.properties
//     4. CRÉER MANUELLEMENT LES TOPICS (voir commandes ci-dessous)
//
//  ▶️ CRÉATION DES TOPICS (à taper dans un terminal, avant d'exécuter le code) :
//
//     Sous Windows (dans le dossier d'installation de Kafka) :
//        bin\windows\kafka-topics.bat --create --topic tp01-commandes --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --config retention.ms=604800000
//        bin\windows\kafka-topics.bat --create --topic tp01-notifications --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1 --config retention.ms=86400000
//
//     Sous Linux / Mac :
//        bin/kafka-topics.sh --create --topic tp01-commandes --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --config retention.ms=604800000
//        bin/kafka-topics.sh --create --topic tp01-notifications --bootstrap-server localhost:9092 --partitions 2 --replication-factor 1 --config retention.ms=86400000
//
//  ▶️ LANCEMENT DU PROGRAMME JAVA :
//       mvn clean package
//       mvn exec:java -Dexec.mainClass="com.kafka.TopicManagerSimple"
//
//  🧹 APRÈS EXÉCUTION :
//     - Les topics restent sur le cluster (aucune suppression)
//     - Pour les supprimer manuellement :
//         bin/kafka-topics.sh --delete --topic tp01-commandes --bootstrap-server localhost:9092
//         bin/kafka-topics.sh --delete --topic tp01-notifications --bootstrap-server localhost:9092
//
// ============================================================

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
import org.apache.kafka.clients.admin.TopicDescription;
import org.apache.kafka.common.config.ConfigResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TopicManagerSimple {

    private static final Logger log = LoggerFactory.getLogger(TopicManagerSimple.class);
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";

    public static void main(String[] args) {
        log.info("=== TP SIMPLIFIÉ : Gestion des topics Kafka (sans création/suppression) ===");
        log.info("⚠️  Assurez-vous que les topics 'tp01-commandes' et 'tp01-notifications' existent (créés manuellement)");

        // 1. Configuration de connexion à Kafka
        Properties props = new Properties();
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        props.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "10000");

        // 2. Création de l'AdminClient (fermeture automatique)
        try (AdminClient admin = AdminClient.create(props)) {

            log.info("Connecté à {}", BOOTSTRAP_SERVERS);

            // 3. Lister tous les topics (existants)
            listerTopics(admin);

            // 4. Décrire le topic "tp01-commandes"
            decrireTopic(admin, "tp01-commandes");

            // 5. Modifier la rétention du topic "tp01-commandes" (2 jours)
            modifierRetention(admin, "tp01-commandes", 2 * 24 * 60 * 60 * 1000L);

            log.info("=== TP TERMINÉ AVEC SUCCÈS ===");

        } catch (Exception e) {
            log.error("Erreur inattendue : {}", e.getMessage(), e);
        }
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
    // Décrire un topic : nombre de partitions, configuration de rétention
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
    // Modifier la rétention d'un topic (alterConfigs)
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
}