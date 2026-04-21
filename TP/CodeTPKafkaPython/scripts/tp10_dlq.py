"""
TP 10 – Dead Letter Queue (DLQ)
═══════════════════════════════════════════════════════════════
Objectif  : Isoler les messages en erreur dans un topic dédié
            sans bloquer le flux principal.
Commande  : python tp10_dlq.py

💡 Essentiel à retenir
  - La DLQ isole les messages problématiques.
  - Le flux principal continue même si un message est invalide.
  - Ajoutez des headers dans la DLQ (raison, timestamp, topic source).
  - Prévoyez un outil de rejeu pour la DLQ (reprocessing).
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, Producer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, TOPIC_DLQ, DEFAULT_TIMEOUT


def send_to_dlq(
    dlq_producer: Producer,
    dlq_topic: str,
    original_value: bytes,
    reason: str,
    source_topic: str,
    source_offset: int,
) -> None:
    """Envoie un message vers la DLQ avec métadonnées."""
    headers = [
        ("dlq_reason", reason.encode()),
        ("dlq_source_topic", source_topic.encode()),
        ("dlq_source_offset", str(source_offset).encode()),
    ]
    dlq_producer.produce(
        dlq_topic,
        value=original_value,
        headers=headers,
    )
    dlq_producer.poll(0)
    print(f"   ⚠️  Message envoyé vers DLQ '{dlq_topic}' (raison: {reason})")


def process_with_dlq(
    topic: str,
    dlq_topic: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    max_messages: int = 5,
) -> dict:
    """
    Traite les messages avec gestion DLQ.
    Retourne un résumé {processed, dlq_count}.
    """
    consumer_conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": "tp-dlq-group",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    consumer = Consumer(consumer_conf)
    dlq_producer = Producer({"bootstrap.servers": bootstrap_servers})
    consumer.subscribe([topic])

    processed = 0
    dlq_count = 0
    count = 0

    try:
        while count < max_messages:
            msg = consumer.poll(DEFAULT_TIMEOUT)
            if msg is None:
                print("   ℹ️  Plus de messages disponibles.")
                break
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    break
                continue

            count += 1
            value_bytes = msg.value() or b""
            print(f"\n   📥 Message #{count} (offset={msg.offset()})")

            # ─── Simulation d'un traitement métier ───────────────────
            try:
                text = value_bytes.decode("utf-8")
                data = json.loads(text)

                # Règle métier : on rejette les montants négatifs
                if data.get("amount", 0) < 0:
                    raise ValueError(f"Montant négatif interdit : {data['amount']}")

                print(f"   ✅ Traitement OK : {data}")
                consumer.commit()
                processed += 1

            except json.JSONDecodeError as e:
                send_to_dlq(dlq_producer, dlq_topic, value_bytes, f"JSON invalide: {e}", topic, msg.offset())
                consumer.commit()
                dlq_count += 1

            except ValueError as e:
                send_to_dlq(dlq_producer, dlq_topic, value_bytes, str(e), topic, msg.offset())
                consumer.commit()
                dlq_count += 1

    finally:
        dlq_producer.flush(5)
        consumer.close()

    return {"processed": processed, "dlq_count": dlq_count}


def seed_messages(bootstrap_servers: str = BOOTSTRAP_SERVERS) -> None:
    """Produit quelques messages dont certains sont invalides."""
    producer = Producer({"bootstrap.servers": bootstrap_servers})
    messages = [
        ("order_1", json.dumps({"order_id": 1, "amount": 50.0})),
        ("order_2", "message_pas_json"),                          # → DLQ
        ("order_3", json.dumps({"order_id": 3, "amount": -10.0})),  # → DLQ
        ("order_4", json.dumps({"order_id": 4, "amount": 200.0})),
        ("order_5", json.dumps({"order_id": 5, "amount": 0.01})),
    ]
    for key, value in messages:
        producer.produce(TOPIC_TEST, key=key, value=value)
    producer.flush(10)
    print(f"   ✅ {len(messages)} messages de test produits (dont 2 invalides)")


def main():
    print("=" * 50)
    print("TP 10 – Dead Letter Queue")
    print("=" * 50)

    print("\n[1/2] Injection de messages de test…")
    seed_messages()

    print("\n[2/2] Consommation avec gestion DLQ…")
    result = process_with_dlq(TOPIC_TEST, TOPIC_DLQ)

    print("\n─" * 26)
    print(f"📊 Résumé : {result['processed']} traité(s), {result['dlq_count']} → DLQ")


if __name__ == "__main__":
    main()
