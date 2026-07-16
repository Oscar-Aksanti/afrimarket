# 📊 Projet AfriMarket — Analyse de Données Python

Module pratique pour la formation **« Maîtrisez l'Analyse des Données avec Claude »**

## Contenu du dossier

| Fichier | Description |
|---|---|
| `afrimarket_dataset_senior.csv` | Dataset brut (6 mois, ~6600 lignes, défauts réalistes) |
| `AfriMarket_Analyse_Claude.ipynb` | Notebook complet : audit → cleaning → feature engineering → analyses → viz, avec encadrés "💡 Prompt Claude" à chaque étape |
| `app.py` | Dashboard interactif Streamlit |
| `Resume_Executif_AfriMarket.docx` | Résumé exécutif 1 page + 5 recommandations |
| `afrimarket_clean.csv` | Dataset nettoyé, généré par le notebook (à créer en exécutant le notebook une première fois) |

## Comment lancer le notebook

```bash
pip install pandas numpy matplotlib seaborn jupyter --break-system-packages
jupyter notebook AfriMarket_Analyse_Claude.ipynb
```

Exécute les cellules dans l'ordre (Kernel > Restart & Run All la première fois).

## Comment lancer le dashboard Streamlit

```bash
pip install streamlit pandas numpy matplotlib seaborn --break-system-packages
streamlit run app.py
```

Le dashboard nettoie et prépare les données lui-même (pas besoin d'exécuter le notebook avant) — il lit directement `afrimarket_dataset_senior.csv`.

## Pédagogie

Ce projet est pensé pour être suivi **avec Claude à côté**. Chaque étape clé du
notebook contient un encadré `💡 Prompt Claude` montrant le prompt exact à
copier-coller pour :
- comprendre le raisonnement derrière le code,
- demander une variante,
- ou faire challenger le code par Claude.

**Niveau visé :** Data Analyst junior/intermédiaire.

## Le dataset (données réelles fournies)

`afrimarket_dataset_senior.csv` contient 10 100 commandes sur 6 mois
(juillet–décembre 2025), avec 14 colonnes : `id_commande`, `date_commande`,
`id_client`, `ville`, `categorie`, `nom_produit`, `prix_unitaire`, `quantite`,
`remise`, `cout_livraison`, `methode_paiement`, `canal_marketing`,
`cout_marketing`, `statut_commande`.

Défauts réels identifiés lors de l'audit :
- 100 doublons exacts de commandes
- Ville mal orthographiée : `Kinshassa` → `Kinshasa`
- Catégorie en casse incohérente : `electronique` → `Électronique`
- Statut en casse incohérente : `retournée` → `Retournée`
- ~622 prix invalides (valeur sentinelle négative ~-50, indépendante de la catégorie → corrigés par la médiane de la catégorie, pas par `abs()`)
- ~600 remises négatives (valeur sentinelle -0.1 → remise est un **pourcentage**, pas un montant)
- ~600 commandes à quantité nulle (supprimées)

⚠️ **Point important pour l'analyse :** `remise` est un pourcentage (0 à 0.3),
donc `chiffre_affaires = prix_unitaire * quantite * (1 - remise)`, et non une
soustraction directe.

**🚨 Insight clé découvert dans l'analyse :** le taux d'annulation global est
bas (1,9 %), mais grimpe à ~13 % pour la seule ville de Douala — une anomalie
localisée à investiguer en priorité, à ne pas confondre avec un problème
structurel de toute l'entreprise. C'est un excellent exemple pédagogique pour
montrer qu'une moyenne globale peut masquer un signal fort.
