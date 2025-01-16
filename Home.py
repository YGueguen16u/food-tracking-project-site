import streamlit as st

st.set_page_config(
    page_title="Food Analytics Dashboard",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Tableau de Bord d'Analyse Alimentaire")

st.markdown("""
## Bienvenue dans votre tableau de bord d'analyse alimentaire !

### Pages disponibles :

1. **🍽️ Analyse par Type d'Aliment**
   - Visualisez les proportions de macronutriments par type d'aliment
   - Comparez les profils nutritionnels
   - Analysez les statistiques détaillées

2. **👤 Analyse par Utilisateur**
   - Suivez l'évolution des apports nutritionnels par utilisateur
   - Visualisez les tendances et variations
   - Consultez les statistiques personnalisées

3. **📈 Analyse Quotidienne Globale**
   - Explorez les tendances globales
   - Analysez les variations quotidiennes
   - Découvrez les corrélations entre métriques

### Fonctionnalités communes :
- Choix entre les données DuckDB et Pandas
- Sélection flexible des métriques à analyser
- Visualisations interactives
- Statistiques détaillées
- Accès aux données brutes
""")

st.sidebar.success("Sélectionnez une page ci-dessus.")
