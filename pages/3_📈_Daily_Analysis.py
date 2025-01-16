import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import sys
import os
from scipy.stats import gaussian_kde
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from aws_s3.connect_s3 import S3Manager

st.set_page_config(page_title="Daily Analysis", page_icon="📈", layout="wide")

# Fonction pour charger les données
@st.cache_data
def load_data(source):
    s3 = S3Manager()
    if source == "DuckDB":
        file_path = "transform/folder_6_parquet/folder_5_percentage_change_filtered/daily_percentage_change_duckdb.parquet"
    else:
        file_path = "transform/folder_6_parquet/folder_5_percentage_change_filtered/daily_percentage_change_pandas.parquet"
    
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

st.title("📈 Analyse Quotidienne Globale")

# Sélection de la source de données
source = st.radio(
    "Choisir la source de données",
    ["DuckDB", "Pandas"],
    horizontal=True
)

# Chargement des données
df = load_data(source)

if df is not None:
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
            value=(df["date"].min().date(), df["date"].max().date()),
            min_value=df["date"].min().date(),
            max_value=df["date"].max().date()
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
            df_filtered = df[mask]
            
            # Évolution temporelle
            st.subheader("Évolution temporelle globale")
            
            # Graphique des tendances
            fig = go.Figure()
            
            for metric in selected_metrics:
                # Valeurs journalières
                fig.add_trace(go.Scatter(
                    x=df_filtered["date"],
                    y=df_filtered[metrics[metric]],
                    name=f"{metric} (journalier)",
                    line=dict(dash="dash")
                ))
                
                # Moyennes mobiles
                fig.add_trace(go.Scatter(
                    x=df_filtered["date"],
                    y=df_filtered[f"rolling_avg_{metrics[metric]}"],
                    name=f"{metric} (moyenne mobile)",
                    line=dict(width=3)
                ))
            
            fig.update_layout(
                title="Évolution des métriques nutritionnelles",
                xaxis_title="Date",
                yaxis_title="Valeur",
                legend_title="Métriques"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Graphiques par macronutriment
            st.subheader("Évolution par macronutriment")
            
            for metric in selected_metrics:
                # Créer deux colonnes pour le graphique et les statistiques
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = go.Figure()
                    
                    # Valeurs journalières
                    fig.add_trace(go.Scatter(
                        x=df_filtered["date"],
                        y=df_filtered[metrics[metric]],
                        mode="lines+markers",
                        name=metric,
                        line=dict(width=2),
                        marker=dict(size=6)
                    ))
                    
                    # Moyenne mobile sur 7 jours
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
                
                with col2:
                    # Statistiques pour ce macronutriment
                    st.markdown(f"**Statistiques - {metric}**")
                    stats = df_filtered[metrics[metric]].describe().round(2)
                    stats.index = ['Nombre', 'Moyenne', 'Écart-type', 'Min', '25%', '50%', '75%', 'Max']
                    st.dataframe(stats, use_container_width=True)
                    
                    # Variation quotidienne pour ce macronutriment
                    st.markdown(f"**Variations - {metric}**")
                    pct_change = df_filtered[metrics[metric]].pct_change() * 100
                    pct_stats = pct_change.describe().round(2)
                    st.dataframe(pct_stats, use_container_width=True)
            
            # Distribution des variations
            st.subheader("Distribution des variations quotidiennes")
            
            # Calculer les variations pour chaque métrique
            variations = {}
            for metric in selected_metrics:
                variations[metric] = df_filtered[metrics[metric]].pct_change() * 100
            
            # Violin plot pour toutes les métriques
            fig_violin = go.Figure()
            for metric in selected_metrics:
                fig_violin.add_trace(go.Violin(
                    y=variations[metric],
                    name=metric,
                    box_visible=True,
                    meanline_visible=True,
                    points="outliers"
                ))
            
            fig_violin.update_layout(
                title="Distribution des variations (Violin Plot)",
                yaxis_title="Variation (%)",
                showlegend=True,
                height=500,
                violinmode="overlay"
            )
            st.plotly_chart(fig_violin, use_container_width=True)
            
            # Histogrammes par métrique
            cols = st.columns(len(selected_metrics))
            for idx, metric in enumerate(selected_metrics):
                with cols[idx]:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=variations[metric],
                        name=metric,
                        nbinsx=30,
                        histnorm='probability density'
                    ))
                    
                    # Ajouter une courbe de densité
                    hist_data = variations[metric].dropna()
                    kde = gaussian_kde(hist_data)
                    x_range = np.linspace(hist_data.min(), hist_data.max(), 100)
                    fig_hist.add_trace(go.Scatter(
                        x=x_range,
                        y=kde(x_range),
                        name="Densité",
                        line=dict(color='red', width=2)
                    ))
                    
                    fig_hist.update_layout(
                        title=f"Distribution {metric}",
                        xaxis_title="Variation (%)",
                        yaxis_title="Densité",
                        showlegend=False,
                        height=400
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
            
            # Ajout de l'interprétation business
            st.markdown("""
            ### Comment lire ces graphiques ?

            Les distributions nous montrent comment varient les habitudes alimentaires au quotidien :

            - Une courbe fine et haute ? La personne mange à peu près pareil chaque jour
            - Une courbe étalée ? Les quantités changent beaucoup d'un jour à l'autre
            - Plusieurs pics ? Il y a différentes routines alimentaires selon les jours
            - Des points isolés ? Ce sont des jours particuliers (resto, fête...)

            ### À quoi ça sert concrètement ?

            **Pour personnaliser les conseils**
            On peut adapter nos recommandations selon que la personne a des habitudes fixes ou variables. Par exemple, proposer des alternatives plus variées à quelqu'un qui mange toujours la même chose.

            **Pour prévenir les excès**
            Quand on voit des variations importantes, on peut envoyer des alertes ou suggérer des ajustements. C'est utile pour garder un équilibre au quotidien.

            **Pour mesurer les progrès**
            En comparant les graphiques avant/après, on voit si les nouvelles habitudes se mettent en place. Ça permet aussi de voir si nos conseils sont vraiment utiles.

            **Pour mieux accompagner**
            Certaines personnes ont besoin de régularité, d'autres de flexibilité. Ces graphiques nous aident à proposer un suivi qui correspond vraiment aux besoins de chacun.
            """)
            
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
                st.subheader("Statistiques des variations")
                # Créer un DataFrame avec les variations calculées
                pct_changes = {}
                for metric in selected_metrics:
                    pct_changes[f"{metric} (%)"] = df_filtered[metrics[metric]].pct_change() * 100
                
                pct_df = pd.DataFrame(pct_changes)
                pct_stats = pct_df.describe().round(2)
                st.dataframe(pct_stats, use_container_width=True)
            
            # Corrélations
            st.subheader("Matrice de corrélation")
            corr_data = df_filtered[[metrics[m] for m in selected_metrics]].corr()
            
            fig_corr = px.imshow(
                corr_data,
                labels=dict(color="Corrélation"),
                x=selected_metrics,
                y=selected_metrics,
                color_continuous_scale="RdBu",
                aspect="auto"
            )
            
            fig_corr.update_layout(
                title="Corrélation entre les métriques"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Données brutes
            with st.expander("Voir les données brutes"):
                display_cols = ["date"] + [metrics[m] for m in selected_metrics]
                df_display = df_filtered[display_cols].copy()
                
                # Ajouter les variations calculées
                for metric in selected_metrics:
                    df_display[f"{metric} variation (%)"] = df_display[metrics[metric]].pct_change() * 100
                
                st.dataframe(df_display.sort_values("date"), use_container_width=True)
