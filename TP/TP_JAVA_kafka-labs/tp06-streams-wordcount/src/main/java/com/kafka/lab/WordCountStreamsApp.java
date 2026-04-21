package com.kafka.lab;

// =================================================================
//  TP06 — Kafka Streams : WordCount en temps réel
// =================================================================
//
//  OBJECTIF :
//    Découvrir l'API Kafka Streams DSL pour transformer des flux de données.
//    Implémentation du classique "WordCount" :
//    compter les occurrences de chaque mot en temps réel.
//
//  ARCHITECTURE DU PIPELINE :
//    topic "streams-input" → [split mots] → [group by mot] → [count]
//    → topic "streams-wordcount-output"
//
//  -----------------------------------------------------------------
//  PRÉREQUIS AVANT DE LANCER CE TP (à vérifier un par un) :
//  -----------------------------------------------------------------
//    ✅ TPs 01-03 terminés (Kafka installé et fonctionnel en local)
//    ✅ Zookeeper et Kafka démarrés :
//         $ zookeeper-server-start.sh config/zookeeper.properties
//         $ kafka-server-start.sh config/server.properties
//    ✅ Création des topics obligatoires :
//         kafka-topics.sh --create --topic streams-input \
//           --partitions 3 --replication-factor 1 \
//           --bootstrap-server localhost:9092
//
//         kafka-topics.sh --create --topic streams-wordcount-output \
//           --partitions 3 --replication-factor 1 \
//           --bootstrap-server localhost:9092
//    ✅ Vérification : kafka-topics.sh --list --bootstrap-server localhost:9092
//
//  -----------------------------------------------------------------
//  COMMENT LANCER L'APPLICATION (3 terminaux) :
//  -----------------------------------------------------------------
//   Terminal 1 – Lancement du Streams WordCount :
//     > cd tp06-streams-wordcount
//     > mvn clean package -q
//     > mvn exec:java -Dexec.mainClass="com.kafka.lab.WordCountStreamsApp"
//
//   Terminal 2 – Production de messages :
//     > kafka-console-producer.sh --topic streams-input \
//         --bootstrap-server localhost:9092
//     Taper par exemple :
//         kafka est une plateforme de streaming kafka est rapide
//
//   Terminal 3 – Consommation des résultats (comptages) :
//     > kafka-console-consumer.sh --topic streams-wordcount-output \
//         --bootstrap-server localhost:9092 --from-beginning \
//         --property print.key=true --property key.separator=" → " \
//         --value-deserializer org.apache.kafka.common.serialization.LongDeserializer
//
//  -----------------------------------------------------------------
//  RÉSULTAT ATTENDU DANS LE CONSOMMATEUR (Terminal 3) :
//  -----------------------------------------------------------------
//    kafka → 2
//    est → 2
//    une → 1
//    plateforme → 1
//    de → 1
//    streaming → 1
//    rapide → 1
//
//  À chaque nouveau message produit, les comptages sont mis à jour
//  et seuls les changements sont envoyés dans le topic de sortie.
// =================================================================

import java.util.Arrays;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;
import org.apache.kafka.streams.kstream.Consumed;
import org.apache.kafka.streams.kstream.Grouped;
import org.apache.kafka.streams.kstream.KGroupedStream;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.KTable;
import org.apache.kafka.streams.kstream.Materialized;
import org.apache.kafka.streams.kstream.Produced;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WordCountStreamsApp {

    private static final Logger log = LoggerFactory.getLogger(WordCountStreamsApp.class);

    // Noms des topics – doivent exister AVANT le lancement
    private static final String INPUT_TOPIC  = "streams-input";
    private static final String OUTPUT_TOPIC = "streams-wordcount-output";

    public static void main(String[] args) {
        log.info("=== TP06 : Démarrage Kafka Streams WordCount ===");

        // ─────────────────────────────────────────────────────────
        // Étape 1 – Configuration des paramètres Kafka Streams
        // ─────────────────────────────────────────────────────────
        Properties config = buildStreamsConfig();

        // ─────────────────────────────────────────────────────────
        // Étape 2 – Construction de la topologie (pipeline)
        // ─────────────────────────────────────────────────────────
        Topology topology = buildTopology();
        log.info("Topologie du pipeline :\n{}", topology.describe());

        // ─────────────────────────────────────────────────────────
        // Étape 3 – Création et lancement de l'application Streams
        // ─────────────────────────────────────────────────────────
        KafkaStreams streams = new KafkaStreams(topology, config);

        // Latch pour attendre l'arrêt propre (Ctrl+C)
        CountDownLatch latch = new CountDownLatch(1);

        // Hook d'arrêt : fermeture propre de Kafka Streams
        Runtime.getRuntime().addShutdownHook(new Thread("streams-shutdown") {
            @Override
            public void run() {
                log.info("Arrêt de Kafka Streams...");
                streams.close();   // attend la fin du traitement
                latch.countDown();
            }
        });

        // --- Gestion robuste des exceptions au niveau des threads internes ---
        // StreamsUncaughtExceptionHandler.handle(Throwable) est appelée quand
        // un thread de traitement lance une exception non rattrapée.
        // On retourne REPLACE_THREAD pour que le thread soit recréé automatiquement.
        streams.setUncaughtExceptionHandler(
            (StreamsUncaughtExceptionHandler) exception -> {
                log.error("Exception non gérée dans un thread de traitement : {}",
                          exception.getMessage(), exception);
                // REPLACE_THREAD : le thread est recréé automatiquement
                return StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.REPLACE_THREAD;
            }
        );

        try {
            streams.start();
            log.info("✓ Kafka Streams démarré !");
            log.info("→ Envoyez des messages dans '{}' et observez '{}'",
                     INPUT_TOPIC, OUTPUT_TOPIC);
            log.info("→ Appuyez sur Ctrl+C pour arrêter");

            latch.await();  // attend l'interruption
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        log.info("=== TP06 : Kafka Streams arrêté proprement ===");
    }

    // -----------------------------------------------------------------
    //  CONSTRUCTION DE LA TOPOLOGIE (le pipeline de traitement)
    //  Chaque étape est détaillée pas à pas.
    // -----------------------------------------------------------------
    public static Topology buildTopology() {
        StreamsBuilder builder = new StreamsBuilder();

        // ------------------- ÉTAPE 1 : SOURCE -------------------------
        // Lecture depuis le topic d'entrée.
        // KStream<String, String> = flux infini de (clé, valeur)
        KStream<String, String> lignesTexte = builder.stream(
                INPUT_TOPIC,
                Consumed.with(Serdes.String(), Serdes.String())
        );

        // ------------------- ÉTAPE 2 : MISE EN MINUSCULES --------------
        // mapValues : transforme chaque valeur (le texte) sans toucher à la clé.
        KStream<String, String> lignesMinuscules = lignesTexte
                .mapValues(valeur -> valeur.toLowerCase());

        // ------------------- ÉTAPE 3 : DÉCOUPAGE EN MOTS (flatMap) -----
        // flatMapValues : une ligne → plusieurs mots (expansion).
        // Attention : "\\W+" découpe sur tout caractère non alphabétique.
        // On filtre ensuite les chaînes vides.
        KStream<String, String> mots = lignesMinuscules
                .flatMapValues(ligne ->
                        Arrays.asList(ligne.split("\\W+"))
                )
                .filter((cle, mot) -> mot != null && !mot.isEmpty());

        // ------------------- ÉTAPE 4 : CHANGEMENT DE CLÉ --------------
        // Pour compter par mot, la clé doit être le mot lui-même.
        // selectKey : redéfinit la clé du flux.
        // ⚠️  Changer la clé provoque un REPARTITIONNEMENT automatique
        //    (les données sont réparties sur les partitions selon la nouvelle clé).
        KStream<String, String> motsAvecCle = mots
                .selectKey((cleAncienne, mot) -> mot);

        // ------------------- ÉTAPE 5 : GROUPEMENT ---------------------
        // groupByKey : regroupe les messages ayant la même clé (le mot).
        KGroupedStream<String, String> motsGroupes = motsAvecCle
                .groupByKey(Grouped.with(Serdes.String(), Serdes.String()));

        // ------------------- ÉTAPE 6 : COMPTAGE (COUNT) ---------------
        // count() retourne une KTable<String, Long> : une table qui s'enrichit
        // à chaque nouvelle occurrence.
        // Materialized.as() : nom du "state store" local (rocksDB) qui garde
        // les compteurs en mémoire persistante.
        KTable<String, Long> nombreOccurrences = motsGroupes
                .count(Materialized.as("compteur-mots"));

        // ------------------- ÉTAPE 7 : SINK (SORTIE) ------------------
        // toStream() convertit la KTable en KStream pour écrire dans un topic.
        // peek() : log de chaque mise à jour (sans modifier le flux).
        // to() : écrit dans le topic de sortie avec sérialiseurs (String, Long).
        nombreOccurrences.toStream()
                .peek((mot, count) ->
                        log.info("📊 '{}' → {} occurrence(s)", mot, count)
                )
                .to(OUTPUT_TOPIC,
                        Produced.with(Serdes.String(), Serdes.Long())
                );

        return builder.build();
    }

    // -----------------------------------------------------------------
    //  CONFIGURATION DE KAFKA STREAMS (paramètres obligatoires)
    // -----------------------------------------------------------------
    private static Properties buildStreamsConfig() {
        Properties config = new Properties();

        // APPLICATION_ID : identifie l'application de façon unique.
        // Il sert de consumer group ID et de préfixe pour les topics internes.
        // ⚠️ Si vous changez cet ID, le comptage reprendra de zéro.
        config.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp06-wordcount-app");

        // Adresse du broker Kafka
        config.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");

        // Sérialiseurs par défaut (ici String pour tout)
        config.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        config.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        // Dossier local où seront stockés les state stores (ex: compteurs).
        // Doit être unique par application.
        config.put(StreamsConfig.STATE_DIR_CONFIG, "/tmp/kafka-streams/tp06");

        // Fréquence de commit de l'état (toutes les 2 secondes)
        config.put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, "2000");

        // Nombre de threads de traitement (1 suffit pour ce TP)
        config.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, "1");

        return config;
    }
}