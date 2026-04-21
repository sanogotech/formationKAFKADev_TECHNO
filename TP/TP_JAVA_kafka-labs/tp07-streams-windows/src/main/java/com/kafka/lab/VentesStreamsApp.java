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
//      kafka-topics.sh --create --topic ventes-stream --partitions 3 ...
//      kafka-topics.sh --create --topic catalogue-table --partitions 1 ...
//      kafka-topics.sh --create --topic stats-ventes-1min --partitions 3 ...
//
//  COMMENT LANCER :
//   Terminal 1 : mvn exec:java -Dexec.mainClass="com.kafka.lab.VentesStreamsApp"
//   Terminal 2 : Envoyer des ventes dans ventes-stream
// ============================================================

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.kstream.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;

public class VentesStreamsApp {

    private static final Logger log = LoggerFactory.getLogger(VentesStreamsApp.class);

    public static void main(String[] args) {
        log.info("=== TP07 : Kafka Streams — Fenêtres & KTable Joins ===");

        Properties config = new Properties();
        config.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp07-ventes-streams");
        config.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        config.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        config.put(StreamsConfig.STATE_DIR_CONFIG, "/tmp/kafka-streams/tp07");
        // Timestamp extractor par défaut = utilise le timestamp Kafka du message
        config.put(StreamsConfig.DEFAULT_TIMESTAMP_EXTRACTOR_CLASS_CONFIG,
                org.apache.kafka.streams.processor.WallclockTimestampExtractor.class);

        Topology topology = buildTopology();
        log.info("Topologie :\n{}", topology.describe());

        KafkaStreams streams = new KafkaStreams(topology, config);
        CountDownLatch latch = new CountDownLatch(1);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            streams.close(Duration.ofSeconds(10));
            latch.countDown();
        }));

        streams.start();
        log.info("✓ Streams démarré. Envoyez des ventes dans 'ventes-stream'");
        log.info("  Format attendu : clé=produit-code, valeur={\"produit\":\"LAP-001\",\"montant\":1299.99}");

        try { latch.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  CONSTRUCTION DE LA TOPOLOGIE AVEC FENÊTRES ET JOINTURES
    // ────────────────────────────────────────────────────────────────────────────
    public static Topology buildTopology() {
        StreamsBuilder builder = new StreamsBuilder();

        // ── Source 1 : flux de ventes ─────────────────────────────────────────
        // Chaque message = {"produit":"LAP-001","montant":1299.99,"qte":1}
        KStream<String, String> ventes = builder.stream("ventes-stream",
                Consumed.with(Serdes.String(), Serdes.String()));

        // ── Source 2 : table catalogue (référentiel produits) ─────────────────
        // KTable = vue matérialisée d'un topic, mise à jour par upsert
        // Un message avec la même clé = mise à jour de la valeur
        // Un message avec valeur null = suppression (tombstone)
        KTable<String, String> catalogue = builder.table("catalogue-table",
                Consumed.with(Serdes.String(), Serdes.String()),
                // Matérialiser = stocker dans un state store interrogeable
                Materialized.as("catalogue-store"));

        // ── Transformation 1 : Extraire le montant de chaque vente ───────────
        // mapValues() transforme la valeur sans changer la clé
        KStream<String, Double> montants = ventes.mapValues(json -> {
            try {
                // Parser JSON basique (en prod : utiliser Jackson)
                String valStr = json.replaceAll(".*\"montant\"\\s*:\\s*([0-9.]+).*", "$1");
                double montant = Double.parseDouble(valStr);
                log.debug("Vente parsée : {}", montant);
                return montant;
            } catch (Exception e) {
                log.warn("JSON invalide ignoré : {}", json);
                return 0.0;
            }
        }).filter((cle, montant) -> montant > 0); // Filtrer les erreurs de parsing

        // ── Transformation 2 : TUMBLING WINDOW — stats par minute ────────────
        // Fenêtre Tumbling : intervalles fixes, non-chevauchants
        // Ex : [10:00-10:01], [10:01-10:02], [10:02-10:03], ...
        // → Parfait pour des rapports périodiques (stats par heure, par jour)
        KTable<Windowed<String>, Double> statsParMinute = montants
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .windowedBy(
                        // Fenêtre de 60 secondes
                        // withNoGrace = pas de tolérance pour les messages tardifs
                        // En prod : TimeWindows.ofSizeAndGrace(60s, 10s) pour les retards
                        TimeWindows.ofSizeWithNoGrace(Duration.ofSeconds(60))
                )
                .aggregate(
                        () -> 0.0,                          // Valeur initiale
                        (produit, montant, total) -> total + montant, // Agréger
                        Materialized.<String, Double, WindowStore<Bytes, byte[]>>as(
                                "stats-par-minute")
                                .withValueSerde(Serdes.Double())
                );

        // Écrire les stats dans le topic de sortie
        statsParMinute.toStream()
                .peek((windowedKey, total) ->
                        log.info("📊 [TUMBLING 1min] {} → {:.2f}€ | Fenêtre: {} → {}",
                                windowedKey.key(),
                                total,
                                windowedKey.window().startTime(),
                                windowedKey.window().endTime())
                )
                .map((windowedKey, total) ->
                        // Convertir la clé Windowed<String> en String normale
                        KeyValue.pair(
                                windowedKey.key() + "@" + windowedKey.window().start(),
                                String.valueOf(total)
                        )
                )
                .to("stats-ventes-1min", Produced.with(Serdes.String(), Serdes.String()));

        // ── Transformation 3 : KStream-KTable JOIN — enrichissement ──────────
        // Enrichir chaque vente avec les infos du catalogue produit
        // Join = pour chaque vente, chercher le produit dans la KTable
        // ATTENTION : les clés doivent être IDENTIQUES des deux côtés !
        //             KStream key = produit code, KTable key = produit code ✓
        KStream<String, String> ventesEnrichies = ventes
                .join(
                        catalogue,
                        // ValueJoiner : comment combiner vente + produit
                        (ventejson, produitjson) -> {
                            if (produitjson == null) {
                                // Produit non trouvé dans la KTable
                                return ventejson + ",\"categorie\":\"INCONNUE\"";
                            }
                            // Fusion simple des deux JSON (en prod : Jackson)
                            String merged = ventejson.replace("}", "")
                                    + ",\"catalogue\":" + produitjson + "}";
                            log.info("✓ JOIN vente+catalogue : {}", merged);
                            return merged;
                        },
                        // Joined.with() : sérialiseurs pour le join
                        Joined.with(Serdes.String(), Serdes.String(), Serdes.String())
                );

        // Publier les ventes enrichies
        ventesEnrichies.to("ventes-enrichies",
                Produced.with(Serdes.String(), Serdes.String()));

        // ── Transformation 4 : SESSION WINDOW — détecter les rafales ─────────
        // Session Window : groupe les messages proches dans le temps
        // Si 2 messages arrivent avec moins de 30s d'écart → même session
        // Quand plus aucun message pendant 30s → session fermée
        // → Parfait pour l'analyse comportementale (sessions utilisateurs)
        KTable<Windowed<String>, Long> sessions = montants
                .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
                .windowedBy(
                        // Inactivité de 30s = fin de session
                        SessionWindows.ofInactivityGapWithNoGrace(Duration.ofSeconds(30))
                )
                .count(Materialized.as("sessions-store"));

        sessions.toStream()
                .peek((windowedKey, count) ->
                        log.info("🎯 [SESSION] {} → {} ventes en {} secondes",
                                windowedKey.key(),
                                count,
                                (windowedKey.window().endTime().toEpochMilli() -
                                 windowedKey.window().startTime().toEpochMilli()) / 1000)
                );

        return builder.build();
    }
}
