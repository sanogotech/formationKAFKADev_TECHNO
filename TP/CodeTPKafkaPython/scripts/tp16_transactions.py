"""
TP 16 – Transactions Kafka (exactly-once end-to-end)
═══════════════════════════════════════════════════════════════
Objectif  : Grouper plusieurs messages dans une transaction atomique :
            soit tous sont visibles, soit aucun (en cas de rollback).
Commande  : python tp16_transactions.py

💡 Essentiel à retenir
  - transactional.id doit être unique par instance producteur.
  - init_transactions() → begin_transaction() → produce() × N → commit_transaction().
  - abort_transaction() annule tous les messages du batch.
  - Côté consommateur : isolation.level=read_committed (ne lit que les tx committées).
  - Les transactions ont un coût en latence (~20-50 ms) → batch autant que possible.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from confluent_kafka import Producer, Consumer, KafkaException
from config import BOOTSTRAP_SERVERS, TOPIC_TX, TOPIC_TEST, PRODUCER_FLUSH_TIMEOUT


# ─── Producteur transactionnel ────────────────────────────────────────────────

def create_transactional_producer(
    transactional_id: str,
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
) -> Producer:
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "transactional.id": transactional_id,
        "enable.idempotence": True,
        "acks": "all",
    }
    return Producer(conf)


def run_successful_transaction(
    producer: Producer,
    topic: str,
    messages: list[dict],
) -> None:
    """Exécute une transaction qui se termine avec succès (commit)."""
    print("   🟢 Démarrage de la transaction…")
    producer.begin_transaction()

    try:
        for msg in messages:
            producer.produce(
                topic,
                key=str(msg["id"]).encode(),
                value=json.dumps(msg).encode(),
            )
            print(f"      📤 Produit (dans tx) : {msg}")

        producer.commit_transaction()
        print("   ✅ Transaction COMMITÉE – tous les messages sont visibles")

    except KafkaException as e:
        print(f"   ❌ Erreur Kafka : {e}")
        producer.abort_transaction()
        print("   🔴 Transaction ANNULÉE")
        raise


def run_aborted_transaction(
    producer: Producer,
    topic: str,
    messages: list[dict],
) -> None:
    """Exécute une transaction qui se termine par un rollback (abort)."""
    print("   🟡 Démarrage d'une transaction qui sera annulée…")
    producer.begin_transaction()

    try:
        for msg in messages:
            producer.produce(
                topic,
                key=str(msg["id"]).encode(),
                value=json.dumps(msg).encode(),
            )
            print(f"      📤 Produit (dans tx) : {msg}")

        # Simulation d'une erreur métier → rollback
        raise ValueError("Erreur métier simulée → annulation de la transaction")

    except ValueError as e:
        print(f"   ⚠️  {e}")
        producer.abort_transaction()
        print("   🔴 Transaction ANNULÉE – les messages ne sont PAS visibles")


# ─── Consommateur transactionnel ─────────────────────────────────────────────

def consume_committed_only(
    topic: str,
    group_id: str = "tp-tx-consumer",
    bootstrap_servers: str = BOOTSTRAP_SERVERS,
    max_messages: int = 10,
) -> list[dict]:
    """
    Consomme uniquement les messages des transactions committées.
    isolation.level=read_committed est la clé.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "isolation.level": "read_committed",   # ← NE lit pas les tx en cours ou annulées
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])

    messages = []
    empty_polls = 0

    while len(messages) < max_messages and empty_polls < 3:
        msg = consumer.poll(1.0)
        if msg is None:
            empty_polls += 1
            continue
        if msg.error():
            continue
        empty_polls = 0
        data = json.loads(msg.value().decode())
        messages.append(data)
        consumer.commit()

    consumer.close()
    return messages


def main():
    print("=" * 50)
    print("TP 16 – Transactions Kafka")
    print("=" * 50)

    producer = create_transactional_producer("tp16-producer-001")
    producer.init_transactions()

    # ── Transaction 1 : commit ────────────────────────────────────────
    print("\n[1/2] Transaction avec COMMIT")
    run_successful_transaction(producer, TOPIC_TEST, [
        {"id": 10, "event": "cmd_créée", "montant": 150.0},
        {"id": 11, "event": "stock_réservé", "produit": "A42"},
        {"id": 12, "event": "paiement_initié", "montant": 150.0},
    ])

    # ── Transaction 2 : abort ─────────────────────────────────────────
    print("\n[2/2] Transaction avec ABORT")
    run_aborted_transaction(producer, TOPIC_TEST, [
        {"id": 20, "event": "cmd_créée", "montant": 999.0},
        {"id": 21, "event": "stock_réservé", "produit": "B99"},
    ])

    # ── Vérification côté consommateur ───────────────────────────────
    print("\n[Vérification] Lecture avec isolation.level=read_committed")
    committed_messages = consume_committed_only(TOPIC_TEST)
    print(f"   📥 {len(committed_messages)} message(s) visible(s) (tx committées uniquement)")

    # Les messages de la tx annulée (id=20, 21) ne doivent PAS apparaître
    aborted_ids = {m["id"] for m in committed_messages if m.get("id") in [20, 21]}
    if aborted_ids:
        print(f"   ⚠️  Messages de la tx annulée visibles : {aborted_ids}")
    else:
        print("   ✅ Messages de la tx annulée correctement masqués")


if __name__ == "__main__":
    main()
