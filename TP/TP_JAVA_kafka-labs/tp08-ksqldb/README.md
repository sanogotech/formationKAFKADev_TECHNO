## TP08 – ksqlDB : Guide pas à pas (sans code Java)

Ce guide vous permet d’exécuter l’intégralité du TP en utilisant **uniquement Docker et ksqlDB**, sans écrire de code Java.  
Les seules commandes nécessaires sont des commandes shell et des requêtes SQL.

---

### 1. Prérequis

- **Docker Desktop** installé et démarré
- **Docker Compose** (inclus avec Docker Desktop)
- Ports disponibles : 9092 (Kafka), 8088 (ksqlDB), 8080 (Kafka UI), 8081 (Schema Registry)

> ⚠️ Le TP s’appuie sur le topic `tp01-commandes` déjà créé et alimenté lors du TP02.  
> Si ce topic est vide ou inexistant, suivez l’**étape 2b** pour y injecter des messages de test.

---

### 2. Démarrer la stack complète

Ouvrez un terminal dans le dossier contenant `docker-compose-ksqldb.yml` et exécutez :

```bash
docker compose -f docker-compose-ksqldb.yml up -d
```

Cette commande lance :
- Kafka (mode KRaft)
- Schema Registry
- ksqlDB Server
- ksqlDB CLI (conteneur prêt à l’emploi)
- Kafka UI (interface web)

Attendez 30 secondes environ que tous les services soient **healthy**.

Vérifiez que ksqlDB répond :

```bash
curl http://localhost:8088/info
```

Vous devez voir un JSON contenant la version.

---

### 2b. (Optionnel) Alimenter le topic `tp01-commandes` avec des données factices

Si vous n’avez pas de données existantes, utilisez le **producteur console** intégré à Kafka.

Ouvrez un second terminal et connectez-vous au conteneur Kafka :

```bash
docker exec -it tp08-kafka bash
```

Puis lancez la production de messages JSON (une ligne par commande) :

```bash
kafka-console-producer --bootstrap-server localhost:9092 --topic tp01-commandes --property parse.key=true --property key.separator=,
```

> **Important** : la syntaxe attend une **clé** avant la virgule, puis la valeur JSON.  
> Exemple de message (copiez-collez les lignes une par une) :

```
cmd001,{"id":"cmd001","client":"alice","produit":"laptop","quantite":1,"montant":1200.0,"statut":"PAYEE","timestamp":"2025-03-20T10:00:00"}
cmd002,{"id":"cmd002","client":"bob","produit":"souris","quantite":2,"montant":50.0,"statut":"PAYEE","timestamp":"2025-03-20T10:05:00"}
cmd003,{"id":"cmd003","client":"alice","produit":"clavier","quantite":1,"montant":80.0,"statut":"PAYEE","timestamp":"2025-03-20T10:10:00"}
cmd004,{"id":"cmd004","client":"charlie","produit":"ecran","quantite":1,"montant":350.0,"statut":"PAYEE","timestamp":"2025-03-20T10:15:00"}
cmd005,{"id":"cmd005","client":"bob","produit":"laptop","quantite":1,"montant":1250.0,"statut":"PAYEE","timestamp":"2025-03-20T10:20:00"}
```

Appuyez sur **Ctrl+C** pour quitter le producteur.  
Répétez l’opération si vous voulez plus de messages.

Quittez le conteneur : `exit`

---

### 3. Se connecter à ksqlDB CLI

Dans le terminal principal, exécutez :

```bash
docker exec -it tp08-ksqldb-cli ksql http://ksqldb-server:8088
```

Vous arrivez sur une invite `ksql>`.

---

### 4. Exécuter les requêtes SQL du TP

Vous avez deux possibilités :

#### Option A – Copier/coller les commandes une à une

Ouvrez le fichier `tp08-ksqldb-queries.sql` dans un éditeur.  
Copiez-collez chaque bloc dans l’invite `ksql>` en commençant par :

```sql
SET 'auto.offset.reset' = 'earliest';
```

Puis créez le stream sur le topic existant :

```sql
CREATE OR REPLACE STREAM commandes_stream (
    id VARCHAR,
    client VARCHAR,
    produit VARCHAR,
    quantite INT,
    montant DOUBLE,
    statut VARCHAR,
    timestamp VARCHAR
) WITH (
    KAFKA_TOPIC = 'tp01-commandes',
    VALUE_FORMAT = 'JSON',
    PARTITIONS = 3
);
```

Vérifiez :

```sql
DESCRIBE commandes_stream;
```

Ensuite, exécutez les requêtes d’interrogation (elles ne s’arrêtent pas seules – utilisez **Ctrl+C** pour interrompre) :

```sql
SELECT id, client, produit, montant,
       TIMESTAMPTOSTRING(ROWTIME, 'HH:mm:ss') AS heure
FROM commandes_stream
EMIT CHANGES
LIMIT 10;
```

> **`LIMIT 10`** arrête automatiquement la requête après 10 messages.

Enchaînez avec les autres requêtes du fichier (filtres, stream dérivé `commandes_vip`, table `stats_clients`, jointure, fenêtrage, etc.).

#### Option B – Exécuter tout le script d’un coup

À l’intérieur de ksqlDB CLI :

```sql
RUN SCRIPT '/path/to/tp08-ksqldb-queries.sql';
```

Mais attention : le fichier doit être accessible depuis le conteneur.  
Pour cela, vous pouvez le copier dans le conteneur (hors scope de ce guide simple).  
Préférez l’option A pour le TP.

---

### 5. Vérifier les résultats avec Kafka UI

Ouvrez un navigateur à l’adresse : [http://localhost:8080](http://localhost:8080)

- Dans l’onglet **Topics**, vous verrez :
  - `tp01-commandes` (topic source)
  - `COMMANDES_VIP` (créé automatiquement par ksqlDB)
  - `STATS_CLIENTS` (topic de la table)
  - `COMMANDES_ENRICHIES` (jointure)

- Cliquez sur un topic puis sur **Messages** pour visualiser les données produites par ksqlDB.

---

### 6. Arrêter et nettoyer proprement

Une fois le TP terminé, retournez dans le terminal et exécutez :

```bash
docker compose -f docker-compose-ksqldb.yml down -v
```

L’option `-v` supprime les volumes (données Kafka, topics, etc.) pour repartir d’un environnement vierge au prochain `up`.

---

## Résumé des commandes essentielles

| Action | Commande |
|--------|----------|
| Démarrer tous les services | `docker compose -f docker-compose-ksqldb.yml up -d` |
| Se connecter à ksqlDB CLI | `docker exec -it tp08-ksqldb-cli ksql http://ksqldb-server:8088` |
| Lancer un producteur console (si besoin) | `docker exec -it tp08-kafka bash` puis `kafka-console-producer ...` |
| Accéder à Kafka UI | http://localhost:8080 |
| Arrêter et tout supprimer | `docker compose -f docker-compose-ksqldb.yml down -v` |

---

## Points clés à retenir (sans code)

- **ksqlDB transforme des topics Kafka en streams/table SQL**.
- Les `CREATE STREAM AS SELECT` créent automatiquement de nouveaux topics.
- Les requêtes **push** (`EMIT CHANGES`) sont des flux continus.
- Les requêtes **pull** (sans `EMIT CHANGES`) sont des instantanés sur une table.
- Toute l’orchestration se fait via Docker et des commandes SQL, sans Java.

Vous pouvez maintenant exécuter le TP complètement en ligne de commande.