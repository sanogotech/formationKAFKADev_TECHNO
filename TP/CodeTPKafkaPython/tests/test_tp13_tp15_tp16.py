"""
Tests TP 13, TP 15 & TP 16 – Lag, Idempotence et Transactions
"""

import json
import time
import pytest
from confluent_kafka import Producer, Consumer

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tp13_lag import get_lag
from tp15_idempotence import produce_idempotent, produced_offsets
from tp16_transactions import (
    create_transactional_producer,
    run_successful_transaction,
    run_aborted_transaction,
    consume_committed_only,
)


# ─── TP 13 : Lag ──────────────────────────────────────────────────────────────

class TestLag:

    def test_lag_is_zero_for_fresh_consumer(self, unique_topic):
        bootstrap, topic = unique_topic

        # Produire 3 messages
        p = Producer({"bootstrap.servers": bootstrap})
        for i in range(3):
            p.produce(topic, value=f"msg_{i}".encode())
        p.flush(5)
        time.sleep(0.3)

        # Consommer tous les messages
        conf = {
            "bootstrap.servers": bootstrap,
            "group.id": "lag-test-group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        consumer = Consumer(conf)
        consumer.subscribe([topic])
        received = 0
        while received < 3:
            msg = consumer.poll(2.0)
            if msg and not msg.error():
                received += 1
                consumer.commit()
        consumer.close()
        time.sleep(0.3)

        # Le lag doit être 0 après consommation totale
        lag_info = get_lag(topic, "lag-test-group", bootstrap)
        total_lag = sum(p["lag"] for p in lag_info.values())
        assert total_lag == 0, f"Lag attendu 0, obtenu {total_lag}"

    def test_lag_equals_unconsumed_messages(self, unique_topic):
        bootstrap, topic = unique_topic

        # Produire 5 messages
        p = Producer({"bootstrap.servers": bootstrap})
        for i in range(5):
            p.produce(topic, value=f"msg_{i}".encode())
        p.flush(5)
        time.sleep(0.3)

        # Ne PAS consommer → lag attendu = 5
        lag_info = get_lag(topic, "no-consumer-group", bootstrap)
        total_lag = sum(info["lag"] for info in lag_info.values())
        assert total_lag == 5, f"Lag attendu 5, obtenu {total_lag}"

    def test_get_lag_returns_dict(self, unique_topic):
        bootstrap, topic = unique_topic
        lag_info = get_lag(topic, "any-group", bootstrap)
        assert isinstance(lag_info, dict)
        for partition_id, info in lag_info.items():
            assert isinstance(partition_id, int)
            assert "lag" in info
            assert "committed" in info
            assert "end" in info


# ─── TP 15 : Idempotence ──────────────────────────────────────────────────────

class TestIdempotence:

    def test_idempotent_producer_sends_all_messages(self, unique_topic):
        bootstrap, topic = unique_topic
        produced_offsets.clear()

        messages = [
            {"id": 1, "event": "test_A"},
            {"id": 2, "event": "test_B"},
            {"id": 3, "event": "test_C"},
        ]
        produce_idempotent(topic, messages, bootstrap_servers=bootstrap)
        assert len(produced_offsets) == 3

    def test_idempotent_producer_no_duplicate_offsets(self, unique_topic):
        bootstrap, topic = unique_topic
        produced_offsets.clear()

        messages = [{"id": i, "event": f"e{i}"} for i in range(5)]
        produce_idempotent(topic, messages, bootstrap_servers=bootstrap)

        assert len(produced_offsets) == len(set(produced_offsets)), \
            "Des offsets dupliqués ont été détectés !"


# ─── TP 16 : Transactions ─────────────────────────────────────────────────────

class TestTransactions:

    def test_committed_transaction_messages_are_visible(self, unique_topic):
        bootstrap, topic = unique_topic

        producer = create_transactional_producer(
            f"test-tx-{topic[:8]}",
            bootstrap_servers=bootstrap,
        )
        producer.init_transactions()

        messages = [
            {"id": 1, "event": "cmd_créée"},
            {"id": 2, "event": "paiement"},
        ]
        run_successful_transaction(producer, topic, messages)
        time.sleep(0.5)

        # Les messages committés doivent être lisibles
        received = consume_committed_only(topic, group_id=f"tx-check-{topic[:6]}",
                                          bootstrap_servers=bootstrap, max_messages=5)
        assert len(received) == 2
        ids = {m["id"] for m in received}
        assert ids == {1, 2}

    def test_aborted_transaction_messages_not_visible(self, unique_topic):
        bootstrap, topic = unique_topic

        producer = create_transactional_producer(
            f"test-abort-{topic[:8]}",
            bootstrap_servers=bootstrap,
        )
        producer.init_transactions()

        # Transaction annulée
        abort_msgs = [{"id": 99, "event": "should_not_appear"}]
        run_aborted_transaction(producer, topic, abort_msgs)
        time.sleep(0.5)

        # Ces messages NE doivent PAS être visibles avec read_committed
        received = consume_committed_only(topic, group_id=f"abort-check-{topic[:6]}",
                                          bootstrap_servers=bootstrap, max_messages=5)
        ids = {m.get("id") for m in received if m}
        assert 99 not in ids, "Message d'une tx annulée ne doit pas être visible"

    def test_mixed_commit_and_abort(self, unique_topic):
        bootstrap, topic = unique_topic

        producer = create_transactional_producer(
            f"test-mix-{topic[:8]}",
            bootstrap_servers=bootstrap,
        )
        producer.init_transactions()

        # TX 1 : commit (id=1, 2)
        run_successful_transaction(producer, topic, [
            {"id": 1, "val": "ok_1"},
            {"id": 2, "val": "ok_2"},
        ])

        # TX 2 : abort (id=10, 11)
        run_aborted_transaction(producer, topic, [
            {"id": 10, "val": "nope_1"},
            {"id": 11, "val": "nope_2"},
        ])

        # TX 3 : commit (id=3)
        run_successful_transaction(producer, topic, [{"id": 3, "val": "ok_3"}])
        time.sleep(0.5)

        received = consume_committed_only(topic, group_id=f"mix-check-{topic[:6]}",
                                          bootstrap_servers=bootstrap, max_messages=10)
        ids = {m["id"] for m in received}

        assert 1 in ids and 2 in ids and 3 in ids, "Les messages committés doivent être présents"
        assert 10 not in ids and 11 not in ids, "Les messages annulés ne doivent pas apparaître"
