

# 🧪 TP : Concepts de base du streaming Kafka

## 🎯 Objectif du TP

Dans ce TP, tu vas apprendre les concepts fondamentaux du streaming :

* 🔹 Event stream (flux d’événements)
* 🔹 Timestamp (temps des événements)
* 🔹 Windowing (fenêtrage simple)
* 🔹 Count (compter les événements)
* 🔹 Key grouping (regroupement par utilisateur)
* 🔹 Real-time aggregation (agrégation temps réel)

👉 Tout est simulé en Python pour comprendre avant d’aller vers **Apache Kafka**

---

# 📦 1. Dataset (flux d’événements avec temps)

```python id="tp_stream_01"
# Chaque événement contient : (user, event, timestamp)
stream = [
    ("user1", "click", 1),
    ("user2", "click", 2),
    ("user1", "click", 3),
    ("user3", "purchase", 4),
    ("user1", "click", 5),
    ("user2", "purchase", 6),
    ("user3", "click", 7)
]
```

---

# 🔹 2. GROUP BY KEY (regrouper par utilisateur)

```python id="tp_stream_02"
from collections import defaultdict

grouped = defaultdict(list)

for user, event, ts in stream:
    grouped[user].append((event, ts))

print("\n=== GROUP BY USER ===")
for k, v in grouped.items():
    print(k, ":", v)
```

### 🖥️ Console attendue

```
user1 : [('click', 1), ('click', 3), ('click', 5)]
user2 : [('click', 2), ('purchase', 6)]
user3 : [('purchase', 4), ('click', 7)]
```

---

# 🔹 3. COUNT EVENTS (compter les événements par user)

```python id="tp_stream_03"
count_by_user = defaultdict(int)

for user, event, ts in stream:
    count_by_user[user] += 1

print("\n=== COUNT EVENTS PER USER ===")
print(dict(count_by_user))
```

### 🖥️ Console attendue

```
{'user1': 3, 'user2': 2, 'user3': 2}
```

---

# 🔹 4. FILTER REAL-TIME (filtrer uniquement clicks)

```python id="tp_stream_04"
clicks = []

for user, event, ts in stream:
    if event == "click":
        clicks.append((user, ts))

print("\n=== ONLY CLICKS ===")
print(clicks)
```

### 🖥️ Console attendue

```
[('user1', 1), ('user2', 2), ('user1', 3), ('user1', 5), ('user3', 7)]
```

---

# 🔹 5. SIMPLE WINDOWING (fenêtre de temps)

👉 On regroupe les événements par intervalle de 3 secondes

```python id="tp_stream_05"
window_size = 3

windows = defaultdict(list)

for user, event, ts in stream:
    window_id = ts // window_size
    windows[window_id].append((user, event, ts))

print("\n=== WINDOWING (3 seconds) ===")
for w, events in windows.items():
    print(f"Window {w}:", events)
```

### 🖥️ Console attendue

```
Window 0: [('user1','click',1), ('user2','click',2), ('user1','click',3)]
Window 1: [('user3','purchase',4), ('user1','click',5), ('user2','purchase',6)]
Window 2: [('user3','click',7)]
```

---

# 🔹 6. REAL-TIME AGGREGATION (click vs purchase)

```python id="tp_stream_06"
stats = {"click": 0, "purchase": 0}

for user, event, ts in stream:
    if event in stats:
        stats[event] += 1

print("\n=== REAL TIME AGGREGATION ===")
print(stats)
```

### 🖥️ Console attendue

```
{'click': 5, 'purchase': 2}
```

---

# 🔹 7. STREAM SIMULATION PIPELINE (tout ensemble)

```python id="tp_stream_07"
result = []

for user, event, ts in stream:
    # filtrage
    if event == "click":
        # transformation simple
        result.append(f"{user}-{event}-{ts}")

print("\n=== STREAM PIPELINE ===")
print(result)
```

### 🖥️ Console attendue

```
['user1-click-1', 'user2-click-2', 'user1-click-3', 'user1-click-5', 'user3-click-7']
```

---

# 🧠 EXPLICATION SIMPLE DES CONCEPTS

## 🔹 1. Stream (flux)

Un flux = une suite continue d’événements.

---

## 🔹 2. Windowing

👉 Découpe du flux en périodes de temps

Ex :

* Window 0 → [0–3 sec]
* Window 1 → [3–6 sec]

---

## 🔹 3. Aggregation

👉 Compter ou résumer les événements

Ex :

* combien de clicks ?
* combien d’achats ?

---

## 🔹 4. Key grouping

👉 Regrouper par utilisateur (ou device, ou service)

---

## 🔹 5. Streaming en temps réel

👉 Chaque événement est traité immédiatement

---

# 🚀 CONCLUSION

Ce TP t’a permis de comprendre les bases de :

✔ streaming data
✔ windowing
✔ aggregation
✔ event processing
✔ real-time analytics

👉 Ces concepts sont au cœur de **Apache Kafka**

---

