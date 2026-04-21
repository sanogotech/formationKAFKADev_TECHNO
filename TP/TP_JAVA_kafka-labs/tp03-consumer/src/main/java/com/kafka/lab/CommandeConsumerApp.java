package com.kafka.lab;

// ============================================================
//  TP03 — Kafka Consumer : Lire et traiter des messages
// ============================================================
//
//  OBJECTIF :
//   Comprendre le Consumer Kafka : poll loop, offset management,
//   commit synchrone/asynchrone, gestion du rebalancing,
//   lecture depuis le début ou la fin du topic.
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TP02 terminé — des messages existent dans tp01-commandes
//   ✅ Vérifier : kafka-console-consumer.sh --topic tp01-commandes
//                --from-beginning --bootstrap-server localhost:9092
//
//  COMMENT LANCER :
//   Terminal 1 (Producer) :
//   > cd tp02-producer && mvn exec:java -Dexec.mainClass="com.kafka.lab.CommandeProducerApp"
//
//   Terminal 2 (Consumer) :
//   > cd tp03-consumer
//   > mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.CommandeConsumerApp"
//
//   Appuyer sur Ctrl+C pour arrêter le consumer.
//
//  VÉRIFIER LE LAG :
//   > kafka-consumer-groups.sh --bootstrap-server localhost:9092
//     --describe --group tp03-consumer-group
// ============================================================

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.errors.WakeupException;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

public class CommandeConsumerApp {

    private static final Logger log = LoggerFactory.getLogger(CommandeConsumerApp.class);
    private static final String TOPIC    = "tp01-commandes";
    private static final String GROUP_ID = "tp03-consumer-group";
    private static final ObjectMapper mapper = new ObjectMapper();

    // Variable volatile : modifiable depuis le shutdown hook (autre thread)
    private static volatile boolean running = true;

    // Compteurs pour les statistiques
    private static final AtomicLong totalMessages = new AtomicLong(0);
    private static final AtomicLong totalErreurs  = new AtomicLong(0);

    public static void main(String[] args) throws InterruptedException {
        log.info("=== TP03 : Démarrage du Consumer Kafka (groupe: {}) ===", GROUP_ID);

        // ── Configuration du Consumer ────────────────────────────────────────
        Properties props = buildConsumerConfig();

        KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);

        // ── Shutdown Hook : arrêt propre avec Ctrl+C ─────────────────────────
        // Quand l'utilisateur appuie sur Ctrl+C, la JVM appelle ce thread
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            log.info("Ctrl+C détecté — arrêt propre en cours...");
            running = false;
            // consumer.wakeup() interrompt le poll() en cours
            // et déclenche une WakeupException
            consumer.wakeup();
        }));

        try {
            // ── S'abonner au topic ───────────────────────────────────────────
            // subscribe() avec ConsumerRebalanceListener pour gérer le rebalancing
            consumer.subscribe(
                    List.of(TOPIC),
                    new ConsumerRebalanceListener() {
                        @Override
                        public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
                            // Appelé AVANT le rebalancing — committer les offsets en attente !
                            log.info("⚠ REBALANCE : partitions révoquées : {}", partitions);
                            // Commit synchrone pour ne pas reperdre des messages
                            consumer.commitSync();
                        }

                        @Override
                        public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
                            // Appelé APRÈS le rebalancing — nouvelles partitions disponibles
                            log.info("✓ REBALANCE : partitions assignées : {}", partitions);
                        }
                    }
            );

            log.info("Consumer abonné au topic '{}' — en attente de messages...", TOPIC);
            log.info("TIP : Lancez le Producer dans un autre terminal pour voir les messages arriver !");

            // ── POLL LOOP : boucle principale du consumer ────────────────────
            // C'est le cœur du consumer Kafka — toujours une boucle poll()
            while (running) {
                // poll(duration) : attend des messages pendant max 1 seconde
                // Si aucun message en 1s, retourne une collection vide
                // NE PAS mettre un timeout trop long (session.timeout.ms)
                ConsumerRecords<String, String> records =
                        consumer.poll(Duration.ofMillis(1000));

                if (records.isEmpty()) {
                    // Pas de message — normal, on continue la boucle
                    continue;
                }

                log.info("Batch reçu : {} messages", records.count());

                // Traiter chaque message du batch
                for (ConsumerRecord<String, String> record : records) {
                    traiterMessage(record);
                }

                // ── Commit des offsets ───────────────────────────────────────
                // commitSync() : BLOQUE jusqu'à confirmation Kafka
                // ⚠ APPELER APRÈS avoir traité TOUS les messages du batch
                // Si on commit AVANT le traitement → at-most-once (on peut perdre)
                // Si on commit APRÈS → at-least-once (on peut retraiter si crash)
                consumer.commitSync();
                log.debug("Offsets committés pour {} messages", records.count());
            }

        } catch (WakeupException e) {
            // Normal : déclenché par consumer.wakeup() dans le shutdown hook
            log.info("Consumer réveillé (WakeupException) — arrêt normal");
        } catch (Exception e) {
            log.error("Erreur inattendue dans le consumer : {}", e.getMessage(), e);
        } finally {
            // Fermer proprement le consumer
            // close() committe automatiquement les offsets non committés
            consumer.close();
            log.info("=== Consumer fermé. Stats : {} messages traités, {} erreurs ===",
                    totalMessages.get(), totalErreurs.get());
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  TRAITEMENT D'UN MESSAGE
    // ────────────────────────────────────────────────────────────────────────────
    private static void traiterMessage(ConsumerRecord<String, String> record) {
        try {
            // Infos Kafka du message : partition, offset, clé, timestamp
            log.debug("→ Message : partition={}, offset={}, key={}",
                    record.partition(), record.offset(), record.key());

            // Désérialiser le JSON en objet Commande
            Commande commande = mapper.readValue(record.value(), Commande.class);

            // Traitement métier simulé
            log.info("📦 Commande traitée : {} | Client: {} | Produit: {} | Montant: {}€",
                    commande.getId(),
                    commande.getClient(),
                    commande.getProduit(),
                    commande.getMontant());

            // Simuler un traitement (validation, enrichissement, etc.)
            if (commande.getMontant() > 1000) {
                log.info("  ⭐ Commande VIP détectée (montant > 1000€) — traitement prioritaire");
            }

            totalMessages.incrementAndGet();

        } catch (Exception e) {
            // Ne pas faire planter le consumer pour un message mal formé
            // En production : envoyer vers une Dead Letter Queue (DLQ)
            log.error("✗ Erreur traitement message offset={} : {}",
                    record.offset(), e.getMessage());
            totalErreurs.incrementAndGet();
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  CONFIGURATION DU CONSUMER
    // ────────────────────────────────────────────────────────────────────────────
    private static Properties buildConsumerConfig() {
        Properties props = new Properties();

        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");

        // GROUP_ID : identifie le groupe de consumers
        // Kafka distribue les partitions entre tous les consumers du même groupe
        // Deux consumers dans le même groupe = charge partagée
        // Deux consumers dans des groupes différents = lecture indépendante
        props.put(ConsumerConfig.GROUP_ID_CONFIG, GROUP_ID);

        // Désérialiseurs : inverse des sérialiseurs du Producer
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());

        // AUTO_OFFSET_RESET : que faire quand il n'y a pas d'offset committés ?
        // "earliest" = lire depuis le DÉBUT du topic (utile pour les TPs)
        // "latest"   = lire seulement les NOUVEAUX messages (usage production)
        // "none"     = lever une exception si pas d'offset
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

        // AUTO_COMMIT = false : on gère les commits manuellement
        // Si true : Kafka committe automatiquement toutes les 5s
        // ⚠ Auto-commit peut causer des pertes si le consumer crashe entre 2 commits
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");

        // MAX_POLL_RECORDS : nombre max de messages par poll()
        // Défaut : 500 — réduire si le traitement par message est long
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, "50");

        // SESSION_TIMEOUT_MS : si le consumer ne poll() pas dans ce délai
        // → Kafka considère le consumer mort → rebalancing
        props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, "30000");

        // MAX_POLL_INTERVAL_MS : temps max entre deux poll() (traitement)
        // Si le traitement prend plus de 5 min → consumer exclu du groupe
        props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, "300000");

        return props;
    }
}
