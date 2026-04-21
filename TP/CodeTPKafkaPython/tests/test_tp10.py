"""
Tests TP 10 – Dead Letter Queue
"""

import json
import time
import pytest
from confluent_kafka import Consumer, Producer

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tp10_dlq import process_with_dlq, send_to_dlq


class TestDLQ:

    def test_valid_messages_are_processed(self, unique_topic):
        bootstrap, topic = unique_topic
        dlq_topic = f"{topic}-dlq"

        # Créer le topic DLQ
        from confluent_kafka.admin import AdminClient, NewTopic
        admin = AdminClient({"bootstrap.servers": bootstrap})
        admin.create_topics([NewTopic(dlq_topic, 1, 1)])
        time.sleep(0.3)

        # Injecter uniquement des messages valides
        p = Producer({"bootstrap.servers": bootstrap})
        for i in range(3):
            msg = json.dumps({"order_id": i, "amount": 10.0 * (i + 1)})
            p.produce(topic, value=msg.encode())
        p.flush(5)
        time.sleep(0.3)

        result = process_with_dlq(topic, dlq_topic, bootstrap_servers=bootstrap, max_messages=3)
        assert result["processed"] == 3
        assert result["dlq_count"] == 0

    def test_invalid_json_goes_to_dlq(self, unique_topic):
        bootstrap, topic = unique_topic
        dlq_topic = f"{topic}-dlq"

        from confluent_kafka.admin import AdminClient, NewTopic
        admin = AdminClient({"bootstrap.servers": bootstrap})
        admin.create_topics([NewTopic(dlq_topic, 1, 1)])
        time.sleep(0.3)

        # Injecter un message invalide
        p = Producer({"bootstrap.servers": bootstrap})
        p.produce(topic, value=b"not_json_at_all")
        p.flush(5)
        time.sleep(0.3)

        result = process_with_dlq(topic, dlq_topic, bootstrap_servers=bootstrap, max_messages=1)
        assert result["dlq_count"] == 1
        assert result["processed"] == 0

    def test_negative_amount_goes_to_dlq(self, unique_topic):
        bootstrap, topic = unique_topic
        dlq_topic = f"{topic}-dlq"

        from confluent_kafka.admin import AdminClient, NewTopic
        admin = AdminClient({"bootstrap.servers": bootstrap})
        admin.create_topics([NewTopic(dlq_topic, 1, 1)])
        time.sleep(0.3)

        # Message avec montant négatif (règle métier)
        p = Producer({"bootstrap.servers": bootstrap})
        p.produce(topic, value=json.dumps({"order_id": 99, "amount": -5.0}).encode())
        p.flush(5)
        time.sleep(0.3)

        result = process_with_dlq(topic, dlq_topic, bootstrap_servers=bootstrap, max_messages=1)
        assert result["dlq_count"] == 1

    def test_dlq_message_has_headers(self, unique_topic):
        """Vérifie que les messages DLQ contiennent les métadonnées."""
        bootstrap, topic = unique_topic
        dlq_topic = f"{topic}-dlq"

        from confluent_kafka.admin import AdminClient, NewTopic
        admin = AdminClient({"bootstrap.servers": bootstrap})
        admin.create_topics([NewTopic(dlq_topic, 1, 1)])
        time.sleep(0.3)

        # Envoyer vers la DLQ manuellement
        dlq_producer = Producer({"bootstrap.servers": bootstrap})
        send_to_dlq(
            dlq_producer,
            dlq_topic,
            b"original_message",
            reason="test_reason",
            source_topic=topic,
            source_offset=42,
        )
        dlq_producer.flush(5)
        time.sleep(0.3)

        # Lire le message DLQ et vérifier les headers
        conf = {
            "bootstrap.servers": bootstrap,
            "group.id": "dlq-header-check",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        consumer = Consumer(conf)
        consumer.subscribe([dlq_topic])
        msg = consumer.poll(5.0)
        consumer.close()

        assert msg is not None
        headers = {k: v.decode() for k, v in (msg.headers() or [])}
        assert "dlq_reason" in headers
        assert headers["dlq_reason"] == "test_reason"
        assert "dlq_source_topic" in headers
        assert "dlq_source_offset" in headers
        assert headers["dlq_source_offset"] == "42"
