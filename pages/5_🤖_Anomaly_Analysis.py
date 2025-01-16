import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import numpy as np
import duckdb
import sys
import os
import tempfile

# Ajouter le chemin racine au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from aws_s3.connect_s3 import S3Manager

st.set_page_config(page_title="Détection d'Anomalies Alimentaires", page_icon="🔍", layout="wide")

# Fonction pour charger les données depuis S3
@st.cache_data
def load_data_from_s3(file_path):
    """Charge un fichier depuis S3"""
    s3 = S3Manager()
    temp_file = tempfile.NamedTemporaryFile(suffix=os.path.basename(file_path))
    try:
        s3.download_file(file_path, temp_file.name)
        return temp_file
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier {file_path}: {str(e)}")
        return None

@st.cache_data
def load_all_ai_results():
    """Charge tous les résultats des modèles d'IA depuis S3"""
    # Créer un dossier temporaire
    temp_dir = tempfile.mkdtemp()
    s3 = S3Manager()
    
    try:
        # Anomaly detection results
        predictions_key = "AI/anomaly_detection/results/anomalies_detected.xlsx"
        temp_predictions = os.path.join(temp_dir, "predictions.xlsx")
        s3.download_file(predictions_key, temp_predictions)
        anomaly_data = pd.read_excel(temp_predictions)
        
        stats_key = "AI/anomaly_detection/results/model_statistics.json"
        temp_stats = os.path.join(temp_dir, "stats.json")
        s3.download_file(stats_key, temp_stats)
        with open(temp_stats, 'r', encoding='utf-8') as f:
            anomaly_analysis = json.load(f)
        
        return {
            'anomalies': {
                'data': anomaly_data,
                'analysis': anomaly_analysis
            }
        }
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des résultats : {str(e)}")
        return None
        
    finally:
        # Nettoyage : supprimer les fichiers temporaires
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def display_model_metrics(results):
    """Affiche les métriques principales des modèles"""
    st.subheader("📊 Métriques des Modèles")
    
    st.write("""
    Cette section présente les indicateurs clés de la détection d'anomalies. Le taux d'anomalies 
    indique le pourcentage de repas considérés comme anormaux, tandis que le score moyen d'anomalie 
    reflète l'intensité moyenne des anomalies détectées (plus le score est élevé, plus l'anomalie est marquée).
    """)
    
    # Métriques de détection d'anomalies
    st.write("### 🔍 Détection d'Anomalies")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Taux d'anomalies",
            f"{results['anomalies']['analysis']['general_statistics']['anomaly_rate']}%"
        )
    with col2:
        st.metric(
            "Score moyen d'anomalie",
            f"{results['anomalies']['analysis']['anomaly_statistics']['mean_anomaly_score']:.3f}"
        )

def plot_temporal_patterns(results):
    """Affiche les patterns temporels des repas anormaux"""
    st.subheader("⏰ Distribution Temporelle des Anomalies")
    
    st.write("""
    Ce graphique montre la répartition des repas anormaux au fil de la journée. Les pics indiquent 
    les heures où les anomalies sont plus fréquentes, ce qui peut révéler des habitudes alimentaires 
    particulières ou des moments de la journée plus propices aux écarts alimentaires.
    """)
    
    # Préparer les données des anomalies
    anomaly_data = results['anomalies']['data']
    
    # Distribution par heure pour les anomalies
    anomalies = anomaly_data[anomaly_data['is_anomaly']]
    hour_dist = anomalies.groupby(
        pd.to_datetime(anomalies['heure']).dt.hour
    ).size()
    
    # Créer le graphique
    fig = go.Figure()
    
    # Ajouter la distribution des anomalies
    fig.add_trace(go.Bar(
        x=hour_dist.index,
        y=hour_dist.values,
        name='Anomalies',
        marker_color='red'
    ))
    
    fig.update_layout(
        title="Distribution horaire des repas anormaux",
        xaxis_title="Heure de la journée",
        yaxis_title="Nombre d'anomalies",
        hovermode='x unified',
        showlegend=True,
        xaxis=dict(tickmode='linear', tick0=0, dtick=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_nutritional_patterns(results):
    """Affiche les patterns nutritionnels des anomalies"""
    st.subheader("🥗 Profil Nutritionnel des Anomalies")
    
    st.write("""
    Cette visualisation montre les caractéristiques nutritionnelles moyennes des repas détectés comme 
    anormaux. Les barres représentent les moyennes pour chaque nutriment, et les lignes d'erreur 
    indiquent la variabilité (écart-type). Des valeurs très élevées ou très basses par rapport à 
    vos habitudes peuvent expliquer pourquoi ces repas ont été détectés comme anormaux.
    """)
    
    # Données des anomalies
    anomaly_stats = results['anomalies']['analysis']['nutrient_statistics']['anomalies']
    
    # Créer le graphique en barres
    nutrient_means = {
        'Calories': anomaly_stats['total_calories']['mean'],
        'Lipides': anomaly_stats['total_lipids']['mean'],
        'Glucides': anomaly_stats['total_carbs']['mean'],
        'Protéines': anomaly_stats['total_protein']['mean']
    }
    
    nutrient_stds = {
        'Calories': anomaly_stats['total_calories']['std'],
        'Lipides': anomaly_stats['total_lipids']['std'],
        'Glucides': anomaly_stats['total_carbs']['std'],
        'Protéines': anomaly_stats['total_protein']['std']
    }
    
    fig = go.Figure()
    
    # Ajouter les barres pour chaque nutriment
    for nutrient in nutrient_means.keys():
        fig.add_trace(go.Bar(
            name=nutrient,
            x=[nutrient],
            y=[nutrient_means[nutrient]],
            error_y=dict(
                type='data',
                array=[nutrient_stds[nutrient]],
                visible=True
            )
        ))
    
    fig.update_layout(
        title="Moyennes et écarts-types des nutriments dans les anomalies",
        yaxis_title="Quantité",
        showlegend=False,
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_anomaly_details(results):
    """Affiche les détails des anomalies détectées"""
    st.subheader("🔍 Analyse Détaillée des Anomalies")
    
    st.write("""
    Cette section permet d'explorer en détail les repas identifiés comme anormaux. Vous pouvez filtrer 
    les résultats par score d'anomalie et limiter le nombre de repas affichés. Le tableau montre les 
    détails nutritionnels de chaque repas anormal, avec un gradient de couleur indiquant l'intensité 
    de l'anomalie (plus la couleur est foncée, plus l'anomalie est marquée).
    
    Le graphique de dispersion met en relation les calories et le score d'anomalie, permettant 
    d'identifier si les anomalies sont principalement liées à la quantité de calories consommées.
    """)
    
    anomaly_data = results['anomalies']['data']
    anomalies = anomaly_data[anomaly_data['is_anomaly']].sort_values('anomaly_score')
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        min_score = st.slider(
            "Score d'anomalie minimum",
            float(anomalies['anomaly_score'].min()),
            float(anomalies['anomaly_score'].max()),
            float(anomalies['anomaly_score'].min())
        )
    with col2:
        max_items = st.slider(
            "Nombre d'anomalies à afficher",
            1, 50, 10
        )
    
    # Filtrer les anomalies
    filtered_anomalies = anomalies[
        anomalies['anomaly_score'] >= min_score
    ].head(max_items)
    
    # Afficher le tableau des anomalies
    st.write("#### Anomalies Détectées")
    st.dataframe(
        filtered_anomalies[[
            'date', 'heure', 'total_calories', 'total_lipids',
            'total_carbs', 'total_protein', 'anomaly_score'
        ]].style.background_gradient(subset=['anomaly_score'], cmap='Reds'),
        use_container_width=True
    )
    
    # Graphique des scores d'anomalie
    fig = px.scatter(
        filtered_anomalies,
        x='total_calories',
        y='anomaly_score',
        size='total_calories',
        color='anomaly_score',
        hover_data=[
            'date', 'heure', 'total_lipids', 'total_carbs', 'total_protein'
        ],
        title="Distribution des anomalies par calories et score"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🔍 Détection d'Anomalies Alimentaires")
    
    st.write("""
    Cette page analyse les repas qui s'écartent significativement de vos habitudes alimentaires. 
    Notre modèle de détection d'anomalies identifie les repas inhabituels en se basant sur plusieurs critères :
    - Le moment de la journée
    - La quantité de calories
    - La composition nutritionnelle (lipides, glucides, protéines)
    - Les écarts par rapport à vos moyennes personnelles
    
    Ces informations vous aident à prendre conscience de vos écarts alimentaires et à mieux comprendre 
    vos habitudes.
    """)
    
    try:
        # Charger les résultats
        results = load_all_ai_results()
        
        if results is not None:
            # Afficher les métriques principales
            display_model_metrics(results)
            
            # Afficher les patterns temporels
            plot_temporal_patterns(results)
            
            # Afficher les patterns nutritionnels
            plot_nutritional_patterns(results)
            
            # Afficher les détails des anomalies
            display_anomaly_details(results)
            
        else:
            st.error("Impossible de charger les données. Assurez-vous que le modèle de détection d'anomalies a été entraîné et que les résultats sont disponibles.")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {str(e)}")
        st.info("Assurez-vous que le modèle de détection d'anomalies a été entraîné et que les résultats sont disponibles.")

if __name__ == "__main__":
    main()
