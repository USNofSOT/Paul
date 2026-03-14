import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from src.config.cache import ImageCacheConfig
from src.utils.image_cache import (
    BinaryImageCache,
    CacheStatsSnapshot,
    build_cache_key,
    clear_cached_items,
    cleanup_cache,
)


class FakeStatsRecorder:
    def __init__(self):
        self.request_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        self.calls = []

    def record_request(self, cache_name: str, was_hit: bool) -> CacheStatsSnapshot:
        self.request_count += 1
        if was_hit:
            self.cache_hit_count += 1
        else:
            self.cache_miss_count += 1

        self.calls.append((cache_name, was_hit))
        return CacheStatsSnapshot(
            cache_name=cache_name,
            request_count=self.request_count,
            cache_hit_count=self.cache_hit_count,
            cache_miss_count=self.cache_miss_count,
            cached_percent=round(
                (self.cache_hit_count / self.request_count) * 100,
                2,
            ),
        )


class TestImageCache(unittest.TestCase):
    def test_build_cache_key_is_stable_for_equivalent_payloads(self):
        left = {
            "roles": [{"id": 2, "icon_url": "b"}, {"id": 1, "icon_url": "a"}],
            "layout": {"columns": 3, "spacing": 5},
        }
        right = {
            "layout": {"spacing": 5, "columns": 3},
            "roles": [{"id": 2, "icon_url": "b"}, {"icon_url": "a", "id": 1}],
        }

        self.assertEqual(
            build_cache_key(left, version=2),
            build_cache_key(right, version=2),
        )

    def test_get_or_create_bytes_uses_cached_file_after_first_write(self):
        with TemporaryDirectory() as temp_dir:
            stats_recorder = FakeStatsRecorder()
            cache = BinaryImageCache(
                ImageCacheConfig(
                    name="test_cache",
                    category="tests",
                    directory=temp_dir,
                    default_filename="image.png",
                    max_items=5,
                    ttl_seconds=60,
                ),
                stats_recorder=stats_recorder,
            )
            producer = MagicMock(return_value=b"cached-image")
            payload = {"value": 1}

            first = cache.get_or_create_bytes(payload, producer)
            second = cache.get_or_create_bytes(payload, producer)

            self.assertEqual(first, b"cached-image")
            self.assertEqual(second, b"cached-image")
            self.assertEqual(producer.call_count, 1)
            self.assertEqual(len(list(Path(temp_dir).glob("*.png"))), 1)
            self.assertEqual(
                stats_recorder.calls,
                [("test_cache", False), ("test_cache", True)],
            )

    def test_get_or_create_bytes_async_uses_cached_file_after_first_write(self):
        async def run_test():
            with TemporaryDirectory() as temp_dir:
                stats_recorder = FakeStatsRecorder()
                cache = BinaryImageCache(
                    ImageCacheConfig(
                        name="test_cache",
                        category="tests",
                        directory=temp_dir,
                        default_filename="image.png",
                        max_items=5,
                        ttl_seconds=60,
                    ),
                    stats_recorder=stats_recorder,
                )
                producer = MagicMock(return_value=b"cached-image")
                payload = {"value": 2}

                first = await cache.get_or_create_bytes_async(payload, producer)
                second = await cache.get_or_create_bytes_async(payload, producer)

                self.assertEqual(first, b"cached-image")
                self.assertEqual(second, b"cached-image")
                self.assertEqual(producer.call_count, 1)
                self.assertEqual(len(list(Path(temp_dir).glob("*.png"))), 1)
                self.assertEqual(
                    stats_recorder.calls,
                    [("test_cache", False), ("test_cache", True)],
                )

        import asyncio

        asyncio.run(run_test())

    def test_cleanup_cache_removes_expired_and_overflow_items(self):
        with TemporaryDirectory() as temp_dir:
            config = ImageCacheConfig(
                name="cleanup_cache",
                category="tests",
                directory=temp_dir,
                default_filename="image.png",
                max_items=2,
                ttl_seconds=60,
            )
            base_time = time.time()
            file_specs = [
                ("expired.png", base_time - 120),
                ("keep_newest.png", base_time - 10),
                ("keep_second.png", base_time - 20),
                ("remove_overflow.png", base_time - 30),
            ]

            for file_name, modified_time in file_specs:
                path = Path(temp_dir) / file_name
                path.write_bytes(file_name.encode("utf-8"))
                os.utime(path, (modified_time, modified_time))

            result = cleanup_cache(config, now=base_time)

            self.assertEqual(result.removed_expired, 1)
            self.assertEqual(result.removed_overflow, 1)
            self.assertEqual(result.remaining_items, 2)
            self.assertEqual(
                sorted(path.name for path in Path(temp_dir).glob("*.png")),
                ["keep_newest.png", "keep_second.png"],
            )

    def test_to_discord_file_uses_default_filename(self):
        with TemporaryDirectory() as temp_dir:
            cache = BinaryImageCache(
                ImageCacheConfig(
                    name="test_cache",
                    category="tests",
                    directory=temp_dir,
                    default_filename="image.png",
                    max_items=5,
                    ttl_seconds=60,
                )
            )

            discord_file = cache.to_discord_file(b"image-bytes")

            self.assertEqual(discord_file.filename, "image.png")

    def test_clear_cached_items_removes_all_matching_files(self):
        with TemporaryDirectory() as temp_dir:
            config = ImageCacheConfig(
                name="test_cache",
                category="tests",
                directory=temp_dir,
                default_filename="image.png",
                max_items=5,
                ttl_seconds=60,
            )
            (Path(temp_dir) / "one.png").write_bytes(b"1")
            (Path(temp_dir) / "two.png").write_bytes(b"2")
            (Path(temp_dir) / "note.txt").write_text("ignore", encoding="utf-8")

            removed_items = clear_cached_items(config)

            self.assertEqual(removed_items, 2)
            self.assertEqual(len(list(Path(temp_dir).glob("*.png"))), 0)
            self.assertTrue((Path(temp_dir) / "note.txt").exists())


if __name__ == "__main__":
    unittest.main()
