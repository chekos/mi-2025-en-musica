"""
Genera datos para el dashboard de Mi 2025 en Música.
Convierte UTC a Pacific Time y calcula todas las métricas.

Uso:
    uv run scripts/generate_data.py
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Rutas
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "data" / "streaming_history_2025.json"
OUTPUT_FILE = ROOT / "data" / "spotify-2025.json"

# Zona horaria
UTC = ZoneInfo("UTC")
PACIFIC = ZoneInfo("America/Los_Angeles")

# Fechas importantes
BIRTHDAY = (4, 6)  # 6 de abril
MEXICAN_HOLIDAYS = {
    (1, 1): "Año Nuevo",
    (2, 5): "Día de la Constitución",
    (3, 21): "Natalicio de Benito Juárez",
    (5, 1): "Día del Trabajo",
    (5, 5): "Cinco de Mayo",
    (9, 16): "Día de la Independencia",
    (11, 2): "Día de los Muertos",
    (11, 20): "Revolución Mexicana",
    (12, 25): "Navidad",
}


def utc_to_pacific(ts_str: str) -> datetime:
    """Convierte timestamp UTC a Pacific Time."""
    dt_utc = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    return dt_utc.astimezone(PACIFIC)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def calculate_overview(data: list[dict]) -> dict:
    """Métricas generales."""
    total_ms = sum(item.get("ms_played", 0) for item in data)
    artists = set()
    tracks = set()

    for item in data:
        if item.get("master_metadata_album_artist_name"):
            artists.add(item["master_metadata_album_artist_name"])
        if item.get("spotify_track_uri"):
            tracks.add(item["spotify_track_uri"])

    return {
        "total_plays": len(data),
        "total_minutes": round(total_ms / 60000),
        "total_hours": round(total_ms / 3600000, 1),
        "total_days": round(total_ms / 86400000, 1),
        "unique_artists": len(artists),
        "unique_tracks": len(tracks),
    }


def calculate_top_artists(data: list[dict], limit: int = 5) -> list[dict]:
    """Top artistas por tiempo."""
    artist_time = defaultdict(lambda: {"ms": 0, "plays": 0})

    for item in data:
        artist = item.get("master_metadata_album_artist_name")
        if artist:
            artist_time[artist]["ms"] += item.get("ms_played", 0)
            artist_time[artist]["plays"] += 1

    top = sorted(artist_time.items(), key=lambda x: x[1]["ms"], reverse=True)[:limit]
    max_ms = top[0][1]["ms"] if top else 1

    return [
        {
            "artist": artist,
            "minutes": round(stats["ms"] / 60000),
            "hours": round(stats["ms"] / 3600000, 1),
            "plays": stats["plays"],
            "pct": round(stats["ms"] / max_ms * 100),
        }
        for artist, stats in top
    ]


def calculate_top_tracks(data: list[dict], limit: int = 5) -> list[dict]:
    """Top canciones por tiempo."""
    track_time = defaultdict(lambda: {"ms": 0, "plays": 0, "artist": "", "name": ""})

    for item in data:
        track = item.get("master_metadata_track_name")
        artist = item.get("master_metadata_album_artist_name")
        if track and artist:
            key = f"{track}|||{artist}"
            track_time[key]["ms"] += item.get("ms_played", 0)
            track_time[key]["plays"] += 1
            track_time[key]["artist"] = artist
            track_time[key]["name"] = track

    top = sorted(track_time.items(), key=lambda x: x[1]["ms"], reverse=True)[:limit]
    max_ms = top[0][1]["ms"] if top else 1

    return [
        {
            "track": stats["name"],
            "artist": stats["artist"],
            "minutes": round(stats["ms"] / 60000),
            "hours": round(stats["ms"] / 3600000, 1),
            "plays": stats["plays"],
            "pct": round(stats["ms"] / max_ms * 100),
        }
        for _, stats in top
    ]


def calculate_hourly_heatmap(data: list[dict]) -> list[dict]:
    """Heatmap de escuchas por hora (Pacific Time) y mes."""
    heatmap = defaultdict(int)

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            hour = dt_pacific.hour
            month = dt_pacific.month
            heatmap[(month, hour)] += 1

    return [
        {"month": month, "hour": hour, "plays": plays}
        for (month, hour), plays in heatmap.items()
    ]


def calculate_weekday_hour_heatmap(data: list[dict]) -> list[dict]:
    """Heatmap facetado: día de semana (0=Lun, 6=Dom) × hora × mes."""
    heatmap = defaultdict(int)

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            weekday = dt_pacific.weekday()  # 0=Lun, 6=Dom
            hour = dt_pacific.hour
            month = dt_pacific.month
            heatmap[(month, weekday, hour)] += 1

    return [
        {"month": month, "weekday": weekday, "hour": hour, "plays": plays}
        for (month, weekday, hour), plays in heatmap.items()
    ]


def calculate_day_hour_heatmap(data: list[dict]) -> list[dict]:
    """Heatmap facetado: día del mes (1-31) × hora (0-23) × mes."""
    heatmap = defaultdict(int)

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            day = dt_pacific.day  # 1-31
            hour = dt_pacific.hour
            month = dt_pacific.month
            heatmap[(month, day, hour)] += 1

    return [
        {"month": month, "day": day, "hour": hour, "plays": plays}
        for (month, day, hour), plays in heatmap.items()
    ]


def calculate_hourly_distribution(data: list[dict]) -> list[dict]:
    """Distribución de escuchas por hora del día (Pacific Time)."""
    hours = defaultdict(lambda: {"plays": 0, "ms": 0})

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            hour = dt_pacific.hour
            hours[hour]["plays"] += 1
            hours[hour]["ms"] += item.get("ms_played", 0)

    return [
        {"hour": h, "plays": stats["plays"], "minutes": round(stats["ms"] / 60000)}
        for h, stats in sorted(hours.items())
    ]


def calculate_weekday_vs_weekend(data: list[dict]) -> dict:
    """Comparación semana vs fin de semana - NORMALIZADO por día."""
    weekday = {"plays": 0, "ms": 0, "artists": set(), "days": set()}
    weekend = {"plays": 0, "ms": 0, "artists": set(), "days": set()}

    weekday_artists = defaultdict(int)
    weekend_artists = defaultdict(int)

    for item in data:
        ts = item.get("ts")
        artist = item.get("master_metadata_album_artist_name")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            date_key = dt_pacific.date()
            is_weekend = dt_pacific.weekday() >= 5

            bucket = weekend if is_weekend else weekday
            bucket["plays"] += 1
            bucket["ms"] += item.get("ms_played", 0)
            bucket["days"].add(date_key)
            if artist:
                bucket["artists"].add(artist)
                if is_weekend:
                    weekend_artists[artist] += item.get("ms_played", 0)
                else:
                    weekday_artists[artist] += item.get("ms_played", 0)

    weekday_days = len(weekday["days"]) or 1
    weekend_days = len(weekend["days"]) or 1

    top_weekday = sorted(weekday_artists.items(), key=lambda x: x[1], reverse=True)[:3]
    top_weekend = sorted(weekend_artists.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "weekday": {
            "total_hours": round(weekday["ms"] / 3600000, 1),
            "total_plays": weekday["plays"],
            "days_count": weekday_days,
            "avg_hours_per_day": round(weekday["ms"] / 3600000 / weekday_days, 2),
            "avg_plays_per_day": round(weekday["plays"] / weekday_days, 1),
            "unique_artists": len(weekday["artists"]),
            "top_artists": [{"artist": a, "minutes": round(m / 60000)} for a, m in top_weekday],
        },
        "weekend": {
            "total_hours": round(weekend["ms"] / 3600000, 1),
            "total_plays": weekend["plays"],
            "days_count": weekend_days,
            "avg_hours_per_day": round(weekend["ms"] / 3600000 / weekend_days, 2),
            "avg_plays_per_day": round(weekend["plays"] / weekend_days, 1),
            "unique_artists": len(weekend["artists"]),
            "top_artists": [{"artist": a, "minutes": round(m / 60000)} for a, m in top_weekend],
        },
    }


def calculate_skipped_tracks(data: list[dict], min_plays: int = 10, limit: int = 10) -> list[dict]:
    """Canciones que se empiezan pero no se terminan."""
    track_stats = defaultdict(lambda: {"total_plays": 0, "skipped": 0, "name": "", "artist": ""})

    for item in data:
        track = item.get("master_metadata_track_name")
        artist = item.get("master_metadata_album_artist_name")
        skipped = item.get("skipped", False)
        reason_end = item.get("reason_end", "")

        if track and artist:
            key = f"{track}|||{artist}"
            track_stats[key]["total_plays"] += 1
            track_stats[key]["name"] = track
            track_stats[key]["artist"] = artist

            if skipped or reason_end in ["fwdbtn", "backbtn"]:
                track_stats[key]["skipped"] += 1

    candidates = []
    for key, stats in track_stats.items():
        if stats["total_plays"] >= min_plays:
            skip_rate = stats["skipped"] / stats["total_plays"]
            if skip_rate > 0.3:
                candidates.append({
                    "track": stats["name"],
                    "artist": stats["artist"],
                    "total_plays": stats["total_plays"],
                    "skipped": stats["skipped"],
                    "skip_rate": round(skip_rate * 100),
                })

    return sorted(candidates, key=lambda x: x["skip_rate"], reverse=True)[:limit]


def calculate_monthly_trend(data: list[dict]) -> list[dict]:
    """Tendencia mensual de escuchas (Pacific Time) con deltas."""
    months = defaultdict(lambda: {"plays": 0, "ms": 0})

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            month = dt_pacific.month
            months[month]["plays"] += 1
            months[month]["ms"] += item.get("ms_played", 0)

    month_names = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                   "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    result = [
        {
            "month": m,
            "month_name": month_names[m],
            "plays": stats["plays"],
            "hours": round(stats["ms"] / 3600000, 1),
        }
        for m, stats in sorted(months.items())
    ]

    for i, r in enumerate(result):
        if i == 0:
            r["delta"] = 0
            r["delta_pct"] = 0
        else:
            prev_hours = result[i - 1]["hours"]
            r["delta"] = round(r["hours"] - prev_hours, 1)
            r["delta_pct"] = round((r["hours"] - prev_hours) / prev_hours * 100) if prev_hours > 0 else 0

    if result:
        max_month = max(result, key=lambda x: x["hours"])
        max_delta_month = max(result, key=lambda x: x["delta"])

        for r in result:
            r["is_peak"] = r["month"] == max_month["month"]
            r["is_inflection"] = r["month"] == max_delta_month["month"]

    return result


def calculate_special_days(data: list[dict]) -> dict:
    """Actividad en días especiales."""
    daily_stats = defaultdict(lambda: {"plays": 0, "ms": 0})

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            date_key = (dt_pacific.month, dt_pacific.day)
            daily_stats[date_key]["plays"] += 1
            daily_stats[date_key]["ms"] += item.get("ms_played", 0)

    special = {}

    if BIRTHDAY in daily_stats:
        special["birthday"] = {
            "date": "6 de abril",
            "plays": daily_stats[BIRTHDAY]["plays"],
            "minutes": round(daily_stats[BIRTHDAY]["ms"] / 60000),
        }

    for date, name in MEXICAN_HOLIDAYS.items():
        if date in daily_stats:
            special[f"mx_{date[0]}_{date[1]}"] = {
                "date": name,
                "plays": daily_stats[date]["plays"],
                "minutes": round(daily_stats[date]["ms"] / 60000),
            }

    return special


def find_peak_hours(data: list[dict]) -> dict:
    """Encuentra las horas pico de escucha."""
    hours = defaultdict(int)

    for item in data:
        ts = item.get("ts")
        if ts:
            dt_pacific = utc_to_pacific(ts)
            hours[dt_pacific.hour] += 1

    sorted_hours = sorted(hours.items(), key=lambda x: x[1], reverse=True)
    peak_hour = sorted_hours[0][0] if sorted_hours else 0
    top_hours = [h for h, _ in sorted_hours[:5]]

    return {
        "peak_hour": peak_hour,
        "top_hours": sorted(top_hours),
        "description": f"Más activo entre las {min(top_hours)}:00 y {max(top_hours)}:00"
    }


def main():
    print("Cargando datos...")
    data = load_data()

    print("Calculando métricas (con conversión UTC → Pacific)...")

    peak_info = find_peak_hours(data)

    dashboard_data = {
        "overview": calculate_overview(data),
        "top_artists": calculate_top_artists(data),
        "top_tracks": calculate_top_tracks(data),
        "hourly_heatmap": calculate_hourly_heatmap(data),
        "weekday_hour_heatmap": calculate_weekday_hour_heatmap(data),
        "day_hour_heatmap": calculate_day_hour_heatmap(data),
        "hourly_distribution": calculate_hourly_distribution(data),
        "weekday_vs_weekend": calculate_weekday_vs_weekend(data),
        "skipped_tracks": calculate_skipped_tracks(data, min_plays=10),
        "monthly_trend": calculate_monthly_trend(data),
        "special_days": calculate_special_days(data),
        "peak_hours": peak_info,
        "metadata": {
            "timezone": "America/Los_Angeles (Pacific Time)",
            "data_source": "Spotify Extended Streaming History",
            "skip_definition": "Canción marcada como 'skipped' o terminada con 'fwdbtn'/'backbtn'",
            "min_plays_for_skip_rate": 10,
        }
    }

    print(f"Guardando en {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(dashboard_data, f, indent=2, ensure_ascii=False)

    print("¡Listo!")
    print(f"\nResumen:")
    print(f"  - {dashboard_data['overview']['total_minutes']:,} minutos")
    print(f"  - {dashboard_data['overview']['unique_artists']} artistas")
    print(f"  - Hora pico: {peak_info['peak_hour']}:00 (Pacific)")


if __name__ == "__main__":
    main()
