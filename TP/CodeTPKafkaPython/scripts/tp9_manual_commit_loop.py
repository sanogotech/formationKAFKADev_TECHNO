"""
TP 9 – Consommer en boucle avec commit manuel
═══════════════════════════════════════════════════════════════
Objectif  : Pattern de consommation robuste pour la production.
Commande  : python tp9_manual_commit_loop.py  (Ctrl+C pour arrêter)

💡 Essentiel à retenir
  - Pattern standard : poll() → traitement → commit().
  - try/finally garantit que consumer.close() est toujours appelé.
  - KeyboardInterrupt permet un arrêt propre.
  - Commitez APRÈS un traitement réussi, jamais avant.
  - Pour encore plus de robustesse, gérez les erreurs dans une DLQ (TP 10).
"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, KafkaError
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, GROUP_BOUCLE


def process_message(value: str, offset: int) -> None:
    """Simule un traitement métier (ex: écriture en base)."""
    print(f"   ⚙️  Traitement offset={offset} : {value[:80]}")
    time.sleep(0.1)  # simule I/O


def consume_loop(
    topic: str,
    group_id: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    max_messages: int | None = None,  # None = boucle infinie
) -> int:
    """
    Boucle de consommation avec commit manuel.
    Retourne le nombre de messages traités.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,          # ← indispensable
        "session.timeout.ms": 6000,
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])
    count = 0

    print(f"🔄 Boucle démarrée | topic={topic} | groupe={group_id}")
    print("   (Ctrl+C pour arrêter proprement)\n")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue  # pas de message, on reboucle

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue  # fin normale de partition
                print(f"❌ Erreur Kafka : {msg.error()}")
                continue

            # ─── Traitement ──────────────────────────────────────────
            value = msg.value().decode("utf-8", errors="replace") if msg.value() else ""
            try:
                process_message(value, msg.offset())
                consumer.commit()             # ← commit après succès
                count += 1
                print(f"   ✅ Commité (offset={msg.offset()}, total={count})")
            except Exception as e:
                print(f"   ❌ Erreur traitement : {e} → message ignoré")
                # En production : envoyer vers DLQ (TP 10)

            if max_messages and count >= max_messages:
                print(f"\n🏁 Limite de {max_messages} messages atteinte.")
                break

    except KeyboardInterrupt:
        print("\n⛔  Arrêt demandé (Ctrl+C)")
    finally:
        print("🔒 Fermeture du consommateur…")
        consumer.close()
        print(f"✅ Terminé – {count} message(s) traité(s)")

    return count


def main():
    print("=" * 50)
    print("TP 9 – Boucle de consommation (commit manuel)")
    print("=" * 50)
    consume_loop(TOPIC_TEST, GROUP_BOUCLE)


if __name__ == "__main__":
    main()
