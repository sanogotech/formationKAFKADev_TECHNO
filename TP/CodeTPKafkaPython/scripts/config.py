"""
config.py – Configuration centralisée pour tous les TPs.
Modifiez ce fichier si votre cluster Kafka est sur un autre hôte/port.
"""

# ─── Broker Kafka ────────────────────────────────────────────────────────────
BOOTSTRAP_SERVERS = "localhost:9092"

# ─── Schema Registry (TP20) ──────────────────────────────────────────────────
SCHEMA_REGISTRY_URL = "http://localhost:8081"

# ─── Topics utilisés dans les TPs ────────────────────────────────────────────
TOPIC_TEST      = "tp-test"
TOPIC_DLQ       = "tp-dlq"
TOPIC_AVRO      = "tp-avro"
TOPIC_TX        = "tp-transactions"

# ─── Consumer groups ─────────────────────────────────────────────────────────
GROUP_SIMPLE    = "tp-group"
GROUP_JSON      = "tp-group-json"
GROUP_BOUCLE    = "tp-boucle"
GROUP_LAG       = "tp-lag"

# ─── Paramètres par défaut ───────────────────────────────────────────────────
DEFAULT_TIMEOUT = 5.0          # secondes pour poll()
PRODUCER_FLUSH_TIMEOUT = 10    # secondes pour flush()
