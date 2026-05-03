"""
Moteur de scénarios de démonstration.
Simule des incidents réalistes pour les démos commerciales.
"""

INDUSTRIES = {
    "media": {
        "name": "Groupe Média / Broadcaster",
        "icon": "📺",
        "color": "#E84393",
        "viewers_base": 280000,
        "revenue_per_hour": 45000,
        "sla": 99.9,
        "cdn_count": 5,
        "description": "Diffusion live, chaînes TV, replay VOD"
    },
    "telco": {
        "name": "Opérateur Télécoms",
        "icon": "📡",
        "color": "#00A8E8",
        "viewers_base": 1200000,
        "revenue_per_hour": 180000,
        "sla": 99.95,
        "cdn_count": 8,
        "description": "IPTV, réseau mobile, fibre"
    },
    "ott": {
        "name": "Plateforme OTT / Streaming",
        "icon": "🎬",
        "color": "#E50914",
        "viewers_base": 520000,
        "revenue_per_hour": 95000,
        "sla": 99.9,
        "cdn_count": 6,
        "description": "SVOD, AVOD, live events"
    },
    "sports": {
        "name": "Droits Sportifs / Live Events",
        "icon": "⚽",
        "color": "#00C853",
        "viewers_base": 890000,
        "revenue_per_hour": 320000,
        "sla": 99.99,
        "cdn_count": 7,
        "description": "Champions League, Formule 1, JO"
    },
}

SCENARIOS = {
    "normal": {
        "id": "normal",
        "name": "Fonctionnement Normal",
        "icon": "✅",
        "color": "#1D9E75",
        "severity": "ok",
        "duration_min": 0,
        "metrics": {
            "qoe": 84,
            "rebuffer": 0.4,
            "bitrate": 5.2,
            "latency": 2.1,
            "startup": 1.8,
            "error_rate": 0.1,
            "cdn_eu1": 99.4,
            "cdn_fr2": 99.8,
        },
        "description": "Toutes les métriques sont dans les normes. QoE excellent.",
        "ai_alert": None,
        "impact_viewers": 0,
        "revenue_loss_hour": 0,
    },
    "cdn_failure": {
        "id": "cdn_failure",
        "name": "Panne CDN Majeure",
        "icon": "🔴",
        "color": "#E24B4A",
        "severity": "critical",
        "duration_min": 12,
        "metrics": {
            "qoe": 41,
            "rebuffer": 4.8,
            "bitrate": 1.9,
            "latency": 8.7,
            "startup": 9.2,
            "error_rate": 12.4,
            "cdn_eu1": 67.2,
            "cdn_fr2": 99.1,
        },
        "description": "CDN-EU1 hors ligne depuis 12 min. 34% des viewers impactés. Rebuffering x6.",
        "ai_alert": (
            "🚨 **Alerte critique détectée — Action immédiate requise**\n\n"
            "CDN-EU1 affiche un uptime de 67% — **panne partielle confirmée**. "
            "Impact estimé : **{impact_viewers:,} viewers** avec dégradation sévère.\n\n"
            "**Plan d'action recommandé :**\n"
            "1. Basculer 100% du trafic EU vers CDN-FR2 et CDN-US1 *(confiance 97%)*\n"
            "2. Activer le mode dégradé ABR — réduire la qualité cible à 720p pour préserver la fluidité\n"
            "3. Notifier l'équipe infrastructure — SLA à risque dans **8 minutes**\n\n"
            "⏱ Sans action : perte estimée de **{revenue_loss:,}€/heure** de revenus publicitaires."
        ),
        "impact_viewers_pct": 0.34,
        "revenue_loss_pct": 0.58,
    },
    "traffic_spike": {
        "id": "traffic_spike",
        "name": "Pic de Trafic Inattendu",
        "icon": "🟡",
        "color": "#EF9F27",
        "severity": "warning",
        "duration_min": 5,
        "metrics": {
            "qoe": 62,
            "rebuffer": 2.1,
            "bitrate": 3.1,
            "latency": 5.4,
            "startup": 4.8,
            "error_rate": 2.8,
            "cdn_eu1": 94.1,
            "cdn_fr2": 96.2,
        },
        "description": "+340% de trafic en 3 min suite à un événement viral. Capacité saturée.",
        "ai_alert": (
            "⚠️ **Pic de trafic anormal détecté — Scaling requis**\n\n"
            "Augmentation de **+340%** en 3 minutes — probable event viral ou breaking news. "
            "La capacité CDN actuelle est saturée à **91%**.\n\n"
            "**Actions recommandées :**\n"
            "1. Activer le scaling automatique sur CDN-FR2 et CDN-ASIA1 *(+2 PoP)*\n"
            "2. Réduire temporairement la qualité max à 1080p pour absorber la charge\n"
            "3. Prévenir les équipes commerciales — opportunité de pic d'audience\n\n"
            "📈 Pic prévu pendant encore **18-25 minutes** selon la courbe de tendance."
        ),
        "impact_viewers_pct": 0.18,
        "revenue_loss_pct": 0.22,
    },
    "quality_drop": {
        "id": "quality_drop",
        "name": "Dégradation Qualité Progressive",
        "icon": "🟠",
        "color": "#D85A30",
        "severity": "warning",
        "duration_min": 28,
        "metrics": {
            "qoe": 55,
            "rebuffer": 1.9,
            "bitrate": 2.4,
            "latency": 6.1,
            "startup": 5.6,
            "error_rate": 3.2,
            "cdn_eu1": 97.1,
            "cdn_fr2": 98.3,
        },
        "description": "Dégradation silencieuse depuis 28 min. Bitrate chute progressivement.",
        "ai_alert": (
            "📉 **Dégradation qualité non détectée par les alertes classiques**\n\n"
            "Le bitrate a chuté de **5.2 → 2.4 Mbps** en 28 minutes de façon progressive. "
            "Les seuils d'alerte classiques n'ont pas été déclenchés — **seul l'AI Engine l'a détecté**.\n\n"
            "**Analyse causale :**\n"
            "- Congestion réseau upstream sur 3 nœuds d'encodage\n"
            "- Probable pic thermique sur les serveurs de transcodage\n\n"
            "**Actions recommandées :**\n"
            "1. Basculer l'encodage sur les nœuds de secours *(gain estimé +8 QoE points)*\n"
            "2. Ajuster le profil ABR — augmenter le buffer cible à 12s\n"
            "3. Investiguer la source de congestion upstream"
        ),
        "impact_viewers_pct": 0.22,
        "revenue_loss_pct": 0.31,
    },
    "live_event": {
        "id": "live_event",
        "name": "Grand Événement Live",
        "icon": "⚡",
        "color": "#7F77DD",
        "severity": "info",
        "duration_min": 0,
        "metrics": {
            "qoe": 91,
            "rebuffer": 0.2,
            "bitrate": 6.8,
            "latency": 1.4,
            "startup": 1.2,
            "error_rate": 0.05,
            "cdn_eu1": 99.9,
            "cdn_fr2": 99.9,
        },
        "description": "Mode grand événement activé. Infrastructure pré-scalée. QoE exceptionnel.",
        "ai_alert": (
            "⚡ **Mode Grand Événement — Infrastructure optimisée**\n\n"
            "L'AI Engine a anticipé le pic et pré-scalé l'infrastructure **4h avant l'événement**. "
            "Résultat : QoE à **91/100** malgré **{impact_viewers:,} viewers simultanés**.\n\n"
            "**Optimisations appliquées automatiquement :**\n"
            "1. ✅ Scaling préventif CDN — capacité x3 activée\n"
            "2. ✅ Profil encodage 4K/HDR optimisé\n"
            "3. ✅ Latence réduite à 1.4s — mode ultra-low latency\n"
            "4. ✅ CDN de backup en standby chaud\n\n"
            "📊 Économie estimée vs réaction manuelle : **{revenue_loss:,}€** de pertes évitées."
        ),
        "impact_viewers_pct": 1.0,
        "revenue_loss_pct": 0.0,
    },
}


def get_roi_data(industry_id: str, scenario_id: str) -> dict:
    industry  = INDUSTRIES.get(industry_id, INDUSTRIES["media"])
    scenario  = SCENARIOS.get(scenario_id, SCENARIOS["normal"])
    viewers   = industry["viewers_base"]
    rev_hour  = industry["revenue_per_hour"]

    impact_viewers = int(viewers * scenario.get("impact_viewers_pct", 0))
    revenue_loss   = int(rev_hour * scenario.get("revenue_loss_pct", 0))
    revenue_saved  = int(revenue_loss * 0.85)   # L'outil évite 85% des pertes

    return {
        "viewers_total":   viewers,
        "impact_viewers":  impact_viewers,
        "revenue_loss":    revenue_loss,
        "revenue_saved":   revenue_saved,
        "mttr_before":     42,   # minutes sans outil
        "mttr_after":      4,    # minutes avec outil
        "annual_saving":   revenue_saved * 8760 // 100,
    }
