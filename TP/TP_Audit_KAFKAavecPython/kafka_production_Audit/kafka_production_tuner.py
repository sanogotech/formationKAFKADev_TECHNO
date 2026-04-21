#!/usr/bin/env python3
"""
Kafka Production Configuration & Tuning Generator
Ce script interroge l'utilisateur sur les paramètres d'un cluster Kafka
et génère 40 recommandations d'optimisation pour la production.
"""

import json
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class KafkaConfigGenerator:
    def __init__(self):
        self.config = {}
        self.recommendations = []
        
    def ask_questions(self):
        """Pose les 15 questions de configuration"""
        print("\n" + "="*80)
        print(" CONFIGURATION KAFKA POUR LA PRODUCTION ".center(80, "="))
        print("="*80 + "\n")
        
        questions = [
            ("Nombre de brokers dans le cluster", "int", 3),
            ("Nombre de partitions par topic (défaut)", "int", 6),
            ("Nombre de consumers dans le groupe principal", "int", 3),
            ("Durée de rétention des messages (heures)", "int", 168),  # 7 jours
            ("Facteur de réplication", "int", 3),
            ("CPU par broker (cœurs)", "int", 8),
            ("RAM par broker (Go)", "int", 16),
            ("Taille moyenne des messages (Ko)", "int", 10),
            ("Débit attendu (messages/seconde)", "int", 100000),
            ("Nombre de topics prévus", "int", 50),
            ("Latence maximale acceptable (ms)", "int", 100),
            ("Budget mensuel (€)", "float", 1000),
            ("Niveau de criticité (1-5, 5=mission critique)", "int", 3),
            ("Type de charge (lecture/écriture)", "str", "mixte"),  # lecture, ecriture, mixte
            ("Stratégie de compression", "str", "snappy")  # snappy, gzip, lz4, zstd, none
        ]
        
        print("Veuillez répondre aux questions suivantes :\n")
        
        for i, (question, qtype, default) in enumerate(questions, 1):
            while True:
                try:
                    if qtype == "int":
                        valeur = input(f"{i}. {question} ? [{default}] : ").strip()
                        if not valeur:
                            valeur = default
                        valeur = int(valeur)
                    elif qtype == "float":
                        valeur = input(f"{i}. {question} ? [{default}] : ").strip()
                        if not valeur:
                            valeur = default
                        valeur = float(valeur)
                    else:  # str
                        valeur = input(f"{i}. {question} ? [{default}] : ").strip()
                        if not valeur:
                            valeur = default
                        if qtype == "str" and question == "Type de charge":
                            if valeur not in ["lecture", "ecriture", "mixte"]:
                                print("Choix invalide. Utilisez: lecture, ecriture, mixte")
                                continue
                        if qtype == "str" and question == "Stratégie de compression":
                            if valeur not in ["snappy", "gzip", "lz4", "zstd", "none"]:
                                print("Choix invalide. Utilisez: snappy, gzip, lz4, zstd, none")
                                continue
                    
                    self.config[question] = valeur
                    break
                except ValueError:
                    print("Valeur invalide, veuillez réessayer.")
        
        # Calculs dérivés
        self.config["debit_mo_sec"] = (self.config["Taille moyenne des messages (Ko)"] * 
                                       self.config["Débit attendu (messages/seconde)"]) / 1024
        self.config["stockage_journalier_gb"] = (self.config["debit_mo_sec"] * 86400) / 1024
        self.config["partitions_par_broker"] = (self.config["Nombre de partitions par topic (défaut)"] * 
                                                self.config["Nombre de topics prévus"]) / self.config["Nombre de brokers dans le cluster"]
        
    def generate_recommendations(self):
        """Génère 40 recommandations de tuning"""
        recommendations = []
        
        # 1. Configuration OS et système
        recommendations.append({
            "id": 1,
            "categorie": "Système d'exploitation",
            "recommandation": "Désactiver la swap ou définir vm.swappiness=1",
            "priorite": "Haute",
            "impact": "Évite les pauses GC et améliore la stabilité"
        })
        
        recommendations.append({
            "id": 2,
            "categorie": "Système d'exploitation",
            "recommandation": f"Ajuster vm.max_map_count à 1048570 (actuel: {self.config['CPU par broker (cœurs)'] * 131072})",
            "priorite": "Moyenne",
            "impact": "Permet plus de segments mémoire mappés"
        })
        
        recommendations.append({
            "id": 3,
            "categorie": "Système d'exploitation",
            "recommandation": "Utiliser le filesystem XFS avec noatime",
            "priorite": "Haute",
            "impact": "Meilleures performances d'E/S pour Kafka"
        })
        
        # 2. Configuration JVM
        recommendations.append({
            "id": 4,
            "categorie": "JVM",
            "recommandation": f"Allouer {int(self.config['RAM par broker (Go)'] * 0.6)} Go de heap (-Xms -Xmx)",
            "priorite": "Haute",
            "impact": "Optimisation de l'utilisation mémoire"
        })
        
        recommendations.append({
            "id": 5,
            "categorie": "JVM",
            "recommandation": "Utiliser G1GC avec -XX:+UseG1GC -XX:MaxGCPauseMillis=20",
            "priorite": "Haute",
            "impact": "Réduction des pauses GC"
        })
        
        recommendations.append({
            "id": 6,
            "categorie": "JVM",
            "recommandation": "Activer -XX:+DisableExplicitGC",
            "priorite": "Moyenne",
            "impact": "Évite les appels System.gc()"
        })
        
        # 3. Configuration broker
        recommendations.append({
            "id": 7,
            "categorie": "Broker",
            "recommandation": f"log.retention.hours={self.config['Durée de rétention des messages (heures)']}",
            "priorite": "Haute",
            "impact": "Contrôle l'espace disque"
        })
        
        recommendations.append({
            "id": 8,
            "categorie": "Broker",
            "recommandation": f"num.replica.fetchers={max(2, int(self.config['CPU par broker (cœurs)'] * 0.25))}",
            "priorite": "Haute",
            "impact": "Accélère la réplication"
        })
        
        recommendations.append({
            "id": 9,
            "categorie": "Broker",
            "recommandation": f"compression.type={self.config['Stratégie de compression']}",
            "priorite": "Moyenne",
            "impact": "Réduction de l'utilisation réseau"
        })
        
        recommendations.append({
            "id": 10,
            "categorie": "Broker",
            "recommandation": f"default.replication.factor={min(self.config['Facteur de réplication'], self.config['Nombre de brokers dans le cluster'])}",
            "priorite": "Haute",
            "impact": "Tolérance aux pannes"
        })
        
        # 4. Performance réseau
        recommendations.append({
            "id": 11,
            "categorie": "Réseau",
            "recommandation": f"socket.send.buffer.bytes={max(102400, int(self.config['Taille moyenne des messages (Ko)'] * 1024 * 2))}",
            "priorite": "Moyenne",
            "impact": "Optimisation des buffers réseau"
        })
        
        recommendations.append({
            "id": 12,
            "categorie": "Réseau",
            "recommandation": "num.network.threads=8",
            "priorite": "Moyenne",
            "impact": "Traitement parallèle des requêtes"
        })
        
        # 5. Production/Consommation
        recommendations.append({
            "id": 13,
            "categorie": "Producer",
            "recommandation": "acks=all pour une haute durabilité",
            "priorite": "Haute" if self.config["Niveau de criticité (1-5)"] >= 4 else "Moyenne",
            "impact": "Garantie de non-perte de messages"
        })
        
        recommendations.append({
            "id": 14,
            "categorie": "Producer",
            "recommandation": f"batch.size={min(16384, int(self.config['Taille moyenne des messages (Ko)'] * 1024 * 100))}",
            "priorite": "Moyenne",
            "impact": "Optimisation du batching"
        })
        
        recommendations.append({
            "id": 15,
            "categorie": "Consumer",
            "recommandation": f"max.poll.records={min(500, max(100, int(self.config['Débit attendu (messages/seconde)'] / self.config['Nombre de consumers dans le groupe principal'] / 10)))}",
            "priorite": "Moyenne",
            "impact": "Équilibre latence/débit"
        })
        
        # 6. Partitionnement
        recommendations.append({
            "id": 16,
            "categorie": "Partitions",
            "recommandation": f"Redimensionner les topics à {max(6, int(self.config['partitions_par_broker'] * 2))} partitions",
            "priorite": "Haute" if self.config["Débit attendu (messages/seconde)"] > 50000 else "Basse",
            "impact": "Meilleure parallélisation"
        })
        
        recommendations.append({
            "id": 17,
            "categorie": "Partitions",
            "recommandation": "Éviter plus de 2000 partitions par broker",
            "priorite": "Haute",
            "impact": "Évite la surcharge de gestion"
        })
        
        # 7. Log et segments
        recommendations.append({
            "id": 18,
            "categorie": "Logs",
            "recommandation": f"log.segment.bytes={max(1073741824, int(self.config['stockage_journalier_gb'] * 1024 * 1024 * 1024 / 24))}",
            "priorite": "Moyenne",
            "impact": "Optimisation des segments"
        })
        
        recommendations.append({
            "id": 19,
            "categorie": "Logs",
            "recommandation": "log.cleaner.threads=4",
            "priorite": "Moyenne",
            "impact": "Nettoyage plus rapide"
        })
        
        # 8. Monitoring
        recommendations.append({
            "id": 20,
            "categorie": "Monitoring",
            "recommandation": "Installer Prometheus + Grafana pour le monitoring",
            "priorite": "Haute",
            "impact": "Visibilité complète du cluster"
        })
        
        recommendations.append({
            "id": 21,
            "categorie": "Monitoring",
            "recommandation": "Configurer JMX avec -Dcom.sun.management.jmxremote",
            "priorite": "Moyenne",
            "impact": "Métriques détaillées"
        })
        
        # 9. Sécurité
        recommendations.append({
            "id": 22,
            "categorie": "Sécurité",
            "recommandation": "Activer SSL/TLS pour l'authentification",
            "priorite": "Haute" if self.config["Niveau de criticité (1-5)"] >= 3 else "Basse",
            "impact": "Sécurisation des données"
        })
        
        recommendations.append({
            "id": 23,
            "categorie": "Sécurité",
            "recommandation": "Configurer les ACLs pour le contrôle d'accès",
            "priorite": "Moyenne",
            "impact": "Sécurité granulaire"
        })
        
        # 10. Tuning avancé
        recommendations.append({
            "id": 24,
            "categorie": "Avancé",
            "recommandation": "Activer le rack awareness pour la réplication",
            "priorite": "Haute" if self.config["Nombre de brokers dans le cluster"] >= 6 else "Basse",
            "impact": "Résilience aux pannes de rack"
        })
        
        recommendations.append({
            "id": 25,
            "categorie": "Avancé",
            "recommandation": "Configurer quota.producer.default et quota.consumer.default",
            "priorite": "Moyenne",
            "impact": "Évite les consumers/producers bruyants"
        })
        
        # 11-40: Ajout de plus de recommandations
        more_recs = [
            ("Performance", "Désactiver atime sur les partitions disque", "Haute", "Amélioration E/S"),
            ("Performance", "Utiliser RAID 10 pour les données Kafka", "Haute", "Redondance + performance"),
            ("Performance", "Configurer num.io.threads = 8", "Moyenne", "Traitement disque parallèle"),
            ("Performance", "Ajuster queued.max.requests = 500", "Moyenne", "Queue plus large"),
            ("Network", "Isoler le trafic Kafka sur des interfaces dédiées", "Haute", "Réduction latence"),
            ("Memory", "Configurer OS page cache = 20-30% RAM", "Haute", "Cache disque optimisé"),
            ("GC", "Utiliser -XX:+ParallelRefProcEnabled", "Moyenne", "GC plus rapide"),
            ("GC", "Configurer -XX:G1NewSizePercent=5", "Moyenne", "Optimisation G1"),
            ("Replication", "min.insync.replicas = 2", "Haute", "Garantie écriture"),
            ("Replication", "unclean.leader.election.enable = false", "Haute", "Prévention perte données"),
            ("Tuning", "message.max.bytes = 1MB", "Moyenne", "Taille max message"),
            ("Tuning", "replica.fetch.max.bytes = 2MB", "Moyenne", "Réplication efficace"),
            ("Tuning", "fetch.message.max.bytes = 1MB", "Moyenne", "Taille fetch consumer"),
            ("ZooKeeper", "Utiliser ZooKeeper dédié avec 3+ nœuds", "Haute", "Stabilité métadonnées"),
            ("ZooKeeper", "Configurer zookeeper.session.timeout.ms = 18000", "Moyenne", "Tolérance réseau"),
            ("Disque", "Séparer logs Kafka et segments sur disques différents", "Moyenne", "E/S parallèles"),
            ("Disque", "Utiliser SSD pour les partitions actives", "Haute" if self.config["Débit attendu (messages/seconde)"] > 100000 else "Basse", "Réduction latence"),
            ("Network", "Augmenter net.core.somaxconn = 4096", "Moyenne", "Plus de connexions"),
            ("Consumer", "Enable auto.commit = false", "Haute", "Contrôle des offsets"),
            ("Producer", "max.in.flight.requests.per.connection = 5", "Moyenne", "Pipelining"),
            ("Log", "log.flush.interval.messages = 9223372036854775807", "Haute", "Pas de flush forcé"),
            ("Log", "log.flush.interval.ms = 1000", "Moyenne", "Flush périodique"),
            ("Memory", "Définir replica.socket.receive.buffer.bytes = 65536", "Basse", "Buffer réplication"),
            ("Threads", "background.threads = 10", "Moyenne", "Tâches background"),
            ("Metrics", "Metric reporters = com.linkedin.kafka.cruisecontrol.metricsreporter.CruiseControlMetricsReporter", "Moyenne", "Auto-équilibrage"),
            ("Retention", "log.retention.check.interval.ms = 300000", "Basse", "Vérification rétention"),
            ("Compression", "compression.type = producer", "Moyenne", "Flexibilité compression"),
            ("Offset", "offsets.topic.replication.factor = 3", "Haute", "Durabilité offsets"),
            ("Transaction", "transaction.state.log.replication.factor = 3", "Haute", "Transactions fiables"),
            ("Auto", "auto.create.topics.enable = false", "Haute", "Prévention création accidentelle")
        ]
        
        for i, (cat, rec, prio, impact) in enumerate(more_recs, 26):
            recommendations.append({
                "id": i,
                "categorie": cat,
                "recommandation": rec,
                "priorite": prio,
                "impact": impact
            })
        
        self.recommendations = recommendations[:40]  # Garder exactement 40
        
    def print_report(self):
        """Affiche le rapport complet"""
        print("\n" + "="*80)
        print(" RAPPORT DE CONFIGURATION KAFKA ".center(80, "="))
        print("="*80)
        
        print("\n📊 RÉSUMÉ DE LA CONFIGURATION SAISIE :\n")
        for key, value in self.config.items():
            if isinstance(value, float):
                print(f"  • {key}: {value:.2f}")
            else:
                print(f"  • {key}: {value}")
        
        print("\n" + "-"*80)
        print("🎯 40 RECOMMANDATIONS D'OPTIMISATION POUR LA PRODUCTION")
        print("-"*80)
        
        # Regrouper par catégorie
        categories = {}
        for rec in self.recommendations:
            cat = rec['categorie']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rec)
        
        for cat, recs in sorted(categories.items()):
            print(f"\n📁 {cat.upper()}")
            print("   " + "-"*70)
            for rec in recs:
                priorite_icon = "🔴" if rec['priorite'] == "Haute" else "🟡" if rec['priorite'] == "Moyenne" else "🟢"
                print(f"   {priorite_icon} [{rec['id']:2d}] {rec['recommandation']}")
                print(f"        → Priorité: {rec['priorite']} | Impact: {rec['impact']}")
        
        print("\n" + "="*80)
        print(" MÉTRIQUES CRITIQUES CALCULÉES ")
        print("="*80)
        print(f"  • Débit estimé: {self.config['debit_mo_sec']:.2f} Mo/s")
        print(f"  • Stockage journalier: {self.config['stockage_journalier_gb']:.2f} Go/jour")
        print(f"  • Stockage pour {self.config['Durée de rétention des messages (heures)']}h: {(self.config['stockage_journalier_gb'] * self.config['Durée de rétention des messages (heures)'] / 24):.2f} Go")
        print(f"  • Partitions par broker: {self.config['partitions_par_broker']:.1f}")
        
        # Recommandations finales
        print("\n" + "="*80)
        print(" ACTIONS IMMÉDIATES RECOMMANDÉES ")
        print("="*80)
        
        hautes_priorites = [r for r in self.recommendations if r['priorite'] == "Haute"][:5]
        print("\nTop 5 des actions à implémenter en priorité :")
        for i, rec in enumerate(hautes_priorites, 1):
            print(f"  {i}. {rec['recommandation']}")
        
        print("\n" + "="*80)
        print("✅ Rapport généré avec succès!")
        print("="*80 + "\n")
        
    def export_json(self, filename="kafka_config_report.json"):
        """Exporte la configuration en JSON"""
        export_data = {
            "date_generation": datetime.now().isoformat(),
            "config_utilisateur": self.config,
            "recommandations": self.recommendations,
            "metriques_calculees": {
                "debit_mo_sec": self.config['debit_mo_sec'],
                "stockage_journalier_gb": self.config['stockage_journalier_gb'],
                "partitions_par_broker": self.config['partitions_par_broker']
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"📁 Rapport exporté dans {filename}")
        
    def run(self):
        """Exécute le pipeline complet"""
        try:
            self.ask_questions()
            self.generate_recommendations()
            self.print_report()
            self.export_json()
        except KeyboardInterrupt:
            print("\n\n⚠️  Génération interrompue par l'utilisateur")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            sys.exit(1)


if __name__ == "__main__":
    generator = KafkaConfigGenerator()
    generator.run()
