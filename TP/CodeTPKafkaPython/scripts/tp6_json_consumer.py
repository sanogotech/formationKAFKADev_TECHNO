"""
TP 6 – Consommer des messages JSON
═══════════════════════════════════════════════════════════════
Objectif  : Lire et désérialiser un message JSON depuis Kafka.
Commande  : python tp6_json_consumer.py
Résultat  : ✅ Commande reçue : {'order_id': 123, 'user': 'alice', 'amount': 99.9, ...}

💡 Essentiel à retenir
  - Toujours entourer json.loads() d'un try/except (message malformé).
  - En cas d'erreur de parsing, envoyez le message vers une DLQ (TP 10).
  - Committez APRÈS traitement réussi, jamais avant.
  - Loggez l'offset pour faciliter le débogage.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, GROUP_JSON, DEFAULT_TIMEOUT


def consume_json_one(
    topic: str,
    group_id: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict | None:
    """Consomme un message et le désérialise depuis JSON."""
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])
    result = None
    try:
        msg = consumer.poll(timeout)
        if msg is None:
            print("ℹ️  Aucun message.")
            return None
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print(f"❌ Erreur Kafka : {msg.error()}")
            return None

        # ─── Désérialisation JSON ─────────────────────────────────────
        try:
            data = json.loads(msg.value().decode("utf-8"))
            print(
                f"✅ Commande reçue (partition={msg.partition()}, "
                f"offset={msg.offset()}) : {data}"
            )
            result = data
            consumer.commit()
        except json.JSONDecodeError as e:
            print(f"❌ Message JSON invalide à l'offset {msg.offset()} : {e}")
            print("   → À envoyer vers une DLQ (voir TP 10)")
            consumer.commit()  # on skip ce message

    finally:
        consumer.close()

    return result


def main():
    print("=" * 50)
    print("TP 6 – Consommateur JSON")
    print("=" * 50)
    print(f"→ Lecture depuis : {TOPIC_TEST} | groupe : {GROUP_JSON}")
    consume_json_one(TOPIC_TEST, GROUP_JSON)


if __name__ == "__main__":
    main()
