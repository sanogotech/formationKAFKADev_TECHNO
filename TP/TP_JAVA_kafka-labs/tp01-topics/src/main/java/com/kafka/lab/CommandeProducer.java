package com.kafka.lab;

import java.util.Properties;
import java.util.concurrent.ExecutionException;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

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