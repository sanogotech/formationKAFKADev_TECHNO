"""
TP 4 – Consommer un message (depuis le début)
═══════════════════════════════════════════════════════════════
Objectif  : Lire le premier message disponible depuis 'tp-test'.
Commande  : python tp4_simple_consumer.py
Résultat  : ✅ Reçu → clé=clé1 | valeur=Bonjour Kafka ! | offset=0

💡 Essentiel à retenir
  - auto.offset.reset='earliest' : relit depuis le début si pas d'offset commité.
  - enable.auto.commit=False    : commit manuel obligatoire.
  - Toujours appeler consumer.close() (libère les ressources + commit final).
  - poll(timeout) retourne None si aucun message n'arrive dans le délai.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, GROUP_SIMPLE, DEFAULT_TIMEOUT


def consume_one(
    topic: str,
    group_id: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict | None:
    """
    Consomme un seul message.
    Retourne un dict {key, value, partition, offset} ou None.
    """
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
            print("ℹ️  Aucun message reçu dans le délai imparti.")
        elif msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print("ℹ️  Fin de partition atteinte.")
            else:
                print(f"❌ Erreur Kafka : {msg.error()}")
        else:
            result = {
                "key": msg.key().decode() if msg.key() else None,
                "value": msg.value().decode() if msg.value() else None,
                "partition": msg.partition(),
                "offset": msg.offset(),
            }
            consumer.commit()  # commit après traitement réussi
    finally:
        consumer.close()

    return result


def main():
    print("=" * 50)
    print("TP 4 – Consommateur simple")
    print("=" * 50)
    print(f"→ Lecture depuis : {TOPIC_TEST} | groupe : {GROUP_SIMPLE}")
    msg = consume_one(TOPIC_TEST, GROUP_SIMPLE)
    if msg:
        print(
            f"✅ Reçu → clé={msg['key']} | valeur={msg['value']} "
            f"| partition={msg['partition']} | offset={msg['offset']}"
        )


if __name__ == "__main__":
    main()
