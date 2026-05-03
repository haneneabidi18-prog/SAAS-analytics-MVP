import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# ── Seed reproductible pour la session ──────────────────────────────────────
random.seed(42)
np.random.seed(42)

CDN_LIST = ["CDN-FR2", "CDN-EU1", "CDN-US1", "CDN-ASIA1"]
REGIONS   = ["France", "Allemagne", "Espagne", "UK", "USA", "Asie"]
DEVICES   = ["Desktop", "Mobile", "Smart TV", "Tablet"]


def get_live_metrics() -> dict:
    """Simule les métriques live avec un peu de bruit."""
    now = datetime.now()
    base_viewers = 24000 + int(3000 * np.sin(now.hour * np.pi / 12))
    return {
        "viewers":        base_viewers + random.randint(-500, 500),
        "bitrate_avg":    round(4.2 + random.uniform(-0.4, 0.4), 2),
        "rebuffer_rate":  round(0.8 + random.uniform(-0.2, 0.4), 2),
        "latency_p95":    round(3.1 + random.uniform(-0.3, 0.5), 2),
        "error_rate":     round(0.3 + random.uniform(-0.1, 0.2), 2),
        "startup_time":   round(2.4 + random.uniform(-0.3, 0.6), 2),
        "cdn_health":     {
            "CDN-FR2":   round(99.2 + random.uniform(-0.5, 0.3), 1),
            "CDN-EU1":   round(94.1 + random.uniform(-2.0, 0.5), 1),
            "CDN-US1":   round(98.7 + random.uniform(-0.3, 0.3), 1),
            "CDN-ASIA1": round(97.3 + random.uniform(-0.5, 0.5), 1),
        },
        "timestamp": now,
    }


def get_timeseries(hours: int = 24, metric: str = "qoe") -> pd.DataFrame:
    """Génère une série temporelle réaliste pour les graphiques."""
    now   = datetime.now()
    times = [now - timedelta(hours=hours - i) for i in range(hours + 1)]

    if metric == "qoe":
        base   = [68, 65, 63, 64, 66, 70, 74, 78, 81, 82, 80, 78,
                  76, 79, 81, 83, 82, 79, 76, 74, 75, 76, 78, 78, 78]
        values = [min(100, max(0, b + random.uniform(-2, 2))) for b in base]
    elif metric == "viewers":
        base   = [8000, 6000, 5000, 4800, 5200, 7000, 10000, 14000, 18000, 21000,
                  23000, 24000, 23500, 22000, 21000, 22000, 23000, 24000, 25000,
                  26000, 27000, 25000, 23000, 22000, 24000]
        values = [max(0, b + random.randint(-500, 500)) for b in base]
    elif metric == "bitrate":
        base   = [3.8, 3.6, 3.5, 3.5, 3.7, 3.9, 4.0, 4.2, 4.3, 4.3,
                  4.2, 4.2, 4.1, 4.1, 4.2, 4.2, 4.3, 4.3, 4.2, 4.1,
                  4.0, 4.1, 4.2, 4.2, 4.2]
        values = [round(b + random.uniform(-0.15, 0.15), 2) for b in base]
    elif metric == "rebuffer":
        base   = [1.2, 1.5, 1.8, 1.6, 1.4, 1.1, 0.9, 0.8, 0.7, 0.7,
                  0.8, 0.8, 0.9, 0.9, 0.8, 0.8, 0.8, 0.9, 1.0, 1.1,
                  1.0, 0.9, 0.9, 0.8, 0.8]
        values = [max(0, round(b + random.uniform(-0.1, 0.2), 2)) for b in base]
    else:
        values = [round(random.uniform(50, 95), 1) for _ in range(hours + 1)]

    return pd.DataFrame({"time": times, "value": values})


def get_cdn_performance() -> pd.DataFrame:
    rows = []
    for cdn in CDN_LIST:
        base = {"CDN-FR2": 99.2, "CDN-EU1": 93.8, "CDN-US1": 98.7, "CDN-ASIA1": 97.3}[cdn]
        rows.append({
            "CDN":       cdn,
            "Uptime %":  round(base + random.uniform(-1, 0.5), 1),
            "Latence ms": {"CDN-FR2": 38, "CDN-EU1": 62, "CDN-US1": 55, "CDN-ASIA1": 71}[cdn]
                         + random.randint(-5, 15),
            "Viewers":   random.randint(3000, 9000),
            "Erreurs %": round(random.uniform(0.1, 0.6), 2),
        })
    return pd.DataFrame(rows)


def get_region_breakdown() -> pd.DataFrame:
    viewers = [9000, 5500, 3200, 2800, 2100, 1800]
    viewers = [v + random.randint(-200, 200) for v in viewers]
    return pd.DataFrame({"Region": REGIONS, "Viewers": viewers})


def get_device_breakdown() -> pd.DataFrame:
    pct = [42, 31, 18, 9]
    return pd.DataFrame({"Device": DEVICES, "Part %": pct})
