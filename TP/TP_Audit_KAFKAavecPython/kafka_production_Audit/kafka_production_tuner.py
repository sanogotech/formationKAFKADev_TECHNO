#!/usr/bin/env python3
"""
Kafka Production Configuration & Tuning Generator - Version Consumer Ready
"""

import json
import sys
from datetime import datetime

class KafkaConfigGenerator:
    def __init__(self):
        self.config = {}
        self.recommendations = []

    def ask_questions(self):
        print("\n" + "="*80)
        print(" CONFIGURATION KAFKA POUR LA PRODUCTION ".center(80, "="))
        print("="*80 + "\n")

        questions = [
            ("Nombre de brokers dans le cluster", "int", 3),
            ("Nombre de partitions par topic (défaut)", "int", 6),
            ("Nombre de consumers (tous groupes confondus)", "int", 10),
            ("Nombre de consumers dans le groupe principal", "int", 3),
            ("Durée de rétention des messages (heures)", "int", 168),
            ("Facteur de réplication", "int", 3),
            ("CPU par broker (cœurs)", "int", 8),
            ("RAM par broker (Go)", "int", 16),
            ("Taille moyenne des messages (Ko)", "int", 10),
            ("Débit attendu (messages/seconde)", "int", 100000),
            ("Nombre de topics prévus", "int", 50),
            ("Latence maximale acceptable (ms)", "int", 100),
            ("Budget mensuel (€)", "float", 1000),
            ("Niveau de criticité (1-5)", "int", 3),
            ("Type de charge (lecture/ecriture/mixte)", "str", "mixte"),
            ("Stratégie de compression", "str", "snappy")
        ]

        print("Veuillez répondre aux questions suivantes :\n")
        for i, (q, t, d) in enumerate(questions, 1):
            while True:
                try:
                    val = input(f"{i}. {q} ? [{d}] : ").strip()
                    if not val:
                        val = d
                    if t == "int":
                        val = int(val)
                    elif t == "float":
                        val = float(val)
                    else:
                        if q == "Type de charge (lecture/ecriture/mixte)" and val not in ["lecture","ecriture","mixte"]:
                            print("Choix invalide. Utilisez: lecture, ecriture, mixte")
                            continue
                        if q == "Stratégie de compression" and val not in ["snappy","gzip","lz4","zstd","none"]:
                            print("Choix invalide. Utilisez: snappy, gzip, lz4, zstd, none")
                            continue
                    self.config[q] = val
                    break
                except ValueError:
                    print("Valeur invalide, réessayez.")

        # Calculs dérivés
        taille = self.config.get("Taille moyenne des messages (Ko)", 10)
        debit = self.config.get("Débit attendu (messages/seconde)", 100000)
        self.config["debit_mo_sec"] = (taille * debit) / 1024
        self.config["stockage_journalier_gb"] = (self.config["debit_mo_sec"] * 86400) / 1024
        topics = self.config.get("Nombre de topics prévus", 50)
        partitions_par_topic = self.config.get("Nombre de partitions par topic (défaut)", 6)
        brokers = self.config.get("Nombre de brokers dans le cluster", 3)
        self.config["partitions_par_broker"] = (partitions_par_topic * topics) / brokers
        self.config["partitions_total"] = partitions_par_topic * topics

    def generate_recommendations(self):
        # Récupération sécurisée
        brokers = self.config.get("Nombre de brokers dans le cluster", 3)
        partitions_topic = self.config.get("Nombre de partitions par topic (défaut)", 6)
        total_consumers = self.config.get("Nombre de consumers (tous groupes confondus)", 10)
        main_group_consumers = self.config.get("Nombre de consumers dans le groupe principal", 3)
        retention = self.config.get("Durée de rétention des messages (heures)", 168)
        replication = self.config.get("Facteur de réplication", 3)
        cpu = self.config.get("CPU par broker (cœurs)", 8)
        ram = self.config.get("RAM par broker (Go)", 16)
        taille_msg = self.config.get("Taille moyenne des messages (Ko)", 10)
        debit_msg = self.config.get("Débit attendu (messages/seconde)", 100000)
        n_topics = self.config.get("Nombre de topics prévus", 50)
        latence = self.config.get("Latence maximale acceptable (ms)", 100)
        criticite = self.config.get("Niveau de criticité (1-5)", 3)
        charge = self.config.get("Type de charge (lecture/ecriture/mixte)", "mixte")
        compression = self.config.get("Stratégie de compression", "snappy")
        partitions_total = self.config.get("partitions_total", partitions_topic * n_topics)
        debit_mo_sec = self.config.get("debit_mo_sec", (taille_msg * debit_msg) / 1024)
        stockage_journalier = self.config.get("stockage_journalier_gb", (debit_mo_sec * 86400) / 1024)

        recs = []

        # --- 1. OS & Système ---
        recs.append(("Système d'exploitation", "Désactiver la swap ou vm.swappiness=1", "Haute", "Évite les pauses GC"))
        recs.append(("Système d'exploitation", "vm.max_map_count=1048570", "Moyenne", "Segments mémoire mappés"))
        recs.append(("Système d'exploitation", "Filesystem XFS avec noatime", "Haute", "Performances E/S"))

        # --- 2. JVM ---
        heap = int(ram * 0.6)
        recs.append(("JVM", f"Allouer {heap} Go de heap (-Xms -Xmx)", "Haute", "Optimisation mémoire"))
        recs.append(("JVM", "G1GC: -XX:+UseG1GC -XX:MaxGCPauseMillis=20", "Haute", "Réduction pauses GC"))
        recs.append(("JVM", "-XX:+DisableExplicitGC", "Moyenne", "Évite les appels System.gc()"))

        # --- 3. Broker ---
        recs.append(("Broker", f"log.retention.hours={retention}", "Haute", "Contrôle espace disque"))
        recs.append(("Broker", f"num.replica.fetchers={max(2, int(cpu*0.25))}", "Haute", "Accélère réplication"))
        recs.append(("Broker", f"compression.type={compression}", "Moyenne", "Réduction réseau"))
        recs.append(("Broker", f"default.replication.factor={min(replication, brokers)}", "Haute", "Tolérance pannes"))

        # --- 4. Réseau ---
        recs.append(("Réseau", f"socket.send.buffer.bytes={max(102400, int(taille_msg*1024*2))}", "Moyenne", "Optimisation buffers"))
        recs.append(("Réseau", "num.network.threads=8", "Moyenne", "Traitement parallèle"))

        # --- 5. Producer / Consumer ---
        priorite_acks = "Haute" if criticite >= 4 else "Moyenne"
        recs.append(("Producer", "acks=all pour haute durabilité", priorite_acks, "Garantie non-perte"))
        recs.append(("Producer", f"batch.size={min(16384, int(taille_msg*1024*100))}", "Moyenne", "Optimisation batching"))
        max_poll = min(500, max(100, int(debit_msg / main_group_consumers / 10))) if main_group_consumers > 0 else 500
        recs.append(("Consumer", f"max.poll.records={max_poll}", "Moyenne", "Équilibre latence/débit"))

        # --- 6. Recommandations spécifiques CONSUMERS ---
        # 6.1 Vérifier le ratio consumers / partitions total
        if total_consumers > partitions_total:
            recs.append(("Consumer", f"Réduire le nombre total de consumers ({total_consumers}) à ≤ {partitions_total} (partitions totales)", "Haute", "Évite consumers inactifs"))
        elif total_consumers < partitions_total:
            recs.append(("Consumer", f"Ajouter des consumers (actuellement {total_consumers}) pour atteindre près de {partitions_total} partitions", "Moyenne", "Meilleur parallélisme"))
        else:
            recs.append(("Consumer", f"Nombre de consumers ({total_consumers}) idéalement équilibré avec les partitions ({partitions_total})", "Basse", "Configuration équilibrée"))

        # 6.2 Timeouts session / heartbeat
        if latence < 50:
            recs.append(("Consumer", "session.timeout.ms=10000, heartbeat.interval.ms=3000 (réseau rapide)", "Moyenne", "Détection rapide pannes"))
        else:
            recs.append(("Consumer", "session.timeout.ms=30000, heartbeat.interval.ms=10000 (réseau variable)", "Moyenne", "Évite faux rebalancements"))

        # 6.3 Fetch tuning
        recs.append(("Consumer", f"fetch.min.bytes={1024 if debit_msg < 10000 else 10240}", "Moyenne", "Optimisation débit vs latence"))
        recs.append(("Consumer", f"max.partition.fetch.bytes={max(1048576, int(taille_msg*1024*50))}", "Moyenne", "Taille maximale par partition"))
        recs.append(("Consumer", "enable.auto.commit=false (contrôle manuel des offsets)", "Haute", "Évite les doubles traitements"))

        # --- 7. Partitions ---
        recs.append(("Partitions", f"Redimensionner les topics à {max(6, int(partitions_topic*1.5))} partitions", "Haute" if debit_msg>50000 else "Basse", "Meilleure parallélisation"))
        recs.append(("Partitions", "Éviter plus de 2000 partitions par broker", "Haute", "Évite surcharge"))

        # --- 8. Logs & Stockage ---
        segment_bytes = max(1073741824, int(stockage_journalier * 1024**3 / 24))
        recs.append(("Logs", f"log.segment.bytes={segment_bytes}", "Moyenne", "Optimisation segments"))
        recs.append(("Logs", "log.cleaner.threads=4", "Moyenne", "Nettoyage plus rapide"))

        # --- 9. Monitoring & Sécurité ---
        recs.append(("Monitoring", "Prometheus + Grafana", "Haute", "Visibilité complète"))
        recs.append(("Monitoring", "JMX exporter", "Moyenne", "Métriques détaillées"))
        priorite_secu = "Haute" if criticite >= 3 else "Basse"
        recs.append(("Sécurité", "Activer SSL/TLS", priorite_secu, "Sécurisation données"))
        recs.append(("Sécurité", "Configurer ACLs", "Moyenne", "Contrôle accès"))

        # --- 10. Avancé ---
        recs.append(("Avancé", "Rack awareness si brokers ≥ 6", "Basse" if brokers<6 else "Haute", "Résilience"))
        recs.append(("Avancé", "Configurer des quotas (producer/consumer)", "Moyenne", "Évite les tenants bruyants"))

        # Compléter jusqu'à 40+ recommandations avec des classiques
        extra = [
            ("Performance", "Désactiver atime sur disques", "Haute", "Amélioration E/S"),
            ("Performance", "RAID 10 pour les données Kafka", "Haute", "Redondance + performance"),
            ("Performance", "num.io.threads = 8", "Moyenne", "Traitement disque parallèle"),
            ("Réseau", "Isoler le trafic Kafka sur des interfaces dédiées", "Haute", "Réduction latence"),
            ("Mémoire", "Page cache OS = 20-30% RAM", "Haute", "Cache disque optimisé"),
            ("GC", "-XX:+ParallelRefProcEnabled", "Moyenne", "GC plus rapide"),
            ("Réplication", "min.insync.replicas = 2", "Haute", "Garantie écriture"),
            ("Réplication", "unclean.leader.election.enable = false", "Haute", "Prévention perte données"),
            ("ZooKeeper", "ZK dédié avec 3+ nœuds", "Haute", "Stabilité métadonnées"),
            ("Disque", "Séparer logs Kafka et segments sur disques différents", "Moyenne", "E/S parallèles"),
            ("Log", "log.flush.interval.messages = Long.MAX_VALUE", "Haute", "Pas de flush forcé"),
            ("CruiseControl", "Utiliser CruiseControl pour l'auto-équilibrage", "Moyenne", "Distribution optimisée")
        ]
        for cat, rec, prio, imp in extra:
            recs.append((cat, rec, prio, imp))

        # Convertir en dictionnaires avec ID
        self.recommendations = []
        for idx, (cat, rec, prio, imp) in enumerate(recs[:45], 1):  # on prend les 45 premières
            self.recommendations.append({
                "id": idx,
                "categorie": cat,
                "recommandation": rec,
                "priorite": prio,
                "impact": imp
            })

    def print_report(self):
        print("\n" + "="*80)
        print(" RAPPORT DE CONFIGURATION KAFKA ".center(80, "="))
        print("="*80)
        print("\n📊 RÉSUMÉ DE LA CONFIGURATION SAISIE :\n")
        for k, v in self.config.items():
            if isinstance(v, float):
                print(f"  • {k}: {v:.2f}")
            else:
                print(f"  • {k}: {v}")
        print("\n" + "-"*80)
        print("🎯 RECOMMANDATIONS (dont consumers)")
        print("-"*80)
        cats = {}
        for r in self.recommendations:
            cats.setdefault(r['categorie'], []).append(r)
        for cat, recs in sorted(cats.items()):
            print(f"\n📁 {cat.upper()}")
            for r in recs:
                icon = "🔴" if r['priorite'] == "Haute" else "🟡" if r['priorite'] == "Moyenne" else "🟢"
                print(f"   {icon} [{r['id']:2d}] {r['recommandation']}")
                print(f"        → Priorité: {r['priorite']} | Impact: {r['impact']}")
        print("\n" + "="*80)
        print(" MÉTRIQUES CRITIQUES ")
        print("="*80)
        print(f"  • Débit estimé: {self.config.get('debit_mo_sec',0):.2f} Mo/s")
        print(f"  • Stockage journalier: {self.config.get('stockage_journalier_gb',0):.2f} Go/jour")
        print(f"  • Partitions par broker: {self.config.get('partitions_par_broker',0):.1f}")
        print(f"  • Partitions totales: {self.config.get('partitions_total',0)}")
        print(f"  • Consumers totaux: {self.config.get('Nombre de consumers (tous groupes confondus)',0)}")

    def export_json(self, filename="kafka_config_consumer_report.json"):
        data = {
            "date": datetime.now().isoformat(),
            "config": self.config,
            "recommendations": self.recommendations
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n📁 Rapport exporté dans {filename}")

    def run(self):
        try:
            self.ask_questions()
            self.generate_recommendations()
            self.print_report()
            self.export_json()
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    KafkaConfigGenerator().run()