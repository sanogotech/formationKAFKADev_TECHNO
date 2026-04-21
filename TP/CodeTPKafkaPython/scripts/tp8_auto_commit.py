"""
TP 8 – Commit automatique (à éviter en production)
═══════════════════════════════════════════════════════════════
Objectif  : Comprendre les risques du commit automatique.
Commande  : python tp8_auto_commit.py

⚠️  Ce TP est intentionnellement mauvais pour montrer les pièges.

💡 Essentiel à retenir
  - enable.auto.commit=True : l'offset est commité toutes les
    auto.commit.interval.ms ms, SANS attendre la fin du traitement.
  - Si le processus plante entre le commit et la fin du traitement
    → PERTE de message (le message est marqué comme lu mais pas traité).
  - Si le traitement prend plus de temps que l'intervalle
    → DOUBLONS possibles (le message est retraité après restart).
  - En production : toujours utiliser enable.auto.commit=False + commit manuel.
"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST


def main():
    print("=" * 50)
    print("TP 8 – Commit automatique (démonstration des risques)")
    print("=" * 50)

    # ─── Configuration DANGEREUSE (auto-commit activé) ────────────────
    conf = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": "tp-autocommit",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,           # ⚠️ DÉCONSEILLÉ
        "auto.commit.interval.ms": 1000,      # commit toutes les 1 seconde
    }

    consumer = Consumer(conf)
    consumer.subscribe([TOPIC_TEST])

    print("⚠️  Auto-commit activé (intervalle = 1 s)")
    print("   Simulation : traitement lent de 2 secondes par message")
    print("   → Si le process plante pendant le traitement, le message est PERDU")
    print()

    processed = 0
    try:
        msg = consumer.poll(2.0)
        if msg and not msg.error():
            print(f"   📥 Message reçu à l'offset {msg.offset()}")
            print("   ⏳ Traitement en cours (2s)…")
            # L'offset peut être commité ICI automatiquement
            # même si le traitement n'est pas terminé !
            time.sleep(2)
            print(f"   ✅ Traitement terminé – mais l'offset était peut-être déjà commité !")
            processed += 1
        else:
            print("   ℹ️  Aucun message disponible.")
    finally:
        consumer.close()

    print()
    print("─" * 50)
    print("📚 Leçon :")
    print("   1. Ne jamais utiliser enable.auto.commit=True en production.")
    print("   2. Utiliser enable.auto.commit=False + consumer.commit() après traitement.")
    print("   3. Voir TP 9 pour le pattern correct.")


if __name__ == "__main__":
    main()
