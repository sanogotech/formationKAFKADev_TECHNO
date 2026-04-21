# 🐍 Formation Kafka par la pratique – Python

> **20 TPs progressifs** pour maîtriser Apache Kafka avec Python en partant de zéro.

---

## 📚 Sommaire des TPs

| #  | Fichier                        | Thème                                     |
|----|-------------------------------|-------------------------------------------|
| 01 | `tp1_list_topics.py`          | Connexion au cluster & liste des topics   |
| 02 | `tp2_create_topic.py`         | Créer un topic                            |
| 03 | `tp3_simple_producer.py`      | Produire un message simple                |
| 04 | `tp4_simple_consumer.py`      | Consommer depuis le début                 |
| 05 | `tp5_json_producer.py`        | Produire des messages JSON                |
| 06 | `tp6_json_consumer.py`        | Consommer des messages JSON               |
| 07 | `tp7_key_partitioning.py`     | Partitionnement par clé                   |
| 08 | `tp8_auto_commit.py`          | Commit automatique (à éviter)             |
| 09 | `tp9_manual_commit_loop.py`   | Boucle de consommation + commit manuel    |
| 10 | `tp10_dlq.py`                 | Dead Letter Queue                         |
| 11 | `tp11_compression.py`         | Compression lz4                           |
| 12 | `tp12_batch_consumer.py`      | Consommation par lots                     |
| 13 | `tp13_lag.py`                 | Calcul du lag consommateur                |
| 14 | `tp14_reset_offsets.py`       | Réinitialiser les offsets                 |
| 15 | `tp15_idempotence.py`         | Exactly-once – idempotence                |
| 16 | `tp16_transactions.py`        | Transactions Kafka                        |
| 17 | `tp17_timeout.py`             | Gestion des pannes / timeouts             |
| 18 | `tp18_headers_producer.py`    | En-têtes de messages (producteur)         |
| 19 | `tp19_headers_consumer.py`    | En-têtes de messages (consommateur)       |
| 20 | `tp20_avro_producer.py`       | Avro + Schema Registry                    |

---

## 📦 Prérequis

- **Python 3.9+**
- **Docker & Docker Compose** (pour lancer Kafka localement)
- **pip** (gestionnaire de paquets Python)

---

## 🚀 Démarrage rapide

### 1. Cloner / extraire le projet

```bash
unzip kafka-python-tp.zip
cd kafka-python-tp
```

### 2. Lancer Kafka avec Docker Compose

```bash
docker-compose up -d
```

Attendez ~15 secondes que Kafka soit prêt :

```bash
docker-compose logs -f kafka | grep "Kafka Server started"
```

> Le cluster expose Kafka sur `localhost:9092` et le Schema Registry sur `localhost:8081`.

### 3. Créer l'environnement virtuel Python

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## ▶️ Exécuter un TP

```bash
# Exemple : TP 1
python scripts/tp1_list_topics.py

# Exemple : TP 3 (produire un message)
python scripts/tp3_simple_producer.py

# Exemple : TP 4 (consommer)
python scripts/tp4_simple_consumer.py
```

---

## 🧪 Lancer les tests unitaires

Les tests utilisent **pytest** + **Testcontainers** (Kafka éphémère, Docker requis).

```bash
pytest tests/ -v
```

---

## 🛑 Arrêter Kafka

```bash
docker-compose down
```

---

## 📖 Structure du projet

```
kafka-python-tp/
├── README.md                   ← Ce fichier
├── requirements.txt            ← Dépendances Python
├── docker-compose.yml          ← Stack Kafka locale
├── scripts/
│   ├── config.py               ← Configuration centralisée
│   ├── tp1_list_topics.py
│   ├── tp2_create_topic.py
│   ├── ...
│   └── tp20_avro_producer.py
└── tests/
    ├── conftest.py             ← Fixtures pytest (Testcontainers)
    ├── test_tp1_tp2.py
    ├── test_tp3_tp4.py
    ├── test_tp5_tp6.py
    ├── test_tp7_tp9.py
    ├── test_tp10.py
    ├── test_tp13.py
    └── test_tp15_tp16.py
```

---

## 💡 Concepts clés

| Concept            | Résumé                                                            |
|--------------------|-------------------------------------------------------------------|
| **Topic**          | Canal de messages nommé, divisé en partitions                     |
| **Partition**      | Unité de parallélisme et d'ordre                                  |
| **Offset**         | Position d'un message dans une partition                          |
| **Consumer Group** | Ensemble de consommateurs qui se partagent les partitions         |
| **Lag**            | Écart entre le dernier message produit et le dernier lu           |
| **DLQ**            | Topic de quarantaine pour les messages en erreur                  |
| **Idempotence**    | Garantit qu'un message ne sera produit qu'une seule fois          |
| **Transaction**    | Groupe atomique de messages (exactly-once)                        |

---

## 📝 Ordre recommandé pour un débutant

1. TP1 → TP2 (administration)  
2. TP3 → TP4 (hello world producteur/consommateur)  
3. TP5 → TP6 (JSON)  
4. TP7 (clés)  
5. TP9 (boucle manuelle)  
6. TP10 (DLQ)  
7. TP13 (lag)  
8. TP15 → TP16 (exactly-once)  
9. TP20 (Avro – avancé)

---

*Formation réalisée avec ❤️ – confluent-kafka + Python*
