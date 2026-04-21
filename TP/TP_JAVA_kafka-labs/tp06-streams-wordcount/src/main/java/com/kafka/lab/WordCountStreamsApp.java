package com.kafka.lab;

// ============================================================
//  TP06 — Kafka Streams : WordCount en temps réel
// ============================================================
//
//  OBJECTIF :
//   Découvrir l'API Kafka Streams DSL pour transformer des
//   flux de données. On implémente le classique "WordCount" :
//   compter les occurrences de chaque mot en temps réel.
//
//  ARCHITECTURE DU PIPELINE :
//   topic "streams-input" → [split mots] → [group by mot]
//     → [count] → topic "streams-wordcount-output"
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TPs 01-03 terminés (Kafka en local)
//   ✅ Créer les topics :
//      kafka-topics.sh --create --topic streams-input
//        --partitions 3 --replication-factor 1
//        --bootstrap-server localhost:9092
//
//      kafka-topics.sh --create --topic streams-wordcount-output
//        --partitions 3 --replication-factor 1
//        --bootstrap-server localhost:9092
//
//  COMMENT LANCER :
//   Terminal 1 — Démarrer l'application Streams :
//   > cd tp06-streams-wordcount && mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.WordCountStreamsApp"
//
//   Terminal 2 — Envoyer des messages :
//   > kafka-console-producer.sh --topic streams-input
//     --bootstrap-server localhost:9092
//   Taper : kafka est une plateforme de streaming kafka est rapide
//
//   Terminal 3 — Observer les résultats :
//   > kafka-console-consumer.sh --topic streams-wordcount-output
//     --bootstrap-server localhost:9092 --from-beginning
//     --property print.key=true --property key.separator=" → "
//     --value-deserializer org.apache.kafka.common.serialization.LongDeserializer
//
//  RÉSULTAT ATTENDU :
//   kafka → 2
//   est → 2
//   une → 1
//   plateforme → 1
//   de → 1
//   streaming → 1
//   rapide → 1
// ============================================================

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.kstream.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Arrays;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;

public class WordCountStreamsApp {

    private static final Logger log = LoggerFactory.getLogger(WordCountStreamsApp.class);

    // Noms des topics — doivent exister avant le lancement
    private static final String INPUT_TOPIC  = "streams-input";
    private static final String OUTPUT_TOPIC = "streams-wordcount-output";

    public static void main(String[] args) {
        log.info("=== TP06 : Démarrage Kafka Streams WordCount ===");

        // ── Étape 1 : Configuration Streams ─────────────────────────────────
        Properties config = buildStreamsConfig();

        // ── Étape 2 : Construire la topologie du pipeline ───────────────────
        Topology topology = buildTopology();

        // Afficher la topologie sous forme textuelle (utile pour comprendre)
        log.info("Topologie du pipeline :\n{}", topology.describe());

        // ── Étape 3 : Créer et démarrer l'application Streams ───────────────
        KafkaStreams streams = new KafkaStreams(topology, config);

        // Latch pour attendre l'arrêt (Ctrl+C)
        CountDownLatch latch = new CountDownLatch(1);

        // Shutdown hook : arrêt propre avec Ctrl+C
        Runtime.getRuntime().addShutdownHook(new Thread("streams-shutdown") {
            @Override
            public void run() {
                log.info("Arrêt de Kafka Streams...");
                streams.close();  // Attendre la fin du traitement en cours
                latch.countDown();
            }
        });

        // Gérer les erreurs de démarrage
        streams.setUncaughtExceptionHandler((thread, throwable) -> {
            log.error("Exception non gérée dans le thread {} : {}",
                    thread.getName(), throwable.getMessage(), throwable);
            // En production : relancer l'app ou envoyer une alerte
            return StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.REPLACE_THREAD;
        });

        try {
            // start() lance le traitement en arrière-plan
            streams.start();
            log.info("✓ Kafka Streams démarré !");
            log.info("→ Envoyez des messages dans '{}' et observez '{}'",
                    INPUT_TOPIC, OUTPUT_TOPIC);
            log.info("→ Appuyez sur Ctrl+C pour arrêter");

            // Attendre le signal d'arrêt
            latch.await();

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        log.info("=== TP06 : Kafka Streams arrêté proprement ===");
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  CONSTRUCTION DE LA TOPOLOGIE (le pipeline de traitement)
    //
    //  DSL Kafka Streams = API fonctionnelle, similaire à Java Stream API
    //  Chaque opération retourne un nouveau KStream ou KTable
    // ────────────────────────────────────────────────────────────────────────────
    public static Topology buildTopology() {
        // StreamsBuilder : le constructeur de topologie
        StreamsBuilder builder = new StreamsBuilder();

        // ── Source : lire depuis le topic d'entrée ───────────────────────────
        // KStream = flux infini de paires (clé, valeur)
        // Consumed.with() spécifie les sérialiseurs
        KStream<String, String> lignesTexte = builder.stream(
                INPUT_TOPIC,
                Consumed.with(Serdes.String(), Serdes.String())
        );

        // ── Transformation 1 : mettre en minuscules ──────────────────────────
        KStream<String, String> lignesMinuscules = lignesTexte
                .mapValues(valeur -> valeur.toLowerCase());
        // mapValues() applique une fonction à chaque VALEUR (la clé est conservée)

        // ── Transformation 2 : découper en mots (flatMap) ───────────────────
        // flatMapValues() : 1 ligne → N mots (expand)
        KStream<String, String> mots = lignesMinuscules
                .flatMapValues(ligne ->
                        Arrays.asList(
                                // Split sur espaces et ponctuation
                                ligne.split("\\W+")
                        )
                )
                // Filtrer les mots vides (résultat du split)
                .filter((cle, mot) -> mot != null && !mot.isEmpty());

        // ── Transformation 3 : changer la clé = le mot lui-même ─────────────
        // selectKey() : redéfinir la clé du stream
        // IMPORTANT : changer la clé = repartitionnement automatique !
        // Les messages sont redistribués selon la nouvelle clé
        KStream<String, String> motsAvecCle = mots
                .selectKey((cleAncienne, mot) -> mot);

        // ── Transformation 4 : grouper par mot (la nouvelle clé) ────────────
        // groupByKey() : agréger les messages avec la même clé
        KGroupedStream<String, String> motsGroupes = motsAvecCle
                .groupByKey(Grouped.with(Serdes.String(), Serdes.String()));

        // ── Transformation 5 : COUNT — compter les occurrences ──────────────
        // count() retourne une KTable<String, Long> (mot → nombre d'occurrences)
        // KTable = table de résultats mise à jour incrementalement
        // Materialized.as() : nommer le state store (optionnel mais utile)
        KTable<String, Long> nombreOccurrences = motsGroupes
                .count(Materialized.as("compteur-mots"));

        // ── Sink : écrire les résultats dans le topic de sortie ─────────────
        // toStream() : convertir KTable en KStream pour l'écriture
        nombreOccurrences.toStream()
                .peek((mot, count) ->
                        // peek() : observer sans modifier (pour les logs)
                        log.info("📊 '{}' → {} occurrences", mot, count)
                )
                .to(OUTPUT_TOPIC,
                        // Produced.with() : Long pour les valeurs (nombres)
                        Produced.with(Serdes.String(), Serdes.Long())
                );

        return builder.build();
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  CONFIGURATION KAFKA STREAMS
    // ────────────────────────────────────────────────────────────────────────────
    private static Properties buildStreamsConfig() {
        Properties config = new Properties();

        // APPLICATION_ID : identifiant unique de l'application Streams
        // Utilisé comme consumer group ID et préfixe des topics internes
        // ⚠ Changer cet ID repart depuis le début (nouveaux offsets)
        config.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp06-wordcount-app");

        config.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");

        // Serdes par défaut : String pour les clés ET les valeurs
        config.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        config.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        // Dossier local pour les state stores (KTable, agrégations)
        // Chaque application Streams doit avoir un dossier unique
        config.put(StreamsConfig.STATE_DIR_CONFIG, "/tmp/kafka-streams/tp06");

        // COMMIT_INTERVAL : fréquence de sauvegarde de l'état (toutes les 2s)
        config.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, "2000");

        // Nombre de threads de traitement (1 par défaut, peut être augmenté)
        config.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, "1");

        return config;
    }
}
