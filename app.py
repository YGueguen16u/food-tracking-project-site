import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
from datetime import datetime, timedelta
import sys
import os

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from AWS.s3.connect_s3 import S3Manager

# Configuration de la page
st.set_page_config(
    page_title="Food Analytics Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# Fonction pour charger les données parquet depuis S3
@st.cache_data
def load_parquet_data(s3_key):
    """
    Charge un fichier parquet depuis S3 en utilisant DuckDB
    """
    s3 = S3Manager()
    temp_file = f"temp_{os.path.basename(s3_key)}"
    try:
        if s3.download_file(s3_key, temp_file):
            query = f"SELECT * FROM read_parquet('{temp_file}')"
            return duckdb.query(query).to_df()
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier {s3_key}: {str(e)}")
        return None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# Chargement des données
@st.cache_data
def load_all_data():
    data = {
        "Proportions par type d'aliment (Pandas)": load_parquet_data("transform/folder_6_parquet/folder_4_windows_function_filtered/user_food_proportion_pandas.parquet"),
        "Proportions par type d'aliment (DuckDB)": load_parquet_data("transform/folder_6_parquet/folder_4_windows_function_filtered/user_food_proportion_duckdb.parquet"),
        "Évolution quotidienne (DuckDB)": load_parquet_data("transform/folder_6_parquet/folder_5_percentage_change_filtered/daily_percentage_change_duckdb.parquet"),
        "Évolution quotidienne (Pandas)": load_parquet_data("transform/folder_6_parquet/folder_5_percentage_change_filtered/daily_percentage_change_pandas.parquet"),
        "Évolution par utilisateur (DuckDB)": load_parquet_data("transform/folder_6_parquet/folder_5_percentage_change_filtered/user_daily_percentage_change_duckdb.parquet"),
        "Évolution par utilisateur (Pandas)": load_parquet_data("transform/folder_6_parquet/folder_5_percentage_change_filtered/user_daily_percentage_change_pandas.parquet")
    }
    return data

# Sidebar
st.sidebar.title("🔍 Filtres")

# Chargement des données
data = load_all_data()

# Sélection du dataset
dataset_name = st.sidebar.selectbox(
    "Choisir un dataset",
    list(data.keys())
)

if dataset_name and data[dataset_name] is not None:
    df = data[dataset_name]
    
    # Filtres spécifiques selon le type de dataset
    if "user" in dataset_name.lower():
        # Filtre par utilisateur
        users = sorted(df["user_id"].unique())
        selected_user = st.sidebar.selectbox(
            "Sélectionner un utilisateur", 
            users,
            help="Choisissez un utilisateur pour voir ses données spécifiques"
        )
        
        # Ajout d'un filtre de date pour les utilisateurs si la colonne date existe
        if "date" in df.columns:
            date_range = st.sidebar.date_input(
                "Sélectionner une période",
                value=(df["date"].min().date(), df["date"].max().date()),
                min_value=df["date"].min().date(),
                max_value=df["date"].max().date()
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
                df = df[mask]
        
        df_filtered = df[df["user_id"] == selected_user]
        
        if "proportion" in dataset_name.lower():
            # Visualisation des proportions par type d'aliment
            st.title(f"Analyse des proportions alimentaires - Utilisateur {selected_user}")
            
            # Sélection des types d'aliments
            all_food_types = sorted(df_filtered["Type"].unique())
            selected_types = st.multiselect(
                "Sélectionner les types d'aliments à afficher",
                options=all_food_types,
                default=all_food_types,
                help="Vous pouvez sélectionner plusieurs types d'aliments"
            )
            
            if selected_types:
                df_filtered = df_filtered[df_filtered["Type"].isin(selected_types)]
                
                # Graphique en barres des proportions
                fig = px.bar(
                    df_filtered,
                    x="Type",
                    y=["proportion_total_calories", "proportion_total_lipids", 
                       "proportion_total_protein", "proportion_total_carbs"],
                    title="Proportions par type d'aliment",
                    barmode="group",
                    labels={
                        "proportion_total_calories": "Calories",
                        "proportion_total_lipids": "Lipides",
                        "proportion_total_protein": "Protéines",
                        "proportion_total_carbs": "Glucides",
                        "Type": "Type d'aliment",
                        "value": "Proportion (%)"
                    }
                )
                fig.update_layout(
                    yaxis_title="Proportion (%)",
                    legend_title="Nutriments"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Veuillez sélectionner au moins un type d'aliment")
                
        else:
            # Évolution temporelle par utilisateur
            st.title(f"Évolution temporelle - Utilisateur {selected_user}")
            
            # Graphique des moyennes mobiles
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_filtered["date"],
                y=df_filtered["rolling_avg_total_calories"],
                name="Calories (moyenne mobile)",
                line=dict(color="blue")
            ))
            fig.add_trace(go.Scatter(
                x=df_filtered["date"],
                y=df_filtered["total_calories"],
                name="Calories (valeur journalière)",
                line=dict(color="red", dash="dash")
            ))
            fig.update_layout(title="Évolution des calories")
            st.plotly_chart(fig, use_container_width=True)
            
    else:
        # Visualisation des données globales
        st.title("Analyse globale")
        
        # Vérifier si la colonne date existe avant d'ajouter le filtre de date
        if "date" in df.columns:
            # Sélection de la période
            date_range = st.sidebar.date_input(
                "Sélectionner une période",
                value=(df["date"].min().date(), df["date"].max().date()),
                min_value=df["date"].min().date(),
                max_value=df["date"].max().date()
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
                df_filtered = df[mask]
        else:
            df_filtered = df
            
        # Graphique des tendances globales
        if "date" in df.columns:
            fig = go.Figure()
            metrics = ["total_calories", "total_lipids", "total_protein", "total_carbs"]
            colors = ["blue", "red", "green", "purple"]
            
            for metric, color in zip(metrics, colors):
                if metric in df_filtered.columns:
                    fig.add_trace(go.Scatter(
                        x=df_filtered["date"],
                        y=df_filtered[metric],
                        name=metric.replace("total_", "").title(),
                        line=dict(color=color)
                    ))
            
            fig.update_layout(title="Évolution des métriques nutritionnelles")
            st.plotly_chart(fig, use_container_width=True)
            
        # Affichage des statistiques
        st.subheader("Statistiques descriptives")
        metrics = [col for col in ["total_calories", "total_lipids", "total_protein", "total_carbs"] 
                  if col in df_filtered.columns]
        if metrics:
            st.dataframe(df_filtered[metrics].describe())
    
    # Affichage des données brutes
    if st.checkbox("Afficher les données brutes"):
        st.dataframe(df_filtered)
