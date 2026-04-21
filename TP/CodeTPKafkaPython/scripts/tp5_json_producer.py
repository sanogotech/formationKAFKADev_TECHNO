"""
TP 5 – Produire des messages JSON
═══════════════════════════════════════════════════════════════
Objectif  : Sérialiser un objet Python en JSON et l'envoyer dans Kafka.
Commande  : python tp5_json_producer.py
Résultat  : ✅ Message JSON envoyé : {"order_id": 123, "user": "alice", "amount": 99.9}

💡 Essentiel à retenir
  - JSON est simple mais sans évolution de schéma ni validation.
  - Préférez Avro/Protobuf + Schema Registry en production (TP 20).
  - Encodez toujours en UTF-8 avant d'appeler produce().
  - La clé doit aussi être encodée en bytes.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT


def produce_json(
    topic: str,
    key: str,
    payload: dict,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> None:
    """Sérialise payload en JSON et le produit dans le topic."""
    conf = {"bootstrap.servers": bootstrap_servers}
    producer = Producer(conf)

    serialized = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    producer.produce(topic, key=key.encode("utf-8"), value=serialized)
    producer.flush(PRODUCER_FLUSH_TIMEOUT)
    print(f"✅ Message JSON envoyé : {json.dumps(payload, ensure_ascii=False)}")


def main():
    print("=" * 50)
    print("TP 5 – Producteur JSON")
    print("=" * 50)

    # Exemple de commande e-commerce
    order = {
        "order_id": 123,
        "user": "alice",
        "amount": 99.90,
        "items": ["livre", "stylo"],
    }
    produce_json(TOPIC_TEST, key="order_123", payload=order)

    # Second message
    order2 = {"order_id": 124, "user": "bob", "amount": 45.00, "items": ["cahier"]}
    produce_json(TOPIC_TEST, key="order_124", payload=order2)


if __name__ == "__main__":
    main()
