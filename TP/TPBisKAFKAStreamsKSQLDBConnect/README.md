# README - Traitement de flux (Streaming) avec Kafka et Faust

## Table des matières
1. [Présentation du TP](#présentation-du-tp)
2. [Architecture et concepts Kafka Streams](#architecture-et-concepts-kafka-streams)
3. [Prérequis et installation](#prérequis-et-installation)
4. [Structure des scripts](#structure-des-scripts)
5. [Étape par étape : exécution du TP](#étape-par-étape--exécution-du-tp)
6. [Patterns de streaming et règles d'exécution](#patterns-de-streaming-et-règles-dexécution)
7. [Cas d'usage concrets](#cas-dusage-concrets)
8. [Annexes : dépannage et bonnes pratiques](#annexes--dépannage-et-bonnes-pratiques)

---

## Présentation du TP

Ce TP a pour objectif de mettre en œuvre un **pipeline de traitement de données en temps réel** (stream processing) en utilisant :
- **Apache Kafka** comme plateforme de messagerie distribuée,
- **Faust** (bibliothèque Python) pour implémenter un traitement de flux à la manière de Kafka Streams,
- Un **producteur** qui génère des phrases texte vers un topic Kafka,
- Un **consommateur / agent Faust** qui lit ces phrases, extrait les mots et maintient un compteur global par mot.

Le résultat final : un compteur de mots qui s’incrémente en temps réel à chaque nouvelle phrase produite.

---

## Architecture et concepts Kafka Streams

### Kafka en bref
- **Topic** : flux de messages (log structuré, partitionné et répliqué).
- **Producteur** : envoie des messages sur un topic.
- **Consommateur** : lit les messages d’un topic.
- **Broker** : serveur Kafka (un cluster peut en compter plusieurs).

### Kafka Streams / Faust
Kafka Streams est une bibliothèque Java pour le traitement de flux. **Faust** en est l’équivalent Python. Les concepts clés :

| Concept | Explication |
|---------|--------------|
| **Stream** | Séquence infinie d’événements (messages) ordonnés dans le temps. |
| **Table** | Vue matérialisée d’un flux (ex: état agrégé). La table évolue à chaque nouvel événement. |
| **Agent** (Faust) | Fonction asynchrone qui consomme un flux et applique des transformations. |
| **Topologie** | Graphe de traitement : source → transformations → sink (table ou autre topic). |
| **Temps & fenêtrage** | Possibilité de regrouper les événements par fenêtres glissantes, tumbling, etc. |

Dans notre TP, nous avons un stream (`input_topic`) et une table (`counts_table`). Chaque mot produit met à jour la table.

---

## Prérequis et installation

### Matériel / logiciel nécessaire
- Python 3.8 ou supérieur
- Apache Kafka (>= 2.8) + Zookeeper (ou Kafka avec Kraft)
- pip (gestionnaire de paquets Python)

### Étapes d’installation

1. **Installer Kafka** (téléchargement et démarrage) :
   ```bash
   wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
   tar -xzf kafka_2.13-3.6.0.tgz
   cd kafka_2.13-3.6.0
   ```

2. **Démarrer Zookeeper** (nécessaire pour Kafka classique) :
   ```bash
   bin/zookeeper-server-start.sh config/zookeeper.properties
   ```

3. **Démarrer Kafka** (dans un autre terminal) :
   ```bash
   bin/kafka-server-start.sh config/server.properties
   ```

4. **Créer le topic `input`** (optionnel si auto-création activée) :
   ```bash
   bin/kafka-topics.sh --create --topic input --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
   ```

5. **Installer les dépendances Python** :
   ```bash
   pip install faust kafka-python
   ```

6. **Télécharger les deux scripts Python** :
   - `wordcount_faust.py` (agent Faust)
   - `producer.py` (producteur Kafka)

---

## Structure des scripts

### `wordcount_faust.py` – Consommateur / Agent Faust


```python
#!/usr/bin/env python3
"""
Compteur de mots en streaming avec Faust (Kafka Streams pour Python)
--------------------------------------------------------------------
Lit les messages du topic Kafka 'input', extrait les mots,
et maintient un compteur global par mot dans une table d'état.

PRÉ-REQUIS AVANT LANCEMENT :
- Kafka doit être démarré (broker localhost:9092)
- Le topic 'input' doit exister (ou auto-création activée)
- Installer les dépendances : pip install faust kafka-python

APRÈS EXÉCUTION :
- Arrêter avec Ctrl+C (Faust effectue un checkpoint)
- Pour réinitialiser le comptage, supprimer le topic interne :
  bin/kafka-topics.sh --delete --topic wordcount-python-__assignor-__global_store-wordcount --bootstrap-server localhost:9092
"""

import faust
import logging
from typing import AsyncIterable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application Faust
app = faust.App(
    'wordcount-python',
    broker='kafka://localhost:9092',
    value_serializer='raw',
    topic_partitions=3,
    topic_replication_factor=1,
    store='rocksdb://',
)

# Topic source
input_topic = app.topic('input', value_type=str)

# Table d'état (compteur par mot)
counts_table = app.Table('wordcount', default=int)

@app.agent(input_topic)
async def process(stream: AsyncIterable[str]) -> None:
    """Agent : pour chaque phrase, découpe les mots et incrémente le compteur."""
    async for value in stream:
        try:
            words = value.lower().split()
            for word in words:
                current = counts_table[word]
                counts_table[word] = current + 1
                logger.info(f"{word} : {counts_table[word]}")
        except Exception as e:
            logger.error(f"Erreur sur '{value}' : {e}")

@app.timer(interval=10.0)
async def report_status():
    """Affiche périodiquement le nombre de mots distincts suivis."""
    # Ce timer ne peut pas itérer facilement toutes les clés, on affiche juste un message
    logger.info("Statut : le compteur tourne normalement.")

if __name__ == '__main__':
    app.main()
```

- Crée une application Faust nommée `wordcount-python`.
- Définit un topic `input` de type `str`.
- Définit une table `wordcount` avec `default=int`.
- L’agent `process` lit le stream, split les mots et incrémente la table.
- Un timer optionnel affiche périodiquement l’état.

### `producer.py` – Producteur Kafka (3 modes)


```python
#!/usr/bin/env python3
"""
Producteur Kafka pour alimenter le compteur de mots Faust
---------------------------------------------------------
Envoie des messages texte vers le topic 'input'.

MODES :
- interactif : saisie manuelle des phrases
- auto : génération aléatoire à intervalle régulier
- fichier : lecture ligne à ligne d'un fichier texte

PRÉ-REQUIS :
- Kafka démarré sur localhost:9092
- pip install kafka-python

UTILISATION :
  python producer.py                          # mode interactif
  python producer.py --mode auto -i 2 -d 30   # toutes les 2s pendant 30s
  python producer.py --mode fichier -f data.txt -i 0.5
"""

import argparse
import random
import time
import sys
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

BROKER = 'localhost:9092'
TOPIC = 'input'

# Mots pour la génération aléatoire
MOTS = [
    "kafka", "stream", "faust", "python", "traitement", "données",
    "temps", "réel", "compteur", "mots", "exemple", "producteur",
    "consommateur", "topic", "partition", "broker", "message", "hello"
]

PHRASES_EXEMPLES = [
    "kafka stream processing est puissant",
    "faust simplifie le développement de streams",
    "le compteur de mots compte chaque mot",
    "python et kafka forment un bon couple",
    "le traitement en temps réel est amusant"
]

def create_producer():
    """Crée et retourne un producteur Kafka."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=BROKER,
            value_serializer=lambda v: v.encode('utf-8'),
            acks='all',
            retries=3
        )
        print(f"✅ Connecté à Kafka sur {BROKER}")
        return producer
    except NoBrokersAvailable:
        print(f"❌ Kafka indisponible sur {BROKER}. Vérifiez qu'il tourne.")
        sys.exit(1)

def send_message(producer, message):
    """Envoie un message et affiche un accusé."""
    try:
        future = producer.send(TOPIC, message)
        record = future.get(timeout=5)
        print(f"📤 Envoyé : '{message}' → partition {record.partition}, offset {record.offset}")
    except Exception as e:
        print(f"⚠️ Échec : {e}")

def interactive_mode(producer):
    """Mode interactif : l'utilisateur tape les phrases."""
    print("\n🔵 Mode interactif – Tapez vos phrases (Ctrl+C pour quitter) :")
    try:
        while True:
            text = input("> ").strip()
            if text:
                send_message(producer, text)
    except KeyboardInterrupt:
        print("\n🟡 Arrêt du mode interactif")

def auto_mode(producer, interval=2.0, duration=None):
    """Mode automatique : génération aléatoire de phrases."""
    print(f"\n🟢 Mode auto – Envoi toutes les {interval} secondes")
    start = time.time()
    count = 0
    try:
        while True:
            # Construire une phrase aléatoire
            if random.random() < 0.3:
                phrase = random.choice(PHRASES_EXEMPLES)
            else:
                nb = random.randint(3, 8)
                words = [random.choice(MOTS) for _ in range(nb)]
                phrase = " ".join(words)
            send_message(producer, phrase)
            count += 1
            if duration and (time.time() - start) >= duration:
                print(f"✅ Fin de la durée ({duration}s) – {count} messages envoyés.")
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n🟡 Arrêt manuel – {count} messages envoyés.")

def file_mode(producer, filepath, delay=1.0):
    """Mode fichier : lit un fichier et envoie chaque ligne."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"📄 Fichier '{filepath}' – {len(lines)} lignes à envoyer.")
        for i, line in enumerate(lines, 1):
            send_message(producer, line)
            time.sleep(delay)
        print("✅ Envoi terminé.")
    except FileNotFoundError:
        print(f"❌ Fichier introuvable : {filepath}")
    except Exception as e:
        print(f"❌ Erreur : {e}")

def main():
    parser = argparse.ArgumentParser(description="Producteur Kafka pour le compteur de mots Faust")
    parser.add_argument("--mode", choices=["interactif", "auto", "fichier"], default="interactif")
    parser.add_argument("-i", "--intervalle", type=float, default=2.0, help="Intervalle entre envois (secondes)")
    parser.add_argument("-d", "--duree", type=float, default=None, help="Durée totale (secondes, mode auto)")
    parser.add_argument("-f", "--fichier", type=str, help="Chemin du fichier (mode fichier)")
    args = parser.parse_args()

    print("🚀 PRODUCTEUR KAFKA")
    print(f"   Broker : {BROKER}")
    print(f"   Topic  : {TOPIC}")

    producer = create_producer()

    if args.mode == "interactif":
        interactive_mode(producer)
    elif args.mode == "auto":
        auto_mode(producer, interval=args.intervalle, duration=args.duree)
    elif args.mode == "fichier":
        if not args.fichier:
            print("❌ Mode fichier : spécifiez --fichier <chemin>")
            sys.exit(1)
        file_mode(producer, args.fichier, delay=args.intervalle)

    producer.close()
    print("🔌 Producteur fermé.")

if __name__ == "__main__":
    main()
```

- Se connecte au broker `localhost:9092`.
- Envoie des messages sur le topic `input`.
- Modes :
  - **interactif** : saisie manuelle.
  - **auto** : génération aléatoire de phrases à intervalle régulier.
  - **fichier** : lecture ligne à ligne d’un fichier texte.

---

## Étape par étape : exécution du TP

### Étape 0 : Vérifier que Kafka tourne
```bash
bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```
Vous devriez voir le topic `input` (ou rien si non créé).

### Étape 1 : Lancer l’agent Faust (consommateur)
Ouvrez un **premier terminal** :
```bash
python wordcount_faust.py worker -l info
```
Vous verrez les logs indiquant que Faust se connecte à Kafka, souscrit au topic `input`, et attend des messages.

### Étape 2 : Lancer le producteur
Ouvrez un **second terminal** et choisissez l’un des modes :

#### Mode interactif (vous tapez les phrases)
```bash
python producer.py
```
Tapez une phrase, par exemple `"Bonjour le monde"` et validez. Observez le terminal Faust : chaque mot (`bonjour`, `le`, `monde`) apparaît avec son compteur.

#### Mode automatique (génération aléatoire)
```bash
python producer.py --mode auto --intervalle 1 --duree 20
```
Cela envoie une phrase aléatoire toutes les secondes pendant 20 secondes.

#### Mode fichier (si vous avez un fichier `phrases.txt`)
```bash
echo -e "Kafka stream\nFaust est génial\nTest test" > phrases.txt
python producer.py --mode fichier --fichier phrases.txt --intervalle 0.5
```

### Étape 3 : Observer le traitement en temps réel
Dans le terminal Faust, chaque mot déclenche :
```
[INFO] Mot: 'kafka' -> nouveau compteur: 1
[INFO] Mot: 'stream' -> nouveau compteur: 1
[INFO] Mot: 'faust' -> nouveau compteur: 1
```
Si vous renvoyez `"kafka"`, le compteur passera à 2.

### Étape 4 : Arrêt et nettoyage
- Arrêtez le producteur : `Ctrl+C`.
- Arrêtez l’agent Faust : `Ctrl+C` (Faust effectue un checkpoint de la table).
- Arrêtez Kafka et Zookeeper (`Ctrl+C` dans leurs terminaux).
- (Optionnel) Supprimez les topics internes pour réinitialiser :
  ```bash
  bin/kafka-topics.sh --delete --topic wordcount-python-__assignor-__global_store-wordcount --bootstrap-server localhost:9092
  ```

---

## Patterns de streaming et règles d’exécution

### 1. Pattern **Event Sourcing** (source d’événements)
- Chaque message est un événement immuable (la phrase).
- La table `wordcount` est la **vue projetée** de tous les événements passés.

### 2. Pattern **Stateful processing** (traitement avec état)
- L’agent Faust maintient un état (la table). Cet état est sauvegardé périodiquement dans un topic interne (changelog) et stocké localement (RocksDB).  
- **Règle** : En cas de redémarrage, l’état est restauré automatiquement.

### 3. Pattern **Exactly-once semantics** (sémantique exactement une fois)
- Kafka et Faust permettent de garantir qu’un message est traité une seule fois, même en cas de panne. Dans notre TP, par défaut nous avons "au moins une fois", mais on peut configurer `processing_guarantee="exactly_once"`.

### 4. Règles d’exécution pour un stream
- **Parallélisme** : Le topic `input` a 3 partitions. Faust créera 3 instances de l’agent (une par partition) si on lance plusieurs workers. Chaque mot d’une même phrase va dans la même partition (grâce à la clé ? ici pas de clé, donc round-robin). La table est partitionnée de façon cohérente.
- **Fenêtrage** : On peut modifier le code pour compter les mots par minute : `counts_table = app.Table('wordcount', default=int, help="fenêtre de 60s")` et utiliser `.windowed()`.

### 5. Bonnes pratiques
- Toujours démarrer le consommateur **avant** le producteur pour ne pas rater de messages (Kafka conserve les messages même si consommateur absent, mais pour une démo c’est mieux).
- Utiliser des `try/except` pour éviter qu’un message corrompu n’arrête l’agent.
- Surveiller la latence avec les métriques intégrées de Faust.

---

## Cas d’usage concrets

Ce TP simple illustre des cas réels :

| Cas d’usage | Adaptation du TP |
|-------------|------------------|
| **Analyse de logs en temps réel** | Remplacer les phrases par des lignes de log. La table compte les erreurs par type. |
| **Détection de tendances Twitter** | Flux de tweets → extraction de hashtags → compteur en fenêtre glissante (5min). |
| **IoT – compteurs de capteurs** | Chaque message = `"capteur_id:valeur"`. Table pour stocker la dernière valeur. |
| **Modération de contenu** | Compter les mots interdits par utilisateur. Alerte si seuil dépassé. |
| **Recommandation e-commerce** | Stream de clics → mettre à jour un profil utilisateur (table) → envoyer au moteur de reco. |

Avec Faust, vous pouvez chaîner plusieurs agents, faire des jointures entre topics, ou encore exposer des résultats via une API web (Faust intègre un serveur web).

---

## Annexes : dépannage et bonnes pratiques

### Erreur fréquente : `NoBrokersAvailable`
**Cause** : Kafka n’est pas démarré ou le port `9092` est incorrect.  
**Solution** : Vérifiez avec `netstat -an | grep 9092`. Redémarrez Kafka.

### Erreur : `Topic 'input' does not exist`
**Cause** : Auto-création désactivée ou topic non créé.  
**Solution** : Créez-le manuellement (voir prérequis) ou activez `auto.create.topics.enable=true` dans `server.properties`.

### Perte de l’état après redémarrage
**Cause** : Le topic interne changelog a été supprimé.  
**Solution** : Pour persister l’état, ne pas supprimer les topics internes. Faust restaure automatiquement l’état depuis Kafka.

### Performance
- Pour des millions de messages, augmentez le nombre de partitions et utilisez plusieurs workers Faust :  
  `python wordcount_faust.py worker -l info --web-port=6066` (un worker par partition recommandé).
- Utilisez `store='rocksdb://'` (par défaut) qui est plus performant que la mémoire pour de grands états.

### Ressources supplémentaires
- [Documentation Faust](https://faust.readthedocs.io/)
- [Documentation Kafka](https://kafka.apache.org/documentation/streams/)
- [Kafka Python (kafka-python)](https://kafka-python.readthedocs.io/)

---

**Félicitations !** Vous avez réalisé un pipeline de streaming complet avec Kafka et Faust. Ce TP peut être étendu à des problématiques bien plus complexes (jointures, fenêtrage, détection d’anomalies). N’hésitez pas à modifier les scripts pour explorer d’autres patterns.
