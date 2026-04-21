#!/usr/bin/env python3
"""
Kafka Audit Tool - Audit complet d'un cluster Kafka
Auteur: Audit Tool
Version: 1.0
Description: Audit des configurations, topics, santé et recommandations
- pip install kafka-python requests
- python kafka_audit.py --bootstrap-servers localhost:9092
- python kafka_audit.py --bootstrap-servers localhost:9092 --output json > audit_report.json
"""

import json
import subprocess
import sys
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse

try:
    from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
    from kafka.admin import ConfigResource, ConfigResourceType
    from kafka.errors import NoBrokersAvailable
    import requests
except ImportError:
    print("Installation des dépendances requises...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kafka-python", "requests"])
    from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
    from kafka.admin import ConfigResource, ConfigResourceType
    from kafka.errors import NoBrokersAvailable
    import requests


class KafkaAuditor:
    """Auditeur complet pour cluster Kafka"""
    
    def __init__(self, bootstrap_servers: str, security_protocol: str = "PLAINTEXT",
                 sasl_mechanism: str = None, sasl_username: str = None, 
                 sasl_password: str = None):
        self.bootstrap_servers = bootstrap_servers
        self.security_protocol = security_protocol
        self.sasl_mechanism = sasl_mechanism
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.admin_client = None
        self.consumer = None
        self.audit_results = {
            "cluster_info": {},
            "brokers": [],
            "topics": {},
            "issues": [],
            "recommendations": [],
            "tips": []
        }
        
    def connect(self) -> bool:
        """Établir la connexion au cluster Kafka"""
        try:
            config = {
                'bootstrap_servers': self.bootstrap_servers,
                'request_timeout_ms': 10000
            }
            
            if self.security_protocol != "PLAINTEXT":
                config['security_protocol'] = self.security_protocol
                if self.sasl_mechanism:
                    config['sasl_mechanism'] = self.sasl_mechanism
                    config['sasl_plain_username'] = self.sasl_username
                    config['sasl_plain_password'] = self.sasl_password
            
            self.admin_client = KafkaAdminClient(**config)
            self.consumer = KafkaConsumer(**config)
            
            # Tester la connexion
            self.admin_client.list_topics()
            print(f"✓ Connecté au cluster Kafka: {self.bootstrap_servers}")
            return True
            
        except NoBrokersAvailable:
            print(f"✗ Impossible de se connecter à {self.bootstrap_servers}")
            return False
        except Exception as e:
            print(f"✗ Erreur de connexion: {str(e)}")
            return False
    
    def get_cluster_info(self):
        """Récupérer les informations du cluster"""
        try:
            # Récupération des brokers
            brokers = self.admin_client.describe_cluster()
            
            cluster_info = {
                "cluster_id": brokers.get('cluster_id', 'N/A'),
                "controller_broker": brokers.get('controller', 'N/A'),
                "broker_count": len(brokers.get('brokers', []))
            }
            
            # Détails des brokers
            broker_details = []
            for broker in brokers.get('brokers', []):
                broker_details.append({
                    "node_id": broker.nodeId,
                    "host": broker.host,
                    "port": broker.port,
                    "rack": broker.rack if hasattr(broker, 'rack') else 'N/A'
                })
            
            self.audit_results["cluster_info"] = cluster_info
            self.audit_results["brokers"] = broker_details
            
            print(f"\n📊 Informations du cluster:")
            print(f"  - ID du cluster: {cluster_info['cluster_id']}")
            print(f"  - Nombre de brokers: {cluster_info['broker_count']}")
            print(f"  - Controller: {cluster_info['controller_broker']}")
            
        except Exception as e:
            self.add_issue(f"Impossible de récupérer les infos du cluster: {str(e)}", "HIGH")
    
    def audit_topics(self):
        """Audit détaillé des topics"""
        try:
            topics = self.admin_client.list_topics()
            topic_metadata = self.admin_client.describe_topics()
            
            # Exclure les topics internes
            internal_topics = ['__consumer_offsets', '__transaction_state']
            
            for topic_name in topics:
                if topic_name in internal_topics:
                    continue
                
                topic_configs = self.get_topic_configs(topic_name)
                metadata = next((t for t in topic_metadata if t.topic == topic_name), None)
                
                if metadata:
                    topic_info = {
                        "name": topic_name,
                        "partition_count": len(metadata.partitions),
                        "replication_factor": self.get_replication_factor(metadata),
                        "configs": topic_configs,
                        "partitions_details": self.analyze_partitions(metadata)
                    }
                    
                    self.audit_results["topics"][topic_name] = topic_info
                    self.analyze_topic_health(topic_name, topic_info)
            
            print(f"\n📋 Topics audités: {len(self.audit_results['topics'])}")
            
        except Exception as e:
            self.add_issue(f"Erreur lors de l'audit des topics: {str(e)}", "HIGH")
    
    def get_topic_configs(self, topic_name: str) -> Dict:
        """Récupérer les configurations d'un topic"""
        try:
            resource = ConfigResource(ConfigResourceType.TOPIC, topic_name)
            configs = self.admin_client.describe_configs([resource])
            
            config_dict = {}
            for config in configs:
                for entry in config[0].values():
                    config_dict[entry.name] = entry.value
            
            return config_dict
        except:
            return {}
    
    def get_replication_factor(self, metadata) -> int:
        """Calculer le facteur de réplication d'un topic"""
        try:
            if metadata.partitions:
                return len(metadata.partitions[0].replicas)
        except:
            pass
        return 0
    
    def analyze_partitions(self, metadata):
        """Analyser la distribution des partitions"""
        partitions_info = []
        for partition in metadata.partitions:
            partitions_info.append({
                "partition_id": partition.partition,
                "leader": partition.leader,
                "replicas": [r for r in partition.replicas],
                "isr": [i for i in partition.isr],
                "is_healthy": len(partition.isr) == len(partition.replicas)
            })
        return partitions_info
    
    def analyze_topic_health(self, topic_name: str, topic_info: Dict):
        """Analyser la santé d'un topic"""
        # Vérification du facteur de réplication
        rf = topic_info["replication_factor"]
        if rf == 1:
            self.add_issue(
                f"Topic '{topic_name}' a un facteur de réplication de 1 (risque de perte de données)",
                "MEDIUM",
                topic_name
            )
            self.add_recommendation(
                f"Augmenter le facteur de réplication du topic '{topic_name}' à au moins 2 ou 3",
                "MEDIUM"
            )
        elif rf < self.audit_results["cluster_info"].get("broker_count", 0):
            self.add_recommendation(
                f"Considérer l'augmentation du facteur de réplication du topic '{topic_name}' "
                f"pour mieux utiliser les brokers disponibles",
                "LOW"
            )
        
        # Vérification des partitions déséquilibrées
        unhealthy_partitions = [p for p in topic_info["partitions_details"] if not p["is_healthy"]]
        if unhealthy_partitions:
            self.add_issue(
                f"Topic '{topic_name}' a {len(unhealthy_partitions)} partitions avec des problèmes ISR",
                "HIGH",
                topic_name
            )
            self.add_recommendation(
                f"Vérifier les brokers pour le topic '{topic_name}': partitions {unhealthy_partitions}",
                "HIGH"
            )
        
        # Vérification des configurations
        configs = topic_info["configs"]
        
        # Retention time
        retention_ms = configs.get('retention.ms', '604800000')  # 7 jours par défaut
        retention_days = int(retention_ms) / (24 * 3600 * 1000)
        
        if retention_days > 30:
            self.add_issue(
                f"Topic '{topic_name}' a une rétention de {retention_days:.0f} jours (très élevée)",
                "MEDIUM",
                topic_name
            )
        elif retention_days < 1:
            self.add_recommendation(
                f"Topic '{topic_name}' a une rétention très courte, vérifier si adapté au cas d'usage",
                "LOW"
            )
        
        # Cleanup policy
        cleanup_policy = configs.get('cleanup.policy', 'delete')
        if cleanup_policy == 'compact' and topic_info["partition_count"] > 10:
            self.add_tip(
                f"Topic '{topic_name}' utilise la compaction sur {topic_info['partition_count']} partitions, "
                "surveiller les performances et la taille des segments"
            )
    
    def audit_consumer_groups(self):
        """Auditer les groupes de consommateurs"""
        try:
            consumer_groups = self.admin_client.list_consumer_groups()
            active_groups = []
            
            for group in consumer_groups:
                if group.state == 'Stable':
                    active_groups.append(group.group_id)
            
            if active_groups:
                print(f"\n👥 Groupes de consommateurs actifs: {len(active_groups)}")
                
                if len(active_groups) > 100:
                    self.add_recommendation(
                        f"Nombre élevé de groupes de consommateurs ({len(active_groups)}). "
                        "Considérer la suppression des groupes inutilisés",
                        "MEDIUM"
                    )
            
            self.audit_results["consumer_groups"] = active_groups
            
        except Exception as e:
            print(f"⚠️ Impossible d'auditer les groupes de consommateurs: {str(e)}")
    
    def check_security_config(self):
        """Vérifier la configuration de sécurité"""
        security_checks = []
        
        # Vérification de l'authentification
        if self.security_protocol == "PLAINTEXT":
            self.add_issue(
                "Cluster utilise PLAINTEXT (aucune authentification ni chiffrement)",
                "HIGH"
            )
            self.add_recommendation(
                "Migrer vers SASL_SSL pour l'authentification et le chiffrement",
                "HIGH"
            )
        elif self.security_protocol == "SASL_PLAINTEXT":
            self.add_issue(
                "Authentification SASL sans chiffrement (risque d'écoute)",
                "MEDIUM"
            )
            self.add_recommendation(
                "Activer SSL pour chiffrer les communications",
                "MEDIUM"
            )
        
        # ACLs (si supporté)
        try:
            acls = self.admin_client.describe_acls()
            if not acls:
                self.add_recommendation(
                    "Aucune ACL trouvée. Implémenter le contrôle d'accès basé sur les rôles (RBAC)",
                    "MEDIUM"
                )
        except:
            pass
    
    def check_performance_config(self):
        """Vérifier les configurations de performance"""
        # Recommandations générales
        self.add_tip("Configurer `num.network.threads` et `num.io.threads` selon le nombre de cœurs CPU")
        self.add_tip("Ajuster `log.segment.bytes` à 1GB pour la plupart des workloads")
        self.add_tip("Utiliser `compression.type=snappy` ou `zstd` pour réduire l'utilisation du réseau")
        
        # Vérification du nombre de partitions par topic
        for topic_name, topic_info in self.audit_results["topics"].items():
            partitions = topic_info["partition_count"]
            if partitions > 200:
                self.add_issue(
                    f"Topic '{topic_name}' a {partitions} partitions (risque de surcharge du coordinator)",
                    "MEDIUM",
                    topic_name
                )
            elif partitions == 1 and topic_info.get("configs", {}).get("max.message.bytes", 1048576) > 1048576:
                self.add_recommendation(
                    f"Topic '{topic_name}' a une seule partition avec des gros messages, "
                    "augmenter le nombre de partitions pour le parallélisme",
                    "LOW"
                )
    
    def check_data_lag(self):
        """Vérifier le lag potentiel (nécessite JMX ou API spécifique)"""
        self.add_tip("Configurer des alertes sur le consumer lag via Kafka Lag Exporter ou Burrow")
        self.add_tip("Utiliser Cruise Control pour la rééquilibrage automatique des partitions")
    
    def generate_production_tips(self):
        """Générer des conseils de production"""
        tips = [
            "📌 TIPS PRODUCTION:",
            "  • Configurer `min.insync.replicas=2` pour les topics critiques (avec RF=3)",
            "  • Définir `unclean.leader.election.enable=false` pour éviter la perte de données",
            "  • Surveiller les métriques clés: Request Handler Avg Idle %, Network Processor Avg Idle %",
            "  • Utiliser des monitoring stacks: Prometheus + Grafana + JMX Exporter",
            "  • Configurer des alertes sur: under-replicated partitions, offline partitions",
            "  • Planifier la capacité: 10-20% d'espace disque libre par broker",
            "  • Utiliser des clés de messages pour garantir l'ordre dans les partitions",
            "  • Éviter les messages > 1MB sans configuration spécifique",
            "  • Mettre en place une stratégie de rétention adaptée aux besoins métier",
            "  • Documenter les schémas de messages (Avro/Protobuf avec Schema Registry)"
        ]
        
        for tip in tips:
            self.add_tip(tip)
    
    def add_issue(self, message: str, severity: str = "MEDIUM", topic: str = None):
        """Ajouter un problème détecté"""
        self.audit_results["issues"].append({
            "message": message,
            "severity": severity,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_recommendation(self, message: str, priority: str = "MEDIUM"):
        """Ajouter une recommandation"""
        self.audit_results["recommendations"].append({
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_tip(self, message: str):
        """Ajouter un conseil"""
        self.audit_results["tips"].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def run_audit(self):
        """Exécuter l'audit complet"""
        print("\n" + "="*60)
        print("🔍 DÉMARRAGE DE L'AUDIT KAFKA")
        print("="*60)
        
        if not self.connect():
            return False
        
        self.get_cluster_info()
        self.audit_topics()
        self.audit_consumer_groups()
        self.check_security_config()
        self.check_performance_config()
        self.check_data_lag()
        self.generate_production_tips()
        
        return True
    
    def generate_report(self, output_format: str = "console"):
        """Générer le rapport d'audit"""
        if output_format == "json":
            print(json.dumps(self.audit_results, indent=2, default=str))
            return
        
        # Rapport console
        print("\n" + "="*60)
        print("📊 RAPPORT D'AUDIT KAFKA")
        print("="*60)
        
        # Résumé
        print(f"\n✅ ÉTAT GLOBAL:")
        print(f"  • Cluster ID: {self.audit_results['cluster_info'].get('cluster_id', 'N/A')}")
        print(f"  • Brokers: {len(self.audit_results['brokers'])}")
        print(f"  • Topics: {len(self.audit_results['topics'])}")
        print(f"  • Problèmes: {len(self.audit_results['issues'])}")
        print(f"  • Recommandations: {len(self.audit_results['recommendations'])}")
        
        # Problèmes par sévérité
        if self.audit_results['issues']:
            print("\n⚠️ PROBLÈMES DÉTECTÉS:")
            high_issues = [i for i in self.audit_results['issues'] if i['severity'] == 'HIGH']
            medium_issues = [i for i in self.audit_results['issues'] if i['severity'] == 'MEDIUM']
            
            if high_issues:
                print("\n  🔴 CRITIQUES (HIGH):")
                for issue in high_issues:
                    print(f"    • {issue['message']}")
            
            if medium_issues:
                print("\n  🟡 MOYENS (MEDIUM):")
                for issue in medium_issues:
                    print(f"    • {issue['message']}")
        
        # Recommandations
        if self.audit_results['recommendations']:
            print("\n💡 RECOMMANDATIONS:")
            for rec in self.audit_results['recommendations'][:10]:  # Top 10
                print(f"  • [{rec['priority']}] {rec['message']}")
        
        # Conseils
        if self.audit_results['tips']:
            print("\n🎯 CONSEILS & RETOURS D'EXPÉRIENCE:")
            for tip in self.audit_results['tips'][:15]:  # Top 15
                print(f"  {tip['message']}")
        
        # Détail des topics problématiques
        problematic_topics = []
        for topic_name, topic_info in self.audit_results['topics'].items():
            if topic_info['replication_factor'] == 1:
                problematic_topics.append(topic_name)
        
        if problematic_topics:
            print(f"\n📌 Topics avec RF=1 (risque élevé): {', '.join(problematic_topics[:5])}")
        
        print("\n" + "="*60)
        print("🏁 FIN DE L'AUDIT")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Audit complet d\'un cluster Kafka')
    parser.add_argument('--bootstrap-servers', required=True, 
                       help='Serveurs Kafka (ex: localhost:9092,broker2:9092)')
    parser.add_argument('--security-protocol', default='PLAINTEXT',
                       choices=['PLAINTEXT', 'SSL', 'SASL_PLAINTEXT', 'SASL_SSL'],
                       help='Protocole de sécurité')
    parser.add_argument('--sasl-mechanism', choices=['PLAIN', 'SCRAM-SHA-256', 'SCRAM-SHA-512'],
                       help='Mécanisme SASL')
    parser.add_argument('--sasl-username', help='Nom d\'utilisateur SASL')
    parser.add_argument('--sasl-password', help='Mot de passe SASL')
    parser.add_argument('--output', choices=['console', 'json'], default='console',
                       help='Format de sortie')
    
    args = parser.parse_args()
    
    # Création et exécution de l'audit
    auditor = KafkaAuditor(
        bootstrap_servers=args.bootstrap_servers,
        security_protocol=args.security_protocol,
        sasl_mechanism=args.sasl_mechanism,
        sasl_username=args.sasl_username,
        sasl_password=args.sasl_password
    )
    
    if auditor.run_audit():
        auditor.generate_report(output_format=args.output)
        sys.exit(0)
    else:
        print("❌ L'audit a échoué")
        sys.exit(1)


if __name__ == "__main__":
    main()
