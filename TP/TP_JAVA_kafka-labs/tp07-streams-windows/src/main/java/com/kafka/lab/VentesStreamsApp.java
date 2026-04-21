package com.kafka.lab;

// ============================================================
//  TP07 — Kafka Streams : Fenêtres Temporelles & KTable Joins
// ============================================================
//
//  OBJECTIF :
//   Maîtriser les opérations avancées de Kafka Streams :
//   - Tumbling Windows   : fenêtres fixes non-chevauchantes
//   - Hopping Windows    : fenêtres glissantes
//   - Session Windows    : fenêtres basées sur l'activité
//   - KStream-KTable Join: enrichissement en temps réel
//
//  SCÉNARIO : Analyse des ventes en temps réel
//   - Compter les ventes par produit toutes les 60 secondes
//   - Enrichir chaque vente avec les infos produit (KTable)
//   - Détecter les pics de ventes sur 5 minutes glissantes
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TP06 terminé (Kafka Streams de base compris)
//   ✅ Topics créés :
//      kafka-topics.sh --create --topic ventes-stream --partitions 3 \
//        --bootstrap-server localhost:9092
//      kafka-topics.sh --create --topic catalogue-table --partitions 1 \
//        --bootstrap-server localhost:9092
//      kafka-topics.sh --create --topic stats-ventes-1min --partitions 3 \
//        --bootstrap-server localhost:9092
//      kafka-topics.sh --create --topic ventes-enrichies --partitions 3 \
//        --bootstrap-server localhost:9092
//
//  COMMENT LANCER :
//   Terminal 1 : mvn exec:java -Dexec.mainClass="com.kafka.lab.VentesStreamsApp"
//   Terminal 2 : kafka-console-producer --topic ventes-stream --bootstrap-server localhost:9092
//                > produit1 {"produit":"LAP-001","montant":1299.99,"qte":1}
//                > produit2 {"produit":"TAB-002","montant":599.99,"qte":2}
//   Terminal 3 : kafka-console-consumer --topic stats-ventes-1min --bootstrap-server localhost:9092 \
//                --property print.key=true --property value.deserializer=org.apache.kafka.common.serialization.StringDeserializer
// ============================================================

import java.time.Duration;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;
import org.apache.kafka.streams.errors.StreamsUncaughtExceptionHandler;
import org.apache.kafka.streams.kstream.Consumed;
import org.apache.kafka.streams.kstream.Grouped;
import org.apache.kafka.streams.kstream.Joined;
import org.apache.kafka.streams.kstream.KStream;
import org.apache.kafka.streams.kstream.KTable;
import org.apache.kafka.streams.kstream.Materialized;
import org.apache.kafka.streams.kstream.Produced;
import org.apache.kafka.streams.kstream.SessionWindows;
import org.apache.kafka.streams.kstream.TimeWindows;
import org.apache.kafka.streams.kstream.Windowed;
import org.apache.kafka.streams.processor.WallclockTimestampExtractor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class VentesStreamsApp {

    private static final Logger log = LoggerFactory.getLogger(VentesStreamsApp.class);

    public static void main(String[] args) {
        log.info("=== TP07 : Kafka Streams — Fenêtres & KTable Joins ===");

        Properties config = buildStreamsConfig();
        Topology topology = buildTopology();
        log.info("Topologie :\n{}", topology.describe());

        // Try-with-resources pour fermeture automatique
        try (KafkaStreams streams = new KafkaStreams(topology, config)) {
            CountDownLatch latch = new CountDownLatch(1);

            // Shutdown hook pour arrêt propre
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                log.info("Arrêt demandé, fermeture de Kafka Streams...");
                streams.close(Duration.ofSeconds(10));
                latch.countDown();
            }));

            // Gestion des exceptions fatales (StreamsUncaughtExceptionHandler)
            streams.setUncaughtExceptionHandler(exception -> {
                log.error("Exception fatale dans Kafka Streams : ", exception);
                // SHUTDOWN_APPLICATION arrête l'application entièrement
                return StreamsUncaughtExceptionHandler.StreamThreadExceptionResponse.SHUTDOWN_APPLICATION;
            });

            streams.start();
            log.info("✓ Streams démarré. Envoyez des ventes dans 'ventes-stream'");
            log.info("  Format attendu : clé=produit-code, valeur={\"produit\":\"LAP-001\",\"montant\":1299.99}");

            latch.await();

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.info("Application interrompue");
        }
        log.info("=== TP07 terminé ===");
    }

    // -----------------------------------------------------------------
    //  CONSTRUCTION DE LA TOPOLOGIE AVEC FENÊTRES ET JOINTURES
    // -----------------------------------------------------------------
    public static Topology buildTopology() {
        StreamsBuilder builder = new StreamsBuilder();

        // ── Source 1 : flux de ventes ─────────────────────────────────────────
        KStream<String, String> ventes = builder.stream("ventes-stream",
                Consumed.with(Serdes.String(), Serdes.String()));

        // ── Source 2 : table catalogue (référentiel produits) ─────────────────
        KTable<String, String> catalogue = builder.table("catalogue-table",
                Consumed.with(Serdes.String(), Serdes.String()),
                Materialized.as("catalogue-store"));

        // ── Transformation 1 : Extraire le montant de chaque vente ───────────
        KStream<String, Double> montants = ventes.mapValues(json -> {
            try {
                // Extraction basique du champ "montant" (JSON simplifié)
                String valStr = json.replaceAll(".*\"montant\"\\s*:\\s*([0-9.]+).*", "$1");
                double montant = Double.parseDouble(valStr);
                log.debug("Vente parsée : {}", montant);
                return montant;
            } catch (NumberFormatException | IllegalStateException e) {
                log.warn("JSON invalide ignoré : {} - {}", json, e.getMessage());
                return 0.0;
            }
        }).filter((cle, montant) -> montant > 0);

        // ── Transformation 2 : TUMBLING WINDOW — stats par minute ────────────
        // Utilisation de Materialized.as() sans spécifier les types génériques
        // (le compilateur les infère automatiquement)
        KTable<Windowed<String>, Double> statsParMinute = montants
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofSeconds(60)))
                .aggregate(
                        () -> 0.0,
                        (produit, montant, total) -> total + montant,
                        Materialized.as("stats-par-minute")
                );

        // Écrire les stats dans le topic de sortie
        statsParMinute.toStream()
                .peek((windowedKey, total) ->
                        log.info("📊 [TUMBLING 1min] {} → {:.2f}€ | Fenêtre: {} → {}",
                                windowedKey.key(), total,
                                windowedKey.window().startTime(), windowedKey.window().endTime())
                )
                .map((windowedKey, total) ->
                        KeyValue.pair(windowedKey.key() + "@" + windowedKey.window().start(),
                                      String.valueOf(total))
                )
                .to("stats-ventes-1min", Produced.with(Serdes.String(), Serdes.String()));

        // ── Transformation 3 : KStream-KTable JOIN — enrichissement ──────────
        KStream<String, String> ventesEnrichies = ventes.join(
                catalogue,
                (ventejson, produitjson) -> {
                    if (produitjson == null) {
                        return ventejson + ",\"categorie\":\"INCONNUE\"";
                    }
                    String merged = ventejson.replace("}", "") + ",\"catalogue\":" + produitjson + "}";
                    log.info("✓ JOIN vente+catalogue : {}", merged);
                    return merged;
                },
                Joined.with(Serdes.String(), Serdes.String(), Serdes.String())
        );

        ventesEnrichies.to("ventes-enrichies", Produced.with(Serdes.String(), Serdes.String()));

        // ── Transformation 4 : SESSION WINDOW — détecter les rafales ─────────
        KTable<Windowed<String>, Long> sessions = montants
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .windowedBy(SessionWindows.ofInactivityGapWithNoGrace(Duration.ofSeconds(30)))
                .count(Materialized.as("sessions-store"));

        sessions.toStream()
                .peek((windowedKey, count) -> {
                    long durationSec = (windowedKey.window().endTime().toEpochMilli() -
                                        windowedKey.window().startTime().toEpochMilli()) / 1000;
                    log.info("🎯 [SESSION] {} → {} ventes en {} secondes",
                            windowedKey.key(), count, durationSec);
                });

        return builder.build();
    }

    // -----------------------------------------------------------------
    //  CONFIGURATION DE KAFKA STREAMS
    // -----------------------------------------------------------------
    private static Properties buildStreamsConfig() {
        Properties config = new Properties();
        config.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp07-ventes-streams");
        config.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        config.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        config.put(StreamsConfig.STATE_DIR_CONFIG, "/tmp/kafka-streams/tp07");
        // Extractor d'horodatage (Wallclock = temps système, à ne pas utiliser en prod)
        config.put(StreamsConfig.DEFAULT_TIMESTAMP_EXTRACTOR_CLASS_CONFIG, WallclockTimestampExtractor.class);
        return config;
    }
}