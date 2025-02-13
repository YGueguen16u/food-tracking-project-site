# Food Tracking Project

Cette application Streamlit analyse et visualise les données alimentaires des utilisateurs.

## Guide de Déploiement Détaillé sur AWS

### 1. Prérequis
```bash
# Installation des outils CLI
pip install awscli awsebcli

# Vérification des installations
aws --version
eb --version
```

### 2. Configuration AWS IAM (Dans la console AWS)
1. Créez un nouveau rôle IAM pour Elastic Beanstalk :
   - Allez dans IAM > Rôles > Créer un rôle
   - Sélectionnez "AWS Service" et "Elastic Beanstalk"
   - Attachez ces politiques :
     - `AWSElasticBeanstalkWebTier`
     - `AWSElasticBeanstalkWorkerTier`
     - `AWSElasticBeanstalkMulticontainerDocker`
     - `AmazonS3ReadOnlyAccess` (pour accéder à votre bucket)
   - Nommez le rôle (ex: `food-tracking-app-role`)

2. Créez un utilisateur IAM pour le déploiement :
   - Allez dans IAM > Utilisateurs > Créer un utilisateur
   - Attachez la politique `AWSElasticBeanstalkFullAccess`
   - Sauvegardez les credentials (Access Key et Secret Key)

### 3. Configuration AWS CLI
```bash
aws configure
# Entrez vos credentials AWS :
# AWS Access Key ID: [Votre Access Key]
# AWS Secret Access Key: [Votre Secret Key]
# Default region name: [Votre région, ex: eu-west-3]
# Default output format: json
```

### 4. Préparation du Projet
1. Vérifiez que ces fichiers sont présents :
   - `requirements.txt` : Dépendances Python
   - `.ebextensions/01_environment.config` : Configuration EB
   - `Procfile` : Commande de démarrage
   - `.gitignore` : Fichiers à ignorer

2. Créez un fichier `.ebignore` :
```
venv/
.env
.git/
.gitignore
__pycache__/
*.pyc
```

### 5. Initialisation Elastic Beanstalk
```bash
# Dans le dossier du projet
eb init -p python-3.8 food-tracking-app --region votre-region
# Répondez aux questions :
# - Sélectionnez votre région
# - Créez une nouvelle application ou sélectionnez une existante
# - Choisissez d'utiliser CodeCommit (Non recommandé pour commencer)
# - Configurez les credentials SSH (Optionnel)
```

### 6. Création de l'Environnement
```bash
eb create food-tracking-env \
    --instance-type t2.micro \
    --service-role food-tracking-app-role \
    --elb-type application \
    --vpc.id vpc-xxx \
    --vpc.ec2subnets subnet-xxx,subnet-yyy \
    --vpc.elbsubnets subnet-xxx,subnet-yyy \
    --vpc.securitygroups sg-xxx
```

### 7. Configuration des Variables d'Environnement
```bash
# Dans la console Elastic Beanstalk :
# Configuration > Software > Environment properties
# Ajoutez :
BUCKET_NAME=votre-bucket-s3
AWS_DEFAULT_REGION=votre-region
```

### 8. Déploiement
```bash
# Déployez votre application
eb deploy

# Vérifiez le statut
eb status

# Ouvrez l'application dans le navigateur
eb open
```

### 9. Surveillance et Maintenance
```bash
# Voir les logs
eb logs

# Vérifier la santé
eb health

# Se connecter à l'instance
eb ssh

# Terminer l'environnement (pour éviter les coûts)
eb terminate food-tracking-env
```

## Dépannage Courant

1. **Erreur de connexion S3** :
   - Vérifiez les permissions IAM
   - Confirmez les variables d'environnement
   - Vérifiez les logs avec `eb logs`

2. **L'application ne démarre pas** :
   - Vérifiez le Procfile
   - Vérifiez requirements.txt
   - Consultez les logs

3. **Problèmes de mémoire** :
   - Augmentez la taille de l'instance
   - Optimisez le chargement des données

## Structure du Projet

- `Home.py` : Page d'accueil
- `pages/` : Pages de l'application
- `.ebextensions/` : Configuration AWS EB
- `requirements.txt` : Dépendances
- `.env.example` : Example des variables d'environnement

## Notes Importantes

- Ne jamais commiter `.env` ou les credentials AWS
- Utilisez toujours des rôles IAM plutôt que des credentials en dur
- Surveillez votre utilisation AWS pour éviter les coûts imprévus
- Faites des sauvegardes régulières de vos données

## Deployment Instructions

### Run Docker Locally
To run the Docker container locally, use the following command:

```bash
docker run -p 8501:8501 food-tracking-app
```

### Deploy to AWS Elastic Beanstalk

1. **Initialize Elastic Beanstalk**:
   ```bash
   eb init -p docker food-tracking-app --region eu-west-3
   ```

2. **Create an Environment and Deploy**:
   ```bash
   eb create food-tracking-env
   eb deploy
   ```

### Monitor Deployment
Use the Elastic Beanstalk console or CLI to monitor the deployment process and ensure everything runs smoothly.

This section provides detailed steps to deploy the application on AWS Elastic Beanstalk.

### Prerequisites
- AWS account with access to Elastic Beanstalk, S3, and IAM.
- AWS CLI and Elastic Beanstalk CLI installed locally.

### Steps
1. Configure AWS CLI:
   ```bash
   aws configure
   ```
2. Deploy using Elastic Beanstalk CLI:
   ```bash
   eb init
   eb create
   eb open
   ```

For more detailed deployment instructions, refer to the `DEPLOY_TO_AWS.md` file.
