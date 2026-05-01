from __future__ import annotations

from dataclasses import dataclass

AWARDS_CACHE_CATEGORY = "awards"
REPORTS_CACHE_CATEGORY = "reports"
SHIPS_CACHE_CATEGORY = "ships"

CACHE_CATEGORY_METADATA = {
    AWARDS_CACHE_CATEGORY: {
        "label": "Awards",
        "emoji": "🎖️",
    },
    REPORTS_CACHE_CATEGORY: {
        "label": "Reports",
        "emoji": "📊",
    },
    SHIPS_CACHE_CATEGORY: {
        "label": "Ships",
        "emoji": "🚢",
    },
}

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30

THIRTY_MINUTES_IN_SECONDS = SECONDS_PER_MINUTE * 30
ONE_HOUR_IN_SECONDS = SECONDS_PER_MINUTE * MINUTES_PER_HOUR
TWO_HOURS_IN_SECONDS = ONE_HOUR_IN_SECONDS * 2
THREE_HOURS_IN_SECONDS = ONE_HOUR_IN_SECONDS * 3
SIX_HOURS_IN_SECONDS = ONE_HOUR_IN_SECONDS * 6
TWELVE_HOURS_IN_SECONDS = ONE_HOUR_IN_SECONDS * 12
ONE_DAY_IN_SECONDS = ONE_HOUR_IN_SECONDS * HOURS_PER_DAY
SEVEN_DAYS_IN_SECONDS = ONE_DAY_IN_SECONDS * 7
FOURTEEN_DAYS_IN_SECONDS = ONE_DAY_IN_SECONDS * 14
THIRTY_DAYS_IN_SECONDS = ONE_DAY_IN_SECONDS * DAYS_PER_MONTH

DEFAULT_IMAGE_CACHE_MAX_ITEMS = 128
MEDIUM_IMAGE_CACHE_MAX_ITEMS = 64
LARGE_IMAGE_CACHE_MAX_ITEMS = 512
XLARGE_IMAGE_CACHE_MAX_ITEMS = 2048

DEFAULT_MEMORY_CACHE_MAX_ITEMS = 128


@dataclass(frozen=True)
class ImageCacheConfig:
    name: str
    category: str
    directory: str
    default_filename: str
    max_items: int = DEFAULT_IMAGE_CACHE_MAX_ITEMS
    ttl_seconds: int = ONE_DAY_IN_SECONDS
    version: int = 1
    extension: str = ".png"
    auto_cleanup_trigger_ratio: float | None = 1.1


@dataclass(frozen=True)
class MemoryCacheConfig:
    name: str
    category: str
    ttl_seconds: int
    max_items: int = DEFAULT_MEMORY_CACHE_MAX_ITEMS


IMAGE_CACHE_JANITOR_INTERVAL_HOURS = 6

IMAGE_CACHES = {
    "ribbon_board": ImageCacheConfig(
        name="ribbon_board",
        category=AWARDS_CACHE_CATEGORY,
        directory=".cache/ribbon_board",
        default_filename="ribbons.png",
        max_items=LARGE_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THIRTY_DAYS_IN_SECONDS,
        version=2,
    ),
    "ribbon_icon": ImageCacheConfig(
        name="ribbon_icon",
        category=AWARDS_CACHE_CATEGORY,
        directory=".cache/ribbon_icon",
        default_filename="ribbon_icon.png",
        max_items=XLARGE_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THIRTY_DAYS_IN_SECONDS,
        version=1,
    ),
    "crewreport_voyage_chart": ImageCacheConfig(
        name="crewreport_voyage_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/crewreport/voyage_chart",
        default_filename="voyage_pie_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=ONE_HOUR_IN_SECONDS,
        version=1,
    ),
    "crewreport_hosted_chart": ImageCacheConfig(
        name="crewreport_hosted_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/crewreport/hosted_chart",
        default_filename="hosted_pie_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=ONE_HOUR_IN_SECONDS,
        version=1,
    ),
    "netreport_growth_chart": ImageCacheConfig(
        name="netreport_growth_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/netreport/growth_chart",
        default_filename="growth_bar_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THREE_HOURS_IN_SECONDS,
        version=1,
    ),
    "ship_voyages_trend": ImageCacheConfig(
        name="ship_voyages_trend",
        category=SHIPS_CACHE_CATEGORY,
        directory=".cache/ships/voyages_trend",
        default_filename="ship_voyages_trend.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "ship_hosted_trend": ImageCacheConfig(
        name="ship_hosted_trend",
        category=SHIPS_CACHE_CATEGORY,
        directory=".cache/ships/hosted_trend",
        default_filename="ship_hosted_trend.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "ship_size_trend": ImageCacheConfig(
        name="ship_size_trend",
        category=SHIPS_CACHE_CATEGORY,
        directory=".cache/ships/size_trend",
        default_filename="ship_size_trend.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "rank_size_trend": ImageCacheConfig(
        name="rank_size_trend",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/reports/rank_size_trend",
        default_filename="rank_size_trend.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "ping_usage_trend": ImageCacheConfig(
        name="ping_usage_trend",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/reports/ping_usage_trend",
        default_filename="ping_usage_trend.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "ship_health_summary_chart": ImageCacheConfig(
        name="ship_health_summary_chart",
        category=SHIPS_CACHE_CATEGORY,
        directory=".cache/ships/health_summary_chart",
        default_filename="ship_health_summary_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "pocket_watch_activity_chart": ImageCacheConfig(
        name="pocket_watch_activity_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/pocket_watch/activity_chart",
        default_filename="pocket_watch_activity.png",
        max_items=256,
        ttl_seconds=TWO_HOURS_IN_SECONDS,
        version=1,
    ),
    "health_latency_chart": ImageCacheConfig(
        name="health_latency_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/health/latency",
        default_filename="latency_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THIRTY_MINUTES_IN_SECONDS,
        version=1,
    ),
    "health_connections_chart": ImageCacheConfig(
        name="health_connections_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/health/connections",
        default_filename="connections_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THIRTY_MINUTES_IN_SECONDS,
        version=1,
    ),
    "health_pool_chart": ImageCacheConfig(
        name="health_pool_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/health/pool",
        default_filename="pool_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THIRTY_MINUTES_IN_SECONDS,
        version=1,
    ),
    "health_memory_chart": ImageCacheConfig(
        name="health_memory_chart",
        category=REPORTS_CACHE_CATEGORY,
        directory=".cache/health/memory",
        default_filename="memory_chart.png",
        max_items=MEDIUM_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=THIRTY_MINUTES_IN_SECONDS,
        version=1,
    ),
}

MEMORY_CACHES = {
    "unique_ship_names": MemoryCacheConfig(
        name="unique_ship_names",
        category=SHIPS_CACHE_CATEGORY,
        ttl_seconds=ONE_HOUR_IN_SECONDS,
    ),
    "ship_name_combinations": MemoryCacheConfig(
        name="ship_name_combinations",
        category=SHIPS_CACHE_CATEGORY,
        ttl_seconds=ONE_HOUR_IN_SECONDS,
    ),
    "ship_history": MemoryCacheConfig(
        name="ship_history",
        category=SHIPS_CACHE_CATEGORY,
        ttl_seconds=ONE_HOUR_IN_SECONDS,
    ),
}


def group_image_caches_by_category() -> dict[str, dict[str, ImageCacheConfig]]:
    grouped_caches: dict[str, dict[str, ImageCacheConfig]] = {}
    for cache_name, cache_config in IMAGE_CACHES.items():
        grouped_caches.setdefault(cache_config.category, {})
        grouped_caches[cache_config.category][cache_name] = cache_config
    return grouped_caches


def group_memory_caches_by_category() -> dict[str, dict[str, MemoryCacheConfig]]:
    grouped_caches: dict[str, dict[str, MemoryCacheConfig]] = {}
    for cache_name, cache_config in MEMORY_CACHES.items():
        grouped_caches.setdefault(cache_config.category, {})
        grouped_caches[cache_config.category][cache_name] = cache_config
    return grouped_caches
