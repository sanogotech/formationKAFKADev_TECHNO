"""
TP 2 – Créer un topic
═══════════════════════════════════════════════════════════════
Objectif  : Créer le topic 'tp-test' avec 3 partitions.
Commande  : python tp2_create_topic.py
Résultat  : Topic tp-test créé avec succès (3 partitions, RF=1)

💡 Essentiel à retenir
  - NewTopic(name, num_partitions, replication_factor)
  - replication_factor <= nombre de brokers (utilisez 1 en local).
  - create_topics() est asynchrone → appeler .result() pour attendre.
  - Si le topic existe déjà, une TopicAlreadyExistsException est levée.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.error import KafkaException
from config import BOOTSTRAP_SERVERS, TOPIC_TEST


def create_topic(
    topic_name: str,
    num_partitions: int = 3,
    replication_factor: int = 1,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> bool:
    """
    Crée un topic Kafka.
    Retourne True si créé, False si déjà existant.
    Lève une exception en cas d'autre erreur.
    """
    conf = {"bootstrap.servers": bootstrap_servers}
    admin = AdminClient(conf)
    new_topic = NewTopic(
        topic_name,
        num_partitions=num_partitions,
        replication_factor=replication_factor,
    )
    futures = admin.create_topics([new_topic])
    for topic, future in futures.items():
        try:
            future.result()  # bloque jusqu'à confirmation
            return True
        except KafkaException as e:
            if "already exists" in str(e).lower() or e.args[0].code().name == "TOPIC_ALREADY_EXISTS":
                return False  # pas une vraie erreur
            raise
    return False


def main():
    print("=" * 50)
    print("TP 2 – Création d'un topic")
    print("=" * 50)
    topic = TOPIC_TEST
    try:
        created = create_topic(topic, num_partitions=3, replication_factor=1)
        if created:
            print(f"✅ Topic '{topic}' créé (3 partitions, replication_factor=1)")
        else:
            print(f"ℹ️  Topic '{topic}' existe déjà")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        raise


if __name__ == "__main__":
    main()
