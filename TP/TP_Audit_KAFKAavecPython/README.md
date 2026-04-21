
# 📋 KAFKA PRODUCTION - 40 RÈGLES D'OR À RESPECTER

## Guide des bonnes pratiques pour un cluster Kafka en production
*Version 1.0 - Basé sur des retours d'expérience terrain*

---

## 🏗️ ARCHITECTURE & CONFIGURATION CLUSTER

### 1. Facteur de réplication minimum (RF=3)
**Règle:** Tous les topics critiques doivent avoir un facteur de réplication de 3 minimum.
**Pourquoi:** Tolérance à la perte de 2 brokers sans perte de données.
**Configuration:** `--replication-factor 3` lors de la création du topic

### 2. min.insync.replicas = 2
**Règle:** Configurer `min.insync.replicas=2` pour les topics avec RF=3.
**Pourquoi:** Garantit qu'au moins 2 replicas ont accusé réception avant d'accuser réception au producteur.
**Impact:** Évite la perte de données en cas de panne.

### 3. unclean.leader.election.enable = false
**Règle:** Désactiver l'élection de leader non "clean".
**Pourquoi:** Empêche qu'un replica hors ISR devienne leader (risque de perte de données).
**Valeur:** `unclean.leader.election.enable=false`

### 4. Éviter PLAINTEXT en production
**Règle:** Proscrire le protocole PLAINTEXT en production.
**Alternatives:** SASL_SSL avec SCRAM-SHA-256 ou Kerberos.
**Audit:** Vérifier régulièrement l'absence de brokers en PLAINTEXT.

### 5. Séparer les workloads
**Règle:** Isoler les topics sensibles sur des brokers dédiés.
**Mise en œuvre:** Utiliser les racks et les tags brokers.
**Cas d'usage:** Logs vs transactions vs métriques.

### 6. Limiter le nombre de partitions par broker
**Règle:** Maximum 4000 partitions par broker (2000 recommandé).
**Pourquoi:** Au-delà, les performances du controller se dégradent.
**Surveillance:** `kafka.controller:type=KafkaController` metrics.

### 7. Éviter les partitions uniques pour les gros volumes
**Règle:** Jamais de partition unique pour les topics à haut débit (>10MB/s).
**Calcul:** Partitions = max(3 * brokers, débit_MB/s / 10).
**Conséquence:** Le parallélisme consommateur est limité par le nombre de partitions.

### 8. Configuration des segments logs
**Règle:** `log.segment.bytes=1GB` (défaut 1GB est bien).
**Règle:** `log.retention.check.interval.ms=300000` (5 minutes).
**Optimisation:** Ajuster selon la retention policy.

---

## 🔒 SÉCURITÉ & AUTHENTIFICATION

### 9. Authentification obligatoire
**Règle:** Tous les accès (prod, cons, admin) nécessitent authentification.
**Exceptions:** Aucune, pas même en lecture seule.
**Standards:** SASL/SCRAM pour la compatibilité, Kerberos pour la sécurité maximale.

### 10. Chiffrement TLS/SSL
**Règle:** Chiffrement TLS pour toutes les communications inter-brokers et clients.
**Certificats:** Rotation automatique tous les 90 jours.
**Vérification:** Activer `ssl.client.auth=required` pour le mutual TLS.

### 11. ACLs granulaires
**Règle:** Principe du moindre privilège pour les ACLs.
**Exemple:** 
```bash
# Lecture seule sur topic spécifique
kafka-acls --add --allow-principal User:app --operation Read --topic transactions
```
**Audit:** Vérifier mensuellement les ACLs orphelines.

### 12. Sécuriser __consumer_offsets
**Règle:** Restreindre l'accès au topic interne __consumer_offsets.
**Pourquoi:** Contient des métadonnées sensibles sur les consommateurs.
**ACL:** `--deny-principal User:* --operation All --topic __consumer_offsets`

### 13. Rotation des secrets
**Règle:** Rotation des mots de passe SASL tous les 90 jours minimum.
**Process:** Script automatisé sans downtime.
**Outils:** HashiCorp Vault ou AWS Secrets Manager.

### 14. Audit logs activés
**Règle:** Activer les logs d'audit pour toutes les opérations admin.
**Configuration:** `authorizer.logger=DEBUG`
**Conservation:** 12 mois minimum pour conformité.

---

## 📊 MONITORING & ALERTING

### 15. Surveiller les métriques critiques
**Règle:** Dashboards obligatoires pour les métriques clés.
**Métriques essentielles:**
- Under-replicated partitions
- Offline partitions
- ISR shrink/expansion rate
- Request handler idle %
- Network processor idle %

### 16. Alerting proactif
**Règle:** Alertes configurées sur tous les seuils critiques.
**Seuil 1 (Warning):** Lag > 10k messages, disque > 75%
**Seuil 2 (Critical):** Lag > 100k messages, disque > 85%
**Seuil 3 (Urgent):** Under-replicated > 0, offline partitions > 0

### 17. Monitoring des consumer lags
**Règle:** Surveillance temps réel des lags par consumer group.
**Outils recommandés:**
- Kafka Lag Exporter (Lightbend)
- Burrow (LinkedIn)
- Confluent Control Center

### 18. Logs centralisés
**Règle:** Tous les logs Kafka centralisés dans ELK/Splunk.
**Logs requis:** broker.log, controller.log, kafka-authorizer.log
**Rétention:** 30 jours minimum.

### 19. Tracing distribué
**Règle:** Instrumenter les producteurs et consommateurs avec OpenTelemetry.
**Headers:** Injecter `traceparent` dans les messages.
**Outils:** Jaeger, Zipkin ou AWS X-Ray.

### 20. Métriques JMX exposées
**Règle:** Exposer JMX sur tous les brokers avec authentification.
**Port:** 9999 (dédié, firewallé).
**Collecte:** Prometheus JMX Exporter.

---

## ⚡ PERFORMANCE & OPTIMISATION

### 21. Compression activée
**Règle:** Activer la compression sur tous les topics de production.
**Choix:** Snappy (équilibre) ou Zstd (meilleur ratio).
**Gain:** 30-50% de réduction du trafic réseau.

### 22. Batching optimal
**Règle:** Configurer les producteurs avec batch.size=16384 (16KB) et linger.ms=5-10ms.
**Pourquoi:** Maximise le débit sans augmenter trop la latence.
**Ajustement:** Monitorer `batch-size-avg` et `requests-in-flight`.

### 23. Tampons réseau suffisants
**Règle:** `socket.send.buffer.bytes=1MB` et `socket.receive.buffer.bytes=1MB`.
**OS:** Augmenter `net.core.wmem_max` et `net.core.rmem_max`.
**Vérification:** `ss -m` pour voir les buffers réels.

### 24. Éviter les messages > 1MB
**Règle:** Messages > 1MB nécessitent une configuration spécifique.
**Si nécessaire:** Augmenter `max.message.bytes`, `replica.fetch.max.bytes`, `message.max.bytes`.
**Alternative:** Stocker les gros objets dans S3 et envoyer l'URL.

### 25. Nombre de threads ajusté
**Règle:** `num.network.threads = cores * 2`
**Règle:** `num.io.threads = cores * 2`
**Règle:** `background.threads = 10` (défaut)

### 26. File descriptors élevés
**Règle:** `ulimit -n = 100000` minimum.
**Vérification:** `lsof -p <broker_pid> | wc -l` en production.
**Symptôme:** Erreurs "Too many open files".

### 27. Cache OS réglé
**Règle:** Laisser l'OS gérer le cache (dirty_ratio=20).
**Pourquoi:** Kafka utilise intensément la mémoire paginée.
**Monitor:** `cat /proc/meminfo | grep -i dirty`

### 28. JVM Heap optimal
**Règle:** Heap JVM = 5-10GB max, même sur machines avec 64GB+ RAM.
**Pourquoi:** Le reste sert au cache OS.
**GC:** G1GC avec `MaxGCPauseMillis=20`.

---

## 🔄 OPÉRATIONS & MAINTENANCE

### 29. Stratégie de rétention adaptée
**Règle:** Définir `retention.ms` selon les besoins métier.
**Exemples:**
- Logs applicatifs: 7-30 jours
- Événements métier: 90 jours
- Données réglementaires: 365+ jours

### 30. Plan de capacité
**Règle:** Provisionner 30-40% d'espace disque supplémentaire.
**Réévaluation:** Tous les 6 mois.
**Formule:** Storage = (débit_MB/s * retention_secondes * réplication) / 0.7

### 31. Mises à jour rolling
**Règle:** Jamais de mise à jour simultanée de tous les brokers.
**Process:** Un broker à la fois, attendre la réplication.
**Rollback:** Préparer la procédure avant chaque upgrade.

### 32. Backup des métadonnées
**Règle:** Backup quotidien de `zookeeper` ou `KRaft` metadata.
**Commande:** `kafka-dump-log --files metadata.log`
**Rétention:** 7 jours de backups.

### 33. Tests de résilience
**Règle:** Chaos testing mensuel (tuer brokers, réseau, disque).
**Outils:** Chaos Mesh, Gremlin, ou Netflix Chaos Monkey.
**Scénarios:** 
- Perte d'un broker
- Partition réseau
- Disque plein

### 34. Gestion des versions
**Règle:** Rester à jour avec les versions LTS de Kafka.
**Stratégie:** N-1 maximum (ex: production en 3.4 si 3.5 sorti).
**Testing:** Valider sur staging pendant 2 semaines.

### 35. Documentation des topics
**Règle:** Chaque topic doit avoir une documentation métier et technique.
**Contenu:** 
- Propriétaire
- Schéma (Avro/Protobuf)
- SLO (latence, débit)
- Consumer groups autorisés

### 36. Nettoyage des données orphelines
**Règle:** Supprimer les topics et consumer groups inutilisés.
**Fréquence:** Revue mensuelle.
**Commande:** `kafka-consumer-groups --delete` après vérification.

---

## 🚨 INCIDENTS & RECOVERY

### 37. Runbook des incidents
**Règle:** Procédure écrite pour les incidents courants.
**Inclus:**
- Perte de leader
- Partition sous-répliquée
- Lag explosion
- Corruption de log

### 38. Sauvegarde des segments
**Règle:** Backup quotidien des segments log critiques.
**Outils:** `kafka-replica-verification` + scripts custom.
**Test:** Restauration simulée mensuelle.

### 39. Quorum de brokers
**Règle:** Maintenir toujours un nombre impair de brokers (3,5,7).
**Pourquoi:** Éviter le split-brain.
**Règle:** Ne jamais descendre en dessous de 3 brokers en production.

### 40. DRP (Disaster Recovery Plan)
**Règle:** Plan de reprise d'activité testé tous les 6 mois.
**Objectifs:**
- RTO (Recovery Time Objective) < 4h
- RPO (Recovery Point Objective) < 15min
**Outils:** MirrorMaker 2.0 ou Confluent Replicator

---

## 📌 CHECKLIST DE DÉMARAGE PRODUCTION

Avant de passer en production, vérifiez:

- [ ] RF >= 3 pour les topics critiques
- [ ] min.insync.replicas = 2
- [ ] SASL_SSL activé
- [ ] Monitoring Prometheus + Grafana déployé
- [ ] Alertes configurées sur PagerDuty/Slack
- [ ] Backup des métadonnées automatisé
- [ ] Tests de charge validés
- [ ] Runbook des incidents documenté
- [ ] Équipe formée aux opérations courantes
- [ ] Plan de capacité validé pour 6 mois

---

## 🎯 REX & ASTUCES DE PRODUCTION

> "La configuration par défaut n'est jamais suffisante pour la production" - SRE Kafka

### Cas pratiques résolus:

1. **Problème:** Lag qui explose sur un topic
   - **Cause:** Producteur avec clés = null et partition unique
   - **Solution:** Clés de partitionnement + augmentation partitions

2. **Problème:** Performances dégradées le vendredi
   - **Cause:** Batch jobs qui floodent le cluster
   - **Solution:** Quotas par client-id + throttling

3. **Problème:** Messages corrompus
   - **Cause:** Producteur non-idempotent avec retries
   - **Solution:** `enable.idempotence=true`

### Outils indispensables:
- `kafka-consumer-groups` - Monitoring lags
- `kafka-replica-verification` - Vérification réplication
- `kafka-dump-log` - Debug segments
- `kafka-configs --alter` - Modifications dynamiques

---

## 📚 RÉFÉRENCES

- [Confluent Production Ready Checklist](https://docs.confluent.io/platform/current/installation/production-checklist.html)
- [LinkedIn Kafka Operations Best Practices](https://engineering.linkedin.com/kafka)
- [Uber Kafka Performance Tuning](https://eng.uber.com/kafka/)

---

*Document généré par Kafka 360° Audit Tool - Mise à jour: ${date}*  
*Règles validées sur plus de 100 clusters en production*
