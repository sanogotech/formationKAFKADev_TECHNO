"""
===========================================================
KAFKA AUDIT TOOLKIT - VERSION PRODUCTION
===========================================================

Fonctionnalités :
✔ Audit du lag (par consumer group)
✔ Monitoring throughput
✔ Diagnostic intelligent
✔ Health score global
✔ Détection déséquilibre partitions
✔ Alerting (console + option Slack)
✔ Export JSON + CSV
✔ Mode temps réel

Auteur : Production-ready template
===========================================================
"""

import time
import json
import csv
import requests
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.admin import KafkaAdminClient

# ==============================
# ⚙️ CONFIGURATION
# ==============================
BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "my-topic"
LAG_THRESHOLD = 10000
SLACK_WEBHOOK = None  # 👉 Ajouter URL Slack si besoin
REAL_TIME_MODE = False  # True = boucle infinie

# ==============================
# 🚨 ALERTING
# ==============================
def send_alert(message):
    """
    Envoie une alerte :
    - console
    - Slack (si configuré)
    """
    print(f"🚨 ALERT: {message}")

    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": message})
        except Exception as e:
            print(f"Erreur envoi Slack: {e}")


# ==============================
# 📉 AUDIT LAG
# ==============================
def audit_lag():
    """
    Calcule le lag total par consumer group
    """
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    groups = admin.list_consumer_groups()

    results = []
    total_global_lag = 0

    print("\n📉 LAG AUDIT")

    for group, _ in groups:
        consumer = KafkaConsumer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=group
        )

        group_lag = 0

        for topic in consumer.topics():
            partitions = consumer.partitions_for_topic(topic)
            if not partitions:
                continue

            tps = [TopicPartition(topic, p) for p in partitions]
            end_offsets = consumer.end_offsets(tps)

            for tp in tps:
                committed = consumer.committed(tp) or 0
                lag = end_offsets[tp] - committed
                group_lag += lag

        print(f"Group={group} | Lag={group_lag}")

        if group_lag > LAG_THRESHOLD:
            send_alert(f"Lag élevé sur {group}: {group_lag}")

        total_global_lag += group_lag

        results.append({
            "group": group,
            "lag": group_lag
        })

    return total_global_lag, results


# ==============================
# 📊 THROUGHPUT
# ==============================
def monitor_throughput(duration=5):
    """
    Mesure le nombre de messages par seconde
    """
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset='latest'
    )

    print("\n📊 THROUGHPUT")

    start = time.time()
    count = 0

    for msg in consumer:
        count += 1

        if time.time() - start >= duration:
            rate = count / duration
            print(f"{TOPIC}: {int(rate)} msg/s")
            return rate

    return 0


# ==============================
# ⚖️ PARTITION SKEW
# ==============================
def detect_partition_skew():
    """
    Détecte déséquilibre des partitions
    """
    consumer = KafkaConsumer(bootstrap_servers=BOOTSTRAP_SERVERS)

    partitions = consumer.partitions_for_topic(TOPIC)
    tps = [TopicPartition(TOPIC, p) for p in partitions]
    end_offsets = consumer.end_offsets(tps)

    values = list(end_offsets.values())
    skew = max(values) - min(values)

    print("\n⚖️ PARTITION SKEW")
    print(f"Skew = {skew}")

    return skew > 10000


# ==============================
# 🧠 DIAGNOSTIC INTELLIGENT
# ==============================
def smart_diagnosis(lag, throughput):
    """
    Analyse automatique des problèmes
    """
    if lag > 10000 and throughput < 100:
        return "🚨 Consumers trop lents → scaler consumers"

    if lag > 10000 and throughput > 1000:
        return "⚠️ Producer trop rapide → throttling ou batch"

    if lag == 0 and throughput == 0:
        return "❌ Pipeline arrêté"

    return "✅ Système stable"


# ==============================
# 💯 HEALTH SCORE
# ==============================
def compute_health_score(lag, throughput, skew):
    """
    Score global de santé Kafka
    """
    score = 100

    if lag > 10000:
        score -= 30
    elif lag > 1000:
        score -= 10

    if throughput < 50:
        score -= 20

    if skew:
        score -= 15

    return max(score, 0)


# ==============================
# 📦 EXPORT
# ==============================
def export_results(data):
    """
    Export JSON + CSV
    """
    with open("audit.json", "w") as f:
        json.dump(data, f, indent=4)

    with open("audit.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    print("\n📁 Export effectué (audit.json + audit.csv)")


# ==============================
# 🚀 AUDIT GLOBAL
# ==============================
def full_audit():
    """
    Lance audit complet Kafka
    """
    print("\n🚀 DÉMARRAGE AUDIT KAFKA\n")

    # 1. Lag
    total_lag, lag_details = audit_lag()

    # 2. Throughput
    throughput = monitor_throughput()

    # 3. Partition skew
    skew = detect_partition_skew()

    # 4. Diagnostic
    diagnosis = smart_diagnosis(total_lag, throughput)

    # 5. Health Score
    health_score = compute_health_score(total_lag, throughput, skew)

    # 6. Résumé
    print("\n📊 RÉSUMÉ GLOBAL")
    print(f"Lag total: {total_lag}")
    print(f"Throughput: {throughput} msg/s")
    print(f"Skew: {skew}")
    print(f"Health Score: {health_score}/100")
    print(f"Diagnostic: {diagnosis}")

    # 7. Export
    export_results(lag_details)


# ==============================
# 🔁 MODE TEMPS RÉEL
# ==============================
def run():
    if REAL_TIME_MODE:
        while True:
            full_audit()
            time.sleep(30)  # toutes les 30 sec
    else:
        full_audit()


# ==============================
# ▶️ MAIN
# ==============================
if __name__ == "__main__":
    run()
