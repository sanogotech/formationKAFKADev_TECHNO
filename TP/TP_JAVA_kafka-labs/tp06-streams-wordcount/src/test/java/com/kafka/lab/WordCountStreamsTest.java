package com.kafka.lab;

// ============================================================
//  TEST TP06 — Tester Kafka Streams SANS broker réel
//
//  TopologyTestDriver : permet de tester les topologies Streams
//  en mémoire, sans Kafka, donc très rapide !
//
//  LANCER : mvn test
// ============================================================

import org.apache.kafka.common.serialization.LongDeserializer;
import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.test.TestRecord;
import org.junit.jupiter.api.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Properties;

import static org.junit.jupiter.api.Assertions.*;

class WordCountStreamsTest {

    private static final Logger log = LoggerFactory.getLogger(WordCountStreamsTest.class);

    // TopologyTestDriver : simule Kafka en mémoire
    private TopologyTestDriver testDriver;
    private TestInputTopic<String, String> inputTopic;
    private TestOutputTopic<String, Long>  outputTopic;

    @BeforeEach
    void setup() {
        // Utiliser la topologie de production (même code !)
        Topology topology = WordCountStreamsApp.buildTopology();

        // Config minimale pour les tests
        Properties testConfig = new Properties();
        testConfig.put(StreamsConfig.APPLICATION_ID_CONFIG, "test-wordcount");
        testConfig.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "dummy:9092");
        testConfig.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        testConfig.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        // Créer le driver de test
        testDriver = new TopologyTestDriver(topology, testConfig);

        // Créer les topics de test en mémoire
        inputTopic = testDriver.createInputTopic(
                "streams-input",
                new StringSerializer(), new StringSerializer()
        );
        outputTopic = testDriver.createOutputTopic(
                "streams-wordcount-output",
                new StringDeserializer(), new LongDeserializer()
        );

        log.info("Test setup : TopologyTestDriver créé");
    }

    @AfterEach
    void teardown() {
        testDriver.close();
    }

    @Test
    @DisplayName("Comptage d'un mot unique")
    void testUnMot() {
        // Envoyer un seul mot
        inputTopic.pipeInput("k1", "kafka");

        // Vérifier le résultat
        TestRecord<String, Long> record = outputTopic.readRecord();
        assertEquals("kafka", record.getKey());
        assertEquals(1L, record.getValue());
        log.info("✓ 'kafka' → 1");
    }

    @Test
    @DisplayName("Comptage de plusieurs occurrences")
    void testPlusieursOccurrences() {
        // "kafka" apparaît 3 fois au total
        inputTopic.pipeInput(null, "kafka est excellent");
        inputTopic.pipeInput(null, "kafka est rapide");
        inputTopic.pipeInput(null, "j aime kafka");

        // Lire tous les résultats
        var resultats = outputTopic.readKeyValuesToMap();

        // "kafka" doit avoir été vu 3 fois
        assertEquals(3L, resultats.getOrDefault("kafka", 0L),
                "kafka doit apparaître 3 fois");
        assertEquals(2L, resultats.getOrDefault("est", 0L),
                "'est' doit apparaître 2 fois");

        log.info("✓ Occurrences : {}", resultats);
    }

    @Test
    @DisplayName("Conversion en minuscules")
    void testMinuscules() {
        inputTopic.pipeInput(null, "KAFKA Kafka kafka");

        var resultats = outputTopic.readKeyValuesToMap();

        // Tout doit être compté comme "kafka" (minuscule)
        assertEquals(3L, resultats.getOrDefault("kafka", 0L),
                "La casse doit être ignorée");
        log.info("✓ Insensible à la casse : {}", resultats);
    }

    @Test
    @DisplayName("Filtrage des mots vides")
    void testMotsVides() {
        inputTopic.pipeInput(null, "  kafka  ");
        var resultats = outputTopic.readKeyValuesToMap();

        // Seulement "kafka" — pas de clé vide
        assertFalse(resultats.containsKey(""), "Pas de mot vide dans les résultats");
        assertTrue(resultats.containsKey("kafka"), "kafka doit être compté");
        log.info("✓ Mots vides filtrés");
    }
}
