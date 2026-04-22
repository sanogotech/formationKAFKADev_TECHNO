

# 🧪 TP : Kafka Streams DSL en Python (Simulation)

## 🎯 Objectif

Comprendre les transformations :

* `map`
* `mapValues`
* `filter`
* `selectKey`
* `flatMap`
* `flatMapValues`
* `merge`
* `branch`

---

# 🧭 1. Dataset de départ (simule un topic Kafka)

```python
# Simule un topic Kafka : (key, value)
stream = [
    ("user1", "click:home"),
    ("user2", "click:product"),
    ("user1", "purchase:book"),
    ("user3", "click:home"),
]
```

---

# 🔁 2. map (modifier clé + valeur)

```python
mapped_stream = [(k.upper(), v.upper()) for k, v in stream]

print(mapped_stream)
```

✔ Equivalent Kafka Streams :

```java
stream.map((k, v) -> KeyValue.pair(k.toUpperCase(), v.toUpperCase()))
```

---

# 🧾 3. mapValues (modifier seulement la valeur)

```python
map_values_stream = [(k, v.split(":")[0]) for k, v in stream]

print(map_values_stream)
```

👉 On garde la clé, on transforme la valeur

---

# 🔍 4. filter (filtrer les événements)

```python
filtered_stream = [(k, v) for k, v in stream if "click" in v]

print(filtered_stream)
```

👉 Garde uniquement les clics

---

# 🔑 5. selectKey (changer la clé)

```python
select_key_stream = [(v.split(":")[0], v) for k, v in stream]

print(select_key_stream)
```

👉 La nouvelle clé = type d'événement (`click`, `purchase`)

---

# 🔄 6. flatMap (1 → N avec clé + valeur)

```python
flat_map_stream = []

for k, v in stream:
    parts = v.split(":")
    for part in parts:
        flat_map_stream.append((k, part))

print(flat_map_stream)
```

👉 Un message devient plusieurs

---

# 🧩 7. flatMapValues (1 → N sur valeur seulement)

```python
flat_map_values_stream = [(k, part) for k, v in stream for part in v.split(":")]

print(flat_map_values_stream)
```

---

# 🔀 8. merge (fusion de streams)

```python
stream2 = [
    ("user4", "click:cart"),
    ("user5", "purchase:phone")
]

merged_stream = stream + stream2

print(merged_stream)
```

---

# 🌿 9. branch (séparer en plusieurs flux)

```python
clicks = [(k, v) for k, v in stream if "click" in v]
purchases = [(k, v) for k, v in stream if "purchase" in v]

print("Clicks:", clicks)
print("Purchases:", purchases)
```

👉 Equivalent à :

```java
KStream[] branches = stream.branch(
    (k, v) -> v.contains("click"),
    (k, v) -> v.contains("purchase")
);
```

---

# 🧠 BONUS : Pipeline complet (style Kafka Streams)

```python
result = [
    (k, v.upper())
    for k, v in stream
    if "click" in v
]

print(result)
```

👉 Pipeline :

1. filter
2. mapValues

---

# 📊 Résumé des transformations

| Fonction      | Description                  |
| ------------- | ---------------------------- |
| map           | transforme clé + valeur      |
| mapValues     | transforme uniquement valeur |
| filter        | filtre les messages          |
| selectKey     | change la clé                |
| flatMap       | 1 → plusieurs messages       |
| flatMapValues | 1 valeur → plusieurs         |
| merge         | fusion de streams            |
| branch        | séparation en flux           |

---

# 🚀 Conclusion

Même si **Apache Kafka Streams DSL** est en Java :

👉 Ce TP Python permet de comprendre **80% des concepts** rapidement
👉 Ensuite, tu peux passer facilement à Java / **Kafka Streams réel**

---



---

# 🧪 TP COMPLET : Kafka Streams DSL (Python Simulation + Console)

```python id="kafka_tp_console"
"""
🧠 TP KAFKA STREAMS DSL (SIMULATION PYTHON)

Objectif :
Comprendre les transformations de flux Kafka :
map, mapValues, filter, selectKey, flatMap, merge, branch

👉 On simule un flux temps réel d'événements utilisateurs
"""

# =========================================================
# 📦 1. DATASET (flux d'événements)
# =========================================================

stream = [
    ("user1", "click:home"),
    ("user2", "click:product"),
    ("user1", "purchase:book"),
    ("user3", "click:home"),
    ("user4", "login:success")
]

stream2 = [
    ("user5", "click:cart"),
    ("user6", "purchase:phone")
]

print("\n================ ORIGINAL STREAM ================")
print(stream)


# =========================================================
# 🔁 2. MAP (transformation clé + valeur)
# =========================================================

mapped_stream = []
for k, v in stream:
    mapped_stream.append((k.upper(), v.upper()))

print("\n================ MAP =================")
print(mapped_stream)

"""
💡 Console attendue :
('USER1', 'CLICK:HOME')
('USER2', 'CLICK:PRODUCT')
"""


# =========================================================
# 🧾 3. MAPVALUES (transforme uniquement la valeur)
# =========================================================

map_values_stream = []
for k, v in stream:
    map_values_stream.append((k, v.split(":")[0]))

print("\n================ MAPVALUES =================")
print(map_values_stream)

"""
💡 Console attendue :
('user1', 'click')
('user1', 'purchase')
"""


# =========================================================
# 🔍 4. FILTER (garder uniquement certains events)
# =========================================================

filtered_stream = []
for k, v in stream:
    if "click" in v:
        filtered_stream.append((k, v))

print("\n================ FILTER =================")
print(filtered_stream)

"""
💡 Console attendue :
('user1', 'click:home')
('user2', 'click:product')
('user3', 'click:home')
"""


# =========================================================
# 🔑 5. SELECTKEY (changer la clé)
# =========================================================

select_key_stream = []
for k, v in stream:
    select_key_stream.append((v.split(":")[0], v))

print("\n================ SELECTKEY =================")
print(select_key_stream)

"""
💡 Console attendue :
('click', 'click:home')
('purchase', 'purchase:book')
"""


# =========================================================
# 🔄 6. FLATMAP (1 → N messages)
# =========================================================

flat_map_stream = []

for k, v in stream:
    for part in v.split(":"):
        flat_map_stream.append((k, part))

print("\n================ FLATMAP =================")
print(flat_map_stream)

"""
💡 Console attendue :
('user1','click')
('user1','home')
('user2','click')
('user2','product')
"""


# =========================================================
# 🔀 7. MERGE (fusion de flux)
# =========================================================

merged_stream = stream + stream2

print("\n================ MERGE =================")
print(merged_stream)

"""
💡 Console attendue :
Flux combiné des deux streams
"""


# =========================================================
# 🌿 8. BRANCH (séparation logique)
# =========================================================

clicks = []
purchases = []
others = []

for k, v in stream:
    if "click" in v:
        clicks.append((k, v))
    elif "purchase" in v:
        purchases.append((k, v))
    else:
        others.append((k, v))

print("\n================ BRANCH =================")
print("CLICKS    :", clicks)
print("PURCHASES :", purchases)
print("OTHERS    :", others)

"""
💡 Console attendue :
CLICKS    → interactions navigation
PURCHASES → achats
OTHERS    → login
"""


# =========================================================
# 🧠 9. PIPELINE COMPLET
# =========================================================

pipeline = [
    (k, v.upper())
    for k, v in stream
    if "click" in v
]

print("\n================ PIPELINE =================")
print(pipeline)

"""
💡 Console attendue :
Filtrage + transformation en une seule étape
"""


# =========================================================
# 🎯 FIN
# =========================================================

print("\n✅ TP TERMINÉ AVEC SUCCÈS")
```

---

# 🖥️ SIMULATION CONSOLE APRÈS EXÉCUTION

```
================ ORIGINAL STREAM ================
[('user1', 'click:home'), ('user2', 'click:product'), ...]

================ MAP =================
[('USER1', 'CLICK:HOME'), ('USER2', 'CLICK:PRODUCT'), ...]

================ MAPVALUES =================
[('user1', 'click'), ('user2', 'click'), ('user1', 'purchase')]

================ FILTER =================
[('user1', 'click:home'), ('user2', 'click:product')]

================ SELECTKEY =================
[('click', 'click:home'), ('purchase', 'purchase:book')]

================ FLATMAP =================
[('user1', 'click'), ('user1', 'home'), ...]

================ MERGE =================
[('user1', 'click:home'), ..., ('user5', 'click:cart')]

================ BRANCH =================
CLICKS    : [('user1', 'click:home'), ...]
PURCHASES : [('user1', 'purchase:book')]
OTHERS    : [('user4', 'login:success')]

================ PIPELINE =================
[('user1', 'CLICK:HOME'), ('user2', 'CLICK:PRODUCT')]

✅ TP TERMINÉ AVEC SUCCÈS
```

---

# 🧠 EXPLICATION SIMPLE (IMPORTANT)

## 🔹 1. Ce que représente ce TP

On simule un système temps réel comme :

👉 **Apache Kafka**

Chaque tuple :

```
(user, event)
```

= un message dans un topic Kafka

---

## 🔹 2. Ce que font les transformations

### ✔ map

➡ transforme tout (clé + valeur)

### ✔ mapValues

➡ transforme seulement la valeur

### ✔ filter

➡ garde certains événements

### ✔ selectKey

➡ change la clé (très important pour partitionnement Kafka)

### ✔ flatMap

➡ explose un message en plusieurs

### ✔ merge

➡ fusionne plusieurs flux

### ✔ branch

➡ route les messages dans plusieurs flux

---

## 🔹 3. Vision terrain (très important)

Dans un vrai système Kafka :

* click → analytics
* purchase → billing / CRM
* login → sécurité

👉 Ces transformations permettent de construire :

* dashboards temps réel
* détection de fraude
* tracking utilisateur

---

# 🚀 CONCLUSION

Ce TP te permet de comprendre :

✔ le streaming data
✔ les pipelines Kafka
✔ la logique event-driven
✔ la base de Kafka Streams DSL

---


