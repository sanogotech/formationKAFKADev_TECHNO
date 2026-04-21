package com.kafka.lab;

// ============================================================
//  TP04 — Consumer Groups et Rebalancing
// ============================================================
//
//  OBJECTIF :
//   Simuler plusieurs consumers dans un même groupe pour
//   comprendre la distribution des partitions et le rebalancing.
//   On lance 3 consumers dans des threads séparés qui partagent
//   la lecture d'un topic à 6 partitions.
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TP02 et TP03 terminés
//   ✅ Créer le topic 6 partitions :
//      kafka-topics.sh --create --topic tp04-events
//        --partitions 6 --replication-factor 1
//        --bootstrap-server localhost:9092
//
//  COMMENT LANCER :
//   > cd tp04-consumer-groups
//   > mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.MultiConsumerDemo"
//
//  RÉSULTAT ATTENDU :
//   - Consumer 1 : partitions [0, 1]
//   - Consumer 2 : partitions [2, 3]
//   - Consumer 3 : partitions [4, 5]
//   → Charge équilibrée entre les 3 consumers !
// ============================================================

import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class MultiConsumerDemo {

    private static final Logger log = LoggerFactory.getLogger(MultiConsumerDemo.class);
    private static final String TOPIC    = "tp04-events";
    private static final String GROUP_ID = "tp04-consumer-group";
    private static final String BOOTSTRAP = "localhost:9092";

    // Compteur partagé entre tous les consumers
    private static final AtomicInteger totalTraites = new AtomicInteger(0);

    public static void main(String[] args) throws Exception {
        log.info("=== TP04 : Démonstration Consumer Groups ===");
        log.info("Topic: {} | Groupe: {}", TOPIC, GROUP_ID);

        // ── Étape 1 : Produire des messages de test ──────────────────────────
        log.info("--- Production de 60 messages dans {} ---", TOPIC);
        produireMessages(60);
        Thread.sleep(1000); // Laisser Kafka ingérer les messages

        // ── Étape 2 : Lancer 3 consumers EN PARALLÈLE ───────────────────────
        log.info("--- Lancement de 3 consumers dans le groupe '{}' ---", GROUP_ID);

        // ExecutorService pour gérer les threads des consumers
        ExecutorService executor = Executors.newFixedThreadPool(3);
        List<Future<?>> futures = new ArrayList<>();

        for (int i = 1; i <= 3; i++) {
            int consumerId = i;
            Future<?> future = executor.submit(() -> runConsumer(consumerId));
            futures.add(future);

            // Délai entre chaque démarrage pour voir le rebalancing progressif
            Thread.sleep(500);
        }

        // ── Étape 3 : Observer pendant 15 secondes ──────────────────────────
        log.info("--- Observation pendant 15 secondes ---");
        log.info("TIP : Regardez les logs — chaque consumer annonce ses partitions");
        Thread.sleep(15_000);

        // ── Étape 4 : Simuler l'arrêt d'un consumer → rebalancing ! ─────────
        log.info("--- Simulation de panne : Consumer 1 s'arrête ---");
        futures.get(0).cancel(true); // Interrompre le premier consumer
        Thread.sleep(8_000); // Observer le rebalancing (partitions redistribuées)

        // ── Étape 5 : Arrêter tous les consumers ────────────────────────────
        executor.shutdownNow();
        executor.awaitTermination(10, TimeUnit.SECONDS);

        log.info("=== TP04 Terminé. Total messages traités : {} ===", totalTraites.get());
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  UN CONSUMER DANS UN THREAD
    // ────────────────────────────────────────────────────────────────────────────
    private static void runConsumer(int consumerId) {
        log.info("[Consumer-{}] Démarrage dans le groupe '{}'", consumerId, GROUP_ID);

        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, GROUP_ID);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class.getName());
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "true");
        props.put(ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, "1000");

        KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);

        consumer.subscribe(List.of(TOPIC), new ConsumerRebalanceListener() {
            @Override
            public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
                log.info("[Consumer-{}] ⚠ REBALANCE : partitions révoquées = {}",
                        consumerId, partitions.stream()
                                .map(tp -> "P" + tp.partition()).toList());
            }

            @Override
            public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
                // Après rebalancing : afficher les nouvelles partitions
                log.info("[Consumer-{}] ✓ REBALANCE : partitions assignées = {}",
                        consumerId, partitions.stream()
                                .map(tp -> "P" + tp.partition()).toList());
            }
        });

        try {
            while (!Thread.currentThread().isInterrupted()) {
                ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(500));

                if (!records.isEmpty()) {
                    // Afficher par quelle partition ce consumer lit
                    for (TopicPartition partition : records.partitions()) {
                        List<ConsumerRecord<String, String>> partRecords =
                                records.records(partition);

                        log.info("[Consumer-{}] Partition {} → {} messages",
                                consumerId, partition.partition(), partRecords.size());

                        totalTraites.addAndGet(partRecords.size());
                    }
                }
            }
        } catch (Exception e) {
            if (!Thread.currentThread().isInterrupted()) {
                log.error("[Consumer-{}] Erreur : {}", consumerId, e.getMessage());
            }
        } finally {
            consumer.close();
            log.info("[Consumer-{}] Fermé", consumerId);
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  PRODUCER INTERNE pour générer les messages de test
    // ────────────────────────────────────────────────────────────────────────────
    private static void produireMessages(int nombre) throws Exception {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(props)) {
            for (int i = 1; i <= nombre; i++) {
                // Clé différente par message = distribution sur toutes les partitions
                String cle = "event-" + (i % 10);
                String valeur = String.format("{\"eventId\":%d,\"type\":\"ORDER_CREATED\"}", i);
                producer.send(new ProducerRecord<>(TOPIC, cle, valeur));
            }
            producer.flush();
            log.info("✓ {} messages produits dans '{}'", nombre, TOPIC);
        }
    }
}
