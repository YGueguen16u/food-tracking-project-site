import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from aws_s3.connect_s3 import S3Manager

st.set_page_config(page_title="Cluster Analysis", page_icon="🎯", layout="wide")

# Fonction pour charger les données des types d'aliments
@st.cache_data
def load_food_data():
    s3 = S3Manager()
    file_path = "transform/folder_6_parquet/folder_4_windows_function_filtered/user_food_proportion_duckdb.parquet"
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

# Fonction pour charger les données de clustering
@st.cache_data
def load_cluster_data():
    s3 = S3Manager()
    
    # Charger les résultats des clusters
    results_file = "AI/clustering/results/user_clusters.xlsx"
    temp_results = "temp_clusters.xlsx"
    
    # Charger l'analyse des clusters
    analysis_file = "AI/clustering/results/cluster_analysis.json"
    temp_analysis = "temp_analysis.json"
    
    try:
        # Charger les résultats
        if s3.download_file(results_file, temp_results):
            results_df = pd.read_excel(temp_results)
        else:
            return None, None
            
        # Charger l'analyse
        if s3.download_file(analysis_file, temp_analysis):
            with open(temp_analysis, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        else:
            return None, None
            
        return results_df, analysis_data
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {str(e)}")
        return None, None
    finally:
        if os.path.exists(temp_results):
            os.remove(temp_results)
        if os.path.exists(temp_analysis):
            os.remove(temp_analysis)

st.title("🎯 Analyse des Clusters")

# Chargement des données
results_df, cluster_analysis = load_cluster_data()
food_df = load_food_data()

if results_df is not None and cluster_analysis is not None and food_df is not None:
    # Fusionner les données de clustering avec les types d'aliments
    merged_df = pd.merge(results_df, food_df, on='user_id', how='left')
    
    # Afficher un résumé global
    st.header("Vue d'ensemble des clusters")
    
    # Créer deux colonnes
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Graphique à bulles des caractéristiques principales
        cluster_data = []
        for cluster_id, stats in cluster_analysis.items():
            cluster_num = int(cluster_id.split('_')[1])
            cluster_data.append({
                'cluster': cluster_num,
                'taille': stats['nombre_utilisateurs'],
                'repas_par_jour': stats['repas_par_jour'],
                'calories': stats['moyennes_nutriments']['calories'],
                'heure_principale': stats['heures_principales'][0] if stats['heures_principales'] else None
            })
        
        df_clusters = pd.DataFrame(cluster_data)
        
        fig_bubbles = go.Figure()
        
        fig_bubbles.add_trace(go.Scatter(
            x=df_clusters['repas_par_jour'],
            y=df_clusters['calories'],
            mode='markers',
            marker=dict(
                size=df_clusters['taille']*5,
                color=df_clusters['heure_principale'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Heure principale')
            ),
            text=[f"Cluster {c}<br>Utilisateurs: {t}<br>Repas/jour: {r:.1f}<br>Calories: {cal:.0f}<br>Heure: {h}h"
                  for c, t, r, cal, h in zip(df_clusters['cluster'],
                                           df_clusters['taille'],
                                           df_clusters['repas_par_jour'],
                                           df_clusters['calories'],
                                           df_clusters['heure_principale'])],
            hoverinfo='text'
        ))
        
        fig_bubbles.update_layout(
            title="Vue d'ensemble des clusters",
            xaxis_title="Nombre moyen de repas par jour",
            yaxis_title="Calories moyennes par repas",
            showlegend=False,
            height=500
        )
        
        st.plotly_chart(fig_bubbles, use_container_width=True)
        
    with col2:
        # Afficher les statistiques clés
        st.subheader("Statistiques clés")
        total_users = sum(stats['nombre_utilisateurs'] for stats in cluster_analysis.values())
        st.metric("Nombre total d'utilisateurs", total_users)
        
        n_clusters = len(cluster_analysis)
        st.metric("Nombre de clusters", n_clusters)
        
        avg_meals = sum(stats['repas_par_jour'] * stats['nombre_utilisateurs'] for stats in cluster_analysis.values()) / total_users
        st.metric("Moyenne globale repas/jour", f"{avg_meals:.1f}")
    
    # Analyse détaillée par cluster
    st.header("Analyse détaillée par cluster")
    
    # Sélection du cluster
    selected_cluster = st.selectbox(
        "Sélectionner un cluster pour plus de détails",
        sorted([int(k.split('_')[1]) for k in cluster_analysis.keys()])
    )
    
    cluster_key = f"cluster_{selected_cluster}"
    stats = cluster_analysis[cluster_key]
    
    # Créer trois colonnes pour les détails
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Informations générales")
        st.write(f"Nombre d'utilisateurs : {stats['nombre_utilisateurs']}")
        st.write(f"Repas par jour : {stats['repas_par_jour']:.1f}")
        st.write(f"Heures principales : {', '.join(map(str, stats['heures_principales']))}")
        
    with col2:
        st.subheader("Types d'aliments")
        # Calculer les proportions moyennes par type d'aliment pour ce cluster
        cluster_food_data = merged_df[merged_df['cluster'] == selected_cluster]
        type_proportions = cluster_food_data.groupby('Type').agg({
            'proportion_total_calories': 'mean',
            'proportion_total_lipids': 'mean',
            'proportion_total_protein': 'mean',
            'proportion_total_carbs': 'mean'
        }).round(3)
        
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
        
        # Créer le diagramme circulaire des types d'aliments
        fig_types = go.Figure(data=[go.Pie(
            labels=type_proportions.index,
            values=type_proportions[prop_mapping[prop_type]] * 100,
            textinfo='label+percent',
            hovertemplate="Type: %{label}<br>Proportion: %{percent}<extra></extra>",
            textposition='auto',
            insidetextorientation='radial'
        )])
        
        fig_types.update_layout(
            showlegend=True,
            height=400,
            title=f"Distribution des types d'aliments (par {prop_type.lower()})"
        )
        
        st.plotly_chart(fig_types, use_container_width=True)
        
    with col3:
        st.subheader("Profil nutritionnel")
        # Créer un graphique radar pour les nutriments
        nutriments = stats['moyennes_nutriments']
        fig_nutrients = go.Figure()
        
        fig_nutrients.add_trace(go.Scatterpolar(
            r=[nutriments['calories']/1000,
               nutriments['lipides']/10,
               nutriments['proteines']/10,
               nutriments['glucides']/10],
            theta=['Calories (k)',
                  'Lipides (x10g)',
                  'Protéines (x10g)',
                  'Glucides (x10g)'],
            fill='toself'
        ))
        
        fig_nutrients.update_layout(
            polar=dict(radialaxis=dict(visible=True, showticklabels=True)),
            showlegend=False,
            title="Profil nutritionnel moyen",
            height=400
        )
        
        st.plotly_chart(fig_nutrients, use_container_width=True)
    
    # Distribution temporelle des repas
    st.subheader("Distribution temporelle des repas")
    cluster_data = merged_df[merged_df['cluster'] == selected_cluster]
    
    if 'heure' in cluster_data.columns:
        try:
            # Convertir les heures en format numérique
            if cluster_data['heure'].dtype == 'object':
                # Si l'heure est au format string (HH:MM:SS)
                cluster_data['hour'] = pd.to_datetime(cluster_data['heure']).dt.hour
            else:
                # Si l'heure est déjà numérique
                cluster_data['hour'] = cluster_data['heure'].astype(int)
            
            # Créer un DataFrame avec toutes les heures possibles (0-23)
            all_hours = pd.DataFrame({'hour': range(24)})
            
            # Compter les occurrences pour chaque heure
            hourly_counts = cluster_data['hour'].value_counts().reset_index()
            hourly_counts.columns = ['hour', 'count']
            
            # Fusionner avec toutes les heures possibles pour avoir les heures manquantes
            hourly_dist = pd.merge(all_hours, hourly_counts, on='hour', how='left').fillna(0)
            
            # Calculer les pourcentages
            total_meals = hourly_dist['count'].sum()
            hourly_dist['percentage'] = (hourly_dist['count'] / total_meals * 100).round(2)
            
            # Créer le graphique
            fig_time = go.Figure()
            
            fig_time.add_trace(go.Scatter(
                x=hourly_dist['hour'],
                y=hourly_dist['percentage'],
                mode='lines+markers',
                name='Distribution',
                line=dict(width=2),
                marker=dict(size=8)
            ))
            
            fig_time.update_layout(
                title="Distribution horaire des repas",
                xaxis_title="Heure de la journée",
                yaxis_title="Pourcentage des repas (%)",
                xaxis=dict(
                    tickmode='array',
                    ticktext=[f"{i:02d}h" for i in range(24)],
                    tickvals=list(range(24)),
                    range=[-0.5, 23.5]  # Pour bien montrer toutes les heures
                ),
                yaxis=dict(
                    range=[0, max(hourly_dist['percentage']) * 1.1]  # Ajouter 10% de marge en haut
                ),
                showlegend=False,
                height=400
            )
            
            # Ajouter une grille pour une meilleure lisibilité
            fig_time.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
            fig_time.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
            
            st.plotly_chart(fig_time, use_container_width=True)
            
            # Afficher les données brutes dans un expander
            with st.expander("Voir les données de distribution horaire"):
                st.dataframe(
                    hourly_dist.sort_values('hour')[['hour', 'percentage']].rename(
                        columns={'hour': 'Heure', 'percentage': 'Pourcentage (%)'})
                )
            
        except Exception as e:
            st.error(f"Erreur lors de la création du graphique temporel: {str(e)}")
            st.write("Structure des données temporelles:", cluster_data['heure'].dtype)
            st.write("Premières valeurs:", cluster_data['heure'].head())
    else:
        st.warning("Colonne 'heure' non trouvée dans les données")
    
    # Tableau des proportions par type d'aliment
    st.subheader("Tableau détaillé des proportions par type d'aliment (%)")
    display_df = type_proportions * 100
    display_df.columns = ['Calories', 'Lipides', 'Protéines', 'Glucides']
    st.dataframe(
        display_df.round(2).sort_values('Calories', ascending=False),
        use_container_width=True
    )
    
else:
    st.error("Impossible de charger les données. Veuillez vérifier que toutes les données nécessaires sont disponibles.")
