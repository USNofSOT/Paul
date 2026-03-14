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


IMAGE_CACHE_JANITOR_INTERVAL_HOURS = 12

IMAGE_CACHES = {
    "ribbon_board": ImageCacheConfig(
        name="ribbon_board",
        category=AWARDS_CACHE_CATEGORY,
        directory=".cache/ribbon_board",
        default_filename="ribbons.png",
        max_items=LARGE_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=SEVEN_DAYS_IN_SECONDS,
        version=2,
    ),
    "ribbon_icon": ImageCacheConfig(
        name="ribbon_icon",
        category=AWARDS_CACHE_CATEGORY,
        directory=".cache/ribbon_icon",
        default_filename="ribbon_icon.png",
        max_items=XLARGE_IMAGE_CACHE_MAX_ITEMS,
        ttl_seconds=FOURTEEN_DAYS_IN_SECONDS,
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
}


def group_image_caches_by_category() -> dict[str, dict[str, ImageCacheConfig]]:
    grouped_caches: dict[str, dict[str, ImageCacheConfig]] = {}
    for cache_name, cache_config in IMAGE_CACHES.items():
        grouped_caches.setdefault(cache_config.category, {})
        grouped_caches[cache_config.category][cache_name] = cache_config
    return grouped_caches
