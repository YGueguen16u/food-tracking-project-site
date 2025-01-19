"""
Page Streamlit pour le recommandeur basé sur le contenu
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys
from datetime import datetime
import tempfile

# Ajouter le chemin racine au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from AWS.s3.connect_s3 import S3Manager

# Configuration de la page
st.set_page_config(
    page_title="IM - Content Based Recommender",
    page_icon="📊",
    layout="wide"
)

def load_model_stats():
    """Charge les statistiques du modèle depuis S3"""
    try:
        s3_manager = S3Manager()
        response = s3_manager.s3_client.get_object(
            Bucket=s3_manager.bucket_name,
            Key='AI/recommender/content_based/results/stats.json'
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques : {str(e)}")
        return None

def load_example_recommendations():
    """Charge les recommandations d'exemple depuis S3"""
    try:
        s3_manager = S3Manager()
        response = s3_manager.s3_client.get_object(
            Bucket=s3_manager.bucket_name,
            Key='AI/recommender/content_based/results/recommendations.json'
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        st.error(f"Erreur lors du chargement des recommandations : {str(e)}")
        return None

# Fonction pour nettoyer les colonnes numériques
def clean_numeric_column(df, column):
    """Nettoie une colonne numérique en gérant les formats particuliers"""
    def clean_value(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, float)):
            return float(x)
        # Convertir en string et nettoyer
        x = str(x).replace(' ', '')
        # Gérer le format avec deux points (1.082.4 -> 1082.4)
        if x.count('.') > 1:
            x = x.replace('.', '', x.count('.')-1)
        try:
            return float(x)
        except:
            return np.nan
    
    df[column] = df[column].apply(clean_value)
    return df

# Fonction pour charger les données depuis S3
@st.cache_data
def load_data_from_s3(file_path):
    """Charge un fichier depuis S3 et retourne un DataFrame"""
    s3 = S3Manager()
    temp_file = tempfile.NamedTemporaryFile(suffix=os.path.basename(file_path))
    try:
        s3.download_file(file_path, temp_file.name)
        df = pd.read_excel(temp_file.name)
        temp_file.close()
        
        # Nettoyer les colonnes numériques si c'est le fichier food_processed
        if "food_processed.xlsx" in file_path:
            numeric_cols = ['Valeur calorique', 'Lipides', 'Glucides', 'Protein', 'Fibre alimentaire', 'Sucre', 'Sodium']
            for col in numeric_cols:
                if col in df.columns:
                    df = clean_numeric_column(df, col)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier {file_path}: {str(e)}")
        return None

def plot_feature_distributions(food_features):
    """Crée des visualisations des distributions des caractéristiques"""
    numeric_cols = ['Valeur calorique', 'Lipides', 'Glucides', 'Protein', 'Fibre alimentaire', 'Sucre', 'Sodium']
    
    # Créer une figure avec subplots
    fig = go.Figure()
    
    for col in numeric_cols:
        # Ajouter un violin plot pour chaque caractéristique
        fig.add_trace(go.Violin(
            y=food_features[col],
            name=col,
            box_visible=True,
            meanline_visible=True
        ))
    
    fig.update_layout(
        title="Distribution des caractéristiques nutritionnelles",
        yaxis_title="Valeur",
        showlegend=False,
        height=500
    )
    
    return fig

def plot_food_type_distribution(food_features):
    """Crée un graphique de la distribution des types d'aliments"""
    type_counts = food_features['Type'].value_counts()
    
    fig = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Distribution des types d'aliments"
    )
    
    fig.update_layout(height=500)
    return fig

def plot_feature_correlations(food_features):
    """Crée une heatmap des corrélations entre caractéristiques"""
    # Sélectionner uniquement les nutriments principaux
    main_nutrients = ['Valeur calorique', 'Protein', 'Glucides', 'Lipides']
    corr_matrix = food_features[main_nutrients].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=main_nutrients,
        y=main_nutrients,
        colorscale='RdBu',
        zmid=0
    ))
    
    fig.update_layout(
        title="Corrélations entre les nutriments principaux",
        height=500
    )
    
    return fig

def main():
    st.title("📊 Recommandeur Basé sur le Contenu")

    # Charger les données depuis S3
    food_features = load_data_from_s3("reference_data/food/food_processed.xlsx")
    user_preferences = load_data_from_s3("transform/folder_4_windows_function/type_food/user_food_proportion_pandas.xlsx")
    
    if food_features is None:
        st.error("Impossible de charger les données des aliments depuis S3")
        
    if user_preferences is None:
        st.error("Impossible de charger les préférences utilisateur depuis S3")
    
    model_stats = load_model_stats()
    example_recommendations = load_example_recommendations()
    
    # Vérifier si les données sont disponibles
    if model_stats is None:
        st.warning("⚠️ Les statistiques du modèle ne sont pas disponibles.")
    
    # Section d'introduction
    st.markdown("""
    Le recommandeur basé sur le contenu utilise les caractéristiques nutritionnelles et les types d'aliments
    pour générer des recommandations personnalisées. Il analyse le profil nutritionnel des aliments que vous
    aimez pour suggérer des aliments similaires.
    """)
    
    # Métriques principales
    if model_stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "MAE",
                f"{model_stats['model_metrics']['content_based']['mae']:.3f}",
                help="Erreur absolue moyenne entre les prédictions et les vraies préférences"
            )
        
        with col2:
            st.metric(
                "RMSE",
                f"{model_stats['model_metrics']['content_based']['rmse']:.3f}",
                help="Racine de l'erreur quadratique moyenne"
            )
        
        with col3:
            st.metric(
                "Couverture",
                f"{model_stats['model_metrics']['content_based']['coverage']:.1f}%",
                help="Pourcentage d'aliments que le modèle peut recommander"
            )
        
        with col4:
            st.metric(
                "Utilisateurs",
                f"{model_stats['general_statistics']['total_users']:,}",
                help="Nombre total d'utilisateurs dans le système"
            )
        
        # Afficher les statistiques du modèle
        st.header("📈 Statistiques du Modèle")
        
        # Ajouter une section d'explication des métriques
        with st.expander("ℹ️ Comprendre les Métriques", expanded=True):
            st.markdown("""
            ### Guide d'Interprétation des Métriques
            
            #### MAE (Mean Absolute Error)
            - **Échelle** : 0 à 5 (même échelle que les ratings)
            - **Interprétation** :
                - 0.0 - 0.5 : Excellent - Prédictions très précises
                - 0.5 - 1.0 : Bon - Prédictions fiables
                - 1.0 - 2.0 : Moyen - Prédictions approximatives
                - > 2.0 : Faible - Prédictions peu fiables
            
            #### RMSE (Root Mean Square Error)
            - **Échelle** : 0 à 5
            - **Interprétation** :
                - 0.0 - 0.7 : Excellent - Prédictions très stables
                - 0.7 - 1.2 : Bon - Erreurs bien contrôlées
                - 1.2 - 2.0 : Moyen - Présence d'erreurs importantes
                - > 2.0 : Faible - Erreurs très variables
            - *Note* : Le RMSE est toujours ≥ MAE. Un grand écart entre les deux indique des erreurs de prédiction très variables.
            
            #### Couverture (Coverage)
            - **Échelle** : 0% à 100%
            - **Interprétation** :
                - 90% - 100% : Excellent - Recommandations très diversifiées
                - 70% - 90% : Bon - Bonne diversité
                - 50% - 70% : Moyen - Diversité limitée
                - < 50% : Faible - Recommandations trop restreintes
            """)
    
    # Visualisations
    st.header("Analyse des Données")
    
    if food_features is not None:
        tab1, tab2, tab3 = st.tabs([
            "Distribution des Caractéristiques",
            "Types d'Aliments",
            "Corrélations"
        ])
        
        with tab1:
            st.plotly_chart(
                plot_feature_distributions(food_features),
                use_container_width=True
            )
            
        with tab2:
            st.plotly_chart(
                plot_food_type_distribution(food_features),
                use_container_width=True
            )
            
        with tab3:
            st.plotly_chart(
                plot_feature_correlations(food_features),
                use_container_width=True
            )
    
    # Exemples de recommandations
    st.header("Exemples de Recommandations")
    
    if example_recommendations:
        # Sélection de l'utilisateur
        user_ids = list(example_recommendations.keys())
        selected_user = st.selectbox(
            "Sélectionner un utilisateur",
            user_ids,
            format_func=lambda x: f"Utilisateur {x}"
        )
        
        if selected_user:
            recs = example_recommendations[selected_user]
            
            # Afficher les recommandations dans un tableau
            if recs:
                df_recs = pd.DataFrame(recs)
                df_recs['Similarité'] = df_recs['similarity'].apply(lambda x: f"{x:.2%}")
                
                st.dataframe(
                    df_recs[['Nom', 'Type', 'Similarité']],
                    use_container_width=True
                )
            else:
                st.info("Pas de recommandations disponibles pour cet utilisateur")
    
    # Section technique
    st.header("Détails Techniques")
    
    with st.expander("Comment fonctionne le recommandeur basé sur le contenu ?"):
        st.markdown("""
        Le recommandeur basé sur le contenu fonctionne en plusieurs étapes :
        
        1. **Préparation des données**
           - Extraction des caractéristiques nutritionnelles
           - Encodage des types d'aliments
           - Normalisation des valeurs numériques
        
        2. **Création des profils**
           - Calcul des vecteurs de caractéristiques pour chaque aliment
           - Création des profils utilisateurs basés sur leurs préférences
        
        3. **Génération des recommandations**
           - Calcul de la similarité entre le profil utilisateur et les aliments
           - Sélection des aliments les plus similaires
           - Filtrage des aliments déjà consommés
        
        4. **Évaluation**
           - Calcul des métriques de performance (MAE, RMSE)
           - Analyse de la couverture du système
           - Validation sur un ensemble de test
        """)
    
    # Footer avec timestamp
    st.markdown("---")
    if model_stats:
        st.caption(
            f"Dernière mise à jour du modèle : "
            f"{datetime.fromisoformat(model_stats['general_statistics']['timestamp']).strftime('%d/%m/%Y %H:%M')}"
        )

if __name__ == "__main__":
    main()
