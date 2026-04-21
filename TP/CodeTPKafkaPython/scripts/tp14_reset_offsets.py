"""
TP 14 – Réinitialiser les offsets (rejouer depuis le début)
═══════════════════════════════════════════════════════════════
Objectif  : Forcer un consumer group à relire tous les messages
            depuis le début du topic.
Commande  : python tp14_reset_offsets.py

⚠️  OPÉRATION DANGEREUSE EN PRODUCTION
    Cela relit TOUT l'historique du topic.
    Assurez-vous que votre traitement est idempotent avant de l'utiliser.

💡 Essentiel à retenir
  - Utile pour rejouer après un bug ou lors d'une migration.
  - Le groupe doit être inactif (aucun consommateur connecté).
  - Alternativement, utilisez kafka-consumer-groups.sh --reset-offsets.
  - Rendez votre traitement idempotent pour supporter le rejeu.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, TopicPartition, OFFSET_BEGINNING
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, GROUP_BOUCLE


def reset_offsets_to_beginning(
    topic: str,
    group_id: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    dry_run: bool = False,
) -> dict:
    """
    Réinitialise les offsets d'un consumer group à 0 (début).
    Si dry_run=True, affiche ce qui serait fait sans modifier.
    Retourne {partition: new_offset}.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
    }
    consumer = Consumer(conf)

    metadata = consumer.list_topics(topic, timeout=5)
    topic_meta = metadata.topics.get(topic)
    if not topic_meta:
        print(f"❌ Topic '{topic}' introuvable.")
        consumer.close()
        return {}

    partitions = [
        TopicPartition(topic, p_id, OFFSET_BEGINNING)
        for p_id in topic_meta.partitions.keys()
    ]

    result = {}
    for tp in partitions:
        print(f"   {'[DRY RUN] ' if dry_run else ''}Partition {tp.partition} → reset à offset 0")
        result[tp.partition] = 0

    if not dry_run:
        # Assigner les partitions et commiter l'offset 0
        consumer.assign(partitions)
        for tp in partitions:
            consumer.seek(tp)
        # Forcer le commit des nouveaux offsets
        consumer.commit(offsets=partitions)
        print("✅ Offsets réinitialisés.")
    else:
        print("ℹ️  Mode dry_run : aucune modification effectuée.")

    consumer.close()
    return result


def main():
    print("=" * 50)
    print("TP 14 – Réinitialisation des offsets")
    print("=" * 50)
    print(f"Groupe : '{GROUP_BOUCLE}' | Topic : '{TOPIC_TEST}'")
    print()

    # D'abord en mode dry_run pour voir ce qui se passerait
    print("── Simulation (dry_run=True) ──")
    reset_offsets_to_beginning(TOPIC_TEST, GROUP_BOUCLE, dry_run=True)

    print()
    print("── Réinitialisation réelle ──")
    print("⚠️  Relancez tp9_manual_commit_loop.py pour rejouer depuis le début.")
    # Décommentez la ligne suivante pour effectuer le reset :
    # reset_offsets_to_beginning(TOPIC_TEST, GROUP_BOUCLE, dry_run=False)
    print("ℹ️  Reset commenté pour éviter une opération non intentionnelle.")
    print("   Décommentez la ligne dans main() pour l'exécuter réellement.")


if __name__ == "__main__":
    main()
