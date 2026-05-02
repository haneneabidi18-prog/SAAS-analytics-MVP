"""
QoE Score Engine — Quality of Experience
Formule pondérée sur 6 dimensions.
"""

import numpy as np


WEIGHTS = {
    "video_quality":   0.28,
    "buffering":       0.25,
    "startup_delay":   0.18,
    "audio_sync":      0.12,
    "cdn_health":      0.10,
    "resolution_stab": 0.07,
}

LABELS = {
    "video_quality":   "Qualité vidéo",
    "buffering":       "Fluidité (anti-rebuffering)",
    "startup_delay":   "Délai de démarrage",
    "audio_sync":      "Sync audio/vidéo",
    "cdn_health":      "Santé CDN",
    "resolution_stab": "Stabilité résolution",
}


def _score_video_quality(bitrate_avg: float) -> float:
    """Bitrate moyen en Mbps → score 0-100."""
    if bitrate_avg >= 6.0:   return 100.0
    if bitrate_avg >= 4.5:   return 90.0
    if bitrate_avg >= 3.5:   return 78.0
    if bitrate_avg >= 2.5:   return 62.0
    if bitrate_avg >= 1.5:   return 45.0
    return 25.0


def _score_buffering(rebuffer_rate: float) -> float:
    """Taux de rebuffering % → score 0-100 (inversé)."""
    if rebuffer_rate <= 0.3:  return 100.0
    if rebuffer_rate <= 0.7:  return 90.0
    if rebuffer_rate <= 1.0:  return 78.0
    if rebuffer_rate <= 1.5:  return 60.0
    if rebuffer_rate <= 2.5:  return 40.0
    return 20.0


def _score_startup(startup_time: float) -> float:
    """Temps de démarrage en secondes → score 0-100."""
    if startup_time <= 1.0:  return 100.0
    if startup_time <= 2.0:  return 88.0
    if startup_time <= 3.0:  return 72.0
    if startup_time <= 5.0:  return 52.0
    if startup_time <= 8.0:  return 32.0
    return 15.0


def _score_audio_sync(latency: float) -> float:
    """Latence P95 → proxy pour la sync A/V."""
    if latency <= 1.5:  return 98.0
    if latency <= 2.5:  return 88.0
    if latency <= 3.5:  return 75.0
    if latency <= 5.0:  return 58.0
    return 35.0


def _score_cdn(cdn_health: dict) -> float:
    """Moyenne des uptime CDN → score 0-100."""
    if not cdn_health:
        return 80.0
    avg = np.mean(list(cdn_health.values()))
    return round(max(0, min(100, (avg - 90) * 10)), 1)


def _score_resolution_stability(error_rate: float) -> float:
    """Taux d'erreur → stabilité résolution (proxy)."""
    if error_rate <= 0.1:  return 98.0
    if error_rate <= 0.3:  return 88.0
    if error_rate <= 0.5:  return 74.0
    if error_rate <= 1.0:  return 55.0
    return 30.0


def compute_qoe(metrics: dict) -> dict:
    """
    Calcule le score QoE global et les sous-scores.
    
    Parameters
    ----------
    metrics : dict  (sortie de utils.data.get_live_metrics)
    
    Returns
    -------
    dict avec 'global', 'dimensions', 'label', 'color'
    """
    dims = {
        "video_quality":   _score_video_quality(metrics.get("bitrate_avg", 4.0)),
        "buffering":       _score_buffering(metrics.get("rebuffer_rate", 1.0)),
        "startup_delay":   _score_startup(metrics.get("startup_time", 2.5)),
        "audio_sync":      _score_audio_sync(metrics.get("latency_p95", 3.0)),
        "cdn_health":      _score_cdn(metrics.get("cdn_health", {})),
        "resolution_stab": _score_resolution_stability(metrics.get("error_rate", 0.3)),
    }

    global_score = round(
        sum(dims[k] * WEIGHTS[k] for k in dims), 1
    )

    if global_score >= 85:
        label, color = "Excellent 🟢", "#1D9E75"
    elif global_score >= 70:
        label, color = "Bon 🟡", "#EF9F27"
    elif global_score >= 55:
        label, color = "Acceptable 🟠", "#D85A30"
    else:
        label, color = "Dégradé 🔴", "#E24B4A"

    return {
        "global":     global_score,
        "dimensions": dims,
        "labels":     LABELS,
        "weights":    WEIGHTS,
        "label":      label,
        "color":      color,
    }
