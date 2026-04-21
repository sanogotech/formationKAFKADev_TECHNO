"""
TP 1 – Vérifier la connexion au cluster et lister les topics
═══════════════════════════════════════════════════════════════
Objectif  : Se connecter à Kafka et afficher les topics existants.
Commande  : python tp1_list_topics.py
Résultat  : Topics existants : ['__consumer_offsets', 'tp-test', ...]

💡 Essentiel à retenir
  - AdminClient gère toutes les opérations d'administration.
  - list_topics() retourne les métadonnées complètes du cluster.
  - Une liste vide est normale sur un cluster neuf.
  - Une exception signifie un problème de connexion (vérifiez que Kafka tourne).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka.admin import AdminClient
from config import BOOTSTRAP_SERVERS, DEFAULT_TIMEOUT


def list_topics(bootstrap_servers: str = BOOTSTRAP_SERVERS) -> list[str]:
    """Retourne la liste des noms de topics."""
    conf = {"bootstrap.servers": bootstrap_servers}
    admin = AdminClient(conf)
    metadata = admin.list_topics(timeout=DEFAULT_TIMEOUT)
    return list(metadata.topics.keys())


def main():
    print("=" * 50)
    print("TP 1 – Liste des topics Kafka")
    print("=" * 50)
    try:
        topics = list_topics()
        if topics:
            print(f"✅ {len(topics)} topic(s) trouvé(s) :")
            for t in sorted(topics):
                print(f"   • {t}")
        else:
            print("ℹ️  Aucun topic (cluster neuf)")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        print(f"   Vérifiez que Kafka écoute sur {BOOTSTRAP_SERVERS}")
        raise


if __name__ == "__main__":
    main()
