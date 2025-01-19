# Food Tracking Project

Cette application Streamlit analyse et visualise les données alimentaires des utilisateurs.

## Déploiement sur AWS Elastic Beanstalk

1. Installez l'AWS CLI et l'EB CLI :
```bash
pip install awscli awsebcli
```

2. Configurez vos variables d'environnement AWS dans la console Elastic Beanstalk :
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION
- BUCKET_NAME

3. Initialisez votre application Elastic Beanstalk :
```bash
eb init -p python-3.8 food-tracking-app --region votre-region
```

4. Créez un environnement et déployez :
```bash
eb create food-tracking-env
```

5. Pour les mises à jour futures :
```bash
eb deploy
```

## Structure du Projet

- `Home.py` : Page d'accueil de l'application
- `pages/` : Différentes pages de l'application
- `.ebextensions/` : Configuration pour AWS Elastic Beanstalk
- `Procfile` : Configuration pour le serveur web
- `requirements.txt` : Dépendances Python
- `.env.example` : Example des variables d'environnement nécessaires

## Variables d'Environnement

Copiez `.env.example` vers `.env` et remplissez avec vos credentials AWS :
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
BUCKET_NAME=your_bucket
```

⚠️ Ne jamais commiter le fichier `.env` dans Git !
