# Guide de Déploiement sur AWS Elastic Beanstalk

Ce guide détaille les étapes pour déployer l'application Food Tracking sur AWS Elastic Beanstalk.

## Prérequis

1. Compte AWS avec accès à :
   - Elastic Beanstalk
   - S3
   - IAM pour la gestion des rôles

2. AWS CLI installé localement :
```bash
pip install awscli
aws configure  # Configurez avec vos credentials temporairement
```

3. Elastic Beanstalk CLI installé :
```bash
pip install awsebcli
```

## Étapes de Déploiement

### 1. Préparation de l'Application

Les fichiers suivants doivent être présents dans votre projet :
- `requirements.txt` (déjà existant)
- `Procfile` (déjà créé)
- `.ebextensions/01_environment.config` (déjà créé)
- `.gitignore` (déjà configuré)

### 2. Configuration sur AWS Console

1. Connectez-vous à la [Console AWS](https://aws.amazon.com/console/)

2. Créez un nouveau bucket S3 (si pas déjà fait) :
   - Services > S3
   - "Créer un bucket"
   - Nom : `food-tracking-data` (ou votre nom choisi)
   - Région : choisissez la même que pour Elastic Beanstalk
   - Laissez les autres options par défaut
   - Notez le nom du bucket

3. Créez un utilisateur IAM avec les permissions nécessaires :
   - Services > IAM
   - "Utilisateurs" > "Ajouter un utilisateur"
   - Nom : `food-tracking-app`
   - Type d'accès : Accès programmatique
   - Attacher les politiques :
     - `AWSElasticBeanstalkFullAccess`
     - `AmazonS3FullAccess`
   - Notez l'Access Key ID et Secret Access Key

### 3. Configuration d'Elastic Beanstalk

1. Allez dans Elastic Beanstalk Console :
   - Services > Elastic Beanstalk
   - "Créer une application"

2. Configurez l'application :
   - Nom : `food-tracking-app`
   - Plateforme : Python
   - Version Python : 3.8
   - Type d'application : Web server

3. Configurez l'environnement :
   - Dans "Configuration"
   - Sous "Software" ajoutez les variables d'environnement :
     ```
     AWS_ACCESS_KEY_ID=votre_access_key
     AWS_SECRET_ACCESS_KEY=votre_secret_key
     AWS_DEFAULT_REGION=votre_region
     BUCKET_NAME=votre_bucket
     ```

### 4. Déploiement Local

1. Initialisez EB CLI dans votre projet :
```bash
cd votre_projet
eb init -p python-3.8 food-tracking-app --region votre-region
```

2. Créez l'environnement et déployez :
```bash
eb create food-tracking-env
```

3. Attendez que le déploiement soit terminé (~5-10 minutes)

4. Vérifiez le statut :
```bash
eb status
```

### 5. Vérification et Maintenance

1. Ouvrez l'application :
```bash
eb open
```

2. Vérifiez les logs en cas de problème :
```bash
eb logs
```

3. Pour les mises à jour futures :
```bash
eb deploy
```

4. Pour arrêter l'environnement (pour économiser des coûts) :
```bash
eb terminate food-tracking-env
```

## Résolution des Problèmes Courants

1. Si l'application ne démarre pas :
   - Vérifiez les logs : `eb logs`
   - Assurez-vous que toutes les variables d'environnement sont configurées
   - Vérifiez que le port 8501 est ouvert dans le groupe de sécurité

2. Si les fichiers ne se chargent pas :
   - Vérifiez les permissions du bucket S3
   - Vérifiez les credentials AWS dans les variables d'environnement

3. Pour les problèmes de mémoire :
   - Dans la configuration EB, augmentez la taille de l'instance
   - Ajustez les paramètres de mémoire dans le fichier .ebextensions

## Coûts et Optimisation

- Elastic Beanstalk est facturé selon les ressources utilisées
- Pour minimiser les coûts :
  - Utilisez des instances t3.micro pour le développement
  - Arrêtez l'environnement quand il n'est pas utilisé
  - Configurez le scaling automatique selon vos besoins

## Sécurité

- Ne jamais commiter les credentials AWS
- Utilisez des groupes de sécurité restrictifs
- Activez HTTPS pour la production
- Faites des sauvegardes régulières des données

## Support

En cas de problème :
1. Consultez les logs Elastic Beanstalk
2. Vérifiez la documentation AWS
3. Utilisez AWS Support si nécessaire
