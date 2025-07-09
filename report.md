# Rapport d'analyse : Problèmes de connexion à la base de données

## Problèmes identifiés

### 1. Conflit de configuration de la base de données

J'ai identifié un conflit dans la configuration de la connexion à la base de données :

- Dans le fichier `.env`, la variable `DATABASE_URL` est configurée pour pointer vers la base de données locale PostgreSQL :
  ```
  DATABASE_URL=postgresql://user:password@db:5432/mydb
  ```

- Cependant, dans le fichier `docker-compose.yml`, la variable d'environnement `DATABASE_URL` pour le service backend est explicitement définie pour pointer vers une base de données Azure :
  ```yaml
  environment:
    DATABASE_URL: postgresql://user:Nassim1102@smartcontract-bdd.postgres.database.azure.com:5432/mydb
  ```

Cette configuration dans le `docker-compose.yml` **remplace** la valeur définie dans le fichier `.env`, ce qui fait que l'application tente de se connecter à la base de données Azure au lieu de la base de données locale.

### 2. Conséquences

- Les tables ne sont pas créées dans la base de données locale car l'application tente de se connecter à la base de données Azure.
- Si les identifiants Azure ne sont pas valides ou si la connexion à Azure n'est pas possible, l'application ne pourra pas créer les tables ni stocker de données.

## Solution proposée

Pour résoudre ce problème, vous avez deux options :

### Option 1 : Utiliser la base de données locale (recommandé pour le développement)

Modifiez le fichier `docker-compose.yml` pour utiliser la variable d'environnement du fichier `.env` au lieu de définir explicitement l'URL Azure :

```yaml
environment:
  DATABASE_URL: ${DATABASE_URL}
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  FLASK_APP: app.py
  FLASK_RUN_HOST: 0.0.0.0
```

Cela permettra à l'application d'utiliser l'URL de la base de données locale définie dans le fichier `.env`.

### Option 2 : Utiliser la base de données Azure (si nécessaire pour la production)

Si vous souhaitez utiliser la base de données Azure, assurez-vous que :
1. Les identifiants sont corrects
2. Le serveur Azure est accessible depuis votre environnement
3. Les règles de pare-feu Azure permettent les connexions depuis votre adresse IP

Dans ce cas, vous pouvez soit :
- Laisser la configuration actuelle dans `docker-compose.yml`
- Ou modifier le fichier `.env` pour utiliser l'URL Azure (en décommentant la ligne appropriée)

## Vérification après modification

Après avoir effectué les modifications, vous devriez :

1. Reconstruire les conteneurs Docker :
   ```
   docker-compose down
   docker-compose up --build
   ```

2. Vérifier que les tables sont créées dans la base de données en vous connectant à pgAdmin (accessible à http://localhost:4457) avec :
   - Email : admin@admin.com
   - Mot de passe : admin

3. Ajouter un serveur dans pgAdmin avec les paramètres suivants :
   - Nom : Local PostgreSQL
   - Hôte : db
   - Port : 5432
   - Base de données : mydb
   - Utilisateur : user
   - Mot de passe : password

4. Vérifier que les tables `user`, `report` et `feedback` ont été créées.

## Conclusion

Le problème principal est un conflit de configuration entre le fichier `.env` et `docker-compose.yml`. En résolvant ce conflit, l'application devrait pouvoir se connecter correctement à la base de données et créer les tables nécessaires au démarrage.