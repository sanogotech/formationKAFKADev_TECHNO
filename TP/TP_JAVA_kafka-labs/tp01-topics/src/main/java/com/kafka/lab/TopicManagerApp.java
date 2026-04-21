package com.kafka.lab;

// ============================================================
//  TP01 — Gestion des Topics Kafka avec AdminClient Java
// ============================================================
//
//  OBJECTIF : Apprendre à créer, configurer, lister, décrire
//             et supprimer des topics Kafka programmatiquement.
//
//  PRÉREQUIS AVANT CE TP :
//   1. Java 17+ installé  (vérifier : java -version)
//   2. Maven 3.9+ installé (vérifier : mvn -version)
//   3. Kafka 3.9+ démarré en local sur localhost:9092
//      > Démarrage : bin/kafka-server-start.sh config/kraft/server.properties
//   4. Aucune autre configuration nécessaire
//
//  COMMENT LANCER CE TP :
//   > mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.TopicManagerApp"
//
//  RÉSULTAT ATTENDU :
//   - Création de 3 topics avec configs différentes
//   - Listing des topics
//   - Description détaillée (partitions, leaders, ISR)
//   - Modification de configuration (retention)
//   - Suppression d'un topic
// ============================================================

import org.apache.kafka.clients.admin.*;
import org.apache.kafka.common.config.ConfigResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ExecutionException;

public class TopicManagerApp {

    // Logger SLF4J — les messages apparaissent avec timestamp et niveau
    private static final Logger log = LoggerFactory.getLogger(TopicManagerApp.class);

    // Adresse du broker Kafka — localhost:9092 pour un démarrage local
    // En production : "broker1:9092,broker2:9092,broker3:9092"
    private static final String BOOTSTRAP_SERVERS = "localhost:9092";

    public static void main(String[] args) {
        log.info("=== TP01 : Démarrage de la gestion des Topics Kafka ===");

        // ── Étape 1 : Créer la configuration de connexion ───────────────────
        // Properties est la classe Java standard pour les configurations clé/valeur
        Properties adminProps = new Properties();
        adminProps.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP_SERVERS);
        // Timeout de connexion : 10 secondes avant d'abandonner
        adminProps.put(AdminClientConfig.REQUEST_TIMEOUT_MS_CONFIG, "10000");
        // Reconnexion automatique si le broker est temporairement indisponible
        adminProps.put(AdminClientConfig.RECONNECT_BACKOFF_MAX_MS_CONFIG, "5000");

        // ── try-with-resources : AdminClient est AutoCloseable ───────────────
        // Le client se ferme automatiquement à la fin du bloc
        try (AdminClient adminClient = AdminClient.create(adminProps)) {

            log.info("AdminClient connecté à {}", BOOTSTRAP_SERVERS);

            // ── Étape 2 : Créer les topics ───────────────────────────────────
            creerTopics(adminClient);

            // Petite pause pour laisser Kafka propager les métadonnées
            Thread.sleep(1000);

            // ── Étape 3 : Lister tous les topics ────────────────────────────
            listerTopics(adminClient);

            // ── Étape 4 : Décrire les détails des topics ────────────────────
            decrireTopics(adminClient);

            // ── Étape 5 : Modifier la configuration d'un topic ──────────────
            modifierConfiguration(adminClient);

            // ── Étape 6 : Nettoyer (supprimer un topic de test) ─────────────
            supprimerTopic(adminClient, "tp01-test-temporaire");

            log.info("=== TP01 : Terminé avec succès ! ===");

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("TP interrompu !", e);
        } catch (ExecutionException e) {
            // ExecutionException enveloppe les erreurs asynchrones Kafka
            log.error("Erreur Kafka : {}", e.getCause().getMessage());
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  MÉTHODE : Créer plusieurs topics avec des configurations différentes
    // ────────────────────────────────────────────────────────────────────────────
    private static void creerTopics(AdminClient adminClient)
            throws ExecutionException, InterruptedException {

        log.info("--- Création des topics ---");

        // Liste des topics à créer
        List<NewTopic> topicsACreer = new ArrayList<>();

        // ── Topic 1 : Commandes e-commerce ──────────────────────────────────
        // 3 partitions = 3 consumers peuvent lire en parallèle
        // replication-factor=1 = pas de réplication (dev uniquement!)
        // En production : replication-factor >= 3
        NewTopic topicCommandes = new NewTopic("tp01-commandes", 3, (short) 1);
        topicCommandes.configs(Map.of(
                // Conserver les messages 7 jours (en millisecondes)
                "retention.ms", String.valueOf(7 * 24 * 60 * 60 * 1000L),
                // Taille max d'un segment de log : 512 MB
                "segment.bytes", "536870912",
                // Compression SNAPPY : bon ratio compression/CPU
                "compression.type", "snappy"
        ));
        topicsACreer.add(topicCommandes);

        // ── Topic 2 : Events de notification ────────────────────────────────
        // 6 partitions = parallélisme élevé pour les notifications
        NewTopic topicNotifications = new NewTopic("tp01-notifications", 6, (short) 1);
        topicNotifications.configs(Map.of(
                // Rétention courte : 24h (les notifs ne doivent pas s'accumuler)
                "retention.ms", String.valueOf(24 * 60 * 60 * 1000L),
                // Cleanup policy delete : on supprime les vieux messages
                "cleanup.policy", "delete"
        ));
        topicsACreer.add(topicNotifications);

        // ── Topic 3 : Topic temporaire de test ──────────────────────────────
        // 1 seule partition — suffisant pour les tests
        NewTopic topicTest = new NewTopic("tp01-test-temporaire", 1, (short) 1);
        topicsACreer.add(topicTest);

        // ── Envoi de la requête de création ─────────────────────────────────
        // createTopics() est ASYNCHRONE — retourne un CreateTopicsResult
        CreateTopicsResult result = adminClient.createTopics(topicsACreer);

        // .all().get() rend l'appel SYNCHRONE — attend la confirmation de Kafka
        // Lève ExecutionException si un topic existe déjà ou erreur réseau
        result.all().get();

        log.info("✓ Topics créés avec succès : tp01-commandes (3p), tp01-notifications (6p), tp01-test-temporaire (1p)");
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  MÉTHODE : Lister tous les topics du cluster
    // ────────────────────────────────────────────────────────────────────────────
    private static void listerTopics(AdminClient adminClient)
            throws ExecutionException, InterruptedException {

        log.info("--- Liste de tous les topics ---");

        // listTopics() sans options retourne TOUS les topics y compris internes
        // Avec ListTopicsOptions : on peut filtrer les topics internes
        ListTopicsOptions options = new ListTopicsOptions()
                .listInternal(false); // false = on cache les topics __xxx

        Set<String> topics = adminClient.listTopics(options).names().get();

        // Trier alphabétiquement pour un affichage propre
        topics.stream()
                .sorted()
                .forEach(name -> log.info("  📌 Topic : {}", name));

        log.info("✓ Total : {} topics", topics.size());
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  MÉTHODE : Obtenir les détails d'un topic (partitions, leaders, ISR)
    // ────────────────────────────────────────────────────────────────────────────
    private static void decrireTopics(AdminClient adminClient)
            throws ExecutionException, InterruptedException {

        log.info("--- Description des topics TP01 ---");

        List<String> topicsADecrire = List.of("tp01-commandes", "tp01-notifications");

        // describeTopics() retourne une Map<String, TopicDescription>
        Map<String, TopicDescription> descriptions =
                adminClient.describeTopics(topicsADecrire).allTopicNames().get();

        for (Map.Entry<String, TopicDescription> entry : descriptions.entrySet()) {
            String nomTopic = entry.getKey();
            TopicDescription description = entry.getValue();

            log.info("Topic : {} | Interne : {}", nomTopic, description.isInternal());

            // Parcourir chaque partition du topic
            for (TopicPartitionInfo partInfo : description.partitions()) {
                log.info("  Partition {} | Leader : Broker {} | Réplicas : {} | ISR : {}",
                        partInfo.partition(),
                        partInfo.leader().id(),        // Broker qui gère les lectures/écritures
                        partInfo.replicas().size(),    // Nombre total de réplicas
                        partInfo.isr().size()          // In-Sync Replicas : réplicas à jour
                );
                // ISR = In-Sync Replicas : si ISR < replicas, un broker est en retard !
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  MÉTHODE : Modifier la configuration d'un topic existant
    // ────────────────────────────────────────────────────────────────────────────
    private static void modifierConfiguration(AdminClient adminClient)
            throws ExecutionException, InterruptedException {

        log.info("--- Modification de configuration : tp01-commandes ---");

        // ConfigResource identifie la ressource à modifier (TOPIC, BROKER, etc.)
        ConfigResource resource = new ConfigResource(
                ConfigResource.Type.TOPIC,
                "tp01-commandes"
        );

        // AlterConfigOp : opération SET pour modifier une valeur
        // Autres opérations : DELETE (retour valeur défaut), APPEND, SUBTRACT
        Collection<AlterConfigOp> ops = List.of(
                new AlterConfigOp(
                        new ConfigEntry("retention.ms",
                                String.valueOf(3 * 24 * 60 * 60 * 1000L)), // 3 jours
                        AlterConfigOp.OpType.SET
                ),
                new AlterConfigOp(
                        new ConfigEntry("compression.type", "lz4"),
                        AlterConfigOp.OpType.SET
                )
        );

        adminClient.incrementalAlterConfigs(Map.of(resource, ops)).all().get();
        log.info("✓ Configuration mise à jour : retention=3 jours, compression=lz4");
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  MÉTHODE : Supprimer un topic
    // ────────────────────────────────────────────────────────────────────────────
    private static void supprimerTopic(AdminClient adminClient, String nomTopic)
            throws ExecutionException, InterruptedException {

        log.info("--- Suppression du topic : {} ---", nomTopic);

        // deleteTopics() est asynchrone — .all().get() attend la confirmation
        adminClient.deleteTopics(List.of(nomTopic)).all().get();
        log.info("✓ Topic '{}' supprimé", nomTopic);

        // NOTE : la suppression est effective après delete.topic.enable=true
        // dans server.properties (activé par défaut depuis Kafka 2.x)
    }
}
