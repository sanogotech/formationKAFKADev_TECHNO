package com.kafka.lab;

// ============================================================
//  TP02 — Kafka Producer : Envoyer des messages JSON
// ============================================================
//
//  OBJECTIF :
//   Comprendre comment un Producer Kafka envoie des messages.
//   On couvre : synchrone, asynchrone, partitionnement par clé,
//   callbacks de confirmation, gestion des erreurs.
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TP01 terminé (Kafka démarré, topics créés)
//   ✅ Topic "tp01-commandes" existant (3 partitions)
//      Si non : bin/kafka-topics.sh --create --topic tp01-commandes
//               --partitions 3 --replication-factor 1
//               --bootstrap-server localhost:9092
//
//  COMMENT LANCER :
//   > cd tp02-producer
//   > mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.CommandeProducerApp"
//
//  VÉRIFIER LES MESSAGES ENVOYÉS :
//   > bin/kafka-console-consumer.sh --bootstrap-server localhost:9092
//     --topic tp01-commandes --from-beginning --max-messages 20
//
//  RÉSULTAT ATTENDU :
//   Messages JSON dans le topic tp01-commandes, distribués
//   sur les 3 partitions selon la clé (clientId)
// ============================================================

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;

public class CommandeProducerApp {

    private static final Logger log = LoggerFactory.getLogger(CommandeProducerApp.class);
    private static final String TOPIC = "tp01-commandes";

    // Jackson ObjectMapper : convertit nos objets Java en JSON (et vice-versa)
    // Thread-safe : une seule instance suffit
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        log.info("=== TP02 : Démarrage du Producer Kafka ===");

        // ── Étape 1 : Configurer le Producer ────────────────────────────────
        Properties props = buildProducerConfig();

        // ── try-with-resources : le Producer se ferme automatiquement ────────
        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {

            // ── Étape 2 : Envoi SYNCHRONE (plus simple, plus lent) ──────────
            envoyerSynchrone(producer);

            // ── Étape 3 : Envoi ASYNCHRONE avec callback ────────────────────
            envoyerAsynchrone(producer);

            // ── Étape 4 : Envoi avec CLÉS (contrôle du partitionnement) ─────
            envoyerAvecCles(producer);

            // IMPORTANT : flush() attend que TOUS les messages en attente
            // soient confirmés par le broker avant de fermer le producer
            log.info("Attente de la confirmation de tous les messages...");
            producer.flush();

            log.info("=== TP02 : Tous les messages envoyés ! ===");
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  CONFIGURATION DU PRODUCER
    //  Chaque paramètre impacte les performances et la fiabilité
    // ────────────────────────────────────────────────────────────────────────────
    private static Properties buildProducerConfig() {
        Properties props = new Properties();

        // Adresse(s) du/des broker(s) Kafka
        // En prod : "broker1:9092,broker2:9092,broker3:9092"
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");

        // Sérialiseur de la CLÉ : la clé est un String (ex: clientId)
        // La clé détermine dans quelle partition le message est envoyé
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        // Sérialiseur de la VALEUR : la valeur est aussi un String (JSON)
        // En production : on utiliserait AvroSerializer avec Schema Registry
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        // ACKS : garantie de livraison
        // "0" = fire-and-forget (le plus rapide, peut perdre des messages)
        // "1" = confirmation du leader seulement
        // "all" = confirmation de tous les ISR (le plus fiable) ← RECOMMANDÉ
        props.put(ProducerConfig.ACKS_CONFIG, "all");

        // RETRIES : nombre de tentatives en cas d'erreur réseau transitoire
        // 3 retries avec backoff exponentiel
        props.put(ProducerConfig.RETRIES_CONFIG, 3);

        // BATCH_SIZE : taille du batch avant envoi (en bytes)
        // 32768 bytes = 32 KB — bonne valeur par défaut
        // Augmenter pour de meilleures perfs (au détriment de la latence)
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, 32768);

        // LINGER_MS : temps d'attente avant d'envoyer un batch non plein
        // 5ms = légère latence en échange d'un meilleur débit
        // 0ms = latence minimale (envoie immédiatement)
        props.put(ProducerConfig.LINGER_MS_CONFIG, 5);

        // BUFFER_MEMORY : mémoire totale du buffer côté client (32MB)
        props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 33554432);

        // CLIENT_ID : nom du producer pour le monitoring
        props.put(ProducerConfig.CLIENT_ID_CONFIG, "tp02-commande-producer");

        log.debug("Configuration Producer : acks={}, retries={}, linger_ms={}",
                "all", 3, 5);

        return props;
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  ENVOI SYNCHRONE
    //  - send().get() bloque jusqu'à la confirmation du broker
    //  - Garantit que le message est bien reçu avant de continuer
    //  - PLUS LENT : on attend la réponse pour chaque message
    //  - Cas d'usage : quand on doit absolument confirmer chaque envoi
    // ────────────────────────────────────────────────────────────────────────────
    private static void envoyerSynchrone(KafkaProducer<String, String> producer)
            throws Exception {

        log.info("--- Envoi SYNCHRONE ---");

        // Créer une commande de test
        Commande commande = new Commande("alice", "Laptop Pro", 1, 1299.99);

        // Sérialiser l'objet Java en chaîne JSON
        String jsonPayload = mapper.writeValueAsString(commande);

        // ProducerRecord : enveloppe notre message avec topic, clé, valeur
        // La CLÉ "client-alice" détermine la partition (même clé = même partition)
        ProducerRecord<String, String> record = new ProducerRecord<>(
                TOPIC,          // Nom du topic
                "client-alice", // Clé (détermine la partition)
                jsonPayload     // Valeur (le JSON)
        );

        // send() retourne un Future<RecordMetadata>
        // .get() BLOQUE jusqu'à confirmation (timeout par défaut : 60s)
        RecordMetadata metadata = producer.send(record).get();

        // RecordMetadata contient les infos de placement dans le log Kafka
        log.info("✓ [SYNC] Commande {} envoyée → Partition={}, Offset={}, Timestamp={}",
                commande.getId(),
                metadata.partition(),  // Numéro de partition
                metadata.offset(),     // Position dans la partition
                metadata.timestamp()   // Timestamp d'écriture
        );
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  ENVOI ASYNCHRONE avec CALLBACK
    //  - send() retourne immédiatement (non-bloquant)
    //  - Le callback est appelé quand la confirmation arrive
    //  - PLUS RAPIDE : on n'attend pas chaque confirmation
    //  - Cas d'usage : envoi en masse, haute performance
    // ────────────────────────────────────────────────────────────────────────────
    private static void envoyerAsynchrone(KafkaProducer<String, String> producer)
            throws Exception {

        log.info("--- Envoi ASYNCHRONE avec callback ---");

        int nombreMessages = 10;
        // CountDownLatch : synchronisation — attendre que les N callbacks arrivent
        CountDownLatch latch = new CountDownLatch(nombreMessages);
        // AtomicInteger : compteur thread-safe (les callbacks arrivent en parallèle)
        AtomicInteger erreurs = new AtomicInteger(0);

        String[] clients = {"alice", "bob", "charlie", "diana", "edgar"};
        String[] produits = {"Laptop", "Mouse", "Keyboard", "Monitor", "Headset"};

        for (int i = 0; i < nombreMessages; i++) {
            // Rotation des clients et produits
            String client  = clients[i % clients.length];
            String produit = produits[i % produits.length];
            double montant = 29.99 + (i * 50.0);

            Commande commande = new Commande(client, produit, i + 1, montant);
            String json = mapper.writeValueAsString(commande);

            // send() avec un callback Lambda — appelé quand broker répond
            producer.send(
                    new ProducerRecord<>(TOPIC, "client-" + client, json),
                    (metadata, exception) -> {
                        // Ce bloc est appelé de façon ASYNCHRONE (dans un thread I/O)
                        if (exception == null) {
                            // ✓ Succès : message bien reçu par le broker
                            log.info("✓ [ASYNC] {} → P={}, O={}",
                                    commande.getId(), metadata.partition(), metadata.offset());
                        } else {
                            // ✗ Erreur : log et comptage
                            log.error("✗ [ASYNC] Erreur envoi {} : {}",
                                    commande.getId(), exception.getMessage());
                            erreurs.incrementAndGet();
                        }
                        // Décrémenter le compteur pour signaler que ce callback est traité
                        latch.countDown();
                    }
            );
        }

        // Attendre que tous les callbacks soient reçus (max 10 secondes)
        latch.await();

        if (erreurs.get() == 0) {
            log.info("✓ {} messages envoyés avec succès (0 erreur)", nombreMessages);
        } else {
            log.warn("⚠ {} erreurs sur {} messages", erreurs.get(), nombreMessages);
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  ENVOI AVEC CLÉS — Comprendre le partitionnement
    //  La CLÉ détermine dans quelle partition le message va :
    //    partition = hash(clé) % nombrePartitions
    //  → Même clé = même partition = ordre garanti pour ce client
    // ────────────────────────────────────────────────────────────────────────────
    private static void envoyerAvecCles(KafkaProducer<String, String> producer)
            throws Exception {

        log.info("--- Envoi avec CLÉS pour contrôler le partitionnement ---");

        // Envoyer 3 commandes pour le même client "vip-client"
        // → Toutes iront dans la MÊME partition
        // → L'ordre de lecture est garanti pour ce client !
        for (int i = 1; i <= 3; i++) {
            Commande cmd = new Commande("vip-client", "Produit Premium " + i, i, i * 500.0);
            String json = mapper.writeValueAsString(cmd);

            // Clé fixe = même partition pour ce client
            RecordMetadata meta = producer.send(
                    new ProducerRecord<>(TOPIC, "client-vip", json)
            ).get();

            log.info("✓ [KEY] Commande VIP {} → Partition={} (toujours la même!)",
                    cmd.getId(), meta.partition());
        }

        // Vérification : toutes les commandes vip sont dans la même partition
        log.info("INFO : Les 3 commandes vip sont dans la même partition " +
                 "→ ordre de lecture garanti !");

        // ── Envoi SANS clé (null) : round-robin entre partitions ────────────
        log.info("--- Envoi SANS clé (round-robin) ---");
        for (int i = 0; i < 3; i++) {
            Commande cmd = new Commande("anonyme-" + i, "Gadget", 1, 9.99);
            String json = mapper.writeValueAsString(cmd);

            // null comme clé = distribution round-robin entre partitions
            RecordMetadata meta = producer.send(
                    new ProducerRecord<>(TOPIC, null, json)
            ).get();

            log.info("✓ [NO-KEY] Commande {} → Partition={} (variable!)",
                    cmd.getId(), meta.partition());
        }
    }
}
