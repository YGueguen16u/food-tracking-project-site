import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from AWS.s3.connect_s3 import S3Manager

st.set_page_config(page_title="User Analysis", page_icon="👤", layout="wide")

# Fonction pour charger les données
@st.cache_data
def load_data(source):
    s3 = S3Manager()
    if source == "DuckDB":
        file_path = "transform/folder_6_parquet/folder_5_percentage_change_filtered/user_daily_percentage_change_duckdb.parquet"
    else:
        file_path = "transform/folder_6_parquet/folder_5_percentage_change_filtered/user_daily_percentage_change_pandas.parquet"
    
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

st.title("👤 Analyse par Utilisateur")

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
    
    # Sélection des métriques
    metrics = {
        "Calories": "total_calories",
        "Lipides": "total_lipids",
        "Protéines": "total_protein",
        "Glucides": "total_carbs"
    }
    
    selected_metrics = st.multiselect(
        "Choisir les métriques à analyser",
        list(metrics.keys()),
        default=list(metrics.keys())
    )
    
    if selected_metrics:
        # Période d'analyse
        date_range = st.date_input(
            "Sélectionner une période",
            value=(df_user["date"].min().date(), df_user["date"].max().date()),
            min_value=df_user["date"].min().date(),
            max_value=df_user["date"].max().date()
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df_user["date"].dt.date >= start_date) & (df_user["date"].dt.date <= end_date)
            df_filtered = df_user[mask]
            
            # Évolution temporelle
            st.subheader("Évolution temporelle")
            
            # Graphiques par macronutriment
            st.subheader("Évolution par macronutriment")
            
            for metric in selected_metrics:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_filtered["date"],
                    y=df_filtered[metrics[metric]],
                    mode="lines+markers",
                    name=metric,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
                
                # Ajouter une moyenne mobile sur 7 jours
                rolling_mean = df_filtered[metrics[metric]].rolling(window=7).mean()
                fig.add_trace(go.Scatter(
                    x=df_filtered["date"],
                    y=rolling_mean,
                    mode="lines",
                    name=f"Moyenne mobile (7j)",
                    line=dict(width=2, dash="dash")
                ))
                
                fig.update_layout(
                    title=f"Évolution de {metric}",
                    xaxis_title="Date",
                    yaxis_title=f"{metric}",
                    showlegend=True,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques descriptives
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Statistiques journalières")
                daily_stats = df_filtered[
                    [metrics[m] for m in selected_metrics]
                ].describe().round(2)
                daily_stats.index = ['Nombre', 'Moyenne', 'Écart-type', 'Min', '25%', '50%', '75%', 'Max']
                daily_stats.columns = selected_metrics
                st.dataframe(daily_stats, use_container_width=True)
            
            with col2:
                st.subheader("Variations quotidiennes")
                # Calculer les variations si elles n'existent pas
                pct_changes = {}
                for metric in selected_metrics:
                    col_name = metrics[metric]
                    pct_changes[f"{metric} (%)"] = df_filtered[col_name].pct_change() * 100
                
                pct_df = pd.DataFrame(pct_changes)
                pct_stats = pct_df.describe().round(2)
                st.dataframe(pct_stats, use_container_width=True)
            
            # Données brutes
            with st.expander("Voir les données brutes"):
                display_cols = ["date"] + [metrics[m] for m in selected_metrics]
                df_display = df_filtered[display_cols].copy()
                
                # Ajouter les variations calculées
                for metric in selected_metrics:
                    df_display[f"{metric} variation (%)"] = df_display[metrics[metric]].pct_change() * 100
                
                st.dataframe(df_display.sort_values("date"), use_container_width=True)
