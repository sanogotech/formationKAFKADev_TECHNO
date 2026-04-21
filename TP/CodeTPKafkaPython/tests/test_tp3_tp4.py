"""
Tests TP 3 & TP 4 – Producteur et consommateur simples
"""

import time
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tp3_simple_producer import produce_message
from tp4_simple_consumer import consume_one


class TestSimpleProducer:

    def test_produce_single_message(self, unique_topic):
        bootstrap, topic = unique_topic
        # Ne doit pas lever d'exception
        produce_message(topic, key="k1", value="hello", bootstrap_servers=bootstrap)

    def test_produce_then_consume(self, unique_topic):
        bootstrap, topic = unique_topic
        produce_message(topic, key="k1", value="test_value", bootstrap_servers=bootstrap)
        time.sleep(0.5)
        msg = consume_one(topic, group_id="test-group-1", bootstrap_servers=bootstrap, timeout=5.0)
        assert msg is not None, "Le consommateur doit recevoir un message"
        assert msg["value"] == "test_value"
        assert msg["key"] == "k1"

    def test_produce_multiple_messages(self, unique_topic):
        bootstrap, topic = unique_topic
        for i in range(5):
            produce_message(topic, key=f"k{i}", value=f"msg_{i}", bootstrap_servers=bootstrap)
        time.sleep(0.5)

        from confluent_kafka import Consumer
        conf = {
            "bootstrap.servers": bootstrap,
            "group.id": "test-multi",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        consumer = Consumer(conf)
        consumer.subscribe([topic])
        received = []
        empty = 0
        while len(received) < 5 and empty < 3:
            msg = consumer.poll(2.0)
            if msg is None:
                empty += 1
            elif not msg.error():
                received.append(msg.value().decode())
                empty = 0
        consumer.close()
        assert len(received) == 5


class TestSimpleConsumer:

    def test_consume_returns_none_on_empty_topic(self, unique_topic):
        bootstrap, topic = unique_topic
        result = consume_one(topic, group_id="empty-group", bootstrap_servers=bootstrap, timeout=1.0)
        assert result is None

    def test_consume_returns_correct_fields(self, unique_topic):
        bootstrap, topic = unique_topic
        produce_message(topic, key="mykey", value="myvalue", bootstrap_servers=bootstrap)
        time.sleep(0.5)
        msg = consume_one(topic, group_id="field-check", bootstrap_servers=bootstrap, timeout=5.0)
        assert msg is not None
        assert "key" in msg
        assert "value" in msg
        assert "partition" in msg
        assert "offset" in msg
        assert msg["offset"] >= 0

    def test_consume_offset_starts_at_zero_for_new_group(self, unique_topic):
        bootstrap, topic = unique_topic
        produce_message(topic, key="k0", value="first_msg", bootstrap_servers=bootstrap)
        time.sleep(0.3)
        msg = consume_one(topic, group_id="fresh-group", bootstrap_servers=bootstrap, timeout=5.0)
        assert msg is not None
        assert msg["offset"] == 0
