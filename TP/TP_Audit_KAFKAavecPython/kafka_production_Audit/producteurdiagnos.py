from kafka import KafkaProducer
import json
import time
import random

# ==========================================
# CONFIGURATION DU PRODUCER
# ==========================================

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',

    # Sérialisation JSON → bytes
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),

    # 🔥 Envoie par batch (améliore performance)
    linger_ms=5,  # attend 5ms pour regrouper messages

    # Taille max du batch
    batch_size=16384,

    # 🔐 Fiabilité
    acks='all',  # attend confirmation de tous les brokers

    # 🔁 Retry en cas d’échec
    retries=5,

    # 🚀 Idempotence = pas de doublons
    enable_idempotence=True
)

# ==========================================
# ENVOI DES MESSAGES
# ==========================================

for i in range(100000):

    # Simulation de données métier
    data = {
        "id": i,
        "user_id": random.randint(1, 100),  # clé métier
        "amount": random.random() * 1000,
        "timestamp": time.time()
    }

    # 🔑 IMPORTANT : clé de partition
    # Permet de garantir l’ordre par utilisateur
    key = str(data["user_id"]).encode()

    producer.send(
        "tp-kafka-diagnostic",
        key=key,
        value=data
    )

    # Monitoring simple
    if i % 1000 == 0:
        print(f"[Producer] Sent {i} messages")

# Flush final
producer.flush()

print("✅ Fin envoi")