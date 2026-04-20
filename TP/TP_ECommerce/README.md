

# 🔥 TP COMPLET — SYSTÈME E-COMMERCE TEMPS RÉEL AVEC KAFKA + AKHQ

## (Commandes + Stock + Livraison + Notifications + Analyse)

---

# 🚀 1. CONTEXTE DU TP

Dans un système e-commerce moderne (Amazon-like), chaque action client devient un événement :

* 🛒 commande produit
* 📦 gestion stock
* 🚚 livraison
* 💳 paiement
* 📢 notification client
* 📊 analytics business

👉 Kafka sert de **colonne vertébrale du système e-commerce**.

---

# 🎯 2. OBJECTIF DU TP

À la fin de ce TP, tu sauras :

✔ construire un flux e-commerce complet
✔ gérer commandes en temps réel
✔ synchroniser stock automatiquement
✔ déclencher livraison
✔ envoyer notifications client
✔ analyser ventes en temps réel
✔ superviser avec AKHQ

---

# 🏗️ 3. ARCHITECTURE GLOBALE

```text id="ecom_arch"
                ┌────────────────────┐
                │  Web / Mobile App  │
                └─────────┬──────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ orders-topic     │
                 └──────┬───────────┘
                        │
     ┌──────────────────┼──────────────────┐
     ▼                  ▼                  ▼
Stock Service    Payment Service   Shipping Service
     │                  │                  │
     ▼                  ▼                  ▼
stock-topic     payment-topic     delivery-topic
                        │
                        ▼
              notification-topic
                        │
                        ▼
                analytics-topic
```

---

# 🧱 4. CRÉATION DES TOPICS

## 🎯 Objectif

Créer les flux e-commerce

```bash id="tp_ecom_topics"
kafka-topics.sh --create --topic orders --bootstrap-server localhost:9092 --partitions 3

kafka-topics.sh --create --topic stock --bootstrap-server localhost:9092 --partitions 3

kafka-topics.sh --create --topic payment --bootstrap-server localhost:9092 --partitions 3

kafka-topics.sh --create --topic delivery --bootstrap-server localhost:9092 --partitions 2

kafka-topics.sh --create --topic notifications --bootstrap-server localhost:9092 --partitions 2

kafka-topics.sh --create --topic analytics --bootstrap-server localhost:9092 --partitions 2
```

---

# 🛒 5. PRODUCER — COMMANDES CLIENTS

## 🎯 Objectif

Simuler achat client

```bash id="producer_orders"
kafka-console-producer.sh --topic orders --bootstrap-server localhost:9092
```

---

## ✍️ EXEMPLES

```json id="order_data"
{"orderId":"O001","user":"U1","product":"Laptop","qty":1,"price":1200}

{"orderId":"O002","user":"U2","product":"Phone","qty":2,"price":800}
```

---

## 🔍 INTERPRÉTATION

✔ chaque commande = événement
✔ déclenche tout le système

---

# 📦 6. STOCK SERVICE

## 🎯 Objectif

Mettre à jour stock automatiquement

---

## 💻 Consumer

```bash id="stock_consumer"
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092
```

---

## 💻 Producer stock update

```bash id="stock_update"
kafka-console-producer.sh --topic stock --bootstrap-server localhost:9092
```

---

## 📤 Exemple

```json id="stock_json"
{"product":"Laptop","stock":50}
{"product":"Phone","stock":120}
```

---

## 🔍 INTERPRÉTATION

✔ stock mis à jour automatiquement
✔ logique découplée

---

# 💳 7. PAYMENT SERVICE

## 🎯 Objectif

Simuler paiement

---

```bash id="payment_consumer"
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092
```

---

## 💻 Producer paiement

```bash id="payment_producer"
kafka-console-producer.sh --topic payment --bootstrap-server localhost:9092
```

---

## 📤 Exemple

```json id="payment_data"
{"orderId":"O001","status":"PAID","method":"CARD"}
{"orderId":"O002","status":"FAILED","method":"MOBILE_MONEY"}
```

---

## 🔍 INTERPRÉTATION

✔ validation paiement
✔ déclenche livraison si OK

---

# 🚚 8. SHIPPING SERVICE

## 🎯 Objectif

Gérer livraison

---

```bash id="shipping_consumer"
kafka-console-consumer.sh --topic payment --bootstrap-server localhost:9092
```

---

## 💻 Producer delivery

```bash id="delivery_producer"
kafka-console-producer.sh --topic delivery --bootstrap-server localhost:9092
```

---

## 📤 Exemple

```json id="delivery_json"
{"orderId":"O001","status":"SHIPPED","tracking":"TRK123"}
```

---

## 🔍 INTERPRÉTATION

✔ livraison déclenchée après paiement

---

# 📢 9. NOTIFICATION SERVICE

## 🎯 Objectif

Informer client

---

```bash id="notif_consumer"
kafka-console-consumer.sh --topic delivery --bootstrap-server localhost:9092
```

---

## 📤 Exemple

```json id="notif_json"
{"user":"U1","message":"Votre commande est expédiée"}
```

---

## 🔍 INTERPRÉTATION

✔ expérience client temps réel

---

# 📊 10. ANALYTICS SERVICE

## 🎯 Objectif

Analyse business

---

```bash id="analytics_consumer"
kafka-console-consumer.sh --topic orders --bootstrap-server localhost:9092
```

---

## 📤 Exemple

```json id="analytics_json"
{"product":"Laptop","sales":100}
{"product":"Phone","sales":250}
```

---

## 🔍 INTERPRÉTATION

✔ dashboard business temps réel
✔ décisions marketing

---

# 📊 11. AKHQ — SUPERVISION

## 🎯 Objectif

Observer tout le système

---

## 🌐 ACTION

```text id="akhq_url"
http://localhost:8080
```

---

## 👀 TU VOIS

* orders
* stock
* payment
* delivery
* notifications
* analytics

---

## 🔍 INTERPRÉTATION

✔ AKHQ = cockpit e-commerce

---

# 🔁 12. SCÉNARIO COMPLET

## 🛒 CAS NORMAL

```text id="flow_ok"
Client commande Laptop
```

Flux :

1. order créé
2. stock vérifié
3. paiement validé
4. livraison lancée
5. notification envoyée
6. analytics mis à jour

---

## ❌ CAS ÉCHEC PAIEMENT

```text id="flow_fail"
Payment FAILED
```

Flux :

* pas de livraison
* stock non modifié
* notification échec

---

# 🧠 13. CONCLUSION DU TP

Tu maîtrises maintenant :

✔ architecture e-commerce event-driven
✔ Kafka topics multiples
✔ microservices découplés
✔ traitement temps réel
✔ supervision AKHQ

---

# 🚀 14. POURQUOI CE TP EST IMPORTANT

👉 C’est EXACTEMENT ce que font :

* Amazon 🛒
* Alibaba 🌏
* Shopify 💳
* Jumia 🇨🇮

---

# 🔥 RÉSUMÉ FINAL

```text id="summary_ecom"
Kafka = moteur central des plateformes e-commerce modernes
```

---


