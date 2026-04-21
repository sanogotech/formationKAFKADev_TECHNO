#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run_all.sh – Exécute tous les TPs dans l'ordre (hors TP20 Avro)
# Usage : bash run_all.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPTS_DIR="$(dirname "$0")/scripts"
PYTHON="${PYTHON:-python}"

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

run_tp() {
    local num=$1
    local file=$2
    local desc=$3
    echo ""
    echo -e "${YELLOW}━━━ TP $num – $desc ━━━${RESET}"
    if $PYTHON "$SCRIPTS_DIR/$file"; then
        echo -e "${GREEN}✅ TP $num OK${RESET}"
    else
        echo -e "${RED}❌ TP $num ÉCHOUÉ${RESET}"
        exit 1
    fi
    sleep 1
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Formation Kafka Python – Exécution des 19 TPs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_tp  1  "tp1_list_topics.py"          "Lister les topics"
run_tp  2  "tp2_create_topic.py"         "Créer un topic"
run_tp  3  "tp3_simple_producer.py"      "Producteur simple"
run_tp  4  "tp4_simple_consumer.py"      "Consommateur simple"
run_tp  5  "tp5_json_producer.py"        "Producteur JSON"
run_tp  6  "tp6_json_consumer.py"        "Consommateur JSON"
run_tp  7  "tp7_key_partitioning.py"     "Partitionnement par clé"
run_tp  8  "tp8_auto_commit.py"          "Auto-commit (démonstration)"
run_tp 10  "tp10_dlq.py"                 "Dead Letter Queue"
run_tp 11  "tp11_compression.py"         "Compression lz4"
run_tp 12  "tp12_batch_consumer.py"      "Consommation par lots"
run_tp 13  "tp13_lag.py"                 "Calcul du lag"
run_tp 14  "tp14_reset_offsets.py"       "Reset des offsets (dry-run)"
run_tp 15  "tp15_idempotence.py"         "Idempotence exactly-once"
run_tp 17  "tp17_timeout.py"             "Gestion des timeouts"
run_tp 18  "tp18_headers_producer.py"    "Headers producteur"
run_tp 19  "tp19_headers_consumer.py"    "Headers consommateur"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN} ✅ Tous les TPs ont été exécutés avec succès !${RESET}"
echo ""
echo " ℹ️  TPs exclus de ce script :"
echo "    • TP 9  (tp9_manual_commit_loop.py)  – boucle infinie, Ctrl+C pour arrêter"
echo "    • TP 16 (tp16_transactions.py)        – transactions (exécutez manuellement)"
echo "    • TP 20 (tp20_avro_producer.py)       – requiert Schema Registry"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
