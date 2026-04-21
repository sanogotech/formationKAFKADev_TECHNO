"""
Tests TP 7 & TP 9 – Partitionnement par clé & boucle de consommation
"""

import time
import pytest
from confluent_kafka import Consumer

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tp7_key_partitioning import produce_with_keys, sent_partitions
from tp9_manual_commit_loop import consume_loop


class TestKeyPartitioning:

    def test_same_key_goes_to_same_partition(self, unique_topic):
        bootstrap, topic = unique_topic
        # Vider le dictionnaire global entre tests
        sent_partitions.clear()

        produce_with_keys(topic, bootstrap_servers=bootstrap)
        time.sleep(0.3)

        # user123 doit être dans une seule partition
        assert "user123" in sent_partitions, "La clé user123 doit avoir été envoyée"
        partitions_used = sent_partitions["user123"]
        assert len(partitions_used) == 1, (
            f"user123 doit être dans 1 seule partition, trouvé : {partitions_used}"
        )

    def test_different_keys_may_go_to_different_partitions(self, unique_topic):
        bootstrap, topic = unique_topic
        sent_partitions.clear()

        produce_with_keys(topic, bootstrap_servers=bootstrap)
        time.sleep(0.3)

        # Les deux clés doivent être présentes
        assert "user123" in sent_partitions
        assert "user456" in sent_partitions

        # Les deux clés peuvent avoir des partitions différentes (hash différent)
        p123 = sent_partitions["user123"]
        p456 = sent_partitions["user456"]
        # Ce n'est pas garanti mais c'est probable avec 3 partitions
        # On vérifie juste que les deux sets sont d'un seul élément chacun
        assert len(p123) == 1
        assert len(p456) == 1

    def test_total_messages_produced(self, unique_topic):
        bootstrap, topic = unique_topic
        sent_partitions.clear()

        produce_with_keys(topic, bootstrap_servers=bootstrap)
        time.sleep(0.5)

        # 5 messages user123 + 3 messages user456 = 8 messages
        conf = {
            "bootstrap.servers": bootstrap,
            "group.id": "partition-count",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        consumer = Consumer(conf)
        consumer.subscribe([topic])
        count = 0
        empty = 0
        while empty < 3:
            msg = consumer.poll(1.0)
            if msg is None:
                empty += 1
            elif not msg.error():
                count += 1
                empty = 0
        consumer.close()
        assert count == 8, f"Attendu 8 messages, reçu {count}"


class TestManualCommitLoop:

    def test_consume_loop_processes_messages(self, unique_topic):
        bootstrap, topic = unique_topic

        # Produire des messages de test
        from confluent_kafka import Producer
        p = Producer({"bootstrap.servers": bootstrap})
        for i in range(4):
            p.produce(topic, value=f"msg_{i}".encode())
        p.flush(5)
        time.sleep(0.3)

        # La boucle doit traiter exactement 4 messages et s'arrêter
        count = consume_loop(
            topic,
            group_id="loop-test",
            bootstrap_servers=bootstrap,
            max_messages=4,
        )
        assert count == 4

    def test_consume_loop_returns_zero_on_empty_topic(self, unique_topic):
        bootstrap, topic = unique_topic
        count = consume_loop(
            topic,
            group_id="loop-empty",
            bootstrap_servers=bootstrap,
            max_messages=3,
        )
        assert count == 0
