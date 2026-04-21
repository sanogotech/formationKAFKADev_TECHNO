"""
TP 3 – Produire un message simple avec callback
═══════════════════════════════════════════════════════════════
Objectif  : Envoyer un message texte dans 'tp-test' avec rapport de livraison.
Commande  : python tp3_simple_producer.py
Résultat  : ✅ Message envoyé → tp-test [partition=0] offset=0

💡 Essentiel à retenir
  - Producer.produce() est non-bloquant (fire and forget).
  - Le callback delivery_report confirme (ou infirme) la livraison.
  - flush() vide le buffer interne et attend toutes les confirmations.
  - Sans flush(), les messages peuvent être perdus à la fin du script.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT


# ─── Callback de livraison ────────────────────────────────────────────────────
def delivery_report(err, msg):
    """Appelé par Kafka une fois le message stocké (ou en erreur)."""
    if err:
        print(f"   ❌ Erreur de livraison : {err}")
    else:
        print(
            f"   ✅ Message envoyé → {msg.topic()} "
            f"[partition={msg.partition()}] offset={msg.offset()}"
        )


def produce_message(
    topic: str,
    key: str,
    value: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> None:
    """Produit un message unique et attend la confirmation."""
    conf = {"bootstrap.servers": bootstrap_servers}
    producer = Producer(conf)
    producer.produce(topic, key=key.encode(), value=value.encode(), callback=delivery_report)
    # poll() déclenche les callbacks déjà prêts
    producer.poll(0)
    # flush() s'assure que tout est bien envoyé
    producer.flush(PRODUCER_FLUSH_TIMEOUT)


def main():
    print("=" * 50)
    print("TP 3 – Producteur simple")
    print("=" * 50)
    print(f"→ Envoi vers le topic : {TOPIC_TEST}")
    produce_message(
        topic=TOPIC_TEST,
        key="clé1",
        value="Bonjour Kafka ! 🎉",
    )


if __name__ == "__main__":
    main()
