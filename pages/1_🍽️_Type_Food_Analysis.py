import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from AWS.s3.connect_s3 import S3Manager

st.set_page_config(page_title="Type Food Analysis", page_icon="🍽️", layout="wide")

# Fonction pour charger les données
@st.cache_data
def load_data(source):
    s3 = S3Manager()
    if source == "DuckDB":
        file_path = "transform/folder_6_parquet/folder_4_windows_function_filtered/user_food_proportion_duckdb.parquet"
    else:
        file_path = "transform/folder_6_parquet/folder_4_windows_function_filtered/user_food_proportion_pandas.parquet"
    
    temp_file = f"temp_{os.path.basename(file_path)}"
    try:
        if s3.download_file(file_path, temp_file):
            query = f"SELECT * FROM read_parquet('{temp_file}')"
            return duckdb.query(query).to_df()
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

st.title("🍽️ Analyse par Type d'Aliment")

# Sélection de la source de données
source = st.radio(
    "Choisir la source de données",
    ["DuckDB", "Pandas"],
    horizontal=True
)

# Chargement des données
df = load_data(source)

if df is not None:
    # Sélection de l'utilisateur
    users = sorted(df["user_id"].unique())
    selected_user = st.selectbox(
        "Sélectionner un utilisateur",
        users,
        help="Choisissez un utilisateur pour voir ses données"
    )
    
    # Filtrage par utilisateur
    df_user = df[df["user_id"] == selected_user]
    
    # Sélection des macronutriments
    st.subheader("Sélection des macronutriments")
    macros = {
        "Calories": "proportion_total_calories",
        "Lipides": "proportion_total_lipids",
        "Protéines": "proportion_total_protein",
        "Glucides": "proportion_total_carbs"
    }
    
    selected_macros = st.multiselect(
        "Choisir les macronutriments à analyser",
        list(macros.keys()),
        default=list(macros.keys())
    )
    
    if selected_macros:
        # Création de deux colonnes pour les visualisations
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Statistiques descriptives par type
            st.subheader("Statistiques par type d'aliment")
            
            # Calculer les statistiques pour chaque type d'aliment
            stats_df = df_user.groupby('Type').agg({
                'total_calories': ['mean', 'std', 'min', 'max'],
                'total_lipids': ['mean', 'std', 'min', 'max'],
                'total_protein': ['mean', 'std', 'min', 'max'],
                'total_carbs': ['mean', 'std', 'min', 'max']
            })
            
            # Aplatir les colonnes multi-index
            stats_df.columns = [f"{col[0].split('_')[1]} ({col[1].capitalize()})" 
                              for col in stats_df.columns]
            
            # Arrondir les valeurs
            stats_df = stats_df.round(2)
            
            # Afficher le tableau
            st.dataframe(stats_df, use_container_width=True)
            
            # Diagramme circulaire des proportions
            st.subheader("Répartition par type d'aliment")
            
            # Calculer les moyennes des proportions par type
            proportions_df = df_user.groupby('Type').agg({
                'proportion_total_calories': 'mean',
                'proportion_total_lipids': 'mean',
                'proportion_total_protein': 'mean',
                'proportion_total_carbs': 'mean'
            }).round(3)  # Plus de décimales pour plus de précision
            
            # Sélecteur pour le type de proportion
            prop_type = st.selectbox(
                "Choisir le type de proportion",
                ['Calories', 'Lipides', 'Protéines', 'Glucides'],
                index=0
            )
            
            # Mapping des noms vers les colonnes
            prop_mapping = {
                'Calories': 'proportion_total_calories',
                'Lipides': 'proportion_total_lipids',
                'Protéines': 'proportion_total_protein',
                'Glucides': 'proportion_total_carbs'
            }
            
            # Créer le diagramme circulaire
            fig_pie = go.Figure(data=[go.Pie(
                labels=proportions_df.index,
                values=proportions_df[prop_mapping[prop_type]] * 100,
                textinfo='label+percent',
                hovertemplate="Type: %{label}<br>Proportion: %{percent}<extra></extra>",
                textposition='auto',
                insidetextorientation='radial'
            )])
            
            fig_pie.update_layout(
                showlegend=True,
                height=500,
                title=f"Distribution des types d'aliments (par {prop_type.lower()})"
            )
            
            fig_pie.update_traces(
                textfont_size=12,
                marker=dict(line=dict(color='#000000', width=1))
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Tableau complet des proportions
            st.subheader("Tableau des proportions (%)")
            display_df = proportions_df * 100
            display_df.columns = ['Calories', 'Lipides', 'Protéines', 'Glucides']
            st.dataframe(
                display_df.round(2).sort_values('Calories', ascending=False),
                use_container_width=True
            )
        
        with col2:
            pass
        
        # Graphique en barres
        st.subheader("Répartition des macronutriments")
        df_plot = df_user.groupby("Type")[
            [macros[m] for m in selected_macros]
        ].mean().reset_index()
        
        fig_bar = px.bar(
            df_plot,
            x="Type",
            y=[macros[m] for m in selected_macros],
            title="Proportions par type d'aliment",
            barmode="group",
            labels={
                macros[m]: m for m in selected_macros
            }
        )
        
        fig_bar.update_layout(
            yaxis_title="Proportion (%)",
            xaxis_title="Type d'aliment",
            legend_title="Macronutriments"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Données brutes
        with st.expander("Voir les données brutes"):
            st.dataframe(
                df_user[["Type"] + [macros[m] for m in selected_macros]],
                use_container_width=True
            )
