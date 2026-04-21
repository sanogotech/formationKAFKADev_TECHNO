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

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

public class KafkaConnectManager {

    private static final Logger log = LoggerFactory.getLogger(KafkaConnectManager.class);

    // URL de l'API REST Kafka Connect (port 8083 par défaut)
    private static final String CONNECT_URL = "http://localhost:8083";

    // Jackson pour sérialiser/désérialiser les JSON de l'API
    private static final ObjectMapper mapper = new ObjectMapper();

    // Client HTTP Java 11+ (intégré à la JDK, pas besoin de dépendance)
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    public static void main(String[] args) throws Exception {
        log.info("=== TP09 : Kafka Connect Manager ===");

        // ── Étape 1 : Vérifier que Kafka Connect est disponible ──────────────
        verifierConnectDisponible();

        // ── Étape 2 : Lister les connecteurs existants ───────────────────────
        listerConnecteurs();

        // ── Étape 3 : Déployer le connecteur JDBC Source (MySQL → Kafka) ─────
        deployer_JDBC_Source();

        // ── Étape 4 : Attendre et vérifier le statut ────────────────────────
        Thread.sleep(5000); // Laisser le connecteur démarrer
        verifierStatut("tp09-mysql-source");

        // ── Étape 5 : Afficher les messages arrivant dans Kafka ──────────────
        log.info("--- Vérifier les messages dans Kafka ---");
        log.info("TIP : Ouvrir Kafka UI → http://localhost:8080");
        log.info("TIP : Topics créés : mysql-shopdb-clients, mysql-shopdb-produits, etc.");
        log.info("TIP : Dans phpMyAdmin → shopdb → insérer une ligne → voir le message arriver !");

        log.info("=== TP09 Terminé ! ===");
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Vérifier que Kafka Connect REST API répond
    // ────────────────────────────────────────────────────────────────────────────
    private static void verifierConnectDisponible() throws Exception {
        log.info("--- Vérification de Kafka Connect ---");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/"))
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request,
                HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200) {
            JsonNode info = mapper.readTree(response.body());
            log.info("✓ Kafka Connect disponible — Version: {}",
                    info.path("version").asText("inconnue"));
        } else {
            throw new RuntimeException("Kafka Connect non disponible ! " +
                    "Vérifier que Docker est lancé : docker compose up -d");
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Lister les connecteurs actifs
    // ────────────────────────────────────────────────────────────────────────────
    private static void listerConnecteurs() throws Exception {
        log.info("--- Connecteurs actifs ---");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors?expand=status"))
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request,
                HttpResponse.BodyHandlers.ofString());

        JsonNode connecteurs = mapper.readTree(response.body());
        if (connecteurs.isEmpty()) {
            log.info("  (aucun connecteur actif)");
        } else {
            connecteurs.fieldNames().forEachRemaining(nom -> {
                String statut = connecteurs.path(nom)
                        .path("status").path("connector").path("state").asText("?");
                log.info("  📌 {} → {}", nom, statut);
            });
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Déployer le connecteur JDBC Source : MySQL → Kafka
    //
    //  Ce connecteur lit les tables MySQL et publie chaque ligne
    //  comme un message JSON dans un topic Kafka.
    //  Mode "incrementing" : détecte les nouvelles lignes par auto-increment
    // ────────────────────────────────────────────────────────────────────────────
    private static void deployer_JDBC_Source() throws Exception {
        log.info("--- Déploiement du connecteur JDBC Source (MySQL → Kafka) ---");

        // Configuration du connecteur JDBC Source
        // Voir : https://docs.confluent.io/kafka-connectors/jdbc/current/source-connector/
        Map<String, Object> config = Map.of(
                "name", "tp09-mysql-source",
                "config", Map.of(
                        // Classe du connecteur JDBC Source Confluent
                        "connector.class", "io.confluent.connect.jdbc.JdbcSourceConnector",

                        // Nombre de tâches parallèles (1 par table généralement)
                        "tasks.max", "3",

                        // URL JDBC MySQL (utilise le hostname du service Docker)
                        "connection.url",
                        "jdbc:mysql://mysql:3306/shopdb?useSSL=false&allowPublicKeyRetrieval=true",
                        "connection.user",     "kafka_user",
                        "connection.password", "kafka_pass",

                        // Tables à synchroniser (séparées par virgule)
                        "table.whitelist", "clients,produits,commandes",

                        // Mode de détection des nouvelles lignes :
                        // "incrementing" = par colonne auto-increment (id)
                        // "timestamp"    = par colonne updated_at
                        // "bulk"         = recharger toute la table à chaque poll
                        "mode", "incrementing",
                        "incrementing.column.name", "id",

                        // Intervalle de vérification de nouvelles données (5 secondes)
                        "poll.interval.ms", "5000",

                        // Préfixe des topics Kafka créés : mysql-shopdb-clients
                        "topic.prefix", "mysql-shopdb-",

                        // Format JSON sans schéma Avro (plus simple pour ce TP)
                        "value.converter", "org.apache.kafka.connect.json.JsonConverter",
                        "value.converter.schemas.enable", "false",

                        // Transformer : ajouter le timestamp d'ingestion
                        "transforms", "addTimestamp",
                        "transforms.addTimestamp.type",
                        "org.apache.kafka.connect.transforms.InsertField$Value",
                        "transforms.addTimestamp.timestamp.field", "kafka_ingested_at"
                )
        );

        String body = mapper.writeValueAsString(config);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = httpClient.send(request,
                HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 201) {
            log.info("✓ Connecteur 'tp09-mysql-source' créé avec succès !");
            log.info("  → Topics créés : mysql-shopdb-clients, mysql-shopdb-produits, mysql-shopdb-commandes");
        } else if (response.statusCode() == 409) {
            log.info("✓ Connecteur déjà existant (409 Conflict) — OK");
        } else {
            log.error("✗ Erreur création connecteur : HTTP {} → {}",
                    response.statusCode(), response.body());
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Vérifier le statut d'un connecteur
    // ────────────────────────────────────────────────────────────────────────────
    private static void verifierStatut(String nomConnecteur) throws Exception {
        log.info("--- Statut du connecteur '{}' ---", nomConnecteur);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CONNECT_URL + "/connectors/" + nomConnecteur + "/status"))
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request,
                HttpResponse.BodyHandlers.ofString());

        JsonNode statut = mapper.readTree(response.body());
        String etatConnecteur = statut.path("connector").path("state").asText("?");
        log.info("  État connecteur : {}", etatConnecteur);

        // Vérifier chaque tâche
        statut.path("tasks").forEach(task -> {
            int taskId = task.path("id").asInt();
            String etatTask = task.path("state").asText("?");
            log.info("  Tâche {} : {}", taskId, etatTask);

            if ("FAILED".equals(etatTask)) {
                log.error("  ⚠ Erreur tâche {} : {}", taskId,
                        task.path("trace").asText("(pas de détail)"));
            }
        });

        if ("RUNNING".equals(etatConnecteur)) {
            log.info("✓ Connecteur opérationnel — MySQL → Kafka en cours !");
        } else {
            log.warn("⚠ Connecteur en état '{}' — vérifier les logs Docker", etatConnecteur);
        }
    }
}
