"""
Parseur de logs streaming — détecte et normalise automatiquement
les formats CSV, JSON, JSONL et .log texte.
"""

import pandas as pd
import json
import io
import re
from datetime import datetime


# Mapping de noms de colonnes courants → noms internes normalisés
COLUMN_ALIASES = {
    # Timestamp
    "timestamp": "timestamp", "time": "timestamp", "date": "timestamp",
    "datetime": "timestamp", "ts": "timestamp", "event_time": "timestamp",
    # Viewers
    "viewers": "viewers", "concurrent_viewers": "viewers",
    "active_viewers": "viewers", "users": "viewers", "sessions": "viewers",
    "concurrent_users": "viewers", "connections": "viewers",
    # Bitrate
    "bitrate": "bitrate", "bitrate_kbps": "bitrate", "bitrate_mbps": "bitrate",
    "avg_bitrate": "bitrate", "video_bitrate": "bitrate", "throughput": "bitrate",
    # Rebuffering
    "rebuffer": "rebuffer_rate", "rebuffering": "rebuffer_rate",
    "rebuffer_rate": "rebuffer_rate", "buffering_ratio": "rebuffer_rate",
    "stall_rate": "rebuffer_rate", "buffer_ratio": "rebuffer_rate",
    "rebuffering_ratio": "rebuffer_rate",
    # Latence
    "latency": "latency", "latency_p95": "latency", "p95_latency": "latency",
    "rtt": "latency", "delay": "latency", "response_time": "latency",
    "end_to_end_latency": "latency",
    # Startup
    "startup_time": "startup_time", "startup": "startup_time",
    "time_to_first_frame": "startup_time", "ttff": "startup_time",
    "join_time": "startup_time", "initial_buffering": "startup_time",
    # Erreurs
    "error_rate": "error_rate", "errors": "error_rate",
    "error_ratio": "error_rate", "failure_rate": "error_rate",
    "error_pct": "error_rate",
    # QoE
    "qoe": "qoe", "qoe_score": "qoe", "quality_score": "qoe",
    "mos": "qoe",  # Mean Opinion Score
    # CDN
    "cdn": "cdn", "cdn_name": "cdn", "edge": "cdn", "pop": "cdn",
    # Region
    "region": "region", "country": "region", "geo": "region",
    # Device
    "device": "device", "platform": "device", "device_type": "device",
}

REQUIRED_METRICS = ["viewers", "bitrate", "rebuffer_rate", "latency"]
ALL_METRICS      = ["viewers", "bitrate", "rebuffer_rate", "latency",
                    "startup_time", "error_rate", "qoe"]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes selon les alias connus."""
    rename_map = {}
    for col in df.columns:
        normalized = COLUMN_ALIASES.get(col.lower().strip().replace(" ", "_"), None)
        if normalized:
            rename_map[col] = normalized
    return df.rename(columns=rename_map)


def _normalize_bitrate(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit le bitrate en Mbps si nécessaire."""
    if "bitrate" not in df.columns:
        return df
    median = df["bitrate"].median()
    if median > 10000:      # probablement en bps
        df["bitrate"] = df["bitrate"] / 1_000_000
    elif median > 100:      # probablement en Kbps
        df["bitrate"] = df["bitrate"] / 1000
    return df


def _parse_log_line(line: str) -> dict | None:
    """Tente de parser une ligne de log texte format Apache/Nginx/custom."""
    patterns = [
        # Format: [timestamp] viewers=X bitrate=X rebuffer=X latency=X
        r'\[?(\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2})\]?.*?'
        r'(?:viewers?|concurrent)[=: ]+(\d+).*?'
        r'(?:bitrate)[=: ]+([\d.]+).*?'
        r'(?:rebuffer|buffering)[=: ]+([\d.]+)',
        # Format JSON inline: {"ts": ..., "viewers": ...}
        r'\{.*\}',
    ]

    # Essai JSON inline
    json_match = re.search(r'\{.*\}', line)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception:
            pass

    # Essai key=value
    kv = re.findall(r'(\w+)[=:]([\d.]+)', line)
    if len(kv) >= 2:
        row = {}
        for k, v in kv:
            norm = COLUMN_ALIASES.get(k.lower(), k.lower())
            try:
                row[norm] = float(v)
            except ValueError:
                pass
        if row:
            return row

    return None


def parse_uploaded_file(uploaded_file) -> tuple[pd.DataFrame | None, str, list[str]]:
    """
    Parse un fichier uploadé Streamlit.

    Returns
    -------
    df       : DataFrame normalisé ou None si échec
    fmt      : format détecté ("csv", "json", "jsonl", "log", "unknown")
    warnings : liste de messages d'avertissement
    """
    warnings_ = []
    name      = uploaded_file.name.lower()
    raw       = uploaded_file.read()

    # ── CSV ──────────────────────────────────────────────────────────────────
    if name.endswith(".csv") or name.endswith(".tsv"):
        sep = "\t" if name.endswith(".tsv") else ","
        try:
            df = pd.read_csv(io.BytesIO(raw), sep=sep, nrows=50_000)
            df = _normalize_columns(df)
            df = _normalize_bitrate(df)
            return df, "csv", warnings_
        except Exception as e:
            return None, "csv", [f"Erreur lecture CSV : {e}"]

    # ── JSON tableau ─────────────────────────────────────────────────────────
    if name.endswith(".json"):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                df = pd.DataFrame(data[:50_000])
            elif isinstance(data, dict):
                # Cherche une clé qui contient une liste
                for v in data.values():
                    if isinstance(v, list) and len(v) > 0:
                        df = pd.DataFrame(v[:50_000])
                        break
                else:
                    df = pd.DataFrame([data])
            df = _normalize_columns(df)
            df = _normalize_bitrate(df)
            return df, "json", warnings_
        except Exception as e:
            return None, "json", [f"Erreur lecture JSON : {e}"]

    # ── JSONL ─────────────────────────────────────────────────────────────────
    if name.endswith(".jsonl") or name.endswith(".ndjson"):
        rows = []
        for line in raw.decode("utf-8", errors="replace").splitlines()[:50_000]:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        if rows:
            df = pd.DataFrame(rows)
            df = _normalize_columns(df)
            df = _normalize_bitrate(df)
            return df, "jsonl", warnings_
        return None, "jsonl", ["Aucune ligne JSON valide trouvée"]

    # ── Log texte ─────────────────────────────────────────────────────────────
    if name.endswith(".log") or name.endswith(".txt"):
        rows = []
        for line in raw.decode("utf-8", errors="replace").splitlines()[:50_000]:
            row = _parse_log_line(line)
            if row:
                rows.append(row)
        if rows:
            df = pd.DataFrame(rows)
            df = _normalize_columns(df)
            df = _normalize_bitrate(df)
            if len(df) < 3:
                warnings_.append("Peu de lignes parsées — format de log non standard.")
            return df, "log", warnings_
        return None, "log", ["Format de log non reconnu. Essayez CSV ou JSON."]

    return None, "unknown", ["Format non supporté. Utilisez : .csv, .json, .jsonl, .log"]


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Calcule les statistiques clés depuis le DataFrame normalisé."""
    stats = {"rows": len(df), "columns": list(df.columns)}

    for metric in ALL_METRICS:
        if metric in df.columns:
            col = pd.to_numeric(df[metric], errors="coerce").dropna()
            if len(col) > 0:
                stats[metric] = {
                    "mean":   round(col.mean(), 2),
                    "max":    round(col.max(), 2),
                    "min":    round(col.min(), 2),
                    "p95":    round(col.quantile(0.95), 2),
                    "std":    round(col.std(), 2),
                }

    # Colonnes catégorielles
    for cat in ["cdn", "region", "device"]:
        if cat in df.columns:
            stats[f"{cat}_breakdown"] = df[cat].value_counts().head(10).to_dict()

    return stats


def compute_qoe_from_logs(stats: dict) -> dict:
    """Calcule un score QoE à partir des stats extraites."""
    from utils.qoe import compute_qoe
    metrics = {
        "bitrate_avg":   stats.get("bitrate", {}).get("mean", 4.0),
        "rebuffer_rate": stats.get("rebuffer_rate", {}).get("mean", 1.0),
        "startup_time":  stats.get("startup_time", {}).get("mean", 2.5),
        "latency_p95":   stats.get("latency", {}).get("p95", 3.0),
        "error_rate":    stats.get("error_rate", {}).get("mean", 0.3),
        "cdn_health":    {"CDN-UPLOAD": 97.0},
    }
    return compute_qoe(metrics)


def build_ai_context(df: pd.DataFrame, stats: dict, qoe: dict, filename: str) -> str:
    """Construit le contexte pour le Copilot IA."""
    lines = [
        f"Fichier analysé : {filename} ({stats['rows']:,} lignes)",
        f"Colonnes détectées : {', '.join(stats['columns'][:10])}",
        "",
        "=== MÉTRIQUES CLÉS ===",
    ]
    labels = {
        "viewers":      ("Viewers moyens", ""),
        "bitrate":      ("Bitrate moyen", " Mbps"),
        "rebuffer_rate":("Rebuffering moyen", "%"),
        "latency":      ("Latence P95", " s"),
        "startup_time": ("Startup time moyen", " s"),
        "error_rate":   ("Taux d'erreur moyen", "%"),
        "qoe":          ("QoE Score moyen", "/100"),
    }
    for key, (label, unit) in labels.items():
        if key in stats:
            s = stats[key]
            lines.append(f"- {label} : {s['mean']}{unit} (max: {s['max']}{unit}, P95: {s['p95']}{unit})")

    lines += ["", f"=== SCORE QoE CALCULÉ ===",
              f"Score global : {qoe['global']}/100 — {qoe['label']}"]

    for key, val in qoe["dimensions"].items():
        lines.append(f"  - {qoe['labels'][key]} : {val:.0f}/100")

    if "cdn_breakdown" in stats:
        lines += ["", "=== RÉPARTITION CDN ==="]
        for cdn, count in list(stats["cdn_breakdown"].items())[:5]:
            lines.append(f"- {cdn} : {count} événements")

    if "region_breakdown" in stats:
        lines += ["", "=== RÉPARTITION GÉOGRAPHIQUE ==="]
        for reg, count in list(stats["region_breakdown"].items())[:5]:
            lines.append(f"- {reg} : {count} événements")

    return "\n".join(lines)
