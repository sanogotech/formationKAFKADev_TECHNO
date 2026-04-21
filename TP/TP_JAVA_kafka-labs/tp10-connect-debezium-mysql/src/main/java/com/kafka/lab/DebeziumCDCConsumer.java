package com.kafka.lab;

// ============================================================
//  TP10 — Debezium CDC : Capturer TOUS les changements MySQL
// ============================================================
//
//  OBJECTIF :
//   Utiliser Debezium pour du Change Data Capture (CDC).
//   Debezium lit le binlog MySQL et capture chaque INSERT,
//   UPDATE et DELETE en temps réel, avec les valeurs AVANT
//   et APRÈS chaque modification.
//
//  DIFFÉRENCE AVEC TP09 :
//   TP09 (JDBC Source) = polling périodique (scan toutes les N secondes)
//   TP10 (Debezium)   = événementiel (réagit instantanément via binlog)
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TP09 terminé et Docker Compose en cours d'exécution
//   ✅ MySQL avec binlog activé (déjà fait dans init-mysql.sql)
//   ✅ Vérifier Kafka Connect actif : curl http://localhost:8083/
//   ✅ phpMyAdmin disponible : http://localhost:8090
//
//  COMMENT LANCER :
//   Terminal 1 :
//   > cd tp10-connect-debezium-mysql
//   > mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.DebeziumCDCConsumer"
//
//   Terminal 2 (phpMyAdmin ou MySQL CLI) : faire des changements dans MySQL
//   Voir les événements CDC apparaître en temps réel dans Terminal 1 !
//
//  RÉSULTAT ATTENDU :
//   Chaque INSERT, UPDATE, DELETE dans MySQL génère un événement :
//   {
//     "op": "c",           -- c=create, u=update, d=delete, r=read(snapshot)
//     "before": null,      -- valeur AVANT (null pour INSERT)
//     "after": { ... },    -- valeur APRÈS
//     "source": { ... }    -- métadonnées MySQL (binlog, timestamp, etc.)
//   }
// ============================================================

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.*;

public class DebeziumCDCConsumer {

    private static final Logger log = LoggerFactory.getLogger(DebeziumCDCConsumer.class);
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final String CONNECT_URL  = "http://localhost:8083";
    private static final String BOOTSTRAP    = "localhost:9092";

    // Topics CDC créés par Debezium : un par table surveillée
    // Format : {server_name}.{database}.{table}
    private static final List<String> CDC_TOPICS = List.of(
            "mysql-server.shopdb.clients",
            "mysql-server.shopdb.produits",
            "mysql-server.shopdb.commandes"
    );

    public static void main(String[] args) throws Exception {
        log.info("=== TP10 : Debezium CDC — Capture des changements MySQL ===");

        // ── Étape 1 : Déployer le connecteur Debezium ────────────────────────
        deployerConnecteurDebezium();

        // Attendre que le connecteur démarre et fasse le snapshot initial
        log.info("Attente du snapshot initial Debezium (15 secondes)...");
        log.info("TIP : Debezium lit TOUTES les lignes existantes d'abord (snapshot)");
        log.info("      puis passe en mode 'streaming' pour les nouveaux changements");
        Thread.sleep(15_000);

        // ── Étape 2 : Consommer les événements CDC ───────────────────────────
        log.info("--- Démarrage du Consumer CDC ---");
        log.info("TIP : Allez dans phpMyAdmin (http://localhost:8090) et :");
        log.info("      1. Insérez un nouveau client → voir l'événement 'op:c'");
        log.info("      2. Modifiez un produit (prix) → voir l'événement 'op:u' avec before/after");
        log.info("      3. Supprimez une commande → voir l'événement 'op:d'");
        log.info("Ctrl+C pour arrêter");

        consommerEvenementsCDC();
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  DÉPLOIEMENT DU CONNECTEUR DEBEZIUM
    // ────────────────────────────────────────────────────────────────────────────
    private static void deployerConnecteurDebezium() throws Exception {
        log.info("--- Déploiement du connecteur Debezium MySQL ---");

        HttpClient client = HttpClient.newHttpClient();

        // Configuration Debezium — très différente du JDBC Source !
        // Documentation : https://debezium.io/documentation/reference/connectors/mysql.html
        String config = """
        {
          "name": "tp10-debezium-mysql",
          "config": {
            "connector.class": "io.debezium.connector.mysql.MySqlConnector",
            "tasks.max": "1",
            
            "database.hostname": "mysql",
            "database.port":     "3306",
            "database.user":     "debezium",
            "database.password": "debezium_pass",
            
            "database.server.id": "223344",
            "topic.prefix":       "mysql-server",
            
            "database.include.list": "shopdb",
            "table.include.list":    "shopdb.clients,shopdb.produits,shopdb.commandes",
            
            "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
            "schema.history.internal.kafka.topic": "schema-history-tp10",
            
            "include.schema.changes": "true",
            
            "snapshot.mode": "initial",
            
            "key.converter":   "org.apache.kafka.connect.json.JsonConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "key.converter.schemas.enable":   "false",
            "value.converter.schemas.enable": "false",
            
            "transforms": "unwrap",
            "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
            "transforms.unwrap.add.fields": "op,table,db,source.ts_ms",
            "transforms.unwrap.delete.handling.mode": "rewrite",
            "transforms.unwrap.drop.tombstones": "false"
          }
        }
        """;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(config))
                .build();

        HttpResponse<String> response = client.send(request,
                HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 201) {
            log.info("✓ Connecteur Debezium 'tp10-debezium-mysql' créé !");
            log.info("  Debezium lit maintenant le binlog MySQL en temps réel");
        } else if (response.statusCode() == 409) {
            log.info("✓ Connecteur Debezium déjà existant — OK");
        } else {
            log.error("✗ Erreur : HTTP {} → {}", response.statusCode(), response.body());
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  CONSUMER DES ÉVÉNEMENTS CDC
    //  Chaque message contient : op, before, after, source metadata
    // ────────────────────────────────────────────────────────────────────────────
    private static void consommerEvenementsCDC() {
        Properties props = new Properties();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, BOOTSTRAP);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "tp10-cdc-consumer");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
                StringDeserializer.class.getName());
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
                StringDeserializer.class.getName());
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "true");

        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props)) {
            consumer.subscribe(CDC_TOPICS);
            log.info("Consumer abonné aux topics CDC : {}", CDC_TOPICS);

            long messageCount = 0;

            while (!Thread.currentThread().isInterrupted()) {
                ConsumerRecords<String, String> records =
                        consumer.poll(Duration.ofMillis(1000));

                for (ConsumerRecord<String, String> record : records) {
                    messageCount++;
                    afficherEvenementCDC(record, messageCount);
                }
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  INTERPRÉTER ET AFFICHER UN ÉVÉNEMENT CDC DEBEZIUM
    // ────────────────────────────────────────────────────────────────────────────
    private static void afficherEvenementCDC(
            ConsumerRecord<String, String> record, long num) {
        try {
            // Le topic révèle quelle table a changé
            String table = record.topic().replace("mysql-server.shopdb.", "");

            // Parser le JSON de l'événement
            JsonNode payload = mapper.readTree(record.value());

            // "op" = type d'opération
            // "c" = create (INSERT)
            // "u" = update (UPDATE)
            // "d" = delete (DELETE)
            // "r" = read   (snapshot initial)
            String op = payload.path("__op").asText(
                       payload.path("op").asText("?"));

            String opLabel = switch (op) {
                case "c" -> "✅ INSERT";
                case "u" -> "🔄 UPDATE";
                case "d" -> "❌ DELETE";
                case "r" -> "📸 SNAPSHOT";
                default  -> "❓ " + op;
            };

            // Affichage selon le type d'opération
            log.info("═══ Événement #{} | Table: {} | Op: {} ═══",
                    num, table.toUpperCase(), opLabel);

            // Valeur AVANT la modification (null pour INSERT)
            JsonNode before = payload.path("before");
            if (!before.isMissingNode() && !before.isNull()) {
                log.info("  AVANT  → {}", before.toPrettyString());
            }

            // Valeur APRÈS la modification (null pour DELETE)
            JsonNode after = payload.path("after");
            if (!after.isMissingNode() && !after.isNull()) {
                log.info("  APRÈS  → {}", after.toPrettyString());
            } else if ("d".equals(op)) {
                log.info("  (ligne supprimée — plus de valeur 'after')");
            }

            // Métadonnées de source (timestamp MySQL, position binlog)
            long sourceTs = payload.path("__source_ts_ms")
                    .asLong(payload.path("source").path("ts_ms").asLong(0));
            if (sourceTs > 0) {
                log.info("  Timestamp MySQL : {}ms", sourceTs);
            }

        } catch (Exception e) {
            log.warn("Message non-JSON ignoré (topic={}): {}", record.topic(), record.value());
        }
    }
}
