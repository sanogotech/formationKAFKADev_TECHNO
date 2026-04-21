# Explication détaillée des 15 questions de configuration Kafka

Voici une analyse approfondie de chaque question, son impact sur le cluster Kafka, et comment interpréter les réponses.

---

## 1. **Nombre de brokers dans le cluster**

**Pourquoi cette question ?**  
Détermine la capacité de scaling, la tolérance aux pannes et la performance globale.

**Impact technique :**
- **3 brokers minimum** : Configuration minimale pour la haute disponibilité (avec réplication factor=3)
- **5-7 brokers** : Standard pour production avec bonne résilience
- **10+ brokers** : Grand volume de données, besoin de throughput élevé

**Règles d'or :**
- `facteur_réplication ≤ nombre_brokers`
- Pour chaque partition, un broker peut être leader
- Plus de brokers = meilleure distribution de charge mais plus de coordination

**Exemple concret :**  
Si vous avez 100 topics × 6 partitions = 600 partitions. Avec 3 brokers → 200 partitions/broker (acceptable). Avec 10 brokers → 60 partitions/broker (meilleure performance).

---

## 2. **Nombre de partitions par topic (défaut)**

**Pourquoi cette question ?**  
Les partitions sont l'unité fondamentale de parallélisme dans Kafka.

**Impact technique :**
- **Plus de partitions = plus de parallélisme** (plus de consumers peuvent lire en parallèle)
- **Plus de partitions = plus de surcharge** (chaque partition a des métadonnées, des fichiers, des handles)
- **Limite pratique** : 2000-4000 partitions par broker maximum

**Calcul de référence :**
```
Throughput_max_par_partition ≈ 10-20 MB/s (selon hardware)
Partitions_nécessaires = Débit_total / Throughput_par_partition

Exemple : 100 MB/s débit → 5-10 partitions minimum
```

**Cas d'usage :**
- **Faible débit** (< 10 MB/s) : 3-6 partitions
- **Moyen débit** (10-50 MB/s) : 6-12 partitions  
- **Fort débit** (> 50 MB/s) : 12-24 partitions

---

## 3. **Nombre de consumers dans le groupe principal**

**Pourquoi cette question ?**  
Détermine la vitesse de consommation et l'équilibrage de charge.

**Principe de fonctionnement :**
- Chaque partition est consommée par UN SEUL consumer dans un groupe
- Si plus de consumers que partitions, certains restent inactifs
- Idéal : `nombre_consumers = nombre_partitions`

**Optimisation :**
```python
# Calcul du throughput de consommation
throughput_consumer = débit_total / nombre_consumers
# Chaque consumer doit pouvoir traiter cette quantité
```

**Exemple :**  
Avec 12 partitions et 6 consumers → chaque consumer traite 2 partitions → équilibre parfait  
Avec 12 partitions et 15 consumers → 3 consumers inactifs (gaspillage de ressources)

---

## 4. **Durée de rétention des messages (heures)**

**Pourquoi cette question ?**  
Détermine l'espace disque nécessaire et la conformité légale.

**Impact direct :**
- **Stockage requis = débit (Go/h) × rétention (heures) × facteur_réplication**
- Rétention courte (24h) : Moins de stockage, rejeu limité
- Rétention longue (168h/7j) : Plus de stockage, rejeu possible sur semaine
- Très longue (720h/30j) : Stockage massif, cas d'audit/compliance

**Calcul pratique :**
```
Exemple : 10 MB/s débit = 36 GB/h
Rétention 168h (7j) = 6 TB × réplication(3) = 18 TB de stockage
```

**Recommandations par cas d'usage :**
- **Real-time processing** : 24-72 heures
- **Analytics/Batch** : 168-720 heures (7-30 jours)  
- **Audit/Compliance** : 2160+ heures (90+ jours)
- **IoT/Telemetry** : 24-168 heures selon volatilité

---

## 5. **Facteur de réplication**

**Pourquoi cette question ?**  
Garantit la durabilité des données et la tolérance aux pannes.

**Mathématique de la tolérance :**
```
Réplication = 1 → Aucune tolérance (un broker down = perte données)
Réplication = 2 → Tolère 1 broker down, mais risque de perte
Réplication = 3 → Tolère 2 brokers down (recommandé)
Réplication = 5 → Tolère 4 brokers down (très haute disponibilité)
```

**Compromis :**
- **Avantages** : Durabilité, disponibilité, lecture parallèle possible
- **Inconvénients** : Coût de stockage × réplication, traffic réseau pour réplication

**Configuration ISR (In-Sync Replicas) :**
```properties
min.insync.replicas = 2  # Avec RF=3, requiert 2 réplicas in-sync
# Garantit qu'au moins 2 brokers ont le message avant d'accuser réception
```

---

## 6. **CPU par broker (cœurs)**

**Pourquoi cette question ?**  
Détermine la capacité de traitement des opérations.

**Utilisation typique du CPU :**
- **Compression/Décompression** : Peut utiliser 20-40% CPU
- **Sérialisation/Désérialisation** : 10-20% CPU
- **Replication** : 5-15% CPU
- **Network I/O** : 5-10% CPU
- **GC Java** : Variable (5-15%)

**Règles de sizing :**
```
Minimum production : 8 cœurs
Recommandé : 16-32 cœurs
Haute performance : 32+ cœurs

Formule empirique :
cœurs = (débit_MB/s / 10) + 4
```

**Configurations par cas :**
- **Light workload** (< 50 MB/s) : 8 cœurs
- **Medium workload** (50-200 MB/s) : 16 cœurs  
- **Heavy workload** (200-500 MB/s) : 32 cœurs
- **Très lourd** (> 500 MB/s) : 64+ cœurs

---

## 7. **RAM par broker (Go)**

**Pourquoi cette question ?**  
La RAM est critique pour le page cache du système d'exploitation.

**Allocation mémoire typique :**
```
RAM totale = OS(4GB) + Heap JVM(6-12GB) + Page Cache(reste)

Exemple 32GB RAM :
- OS: 4GB
- Heap JVM: 10GB (Xmx)
- Page Cache: 18GB (utilisé pour les messages récents)
```

**Performance du page cache :**
- **Cache chaud** : Lectures à vitesse mémoire (nanosecondes)
- **Cache froid** : Lectures disque (millisecondes → 1000x plus lent)

**Calcul de besoin :**
```
RAM_requise = (débit_MB/s × temps_lecture_cache_secondes) + heap_JVM

Avec débit 100 MB/s et 60 secondes de cache : 
6GB (cache) + 10GB (heap) = 16GB RAM
```

---

## 8. **Taille moyenne des messages (Ko)**

**Pourquoi cette question ?**  
Influence le batching, la compression, et les buffers réseau.

**Impact sur les performances :**

| Taille message | Batching | Compression | Throughput |
|---------------|----------|-------------|------------|
| < 1KB | Excellent | Très efficace | Limitée par overhead |
| 1-10KB | Optimal | Efficace | Excellent |
| 10-100KB | Bon | Moyenne | Bon |
| 100KB-1MB | Réduit | Faible | Acceptable |
| > 1MB | Pauvre | Inefficace | Nécessite tuning |

**Optimisations spécifiques :**
```java
// Pour petits messages (< 1KB)
batch.size = 16384 (16KB)
linger.ms = 10

// Pour gros messages (> 100KB)
batch.size = 65536 (64KB)  
max.request.size = 10485760 (10MB)
```

---

## 9. **Débit attendu (messages/seconde)**

**Pourquoi cette question ?**  
Détermine la dimensionnement réseau, disque et CPU.

**Calcul du débit réel :**
```
Débit réel (MB/s) = (messages/s × taille_message_Ko) / 1024

Exemple : 100,000 msg/s × 10KB = 976 MB/s (très élevé !)
```

**Seuils critiques :**
- **< 10 MB/s** : Petit débit, configuration standard
- **10-100 MB/s** : Débit moyen, nécessite optimisation réseau
- **100-500 MB/s** : Haut débit, nécessite réseau 10GbE
- **> 500 MB/s** : Très haut débit, nécessite réseau 25/40GbE

**Conseils pratiques :**
```
1 réseau 1GbE → max 125 MB/s théorique (80 MB/s pratique)
1 réseau 10GbE → max 1250 MB/s théorique (800 MB/s pratique)
```

---

## 10. **Nombre de topics prévus**

**Pourquoi cette question ?**  
Chaque topic ajoute des métadonnées et une surcharge de gestion.

**Surcharge par topic :**
- Métadonnées dans ZooKeeper : ~1KB/topic
- Métadonnées dans chaque broker : ~500 bytes/partition
- Handles de fichiers : ~3 handles/partition

**Limites pratiques :**
```
Broker seul : 5,000-10,000 topics (avec peu de partitions)
Cluster 3 brokers : 15,000-30,000 topics
Attention : Plus de topics = plus de timeouts ZK
```

**Design recommandé :**
```
Préférer moins de topics avec plus de partitions
Plutôt que 1000 topics × 1 partition
→ Privilégier 100 topics × 10 partitions

Cas d'exception : Multitenancy sévère → topics multiples
```

---

## 11. **Latence maximale acceptable (ms)**

**Pourquoi cette question ?**  
Détermine les configurations de batching et d'acknowledgment.

**Configurations selon latence :**

| Latence | acks | linger.ms | batch.size | Use case |
|---------|------|-----------|------------|----------|
| < 5ms | 1 | 0 | 16384 | Trading, Gaming |
| 5-20ms | 1 | 5 | 32768 | Real-time API |
| 20-100ms | all | 10 | 65536 | Standard web |
| > 100ms | all | 50 | 131072 | Analytics, Batch |

**Compromis :**
- **Faible latence** = Moins de batching = Plus de requêtes = Plus de CPU
- **Haute latence** = Plus de batching = Plus de throughput = Bufferisation

**Optimisation :**
```properties
# Faible latence
linger.ms=0
batch.size=16384
compression.type=none

# Haute latence acceptable
linger.ms=100  
batch.size=131072
compression.type=snappy
```

---

## 12. **Budget mensuel (€)**

**Pourquoi cette question ?**  
Permet d'arbitrer entre performance et coût.

**Coûts typiques (estimation 2025) :**

| Composant | Coût mensuel (€) |
|-----------|-----------------|
| Broker (4 vCPU, 16GB) | 150-300 |
| Broker (8 vCPU, 32GB) | 300-600 |
| Stockage SSD (1TB) | 50-100 |
| Network (1TB transfert) | 50-100 |
| Support/Management | 200-1000 |

**Arbitrages budgétaires :**
```python
if budget < 1000€:
    # Solution minimale viable
    - 3 brokers (t2.large)
    - SSD standard
    - Pas de réplication cross-AZ
    
elif budget < 5000€:
    # Solution standard
    - 5 brokers (m5.xlarge)  
    - Stockage provisionné IOPS
    - Réplication sur 3 AZ
    
else:
    # Solution haute performance
    - 7+ brokers (c5.2xlarge)
    - Stockage NVMe
    - Réplication 3 AZ + DR
```

---

## 13. **Niveau de criticité (1-5)**

**Pourquoi cette question ?**  
Détermine les configurations de durabilité et disponibilité.

**Niveaux détaillés :**

| Niveau | Cas d'usage | acks | RF | min.isr | TLS |
|--------|-------------|------|----|---------|-----|
| 1 | Dev/Test | 1 | 1 | 1 | Non |
| 2 | Interne non critique | 1 | 2 | 1 | Optionnel |
| 3 | Production standard | all | 3 | 2 | Oui |
| 4 | Critique métier | all | 3 | 2 | Oui |
| 5 | Mission critique | all | 5 | 3 | Oui + KMS |

**Configurations supplémentaires par niveau :**
- **Niveau 4+** : Monitoring alerte 5min, backup quotidien
- **Niveau 5** : DR site secondaire, RPO < 1min, RTO < 15min

---

## 14. **Type de charge (lecture/écriture/mixte)**

**Pourquoi cette question ?**  
Optimise le ratio entre producteurs et consommateurs.

**Optimisations selon type :**

**Charge écriture dominante (80%+ write) :**
```properties
# Optimiser pour les producteurs
num.network.threads = 4
num.io.threads = 8
socket.send.buffer.bytes = 1048576
compression.type = snappy
```

**Charge lecture dominante (80%+ read) :**
```properties
# Optimiser pour les consommateurs  
num.network.threads = 8
num.io.threads = 4
socket.receive.buffer.bytes = 1048576
compression.type = none  # Décompresser à la source
```

**Mixte (50/50) :**
```properties
# Équilibre
num.network.threads = 6
num.io.threads = 6  
socket.send.buffer.bytes = 524288
socket.receive.buffer.bytes = 524288
```

---

## 15. **Stratégie de compression**

**Pourquoi cette question ?**  
Équilibre entre CPU, réseau et espace disque.

**Comparaison des algorithmes :**

| Algo | Ratio | CPU | Vitesse | Use case |
|------|-------|-----|---------|----------|
| None | 1:1 | N/A | Max | Réseau rapide, CPU limité |
| Snappy | 3-4:1 | Faible | Rapide | Standard production |
| LZ4 | 3-4:1 | Très faible | Très rapide | Haute performance |
| Zstd | 5-8:1 | Moyen | Moyenne | Stockage long terme |
| GZIP | 5-6:1 | Élevé | Lent | Legacy, compatibilité |

**Recommandations par cas :**

```python
if taille_messages < 1KB:
    compression = "snappy"  # Bon ratio pour petits messages
    
elif taille_messages < 100KB:
    compression = "lz4"  # Optimal pour messages moyens
    
elif taille_messages > 100KB:
    compression = "zstd"  # Meilleur ratio pour gros messages
    
if débit_messages > 500000:
    compression = "lz4"  # Vitesse primordiale
    
if budget_stockage < 1000€:
    compression = "zstd"  # Économie de stockage
```

---

## 📊 **Tableau récapitulatif des interdépendances**

```
Questions qui influencent les autres :

1. Brokers ← RF, CPU, RAM
2. Partitions ← Débit, Consumers, Brokers  
3. Rétention ← Stockage, Budget
4. Réplication ← Brokers, Criticité
5. CPU/RAM ← Débit, Compression
6. Taille message ← Compression, Buffers
7. Débit ← CPU, RAM, Partitions, Réseau
8. Topics ← Brokers, Partitions
9. Criticité ← RF, min.isr, Sécurité
10. Type charge ← Network/IO threads
```

Cette analyse vous permet de faire des choix éclairés pour chaque paramètre en fonction de votre cas d'usage spécifique !
