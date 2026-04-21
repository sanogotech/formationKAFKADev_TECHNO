"""
TP 11 – Produire avec compression (lz4)
═══════════════════════════════════════════════════════════════
Objectif  : Activer la compression côté producteur pour réduire
            la bande passante et l'espace disque.
Commande  : python tp11_compression.py

💡 Essentiel à retenir
  - La compression est transparente pour le consommateur.
  - lz4 : meilleur compromis vitesse/ratio de compression.
  - snappy : encore plus rapide, moins compressé.
  - gzip/zstd : meilleur ratio, plus lent.
  - Activez toujours la compression pour des volumes > 1 Mo/s.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT

COMPRESSION_TYPES = ["none", "lz4", "snappy", "gzip"]


def produce_with_compression(
    topic: str,
    compression_type: str = "lz4",
    n_messages: int = 100,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> None:
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "compression.type": compression_type,
        "batch.size": 65536,               # 64 KB par batch
        "linger.ms": 10,                   # attendre 10ms pour agréger
    }
    producer = Producer(conf)

    payload = {"data": "x" * 512, "index": 0}  # message de ~512 octets

    for i in range(n_messages):
        payload["index"] = i
        producer.produce(topic, value=json.dumps(payload).encode())
        producer.poll(0)

    producer.flush(PRODUCER_FLUSH_TIMEOUT)
    print(f"✅ {n_messages} messages produits avec compression='{compression_type}'")


def main():
    print("=" * 50)
    print("TP 11 – Compression des messages")
    print("=" * 50)

    for ctype in ["none", "lz4", "snappy", "gzip"]:
        try:
            produce_with_compression(TOPIC_TEST, compression_type=ctype, n_messages=50)
        except Exception as e:
            print(f"   ⚠️  {ctype} : {e}")

    print()
    print("📌 Conseil : en production, lz4 ou snappy sont les meilleurs choix.")


if __name__ == "__main__":
    main()
