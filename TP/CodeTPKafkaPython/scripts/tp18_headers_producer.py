"""
TP 18 – Ajouter des en-têtes (headers) aux messages
═══════════════════════════════════════════════════════════════
Objectif  : Enrichir les messages Kafka avec des métadonnées (headers)
            pour le tracing, le routage ou l'audit.
Commande  : python tp18_headers_producer.py

💡 Essentiel à retenir
  - Les headers sont des paires (nom: str, valeur: bytes).
  - Ils sont transmis avec le message mais ne font pas partie du payload.
  - Utilisations courantes : trace_id, source, version, content-type, tenant_id.
  - Les valeurs sont des bytes → encoder/décoder explicitement.
  - Les headers ne sont PAS indexés par Kafka → ne les utilisez pas pour filtrer.
"""

import json
import uuid
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT


def delivery_report(err, msg):
    if err:
        print(f"   ❌ Erreur : {err}")
    else:
        headers = {k: v.decode() for k, v in (msg.headers() or [])}
        print(
            f"   ✅ Envoyé offset={msg.offset()} | "
            f"headers={headers}"
        )


def produce_with_headers(
    topic: str,
    key: str,
    payload: dict,
    headers: dict[str, str],
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> None:
    """Produit un message avec des en-têtes personnalisés."""
    conf = {"bootstrap.servers": bootstrap_servers}
    producer = Producer(conf)

    # Convertir les headers en liste de tuples (str, bytes)
    kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

    producer.produce(
        topic,
        key=key.encode("utf-8"),
        value=json.dumps(payload).encode("utf-8"),
        headers=kafka_headers,
        callback=delivery_report,
    )
    producer.flush(PRODUCER_FLUSH_TIMEOUT)


def main():
    print("=" * 50)
    print("TP 18 – Headers producteur")
    print("=" * 50)

    # ── Exemple 1 : message avec tracing ─────────────────────────────
    print("\n[1] Message avec trace ID (distributed tracing)")
    produce_with_headers(
        topic=TOPIC_TEST,
        key="order_200",
        payload={"order_id": 200, "amount": 75.0},
        headers={
            "trace_id":    str(uuid.uuid4()),
            "source":      "checkout-service",
            "content_type": "application/json",
            "version":     "v2",
        },
    )

    # ── Exemple 2 : message avec routage multi-tenant ─────────────────
    print("\n[2] Message avec tenant_id (routage multi-tenant)")
    produce_with_headers(
        topic=TOPIC_TEST,
        key="order_201",
        payload={"order_id": 201, "amount": 120.0},
        headers={
            "tenant_id":   "tenant_acme",
            "environment": "production",
            "timestamp":   str(int(time.time())),
        },
    )

    # ── Exemple 3 : message avec versioning de schéma ─────────────────
    print("\n[3] Message avec versioning de schéma")
    produce_with_headers(
        topic=TOPIC_TEST,
        key="order_202",
        payload={"order_id": 202, "user_id": 42, "total": 33.5},
        headers={
            "schema_version": "2.1.0",
            "schema_name":    "OrderEvent",
            "encoding":       "json",
        },
    )


if __name__ == "__main__":
    main()
