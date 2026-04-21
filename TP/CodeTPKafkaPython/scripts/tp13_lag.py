"""
TP 13 – Calculer le lag d'un consumer group
═══════════════════════════════════════════════════════════════
Objectif  : Mesurer l'écart (lag) entre la fin du topic et la position
            du consommateur pour détecter un retard de traitement.
Commande  : python tp13_lag.py

💡 Essentiel à retenir
  - Lag = high_watermark_offset - committed_offset.
  - Un lag > 0 signifie des messages non encore traités.
  - Alertez si le lag dépasse un seuil (ex: > 10 000).
  - Utilisez Prometheus/Grafana pour monitorer le lag en continu.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Consumer, TopicPartition
from config import BOOTSTRAP_SERVERS, TOPIC_TEST, GROUP_LAG, GROUP_BOUCLE


def get_lag(
    topic: str,
    group_id: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> dict:
    """
    Calcule le lag par partition pour un consumer group.
    Retourne : {partition_id: {"committed": int, "end": int, "lag": int}}
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
    }
    consumer = Consumer(conf)

    # Récupérer les métadonnées du topic
    metadata = consumer.list_topics(topic, timeout=5)
    topic_meta = metadata.topics.get(topic)
    if topic_meta is None:
        consumer.close()
        return {}

    # Construire la liste des TopicPartition
    partitions = [
        TopicPartition(topic, p_id)
        for p_id in topic_meta.partitions.keys()
    ]

    lag_info = {}

    for tp in partitions:
        # High watermark (dernier offset + 1)
        low, high = consumer.get_watermark_offsets(tp, timeout=5)

        # Offset commité par le groupe
        committed = consumer.committed([tp], timeout=5)
        committed_offset = committed[0].offset if committed and committed[0].offset >= 0 else 0

        lag = max(0, high - committed_offset)
        lag_info[tp.partition] = {
            "committed": committed_offset,
            "end": high,
            "lag": lag,
        }

    consumer.close()
    return lag_info


def main():
    print("=" * 50)
    print("TP 13 – Calcul du lag consommateur")
    print("=" * 50)

    for group in [GROUP_BOUCLE, GROUP_LAG, "tp-group", "tp-group-json"]:
        print(f"\n📊 Groupe : '{group}' | Topic : '{TOPIC_TEST}'")
        lag_info = get_lag(TOPIC_TEST, group)
        if not lag_info:
            print("   ⚠️  Topic introuvable ou aucune partition.")
            continue

        total_lag = 0
        for partition, info in sorted(lag_info.items()):
            status = "🟢" if info["lag"] == 0 else ("🟡" if info["lag"] < 1000 else "🔴")
            print(
                f"   {status} Partition {partition} : "
                f"committed={info['committed']}, end={info['end']}, "
                f"lag={info['lag']}"
            )
            total_lag += info["lag"]

        print(f"   → Lag total : {total_lag}")
        if total_lag > 10000:
            print("   🚨 ALERTE : lag > 10 000 !")


if __name__ == "__main__":
    main()
