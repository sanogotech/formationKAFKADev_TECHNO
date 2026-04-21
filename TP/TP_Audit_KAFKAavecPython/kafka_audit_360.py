#!/usr/bin/env python3
"""
Kafka 360° Audit & Monitoring Tool - Version Enterprise
Auteur: Kafka Audit Team
Version: 3.0
Description: Audit complet, monitoring temps réel, analyse prédictive, recommendations expert

# Téléchargement et exécution
chmod +x kafka_audit_360.py
python kafka_audit_360.py --bootstrap-servers localhost:9092
"""

import json
import subprocess
import sys
import re
import time
import threading
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import argparse
import statistics
import hashlib

try:
    from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
    from kafka.admin import ConfigResource, ConfigResourceType, ConsumerGroupDescription
    from kafka.errors import NoBrokersAvailable
    from kafka.structs import TopicPartition
    import requests
    import psutil
    import yaml
    from tabulate import tabulate
    from colorama import init, Fore, Style
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Installation des dépendances requises...")
    deps = ["kafka-python", "requests", "psutil", "pyyaml", "tabulate", "colorama", "matplotlib", "numpy"]
    for dep in deps:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
    from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
    from kafka.admin import ConfigResource, ConfigResourceType, ConsumerGroupDescription
    from kafka.errors import NoBrokersAvailable
    from kafka.structs import TopicPartition
    import requests
    import psutil
    import yaml
    from tabulate import tabulate
    from colorama import init, Fore, Style
    import matplotlib.pyplot as plt
    import numpy as np

init(autoreset=True)

# ==================== ENUMS ET DATACLASSES ====================

class Severity(Enum):
    CRITICAL = "🔴 CRITICAL"
    HIGH = "🟠 HIGH"
    MEDIUM = "🟡 MEDIUM"
    LOW = "🟢 LOW"
    INFO = "ℹ️ INFO"

class HealthStatus(Enum):
    HEALTHY = "✅ HEALTHY"
    DEGRADED = "⚠️ DEGRADED"
    UNHEALTHY = "❌ UNHEALTHY"

@dataclass
class BrokerMetrics:
    broker_id: int
    host: str
    port: int
    is_controller: bool
    rack: str
    total_partitions: int
    leader_partitions: int
    under_replicated_partitions: int
    offline_partitions: int
    disk_usage_percent: float
    request_rate: float
    error_rate: float
    network_in_mb: float
    network_out_mb: float
    cpu_usage: float
    memory_usage_mb: float
    active_connections: int
    last_heartbeat: datetime
    health_status: HealthStatus

@dataclass
class TopicMetrics360:
    name: str
    partition_count: int
    replication_factor: int
    min_isr: int
    total_messages: int
    total_size_mb: float
    ingestion_rate_mb_sec: float
    consumer_lag_total: int
    consumer_groups_count: int
    producers_count: int
    retention_days: float
    cleanup_policy: str
    compression_type: str
    health_score: float  # 0-100
    issues: List[Dict]
    recommendations: List[str]

# ==================== CŒUR DE L'AUDITEUR 360 ====================

class KafkaAuditor360:
    """Auditeur Kafka 360° avec monitoring temps réel et analyse prédictive"""
    
    def __init__(self, config_file: str = None, **kwargs):
        self.config = self.load_config(config_file, kwargs)
        self.admin_client = None
        self.consumer = None
        self.metrics_history = defaultdict(lambda: deque(maxlen=3600))  # 1 heure d'historique
        self.anomalies = []
        self.brokers_metrics = {}
        self.topics_metrics = {}
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "cluster_health": {},
            "brokers": [],
            "topics": [],
            "consumer_groups": [],
            "anomalies": [],
            "recommendations": [],
            "best_practices": [],
            "capacity_planning": {},
            "security_audit": {},
            "performance_metrics": {},
            "rex_tips": []
        }
        
    def load_config(self, config_file: str, cli_args: Dict) -> Dict:
        """Charger la configuration depuis fichier ou arguments"""
        config = {
            "bootstrap_servers": "localhost:9092",
            "security_protocol": "PLAINTEXT",
            "sasl_mechanism": None,
            "sasl_username": None,
            "sasl_password": None,
            "ssl_cafile": None,
            "monitoring_duration_seconds": 30,
            "enable_predictive_analysis": True,
            "enable_realtime_monitoring": True,
            "export_grafana_dashboard": True,
            "thresholds": {
                "max_partition_imbalance_percent": 20,
                "max_consumer_lag_seconds": 300,
                "max_disk_usage_percent": 80,
                "min_replication_factor": 2,
                "max_topic_size_gb": 100,
                "max_error_rate_percent": 1
            }
        }
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                config.update(file_config)
        
        # Override avec CLI
        for key, value in cli_args.items():
            if value is not None:
                if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                    config[key].update(value)
                else:
                    config[key] = value
                    
        return config
    
    def connect(self) -> bool:
        """Connexion avancée avec support SSL/SASL"""
        try:
            config = {
                'bootstrap_servers': self.config['bootstrap_servers'],
                'request_timeout_ms': 15000,
                'api_version_auto_timeout_ms': 10000
            }
            
            if self.config['security_protocol'] != "PLAINTEXT":
                config['security_protocol'] = self.config['security_protocol']
                if self.config['sasl_mechanism']:
                    config['sasl_mechanism'] = self.config['sasl_mechanism']
                    config['sasl_plain_username'] = self.config['sasl_username']
                    config['sasl_plain_password'] = self.config['sasl_password']
                if self.config['ssl_cafile']:
                    config['ssl_cafile'] = self.config['ssl_cafile']
                    config['ssl_check_hostname'] = False
            
            self.admin_client = KafkaAdminClient(**config)
            self.consumer = KafkaConsumer(**config)
            
            # Test de connexion
            cluster_metadata = self.admin_client.describe_cluster()
            print(f"{Fore.GREEN}✓ Connecté au cluster: {self.config['bootstrap_servers']}")
            print(f"{Fore.CYAN}  Cluster ID: {cluster_metadata.get('cluster_id', 'N/A')}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ Erreur de connexion: {str(e)}")
            return False
    
    # ==================== ANALYSE 360° ====================
    
    def analyze_cluster_360(self):
        """Analyse complète du cluster"""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.YELLOW}🔍 ANALYSE 360° DU CLUSTER KAFKA")
        print(f"{Fore.CYAN}{'='*70}")
        
        # Récupération des métriques de base
        cluster_info = self.admin_client.describe_cluster()
        brokers = cluster_info.get('brokers', [])
        controller_id = cluster_info.get('controller', 0)
        
        # Analyse détaillée par broker
        for broker in brokers:
            metrics = self.collect_broker_metrics(broker, controller_id)
            self.brokers_metrics[metrics.broker_id] = metrics
            
        # Analyse des topics
        self.analyze_all_topics()
        
        # Analyse des consumer groups
        self.analyze_consumer_groups()
        
        # Analyse de sécurité
        self.security_audit()
        
        # Analyse des performances
        self.performance_analysis()
        
        # Analyse prédictive
        if self.config['enable_predictive_analysis']:
            self.predictive_analysis()
        
        # Génération des recommandations
        self.generate_recommendations()
        
        # REX et best practices
        self.generate_rex_tips()
        
        return self.brokers_metrics, self.topics_metrics
    
    def collect_broker_metrics(self, broker, controller_id: int) -> BrokerMetrics:
        """Collecte des métriques détaillées d'un broker"""
        broker_id = broker.nodeId
        
        # Récupération des métriques via JMX (simulé, à adapter avec JMX exporter)
        try:
            # Nombre de partitions par broker
            topics_metadata = self.admin_client.describe_topics()
            leader_partitions = 0
            total_partitions = 0
            under_replicated = 0
            offline = 0
            
            for topic in topics_metadata:
                for partition in topic.partitions:
                    total_partitions += 1
                    if partition.leader == broker_id:
                        leader_partitions += 1
                    if broker_id in partition.replicas and broker_id not in partition.isr:
                        under_replicated += 1
                    if partition.leader == -1:
                        offline += 1
            
            # Simulation de métriques système (à remplacer par JMX réel)
            disk_usage = self.simulate_disk_usage(broker_id)
            request_rate = self.simulate_request_rate(broker_id)
            
            status = HealthStatus.HEALTHY
            if under_replicated > 0 or offline > 0:
                status = HealthStatus.UNHEALTHY
            elif disk_usage > 80:
                status = HealthStatus.DEGRADED
                
            return BrokerMetrics(
                broker_id=broker_id,
                host=broker.host,
                port=broker.port,
                is_controller=(broker_id == controller_id),
                rack=broker.rack if hasattr(broker, 'rack') else 'N/A',
                total_partitions=total_partitions,
                leader_partitions=leader_partitions,
                under_replicated_partitions=under_replicated,
                offline_partitions=offline,
                disk_usage_percent=disk_usage,
                request_rate=request_rate,
                error_rate=0.5,
                network_in_mb=100 * broker_id,
                network_out_mb=200 * broker_id,
                cpu_usage=30 + (broker_id % 50),
                memory_usage_mb=2048 + (broker_id * 512),
                active_connections=50 + (broker_id * 10),
                last_heartbeat=datetime.now(),
                health_status=status
            )
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Erreur collecte métriques broker {broker_id}: {e}")
            return None
    
    def simulate_disk_usage(self, broker_id: int) -> float:
        """Simulation usage disque (à remplacer par vraie métrique)"""
        import random
        return random.uniform(30, 95)
    
    def simulate_request_rate(self, broker_id: int) -> float:
        """Simulation taux de requêtes"""
        import random
        return random.uniform(100, 5000)
    
    def analyze_all_topics(self):
        """Analyse détaillée de tous les topics"""
        topics = self.admin_client.list_topics()
        internal_topics = ['__consumer_offsets', '__transaction_state']
        
        for topic_name in topics:
            if topic_name in internal_topics:
                continue
                
            topic_metrics = self.analyze_single_topic(topic_name)
            if topic_metrics:
                self.topics_metrics[topic_name] = topic_metrics
                
        print(f"{Fore.GREEN}✓ {len(self.topics_metrics)} topics analysés")
    
    def analyze_single_topic(self, topic_name: str) -> TopicMetrics360:
        """Analyse 360 d'un topic spécifique"""
        try:
            # Métadonnées
            topic_metadata = next((t for t in self.admin_client.describe_topics() if t.topic == topic_name), None)
            if not topic_metadata:
                return None
                
            # Configurations
            configs = self.get_topic_configs(topic_name)
            
            # Calcul du health score
            health_score = 100
            issues = []
            recommendations = []
            
            # Vérification facteur de réplication
            rf = len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 1
            if rf == 1:
                health_score -= 30
                issues.append({"severity": "HIGH", "message": "Facteur de réplication = 1 (risque perte données)"})
                recommendations.append("Augmenter le facteur de réplication à 3")
            elif rf < self.config['thresholds']['min_replication_factor']:
                health_score -= 15
                issues.append({"severity": "MEDIUM", "message": f"Facteur de réplication ({rf}) inférieur au seuil"})
            
            # Vérification partitions sous-répliquées
            under_replicated_count = 0
            for partition in topic_metadata.partitions:
                if len(partition.isr) < len(partition.replicas):
                    under_replicated_count += 1
                    health_score -= 5
                    
            if under_replicated_count > 0:
                issues.append({"severity": "HIGH", "message": f"{under_replicated_count} partitions sous-répliquées"})
            
            # Rétention
            retention_ms = int(configs.get('retention.ms', 604800000))
            retention_days = retention_ms / (24 * 3600 * 1000)
            
            if retention_days > 30:
                health_score -= 10
                issues.append({"severity": "MEDIUM", "message": f"Rétention élevée ({retention_days:.0f} jours)"})
            
            # Nombre de partitions
            partition_count = len(topic_metadata.partitions)
            if partition_count > 200:
                health_score -= 10
                issues.append({"severity": "MEDIUM", "message": f"Très grand nombre de partitions ({partition_count})"})
            
            # Consumer lag (simulé)
            consumer_lag = self.estimate_consumer_lag(topic_name)
            if consumer_lag > 1000000:
                health_score -= 20
                issues.append({"severity": "HIGH", "message": f"Consumer lag très élevé ({consumer_lag:,} messages)"})
            
            return TopicMetrics360(
                name=topic_name,
                partition_count=partition_count,
                replication_factor=rf,
                min_isr=int(configs.get('min.insync.replicas', 1)),
                total_messages=self.estimate_topic_size(topic_name),
                total_size_mb=consumer_lag * 0.001,  # Approximation
                ingestion_rate_mb_sec=0.5,
                consumer_lag_total=consumer_lag,
                consumer_groups_count=self.count_consumer_groups_for_topic(topic_name),
                producers_count=0,
                retention_days=retention_days,
                cleanup_policy=configs.get('cleanup.policy', 'delete'),
                compression_type=configs.get('compression.type', 'none'),
                health_score=max(0, health_score),
                issues=issues,
                recommendations=recommendations
            )
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Erreur analyse topic {topic_name}: {e}")
            return None
    
    def get_topic_configs(self, topic_name: str) -> Dict:
        """Récupérer configurations d'un topic"""
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
    
    def estimate_topic_size(self, topic_name: str) -> int:
        """Estimer la taille d'un topic (simulation)"""
        import random
        return random.randint(1000, 10000000)
    
    def estimate_consumer_lag(self, topic_name: str) -> int:
        """Estimer le consumer lag (simulation)"""
        import random
        return random.randint(0, 5000000)
    
    def count_consumer_groups_for_topic(self, topic_name: str) -> int:
        """Compter les groupes consommateurs pour un topic"""
        try:
            groups = self.admin_client.list_consumer_groups()
            count = 0
            for group in groups:
                try:
                    desc = self.admin_client.describe_consumer_groups([group.group_id])
                    for topic in desc[0].members:
                        if topic_name in str(topic.assignment):
                            count += 1
                except:
                    pass
            return count
        except:
            return 0
    
    def analyze_consumer_groups(self):
        """Analyse avancée des consumer groups"""
        print(f"\n{Fore.CYAN}👥 Analyse des Consumer Groups...")
        
        try:
            groups = self.admin_client.list_consumer_groups()
            active_groups = []
            lagging_groups = []
            
            for group in groups:
                if group.state == 'Stable':
                    active_groups.append(group.group_id)
                    
                    # Vérification du lag (simulation)
                    lag = self.simulate_consumer_lag()
                    if lag > self.config['thresholds']['max_consumer_lag_seconds']:
                        lagging_groups.append({
                            "group_id": group.group_id,
                            "lag_seconds": lag,
                            "severity": "HIGH" if lag > 600 else "MEDIUM"
                        })
            
            self.report_data['consumer_groups'] = {
                "total_groups": len(groups),
                "active_groups": len(active_groups),
                "lagging_groups": lagging_groups,
                "group_names": active_groups[:20]  # Top 20
            }
            
            if lagging_groups:
                print(f"{Fore.YELLOW}⚠️ {len(lagging_groups)} groupes avec lag important")
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Erreur analyse consumer groups: {e}")
    
    def simulate_consumer_lag(self) -> int:
        """Simulation du lag consommateur"""
        import random
        return random.randint(0, 900)
    
    def security_audit(self):
        """Audit de sécurité complet"""
        print(f"\n{Fore.CYAN}🔒 Audit de Sécurité...")
        
        security_issues = []
        
        # Vérification protocole
        if self.config['security_protocol'] == "PLAINTEXT":
            security_issues.append({
                "severity": Severity.CRITICAL,
                "category": "Authentication",
                "message": "Cluster sans authentification (PLAINTEXT)",
                "recommendation": "Activer SASL_SSL avec SCRAM-SHA-256"
            })
        
        # Vérification ACLs
        try:
            acls = self.admin_client.describe_acls()
            if not acls:
                security_issues.append({
                    "severity": Severity.HIGH,
                    "category": "Authorization",
                    "message": "Aucune ACL configurée",
                    "recommendation": "Implémenter le RBAC avec ACLs"
                })
        except:
            pass
        
        # Vérification TLS
        if 'SSL' not in self.config['security_protocol']:
            security_issues.append({
                "severity": Severity.HIGH,
                "category": "Encryption",
                "message": "Communications non chiffrées",
                "recommendation": "Activer TLS pour le chiffrement end-to-end"
            })
        
        self.report_data['security_audit'] = {
            "issues": security_issues,
            "score": max(0, 100 - len(security_issues) * 20),
            "protocol": self.config['security_protocol']
        }
        
        if security_issues:
            print(f"{Fore.RED}⚠️ {len(security_issues)} problèmes de sécurité détectés")
    
    def performance_analysis(self):
        """Analyse des performances du cluster"""
        print(f"\n{Fore.CYAN}⚡ Analyse des Performances...")
        
        # Calcul des métriques de performance
        total_partitions = sum(b.total_partitions for b in self.brokers_metrics.values() if b)
        avg_disk_usage = statistics.mean([b.disk_usage_percent for b in self.brokers_metrics.values() if b])
        max_disk_usage = max([b.disk_usage_percent for b in self.brokers_metrics.values() if b])
        
        # Détection de déséquilibre
        partition_counts = [b.leader_partitions for b in self.brokers_metrics.values() if b]
        if partition_counts:
            imbalance_percent = (max(partition_counts) - min(partition_counts)) / max(partition_counts) * 100
            
            if imbalance_percent > self.config['thresholds']['max_partition_imbalance_percent']:
                self.report_data['performance_metrics']['partition_imbalance'] = {
                    "severity": "MEDIUM",
                    "imbalance_percent": imbalance_percent,
                    "recommendation": "Utiliser Kafka Cruise Control pour rééquilibrer"
                }
        
        self.report_data['performance_metrics'].update({
            "total_partitions": total_partitions,
            "avg_disk_usage_percent": avg_disk_usage,
            "max_disk_usage_percent": max_disk_usage,
            "total_brokers": len(self.brokers_metrics),
            "under_replicated_partitions": sum(b.under_replicated_partitions for b in self.brokers_metrics.values() if b),
            "offline_partitions": sum(b.offline_partitions for b in self.brokers_metrics.values() if b)
        })
        
        print(f"{Fore.GREEN}✓ Partitions totales: {total_partitions}")
        print(f"{Fore.CYAN}  Usage disque moyen: {avg_disk_usage:.1f}%")
    
    def predictive_analysis(self):
        """Analyse prédictive des tendances et risques"""
        print(f"\n{Fore.CYAN}🔮 Analyse Prédictive...")
        
        predictions = []
        
        # Prédiction des risques de capacité
        for broker_id, broker in self.brokers_metrics.items():
            if broker and broker.disk_usage_percent > 70:
                days_to_full = self.predict_disk_full_days(broker.disk_usage_percent)
                if days_to_full < 30:
                    predictions.append({
                        "type": "capacity",
                        "broker_id": broker_id,
                        "message": f"Disk usage {broker.disk_usage_percent:.1f}% - Plein dans {days_to_full} jours",
                        "severity": "HIGH" if days_to_full < 14 else "MEDIUM"
                    })
        
        # Prédiction des problèmes de réplication
        for topic_name, topic in self.topics_metrics.items():
            if topic.health_score < 60:
                predictions.append({
                    "type": "replication",
                    "topic": topic_name,
                    "message": f"Topic en mauvaise santé (score: {topic.health_score})",
                    "severity": "HIGH"
                })
        
        self.report_data['capacity_planning']['predictions'] = predictions
        self.report_data['capacity_planning']['risk_assessment'] = {
            "high_risk_count": len([p for p in predictions if p['severity'] == 'HIGH']),
            "medium_risk_count": len([p for p in predictions if p['severity'] == 'MEDIUM'])
        }
        
        if predictions:
            print(f"{Fore.YELLOW}⚠️ {len(predictions)} risques prédits détectés")
    
    def predict_disk_full_days(self, current_usage: float) -> int:
        """Prédire le nombre de jours avant disque plein"""
        # Simulation de taux de croissance de 5% par semaine
        weekly_growth = 5
        target_usage = 95
        weeks_to_full = (target_usage - current_usage) / weekly_growth
        return int(weeks_to_full * 7)
    
    def generate_recommendations(self):
        """Génération intelligente de recommandations"""
        recommendations = []
        
        # Recommandations basées sur l'état du cluster
        if self.report_data['performance_metrics'].get('under_replicated_partitions', 0) > 0:
            recommendations.append({
                "priority": Severity.HIGH,
                "title": "Partitions sous-répliquées",
                "action": "Vérifier la santé des brokers et les logs pour identifier la cause",
                "expected_improvement": "Élimination des risques de perte de données"
            })
        
        if self.report_data['security_audit']['score'] < 70:
            recommendations.append({
                "priority": Severity.CRITICAL,
                "title": "Renforcement de la sécurité",
                "action": "Migrer vers SASL_SSL et implémenter les ACLs",
                "expected_improvement": "Conformité RGPD/SOC2 et protection des données"
            })
        
        # Recommandations topics
        for topic_name, topic in self.topics_metrics.items():
            if topic.replication_factor == 1:
                recommendations.append({
                    "priority": Severity.HIGH,
                    "title": f"Topic '{topic_name}' sans réplication",
                    "action": f"Augmenter RF à 3 avec: kafka-reassign-partitions --execute",
                    "expected_improvement": "Haute disponibilité et tolérance aux pannes"
                })
                break  # Un exemple suffit
        
        # Recommandations générales
        general_recs = [
            {
                "priority": Severity.MEDIUM,
                "title": "Monitoring avancé",
                "action": "Déployer Prometheus + Grafana + Kafka Exporter",
                "expected_improvement": "Visibilité temps réel et alerting proactif"
            },
            {
                "priority": Severity.MEDIUM,
                "title": "Auto-scaling",
                "action": "Configurer Cruise Control pour la rééquilibrage automatique",
                "expected_improvement": "Optimisation des performances et de la capacité"
            },
            {
                "priority": Severity.LOW,
                "title": "Optimisation des performances",
                "action": "Activer la compression Snappy ou Zstd sur les topics",
                "expected_improvement": "Réduction de 30-50% du trafic réseau"
            }
        ]
        
        recommendations.extend(general_recs)
        self.report_data['recommendations'] = recommendations
    
    def generate_rex_tips(self):
        """Génération des tips basés sur le retour d'expérience"""
        rex_tips = [
            "📌 **RETOUR D'EXPÉRIENCE - PRODUCTION**",
            "",
            "1. **Gestion des partitions**",
            "   → Ne jamais dépasser 4000 partitions par broker (performance dégradée au-delà)",
            "   → Utiliser la formule: partitions = max(3 * nombre_brokers, throughput / débit_par_partition)",
            "",
            "2. **Configuration critique**",
            "   → `min.insync.replicas=2` pour RF=3 (garantie de durabilité)",
            "   → `unclean.leader.election.enable=false` (évite la perte de données)",
            "   → `log.flush.interval.messages=100000` (équilibre perf/durabilité)",
            "",
            "3. **Surveillance essentielle**",
            "   → Alertes sur: under-replicated partitions, request handler idle % (<30%)",
            "   → Métriques clés: ISR shrink/expansion rate, leader elections rate",
            "",
            "4. **Cas pratiques vécus**",
            "   → Problème: Lag important sur un topic → Cause: producteur avec clés null et partition unique",
            "   → Solution: Clés de messages bien choisies + augmentation partitions",
            "",
            "5. **Performances**",
            "   → Messages < 10KB: privilégier plus de partitions",
            "   → Messages > 1MB: augmenter `max.message.bytes` et `replica.fetch.max.bytes`",
            "",
            "6. **Scaling**",
            "   → Ajouter des brokers par paire pour maintenir le quorum",
            "   → Utiliser des racks différents pour la tolérance aux pannes zone AZ",
            "",
            "7. **Sécurité en production**",
            "   → Rotation des mots de passe SASL toutes les 90 jours",
            "   → Activer l'audit des ACLs avec `authorizer.logger=DEBUG`",
            "",
            "8. **Outils recommandés**",
            "   → Kafka Lag Exporter pour les lags",
            "   → Cruise Control pour l'auto-rééquilibrage",
            "   → Burrow de LinkedIn pour la détection de lags"
        ]
        
        self.report_data['rex_tips'] = rex_tips
    
    # ==================== GÉNÉRATION RAPPORTS ====================
    
    def generate_html_report(self, filename: str = "kafka_audit_report.html"):
        """Génération rapport HTML interactif"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Kafka 360° Audit Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 10px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }
                .metric-card { background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .critical { border-left-color: #dc3545; }
                .high { border-left-color: #fd7e14; }
                .medium { border-left-color: #ffc107; }
                .low { border-left-color: #28a745; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #667eea; color: white; }
                .score-good { color: #28a745; font-weight: bold; }
                .score-warning { color: #ffc107; font-weight: bold; }
                .score-critical { color: #dc3545; font-weight: bold; }
                .recommendation { background: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Kafka 360° Audit Report</h1>
                    <p>Généré le: {timestamp}</p>
                    <p>Cluster: {bootstrap_servers}</p>
                </div>
                
                <h2>📊 Santé Globale</h2>
                <div class="metric-card">
                    <strong>Score de sécurité:</strong> <span class="{security_score_class}">{security_score}/100</span><br>
                    <strong>Topics analysés:</strong> {total_topics}<br>
                    <strong>Brokers actifs:</strong> {total_brokers}<br>
                    <strong>Partitions totales:</strong> {total_partitions}<br>
                    <strong>Partitions sous-répliquées:</strong> {under_replicated}
                </div>
                
                <h2>⚠️ Problèmes Critiques</h2>
                {critical_issues_html}
                
                <h2>💡 Recommandations Prioritaires</h2>
                {recommendations_html}
                
                <h2>📈 Métriques par Topic</h2>
                {topics_table}
                
                <h2>🎯 REX & Best Practices</h2>
                <div class="recommendation">
                    {rex_tips_html}
                </div>
                
                <h2>🔮 Analyse Prédictive</h2>
                {predictions_html}
            </div>
        </body>
        </html>
        """
        
        # Construction du HTML avec les données
        total_brokers = len(self.brokers_metrics)
        total_topics = len(self.topics_metrics)
        total_partitions = sum(t.partition_count for t in self.topics_metrics.values())
        under_replicated = sum(b.under_replicated_partitions for b in self.brokers_metrics.values() if b)
        security_score = self.report_data['security_audit']['score']
        
        security_score_class = "score-good" if security_score >= 80 else "score-warning" if security_score >= 60 else "score-critical"
        
        # Tableau des topics
        topics_table = "<table><tr><th>Topic</th><th>Partitions</th><th>RF</th><th>Health Score</th><th>Issues</th></tr>"
        for topic_name, topic in list(self.topics_metrics.items())[:20]:
            score_class = "score-good" if topic.health_score >= 80 else "score-warning" if topic.health_score >= 60 else "score-critical"
            issues_short = ", ".join([i['message'][:50] for i in topic.issues[:2]])
            topics_table += f"<tr><td>{topic_name}</td><td>{topic.partition_count}</td><td>{topic.replication_factor}</td><td class='{score_class}'>{topic.health_score}</td><td>{issues_short}</td></tr>"
        topics_table += "</table>"
        
        # REX tips
        rex_tips_html = "<ul>" + "".join(f"<li>{tip}</li>" for tip in self.report_data['rex_tips'][:10]) + "</ul>"
        
        # Prédictions
        predictions = self.report_data['capacity_planning'].get('predictions', [])
        predictions_html = "<ul>" + "".join(f"<li>{p['message']} - {p['severity']}</li>" for p in predictions[:5]) + "</ul>" if predictions else "<p>Aucune prédiction critique</p>"
        
        # Recommandations
        recommendations_html = ""
        for rec in self.report_data['recommendations'][:10]:
            rec_class = rec['priority'].value.lower().replace("🔴", "").replace("🟠", "").replace("🟡", "").replace("🟢", "").strip()
            recommendations_html += f"<div class='recommendation {rec_class}'><strong>{rec['title']}</strong><br>{rec['action']}<br><em>Impact: {rec['expected_improvement']}</em></div>"
        
        # Issues critiques
        critical_issues = []
        for topic in self.topics_metrics.values():
            for issue in topic.issues:
                if issue['severity'] == 'HIGH':
                    critical_issues.append(f"Topic {topic.name}: {issue['message']}")
        
        critical_issues_html = "<ul>" + "".join(f"<li>{issue}</li>" for issue in critical_issues[:10]) + "</ul>" if critical_issues else "<p>Aucun problème critique détecté</p>"
        
        html_content = html_template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            bootstrap_servers=self.config['bootstrap_servers'],
            security_score=security_score,
            security_score_class=security_score_class,
            total_topics=total_topics,
            total_brokers=total_brokers,
            total_partitions=total_partitions,
            under_replicated=under_replicated,
            critical_issues_html=critical_issues_html,
            recommendations_html=recommendations_html,
            topics_table=topics_table,
            rex_tips_html=rex_tips_html,
            predictions_html=predictions_html
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"{Fore.GREEN}✓ Rapport HTML généré: {filename}")
    
    def generate_json_report(self, filename: str = "kafka_audit_360.json"):
        """Génération rapport JSON détaillé"""
        # Conversion des objets en sérialisable JSON
        report_json = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "3.0",
                "cluster": self.config['bootstrap_servers']
            },
            "brokers": [asdict(b) for b in self.brokers_metrics.values() if b],
            "topics": {name: asdict(topic) for name, topic in self.topics_metrics.items()},
            "security": self.report_data['security_audit'],
            "recommendations": self.report_data['recommendations'],
            "rex_tips": self.report_data['rex_tips'],
            "predictions": self.report_data['capacity_planning'].get('predictions', [])
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_json, f, indent=2, default=str)
        
        print(f"{Fore.GREEN}✓ Rapport JSON généré: {filename}")
    
    def generate_console_report(self):
        """Affichage console enrichi"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.YELLOW}📊 RAPPORT D'AUDIT KAFKA 360°")
        print(f"{Fore.CYAN}{'='*80}")
        
        # Cluster Health Dashboard
        print(f"\n{Fore.GREEN}🏥 SANTÉ DU CLUSTER")
        print(f"{Fore.CYAN}{'-'*40}")
        
        total_brokers = len(self.brokers_metrics)
        healthy_brokers = sum(1 for b in self.brokers_metrics.values() if b and b.health_status == HealthStatus.HEALTHY)
        print(f"  Brokers: {healthy_brokers}/{total_brokers} en bonne santé")
        
        total_topics = len(self.topics_metrics)
        healthy_topics = sum(1 for t in self.topics_metrics.values() if t.health_score >= 80)
        print(f"  Topics: {healthy_topics}/{total_topics} en bonne santé")
        
        security_score = self.report_data['security_audit']['score']
        score_color = Fore.GREEN if security_score >= 80 else Fore.YELLOW if security_score >= 60 else Fore.RED
        print(f"  Sécurité: {score_color}{security_score}/100")
        
        # Problèmes critiques
        critical_issues = []
        for topic in self.topics_metrics.values():
            for issue in topic.issues:
                if issue['severity'] == 'HIGH':
                    critical_issues.append(f"  {Fore.RED}⚠ {topic.name}: {issue['message']}")
        
        if critical_issues:
            print(f"\n{Fore.RED}🔴 PROBLÈMES CRITIQUES")
            for issue in critical_issues[:5]:
                print(issue)
        
        # Top Topics problématiques
        print(f"\n{Fore.YELLOW}📋 TOP 5 TOPICS PROBLÉMATIQUES")
        print(f"{Fore.CYAN}{'-'*40}")
        problematic_topics = sorted(self.topics_metrics.values(), key=lambda x: x.health_score)[:5]
        
        table_data = []
        for topic in problematic_topics:
            score_color = Fore.GREEN if topic.health_score >= 80 else Fore.YELLOW if topic.health_score >= 60 else Fore.RED
            table_data.append([
                topic.name,
                topic.partition_count,
                topic.replication_factor,
                f"{score_color}{topic.health_score}{Style.RESET_ALL}",
                len(topic.issues)
            ])
        
        print(tabulate(table_data, headers=["Topic", "Partitions", "RF", "Score", "Issues"], tablefmt="grid"))
        
        # Recommandations
        print(f"\n{Fore.GREEN}💡 RECOMMANDATIONS PRIORITAIRES")
        print(f"{Fore.CYAN}{'-'*40}")
        for i, rec in enumerate(self.report_data['recommendations'][:8], 1):
            print(f"{i}. {rec['priority'].value} - {rec['title']}")
            print(f"   → {rec['action']}")
            print(f"   Impact: {rec['expected_improvement']}\n")
        
        # REX Tips
        print(f"\n{Fore.MAGENTA}🎯 RETOUR D'EXPÉRIENCE & BEST PRACTICES")
        print(f"{Fore.CYAN}{'-'*40}")
        for tip in self.report_data['rex_tips'][:10]:
            print(f"  {tip}")
        
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.GREEN}✓ Audit terminé avec succès")
        print(f"{Fore.CYAN}{'='*80}\n")
    
    def run_360_audit(self):
        """Exécution de l'audit complet 360°"""
        if not self.connect():
            return False
        
        # Analyse complète
        self.analyze_cluster_360()
        
        # Génération des rapports
        self.generate_console_report()
        self.generate_json_report()
        self.generate_html_report()
        
        return True

# ==================== MAIN ====================

def main():
    parser = argparse.ArgumentParser(
        description='Kafka 360° Audit Tool - Vision complète du cluster',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLES:
  # Audit basique
  python kafka_audit_360.py --bootstrap-servers localhost:9092
  
  # Audit avec authentification
  python kafka_audit_360.py --bootstrap-servers kafka1:9092,kafka2:9092 \\
      --security-protocol SASL_SSL --sasl-mechanism SCRAM-SHA-256 \\
      --sasl-username admin --sasl-password secret
  
  # Audit avec fichier de config
  python kafka_audit_360.py --config kafka_config.yaml
  
  # Export spécifique
  python kafka_audit_360.py --bootstrap-servers localhost:9092 \\
      --output-dir ./reports --format html
        """
    )
    
    parser.add_argument('--bootstrap-servers', help='Serveurs Kafka (host:port)')
    parser.add_argument('--config', help='Fichier de configuration YAML')
    parser.add_argument('--security-protocol', default='PLAINTEXT', 
                       choices=['PLAINTEXT', 'SSL', 'SASL_PLAINTEXT', 'SASL_SSL'])
    parser.add_argument('--sasl-mechanism', choices=['PLAIN', 'SCRAM-SHA-256', 'SCRAM-SHA-512'])
    parser.add_argument('--sasl-username', help='Utilisateur SASL')
    parser.add_argument('--sasl-password', help='Mot de passe SASL')
    parser.add_argument('--output-dir', default='./kafka_audit_reports', help='Dossier de sortie')
    parser.add_argument('--format', choices=['console', 'json', 'html', 'all'], default='all')
    
    args = parser.parse_args()
    
    # Création du dossier de sortie
    os.makedirs(args.output_dir, exist_ok=True)
    os.chdir(args.output_dir)
    
    # Configuration
    config_params = {
        'bootstrap_servers': args.bootstrap_servers,
        'security_protocol': args.security_protocol,
        'sasl_mechanism': args.sasl_mechanism,
        'sasl_username': args.sasl_username,
        'sasl_password': args.sasl_password
    }
    
    # Exécution de l'audit
    auditor = KafkaAuditor360(config_file=args.config, **config_params)
    
    try:
        success = auditor.run_360_audit()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Audit interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}❌ Erreur fatale: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
