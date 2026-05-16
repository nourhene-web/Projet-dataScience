import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Cafe Sales Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CSS PERSONNALISE
# ─────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F8F4F0; }
    .block-container { padding-top: 1rem; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #C0392B;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 13px; color: #666; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 26px; font-weight: 800; color: #2C3E50; margin-top: 4px; }
    .section-title {
        font-size: 20px; font-weight: 700; color: #2C3E50;
        border-bottom: 2px solid #C0392B; padding-bottom: 6px; margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CHARGEMENT ET NETTOYAGE DES DONNEES
# ─────────────────────────────────────────
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    df.replace(['ERROR', 'UNKNOWN'], np.nan, inplace=True)

    df['Quantity']         = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Price Per Unit']   = pd.to_numeric(df['Price Per Unit'], errors='coerce')
    df['Total Spent']      = pd.to_numeric(df['Total Spent'], errors='coerce')
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')

    df.drop_duplicates(inplace=True)

    for col in ['Quantity', 'Price Per Unit', 'Total Spent']:
        df[col].fillna(df[col].median(), inplace=True)

    for col in ['Item', 'Payment Method', 'Location']:
        df[col].fillna(df[col].mode().iloc[0], inplace=True)

    df.dropna(subset=['Transaction Date'], inplace=True)

    df.rename(columns={
        'Transaction ID'   : 'ID_Transaction',
        'Item'             : 'Produit',
        'Quantity'         : 'Quantite',
        'Price Per Unit'   : 'Prix_Unitaire',
        'Total Spent'      : 'Total_Depense',
        'Payment Method'   : 'Mode_Paiement',
        'Location'         : 'Lieu',
        'Transaction Date' : 'Date'
    }, inplace=True)

    df['Mois']         = df['Date'].dt.month
    df['Jour_Semaine'] = df['Date'].dt.dayofweek
    df['Nom_Jour']     = df['Date'].dt.day_name()

    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/hot-beverage.png", width=80)
    st.markdown("## ☕ Café Sales Dashboard")
    st.markdown("**DS2 – Promotion 1LIG**")
    st.markdown("---")

    uploaded_file = st.file_uploader("📂 Charger un fichier CSV", type=["csv"])

    if uploaded_file:
        df = load_data(uploaded_file)
        st.success(f"✅ {len(df):,} transactions chargées")
    else:
        st.info("Chargez votre fichier dirty_cafe_sales.csv")
        st.stop()

    st.markdown("---")
    st.markdown("### 🔍 Filtres")

    # PRODUITS
    all_produits = sorted(df['Produit'].dropna().astype(str).unique())
    produits_sel = st.multiselect("Produit", all_produits, default=all_produits)

    # PAIEMENTS
    df['Mode_Paiement'] = df['Mode_Paiement'].fillna('Unknown').astype(str)
    all_paiements = sorted(df['Mode_Paiement'].unique())
    paiements_sel = st.multiselect("Mode de paiement", all_paiements, default=all_paiements)

    # LIEUX
    df['Lieu'] = df['Lieu'].fillna('').astype(str)
    df = df[df['Lieu'].str.strip() != '']

    all_lieux = sorted(df['Lieu'].unique())
    lieux_sel = st.multiselect("Lieu de vente", all_lieux, default=all_lieux)

    # DEBUG (tu voulais garder print)
    print(df['Lieu'].apply(type).value_counts())
    print(df['Lieu'].unique())

    # MOIS
    mois_min, mois_max = int(df['Mois'].min()), int(df['Mois'].max())
    mois_range = st.slider("Période (mois)", mois_min, mois_max, (mois_min, mois_max))

    # MONTANT
    montant_min = float(df['Total_Depense'].min())
    montant_max = float(df['Total_Depense'].max())

    montant_range = st.slider(
        "Montant transaction (€)",
        montant_min, montant_max,
        (montant_min, montant_max)
    )

# ─────────────────────────────────────────
# FILTRES (CORRIGÉ)
# ─────────────────────────────────────────
mask = (
    df['Produit'].isin(produits_sel) &
    df['Mode_Paiement'].isin(paiements_sel) &
    df['Lieu'].isin(lieux_sel) &
    df['Mois'].between(mois_range[0], mois_range[1]) &
    df['Total_Depense'].between(montant_range[0], montant_range[1])
)

dff = df[mask].copy()

if len(dff) == 0:
    st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# ─────────────────────────────────────────
# TITRE
# ─────────────────────────────────────────
st.markdown("# ☕ Tableau de Bord des Ventes – Café 2023")
st.markdown(f"*Données filtrées : **{len(dff):,}** transactions sur {len(df):,} au total*")
st.markdown("---")

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Vue Globale", "🛒 Produits", "📅 Temporel", "🗂️ Données"])

# ─────────────────────────────────────────
# TAB 1
# ─────────────────────────────────────────
with tab1:

    st.markdown('<div class="section-title">Indicateurs Clés</div>', unsafe_allow_html=True)

    ca_total   = dff['Total_Depense'].sum()
    nb_trans   = len(dff)
    panier_moy = dff['Total_Depense'].mean()
    qte_moy    = dff['Quantite'].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CA Total", f"{ca_total:,.2f} €")
    col2.metric("Transactions", f"{nb_trans:,}")
    col3.metric("Panier Moyen", f"{panier_moy:.2f} €")
    col4.metric("Quantité Moy.", f"{qte_moy:.2f}")

# ─────────────────────────────────────────
# TAB 2
# ─────────────────────────────────────────
with tab2:

    st.markdown('<div class="section-title">Produits</div>', unsafe_allow_html=True)

    ca_prod = dff.groupby('Produit')['Total_Depense'].sum().sort_values()

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(ca_prod.index, ca_prod.values, color='skyblue')
    st.pyplot(fig)

# ─────────────────────────────────────────
# TAB 3
# ─────────────────────────────────────────
with tab3:

    st.markdown('<div class="section-title">Temporel</div>', unsafe_allow_html=True)

    ca_daily = dff.groupby('Date')['Total_Depense'].sum()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ca_daily.index, ca_daily.values)
    st.pyplot(fig)

# ─────────────────────────────────────────
# TAB 4
# ─────────────────────────────────────────
with tab4:

    st.markdown('<div class="section-title">Données</div>', unsafe_allow_html=True)

    st.dataframe(dff.head(500))