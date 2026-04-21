package com.kafka.lab;

// ============================================================
//  TP09 — Kafka Connect : Gérer les connecteurs via REST API
// ============================================================
//
//  OBJECTIF :
//   Déployer et gérer des connecteurs Kafka Connect depuis Java.
//   On implémente un client REST pour l'API Kafka Connect
//   et on déploie un connecteur JDBC Source (MySQL → Kafka).
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ Docker Desktop installé et fonctionnel
//   ✅ Lancer l'environnement Docker :
//      docker compose -f docker-compose-connect.yml up -d
//   ✅ Attendre que Kafka Connect soit prêt (~2 minutes) :
//      curl http://localhost:8083/    (doit retourner 200)
//   ✅ Vérifier phpMyAdmin : http://localhost:8090
//      (login: root / rootpass, DB: shopdb)
//
//  COMMENT LANCER :
//   > cd tp09-connect-cdc
//   > mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.KafkaConnectManager"
//
//  RÉSULTAT ATTENDU :
//   - Connecteur JDBC Source créé → MySQL → Kafka
//   - Messages des tables MySQL visibles dans Kafka
//   - Kafka UI : http://localhost:8080 → Topics → mysql-shopdb-*
// ============================================================

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

public class KafkaConnectManager {

    private static final Logger log = LoggerFactory.getLogger(KafkaConnectManager.class);

    private static final String CONNECT_URL = "http://localhost:8083";
    private static final ObjectMapper mapper = new ObjectMapper();
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    public static void main(String[] args) throws Exception {
        log.info("=== TP09 : Kafka Connect Manager ===");

        verifierConnectDisponible();
        listerConnecteurs();
        deployer_JDBC_Source();
        Thread.sleep(5000);
        verifierStatut("tp09-mysql-source");

        log.info("--- Vérifier les messages dans Kafka ---");
        log.info("TIP : Ouvrir Kafka UI → http://localhost:8080");
        log.info("TIP : Topics créés : mysql-shopdb-clients, mysql-shopdb-produits, etc.");
        log.info("TIP : Dans phpMyAdmin → shopdb → insérer une ligne → voir le message arriver !");

        log.info("=== TP09 Terminé ! ===");
    }

    private static void verifierConnectDisponible() throws Exception {
        log.info("--- Vérification de Kafka Connect ---");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/"))
                .GET()
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() == 200) {
            JsonNode info = mapper.readTree(response.body());
            log.info("✓ Kafka Connect disponible — Version: {}", info.path("version").asText("inconnue"));
        } else {
            throw new RuntimeException("Kafka Connect non disponible ! Vérifier Docker : docker compose up -d");
        }
    }

    private static void listerConnecteurs() throws Exception {
        log.info("--- Connecteurs actifs ---");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors?expand=status"))
                .header("Accept", "application/json")
                .GET()
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode connecteurs = mapper.readTree(response.body());
        if (connecteurs.isEmpty()) {
            log.info("  (aucun connecteur actif)");
        } else {
            connecteurs.fieldNames().forEachRemaining(nom -> {
                String statut = connecteurs.path(nom).path("status").path("connector").path("state").asText("?");
                log.info("  📌 {} → {}", nom, statut);
            });
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Déploiement du connecteur JDBC Source (MySQL → Kafka)
    //  Correction : utilisation de HashMap au lieu de Map.of (nombre d'arguments illimité)
    // ────────────────────────────────────────────────────────────────────────────
    private static void deployer_JDBC_Source() throws Exception {
        log.info("--- Déploiement du connecteur JDBC Source (MySQL → Kafka) ---");

        // Construction de la configuration interne du connecteur
        Map<String, Object> connectorConfig = new HashMap<>();
        connectorConfig.put("connector.class", "io.confluent.connect.jdbc.JdbcSourceConnector");
        connectorConfig.put("tasks.max", "3");
        connectorConfig.put("connection.url", "jdbc:mysql://mysql:3306/shopdb?useSSL=false&allowPublicKeyRetrieval=true");
        connectorConfig.put("connection.user", "kafka_user");
        connectorConfig.put("connection.password", "kafka_pass");
        connectorConfig.put("table.whitelist", "clients,produits,commandes");
        connectorConfig.put("mode", "incrementing");
        connectorConfig.put("incrementing.column.name", "id");
        connectorConfig.put("poll.interval.ms", "5000");
        connectorConfig.put("topic.prefix", "mysql-shopdb-");
        connectorConfig.put("value.converter", "org.apache.kafka.connect.json.JsonConverter");
        connectorConfig.put("value.converter.schemas.enable", "false");
        connectorConfig.put("transforms", "addTimestamp");
        connectorConfig.put("transforms.addTimestamp.type", "org.apache.kafka.connect.transforms.InsertField$Value");
        connectorConfig.put("transforms.addTimestamp.timestamp.field", "kafka_ingested_at");

        // Configuration racine : nom + config
        Map<String, Object> payload = new HashMap<>();
        payload.put("name", "tp09-mysql-source");
        payload.put("config", connectorConfig);

        String body = mapper.writeValueAsString(payload);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 201) {
            log.info("✓ Connecteur 'tp09-mysql-source' créé avec succès !");
            log.info("  → Topics créés : mysql-shopdb-clients, mysql-shopdb-produits, mysql-shopdb-commandes");
        } else if (response.statusCode() == 409) {
            log.info("✓ Connecteur déjà existant (409 Conflict) — OK");
        } else {
            log.error("✗ Erreur création connecteur : HTTP {} → {}", response.statusCode(), response.body());
        }
    }

    private static void verifierStatut(String nomConnecteur) throws Exception {
        log.info("--- Statut du connecteur '{}' ---", nomConnecteur);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors/" + nomConnecteur + "/status"))
                .GET()
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode statut = mapper.readTree(response.body());
        String etatConnecteur = statut.path("connector").path("state").asText("?");
        log.info("  État connecteur : {}", etatConnecteur);

        statut.path("tasks").forEach(task -> {
            int taskId = task.path("id").asInt();
            String etatTask = task.path("state").asText("?");
            log.info("  Tâche {} : {}", taskId, etatTask);
            if ("FAILED".equals(etatTask)) {
                log.error("  ⚠ Erreur tâche {} : {}", taskId, task.path("trace").asText("(pas de détail)"));
            }
        });

        if ("RUNNING".equals(etatConnecteur)) {
            log.info("✓ Connecteur opérationnel — MySQL → Kafka en cours !");
        } else {
            log.warn("⚠ Connecteur en état '{}' — vérifier les logs Docker", etatConnecteur);
        }
    }
}