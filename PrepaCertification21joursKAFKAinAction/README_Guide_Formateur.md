# 🚀 Formation Kafka — De Zéro à Héros (21 Jours)
## Guide du Formateur — Comment utiliser et animer ces supports

---

## 📋 Table des matières

1. [Vue d'ensemble de la formation](#1-vue-densemble)
2. [Structure de chaque document](#2-structure-de-chaque-document)
3. [Comment préparer une session](#3-comment-préparer-une-session)
4. [Comment animer chaque section](#4-comment-animer-chaque-section)
5. [Gestion des labs pratiques](#5-gestion-des-labs-pratiques)
6. [Gestion des profils d'apprenants](#6-gestion-des-profils-dapprenants)
7. [Planning détaillé par semaine](#7-planning-détaillé-par-semaine)
8. [Checklist technique avant chaque jour](#8-checklist-technique-avant-chaque-jour)
9. [Conseils pédagogiques avancés](#9-conseils-pédagogiques-avancés)
10. [FAQ Formateur](#10-faq-formateur)
11. [Ressources complémentaires](#11-ressources-complémentaires)

---

## 1. Vue d'ensemble

### 📦 Ce que contient ce dossier

```
kafka-formation/
├── Kafka_Jour0_Introduction.docx          # Jour 0  : État de l'art, architecture, top 20 usages
├── Kafka_Jour1_Setup.docx                 # Jour 1  : Installation Docker, CLI, Kafka UI
├── Kafka_Jour2_Architecture.docx          # Jour 2  : Partitionnement, réplication, failover
├── Kafka_Jour3_Producer.docx              # Jour 3  : Producer Java/Spring, tuning, benchmark
├── Kafka_Jour4_Consumer.docx              # Jour 4  : Consumer Groups, offsets, résilience
├── Kafka_Jour5_SchemaRegistry.docx        # Jour 5  : Avro, Schema Registry, compatibilité
├── Kafka_Jour6_KafkaStreams.docx           # Jour 6  : Kafka Streams, filter/map/aggregate/join
├── Kafka_Jour7_ksqlDB.docx                # Jour 7  : ksqlDB, SQL temps réel, détection fraude
├── Kafka_Jour8_KafkaConnect.docx          # Jour 8  : Kafka Connect, JDBC, Elasticsearch
├── Kafka_Jour9_Debezium.docx              # Jour 9  : CDC Debezium, binlog, Pattern Outbox
├── Kafka_Jour10_ConnectAvance.docx        # Jour 10 : SMT, DLQ, pipeline complet
├── Kafka_Jour11_EDA.docx                  # Jour 11 : EDA, CQRS, Event Sourcing, Saga
├── Kafka_Jour12_Performance.docx          # Jour 12 : Performance, tuning, benchmark
├── Kafka_Jour13_Securite.docx             # Jour 13 : SSL/TLS, SASL, ACL
├── Kafka_Jour14_Administration.docx       # Jour 14 : Rétention, compaction, administration
├── Kafka_Jour15_Monitoring.docx           # Jour 15 : Prometheus, Grafana, alertes
├── Kafka_Jour16_Troubleshooting.docx      # Jour 16 : Diagnostic et résolution en production
├── Kafka_Jour17-18_MiniProjet2.docx       # Jours 17-18 : Mini Projet SI Entreprise
├── Kafka_Jour19-20_ProjetFinal.docx       # Jours 19-20 : Projet Final Expert niveau DSI
└── Kafka_Jour21_SoutenanceCertification.docx  # Jour 21 : Soutenance et certification
```

### 🎯 Philosophie pédagogique

| Principe | Description |
|----------|-------------|
| **80% Pratique** | Chaque journée est dominée par des labs hands-on avec du vrai code |
| **Progression spirale** | Chaque concept est introduit simplement, puis approfondi les jours suivants |
| **Contextualisation** | Tous les exemples utilisent des cas réels : paiements mobiles, IoT énergie, CRM |
| **Validation continue** | Quiz après chaque journée, évaluation avant/après pour mesurer la progression |
| **Apprentissage actif** | Les apprenants font avant de comprendre, pas l'inverse |

### 👥 Public cible

- Développeurs Java / Python souhaitant intégrer Kafka
- Architectes data et solutions
- DevOps / Platform Engineers
- Data Engineers
- DSI souhaitant comprendre les enjeux techniques

### ⏱ Durée et format

- **Format recommandé** : 1 journée par document (8h avec pauses)
- **Ratio théorie/pratique** : 20% / 80%
- **Taille de groupe idéale** : 6 à 12 apprenants
- **Maximum absolu** : 15 apprenants (au-delà, la gestion des labs devient difficile)

---

## 2. Structure de chaque document

Chaque document suit **exactement la même structure** — les apprenants s'y habituent rapidement et savent où trouver ce dont ils ont besoin.

```
┌─────────────────────────────────────────────┐
│  1. PAGE DE COUVERTURE                      │
│     Titre, jour, ratio théorie/pratique     │
├─────────────────────────────────────────────┤
│  2. OBJECTIFS DU JOUR                       │
│     Ce que tu vas maîtriser + Livrables     │
├─────────────────────────────────────────────┤
│  3. ÉVALUATION AVANT (Tip Box jaune)        │
│     Question ouverte — noter SA réponse     │
├─────────────────────────────────────────────┤
│  4. THÉORIE (20 min max)                    │
│     Tableaux, schémas, concepts clés        │
├─────────────────────────────────────────────┤
│  5. LABS PRATIQUES (3 labs de 30-45 min)    │
│     Code complet, commandes, étapes         │
├─────────────────────────────────────────────┤
│  6. AVANT / APRÈS                           │
│     Ce qui a changé en une journée          │
├─────────────────────────────────────────────┤
│  7. MINI QUIZ (10 questions)                │
│     Validation des acquis, corrigé inclus   │
├─────────────────────────────────────────────┤
│  8. L'ESSENTIEL À RETENIR                   │
│     8 points clés encadrés en bleu          │
└─────────────────────────────────────────────┘
```

### 🎨 Code couleur des encadrés

| Couleur | Type d'encadré | Signification |
|---------|---------------|---------------|
| 🔵 Bleu | `infoBox` | Information importante, définition |
| 🟡 Jaune | `tipBox` | Conseil, bonne pratique, astuce |
| 🟠 Orange | `warnBox` | Attention, erreur fréquente, anti-pattern |
| 🟢 Vert | `successBox` | Résultat attendu, validation d'une étape |
| ⬛ Fond sombre | `codeBox` | Code à exécuter (commandes, Java, SQL) |

---

## 3. Comment préparer une session

### La veille (J-1)

**Environnement technique :**
```bash
# 1. Vérifier que Docker fonctionne sur votre machine de démo
docker --version           # >= 24.x
docker compose version     # >= v2.x

# 2. Puller les images à l'avance (éviter les attentes en séance)
docker pull confluentinc/cp-kafka:7.6.0
docker pull confluentinc/cp-schema-registry:7.6.0
docker pull provectuslabs/kafka-ui:latest
docker pull confluentinc/cp-kafka-connect:7.6.0
docker pull mysql:8.0
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.12.0
docker pull prom/prometheus:latest
docker pull grafana/grafana:latest

# 3. Lancer le cluster et vérifier qu'il répond
docker compose up -d
curl -s localhost:9092      # Kafka
curl -s localhost:8080      # Kafka UI
curl -s localhost:8081      # Schema Registry
```

**Pédagogique :**
- Relire le document du jour entier (même si tu le connais)
- Faire les labs toi-même pour vérifier que tout fonctionne
- Préparer 2-3 analogies du quotidien pour les concepts abstraits
- Identifier les apprenants qui pourraient être en difficulté

### Le matin (J)

- Arriver 30 minutes avant les apprenants
- Lancer Docker et vérifier les services
- Ouvrir le document du jour sur le vidéoprojecteur
- Afficher Kafka UI sur un onglet browser séparé
- Préparer un terminal propre (grande police, fond sombre)

---

## 4. Comment animer chaque section

### 4.1 L'évaluation avant (5 min)

> **Rôle** : Activer les connaissances préalables et créer un "contrat pédagogique" avec les apprenants.

**Comment faire :**
1. Lire la question à voix haute (encadré jaune en haut du document)
2. Demander aux apprenants d'écrire leur réponse sur papier — **pas de discussion encore**
3. Demander 2-3 réponses à voix haute sans corriger
4. Dire : *"On reviendra à vos réponses en fin de journée"*

**Pourquoi c'est important :** Les apprenants qui formulent une hypothèse avant le cours retiennent 40% de plus que ceux qui n'ont pas d'hypothèse préalable (effet de génération, Slamecka & Graf, 1978).

---

### 4.2 La théorie (20 min max — règle absolue)

> **Règle d'or : 20 minutes maximum. Après, les apprenants décrochent.**

**Structure recommandée :**
```
[2 min]  Accroche : une situation concrète qui pose le problème
[5 min]  Concept principal : expliquer avec le tableau du document
[5 min]  Analogie du quotidien : rendre le concept tangible
[5 min]  Démo visuelle : montrer dans Kafka UI ou schéma
[3 min]  Questions / vérification de compréhension
```

**Analogies qui marchent bien :**

| Concept Kafka | Analogie efficace |
|---------------|-------------------|
| Topic | Chaîne TV (TF1, France 2...) — chacun diffuse un type de contenu |
| Partition | Caisse de supermarché — plusieurs caisses = traitement parallèle |
| Offset | Marque-page dans un livre — reprendre exactement où on s'est arrêté |
| Consumer Group | Équipe de facteurs se partageant les rues d'un quartier |
| Réplication | Photocopies d'un document dans plusieurs classeurs |
| Debezium | Caméra de surveillance qui filme chaque changement en temps réel |
| Schema Registry | Contrat signé entre les équipes sur la structure des données |
| Kafka Streams | Chaîne d'assemblage d'usine — chaque poste transforme le produit |

---

### 4.3 Les labs pratiques (l'essentiel — 80% du temps)

> **Principe clé : les apprenants tapent eux-mêmes. Ne pas copier-coller à leur place.**

**Le rythme idéal pour un lab :**

```
[2 min]   Expliquer l'objectif du lab (lire l'infoBox bleue)
[1 min]   Montrer le résultat final attendu (la successBox verte)
[X min]   Les apprenants réalisent le lab en autonomie ou en binôme
[5 min]   Débrief collectif : "Qu'avez-vous observé ?"
[2 min]   Pointer les pièges fréquents (warnBox orange)
```

**Gestion des labs en groupe :**

- **Binômes recommandés** : associer un profil avancé avec un profil débutant
- **Écrans partagés** : projeter votre terminal pour guider sans bloquer l'autonomie
- **Signal d'aide** : demander aux apprenants de lever la main ou poser un post-it rouge
- **Timing souple** : si 80% ont fini, passer. Les 20% restants terminent pendant le débrief

**Si un lab ne fonctionne pas :**
```bash
# Solution de secours universelle — réinitialiser l'environnement
docker compose down -v
docker compose up -d
# Attendre 30 secondes puis reprendre
```

---

### 4.4 Le mini quiz (10 min)

> **Objectif** : Ancrage mémoriel, pas sanction. Créer une atmosphère détendue.

**Comment faire :**
1. Dire : *"Fermez le document, stylo en main. C'est pour vous, pas pour moi."*
2. Laisser 8 minutes pour répondre individuellement
3. Lecture collective des réponses — **les apprenants s'auto-corrigent**
4. Pour chaque question, demander : *"Qui a répondu B ? Pourquoi ?"*
5. Score : noter mentalement qui est en difficulté sur quels concepts

**Score cible :**
- 8/10 ou plus → journée maîtrisée ✅
- 6-7/10 → réviser les points faibles le lendemain matin (10 min de rappel)
- Moins de 6/10 → prévoir du soutien individuel ou revoir le concept en journée suivante

---

### 4.5 L'essentiel à retenir (5 min)

> **Le moment de clôture** — toujours terminer par là.

**Rituel recommandé :**
1. Lire les 8 points à voix haute, lentement
2. Pour chaque point, demander : *"Quelqu'un peut me donner un exemple concret ?"*
3. Revenir à l'évaluation du matin : *"Aviez-vous bien anticipé ?"*
4. Demander : *"Quel est le point qui vous a le plus surpris aujourd'hui ?"*

---

## 5. Gestion des labs pratiques

### Configuration technique recommandée

**Option A — Chaque apprenant sur sa machine (idéal)**
```
Prérequis machine apprenant :
- RAM : 8 GB minimum (16 GB recommandé)
- Docker Desktop installé et configuré avec 6 GB RAM alloués
- Java 17+ installé
- Maven 3.8+ installé
- IDE : IntelliJ IDEA Community ou VS Code avec Java Extension Pack
- Git installé
```

**Option B — Serveur partagé avec accès par apprenant**
```bash
# Sur le serveur : créer un namespace par apprenant
for i in {1..12}; do
  docker network create kafka-apprenant-$i
  # Chaque apprenant a son propre cluster sur des ports distincts
  # Apprenant 1 : ports 9092, 8080, 8081
  # Apprenant 2 : ports 9192, 8180, 8181
  # etc.
done
```

**Option C — Environnement cloud (Gitpod / GitHub Codespaces)**
```yaml
# .gitpod.yml — lancer automatiquement le cluster Kafka
tasks:
  - name: Kafka Cluster
    init: docker compose pull
    command: docker compose up -d && echo "Cluster Kafka prêt !"
ports:
  - port: 9092
  - port: 8080
  - port: 8081
```

### Gestion du temps dans les labs

| Lab | Durée prévue | Signal d'alerte | Action |
|-----|-------------|-----------------|--------|
| Lab 1 | 45 min | À 40 min | Faire un point collectif, montrer la solution |
| Lab 2 | 45 min | À 40 min | Idem |
| Lab 3 | 30 min | À 25 min | Démo formateur si nécessaire |

### Quand un apprenant est bloqué

```
Étape 1 : Demander "Quel message d'erreur exact tu vois ?"
Étape 2 : Demander "Qu'est-ce que tu as essayé pour débloquer ?"
Étape 3 : Guider par questions (Socratique), pas donner la réponse directement
Étape 4 : Si bloqué > 5 min sur la même erreur → donner la solution et expliquer
Étape 5 : Toujours faire reformuler la solution par l'apprenant
```

---

## 6. Gestion des profils d'apprenants

### Les profils fréquents

**🚀 Le développeur Java confirmé**
- Confort : Labs 3 et 4 (Producer/Consumer avancé)
- Défi : Lui proposer des extensions (idempotence, transactions)
- Rôle en groupe : Pair pour les débutants

**🐢 Le débutant en développement**
- Confort : Commandes CLI, Kafka UI
- Défi : Partie Java/Spring — prévoir du code pré-écrit
- Rôle en groupe : Bien avec un pair avancé, focus sur la compréhension conceptuelle

**🏗️ L'architecte / DSI**
- Confort : Jours 11-15 (EDA, performance, sécurité, architecture)
- Défi : Les labs de code — lui proposer de valider plutôt que de coder
- Rôle en groupe : Animer les discussions sur les choix d'architecture

**🔧 Le DevOps / SRE**
- Confort : Jours 13-16 (sécurité, admin, monitoring, troubleshooting)
- Défi : La partie streaming/CQRS
- Rôle en groupe : Gérer l'infra Docker pour l'équipe

### Adapter le rythme

```
Si le groupe va TROP VITE :
→ Proposer les "extensions" en fin de lab (mention dans les labs)
→ Aller plus loin dans le tuning / l'optimisation
→ Demander de documenter l'architecture de ce qu'ils viennent de faire

Si le groupe va TROP LENTEMENT :
→ Faire les labs en démo collective (formateur fait, apprenants observent et posent des questions)
→ Sauter les labs 3 et se concentrer sur labs 1 et 2
→ Utiliser le code pré-écrit comme point de départ au lieu de zéro
```

---

## 7. Planning détaillé par semaine

### Semaine 1 — Fondamentaux (Jours 0-5)

```
Jour 0  : Introduction générale (peut se faire en demi-journée si public technique)
Jour 1  : Installation — S'assurer que TOUS les clusters sont opérationnels avant de passer
Jour 2  : Architecture — Le lab failover est le moment "wow" de la semaine
Jour 3  : Producer — Nécessite Java. Prévoir du code pré-écrit pour les non-Java
Jour 4  : Consumer — Lab de crash et reprise : très concret et mémorable
Jour 5  : Schema Registry — Terminer par la démonstration d'incompatibilité (moment fort)
```

**Points d'attention Semaine 1 :**
- Jour 1 : Consacrer 30 min supplémentaires si des machines ont des problèmes Docker
- Jour 3 : Prévoir un `pom.xml` et le code Java de base pré-écrit sur une clé USB ou GitHub
- Avant Jour 6 : Vérifier que tous les apprenants ont un cluster fonctionnel

---

### Semaine 2 — Intégration & Streaming (Jours 6-10)

```
Jour 6  : Kafka Streams — Le join Stream+Table est le lab le plus difficile
Jour 7  : ksqlDB — Journée "fun", les non-développeurs adorent le SQL
Jour 8  : Connect — Le pipeline MySQL->Kafka->ES en 1h est très gratifiant
Jour 9  : Debezium — Voir un DELETE capturé en temps réel : moment "magie"
Jour 10 : Connect Avancé — DLQ + SMT : journée de consolidation
```

**Points d'attention Semaine 2 :**
- Jour 6 : Kafka Streams nécessite de bonnes bases Java (Jour 3). Vérifier le niveau du groupe
- Jour 7 : Toujours faire `SET 'auto.offset.reset' = 'earliest';` avant les labs ksqlDB
- Jour 8 : Le téléchargement des plugins Connect peut prendre 5-10 min — lancer à l'avance
- Jour 9 : Vérifier que MySQL est configuré avec `--binlog-format=ROW` (dans le docker-compose)

---

### Semaine 3 — Architecture & Production (Jours 11-16)

```
Jour 11 : EDA/CQRS — Journée conceptuelle, prévoir plus de discussion
Jour 12 : Performance — Les résultats du benchmark sont toujours surprenants
Jour 13 : Sécurité — Lab long (certificats), commencer par la théorie très vite
Jour 14 : Administration — Rolling upgrade : simuler avec 3 containers Docker
Jour 15 : Monitoring — Grafana est très visuel, les apprenants adorent
Jour 16 : Troubleshooting — Simulation de pannes : journée très interactive
```

**Points d'attention Semaine 3 :**
- Jour 11 : Prévoir des post-its pour le design d'architecture CQRS en groupe
- Jour 13 : Les commandes `keytool` peuvent échouer selon le JDK. Prévoir une CA pré-générée
- Jour 15 : Lancer Prometheus + Grafana la veille pour éviter les délais de démarrage

---

### Semaine finale — Projets (Jours 17-21)

```
Jours 17-18 : Mini Projet #2 — 2 jours consécutifs, travailler en équipes de 3
Jours 19-20 : Projet Final — Individuel ou binôme, formateur disponible en coaching
Jour 21     : Soutenance — Préparer l'espace de présentation la veille
```

**Organisation de la soutenance (Jour 21) :**
```
08h00 - 08h30 : Préparation technique des apprenants
08h30 - 09h00 : Quiz de certification (30 min, 20 questions)
09h00 - 11h30 : Soutenances individuelles (2h30 par apprenant en rotation)
11h30 - 12h00 : Délibération
12h00 - 12h30 : Remise des certifications + Retrospective collective
```

---

## 8. Checklist technique avant chaque jour

### ✅ Checklist universelle (tous les jours)

```bash
# 1. Vérifier que Docker tourne
docker ps

# 2. Vérifier que Kafka répond
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# 3. Vérifier Kafka UI
curl -s http://localhost:8080 > /dev/null && echo "Kafka UI OK"

# 4. Vérifier Schema Registry
curl -s http://localhost:8081/subjects && echo "Schema Registry OK"
```

### ✅ Checklists spécifiques par jour

**Jours 8-10 (Kafka Connect) :**
```bash
# Vérifier que Connect est prêt avec les plugins installés
curl -s http://localhost:8083/connector-plugins | python3 -m json.tool | grep -i "jdbc\|elastic\|debezium"
# Si vide -> les plugins ne sont pas installés -> reconstruire l'image
```

**Jour 9 (Debezium) :**
```bash
# Vérifier binlog MySQL
docker exec -it mysql mysql -u root -prootpassword -e "SHOW VARIABLES LIKE 'log_bin';"
# Doit retourner: log_bin | ON
docker exec -it mysql mysql -u root -prootpassword -e "SHOW VARIABLES LIKE 'binlog_format';"
# Doit retourner: binlog_format | ROW
```

**Jours 15 (Monitoring) :**
```bash
# Vérifier que Prometheus scrape Kafka
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep '"health"'
# Doit retourner: "health": "up"
```

**Jours 19-20 (Projet Final) :**
```bash
# Vérifier MirrorMaker 2 (si multi-DC simulé)
curl -s http://localhost:8083/connectors | python3 -m json.tool

# Vérifier que tous les connecteurs sont RUNNING
curl -s http://localhost:8083/connectors?expand=status | python3 -c "
import sys, json
data = json.load(sys.stdin)
for name, info in data.items():
    state = info['status']['connector']['state']
    print(f'{name}: {state}')
"
```

---

## 9. Conseils pédagogiques avancés

### La règle des 3 expositions

Pour qu'un concept soit maîtrisé, un apprenant a besoin de le rencontrer **au moins 3 fois** de manière différente :

1. **Exposition 1** : Théorie avec tableau/analogie (20 min)
2. **Exposition 2** : Lab pratique (45 min)
3. **Exposition 3** : Quiz + révision le lendemain matin (10 min de rappel)

Les jours suivants, les concepts réapparaissent naturellement dans les labs, créant des expositions supplémentaires sans effort supplémentaire.

### La technique du "Pourquoi avant le Comment"

> ❌ **Ne pas faire** : "Voici comment créer un topic : `kafka-topics --create...`"
>
> ✅ **Faire** : "Imaginez que vous êtes Netflix et que vous devez diffuser des événements de lecture vers 50 services différents. Comment feriez-vous ? *(Pause, discussion)* Kafka résout exactement ça avec les topics. Voici comment en créer un..."

Les apprenants qui comprennent *pourquoi* avant *comment* retiennent 3x plus longtemps.

### La technique de l'erreur volontaire

Dans les labs, introduire **intentionnellement** une erreur courante, puis demander aux apprenants de la trouver. Exemples :

```bash
# Erreur intentionnelle 1 : oublier --from-beginning
kafka-console-consumer --bootstrap-server localhost:9092 --topic paiements
# → Les apprenants ne voient pas les anciens messages → "Pourquoi ?"

# Erreur intentionnelle 2 : mauvais port
kafka-topics --list --bootstrap-server localhost:9093
# → Erreur de connexion → "Quel port faut-il utiliser ?"

# Erreur intentionnelle 3 : schema incompatible
# → Le Schema Registry rejette → "Qu'est-ce qui se passe ?"
```

### Le débrief en 3 questions

Après chaque lab, toujours poser ces 3 questions :
1. **"Qu'avez-vous observé qui vous a surpris ?"** (ouvert)
2. **"Quel lien faites-vous avec ce qu'on a vu ce matin ?"** (consolidation)
3. **"Dans votre contexte professionnel, où utiliseriez-vous ça ?"** (transfert)

### Le pair programming adapté à Kafka

Pour les labs Java (Jours 3, 4, 6, 11) :
- **Conducteur** : tape le code
- **Navigateur** : lit le document, guide, repère les erreurs
- **Rotation toutes les 15 minutes** : changer de rôle

---

## 10. FAQ Formateur

### ❓ "Docker ne fonctionne pas sur ma machine"

```bash
# Sur Mac avec M1/M2/M3 : forcer la plateforme
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up -d

# Sur Windows : vérifier WSL2
wsl --status  # Doit être WSL 2

# Mémoire insuffisante : réduire les replicas
# Dans docker-compose.yml : KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

### ❓ "Je n'ai pas assez de temps pour tout faire"

**Version 10 jours (essentiel) :**
```
Jours 0-1  : Introduction + Setup
Jours 2-3  : Architecture + Producer
Jour 4-5   : Consumer + Schema Registry
Jours 6-7  : Kafka Streams + ksqlDB
Jours 8-9  : Connect + Debezium
Jour 10    : Projet Final simplifié (pipelines uniquement)
```

**Version 5 jours (initiation) :**
```
Jour 1 : Jours 0+1 (introduction + setup)
Jour 2 : Jours 3+4 (producer + consumer)
Jour 3 : Jours 7+8 (ksqlDB + Connect)
Jour 4 : Jour 11   (EDA/CQRS concepts)
Jour 5 : Mini projet simplifié
```

### ❓ "Le groupe est très hétérogène en niveau"

- Créer des binômes niveau avancé + débutant
- Préparer des "extensions" pour les avancés (toujours possible d'aller plus loin)
- Préparer du code pré-écrit pour les débutants en Java
- Utiliser ksqlDB (Jour 7) pour les non-développeurs — pas de code Java

### ❓ "Un apprenant est complètement perdu"

Signe souvent d'un prérequis manquant. Vérifier :
- Linux/terminal : connaît `ls`, `cd`, `cat`, `grep` ?
- Docker : comprend la notion de container ?
- Java/Maven : a déjà compilé un projet Java ?

Si non → lui donner accès à une machine pré-configurée avec tout le code pré-écrit.

### ❓ "Comment expliquer Kafka à un DSI en 5 minutes ?"

> *"Imaginez que votre SI est une ville. Les services sont des bâtiments. Aujourd'hui, quand le bâtiment A doit parler au bâtiment B, il lui envoie un coursier directement. Si B est fermé, le coursier attend ou repart bredouille. Kafka est la poste centrale de la ville : A dépose son courrier, Kafka le stocke et B le récupère quand il est prêt. Chaque service est indépendant. Si l'un tombe, les autres continuent. Et tout le courrier est conservé 30 jours — audit trail complet, conformité automatique."*

---

## 11. Ressources complémentaires

### 📚 Livres recommandés

| Titre | Auteur(s) | Niveau | Disponible |
|-------|-----------|--------|------------|
| Kafka: The Definitive Guide | Shapira, Palino, Sivaram | Intermédiaire | O'Reilly |
| Designing Event-Driven Systems | Ben Stopford | Avancé | Gratuit PDF (Confluent) |
| Kafka Streams in Action | William Bejeck | Avancé | Manning |
| Making Sense of Stream Processing | Martin Kleppmann | Intermédiaire | Gratuit PDF |

### 🌐 Ressources en ligne

```
Documentation officielle :
  https://kafka.apache.org/documentation/
  https://docs.confluent.io/

Tutoriels interactifs :
  https://developer.confluent.io/courses/
  https://kafka-tutorials.confluent.io/

Communauté :
  https://launchpass.com/confluentcommunity  (Slack)
  https://stackoverflow.com/questions/tagged/apache-kafka

Certifications :
  https://www.confluent.io/certification/  (CCDAK, CCOAK)
```

### 🛠 Outils complémentaires

| Outil | Usage | Lien |
|-------|-------|------|
| Kafka UI | Interface web gratuite | github.com/provectuslabs/kafka-ui |
| AKHQ | Alternative Kafka UI | akhq.io |
| Offset Explorer | GUI Windows/Mac/Linux | kafkatool.com |
| Kcat (kafkacat) | CLI avancé | github.com/edenhill/kcat |
| Conduktor | Platform enterprise | conduktor.io |
| Confluent CLI | CLI Confluent Cloud | docs.confluent.io/confluent-cli |

### 📊 Métriques à surveiller en production

```
CRITIQUE (alerte immédiate) :
  kafka_broker_under_replicated_partitions > 0
  kafka_broker_active_controller_count != 1
  kafka_broker_offline_partitions_count > 0

HAUTE (alerte dans les 5 minutes) :
  kafka_consumer_lag > 10 000
  kafka_produce_request_latency_p99_ms > 500
  disk_usage_percent > 80

MOYENNE (alerte dans l'heure) :
  kafka_network_request_queue_size > 100
  jvm_memory_heap_used_percent > 85
```

---

## 🎯 Résumé — Les 10 commandements du formateur Kafka

1. **Tu feras les labs toi-même** la veille, sans regarder les solutions
2. **Tu démarreras par le "Pourquoi"** avant de montrer le "Comment"
3. **Tu ne dépasseras pas 20 minutes de théorie** consécutive
4. **Tu laisseras les apprenants taper eux-mêmes** — jamais à leur place
5. **Tu utiliseras des analogies du quotidien** pour chaque concept abstrait
6. **Tu liras l'évaluation avant** et **tu y reviendras** en fin de journée
7. **Tu feras le quiz collectivement** avec auto-correction et discussion
8. **Tu adapteras le rythme** au groupe, pas au programme
9. **Tu préparerez du code pré-écrit** pour les non-développeurs
10. **Tu termineras toujours par "L'essentiel à retenir"** — sans exception

---

*Formation Kafka 21 Jours — De Zéro à Héros | Approche 80% Pratique*
*Guide du Formateur v1.0 — Tous droits réservés*
