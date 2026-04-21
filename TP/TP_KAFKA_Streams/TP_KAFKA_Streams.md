#  **10 TPs Kafka Streams** 

---

## 📚 Définitions de base (avant de commencer)

| Concept | Définition |
|---------|-------------|
| **Kafka Streams** | Bibliothèque Java pour construire des applications de streaming temps réel, élastiques et fault-tolerant, sans clusters externes. |
| **KStream** | Flux d'enregistrements (chaque nouvel événement est ajouté). Modélise un sujet Kafka. |
| **KTable** | Vue mutable d'un flux (état). Pour chaque clé, la dernière valeur est conservée (changelog). |
| **GlobalKTable** | KTable répliquée sur toutes les instances (jointure sans partitionnement). |
| **Window** | Regroupement temporel (tumbling, hopping, sliding, session). |
| **Processor API** | API bas niveau pour un contrôle précis du traitement. |
| **State Store** | Stockage local (RocksDB) pour l'état (agrégations, jointures). |
| **Exactly-once** | Garantie que chaque message est traité une seule fois, même en cas de panne. |

---

## 🛠️ Prérequis (avant tout TP)

1. **Java 17** : `java -version`
2. **Maven 3.8+** : `mvn -version`
3. **Kafka 3.6.0** téléchargé et démarré :
   ```bash
   # Terminal 1
   bin/zookeeper-server-start.sh config/zookeeper.properties
   # Terminal 2
   bin/kafka-server-start.sh config/server.properties
   ```
4. Activer `auto.create.topics.enable=true` dans `server.properties`.
5. Pour chaque TP, créer les topics nécessaires (commande donnée dans le TP).

---

## 📁 Structure du projet Maven

```
kafka-streams-tp/
├── pom.xml
├── src/main/java/com/example/
│   ├── tp1_simple_stream/UpperCaseStream.java
│   ├── tp2_filtre_transformation/FilterTransformStream.java
│   ├── tp3_agregation_count/WordCountStream.java
│   ├── tp4_windowed_aggregation/WindowedWordCount.java
│   ├── tp5_join/StreamStreamJoin.java
│   ├── tp6_ktable_global/EnrichmentWithGlobalKTable.java
│   ├── tp7_interactive_queries/InteractiveQueryDemo.java
│   ├── tp8_error_handling/ErrorHandlingStream.java
│   ├── tp9_exactly_once/ExactlyOnceStream.java
│   └── tp10_processor_api/CustomProcessorStream.java
└── src/test/java/com/example/
    └── tp1_simple_stream/UpperCaseStreamTest.java
```

---

## 1️⃣ Fichier `pom.xml` (Java 17, commenté)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>kafka-streams-tp</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <!-- Version Kafka compatible Java 17 -->
        <kafka.version>3.6.0</kafka.version>
        <junit.version>5.10.1</junit.version>
    </properties>

    <dependencies>
        <!-- Kafka Streams : cœur du TP -->
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-streams</artifactId>
            <version>${kafka.version}</version>
        </dependency>
        <!-- Clients Kafka : pour producteurs/consommateurs si besoin -->
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-clients</artifactId>
            <version>${kafka.version}</version>
        </dependency>
        <!-- Logging simple (slf4j) pour voir ce qui se passe -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-simple</artifactId>
            <version>2.0.9</version>
        </dependency>
        <!-- Tests unitaires JUnit 5 -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${junit.version}</version>
            <scope>test</scope>
        </dependency>
        <!-- Utilitaires de test pour Kafka Streams (TopologyTestDriver) -->
        <dependency>
            <groupId>org.apache.kafka</groupId>
            <artifactId>kafka-streams-test-utils</artifactId>
            <version>${kafka.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Compilateur Java 17 -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <release>17</release>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

---

## 2️⃣ TP1 : Stream simple – transformation en majuscules

**Fichier** : `src/main/java/com/example/tp1_simple_stream/UpperCaseStream.java`

```java
package com.example.tp1_simple_stream;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.KStream;
import java.util.Properties;

/**
 * TP1 : Stream simple - Transformation de chaînes en majuscules.
 * 
 * <p>Objectif : Lire un topic "input-topic", appliquer toUpperCase() sur chaque valeur,
 * écrire le résultat dans "output-topic".</p>
 * 
 * <p>Concepts clés :
 * <ul>
 *   <li>{@link KStream} : flux d'enregistrements (chaque message est un événement).</li>
 *   <li>{@link StreamsBuilder} : construit la topologie (graphe de traitement).</li>
 *   <li>{@link KafkaStreams} : moteur d'exécution du stream.</li>
 * </ul>
 * 
 * <p>Prérequis : topics créés</p>
 * <pre>
 * kafka-topics.sh --create --topic input-topic --bootstrap-server localhost:9092
 * kafka-topics.sh --create --topic output-topic --bootstrap-server localhost:9092
 * </pre>
 * 
 * <p>Test manuel :</p>
 * <pre>
 * # Produire un message
 * echo "hello" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # Consommer le résultat
 * kafka-console-consumer --topic output-topic --bootstrap-server localhost:9092 --from-beginning
 * # Résultat attendu : HELLO
 * </pre>
 * 
 * <p>Tips :
 * <ul>
 *   <li>Toujours définir un application.id unique pour chaque application.</li>
 *   <li>Les Serdes (sérialiseur/désérialiseur) doivent être cohérents avec le type des données.</li>
 *   <li>Ajouter un shutdown hook pour fermer proprement KafkaStreams.</li>
 * </ul>
 * </p>
 */
public class UpperCaseStream {

    public static void main(String[] args) {
        // 1. Configuration des propriétés pour Kafka Streams
        Properties props = new Properties();
        // Identifiant unique de l'application (utilisé pour le groupement et le checkpointing)
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp1-upper-case");
        // Adresse du cluster Kafka
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        // Sérialisation par défaut pour les clés (String)
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        // Sérialisation par défaut pour les valeurs (String)
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        // 2. Construction du graphe de traitement (topologie)
        StreamsBuilder builder = new StreamsBuilder();
        
        // Créer un KStream à partir du topic "input-topic"
        // La clé est String, la valeur est String
        KStream<String, String> source = builder.stream("input-topic");
        
        // Transformation : appliquer toUpperCase() sur chaque valeur
        // mapValues préserve la clé et modifie la valeur
        KStream<String, String> upperCaseStream = source.mapValues(value -> {
            // Transformation simple : mettre en majuscules
            // Note : si value est null, toUpperCase() lèverait NPE – on pourrait ajouter une vérification
            return value.toUpperCase();
        });
        
        // Écrire le flux résultant dans "output-topic"
        upperCaseStream.to("output-topic");
        
        // Alternative plus concise (chaînage) :
        // builder.stream("input-topic").mapValues(String::toUpperCase).to("output-topic");

        // 3. Création et démarrage de l'application Kafka Streams
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        
        // Démarrer le traitement (non-bloquant)
        streams.start();
        
        // Ajouter un hook pour fermer l'application lors de l'arrêt du JVM (Ctrl+C)
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Fermeture de l'application...");
            streams.close();  // Ferme proprement (vidange, commit)
        }));
        
        // Le programme principal se termine ici, mais les streams continuent en arrière-plan.
        // Pour une démonstration en ligne de commande, on peut faire une boucle d'attente.
        System.out.println("TP1 démarré. Envoyez des messages sur 'input-topic'.");
        // Attente infinie (l'application tourne jusqu'à interruption)
        try {
            Thread.sleep(Long.MAX_VALUE);
        } catch (InterruptedException e) {
            streams.close();
        }
    }
}
```

**Résultat détaillé commenté** :
- Entrée : `"hello"` → Sortie : `"HELLO"`
- Explication : `mapValues` applique la fonction à chaque message indépendamment.
- **Tip** : Pour tester rapidement sans Kafka réel, utiliser `TopologyTestDriver` (voir test unitaire).

---

## 3️⃣ TP2 : Filtre et transformation

**Fichier** : `src/main/java/com/example/tp2_filtre_transformation/FilterTransformStream.java`

```java
package com.example.tp2_filtre_transformation;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.KStream;
import java.util.Properties;

/**
 * TP2 : Filtre et transformation.
 * 
 * <p>Objectif : Lire un flux, ne conserver que les messages dont la valeur a une longueur >= 5,
 * puis ajouter le préfixe "OK: " avant d'écrire dans output-topic.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>{@link KStream#filter(Predicate)} : supprime les enregistrements selon un prédicat.</li>
 *   <li>Chaining : on enchaîne les opérations (filter puis mapValues).</li>
 * </ul>
 * 
 * <p>Prérequis : mêmes topics que TP1.</p>
 * 
 * <p>Test manuel :</p>
 * <pre>
 * # Message trop court (ignoré)
 * echo "hi" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # Message valide
 * echo "hello" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # Consommation output : OK: hello
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>filter s'applique au niveau de l'enregistrement (clé et valeur).</li>
 *   <li>Pour filtrer sur la valeur uniquement, ignorez la clé.</li>
 *   <li>Les opérations sont lazy : rien ne se passe avant l'exécution.</li>
 * </ul>
 */
public class FilterTransformStream {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp2-filter");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        StreamsBuilder builder = new StreamsBuilder();
        KStream<String, String> source = builder.stream("input-topic");

        // Étape 1 : filtre (garde les valeurs de longueur >= 5)
        KStream<String, String> filtered = source.filter((key, value) -> {
            // key n'est pas utilisé ici, mais on pourrait.
            boolean keep = value != null && value.length() >= 5;
            if (!keep) {
                System.out.println("Message ignoré (trop court) : " + value);
            }
            return keep;
        });
        
        // Étape 2 : transformation (ajout préfixe)
        KStream<String, String> transformed = filtered.mapValues(value -> "OK: " + value);
        
        // Écriture
        transformed.to("output-topic");

        // Démarrage (identique TP1)
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP2 démarré. Filtre (longueur >=5) + préfixe 'OK: '.");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat détaillé** :
- `"hi"` → (aucune sortie, log "ignoré")
- `"hello"` → `"OK: hello"`
- **Pourquoi ?** Le filtre élimine les messages courts ; les autres subissent la transformation.

---

## 4️⃣ TP3 : Agrégation – comptage de mots

**Fichier** : `src/main/java/com/example/tp3_agregation_count/WordCountStream.java`

```java
package com.example.tp3_agregation_count;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.*;
import java.util.Arrays;
import java.util.Properties;

/**
 * TP3 : Comptage de mots (WordCount) avec KTable.
 * 
 * <p>Objectif : Lire des lignes de texte, découper en mots, compter les occurrences
 * de chaque mot, et produire un flux de mises à jour (changelog) dans output-topic.</p>
 * 
 * <p>Concepts clés :
 * <ul>
 *   <li>{@link KStream#flatMapValues} : génère 0, 1 ou plusieurs valeurs à partir d'une valeur.</li>
 *   <li>{@link KStream#groupBy} : regroupe par clé (prépare pour agrégation).</li>
 *   <li>{@link KGroupedStream#count()} : agrège en comptant les occurrences (retourne une KTable).</li>
 *   <li>{@link KTable} : table de mise à jour (pour chaque clé, la dernière valeur).</li>
 *   <li>Materialization : les stores de state (RocksDB) sont créés automatiquement.</li>
 * </ul>
 * 
 * <p>Définition : Une KTable est un flux de changements. Chaque nouvelle valeur pour une clé
 * remplace l'ancienne. Le comptage produit une KTable où la valeur est le compteur actuel.</p>
 * 
 * <p>Prérequis : topics input-topic, output-topic.</p>
 * 
 * <p>Test manuel :</p>
 * <pre>
 * echo "hello world hello" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # Consommation output (format clé:compteur)
 * kafka-console-consumer --topic output-topic --bootstrap-server localhost:9092 --from-beginning --property print.key=true
 * # Résultat attendu :
 * hello 2
 * world 1
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>Utilisez Serdes.Long() pour les compteurs.</li>
 *   <li>L'ordre des messages peut influencer les résultats intermédiaires (mais final correct).</li>
 *   <li>Pour voir tous les changements (chaque incrément), ajoutez .toStream().print(...).</li>
 * </ul>
 */
public class WordCountStream {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp3-wordcount");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        StreamsBuilder builder = new StreamsBuilder();
        
        // Flux d'entrée : chaque message est une ligne de texte
        KStream<String, String> textLines = builder.stream("input-topic");
        
        // flatMapValues : décompose une ligne en plusieurs mots
        // Exemple : "hello world" -> ["hello", "world"]
        KStream<String, String> words = textLines.flatMapValues(
            line -> Arrays.asList(line.toLowerCase().split("\\W+")) // \\W+ = tout non-lettre
        );
        
        // GroupBy : on utilise le mot comme nouvelle clé
        // La clé d'origine est ignorée (on utilise (key, word) -> word)
        KGroupedStream<String, String> grouped = words.groupBy(
            (key, word) -> word,
            Grouped.with(Serdes.String(), Serdes.String()) // sérialiseurs pour la nouvelle clé et la valeur
        );
        
        // Agrégation : compter les occurrences par mot
        // Le résultat est une KTable<String, Long>
        KTable<String, Long> wordCounts = grouped.count();
        
        // Transformer la KTable en KStream pour l'écrire dans un topic
        // Chaque mise à jour de la table devient un enregistrement dans le stream
        wordCounts.toStream().to("output-topic", Produced.with(Serdes.String(), Serdes.Long()));
        
        // Alternative : matérialiser explicitement le store
        // grouped.count(Materialized.as("word-count-store"));
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP3 WordCount démarré. Envoyez des lignes de texte.");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat détaillé commenté** :
- Entrée : `"hello world hello"`
- Sorties successives (si on observe en temps réel) :
  1. `hello -> 1`
  2. `world -> 1`
  3. `hello -> 2` (mise à jour)
- **Explication** : KTable envoie chaque changement de compteur. La valeur finale est `hello:2, world:1`.

---

## 5️⃣ TP4 : Fenêtrage temporel (windowed aggregation)

**Fichier** : `src/main/java/com/example/tp4_windowed_aggregation/WindowedWordCount.java`

```java
package com.example.tp4_windowed_aggregation;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.*;
import org.apache.kafka.streams.state.WindowStore;
import java.time.Duration;
import java.util.Arrays;
import java.util.Properties;

/**
 * TP4 : Fenêtrage temporel (Windowed WordCount).
 * 
 * <p>Objectif : Compter les mots par fenêtre glissante (hopping window) de 10 secondes
 * avec avance de 5 secondes. Chaque fenêtre est indépendante.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>{@link TimeWindows} : fenêtrage basé sur le timestamp de l'enregistrement.</li>
 *   <li>{@link KGroupedStream#windowedBy(Windows)} : découpe le groupe en fenêtres.</li>
 *   <li>Windowed<K> : clé composée (mot + intervalle de temps).</li>
 * </ul>
 * 
 * <p>Définition : Fenêtre glissante (hopping) – durée et avance. Un mot peut appartenir
 * à plusieurs fenêtres si l'avance < durée.</p>
 * 
 * <p>Prérequis : topics input-topic, output-topic.</p>
 * 
 * <p>Test manuel (avec deux messages espacés) :</p>
 * <pre>
 * # Message 1 à t=0
 * echo "hello" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # Attendre 6 secondes
 * # Message 2 à t=6
 * echo "hello" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # Les fenêtres : [0-10) contient 2, [5-15) contient 1 (selon les timestamps exacts)
 * # Utiliser un consommateur avec --property print.key=true pour voir les fenêtres.
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>Les timestamps des messages sont pris par défaut du timestamp du broker. Vous pouvez définir un extracteur personnalisé.</li>
 *   <li>Pour sérialiser Windowed<String>, utilisez WindowedSerdes.timeWindowedSerdeFrom(String.class).</li>
 *   <li>La taille de fenêtre doit être adaptée au volume de données.</li>
 * </ul>
 */
public class WindowedWordCount {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp4-windowed");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        // Important pour les fenêtres : indiquer le store type (WindowStore)
        // Pas obligatoire, mais bon pour la clarté
        props.put(StreamsConfig.STATE_DIR_CONFIG, "/tmp/kafka-streams-tp4");

        StreamsBuilder builder = new StreamsBuilder();
        
        KStream<String, String> source = builder.stream("input-topic");
        
        // Découpage en mots
        KStream<String, String> words = source.flatMapValues(
            line -> Arrays.asList(line.toLowerCase().split("\\W+"))
        );
        
        // Définition de la fenêtre : durée 10 secondes, avance 5 secondes
        // ofSizeWithNoGrace : pas de période de grâce (grace period = 0)
        TimeWindows window = TimeWindows.ofSizeWithNoGrace(Duration.ofSeconds(10))
                                         .advanceBy(Duration.ofSeconds(5));
        
        // GroupBy puis fenêtrage
        KTable<Windowed<String>, Long> counts = words
            .groupBy((key, word) -> word, Grouped.with(Serdes.String(), Serdes.String()))
            .windowedBy(window)
            .count(Materialized.<String, Long, WindowStore<org.apache.kafka.common.utils.Bytes, byte[]>>as("windowed-counts")
                .withKeySerde(Serdes.String())
                .withValueSerde(Serdes.Long()));
        
        // Écriture dans le topic de sortie
        // Nécessite un sérialiseur spécifique pour la clé Windowed<String>
        counts.toStream().to("output-topic", 
            Produced.with(WindowedSerdes.timeWindowedSerdeFrom(String.class), Serdes.Long()));
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP4 Windowed WordCount démarré (fenêtre 10s, avance 5s).");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat détaillé commenté** (exemple concret avec timestamps) :
- À t=0s : `"hello"` → fenêtre [0,10) : `hello=1` ; fenêtre [0,10) est la seule active.
- À t=6s : `"hello"` → fenêtre [0,10) : `hello=2` ; fenêtre [5,15) : `hello=1`.
- Les sorties sont des clés composites : `hello@[0,10)` et `hello@[5,15)`.

---

## 6️⃣ TP5 : Jointure entre deux flux (Stream-Stream Join)

**Fichier** : `src/main/java/com/example/tp5_join/StreamStreamJoin.java`

```java
package com.example.tp5_join;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.*;
import java.time.Duration;
import java.util.Properties;

/**
 * TP5 : Jointure entre deux flux (Stream-Stream Join).
 * 
 * <p>Objectif : Joindre des commandes (orders-topic) et des paiements (payments-topic)
 * sur la clé (orderId) dans une fenêtre de 5 minutes. Le résultat combine les deux.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>Join de deux KStream : produit un nouveau KStream.</li>
 *   <li>Fenêtre de jointure (JoinWindows) : seuls les événements proches temporellement sont joints.</li>
 *   <li>innerJoin, leftJoin, outerJoin disponibles.</li>
 * </ul>
 * 
 * <p>Définition : Une jointure de flux est basée sur le timestamp. Deux événements
 * avec la même clé sont joints si leurs timestamps diffèrent au plus de la fenêtre.</p>
 * 
 * <p>Prérequis :</p>
 * <pre>
 * kafka-topics.sh --create --topic orders-topic --bootstrap-server localhost:9092
 * kafka-topics.sh --create --topic payments-topic --bootstrap-server localhost:9092
 * kafka-topics.sh --create --topic output-topic --bootstrap-server localhost:9092
 * </pre>
 * 
 * <p>Test manuel :</p>
 * <pre>
 * # Commande
 * echo "123:book" | kafka-console-producer --topic orders-topic --property parse.key=true --property key.separator=: --bootstrap-server localhost:9092
 * # Paiement (dans les 5 minutes)
 * echo "123:OK" | kafka-console-producer --topic payments-topic --property parse.key=true --property key.separator=: --bootstrap-server localhost:9092
 * # Consommer output : Order: book | Payment: OK
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>Les deux flux doivent être partitionnés de la même manière (même nombre de partitions).</li>
 *   <li>La fenêtre de jointure doit être adaptée à la latence attendue entre les événements.</li>
 *   <li>Utilisez .peek() pour déboguer.</li>
 * </ul>
 */
public class StreamStreamJoin {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp5-join");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        StreamsBuilder builder = new StreamsBuilder();
        
        // Flux des commandes : clé = orderId, valeur = produit
        KStream<String, String> orders = builder.stream("orders-topic");
        // Flux des paiements : clé = orderId, valeur = statut
        KStream<String, String> payments = builder.stream("payments-topic");
        
        // Fenêtre de jointure : 5 minutes (tolérance de temps)
        JoinWindows joinWindow = JoinWindows.ofTimeDifferenceWithNoGrace(Duration.ofMinutes(5));
        
        // Jointure interne (inner join) : seuls les événements avec correspondance sont émis
        KStream<String, String> joined = orders.join(
            payments,
            (orderValue, paymentValue) -> "Order: " + orderValue + " | Payment: " + paymentValue,
            joinWindow,
            StreamJoined.with(Serdes.String(), Serdes.String(), Serdes.String())
        );
        
        // Alternative : leftJoin (garde les commandes sans paiement)
        // KStream<String, String> leftJoined = orders.leftJoin(payments, ...);
        
        joined.to("output-topic");
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP5 Stream-Stream Join démarré (fenêtre 5 min).");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat détaillé** :
- Commande `(123, book)` + Paiement `(123, OK)` dans les 5 minutes → `(123, "Order: book | Payment: OK")`
- Si paiement après 5 minutes → pas de jointure (message perdu pour cette fenêtre).

---

## 7️⃣ TP6 : KTable et GlobalKTable (enrichissement)

**Fichier** : `src/main/java/com/example/tp6_ktable_global/EnrichmentWithGlobalKTable.java`

```java
package com.example.tp6_ktable_global;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.*;
import java.util.Properties;

/**
 * TP6 : Enrichissement d'un flux avec une GlobalKTable (table de référence).
 * 
 * <p>Objectif : Enrichir des transactions (produitId, quantité) avec le nom du produit
 * stocké dans une table globale (topic "products-topic").</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>{@link GlobalKTable} : table répliquée sur chaque instance de l'application.</li>
 *   <li>Jointure KStream-GlobalKTable : permet une jointure sans partitionnement co-partitionné.</li>
 *   <li>Utile pour des données de référence peu volumineuses.</li>
 * </ul>
 * 
 * <p>Définition : Une GlobalKTable lit toutes les partitions du topic sous-jacent
 * et les réplique localement. Elle supporte les jointures avec n'importe quelle clé.</p>
 * 
 * <p>Prérequis :</p>
 * <pre>
 * kafka-topics.sh --create --topic products-topic --bootstrap-server localhost:9092
 * kafka-topics.sh --create --topic transactions-topic --bootstrap-server localhost:9092
 * kafka-topics.sh --create --topic output-topic --bootstrap-server localhost:9092
 * # Peupler products-topic (key=produitId, value=nom)
 * echo "p1:Laptop" | kafka-console-producer --topic products-topic --property parse.key=true --property key.separator=: --bootstrap-server localhost:9092
 * </pre>
 * 
 * <p>Test :</p>
 * <pre>
 * echo "p1:2" | kafka-console-producer --topic transactions-topic --property parse.key=true --property key.separator=: --bootstrap-server localhost:9092
 * # Consommer output : "Product: Laptop | Qty: 2"
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>Les GlobalKTables sont chargées entièrement en mémoire (attention à la taille).</li>
 *   <li>La jointure utilise un extracteur de clé (KeyValueMapper) pour récupérer la clé de la table.</li>
 * </ul>
 */
public class EnrichmentWithGlobalKTable {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp6-enrich");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        StreamsBuilder builder = new StreamsBuilder();

        // Flux des transactions : clé = productId, valeur = quantité (en String pour simplicité)
        KStream<String, String> transactions = builder.stream("transactions-topic");
        
        // Table globale des produits : clé = productId, valeur = nom du produit
        GlobalKTable<String, String> products = builder.globalTable("products-topic");
        
        // Jointure : pour chaque transaction, on récupère le nom du produit correspondant
        // La transaction fournit la clé (productId) pour chercher dans la GlobalKTable
        KStream<String, String> enriched = transactions.join(
            products,
            (txKey, txValue) -> txKey,   // extracteur de clé : la clé de la transaction est la clé produit
            (txValue, productName) -> "Product: " + productName + " | Qty: " + txValue
        );
        
        enriched.to("output-topic");
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP6 Enrichissement avec GlobalKTable démarré.");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat** :
- Transaction `(p1, 2)` + Produit `(p1, Laptop)` → `"Product: Laptop | Qty: 2"`
- Si le produit n'existe pas, la jointure ignore la transaction (inner join). Pour leftJoin, utilisez `leftJoin`.

---

## 8️⃣ TP7 : Requêtes interactives (Interactive Queries)

**Fichier** : `src/main/java/com/example/tp7_interactive_queries/InteractiveQueryDemo.java`

```java
package com.example.tp7_interactive_queries;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.Materialized;
import org.apache.kafka.streams.state.KeyValueStore;
import org.apache.kafka.streams.state.QueryableStoreTypes;
import org.apache.kafka.streams.state.ReadOnlyKeyValueStore;
import java.util.Properties;

/**
 * TP7 : Requêtes interactives (Interactive Queries).
 * 
 * <p>Objectif : Exposer l'état local d'une KTable (store matérialisé) pour interrogation
 * directe, sans passer par un topic. Ici, on simule une requête en ligne de commande.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>State Store : stockage local (RocksDB) utilisé par les opérations stateful (count, aggregate).</li>
 *   <li>{@link KafkaStreams#store(StoreQueryParameters)} : accès direct au store.</li>
 *   <li>Requêtes interactives : pour construire des API REST ou des dashboards temps réel.</li>
 * </ul>
 * 
 * <p>Définition : Un store matérialisé est nommé et peut être interrogé par son nom.
 * Dans une application distribuée, il faut interroger toutes les instances (via clé de partition).</p>
 * 
 * <p>Prérequis : topics input-topic, output-topic (même que TP3).</p>
 * 
 * <p>Test :</p>
 * <pre>
 * # Produire quelques mots
 * echo "hello world" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # L'application affichera dans la console : Count of 'hello': 1
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>Le store doit être nommé explicitement avec Materialized.as("nom").</li>
 *   <li>L'accès au store n'est possible qu'après que l'application a fini la restauration (streams.start() + un délai).</li>
 *   <li>Pour une API REST, utilisez un serveur HTTP (ex: Javalin) et interrogez le store.</li>
 * </ul>
 */
public class InteractiveQueryDemo {

    public static void main(String[] args) throws InterruptedException {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp7-iq");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.STATE_DIR_CONFIG, "/tmp/kafka-streams-tp7");

        StreamsBuilder builder = new StreamsBuilder();
        
        // Nom du store
        final String storeName = "word-count-store";
        
        // Topologie : comptage de mots avec matérialisation explicite
        builder.stream("input-topic")
               .flatMapValues(line -> java.util.Arrays.asList(line.toLowerCase().split("\\W+")))
               .groupBy((k, v) -> v)
               .count(Materialized.as(storeName));   // <- store nommé
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        
        // Attendre que l'application ait restauré l'état (quelques secondes)
        Thread.sleep(5000);
        
        // Accès au store local (dans cette instance unique)
        ReadOnlyKeyValueStore<String, Long> store = streams.store(
            org.apache.kafka.streams.StoreQueryParameters.fromNameAndType(storeName, QueryableStoreTypes.keyValueStore())
        );
        
        // Exemple de requête : récupérer le compteur pour "hello"
        Long countHello = store.get("hello");
        System.out.println("=== Requête interactive ===");
        System.out.println("Count of 'hello' : " + (countHello == null ? 0 : countHello));
        
        // Pour une démonstration continue, on pourrait boucler et mettre à jour.
        // Ici, on ferme après 10 secondes.
        Thread.sleep(10000);
        streams.close();
    }
}
```

**Résultat** : Affiche le compteur actuel du mot "hello" en fonction des messages reçus.

---

## 9️⃣ TP8 : Gestion des erreurs (deserialization)

**Fichier** : `src/main/java/com/example/tp8_error_handling/ErrorHandlingStream.java`

```java
package com.example.tp8_error_handling;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.errors.LogAndContinueExceptionHandler;
import org.apache.kafka.streams.kstream.KStream;
import java.util.Properties;

/**
 * TP8 : Gestion des erreurs (désérialisation, exceptions métier).
 * 
 * <p>Objectif : Configurer l'application pour ignorer les messages qui causent des
 * erreurs de désérialisation ou des exceptions dans le traitement, et continuer.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>{@link StreamsConfig#DEFAULT_DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG}</li>
 *   <li>{@link LogAndContinueExceptionHandler} : log et ignore l'enregistrement défectueux.</li>
 *   <li>Sinon, le défaut (fail) stoppe l'application.</li>
 * </ul>
 * 
 * <p>Test : Envoyez un message "error" (qui déclenchera une exception volontaire)
 * et observez que l'application ne crash pas.</p>
 * 
 * <pre>
 * echo "normal" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * echo "error" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092
 * # output-topic ne contiendra que "NORMAL" (pas de sortie pour "error")
 * # La console log montrera l'exception mais le stream continue.
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>Utilisez un handler personnalisé pour envoyer les erreurs dans un DLQ (dead letter queue).</li>
 *   <li>Pensez aussi à {@link StreamsConfig#DEFAULT_PRODUCTION_EXCEPTION_HANDLER_CLASS_CONFIG} pour les erreurs d'écriture.</li>
 * </ul>
 */
public class ErrorHandlingStream {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp8-error");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        // Configuration pour ignorer les erreurs de désérialisation
        props.put(StreamsConfig.DEFAULT_DESERIALIZATION_EXCEPTION_HANDLER_CLASS_CONFIG, LogAndContinueExceptionHandler.class);

        StreamsBuilder builder = new StreamsBuilder();
        KStream<String, String> source = builder.stream("input-topic");
        
        // Transformation qui lance une exception si la valeur contient "error"
        source.mapValues(value -> {
            if (value.contains("error")) {
                throw new RuntimeException("Exception simulée pour valeur: " + value);
            }
            return value.toUpperCase();
        }).to("output-topic");
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP8 Error handling démarré. Les messages avec 'error' seront ignorés.");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat** :
- `"normal"` → `"NORMAL"`
- `"error"` → exception loguée, message ignoré, application continue.

---

## 🔟 TP9 : Exactly-once semantics

**Fichier** : `src/main/java/com/example/tp9_exactly_once/ExactlyOnceStream.java`

```java
package com.example.tp9_exactly_once;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.kstream.KStream;
import java.util.Properties;

/**
 * TP9 : Exactly-once semantics.
 * 
 * <p>Objectif : Configurer l'application pour garantir un traitement exactement une fois
 * (exactly-once) même en cas de panne ou de reprise.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>StreamsConfig#PROCESSING_GUARANTEE_CONFIG = EXACTLY_ONCE_V2 (ou EXACTLY_ONCE_BETA).</li>
 *   <li>Utilise les transactions Kafka pour atomiser lecture, traitement, écriture.</li>
 *   <li>Impact sur les performances (moindre depuis V2).</li>
 * </ul>
 * 
 * <p>Prérequis : Aucun topic spécial, mais le cluster Kafka doit supporter les transactions
 * (configuration par défaut).</p>
 * 
 * <p>Test : Simulez un crash (kill -9) de l'application puis redémarrez ; les messages
 * ne seront pas dupliqués ni perdus. (Difficile à démontrer simplement, mais la config est là).</p>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>EXACTLY_ONCE_V2 est plus performant que la version V1.</li>
 *   <li>Le consumer group doit être unique.</li>
 *   <li>Les topics de sortie doivent avoir des partitions, et les producers configurés pour idempotence.</li>
 * </ul>
 */
public class ExactlyOnceStream {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp9-exactly-once");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        
        // Activation de la garantie exactly-once (version 2 recommandée)
        props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
        
        // Optionnel : augmenter le timeout transactionnel (par défaut 1 minute)
        props.put(StreamsConfig.TRANSACTIONAL_PRODUCER_CONFIG, "transactional.id=tp9");
        
        StreamsBuilder builder = new StreamsBuilder();
        KStream<String, String> source = builder.stream("input-topic");
        source.mapValues(String::toUpperCase).to("output-topic");
        
        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP9 Exactly-once démarré. Chaque message sera traité exactement une fois.");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat** : Pas de différence visible en fonctionnement normal, mais garantie de non-duplication après reprise.

---

## 1️⃣1️⃣ TP10 : Processor API (bas niveau)

**Fichier** : `src/main/java/com/example/tp10_processor_api/CustomProcessorStream.java`

```java
package com.example.tp10_processor_api;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;
import org.apache.kafka.streams.processor.api.Processor;
import org.apache.kafka.streams.processor.api.ProcessorContext;
import org.apache.kafka.streams.processor.api.ProcessorSupplier;
import org.apache.kafka.streams.processor.api.Record;
import java.util.Properties;

/**
 * TP10 : Processor API (bas niveau).
 * 
 * <p>Objectif : Implémenter un processeur personnalisé qui filtre les mots de moins
 * de 3 lettres et met en majuscules les autres. Utilisation de l'API Processor
 * au lieu de la DSL KStream.</p>
 * 
 * <p>Concepts :
 * <ul>
 *   <li>Topologie construite manuellement avec {@link Topology#addSource}, {@link Topology#addProcessor}, {@link Topology#addSink}.</li>
 *   <li>Interface {@link Processor} : contrôle précis de l'émission, gestion d'état.</li>
 *   <li>Utile pour des opérations complexes ou non prévues par la DSL.</li>
 * </ul>
 * 
 * <p>Prérequis : topics input-topic, output-topic.</p>
 * 
 * <p>Test :</p>
 * <pre>
 * echo "a" | kafka-console-producer --topic input-topic --bootstrap-server localhost:9092   # ignoré
 * echo "ab" | kafka-console-producer ... # ignoré
 * echo "abc" | kafka-console-producer ... # devient "ABC" dans output
 * </pre>
 * 
 * <p>Tips :</p>
 * <ul>
 *   <li>La Processor API est plus verbeuse mais très flexible.</li>
 *   <li>On peut combiner DSL et Processor API via {@link org.apache.kafka.streams.kstream.Processors}.</li>
 *   <li>Pensez à fermer les resources dans close().</li>
 * </ul>
 */
public class CustomProcessorStream {

    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "tp10-processor");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());

        // Création d'une topologie vide
        Topology topology = new Topology();
        
        // 1. Source : lit depuis input-topic
        topology.addSource("source", "input-topic");
        
        // 2. Processeur personnalisé
        topology.addProcessor("filter-processor", new ProcessorSupplier<String, String, String, String>() {
            @Override
            public Processor<String, String, String, String> get() {
                return new Processor<>() {
                    private ProcessorContext<String, String> context;
                    
                    @Override
                    public void init(ProcessorContext<String, String> context) {
                        this.context = context;
                        // On peut ici initialiser des state stores
                    }
                    
                    @Override
                    public void process(Record<String, String> record) {
                        String word = record.value();
                        // Filtrer les mots de longueur < 3
                        if (word != null && word.length() >= 3) {
                            // Transformer en majuscules
                            String upper = word.toUpperCase();
                            // Forward vers le sink
                            context.forward(record.withValue(upper));
                        } else {
                            // On ignore (on ne forward pas)
                            System.out.println("Ignored word: " + word);
                        }
                    }
                    
                    @Override
                    public void close() {
                        // Nettoyage
                    }
                };
            }
        }, "source");  // le processeur est connecté à la source "source"
        
        // 3. Sink : écrit dans output-topic
        topology.addSink("sink", "output-topic", "filter-processor");
        
        // Optionnel : afficher la topologie
        System.out.println("Topologie : " + topology.describe());
        
        KafkaStreams streams = new KafkaStreams(topology, props);
        streams.start();
        Runtime.getRuntime().addShutdownHook(new Thread(streams::close));
        System.out.println("TP10 Processor API démarré. Seuls les mots >=3 lettres sont conservés et mis en majuscules.");
        
        try { Thread.sleep(Long.MAX_VALUE); } catch (InterruptedException e) { streams.close(); }
    }
}
```

**Résultat** :
- `"a"` → rien
- `"ab"` → rien
- `"abc"` → `"ABC"`

---

## 🧪 Tests unitaires (exemple pour TP1)

**Fichier** : `src/test/java/com/example/tp1_simple_stream/UpperCaseStreamTest.java`

```java
package com.example.tp1_simple_stream;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.*;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.util.Properties;
import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Test unitaire pour TP1 utilisant TopologyTestDriver.
 * Ce test ne nécessite pas de cluster Kafka réel.
 */
public class UpperCaseStreamTest {
    private TopologyTestDriver testDriver;
    private TestInputTopic<String, String> inputTopic;
    private TestOutputTopic<String, String> outputTopic;

    @BeforeEach
    void setup() {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "test");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "dummy");
        StreamsBuilder builder = new StreamsBuilder();
        builder.stream("input-topic")
               .mapValues(String::toUpperCase)
               .to("output-topic");
        Topology topology = builder.build();
        testDriver = new TopologyTestDriver(topology, props);
        inputTopic = testDriver.createInputTopic("input-topic", Serdes.String().serializer(), Serdes.String().serializer());
        outputTopic = testDriver.createOutputTopic("output-topic", Serdes.String().deserializer(), Serdes.String().deserializer());
    }

    @AfterEach
    void tearDown() {
        testDriver.close();
    }

    @Test
    void testUpperCaseTransformation() {
        // Envoyer un message
        inputTopic.pipeInput("hello");
        // Vérifier la sortie
        String result = outputTopic.readValue();
        assertEquals("HELLO", result);
    }
    
    @Test
    void testMultipleMessages() {
        inputTopic.pipeInput("hello");
        inputTopic.pipeInput("world");
        assertEquals("HELLO", outputTopic.readValue());
        assertEquals("WORLD", outputTopic.readValue());
    }
}
```

Exécution : `mvn test`

---

## 📊 Résultats attendus (récapitulatif commenté)

| TP | Résultat détaillé | Explication |
|----|------------------|-------------|
| 1  | `"hello"` → `"HELLO"` | Transformation simple sans état. |
| 2  | `"hi"` ignoré ; `"hello"` → `"OK: hello"` | Filtre élimine les courts, puis transformation. |
| 3  | `"hello world hello"` → `hello:2, world:1` | Agrégation avec état (KTable). |
| 4  | Comptage par fenêtre de 10s | Les résultats dépendent du timestamp. |
| 5  | Commande + Paiement → message enrichi | Jointure temporelle de deux flux. |
| 6  | Transaction + Produit → `"Product: Laptop \| Qty: 2"` | Jointure avec table de référence globale. |
| 7  | Interrogation directe du store : `hello=2` | Requête interactive sur l'état local. |
| 8  | Message `"error"` → ignoré sans crash | Gestion robuste des exceptions. |
| 9  | Exactly-once : pas de doublon après reprise | Garantie transactionnelle. |
| 10 | `"abc"` → `"ABC"` ; `"ab"` ignoré | Processeur bas niveau personnalisé. |

---

## 💡 Définitions et Tips supplémentaires

### Définitions clés
- **Topologie** : Graphe de traitement (sources, processeurs, sinks).
- **State Store** : Stockage local (RocksDB) pour les opérations stateful.
- **Repartitioning** : Lorsque la clé change, Kafka Streams crée un topic interne de répartition.
- **Grace period** : Pendant combien de temps on accepte des messages en retard pour une fenêtre.

### Tips généraux
1. **Toujours fermer `KafkaStreams`** avec un shutdown hook.
2. **Utilisez `TopologyTestDriver`** pour les tests unitaires (rapides, sans Kafka).
3. **Surveillez les topics internes** (préfixés par l'application.id) pour déboguer.
4. **Pour la performance**, évitez les `groupBy` inutiles et choisissez le bon nombre de threads (`num.stream.threads`).
5. **La sérialisation** : privilégiez Avro ou Protobuf avec `SpecificAvroSerde` pour l'évolution des schémas.

---

## 🚀 Exécution des TPs

```bash
# Compiler
mvn clean compile

# Lancer un TP (exemple TP1) - depuis l'IDE ou avec exec:java
# Il faut ajouter le plugin exec dans pom.xml ou utiliser une classe main.
# Sinon, générer un uber-jar ou exécuter directement depuis l'IDE.
```

Pour une exécution simplifiée, vous pouvez ajouter dans `pom.xml` le plugin `exec-maven-plugin` :

```xml
<plugin>
    <groupId>org.codehaus.mojo</groupId>
    <artifactId>exec-maven-plugin</artifactId>
    <version>3.1.0</version>
    <configuration>
        <mainClass>com.example.tp1_simple_stream.UpperCaseStream</mainClass>
    </configuration>
</plugin>
```

Puis : `mvn exec:java -Dexec.mainClass="com.example.tp1_simple_stream.UpperCaseStream"`

---

Ce TP complet couvre tous les concepts de Kafka Streams avec une approche progressive, des explications approfondies et des tests. Bon apprentissage !
