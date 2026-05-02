# StreamAnalytics Pro 📡

Plateforme SaaS de monitoring streaming temps réel avec fonctionnalités AI premium.

## Fonctionnalités

| Feature | Description | Statut |
|---------|-------------|--------|
| 📊 Dashboard Live | Métriques temps réel — viewers, bitrate, CDN, latence | ✅ |
| 🎯 QoE Score | Score qualité pondéré sur 6 dimensions | ✅ PREMIUM |
| 🧠 AI Decision Engine | Recommandations intelligentes et actionnables | ✅ PREMIUM |
| 🤖 AI Copilot | Chat IA contextuel avec métriques live (Claude) | ✅ PREMIUM |

## Structure du projet

```
streamlit-analytics/
├── Home.py                          # Page d'accueil
├── pages/
│   ├── 1_📊_Dashboard.py            # Dashboard principal
│   ├── 2_🎯_QoE_Score.py            # Score QoE détaillé
│   ├── 3_🧠_AI_Decision_Engine.py   # Engine de décisions IA
│   └── 4_🤖_AI_Copilot.py          # Chat avec Claude
├── utils/
│   ├── data.py                      # Données & simulation
│   ├── qoe.py                       # Calcul du score QoE
│   └── decision_engine.py           # Logique des décisions AI
├── .streamlit/
│   ├── config.toml                  # Thème dark + config
│   └── secrets.toml                 # Clé API (ne pas committer)
├── requirements.txt
└── .gitignore
```

## Déploiement sur Streamlit Cloud

### 1. Pusher sur GitHub
```bash
git init
git add .
git commit -m "feat: StreamAnalytics Pro v2 — QoE + AI Engine + Copilot"
git remote add origin https://github.com/VOTRE_USER/streamlit-analytics.git
git push -u origin main
```

### 2. Connecter à Streamlit Cloud
1. Aller sur [share.streamlit.io](https://share.streamlit.io)
2. "New app" → sélectionner votre repo
3. Main file : `Home.py`

### 3. Configurer la clé API (Copilot IA)
Dans Streamlit Cloud → votre app → **Settings → Secrets** :
```toml
ANTHROPIC_API_KEY = "sk-ant-votre-cle-ici"
```

Obtenez votre clé sur [console.anthropic.com](https://console.anthropic.com).

### 4. ⚠️ Ne jamais committer secrets.toml
Le fichier `.gitignore` est déjà configuré pour l'exclure.

## Développement local

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Connecter vos vraies données

Remplacez les fonctions dans `utils/data.py` par vos appels API réels :
- `get_live_metrics()` → votre API de métriques streaming
- `get_timeseries()` → votre base de données InfluxDB / TimescaleDB
- `get_cdn_performance()` → API de votre CDN provider

---
Powered by [Claude AI](https://anthropic.com) · Streamlit · Plotly
