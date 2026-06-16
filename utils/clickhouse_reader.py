"""
Lecture des metriques depuis ClickHouse pour l'app StreamAnalytics.

A placer dans utils/clickhouse_reader.py de ton app Streamlit.

Strategie de fallback :
  - Si ClickHouse est configure (secrets) ET accessible -> donnees reelles
  - Sinon -> retourne None, et l'appelant garde la simulation existante

Ainsi la meme app fonctionne en demo (simulation) et en production (donnees reelles)
sans changement de code dans les pages.
"""

from datetime import datetime, timedelta

try:
    import streamlit as st
except ImportError:
    st = None


def _config():
    """Recupere la config ClickHouse depuis les secrets Streamlit."""
    if st is None:
        return None
    host = st.secrets.get("CLICKHOUSE_HOST")
    if not host:
        return None
    return {
        "host":     host,
        "port":     int(st.secrets.get("CLICKHOUSE_PORT", 8123)),
        "username": st.secrets.get("CLICKHOUSE_USER", "default"),
        "password": st.secrets.get("CLICKHOUSE_PASSWORD", ""),
        "database": st.secrets.get("CLICKHOUSE_DATABASE", "streamanalytics"),
    }


def _get_client():
    cfg = _config()
    if not cfg:
        return None
    try:
        import clickhouse_connect
        client = clickhouse_connect.get_client(**cfg)
        client.query("SELECT 1")
        return client
    except Exception:
        return None


def is_available() -> bool:
    """True si ClickHouse est configure et accessible."""
    return _get_client() is not None


def get_live_metrics_real(org_id: str, window_minutes: int = 5) -> dict | None:
    """
    Retourne les metriques agregees recentes pour une organisation,
    au meme format que get_live_metrics() simule.
    None si ClickHouse indisponible ou aucune donnee.
    """
    client = _get_client()
    if client is None:
        return None

    since = datetime.now() - timedelta(minutes=window_minutes)
    try:
        # Agregats globaux sur la fenetre
        row = client.query(
            """
            SELECT
                avg(rebuffer_rate)        AS rebuffer_rate,
                avg(bitrate_mbps)         AS bitrate_avg,
                avg(startup_time_s)       AS startup_time,
                quantile(0.95)(latency_p95_s) AS latency_p95,
                avg(error_rate)           AS error_rate,
                max(viewers)              AS viewers
            FROM streamanalytics.metrics_raw
            WHERE org_id = {org:String} AND event_time >= {since:DateTime}
            """,
            parameters={"org": org_id, "since": since},
        ).result_rows

        if not row or row[0][5] is None:
            return None
        r = row[0]

        # Sante par CDN
        cdn_rows = client.query(
            """
            SELECT cdn, avg(cdn_health) AS health
            FROM streamanalytics.metrics_raw
            WHERE org_id = {org:String} AND event_time >= {since:DateTime}
            GROUP BY cdn
            """,
            parameters={"org": org_id, "since": since},
        ).result_rows
        cdn_health = {cdn: round(float(h), 1) for cdn, h in cdn_rows}

        return {
            "timestamp":     datetime.now(),
            "viewers":       int(r[5] or 0),
            "bitrate_avg":   round(float(r[1] or 0), 2),
            "rebuffer_rate": round(float(r[0] or 0), 3),
            "latency_p95":   round(float(r[3] or 0), 2),
            "startup_time":  round(float(r[2] or 0), 2),
            "error_rate":    round(float(r[4] or 0), 3),
            "cdn_health":    cdn_health,
        }
    except Exception:
        return None


def get_timeseries(org_id: str, metric: str = "rebuffer_avg",
                   hours: int = 1) -> list[tuple]:
    """
    Retourne une serie temporelle (minute, valeur) depuis la vue agregee 1min.
    Utile pour les graphiques d'historique.
    """
    client = _get_client()
    if client is None:
        return []

    since = datetime.now() - timedelta(hours=hours)
    agg_map = {
        "rebuffer_avg":   "avgMerge(rebuffer_avg)",
        "bitrate_avg":    "avgMerge(bitrate_avg)",
        "latency_p95":    "quantileMerge(0.95)(latency_p95)",
        "error_avg":      "avgMerge(error_avg)",
        "cdn_health_avg": "avgMerge(cdn_health_avg)",
        "viewers_max":    "maxMerge(viewers_max)",
    }
    expr = agg_map.get(metric, "avgMerge(rebuffer_avg)")
    try:
        rows = client.query(
            f"""
            SELECT minute, {expr} AS value
            FROM streamanalytics.metrics_1min
            WHERE org_id = {{org:String}} AND minute >= {{since:DateTime}}
            GROUP BY minute
            ORDER BY minute
            """,
            parameters={"org": org_id, "since": since},
        ).result_rows
        return [(m, round(float(v), 3)) for m, v in rows]
    except Exception:
        return []
