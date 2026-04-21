package com.kafka.lab;

// ============================================================
//  Modèle de données : Commande e-commerce
//
//  Cette classe représente une commande qui sera sérialisée
//  en JSON et envoyée dans Kafka via le Producer.
//
//  Jackson @JsonProperty : nécessaire pour la sérialisation
//  Le constructeur sans arguments est requis par Jackson
// ============================================================

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.UUID;

public class Commande {

    // ── Champs de la commande ────────────────────────────────────────────────

    @JsonProperty("id")
    private String id;

    @JsonProperty("client")
    private String client;

    @JsonProperty("produit")
    private String produit;

    @JsonProperty("quantite")
    private int quantite;

    @JsonProperty("montant")
    private double montant;

    @JsonProperty("statut")
    private String statut;

    @JsonProperty("timestamp")
    private String timestamp;

    // ── Constructeur sans args — requis par Jackson ──────────────────────────
    public Commande() {}

    // ── Constructeur complet ─────────────────────────────────────────────────
    public Commande(String client, String produit, int quantite, double montant) {
        // UUID aléatoire comme identifiant unique
        this.id        = UUID.randomUUID().toString().substring(0, 8);
        this.client    = client;
        this.produit   = produit;
        this.quantite  = quantite;
        this.montant   = montant;
        this.statut    = "EN_ATTENTE";
        // ISO 8601 : format standard pour les timestamps
        this.timestamp = Instant.now().toString();
    }

    // ── Getters (Jackson en a besoin pour la sérialisation) ─────────────────
    public String getId()        { return id; }
    public String getClient()    { return client; }
    public String getProduit()   { return produit; }
    public int    getQuantite()  { return quantite; }
    public double getMontant()   { return montant; }
    public String getStatut()    { return statut; }
    public String getTimestamp() { return timestamp; }

    // Setters (nécessaires pour la désérialisation)
    public void setId(String id)              { this.id = id; }
    public void setClient(String client)      { this.client = client; }
    public void setProduit(String produit)    { this.produit = produit; }
    public void setQuantite(int quantite)     { this.quantite = quantite; }
    public void setMontant(double montant)    { this.montant = montant; }
    public void setStatut(String statut)      { this.statut = statut; }
    public void setTimestamp(String ts)       { this.timestamp = ts; }

    @Override
    public String toString() {
        return String.format("Commande{id='%s', client='%s', produit='%s', quantite=%d, montant=%.2f€, statut='%s'}",
                id, client, produit, quantite, montant, statut);
    }
}
