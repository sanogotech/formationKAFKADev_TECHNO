package com.kafka.lab;

// ============================================================
//  TEST TP01 — Tests unitaires de la gestion des Topics
//
//  PRÉREQUIS : Kafka en local sur localhost:9092
//  LANCER    : mvn test
//  OU        : mvn test -Dtest=TopicManagerTest
// ============================================================

import org.apache.kafka.clients.admin.*;
import org.apache.kafka.common.errors.TopicExistsException;
import org.junit.jupiter.api.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ExecutionException;

import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class TopicManagerTest {

    private static final Logger log = LoggerFactory.getLogger(TopicManagerTest.class);
    private static AdminClient adminClient;

    // Nom unique avec timestamp pour éviter les conflits entre exécutions
    private static final String TEST_TOPIC = "tp01-test-" + System.currentTimeMillis();

    @BeforeAll
    static void setup() {
        // Créer l'AdminClient UNE FOIS pour tous les tests
        Properties props = new Properties();
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        adminClient = AdminClient.create(props);
        log.info("Test setup : AdminClient créé, topic de test = {}", TEST_TOPIC);
    }

    @AfterAll
    static void teardown() throws Exception {
        // Nettoyer : supprimer le topic de test et fermer le client
        try {
            adminClient.deleteTopics(List.of(TEST_TOPIC)).all().get();
            log.info("Teardown : topic {} supprimé", TEST_TOPIC);
        } catch (Exception e) {
            log.warn("Teardown : impossible de supprimer {} : {}", TEST_TOPIC, e.getMessage());
        } finally {
            adminClient.close();
        }
    }

    @Test
    @Order(1)
    @DisplayName("Création d'un topic avec 3 partitions")
    void testCreationTopic() throws Exception {
        // ARRANGE : préparer le topic à créer
        NewTopic newTopic = new NewTopic(TEST_TOPIC, 3, (short) 1);

        // ACT : créer le topic
        adminClient.createTopics(List.of(newTopic)).all().get();

        Thread.sleep(500); // Attendre propagation des métadonnées

        // ASSERT : vérifier que le topic existe
        Set<String> topics = adminClient.listTopics().names().get();
        assertTrue(topics.contains(TEST_TOPIC),
                "Le topic " + TEST_TOPIC + " doit exister après création");

        log.info("✓ TEST PASSÉ : Topic créé avec 3 partitions");
    }

    @Test
    @Order(2)
    @DisplayName("Vérification des partitions du topic")
    void testNombrePartitions() throws Exception {
        // ACT : décrire le topic
        Map<String, TopicDescription> desc =
                adminClient.describeTopics(List.of(TEST_TOPIC)).allTopicNames().get();

        // ASSERT : 3 partitions attendues
        TopicDescription description = desc.get(TEST_TOPIC);
        assertNotNull(description, "La description ne doit pas être null");
        assertEquals(3, description.partitions().size(),
                "Le topic doit avoir exactement 3 partitions");

        log.info("✓ TEST PASSÉ : {} partitions vérifiées", description.partitions().size());
    }

    @Test
    @Order(3)
    @DisplayName("Création d'un topic déjà existant lève TopicExistsException")
    void testCreationTopicExistant() {
        // Tenter de créer le même topic — doit lever une exception
        NewTopic duplicateTopic = new NewTopic(TEST_TOPIC, 1, (short) 1);

        ExecutionException exception = assertThrows(ExecutionException.class, () ->
                adminClient.createTopics(List.of(duplicateTopic)).all().get()
        );

        // Vérifier que c'est bien une TopicExistsException
        assertTrue(exception.getCause() instanceof TopicExistsException,
                "Doit lever TopicExistsException");

        log.info("✓ TEST PASSÉ : TopicExistsException levée comme attendu");
    }
}
