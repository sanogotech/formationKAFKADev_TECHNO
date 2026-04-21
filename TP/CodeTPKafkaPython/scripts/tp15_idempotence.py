"""
TP 15 – Exactly-once : idempotence producteur
═══════════════════════════════════════════════════════════════
Objectif  : Activer l'idempotence pour garantir qu'un message
            n'est jamais dupliqué même en cas de retry réseau.
Commande  : python tp15_idempotence.py

💡 Essentiel à retenir
  - enable.idempotence=True      : chaque message a un n° de séquence unique.
  - acks='all'                   : attendre la confirmation de tous les ISR.
  - retries=10 (ou plus)         : retry automatique en cas d'échec réseau.
  - max.in.flight.requests.per.connection=5 max (avec idempotence).
  - L'idempotence est la 1ère brique de l'exactly-once.
  - Pour l'exactly-once complet (producteur + consommateur) → TP 16.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer, KafkaException
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT

produced_offsets = []


def delivery_report(err, msg):
    if err:
        print(f"   ❌ Erreur : {err}")
    else:
        produced_offsets.append(msg.offset())
        print(
            f"   ✅ Message idempotent envoyé → "
            f"partition={msg.partition()} | offset={msg.offset()}"
        )


def produce_idempotent(
    topic: str,
    messages: list[dict],
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> None:
    """
    Produit des messages avec idempotence activée.
    Chaque message ne sera stocké qu'UNE SEULE FOIS dans Kafka,
    même si le réseau retransmet la requête.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        # ─── Idempotence ──────────────────────────────────────────────
        "enable.idempotence": True,
        "acks": "all",                              # toutes les répliques
        "retries": 10,                              # retry automatique
        "max.in.flight.requests.per.connection": 5, # max autorisé avec idempotence
        # ─── Performances ────────────────────────────────────────────
        "linger.ms": 5,
        "batch.size": 32768,
    }

    try:
        producer = Producer(conf)
    except KafkaException as e:
        print(f"❌ Impossible de créer le producteur : {e}")
        raise

    for msg in messages:
        producer.produce(
            topic,
            key=str(msg.get("id", "")).encode(),
            value=json.dumps(msg).encode(),
            callback=delivery_report,
        )
        producer.poll(0)

    producer.flush(PRODUCER_FLUSH_TIMEOUT)


def main():
    print("=" * 50)
    print("TP 15 – Idempotence (exactly-once producteur)")
    print("=" * 50)

    messages = [
        {"id": 1, "event": "paiement", "montant": 100.0},
        {"id": 2, "event": "paiement", "montant": 250.0},
        {"id": 3, "event": "remboursement", "montant": -50.0},
    ]

    print(f"→ Envoi de {len(messages)} messages avec idempotence activée")
    produce_idempotent(TOPIC_TEST, messages)

    # Vérifier l'unicité des offsets (pas de doublon)
    duplicates = len(produced_offsets) != len(set(produced_offsets))
    print()
    print(f"📊 Offsets produits : {produced_offsets}")
    if duplicates:
        print("⚠️  DOUBLONS détectés ! (ne devrait pas arriver avec idempotence)")
    else:
        print("✅ Aucun doublon – idempotence confirmée")


if __name__ == "__main__":
    main()
