package com.kafka.lab;

// ============================================================
//  TP05 — Sérialisation Avro & Schema Registry
// ============================================================
//
//  OBJECTIF :
//   Utiliser Apache Avro pour sérialiser les messages Kafka.
//   Avro = format binaire compact + schéma centralisé.
//   Le Schema Registry stocke les schémas et assure
//   la compatibilité lors des évolutions.
//
//  AVANTAGES D'AVRO vs JSON :
//   ✅ 3-10x plus compact (binaire vs texte)
//   ✅ Schéma partagé → moins de données à transmettre
//   ✅ Évolution du schéma avec compatibilité backward/forward
//   ✅ Validation automatique des données
//
//  PRÉREQUIS AVANT CE TP :
//   ✅ TP01-04 terminés
//   ✅ Schema Registry lancé :
//      docker run -d --name schema-registry \
//        -e SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS=localhost:9092 \
//        -e SCHEMA_REGISTRY_HOST_NAME=localhost \
//        -p 8081:8081 confluentinc/cp-schema-registry:7.6.0
//   ✅ Vérifier : curl http://localhost:8081/subjects
//
//  COMMENT LANCER :
//   > cd tp05-avro-schema && mvn clean package -q
//   > mvn exec:java -Dexec.mainClass="com.kafka.lab.AvroProducerApp"
// ============================================================

import org.apache.avro.Schema;
import org.apache.avro.generic.GenericData;
import org.apache.avro.generic.GenericRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;

/**
 * Démonstration Avro "à la main" (sans io.confluent.kafka-avro-serializer)
 * pour comprendre le mécanisme sous-jacent.
 * En production, utiliser KafkaAvroSerializer de Confluent.
 */
public class AvroProducerApp {

    private static final Logger log = LoggerFactory.getLogger(AvroProducerApp.class);

    // Schéma Avro défini inline — en production : fichier .avsc dans resources/
    private static final String SCHEMA_JSON = """
        {
          "type": "record",
          "name": "Produit",
          "namespace": "com.kafka.lab.avro",
          "doc": "Schéma Avro pour un produit e-commerce",
          "fields": [
            { "name": "id",          "type": "int",
              "doc": "Identifiant unique du produit" },
            { "name": "code",        "type": "string",
              "doc": "Code produit (ex: LAP-001)" },
            { "name": "nom",         "type": "string",
              "doc": "Nom du produit" },
            { "name": "categorie",   "type": ["null", "string"],
              "default": null,
              "doc": "Catégorie — nullable (union avec null)" },
            { "name": "prix",        "type": "double",
              "doc": "Prix en euros" },
            { "name": "stock",       "type": "int",
              "default": 0,
              "doc": "Stock disponible — défaut à 0" },
            { "name": "timestamp",   "type": "long",
              "logicalType": "timestamp-millis",
              "doc": "Timestamp Unix en millisecondes" }
          ]
        }
        """;

    public static void main(String[] args) throws Exception {
        log.info("=== TP05 : Sérialisation Avro & Schema Registry ===");

        // ── Étape 1 : Parser le schéma Avro ──────────────────────────────────
        Schema schema = new Schema.Parser().parse(SCHEMA_JSON);
        log.info("✓ Schéma Avro parsé : {} champs", schema.getFields().size());
        schema.getFields().forEach(f ->
                log.info("  - {} : {} (doc: {})", f.name(), f.schema(), f.doc()));

        // ── Étape 2 : Enregistrer le schéma dans Schema Registry ─────────────
        String schemaId = enregistrerSchema("tp05-produits-value", SCHEMA_JSON);
        log.info("✓ Schéma enregistré dans Schema Registry, ID={}", schemaId);

        // ── Étape 3 : Créer des enregistrements Avro génériques ──────────────
        log.info("--- Création d'enregistrements Avro ---");

        GenericRecord produit1 = new GenericData.Record(schema);
        produit1.put("id",         1);
        produit1.put("code",       "LAP-001");
        produit1.put("nom",        "Laptop Pro 15");
        produit1.put("categorie",  "Informatique");   // Union null|string
        produit1.put("prix",       1299.99);
        produit1.put("stock",      50);
        produit1.put("timestamp",  System.currentTimeMillis());

        GenericRecord produit2 = new GenericData.Record(schema);
        produit2.put("id",         2);
        produit2.put("code",       "MOU-002");
        produit2.put("nom",        "Souris Ergonomique");
        produit2.put("categorie",  null);             // null = valeur nullable acceptée
        produit2.put("prix",       49.99);
        produit2.put("stock",      200);
        produit2.put("timestamp",  System.currentTimeMillis());

        // ── Étape 4 : Sérialiser en binaire Avro ─────────────────────────────
        byte[] bytes1 = serializerAvro(produit1, schema);
        byte[] bytes2 = serializerAvro(produit2, schema);

        log.info("✓ Produit 1 sérialisé : {} bytes (JSON équiv. ~150 bytes)",
                bytes1.length);
        log.info("✓ Produit 2 sérialisé : {} bytes", bytes2.length);

        // ── Étape 5 : Comparer avec JSON ─────────────────────────────────────
        String jsonEquiv = """
            {"id":1,"code":"LAP-001","nom":"Laptop Pro 15",
             "categorie":"Informatique","prix":1299.99,"stock":50,
             "timestamp":1714500000000}""";
        log.info("📊 Comparaison taille :");
        log.info("   JSON  : {} bytes", jsonEquiv.getBytes(StandardCharsets.UTF_8).length);
        log.info("   Avro  : {} bytes", bytes1.length);
        log.info("   Gain  : {}%", (100 - (bytes1.length * 100 / jsonEquiv.length())));

        // ── Étape 6 : Désérialiser ────────────────────────────────────────────
        GenericRecord deserialise = deserializerAvro(bytes1, schema);
        log.info("✓ Désérialisé : {} → prix={}€",
                deserialise.get("nom"), deserialise.get("prix"));

        log.info("=== TP05 Terminé ===");
        log.info("TIP : En production, utiliser io.confluent.kafka.serializers.KafkaAvroSerializer");
        log.info("      avec le connecteur Confluent Schema Registry pour une intégration complète");
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Enregistrer le schéma dans Schema Registry via l'API REST
    // ────────────────────────────────────────────────────────────────────────────
    private static String enregistrerSchema(String subject, String schemaJson) {
        try {
            HttpClient client = HttpClient.newHttpClient();
            // Envelopper le schéma dans le format attendu par Schema Registry
            String body = "{\"schema\":" +
                    new com.fasterxml.jackson.databind.ObjectMapper()
                            .writeValueAsString(schemaJson) + "}";

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("http://localhost:8081/subjects/" + subject + "/versions"))
                    .header("Content-Type", "application/vnd.schemaregistry.v1+json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = client.send(request,
                    HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() == 200 || response.statusCode() == 201) {
                return response.body(); // {"id": 1}
            } else {
                log.warn("Schema Registry non disponible ({}), mode local seulement",
                        response.statusCode());
                return "local-only";
            }
        } catch (Exception e) {
            log.warn("Schema Registry non joignable : {} — mode local", e.getMessage());
            return "offline";
        }
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Sérialisation Avro en mémoire
    // ────────────────────────────────────────────────────────────────────────────
    private static byte[] serializerAvro(GenericRecord record, Schema schema)
            throws Exception {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        org.apache.avro.io.DatumWriter<GenericRecord> writer =
                new org.apache.avro.generic.GenericDatumWriter<>(schema);
        org.apache.avro.io.Encoder encoder =
                org.apache.avro.io.EncoderFactory.get().binaryEncoder(baos, null);
        writer.write(record, encoder);
        encoder.flush();
        return baos.toByteArray();
    }

    // ────────────────────────────────────────────────────────────────────────────
    //  Désérialisation Avro depuis bytes
    // ────────────────────────────────────────────────────────────────────────────
    private static GenericRecord deserializerAvro(byte[] bytes, Schema schema)
            throws Exception {
        org.apache.avro.io.DatumReader<GenericRecord> reader =
                new org.apache.avro.generic.GenericDatumReader<>(schema);
        org.apache.avro.io.Decoder decoder =
                org.apache.avro.io.DecoderFactory.get().binaryDecoder(bytes, null);
        return reader.read(null, decoder);
    }
}
