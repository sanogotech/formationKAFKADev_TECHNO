"""
- pip install kafka-python

- kafka-consumer-groups.bat --bootstrap-server localhost:9092 --describe --group group-payment

"""
import time
from kafka import KafkaConsumer, TopicPartition, KafkaAdminClient
from kafka.admin import NewTopic

BOOTSTRAP_SERVERS = "localhost:9092"


def get_consumer_groups():
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    groups = admin.list_consumer_groups()
    return [group[0] for group in groups]


def get_group_offsets(group_id):
    consumer = KafkaConsumer(bootstrap_servers=BOOTSTRAP_SERVERS)
    partitions = consumer.partitions_for_topic

    offsets = consumer.committed
    return offsets


def get_lag_for_group(group_id):
    consumer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=group_id,
        enable_auto_commit=False
    )

    topics = consumer.topics()
    lag_report = []

    for topic in topics:
        partitions = consumer.partitions_for_topic(topic)
        if partitions is None:
            continue

        topic_partitions = [TopicPartition(topic, p) for p in partitions]

        end_offsets = consumer.end_offsets(topic_partitions)

        for tp in topic_partitions:
            committed = consumer.committed(tp)
            latest = end_offsets[tp]

            if committed is None:
                lag = latest
            else:
                lag = latest - committed

            lag_report.append({
                "group": group_id,
                "topic": tp.topic,
                "partition": tp.partition,
                "current_offset": committed,
                "latest_offset": latest,
                "lag": lag
            })

    return lag_report


def analyze_lag(lag_data):
    recommendations = []

    total_lag = sum(item["lag"] for item in lag_data)

    if total_lag == 0:
        status = "OK ✅"
    elif total_lag < 1000:
        status = "LAG FAIBLE ⚠️"
    else:
        status = "LAG ÉLEVÉ 🚨"

    # Analyse avancée
    if total_lag > 1000:
        recommendations.append("👉 Augmenter le nombre de consumers")
        recommendations.append("👉 Vérifier les performances du consumer (CPU, DB, API)")
        recommendations.append("👉 Augmenter le nombre de partitions si possible")

    slow_partitions = [d for d in lag_data if d["lag"] > 500]

    if slow_partitions:
        recommendations.append("👉 Certaines partitions sont en retard → déséquilibre possible")

    if len(lag_data) > 0:
        partitions = len(lag_data)
        if partitions < 3:
            recommendations.append("👉 Trop peu de partitions → limiter le parallélisme")

    return status, total_lag, recommendations


def audit_kafka():
    print("🔍 Audit Kafka Lag en cours...\n")

    groups = get_consumer_groups()

    if not groups:
        print("❌ Aucun consumer group trouvé")
        return

    for group in groups:
        print(f"\n📦 Consumer Group: {group}")

        lag_data = get_lag_for_group(group)

        if not lag_data:
            print("⚠️ Aucun lag détecté ou topic vide")
            continue

        status, total_lag, recommendations = analyze_lag(lag_data)

        print(f"📊 Total Lag: {total_lag}")
        print(f"📈 Status: {status}")

        print("\n📄 Détails par partition:")
        for d in lag_data:
            print(f"  - Topic: {d['topic']} | Partition: {d['partition']} | Lag: {d['lag']}")

        print("\n💡 Recommandations:")
        if recommendations:
            for r in recommendations:
                print(r)
        else:
            print("✅ Aucun problème détecté")

        print("\n" + "-" * 50)


if __name__ == "__main__":
    audit_kafka()
