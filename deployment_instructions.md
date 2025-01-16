# Déploiement de l'Application Streamlit

## Solutions de Déploiement Recommandées

### 1. Streamlit Cloud (Solution Recommandée)
- ✅ Plan gratuit permettant d'héberger jusqu'à 3 applications publiques
- ✅ Intégration native avec GitHub
- ✅ Gestion sécurisée des secrets (stockage sécurisé des credentials AWS)
- ✅ Configuration simple et rapide

### 2. Alternative : Heroku
- Plan gratuit disponible (avec limitations)
- Gestion sécurisée des variables d'environnement

## Pourquoi Choisir Streamlit Cloud ?
1. Gratuit pour les applications publiques
2. Spécialement optimisé pour Streamlit
3. Gestion sécurisée des credentials AWS
4. Processus de déploiement simplifié

## Guide de Déploiement

### 1. Préparation du Repository GitHub
- Créer un nouveau repository GitHub
- Structure minimale requise :
  ```
  ├── streamlit_app/
  │   ├── app.py            # Votre application Streamlit
  │   └── requirements.txt  # Dépendances du projet
  ```

### 2. Gestion des Credentials
- ⚠️ Ne jamais commiter les fichiers `.env` ou credentials
- Configuration sur Streamlit Cloud :
  - Aller dans la section "Secrets"
  - Ajouter les variables d'environnement AWS :
    ```
    AWS_ACCESS_KEY_ID=votre_access_key
    AWS_SECRET_ACCESS_KEY=votre_secret_key
    AWS_DEFAULT_REGION=votre_region
    ```

### 3. Coûts
- Streamlit Cloud : Gratuit pour les applications publiques
- AWS S3 : 
  - Coûts basés sur l'utilisation
  - Tarification très abordable pour le stockage et la lecture
  - Premiers 5GB généralement gratuits

### 4. Étapes de Déploiement
1. Connecter votre compte GitHub à Streamlit Cloud
2. Sélectionner votre repository
3. Configurer les variables d'environnement
4. Déployer l'application

### 5. Bonnes Pratiques
- Utiliser `.gitignore` pour exclure les fichiers sensibles
- Tester l'application localement avant le déploiement
- Monitorer l'utilisation des ressources AWS
- Mettre en place des alertes de coûts AWS

## Support et Ressources
- [Documentation Streamlit Cloud](https://docs.streamlit.io/streamlit-cloud)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)
- [Streamlit Security](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
