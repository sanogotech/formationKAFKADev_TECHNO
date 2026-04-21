"""
TP 17 – Simuler une panne réseau et gérer les timeouts
═══════════════════════════════════════════════════════════════
Objectif  : Configurer les timeouts producteur et gérer les erreurs
            de livraison en cas de panne réseau.
Commande  : python tp17_timeout.py

💡 Essentiel à retenir
  - delivery.timeout.ms : temps total max avant abandon (inclus les retries).
  - request.timeout.ms  : timeout par tentative individuelle.
  - message.timeout.ms  : alias de delivery.timeout.ms (API plus ancienne).
  - retry.backoff.ms    : délai entre deux retries.
  - En cas d'erreur définitive, le callback reçoit err != None.
  - Loggez toutes les erreurs de delivery pour audit.
"""

import json
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT

delivery_results = {"ok": 0, "error": 0}


def delivery_report_with_retry_info(err, msg):
    """Callback enrichi qui loggue les détails d'erreur."""
    if err:
        delivery_results["error"] += 1
        print(f"   ❌ Échec de livraison : {err.str()} (code={err.code().name})")
        # Codes d'erreur courants :
        # _MSG_TIMED_OUT   : delivery.timeout.ms dépassé
        # _UNKNOWN_TOPIC   : topic inexistant
        # _UNKNOWN_PARTITION : partition invalide
    else:
        delivery_results["ok"] += 1
        print(
            f"   ✅ Livré → {msg.topic()} "
            f"[{msg.partition()}] offset={msg.offset()} "
            f"latency={msg.latency():.3f}s"
        )


def produce_with_timeout_config(
    topic: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    delivery_timeout_ms: int = 5000,
    request_timeout_ms: int = 2000,
    retry_backoff_ms: int = 200,
    n_messages: int = 3,
) -> dict:
    """
    Produit des messages avec des timeouts configurables.
    Retourne le résumé {ok, error}.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        # ─── Timeouts ────────────────────────────────────────────────
        "delivery.timeout.ms": delivery_timeout_ms,  # timeout global
        "request.timeout.ms": request_timeout_ms,    # timeout par tentative
        "retry.backoff.ms": retry_backoff_ms,         # délai entre retries
        # ─── Retries ─────────────────────────────────────────────────
        "retries": 5,
        "acks": "all",
    }

    producer = Producer(conf)

    for i in range(n_messages):
        payload = {"id": i, "ts": time.time()}
        producer.produce(
            topic,
            key=f"key_{i}".encode(),
            value=json.dumps(payload).encode(),
            callback=delivery_report_with_retry_info,
        )
        producer.poll(0)

    producer.flush(PRODUCER_FLUSH_TIMEOUT)
    return dict(delivery_results)


def simulate_unreachable_broker() -> None:
    """
    Simule une connexion vers un broker inexistant
    pour observer le comportement en cas de panne.
    """
    print("\n── Simulation panne réseau (broker inexistant) ──")
    conf = {
        "bootstrap.servers": "localhost:19999",    # port inexistant
        "delivery.timeout.ms": 3000,               # abandonne après 3s
        "request.timeout.ms": 1000,
        "retries": 2,
        "socket.timeout.ms": 1000,
    }

    errors = []

    def on_delivery(err, msg):
        if err:
            errors.append(err.str())

    producer = Producer(conf)
    producer.produce("tp-test", value=b"test panne", callback=on_delivery)
    producer.flush(5)

    if errors:
        print(f"   ✅ Erreur capturée correctement : {errors[0][:80]}")
    else:
        print("   ⚠️  Aucune erreur capturée (le broker a répondu ?)")


def main():
    print("=" * 50)
    print("TP 17 – Gestion des timeouts et pannes réseau")
    print("=" * 50)

    # ── Cas normal : broker disponible ───────────────────────────────
    print("\n[1/2] Production normale avec timeouts configurés")
    result = produce_with_timeout_config(
        TOPIC_TEST,
        delivery_timeout_ms=10000,
        request_timeout_ms=3000,
    )
    print(f"   Résumé : {result['ok']} OK | {result['error']} erreur(s)")

    # ── Cas panne : broker injoignable ───────────────────────────────
    simulate_unreachable_broker()

    print()
    print("📌 Paramètres recommandés en production :")
    print("   delivery.timeout.ms = 120000  (2 min)")
    print("   request.timeout.ms  = 30000   (30 s)")
    print("   retries             = 10")
    print("   retry.backoff.ms    = 500")


if __name__ == "__main__":
    main()
