"""
TP 12 – Consommer par lots (batch consumer)
═══════════════════════════════════════════════════════════════
Objectif  : Lire plusieurs messages à la fois et les traiter en batch
            pour améliorer les performances (ex: bulk insert en base).
Commande  : python tp12_batch_consumer.py

💡 Essentiel à retenir
  - poll() dans une boucle collecte des messages un par un.
  - Regroupez-les dans une liste et committez UNE FOIS après le batch.
  - Réduisez le nombre d'appels DB/API : traitez par lots de 10-100.
  - Ajustez fetch.max.bytes et max.partition.fetch.bytes selon vos besoins.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST

BATCH_SIZE = 10
POLL_TIMEOUT = 0.5


def consume_batch(
    topic: str,
    group_id: str = "tp-batch",
    batch_size: int = BATCH_SIZE,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    max_batches: int = 3,
) -> list[list[dict]]:
    """
    Consomme les messages par lots de batch_size.
    Retourne la liste des batches traités.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        # Limite le volume récupéré par poll()
        "fetch.max.bytes": 1_048_576,        # 1 MB max par fetch
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])

    all_batches = []
    batch_num = 0

    try:
        while batch_num < max_batches:
            batch: list[dict] = []

            # ─── Collecte jusqu'à batch_size messages ─────────────────
            while len(batch) < batch_size:
                msg = consumer.poll(POLL_TIMEOUT)
                if msg is None:
                    break  # timeout → on traite ce qu'on a
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        break
                    continue
                batch.append({
                    "key": msg.key().decode() if msg.key() else None,
                    "value": msg.value().decode() if msg.value() else "",
                    "offset": msg.offset(),
                    "partition": msg.partition(),
                })

            if not batch:
                print("   ℹ️  Aucun message disponible.")
                break

            # ─── Traitement du batch ───────────────────────────────────
            batch_num += 1
            print(f"\n📦 Batch #{batch_num} ({len(batch)} messages)")
            for item in batch:
                val = item["value"][:60]
                print(f"   [{item['partition']}:{item['offset']}] {val}")

            # ─── Commit UNE FOIS pour tout le batch ───────────────────
            consumer.commit()
            print(f"   ✅ Batch #{batch_num} commité")
            all_batches.append(batch)

    finally:
        consumer.close()

    return all_batches


def main():
    print("=" * 50)
    print("TP 12 – Consommation par lots")
    print("=" * 50)
    batches = consume_batch(TOPIC_TEST)
    total = sum(len(b) for b in batches)
    print(f"\n📊 {len(batches)} batch(es) traité(s) – {total} message(s) au total")


if __name__ == "__main__":
    main()
