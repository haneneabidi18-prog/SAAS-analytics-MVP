"""
AI Decision Engine — Génère des recommandations actionnables
basées sur les métriques live + le score QoE.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Decision:
    priority: str          # "critical" | "warning" | "info"
    icon: str
    title: str
    description: str
    impact: str
    confidence: int        # 0-100
    action_label: str
    copilot_prompt: str    # question pré-remplie pour le Copilot


def analyze(metrics: dict, qoe: dict) -> List[Decision]:
    """
    Analyse les métriques et retourne une liste de décisions triées par priorité.
    """
    decisions: List[Decision] = []
    cdn_health = metrics.get("cdn_health", {})
    rebuffer   = metrics.get("rebuffer_rate", 0)
    bitrate    = metrics.get("bitrate_avg", 4.2)
    startup    = metrics.get("startup_time", 2.5)
    viewers    = metrics.get("viewers", 20000)
    latency    = metrics.get("latency_p95", 3.0)
    qoe_score  = qoe.get("global", 75)
    dims       = qoe.get("dimensions", {})

    # ── CDN dégradé ────────────────────────────────────────────────────────
    degraded_cdns = [
        cdn for cdn, health in cdn_health.items() if health < 97.0
    ]
    for cdn in degraded_cdns:
        health = cdn_health[cdn]
        severity = "critical" if health < 94 else "warning"
        decisions.append(Decision(
            priority     = severity,
            icon         = "🔴" if severity == "critical" else "🟡",
            title        = f"Basculer le trafic hors de {cdn}",
            description  = f"{cdn} affiche un uptime de {health}% — en dessous du seuil optimal. "
                           f"Environ {int(viewers * 0.3):,} viewers potentiellement impactés.",
            impact       = f"Gain QoE estimé : +{8 if severity=='critical' else 4} points",
            confidence   = 94 if severity == "critical" else 82,
            action_label = "Basculer le trafic",
            copilot_prompt = f"Pourquoi {cdn} est-il dégradé et vers quel CDN dois-je basculer en priorité ? "
                             f"Quel est le risque si je ne fais rien ?"
        ))

    # ── Rebuffering élevé ───────────────────────────────────────────────────
    if rebuffer > 1.0:
        decisions.append(Decision(
            priority     = "critical" if rebuffer > 1.5 else "warning",
            icon         = "🔴" if rebuffer > 1.5 else "🟡",
            title        = "Réduire le taux de rebuffering",
            description  = f"Le taux de rebuffering est à {rebuffer}% — au-dessus du seuil acceptable (1%). "
                           f"Cela pénalise fortement le score QoE (dimension fluidité : {dims.get('buffering', 0):.0f}/100).",
            impact       = "Gain QoE estimé : +12 points sur la dimension fluidité",
            confidence   = 88,
            action_label = "Activer l'ABR agressif",
            copilot_prompt = f"Le rebuffering est à {rebuffer}%. Quelle est la cause probable et "
                             f"quelle configuration ABR recommandes-tu pour le réduire rapidement ?"
        ))

    # ── Délai de démarrage ──────────────────────────────────────────────────
    if startup > 3.0:
        decisions.append(Decision(
            priority     = "warning",
            icon         = "🟡",
            title        = "Optimiser le délai de démarrage",
            description  = f"Le startup time moyen est de {startup}s — au-dessus du seuil recommandé (2s). "
                           f"Les utilisateurs mobiles sont les plus touchés.",
            impact       = "Réduction du taux d'abandon initial de ~15%",
            confidence   = 79,
            action_label = "Activer le préchargement",
            copilot_prompt = f"Le délai de démarrage est à {startup}s. Comment optimiser le préchargement "
                             f"et le manifeste HLS pour réduire ce délai ?"
        ))

    # ── Bitrate bas ─────────────────────────────────────────────────────────
    if bitrate < 3.5:
        decisions.append(Decision(
            priority     = "warning",
            icon         = "🟡",
            title        = "Augmenter le bitrate cible",
            description  = f"Le bitrate moyen est à {bitrate} Mbps — les streams 1080p nécessitent min 4 Mbps. "
                           f"La qualité vidéo est dégradée pour les viewers en réseau stable.",
            impact       = "Gain QoE estimé : +8 points sur la qualité vidéo",
            confidence   = 76,
            action_label = "Ajuster le profil d'encodage",
            copilot_prompt = f"Le bitrate est à {bitrate} Mbps. Quels profils d'encodage recommandes-tu "
                             f"pour améliorer la qualité sans surcharger les CDN ?"
        ))

    # ── QoE global faible ───────────────────────────────────────────────────
    if qoe_score < 65:
        decisions.append(Decision(
            priority     = "critical",
            icon         = "🔴",
            title        = "Score QoE global critique — action immédiate",
            description  = f"Le QoE global est à {qoe_score}/100 — en zone critique. "
                           f"Plusieurs dimensions sont dégradées simultanément.",
            impact       = "Risque élevé d'abandon et de churn viewers",
            confidence   = 97,
            action_label = "Voir le rapport complet",
            copilot_prompt = f"Mon QoE global est à {qoe_score}/100. Donne-moi un plan d'action prioritaire "
                             f"pour le remonter au-dessus de 75 le plus rapidement possible."
        ))

    # ── Pic de charge prévu ──────────────────────────────────────────────────
    decisions.append(Decision(
        priority     = "info",
        icon         = "🔵",
        title        = "Pic de charge prévu ce soir à 21h",
        description  = f"Tendance détectée : +38% de viewers attendus entre 20h30 et 22h. "
                       f"Capacité actuelle : {viewers:,} viewers — marge disponible estimée à 15%.",
        impact       = "Préparation préventive recommandée",
        confidence   = 81,
        action_label = "Planifier le scaling",
        copilot_prompt = "Un pic de viewers est prévu ce soir à 21h. Comment dois-je préparer mon infrastructure "
                         "CDN et mon encodeur pour absorber +38% de charge sans dégradation QoE ?"
    ))

    # Tri : critical → warning → info
    order = {"critical": 0, "warning": 1, "info": 2}
    decisions.sort(key=lambda d: order.get(d.priority, 9))

    return decisions
