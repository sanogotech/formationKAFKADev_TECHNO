"""
TP 19 – Lire les en-têtes (headers) côté consommateur
═══════════════════════════════════════════════════════════════
Objectif  : Extraire et utiliser les headers pour router ou enrichir
            le traitement des messages.
Commande  : python tp19_headers_consumer.py
            (Exécutez d'abord tp18_headers_producer.py)

💡 Essentiel à retenir
  - msg.headers() retourne une liste de tuples [(nom, bytes), ...] ou None.
  - Toujours vérifier si headers est None avant d'itérer.
  - Les valeurs sont des bytes → decode() explicite.
  - Utilisez les headers pour le routage sans désérialiser le payload.
  - Ne stockez pas de données métier sensibles dans les headers.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, DEFAULT_TIMEOUT


def parse_headers(raw_headers) -> dict[str, str]:
    """Convertit la liste brute de headers en dictionnaire Python."""
    if not raw_headers:
        return {}
    result = {}
    for name, value in raw_headers:
        try:
            result[name] = value.decode("utf-8") if isinstance(value, bytes) else str(value)
        except UnicodeDecodeError:
            result[name] = repr(value)
    return result


def route_by_header(headers: dict, payload: dict) -> str:
    """
    Exemple de routage basé sur les headers.
    Retourne l'action à effectuer.
    """
    source  = headers.get("source", "unknown")
    tenant  = headers.get("tenant_id", "default")
    version = headers.get("schema_version", "1.0.0")

    if tenant == "tenant_acme":
        return f"[ACME] traitement prioritaire du message de {source}"
    elif version.startswith("2."):
        return f"[V2] décodage schema v2 du message de {source}"
    else:
        return f"[STANDARD] traitement standard du message de {source}"


def consume_with_headers(
    topic: str,
    group_id: str = "tp-headers-consumer",
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    max_messages: int = 6,
) -> list[dict]:
    """Consomme des messages et affiche leurs headers."""
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])

    results = []
    empty_polls = 0

    try:
        while len(results) < max_messages and empty_polls < 3:
            msg = consumer.poll(DEFAULT_TIMEOUT)

            if msg is None:
                empty_polls += 1
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    empty_polls += 1
                continue

            empty_polls = 0
            headers = parse_headers(msg.headers())

            # Décoder le payload
            try:
                payload = json.loads(msg.value().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {"raw": repr(msg.value())}

            # Affichage
            print(f"\n   📥 Message offset={msg.offset()} partition={msg.partition()}")
            if headers:
                print("   🏷️  Headers :")
                for k, v in headers.items():
                    print(f"      {k} = {v}")
            else:
                print("   🏷️  Aucun header")

            print(f"   📦 Payload : {payload}")

            # Routage basé sur les headers
            action = route_by_header(headers, payload)
            print(f"   🔀 Action  : {action}")

            consumer.commit()
            results.append({"headers": headers, "payload": payload, "action": action})

    finally:
        consumer.close()

    return results


def main():
    print("=" * 50)
    print("TP 19 – Headers consommateur")
    print("=" * 50)
    print(f"→ Lecture depuis : {TOPIC_TEST}")
    print("   (Assurez-vous d'avoir exécuté tp18_headers_producer.py avant)")

    messages = consume_with_headers(TOPIC_TEST)
    with_headers = sum(1 for m in messages if m["headers"])
    print(f"\n📊 {len(messages)} message(s) lus, {with_headers} avec headers")


if __name__ == "__main__":
    main()
