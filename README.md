# ContentFlow Backend API

Backend FastAPI de **ContentFlow**, une plateforme SaaS de stratégie éditoriale et de création de contenu assistée par IA.

Ce backend contient actuellement le module de **gestion des utilisateurs** :

* inscription avec email et mot de passe ;
* connexion avec email et mot de passe ;
* hashage sécurisé des mots de passe avec Argon2 ;
* authentification JWT ;
* récupération de l’utilisateur connecté ;
* connexion avec Notion via OAuth 2.0 ;
* création ou liaison automatique d’un compte utilisateur via Notion ;
* stockage des informations de connexion Notion dans PostgreSQL.

---

## Technologies utilisées

* Python 3
* FastAPI
* PostgreSQL
* Docker Compose
* SQLAlchemy
* Pydantic Settings
* JWT avec PyJWT
* Argon2 avec `pwdlib`
* Notion OAuth 2.0
* ngrok pour tester le callback OAuth Notion en local

---

## Structure du projet

```text
contentflow-backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── database.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── oauth_state.py
│   │   └── security.py
│   │
│   ├── db/
│   │   └── database.py
│   │
│   ├── models/
│   │   └── user.py
│   │
│   ├── schemas/
│   │   └── user.py
│   │
│   └── services/
│
├── compose.yaml
├── .env.example
├── requirements.txt
└── README.md
```

---

## Installation du projet

### 1. Cloner le dépôt

```bash
git clone <URL_DU_DEPOT>
cd contentflow-backend
```

### 2. Créer et activer l’environnement virtuel

Sous Git Bash sur Windows :

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer le fichier `.env`

Copier le modèle :

```bash
cp .env.example .env
```

Puis compléter les variables dans `.env`.

> Le fichier `.env` ne doit jamais être envoyé sur GitHub.

### 5. Démarrer PostgreSQL avec Docker

```bash
docker compose up -d
```

Vérifier que la base est démarrée :

```bash
docker compose ps
```

### 6. Lancer FastAPI

```bash
fastapi dev app/main.py
```

L’API est disponible sur :

```text
http://127.0.0.1:8000
```

La documentation Swagger est disponible sur :

```text
http://127.0.0.1:8000/docs
```

---

## Variables d’environnement

Exemple de fichier `.env` :

```env
APP_NAME=ContentFlow Backend API
APP_ENV=development

DATABASE_URL=postgresql+psycopg://contentflow_user:contentflow_password@localhost:5432/contentflow_db

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

NOTION_CLIENT_ID=replace-with-notion-client-id
NOTION_CLIENT_SECRET=replace-with-notion-client-secret
NOTION_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/auth/notion/callback
NOTION_FRONTEND_REDIRECT_URI=http://127.0.0.1:8000/docs
```

Pour Notion, `NOTION_REDIRECT_URI` doit être exactement identique à l’URI configurée dans l’intégration Notion.

---

## Base de données

PostgreSQL est lancé avec Docker Compose.

La table principale actuelle est :

```text
users
```

Elle contient notamment :

```text
id
first_name
last_name
email
password_hash
auth_provider
notion_user_id
notion_workspace_id
notion_access_token
notion_refresh_token
notion_email
is_active
created_at
updated_at
```

### Important

Actuellement, les tables sont créées au démarrage avec :

```python
Base.metadata.create_all(bind=engine)
```

Pour la suite du projet, il est conseillé d’utiliser **Alembic** pour gérer les migrations de base de données, notamment lorsque de nouvelles tables ou colonnes seront ajoutées.

---

## Routes disponibles

### Vérification de l’API

| Méthode | Route              | Description                        |
| ------- | ------------------ | ---------------------------------- |
| GET     | `/`                | Vérifie que l’API est accessible   |
| GET     | `/health/`         | Vérifie le fonctionnement de l’API |
| GET     | `/database/health` | Vérifie la connexion PostgreSQL    |

### Authentification email / mot de passe

| Méthode | Route            | Description                                   |
| ------- | ---------------- | --------------------------------------------- |
| POST    | `/auth/register` | Créer un compte avec email et mot de passe    |
| POST    | `/auth/login`    | Se connecter avec email et mot de passe       |
| GET     | `/auth/me`       | Récupérer le profil de l’utilisateur connecté |

### Authentification Notion

| Méthode | Route                   | Description                                 |
| ------- | ----------------------- | ------------------------------------------- |
| GET     | `/auth/notion/login`    | Redirige vers la page d’autorisation Notion |
| GET     | `/auth/notion/callback` | Reçoit le callback OAuth de Notion          |

---

## Exemple d’inscription

### Requête

```http
POST /auth/register
Content-Type: application/json
```

```json
{
  "first_name": "Youssef",
  "last_name": "Test",
  "email": "youssef@example.com",
  "password": "MotDePasse123!"
}
```

### Réponse

```json
{
  "id": 1,
  "first_name": "Youssef",
  "last_name": "Test",
  "email": "youssef@example.com",
  "auth_provider": "email",
  "is_active": true,
  "created_at": "..."
}
```

---

## Exemple de connexion email / mot de passe

### Requête

```http
POST /auth/login
Content-Type: application/json
```

```json
{
  "email": "youssef@example.com",
  "password": "MotDePasse123!"
}
```

### Réponse

```json
{
  "access_token": "JWT_TOKEN",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "first_name": "Youssef",
    "last_name": "Test",
    "email": "youssef@example.com",
    "auth_provider": "email",
    "is_active": true
  }
}
```

---

## Utilisation d’une route protégée

Après connexion, le frontend doit envoyer le JWT dans les headers :

```http
Authorization: Bearer JWT_TOKEN
```

Exemple :

```http
GET /auth/me
Authorization: Bearer JWT_TOKEN
```

---

## Fonctionnement de la connexion Notion

1. L’utilisateur ouvre `/auth/notion/login`.
2. Le backend redirige vers Notion.
3. L’utilisateur choisit les pages ou bases Notion à autoriser.
4. Notion redirige vers `/auth/notion/callback`.
5. Le backend échange le code OAuth contre un token Notion.
6. Le backend crée ou retrouve l’utilisateur.
7. Le backend enregistre les informations Notion dans PostgreSQL.
8. Le backend génère un JWT ContentFlow.
9. L’utilisateur est redirigé vers l’URL définie dans `NOTION_FRONTEND_REDIRECT_URI`.

Si l’utilisateur possède déjà un compte email avec la même adresse que son compte Notion, le backend lie la connexion Notion à ce compte existant afin d’éviter les doublons.

---

## Test local de Notion OAuth avec ngrok

Notion demande une URL HTTPS pour le callback OAuth. En local, FastAPI fonctionne généralement en HTTP. Il faut donc utiliser un tunnel HTTPS.

Lancer FastAPI dans un terminal :

```bash
fastapi dev app/main.py
```

Lancer ngrok dans un autre terminal :

```bash
ngrok http 8000
```

ngrok retourne une URL du type :

```text
https://xxxxx.ngrok-free.app
```

Cette URL doit être ajoutée :

* dans l’intégration Notion, comme URI de redirection ;
* dans `.env`, dans `NOTION_REDIRECT_URI`.

Exemple :

```env
NOTION_REDIRECT_URI=https://xxxxx.ngrok-free.app/auth/notion/callback
```

---

## Points importants de sécurité

* Ne jamais envoyer le fichier `.env` sur GitHub.
* Ne jamais exposer `NOTION_CLIENT_SECRET`.
* Ne jamais exposer un token Notion au frontend.
* Les mots de passe sont hashés avec Argon2.
* Le JWT est utilisé pour protéger les routes nécessitant une connexion.
* Le paramètre OAuth `state` est utilisé pour éviter les callbacks OAuth non valides.

---

## Points restant à développer

Les éléments suivants restent à intégrer dans le projet global :

* gestion des agences / organisations ;
* rôles utilisateurs : administrateur, collaborateur, etc. ;
* invitation de membres ;
* gestion du profil utilisateur ;
* déconnexion côté frontend ;
* réinitialisation de mot de passe ;
* stockage chiffré des tokens Notion ;
* remplacement du JWT dans l’URL après OAuth par une méthode plus sécurisée ;
* migrations Alembic ;
* configuration CORS pour permettre au frontend de communiquer avec l’API ;
* modules métier :

  * génération d’idées ;
  * rédaction assistée par IA ;
  * curation RSS et URL ;
  * calendrier éditorial ;
  * synchronisation avancée avec Notion.

---

## Auteur / transmission

Le module d’authentification a été initialisé avec :

* FastAPI ;
* PostgreSQL dans Docker ;
* authentification email / mot de passe ;
* JWT ;
* Notion OAuth 2.0.

La personne qui reprend le projet doit d’abord créer son propre fichier `.env` à partir de `.env.example`, puis lancer PostgreSQL avec Docker et l’API FastAPI.
