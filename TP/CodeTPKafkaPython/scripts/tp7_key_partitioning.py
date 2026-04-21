"""
TP 7 – Partitionnement par clé
═══════════════════════════════════════════════════════════════
Objectif  : Montrer que tous les messages avec la même clé vont dans
            la même partition (ordre garanti par clé).
Commande  : python tp7_key_partitioning.py
Résultat  : Tous les messages user123 → partition identique

💡 Essentiel à retenir
  - La partition est calculée par : hash(clé) % nb_partitions
  - Même clé = même partition = ordre préservé pour cet utilisateur.
  - Choisissez une clé métier : userId, orderId, sessionId…
  - Clé null → distribution round-robin (aucune garantie d'ordre).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT

sent_partitions = {}  # clé → ensemble de partitions observées


def delivery_report(err, msg):
    if err:
        print(f"   ❌ Erreur : {err}")
        return
    key = msg.key().decode() if msg.key() else "null"
    p = msg.partition()
    sent_partitions.setdefault(key, set()).add(p)
    print(f"   📨 Clé='{key}' → partition={p} | offset={msg.offset()}")


def produce_with_keys(
    topic: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> None:
    conf = {"bootstrap.servers": bootstrap_servers}
    producer = Producer(conf)

    # 5 messages avec la même clé (même utilisateur)
    for i in range(5):
        producer.produce(
            topic,
            key="user123",
            value=f"Événement {i} de user123",
            callback=delivery_report,
        )
        producer.poll(0)

    # 3 messages avec une clé différente
    for i in range(3):
        producer.produce(
            topic,
            key="user456",
            value=f"Événement {i} de user456",
            callback=delivery_report,
        )
        producer.poll(0)

    producer.flush(PRODUCER_FLUSH_TIMEOUT)


def main():
    print("=" * 50)
    print("TP 7 – Partitionnement par clé")
    print("=" * 50)
    produce_with_keys(TOPIC_TEST)

    print()
    print("🔍 Résumé des partitions utilisées par clé :")
    for key, partitions in sent_partitions.items():
        unique = len(partitions) == 1
        status = "✅ partition unique (ordre garanti)" if unique else "⚠️  partitions multiples"
        print(f"   Clé '{key}' → partitions {partitions} → {status}")


if __name__ == "__main__":
    main()
