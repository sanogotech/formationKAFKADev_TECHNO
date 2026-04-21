"""
conftest.py – Fixtures pytest partagées pour tous les tests.

Utilise Testcontainers pour lancer un broker Kafka éphémère
(Docker requis). Le cluster est partagé pour toute la session de tests.
"""

import pytest
import time

# ─── Tentative d'import Testcontainers ───────────────────────────────────────
try:
    from testcontainers.kafka import KafkaContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False


# ─── Skip automatique si Testcontainers n'est pas disponible ─────────────────
requires_kafka = pytest.mark.skipif(
    not TESTCONTAINERS_AVAILABLE,
    reason="testcontainers[kafka] non installé – pip install testcontainers[kafka]",
)


@pytest.fixture(scope="session")
def kafka_bootstrap(request):
    """
    Lance un cluster Kafka Testcontainers pour toute la session.
    Retourne l'adresse bootstrap (ex: 'localhost:49152').
    """
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers[kafka] non installé")

    with KafkaContainer("confluentinc/cp-kafka:7.6.1") as kafka:
        bootstrap = kafka.get_bootstrap_server()
        print(f"\n🐋 Kafka Testcontainers démarré : {bootstrap}")
        # Attendre que le broker soit prêt
        time.sleep(2)
        yield bootstrap
        print("\n🛑 Arrêt du cluster Kafka Testcontainers")


@pytest.fixture(scope="function")
def unique_topic(kafka_bootstrap):
    """
    Crée un topic unique par test (isolation totale).
    Retourne (bootstrap_servers, topic_name).
    """
    import uuid
    from confluent_kafka.admin import AdminClient, NewTopic

    topic_name = f"test-{uuid.uuid4().hex[:8]}"
    admin = AdminClient({"bootstrap.servers": kafka_bootstrap})
    new_topic = NewTopic(topic_name, num_partitions=3, replication_factor=1)

    futures = admin.create_topics([new_topic])
    for _, f in futures.items():
        f.result()

    time.sleep(0.5)  # laisser le topic se propager
    yield kafka_bootstrap, topic_name

    # Nettoyage
    admin.delete_topics([topic_name])
