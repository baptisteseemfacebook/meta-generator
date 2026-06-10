# Meta Description Generator

Génère 5 propositions de meta descriptions SEO (140–160 caractères) en analysant les 10 premiers résultats Google pour un mot-clé donné.

## Lancement en local

```bash
pip install -r requirements.txt
python app.py
```

Ouvre http://localhost:5000 dans ton navigateur.

## Déploiement sur Netlify

> **Note** : Flask est une app WSGI serveur. Netlify héberge du statique + des fonctions serverless. Pour déployer Flask sur Netlify, l'approche la plus simple est d'utiliser **Render** ou **Railway** (gratuit, supporte Flask nativement). Si tu veux absolument Netlify, il faut réécrire les routes en fonctions serverless.

### Option recommandée — Render.com (gratuit)

1. Crée un compte sur [render.com](https://render.com)
2. "New Web Service" → connecte ton repo GitHub
3. Paramètres :
   - **Build command** : `pip install -r requirements.txt`
   - **Start command** : `gunicorn app:app`
   - **Runtime** : Python 3.11
4. Ajoute `gunicorn` dans `requirements.txt`
5. Deploy — tu obtiens une URL publique en 2 min

### Option alternative — Railway.app

1. Crée un compte sur [railway.app](https://railway.app)
2. "New Project" → Deploy from GitHub repo
3. Railway détecte Flask automatiquement
4. Ajoute un `Procfile` : `web: gunicorn app:app`

## Structure du projet

```
meta-generator/
├── app.py                  # Backend Flask (scraping + génération)
├── templates/
│   └── index.html          # Interface utilisateur
├── requirements.txt
├── runtime.txt
├── netlify.toml
└── README.md
```

## Formats générés

| Format | Description |
|--------|-------------|
| ❓ Question | Accroche sous forme de question |
| 🔢 Chiffres | Liste chiffrée avec données SERP |
| ✅ Bénéfice | Mise en avant du bénéfice direct |
| ⚡ Urgence | Ton urgent, accès immédiat |
| ⭐ Preuve Sociale | Autorité et validation sociale |
