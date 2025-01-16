import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import numpy as np
import sys
import os

# Ajouter le chemin racine au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from aws_s3.connect_s3 import S3Manager

def load_recommendations():
    """Charge les recommandations depuis S3"""
    s3_manager = S3Manager()
    try:
        response = s3_manager.s3_client.get_object(
            Bucket=s3_manager.bucket_name,
            Key='AI/recommender/collaborative_filtering/results/recommendations.json'
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        st.error(f"Erreur lors du chargement des recommandations: {str(e)}")
        return None

def load_stats():
    """Charge les statistiques depuis S3"""
    s3_manager = S3Manager()
    try:
        response = s3_manager.s3_client.get_object(
            Bucket=s3_manager.bucket_name,
            Key='AI/recommender/collaborative_filtering/results/stats.json'
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {str(e)}")
        return None

def plot_recommendations(recommendations, user_id, model_type):
    """Crée un graphique des recommandations pour un utilisateur"""
    if str(user_id) not in recommendations[model_type]:
        return None
        
    user_recs = recommendations[model_type][str(user_id)]
    df = pd.DataFrame(user_recs)
    
    fig = px.bar(
        df,
        x='type',
        y='score',
        title=f"Recommandations de types d'aliments ({model_type})",
        labels={'type': "Type d'aliment", 'score': 'Score de recommandation'}
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
        height=400
    )
    return fig

def main():
    st.title("🤝 Recommandations Collaboratives")
    
    # Ajouter une section d'explications
    with st.expander("ℹ️ Comprendre les métriques et visualisations", expanded=True):
        st.markdown("""
        ### 📊 Métriques de Performance
        
        #### MAE (Mean Absolute Error)
        - Mesure l'erreur moyenne absolue entre les prédictions et les vraies préférences
        - **Interprétation** :
            * 0.0 - 0.5 : Excellente précision
            * 0.5 - 1.0 : Bonne précision
            * 1.0 - 1.5 : Précision moyenne
            * > 1.5 : Faible précision
        - Exemple : Un MAE de 0.8 signifie que les prédictions sont en moyenne à 0.8 points des vraies préférences
        
        #### RMSE (Root Mean Square Error)
        - Similaire au MAE mais pénalise davantage les grandes erreurs
        - **Interprétation** :
            * 0.0 - 0.7 : Excellente précision
            * 0.7 - 1.2 : Bonne précision
            * 1.2 - 1.7 : Précision moyenne
            * > 1.7 : Faible précision
        - Exemple : Un RMSE de 1.0 indique des erreurs plus importantes que MAE = 1.0
        
        #### Couverture (Coverage)
        - Pourcentage des types d'aliments que le modèle peut recommander
        - **Interprétation** :
            * 90% - 100% : Excellente couverture
            * 70% - 90% : Bonne couverture
            * 50% - 70% : Couverture moyenne
            * < 50% : Faible couverture
        - Exemple : Une couverture de 85% signifie que le modèle peut recommander 85% des types d'aliments disponibles
        
        ### 📈 Visualisations des Recommandations
        
        #### Graphiques par Type d'Aliment
        - **Axe X** : Types d'aliments (ex: Fruits, Légumes, etc.)
        - **Axe Y** : Score de recommandation (0 à 5)
        - Plus la barre est haute, plus le type d'aliment est recommandé
        
        #### Les Trois Modèles de Recommandation
        
        1. **👥 User-User CF (Filtrage Collaboratif Utilisateur-Utilisateur)**
           - Recommande des types d'aliments basés sur les préférences d'utilisateurs similaires
           - Plus adapté quand les utilisateurs ont des goûts stables
           - Exemple : Si des utilisateurs similaires à vous aiment les légumes, le modèle vous recommandera des légumes
        
        2. **🔄 Item-Item CF (Filtrage Collaboratif Item-Item)**
           - Recommande des types d'aliments similaires à ceux que vous avez appréciés
           - Plus adapté quand les relations entre aliments sont stables
           - Exemple : Si vous aimez les fruits, le modèle recommandera d'autres types d'aliments souvent appréciés par les amateurs de fruits
        
        3. **🤝 Hybride**
           - Combine les forces des deux approches précédentes
           - Plus robuste car compense les faiblesses de chaque approche
           - Exemple : Utilise à la fois les similarités entre utilisateurs et entre types d'aliments pour faire des recommandations plus précises
        
        #### Interprétation des Scores
        - **4.0 - 5.0** : Recommandation très forte
        - **3.0 - 4.0** : Recommandation forte
        - **2.0 - 3.0** : Recommandation modérée
        - **1.0 - 2.0** : Recommandation faible
        """)
    
    # Charger les données
    recommendations = load_recommendations()
    stats = load_stats()
    
    if recommendations is None or stats is None:
        st.error("Impossible de charger les données. Veuillez réessayer plus tard.")
        return
        
    # Afficher les statistiques générales
    st.header("📊 Statistiques Générales")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Utilisateurs",
            stats['general_statistics']['total_users']
        )
    with col2:
        st.metric(
            "Types d'aliments",
            stats['general_statistics']['total_items']
        )
    with col3:
        st.metric(
            "Interactions",
            stats['general_statistics']['total_interactions']
        )
        
    # Afficher les métriques des modèles
    st.header("📈 Performance des Modèles")
    metrics_df = pd.DataFrame({
        'Modèle': ['User-User CF', 'Item-Item CF', 'Hybride'],
        'MAE': [
            stats['model_metrics']['user_user_cf']['mae'],
            stats['model_metrics']['item_item_cf']['mae'],
            stats['model_metrics']['hybrid']['mae']
        ],
        'RMSE': [
            stats['model_metrics']['user_user_cf']['rmse'],
            stats['model_metrics']['item_item_cf']['rmse'],
            stats['model_metrics']['hybrid']['rmse']
        ],
        'Couverture (%)': [
            stats['model_metrics']['user_user_cf']['coverage'],
            stats['model_metrics']['item_item_cf']['coverage'],
            stats['model_metrics']['hybrid']['coverage']
        ]
    })
    
    st.dataframe(
        metrics_df.style.format({
            'MAE': '{:.3f}',
            'RMSE': '{:.3f}',
            'Couverture (%)': '{:.1f}'
        }),
        hide_index=True
    )
    
    # Sélection de l'utilisateur
    st.header("🎯 Recommandations Personnalisées")
    user_ids = sorted([int(uid) for uid in recommendations['user_user_cf'].keys()])
    selected_user = st.selectbox(
        "Sélectionnez un utilisateur",
        user_ids,
        format_func=lambda x: f"Utilisateur {x}"
    )
    
    # Afficher les recommandations
    if selected_user:
        tabs = st.tabs(["👥 User-User CF", "🔄 Item-Item CF", "🤝 Hybride"])
        
        with tabs[0]:
            fig = plot_recommendations(recommendations, selected_user, 'user_user_cf')
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Afficher le tableau détaillé
                st.subheader("Détails des recommandations")
                recs_df = pd.DataFrame(recommendations['user_user_cf'][str(selected_user)])
                st.dataframe(
                    recs_df.style.format({'score': '{:.3f}'}),
                    hide_index=True
                )
                
        with tabs[1]:
            fig = plot_recommendations(recommendations, selected_user, 'item_item_cf')
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Afficher le tableau détaillé
                st.subheader("Détails des recommandations")
                recs_df = pd.DataFrame(recommendations['item_item_cf'][str(selected_user)])
                st.dataframe(
                    recs_df.style.format({'score': '{:.3f}'}),
                    hide_index=True
                )
                
        with tabs[2]:
            fig = plot_recommendations(recommendations, selected_user, 'hybrid')
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Afficher le tableau détaillé
                st.subheader("Détails des recommandations")
                recs_df = pd.DataFrame(recommendations['hybrid'][str(selected_user)])
                st.dataframe(
                    recs_df.style.format({'score': '{:.3f}'}),
                    hide_index=True
                )
                
    # Ajouter des informations sur la dernière mise à jour
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Informations")
    st.sidebar.markdown(f"Dernière mise à jour: {stats['general_statistics']['timestamp']}")

if __name__ == "__main__":
    main()
