"""
Dashboard Streamlit — AfriMarket
Formation : Maîtrisez l'Analyse des Données avec Claude

Lancement : streamlit run app.py
Prérequis : afrimarket_dataset_senior.csv dans le même dossier
"""

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="AfriMarket — Dashboard Stratégique", layout="wide", page_icon="📊")

COULEUR_PRINCIPALE = "#D97757"
COULEUR_SECONDAIRE = "#4A5568"
COULEUR_FONCEE = "#121821"
sns.set_style("whitegrid")


# ----------------------------------------------------------------------------
# CHARGEMENT & NETTOYAGE (identique au notebook, mis en cache)
# ----------------------------------------------------------------------------
@st.cache_data
def charger_et_nettoyer():
    df = pd.read_csv("afrimarket_dataset_senior.csv")
    df_clean = df.copy()

    df_clean = df_clean.drop_duplicates()
    df_clean = df_clean.drop_duplicates(subset=["id_commande"], keep="first")

    df_clean["date_commande"] = pd.to_datetime(df_clean["date_commande"], format="%Y-%m-%d", errors="coerce")

    df_clean["ville"] = df_clean["ville"].str.strip().replace({"Kinshassa": "Kinshasa"})
    df_clean["categorie"] = df_clean["categorie"].str.strip().replace({"electronique": "Électronique"})
    df_clean["statut_commande"] = df_clean["statut_commande"].str.strip().replace({"retournée": "Retournée"})

    df_clean.loc[df_clean["remise"] < 0, "remise"] = 0

    median_prix_cat = df_clean[df_clean["prix_unitaire"] > 0].groupby("categorie")["prix_unitaire"].median()
    df_clean.loc[df_clean["prix_unitaire"] <= 0, "prix_unitaire"] = (
        df_clean.loc[df_clean["prix_unitaire"] <= 0, "categorie"].map(median_prix_cat)
    )

    df_clean = df_clean[df_clean["quantite"] > 0]
    df_clean = df_clean.dropna(subset=["date_commande"]).reset_index(drop=True)

    # Feature engineering
    df_clean["chiffre_affaires"] = df_clean["prix_unitaire"] * df_clean["quantite"] * (1 - df_clean["remise"])
    df_clean["marge_brute"] = df_clean["chiffre_affaires"] * 0.42
    df_clean["profit_net"] = df_clean["marge_brute"] - df_clean["cout_marketing"] - df_clean["cout_livraison"]
    df_clean["mois"] = df_clean["date_commande"].dt.to_period("M").astype(str)
    df_clean["indicateur_retour"] = (df_clean["statut_commande"] == "Retournée").astype(int)
    df_clean["nombre_commandes_par_client"] = df_clean.groupby("id_client")["id_commande"].transform("count")
    df_clean["valeur_vie_client"] = df_clean.groupby("id_client")["chiffre_affaires"].transform("sum")

    return df_clean


df = charger_et_nettoyer()

# ----------------------------------------------------------------------------
# SIDEBAR - FILTRES
# ----------------------------------------------------------------------------
st.sidebar.markdown("## 🎛️ Filtres")

villes_dispo = sorted(df["ville"].unique())
villes_sel = st.sidebar.multiselect("Ville", villes_dispo, default=villes_dispo)

cat_dispo = sorted(df["categorie"].unique())
cat_sel = st.sidebar.multiselect("Catégorie", cat_dispo, default=cat_dispo)

canaux_dispo = sorted(df["canal_marketing"].unique())
canaux_sel = st.sidebar.multiselect("Canal marketing", canaux_dispo, default=canaux_dispo)

paiement_dispo = sorted(df["methode_paiement"].unique())
paiement_sel = st.sidebar.multiselect("Méthode de paiement", paiement_dispo, default=paiement_dispo)

mois_dispo = sorted(df["mois"].unique())
mois_sel = st.sidebar.select_slider(
    "Période (mois)", options=mois_dispo, value=(mois_dispo[0], mois_dispo[-1])
)

statuts_dispo = sorted(df["statut_commande"].unique())
statuts_sel = st.sidebar.multiselect("Statut", statuts_dispo, default=statuts_dispo)

st.sidebar.markdown("---")
st.sidebar.caption("Formation « Maîtrisez l'Analyse des Données avec Claude » — formations4data")

df_f = df[
    df["ville"].isin(villes_sel)
    & df["categorie"].isin(cat_sel)
    & df["canal_marketing"].isin(canaux_sel)
    & df["methode_paiement"].isin(paiement_sel)
    & df["statut_commande"].isin(statuts_sel)
    & (df["mois"] >= mois_sel[0])
    & (df["mois"] <= mois_sel[1])
]

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div style="background-color:{COULEUR_FONCEE};padding:24px;border-radius:10px;margin-bottom:20px;">
        <h1 style="color:white;margin:0;">📊 AfriMarket — Dashboard Stratégique</h1>
        <p style="color:#cbd5e0;margin:6px 0 0 0;">Analyse e-commerce panafricaine · 6 mois d'activité</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_f.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
ca_total = df_f["chiffre_affaires"].sum()
profit_total = df_f["profit_net"].sum()
panier_moyen = df_f["chiffre_affaires"].mean()
taux_annulation = (df_f["statut_commande"] == "Annulée").mean()
taux_retour = (df_f["statut_commande"] == "Retournée").mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 CA total", f"{ca_total:,.0f} $")
k2.metric("📈 Profit net estimé", f"{profit_total:,.0f} $")
k3.metric("🛒 Panier moyen", f"{panier_moyen:,.1f} $")
k4.metric("❌ Taux d'annulation", f"{taux_annulation:.1%}")
k5.metric("↩️ Taux de retour", f"{taux_retour:.1%}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🏷 Catégories", "🌍 Géographie", "📢 Marketing", "👥 Clients", "📄 Données"]
)

# ----------------------------------------------------------------------------
# TAB 1 - CATEGORIES
# ----------------------------------------------------------------------------
with tab1:
    col1, col2 = st.columns(2)

    cat_perf = df_f.groupby("categorie").agg(
        ca=("chiffre_affaires", "sum"),
        marge=("marge_brute", "sum"),
        taux_retour=("indicateur_retour", "mean"),
    ).sort_values("ca", ascending=False)

    with col1:
        st.subheader("CA par catégorie")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(y=cat_perf.index, x=cat_perf["ca"], color=COULEUR_PRINCIPALE, ax=ax)
        ax.set_xlabel("CA ($)")
        ax.set_ylabel("")
        st.pyplot(fig)

    with col2:
        st.subheader("Taux de retour par catégorie")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(y=cat_perf.index, x=cat_perf["taux_retour"] * 100, color=COULEUR_SECONDAIRE, ax=ax)
        ax.set_xlabel("Taux de retour (%)")
        ax.set_ylabel("")
        st.pyplot(fig)

    st.subheader("Évolution mensuelle du CA par catégorie")
    evo_cat = df_f.groupby(["mois", "categorie"])["chiffre_affaires"].sum().unstack()
    fig, ax = plt.subplots(figsize=(11, 4))
    evo_cat.plot(kind="line", marker="o", ax=ax)
    ax.set_ylabel("CA ($)")
    ax.legend(title="Catégorie", bbox_to_anchor=(1.02, 1), loc="upper left")
    st.pyplot(fig)

    st.dataframe(cat_perf.style.format({"ca": "{:,.0f}", "marge": "{:,.0f}", "taux_retour": "{:.1%}"}))

# ----------------------------------------------------------------------------
# TAB 2 - GEOGRAPHIE
# ----------------------------------------------------------------------------
with tab2:
    geo_perf = df_f.groupby("ville").agg(
        ca=("chiffre_affaires", "sum"),
        profit=("profit_net", "sum"),
        taux_annulation=("statut_commande", lambda s: (s == "Annulée").mean()),
    ).sort_values("ca", ascending=False)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("CA par ville")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(y=geo_perf.index, x=geo_perf["ca"], color=COULEUR_PRINCIPALE, ax=ax)
        ax.set_xlabel("CA ($)")
        ax.set_ylabel("")
        st.pyplot(fig)

    with col2:
        st.subheader("Détail")
        st.dataframe(geo_perf.style.format({"ca": "{:,.0f}", "profit": "{:,.0f}", "taux_annulation": "{:.1%}"}))

    max_annulation = geo_perf["taux_annulation"].max()
    if max_annulation > 0.05:
        ville_alerte = geo_perf["taux_annulation"].idxmax()
        st.error(
            f"🚨 **Anomalie détectée** : {ville_alerte} affiche un taux d'annulation de "
            f"{max_annulation:.1%}, nettement supérieur aux autres villes. À investiguer en priorité "
            "(logistique, paiement à la livraison, concurrence locale)."
        )

    st.subheader("Taux d'annulation par ville")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(y=geo_perf.index, x=geo_perf["taux_annulation"] * 100, color=COULEUR_SECONDAIRE, ax=ax)
    ax.set_xlabel("Taux d'annulation (%)")
    ax.set_ylabel("")
    st.pyplot(fig)

    st.subheader("Heatmap — CA par ville et catégorie")
    pivot = df_f.pivot_table(values="chiffre_affaires", index="ville", columns="categorie", aggfunc="sum", fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(pivot, annot=True, fmt=",.0f", cmap="Oranges", ax=ax, cbar_kws={"label": "CA ($)"})
    st.pyplot(fig)

# ----------------------------------------------------------------------------
# TAB 3 - MARKETING
# ----------------------------------------------------------------------------
with tab3:
    mkt_perf = df_f.groupby("canal_marketing").agg(
        ca=("chiffre_affaires", "sum"),
        cout=("cout_marketing", "sum"),
    ).reset_index()
    mkt_perf["roi"] = (mkt_perf["ca"] - mkt_perf["cout"]) / mkt_perf["cout"].replace(0, np.nan)

    retention = df_f.groupby(["canal_marketing", "id_client"])["id_commande"].count().reset_index()
    retention["recurrent"] = retention["id_commande"] > 1
    taux_retention = retention.groupby("canal_marketing")["recurrent"].mean()
    mkt_perf["taux_retention"] = mkt_perf["canal_marketing"].map(taux_retention)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("CA par canal")
        mkt_sorted = mkt_perf.sort_values("ca", ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(y=mkt_sorted["canal_marketing"], x=mkt_sorted["ca"], color=COULEUR_PRINCIPALE, ax=ax)
        ax.set_xlabel("CA ($)")
        ax.set_ylabel("")
        st.pyplot(fig)

    with col2:
        st.subheader("ROI par canal")
        mkt_roi = mkt_perf.dropna(subset=["roi"]).sort_values("roi", ascending=False)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(y=mkt_roi["canal_marketing"], x=mkt_roi["roi"], color=COULEUR_SECONDAIRE, ax=ax)
        ax.set_xlabel("ROI")
        ax.set_ylabel("")
        st.pyplot(fig)

    st.info(
        "⚠️ Un canal à faible coût peut afficher un ROI élevé sur un volume de CA plus faible. "
        "Toujours lire le ROI avec le CA absolu à côté avant de réallouer un budget."
    )
    st.dataframe(mkt_perf.style.format({"ca": "{:,.0f}", "cout": "{:,.0f}", "roi": "{:.1f}", "taux_retention": "{:.1%}"}))

    st.subheader("Bonus — méthode de paiement")
    pay_perf = df_f.groupby("methode_paiement").agg(
        ca=("chiffre_affaires", "sum"),
        taux_annulation=("statut_commande", lambda s: (s == "Annulée").mean()),
        taux_retour=("indicateur_retour", "mean"),
    ).sort_values("ca", ascending=False)
    st.dataframe(pay_perf.style.format({"ca": "{:,.0f}", "taux_annulation": "{:.1%}", "taux_retour": "{:.1%}"}))

# ----------------------------------------------------------------------------
# TAB 4 - CLIENTS
# ----------------------------------------------------------------------------
with tab4:
    n_clients_total = df_f["id_client"].nunique()
    pct_recurrents = (df_f.groupby("id_client")["id_commande"].count() > 1).mean()

    c1, c2 = st.columns(2)
    c1.metric("👥 Clients uniques", f"{n_clients_total:,.0f}")
    c2.metric("🔁 % clients récurrents", f"{pct_recurrents:.1%}")

    clv_par_client = df_f.groupby("id_client")["chiffre_affaires"].sum().sort_values(ascending=False)
    cumul_pct = clv_par_client.cumsum() / clv_par_client.sum()
    pct_clients_80 = (cumul_pct <= 0.8).sum() / len(cumul_pct) if len(cumul_pct) else 0

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Courbe de Pareto — {pct_clients_80:.1%} des clients génèrent 80% du CA")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(range(1, len(cumul_pct) + 1), cumul_pct.values * 100, color=COULEUR_PRINCIPALE, linewidth=2)
        ax.axhline(80, color="grey", linestyle="--")
        ax.set_xlabel("Nombre de clients (triés par CA)")
        ax.set_ylabel("% cumulé du CA")
        st.pyplot(fig)

    with col2:
        st.subheader("Segmentation clients")
        nb_commandes = df_f.groupby("id_client")["id_commande"].count()

        def segmenter(n):
            if n == 1:
                return "Occasionnel"
            elif n <= 4:
                return "Régulier"
            return "VIP"

        segments = nb_commandes.apply(segmenter)
        fig, ax = plt.subplots(figsize=(6, 4))
        segments.value_counts().reindex(["Occasionnel", "Régulier", "VIP"]).plot(
            kind="bar", color=[COULEUR_PRINCIPALE, COULEUR_SECONDAIRE, COULEUR_FONCEE], ax=ax
        )
        ax.set_ylabel("Nombre de clients")
        plt.xticks(rotation=0)
        st.pyplot(fig)

    st.subheader("Top 10 clients (valeur vie client)")
    st.dataframe(clv_par_client.head(10).reset_index().rename(
        columns={"id_client": "Client", "chiffre_affaires": "CLV ($)"}
    ).style.format({"CLV ($)": "{:,.0f}"}))

# ----------------------------------------------------------------------------
# TAB 5 - DONNEES BRUTES / EXPORT
# ----------------------------------------------------------------------------
with tab5:
    st.subheader("Données filtrées (df_clean)")
    st.dataframe(df_f)
    st.caption(f"{len(df_f):,} lignes après filtres et nettoyage (sur {len(df):,} lignes propres au total)")
    st.download_button(
        "⬇️ Télécharger les données filtrées (CSV)",
        df_f.to_csv(index=False).encode("utf-8"),
        "afrimarket_filtre.csv",
        "text/csv",
    )
