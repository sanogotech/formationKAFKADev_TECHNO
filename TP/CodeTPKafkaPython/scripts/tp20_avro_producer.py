"""
TP 20 – Avro + Schema Registry (format de production)
═══════════════════════════════════════════════════════════════
Objectif  : Sérialiser/désérialiser des messages avec Avro et valider
            les schémas via Confluent Schema Registry.
Commande  : python tp20_avro_producer.py   (+ tp20_avro_consumer.py)
Prérequis : pip install confluent-kafka[avro]
            Schema Registry sur localhost:8081 (docker-compose up -d)

💡 Essentiel à retenir
  - Avro est plus compact que JSON et valide le schéma automatiquement.
  - Schema Registry stocke et versionne les schémas centralement.
  - Les producteurs et consommateurs partagent la même définition de schéma.
  - L'évolution de schéma (ajout de champs optionnels) est gérée proprement.
  - En production : TOUJOURS Avro ou Protobuf plutôt que JSON brut.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from config import BOOTSTRAP_SERVERS, SCHEMA_REGISTRY_URL, TOPIC_AVRO, PRODUCER_FLUSH_TIMEOUT

# ─── Schéma Avro de l'entité "Order" ─────────────────────────────────────────
ORDER_SCHEMA = """
{
  "type": "record",
  "name": "Order",
  "namespace": "com.formation.kafka",
  "fields": [
    {"name": "order_id",  "type": "int",    "doc": "Identifiant unique de la commande"},
    {"name": "user_id",   "type": "string", "doc": "Identifiant de l'utilisateur"},
    {"name": "amount",    "type": "double", "doc": "Montant total en euros"},
    {"name": "status",    "type": {
        "type": "enum",
        "name": "OrderStatus",
        "symbols": ["CREATED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"]
      },
      "default": "CREATED"
    },
    {"name": "timestamp", "type": "long",   "doc": "Unix timestamp en millisecondes"}
  ]
}
"""


def produce_avro_messages(
    topic: str = TOPIC_AVRO,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    schema_registry_url: str = SCHEMA_REGISTRY_URL,
) -> None:
    """
    Produit des messages Avro sérialisés avec Schema Registry.
    """
    try:
        from confluent_kafka import Producer
        from confluent_kafka.serialization import SerializationContext, MessageField
        from confluent_kafka.schema_registry import SchemaRegistryClient
        from confluent_kafka.schema_registry.avro import AvroSerializer
    except ImportError:
        print("❌ Module Avro manquant.")
        print("   Installez-le avec : pip install 'confluent-kafka[avro]'")
        return

    # Connexion au Schema Registry
    sr_client = SchemaRegistryClient({"url": schema_registry_url})

    # Sérialiseur Avro
    avro_serializer = AvroSerializer(
        sr_client,
        ORDER_SCHEMA,
        conf={"auto.register.schemas": True},  # enregistre le schéma si inexistant
    )

    producer = Producer({"bootstrap.servers": bootstrap_servers})

    import time
    orders = [
        {"order_id": 1001, "user_id": "alice", "amount": 149.99,
         "status": "CREATED",   "timestamp": int(time.time() * 1000)},
        {"order_id": 1002, "user_id": "bob",   "amount": 89.50,
         "status": "PAID",      "timestamp": int(time.time() * 1000)},
        {"order_id": 1003, "user_id": "carol", "amount": 320.00,
         "status": "SHIPPED",   "timestamp": int(time.time() * 1000)},
    ]

    def delivery_report(err, msg):
        if err:
            print(f"   ❌ Erreur : {err}")
        else:
            print(f"   ✅ Avro envoyé → {msg.topic()} [{msg.partition()}] offset={msg.offset()}")

    for order in orders:
        producer.produce(
            topic=topic,
            key=str(order["order_id"]).encode(),
            value=avro_serializer(
                order,
                SerializationContext(topic, MessageField.VALUE),
            ),
            callback=delivery_report,
        )
        producer.poll(0)
        print(f"   📤 Produit : {order}")

    producer.flush(PRODUCER_FLUSH_TIMEOUT)


def consume_avro_messages(
    topic: str = TOPIC_AVRO,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    schema_registry_url: str = SCHEMA_REGISTRY_URL,
    max_messages: int = 5,
) -> list[dict]:
    """
    Consomme et désérialise des messages Avro depuis Schema Registry.
    """
    try:
        from confluent_kafka import DeserializingConsumer
        from confluent_kafka.serialization import SerializationContext, MessageField
        from confluent_kafka.schema_registry import SchemaRegistryClient
        from confluent_kafka.schema_registry.avro import AvroDeserializer
    except ImportError:
        print("❌ Module Avro manquant.")
        return []

    sr_client = SchemaRegistryClient({"url": schema_registry_url})
    avro_deserializer = AvroDeserializer(sr_client)

    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": "tp-avro-consumer",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "value.deserializer": avro_deserializer,
    }
    consumer = DeserializingConsumer(conf)
    consumer.subscribe([topic])

    messages = []
    empty_polls = 0

    while len(messages) < max_messages and empty_polls < 3:
        msg = consumer.poll(2.0)
        if msg is None:
            empty_polls += 1
            continue
        if msg.error():
            empty_polls += 1
            continue
        empty_polls = 0
        order = msg.value()
        print(f"   📥 Désérialisé : {order}")
        messages.append(order)
        consumer.commit()

    consumer.close()
    return messages


def main():
    print("=" * 50)
    print("TP 20 – Avro + Schema Registry")
    print("=" * 50)

    print(f"\n[1/2] Production de messages Avro → topic '{TOPIC_AVRO}'")
    print(f"      Schema Registry : {SCHEMA_REGISTRY_URL}")
    produce_avro_messages()

    print(f"\n[2/2] Consommation et désérialisation Avro")
    messages = consume_avro_messages()
    print(f"\n✅ {len(messages)} message(s) Avro reçu(s) et validé(s) par le schéma")
    print()
    print("📌 Bénéfices Avro vs JSON :")
    print("   • Validation de schéma automatique")
    print("   • Payload ~3x plus compact")
    print("   • Évolution de schéma gérée (backward/forward compatibility)")
    print("   • Contrat fort entre producteur et consommateur")


if __name__ == "__main__":
    main()
