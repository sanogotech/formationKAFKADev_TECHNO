"""
Tests TP 5 & TP 6 – Producteur et consommateur JSON
"""

import json
import time
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tp5_json_producer import produce_json
from tp6_json_consumer import consume_json_one
from confluent_kafka import Producer, Consumer


class TestJsonProducer:

    def test_produce_json_dict(self, unique_topic):
        bootstrap, topic = unique_topic
        payload = {"order_id": 1, "user": "alice", "amount": 50.0}
        produce_json(topic, key="order_1", payload=payload, bootstrap_servers=bootstrap)

    def test_json_is_valid_after_roundtrip(self, unique_topic):
        bootstrap, topic = unique_topic
        payload = {"order_id": 42, "user": "bob", "amount": 99.99, "items": ["a", "b"]}
        produce_json(topic, key="order_42", payload=payload, bootstrap_servers=bootstrap)
        time.sleep(0.5)

        # Lire le message brut et vérifier le JSON
        conf = {
            "bootstrap.servers": bootstrap,
            "group.id": "json-raw-check",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        consumer = Consumer(conf)
        consumer.subscribe([topic])
        msg = consumer.poll(5.0)
        consumer.close()

        assert msg is not None
        data = json.loads(msg.value().decode("utf-8"))
        assert data["order_id"] == 42
        assert data["user"] == "bob"
        assert data["amount"] == pytest.approx(99.99, rel=1e-5)
        assert data["items"] == ["a", "b"]

    def test_produce_nested_json(self, unique_topic):
        bootstrap, topic = unique_topic
        nested = {
            "id": 100,
            "metadata": {"source": "web", "version": "v2"},
            "tags": ["urgent", "vip"],
        }
        # Ne doit pas lever d'exception
        produce_json(topic, key="nested", payload=nested, bootstrap_servers=bootstrap)


class TestJsonConsumer:

    def test_consume_returns_dict(self, unique_topic):
        bootstrap, topic = unique_topic
        payload = {"order_id": 7, "user": "carol", "amount": 10.0}
        produce_json(topic, key="order_7", payload=payload, bootstrap_servers=bootstrap)
        time.sleep(0.5)

        result = consume_json_one(topic, group_id="json-consume-test",
                                  bootstrap_servers=bootstrap, timeout=5.0)
        assert result is not None
        assert isinstance(result, dict)
        assert result["order_id"] == 7

    def test_consume_handles_invalid_json_gracefully(self, unique_topic):
        bootstrap, topic = unique_topic

        # Injecter un message non-JSON
        conf = {"bootstrap.servers": bootstrap}
        producer = Producer(conf)
        producer.produce(topic, value=b"pas_du_json_{")
        producer.flush(5)
        time.sleep(0.3)

        # consume_json_one ne doit pas crasher
        try:
            consume_json_one(topic, group_id="json-invalid-test",
                             bootstrap_servers=bootstrap, timeout=3.0)
        except Exception as e:
            pytest.fail(f"consume_json_one a levé une exception inattendue : {e}")

    def test_consume_returns_none_on_empty_topic(self, unique_topic):
        bootstrap, topic = unique_topic
        result = consume_json_one(topic, group_id="empty-json",
                                  bootstrap_servers=bootstrap, timeout=1.0)
        assert result is None
