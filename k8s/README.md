# Guide de déploiement Kubernetes pour SmartContractAnalyser

Ce répertoire contient les fichiers manifestes Kubernetes nécessaires pour déployer l'application SmartContractAnalyser sur un cluster Kubernetes (comme Minikube ou AKS).

## Structure des fichiers

- `app-secrets.yaml` : Définit les secrets utilisés par l'application, notamment la clé API OpenAI
- `backend-deployment.yaml` : Déploiement du backend Flask
- `backend-service.yaml` : Service exposant le backend
- `frontend-deployment.yaml` : Déploiement du frontend React
- `frontend-service.yaml` : Service exposant le frontend
- `kustomization.yaml` : Configuration Kustomize pour faciliter le déploiement

## Fonctionnement

### Composants principaux

1. **Backend (Flask)**
   - Déployé avec 1 réplica
   - Expose le port 8000
   - Utilise la clé API OpenAI stockée dans un secret Kubernetes
   - Configuré avec des limites de ressources (CPU/mémoire)

2. **Frontend (React)**
   - Déployé avec 1 réplica
   - Expose le port 80
   - Configuré pour communiquer avec le backend via le service backend-service
   - Configuré avec des limites de ressources (CPU/mémoire)

3. **Services**
   - `backend-service` : Expose le backend sur le port 30455 (NodePort)
   - `frontend-service` : Expose le frontend sur le port 30456 (NodePort)

4. **Secrets**
   - `app-secrets` : Stocke la clé API OpenAI encodée en base64

### Comparaison avec docker-compose

Cette configuration Kubernetes est équivalente au `docker-compose.yml` à la racine du projet, mais avec les différences suivantes :

- **Kubernetes** utilise des objets distincts (Deployments, Services, Secrets) au lieu d'une configuration monolithique
- Les **services de base de données** (PostgreSQL et pgAdmin) ne sont pas inclus dans cette configuration Kubernetes
- Les **variables d'environnement** sont définies directement dans les manifestes ou via des secrets
- L'**exposition des services** se fait via NodePort au lieu de ports mappés directement

## Déploiement

### Prérequis

- Un cluster Kubernetes fonctionnel (Minikube, AKS, etc.)
- kubectl installé et configuré
- Images Docker construites et disponibles (localement ou dans un registre)

### Préparation des secrets

Avant de déployer, vous devez mettre à jour le fichier `app-secrets.yaml` avec votre clé API OpenAI encodée en base64 :

```bash
echo -n "votre-clé-api-openai" | base64
```

Remplacez la valeur `openai-api-key` dans `app-secrets.yaml` par le résultat.

### Méthode 1 : Déploiement individuel des manifestes

```bash
kubectl apply -f k8s/app-secrets.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-service.yaml
```

### Méthode 2 : Déploiement avec Kustomize

```bash
kubectl apply -k k8s/
```

## Accès à l'application

Une fois déployée, l'application est accessible via :

- **Frontend** : http://<adresse-ip-du-nœud>:30456
- **Backend API** : http://<adresse-ip-du-nœud>:30455

Pour Minikube, vous pouvez obtenir l'adresse IP avec :

```bash
minikube ip
```

## Dépannage

- **Problème** : Les pods ne démarrent pas
  - **Solution** : Vérifiez les logs avec `kubectl logs <nom-du-pod>`

- **Problème** : Les services ne sont pas accessibles
  - **Solution** : Vérifiez que les services sont correctement exposés avec `kubectl get services`

- **Problème** : Le frontend ne peut pas communiquer avec le backend
  - **Solution** : Vérifiez que la variable d'environnement `REACT_APP_API_URL` pointe vers le bon service

- **Problème** : L'analyse des contrats échoue
  - **Solution** : Vérifiez que le secret contenant la clé API OpenAI est correctement configuré

## Nettoyage

Pour supprimer tous les ressources déployées :

```bash
kubectl delete -k k8s/
```

Ou individuellement :

```bash
kubectl delete -f k8s/frontend-service.yaml
kubectl delete -f k8s/backend-service.yaml
kubectl delete -f k8s/frontend-deployment.yaml
kubectl delete -f k8s/backend-deployment.yaml
kubectl delete -f k8s/app-secrets.yaml
```

## Commandes Kubernetes essentielles

Voici une liste des commandes Kubernetes essentielles pour gérer et surveiller votre application.

### Vérifier si les pods tournent

```bash
# Lister tous les pods dans le namespace courant
kubectl get pods

# Lister tous les pods dans tous les namespaces
kubectl get pods --all-namespaces

# Afficher des informations détaillées sur les pods
kubectl get pods -o wide

# Surveiller l'état des pods en temps réel
kubectl get pods --watch

# Lister les pods avec des sélecteurs spécifiques
kubectl get pods -l app=backend
```

### Voir les services

```bash
# Lister tous les services
kubectl get services

# Afficher des informations détaillées sur les services
kubectl get services -o wide

# Décrire un service spécifique
kubectl describe service backend-service
```

### Voir les volumes / persistance

```bash
# Lister tous les PersistentVolumes
kubectl get pv

# Lister toutes les PersistentVolumeClaims
kubectl get pvc

# Lister tous les StorageClasses
kubectl get storageclass

# Décrire un PersistentVolume spécifique
kubectl describe pv <nom-du-pv>

# Décrire une PersistentVolumeClaim spécifique
kubectl describe pvc <nom-du-pvc>
```

### Voir les logs

```bash
# Afficher les logs d'un pod
kubectl logs <nom-du-pod>

# Afficher les logs d'un conteneur spécifique dans un pod multi-conteneurs
kubectl logs <nom-du-pod> -c <nom-du-conteneur>

# Suivre les logs en temps réel
kubectl logs -f <nom-du-pod>

# Afficher les logs des pods précédents (en cas de redémarrage)
kubectl logs <nom-du-pod> --previous

# Afficher les logs des dernières 20 minutes
kubectl logs --since=20m <nom-du-pod>
```

### Redémarrer / supprimer un pod

```bash
# Supprimer un pod
kubectl delete pod <nom-du-pod>

# Redémarrer un pod (en le supprimant, il sera recréé par le Deployment)
kubectl delete pod <nom-du-pod>

# Redémarrer tous les pods d'un déploiement
kubectl rollout restart deployment <nom-du-deployment>

# Supprimer un pod sans délai d'attente
kubectl delete pod <nom-du-pod> --grace-period=0 --force
```

### Débugger un déploiement

```bash
# Décrire un déploiement pour voir son état et les événements
kubectl describe deployment <nom-du-deployment>

# Vérifier l'historique des déploiements
kubectl rollout history deployment <nom-du-deployment>

# Vérifier le statut d'un déploiement
kubectl rollout status deployment <nom-du-deployment>

# Revenir à une version précédente d'un déploiement
kubectl rollout undo deployment <nom-du-deployment>

# Revenir à une révision spécifique
kubectl rollout undo deployment <nom-du-deployment> --to-revision=<numéro-de-révision>

# Mettre en pause un déploiement (pour éviter les mises à jour automatiques)
kubectl rollout pause deployment <nom-du-deployment>

# Reprendre un déploiement en pause
kubectl rollout resume deployment <nom-du-deployment>

# Exécuter une commande dans un pod pour le déboguer
kubectl exec -it <nom-du-pod> -- /bin/bash
```

### Vérifier l'état du cluster

```bash
# Afficher les informations sur le cluster
kubectl cluster-info

# Afficher l'état des nœuds du cluster
kubectl get nodes

# Afficher des informations détaillées sur les nœuds
kubectl describe node <nom-du-nœud>

# Vérifier l'utilisation des ressources des nœuds
kubectl top nodes

# Vérifier l'utilisation des ressources des pods
kubectl top pods

# Vérifier les composants du plan de contrôle
kubectl get componentstatuses
```

### Autres commandes utiles

```bash
# Créer un port-forward pour accéder à un service localement
kubectl port-forward service/<nom-du-service> <port-local>:<port-service>

# Afficher les événements du cluster
kubectl get events

# Afficher les événements triés par timestamp
kubectl get events --sort-by='.metadata.creationTimestamp'

# Afficher les secrets
kubectl get secrets

# Afficher les ConfigMaps
kubectl get configmaps

# Afficher les namespaces
kubectl get namespaces

# Changer de contexte (cluster)
kubectl config use-context <nom-du-contexte>

# Afficher les contextes disponibles
kubectl config get-contexts
```
