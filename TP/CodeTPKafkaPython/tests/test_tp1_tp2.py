"""
Tests TP 1 & TP 2 – Administration : liste et création de topics
"""

import pytest
import time
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException

# Import des fonctions à tester
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tp1_list_topics import list_topics
from tp2_create_topic import create_topic


# ─── TP 1 ─────────────────────────────────────────────────────────────────────

class TestListTopics:

    def test_list_topics_returns_list(self, unique_topic):
        bootstrap, topic = unique_topic
        topics = list_topics(bootstrap_servers=bootstrap)
        assert isinstance(topics, list), "list_topics() doit retourner une liste"

    def test_created_topic_appears_in_list(self, unique_topic):
        bootstrap, topic = unique_topic
        topics = list_topics(bootstrap_servers=bootstrap)
        assert topic in topics, f"Le topic '{topic}' doit apparaître dans la liste"

    def test_list_topics_invalid_broker(self):
        with pytest.raises(Exception):
            list_topics(bootstrap_servers="localhost:19999")


# ─── TP 2 ─────────────────────────────────────────────────────────────────────

class TestCreateTopic:

    def test_create_new_topic(self, kafka_bootstrap):
        import uuid
        topic_name = f"new-{uuid.uuid4().hex[:6]}"
        created = create_topic(
            topic_name,
            num_partitions=2,
            replication_factor=1,
            bootstrap_servers=kafka_bootstrap,
        )
        assert created is True, "Doit retourner True pour un nouveau topic"

        # Vérifier que le topic existe maintenant
        topics = list_topics(bootstrap_servers=kafka_bootstrap)
        assert topic_name in topics

    def test_create_existing_topic_returns_false(self, unique_topic):
        bootstrap, existing_topic = unique_topic
        # Tenter de recréer le même topic
        result = create_topic(
            existing_topic,
            bootstrap_servers=bootstrap,
        )
        assert result is False, "Doit retourner False si le topic existe déjà"

    def test_create_topic_with_3_partitions(self, kafka_bootstrap):
        import uuid
        topic_name = f"parts-{uuid.uuid4().hex[:6]}"
        create_topic(topic_name, num_partitions=3, bootstrap_servers=kafka_bootstrap)

        admin = AdminClient({"bootstrap.servers": kafka_bootstrap})
        metadata = admin.list_topics(timeout=5)
        topic_meta = metadata.topics.get(topic_name)

        assert topic_meta is not None
        assert len(topic_meta.partitions) == 3
